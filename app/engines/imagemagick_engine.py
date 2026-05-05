from __future__ import annotations

import asyncio
from shutil import which

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


IMAGE_FORMATS = (
    "avif",
    "bmp",
    "gif",
    "heic",
    "ico",
    "jpg",
    "jpeg",
    "pdf",
    "png",
    "tif",
    "tiff",
    "webp",
)
SUPPORTED_PAIRS = {
    (format_in, format_out)
    for format_in in IMAGE_FORMATS
    for format_out in IMAGE_FORMATS
    if format_in != format_out
}

VALID_GRAVITIES = {
    "northwest",
    "north",
    "northeast",
    "west",
    "center",
    "east",
    "southwest",
    "south",
    "southeast",
}
VALID_ASPECTS = {"1:1", "4:5", "5:4", "3:2", "2:3", "16:9", "9:16", "4:3", "3:4"}
ICO_AUTO_RESIZE = "256,128,64,48,32,16"


class ImageMagickEngine(BaseEngine):
    name = "imagemagick"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="magick",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        command = self._build_command(task)
        task.append_log("Running: " + " ".join(command))
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            stdout, stderr = await process.communicate()
            if stdout:
                task.append_log(stdout.decode("utf-8", errors="replace").strip())
            if stderr:
                task.append_log(stderr.decode("utf-8", errors="replace").strip())
            if process.returncode != 0:
                raise RuntimeError(f"ImageMagick exited with code {process.returncode}")
            task.progress = 1.0
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

    async def cancel(self, task: Task) -> None:
        process = self._processes.get(task.id)
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        task.mark_cancelled()

    def supports(self, format_in: str, format_out: str) -> bool:
        return (format_in.lower(), format_out.lower()) in SUPPORTED_PAIRS

    @property
    def capabilities(self) -> EngineCapabilities:
        return self._capabilities

    def _build_command(self, task: Task) -> list[str]:
        operation = str(task.options.get("operation") or "").lower()
        if operation == "montage":
            return _build_montage_command(task)
        return self._build_single_command(task)

    def _build_single_command(self, task: Task) -> list[str]:
        binary = _imagemagick_binary()
        options = task.options
        command: list[str] = [binary]

        density = _int_option(options.get("density"))
        if density and density > 0:
            command.extend(["-density", str(density)])

        command.append(str(task.input_path))

        rotate = _int_option(options.get("rotate"))
        if rotate:
            command.extend(["-rotate", str(rotate)])

        if options.get("flip"):
            command.append("-flip")
        if options.get("flop"):
            command.append("-flop")

        if options.get("auto_trim"):
            command.extend(["-trim", "+repage"])

        crop_aspect = options.get("crop_aspect")
        if crop_aspect and crop_aspect in VALID_ASPECTS:
            command.extend(["-gravity", "center", "-crop", crop_aspect, "+repage"])

        crop = options.get("crop")
        if crop:
            command.extend(["-crop", str(crop), "+repage"])

        resize_value = _resolve_resize(options)
        if resize_value:
            command.extend(["-resize", resize_value])

        if options.get("grayscale"):
            command.extend(["-colorspace", "Gray"])

        sepia = _int_option(options.get("sepia"))
        if sepia and sepia > 0:
            command.extend(["-sepia-tone", f"{sepia}%"])

        if options.get("negate"):
            command.append("-negate")
        if options.get("normalize"):
            command.append("-normalize")

        brightness = _int_option(options.get("brightness")) or 0
        contrast = _int_option(options.get("contrast")) or 0
        if brightness or contrast:
            command.extend(["-brightness-contrast", f"{brightness}x{contrast}"])

        gamma = _float_option(options.get("gamma"))
        if gamma is not None and gamma > 0 and gamma != 1.0:
            command.extend(["-gamma", _format_float(gamma)])

        blur = _float_option(options.get("blur"))
        if blur is not None and blur > 0:
            command.extend(["-blur", f"0x{_format_float(blur)}"])

        sharpen = _float_option(options.get("sharpen"))
        if sharpen is not None and sharpen > 0:
            command.extend(["-sharpen", f"0x{_format_float(sharpen)}"])

        if options.get("denoise"):
            command.append("-enhance")

        if options.get("vignette"):
            command.extend(["-background", "black", "-vignette", "0x10"])

        border_size = _int_option(options.get("border_size"))
        if border_size and border_size > 0:
            border_color = str(options.get("border_color") or "black")
            command.extend([
                "-bordercolor",
                border_color,
                "-border",
                f"{border_size}x{border_size}",
            ])

        frame_size = _int_option(options.get("frame_size"))
        if frame_size and frame_size > 0:
            command.extend(["-frame", f"{frame_size}x{frame_size}"])

        watermark_text = options.get("watermark_text")
        if watermark_text:
            command.extend(_watermark_args(watermark_text, options))
            command.extend(["-gravity", "none"])

        if options.get("strip"):
            command.append("-strip")

        quality = _int_option(options.get("quality"))
        if quality is not None:
            command.extend(["-quality", str(quality)])

        if task.format_out.lower() == "ico" and not resize_value:
            command.extend(["-define", f"icon:auto-resize={ICO_AUTO_RESIZE}"])

        command.append(str(task.output_path))
        return command


def _imagemagick_binary() -> str:
    if which("magick"):
        return "magick"
    return "convert"


_MONTAGE_TILE_RE = None  # populated below to avoid moving the import


def _build_montage_command(task: Task) -> list[str]:
    import re as _re

    sources = list(task.inputs)
    if len(sources) < 2:
        raise RuntimeError("Montage requires at least two input images")

    options = task.options
    binary = _imagemagick_binary()
    if binary == "magick":
        command = ["magick", "montage"]
    else:
        command = ["montage"]

    for source in sources:
        command.append(str(source))

    tile = str(options.get("montage_tile") or "auto").lower()
    if tile == "auto":
        tile = _auto_tile(len(sources))
    if not _re.match(r"^\d+x\d+$", tile):
        raise RuntimeError(f"montage_tile must look like '3x3', got {options.get('montage_tile')}")
    command.extend(["-tile", tile])

    geometry = str(options.get("montage_geometry") or "200x200+5+5")
    if not _re.match(r"^\d+x\d+(?:[+]\d+[+]\d+)?$", geometry):
        raise RuntimeError(
            f"montage_geometry must look like '200x200+5+5', got {options.get('montage_geometry')}"
        )
    command.extend(["-geometry", geometry])

    background = str(options.get("montage_background") or "white")
    command.extend(["-background", background])

    label = options.get("montage_label")
    if label:
        command.extend(["-label", str(label)])

    command.append(str(task.output_path))
    return command


def _auto_tile(count: int) -> str:
    import math

    if count <= 1:
        return "1x1"
    cols = int(math.ceil(math.sqrt(count)))
    rows = int(math.ceil(count / cols))
    return f"{cols}x{rows}"


def _resolve_resize(options: dict) -> str | None:
    raw = options.get("resize")
    mode = (options.get("resize_mode") or "dimension").lower()
    if raw is None or raw == "":
        return None
    text = str(raw).strip()
    if not text:
        return None

    if mode == "dimension":
        return text
    if mode == "longest_edge":
        edge = _int_option(text)
        if not edge or edge <= 0:
            return None
        return f"{edge}x{edge}>"
    if mode == "percent":
        percent = _float_option(text)
        if percent is None or percent <= 0:
            return None
        return f"{_format_float(percent)}%"
    if mode == "megapixel":
        megapixels = _float_option(text)
        if megapixels is None or megapixels <= 0:
            return None
        pixels = int(megapixels * 1_000_000)
        return f"@{pixels}"
    return text


def _watermark_args(text: str, options: dict) -> list[str]:
    gravity = str(options.get("watermark_position") or "southeast").lower()
    if gravity not in VALID_GRAVITIES:
        gravity = "southeast"
    opacity = _int_option(options.get("watermark_opacity"))
    if opacity is None:
        opacity = 60
    opacity = max(0, min(100, opacity))
    alpha = opacity / 100.0
    fill = f"rgba(255,255,255,{_format_float(alpha)})"
    pointsize = _int_option(options.get("watermark_size")) or 36
    return [
        "-gravity",
        gravity,
        "-pointsize",
        str(pointsize),
        "-fill",
        fill,
        "-annotate",
        "+12+12",
        str(text),
    ]


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float_option(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_float(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")
