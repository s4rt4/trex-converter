from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities
from app.engines.imagemagick_engine import _imagemagick_binary


BITMAP_TRACE_FORMATS = ("png", "jpg", "jpeg", "bmp", "tif", "tiff", "gif", "webp")
TRACE_PAIRS = {(fmt, "svg") for fmt in BITMAP_TRACE_FORMATS}

INKSCAPE_PAIRS = {
    ("svg", "png"),
    ("svg", "pdf"),
    ("svg", "svg"),
    ("svg", "eps"),
    ("svg", "ps"),
    ("svg", "emf"),
    ("svg", "wmf"),
    ("svg", "dxf"),
    ("pdf", "svg"),
    ("dxf", "svg"),
}

SUPPORTED_PAIRS = INKSCAPE_PAIRS | TRACE_PAIRS

SVG_SVG_OPERATIONS = {"trim", "cleanup"}
PS_LEVELS = {2, 3}
TEXT_TO_PATH_FORMATS = {"pdf", "eps", "ps", "svg"}

DXF_EXTENSIONS = {
    "r14": "org.ekips.output.dxf_outlines",
    "r12": "org.inkscape.output.dxf_twelve",
}


class InkscapeEngine(BaseEngine):
    name = "inkscape"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="inkscape",
            extra_binaries=("potrace", "magick"),
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        pair = (task.format_in.lower(), task.format_out.lower())
        if pair not in SUPPORTED_PAIRS:
            raise RuntimeError(
                f"Unsupported SVG conversion: {task.format_in} -> {task.format_out}"
            )

        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if pair in TRACE_PAIRS:
            await self._run_trace(task)
        else:
            command = build_command(task)
            task.append_log("Running: " + " ".join(command))
            await self._run(command, task, "inkscape")

        if not output_path.exists():
            raise RuntimeError(
                f"Conversion did not produce expected output: {output_path}"
            )

        task.append_log(f"Wrote: {output_path}")
        task.progress = 1.0

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

    async def _run_trace(self, task: Task) -> None:
        input_path = Path(task.input_path)
        output_path = Path(task.output_path)

        with tempfile.TemporaryDirectory(prefix="trex-trace-") as tmpdir:
            pgm_path = Path(tmpdir) / "input.pgm"
            magick_cmd = _build_magick_pgm_command(input_path, pgm_path)
            task.append_log("Running: " + " ".join(magick_cmd))
            await self._run(magick_cmd, task, "magick")

            potrace_cmd = build_potrace_command(task, pgm_path, output_path)
            task.append_log("Running: " + " ".join(potrace_cmd))
            await self._run(potrace_cmd, task, "potrace")

    async def _run(self, command: list[str], task: Task, label: str) -> None:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            _, stderr_bytes = await process.communicate()
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

        if process.returncode != 0:
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"{label} exited with code {process.returncode}: {stderr_text}"
            )


def build_command(task: Task) -> list[str]:
    format_in = task.format_in.lower()
    format_out = task.format_out.lower()
    options = task.options
    input_path = Path(task.input_path)
    output_path = Path(task.output_path)

    if (format_in, format_out) not in INKSCAPE_PAIRS:
        raise RuntimeError(
            f"Unsupported Inkscape pair: {format_in} -> {format_out}"
        )

    command: list[str] = [
        "inkscape",
        f"--export-filename={output_path}",
    ]

    if format_out == "dxf":
        # Extension-based export: --export-type is omitted, the extension drives output.
        dxf_format = str(options.get("inkscape_dxf_format") or "r14").lower()
        if dxf_format not in DXF_EXTENSIONS:
            raise RuntimeError(
                f"inkscape_dxf_format must be one of "
                f"{sorted(DXF_EXTENSIONS)}, got {dxf_format}"
            )
        command.append(f"--export-extension={DXF_EXTENSIONS[dxf_format]}")
    elif format_in == "dxf" and format_out == "svg":
        command.append("--export-type=svg")
        command.append("--export-plain-svg")
    elif format_in == "pdf" and format_out == "svg":
        command.append("--export-type=svg")
        command.append("--export-plain-svg")
        command.extend(_pdf_page_args(options))
    elif format_out == "png":
        command.append("--export-type=png")
        command.extend(_raster_size_args(options))
        command.extend(_export_id_args(options))
    elif format_out == "pdf":
        command.append("--export-type=pdf")
        command.extend(_export_id_args(options))
        if _bool_option(options.get("text_to_path")):
            command.append("--export-text-to-path")
    elif format_out in ("eps", "ps"):
        command.append(f"--export-type={format_out}")
        command.extend(_ps_level_args(options))
        command.extend(_export_id_args(options))
        if _bool_option(options.get("text_to_path")):
            command.append("--export-text-to-path")
    elif format_out in ("emf", "wmf"):
        command.append(f"--export-type={format_out}")
        command.extend(_export_id_args(options))
    elif format_out == "svg":
        operation = str(options.get("operation") or "cleanup").lower()
        if operation not in SVG_SVG_OPERATIONS:
            raise RuntimeError(
                f"Unsupported SVG operation: {operation} "
                f"(expected one of {sorted(SVG_SVG_OPERATIONS)})"
            )
        command.append("--export-type=svg")
        command.append("--export-plain-svg")
        command.append("--vacuum-defs")
        if operation == "trim":
            command.append("--export-area-drawing")
        command.extend(_export_id_args(options))
        if _bool_option(options.get("text_to_path")):
            command.append("--export-text-to-path")
    else:
        raise RuntimeError(f"Unsupported SVG output format: {format_out}")

    command.append(str(input_path))
    return command


def build_potrace_command(
    task: Task, pgm_path: Path, output_path: Path
) -> list[str]:
    options = task.options
    command = ["potrace", str(pgm_path), "-s", "-o", str(output_path)]

    threshold = options.get("trace_threshold")
    if threshold is not None and threshold != "":
        try:
            value = float(threshold)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"trace_threshold must be a number, got {threshold!r}"
            ) from exc
        if not 0.0 <= value <= 1.0:
            raise RuntimeError(
                f"trace_threshold must be between 0 and 1, got {value}"
            )
        command.extend(["-k", f"{value:g}"])

    turdsize = _int_option(options.get("trace_turdsize"))
    if turdsize is not None:
        if turdsize < 0:
            raise RuntimeError(f"trace_turdsize must be >= 0, got {turdsize}")
        command.extend(["-t", str(turdsize)])

    alphamax = options.get("trace_alphamax")
    if alphamax is not None and alphamax != "":
        try:
            value = float(alphamax)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"trace_alphamax must be a number, got {alphamax!r}"
            ) from exc
        if value < 0.0:
            raise RuntimeError(f"trace_alphamax must be >= 0, got {value}")
        command.extend(["-a", f"{value:g}"])

    return command


def _build_magick_pgm_command(input_path: Path, pgm_path: Path) -> list[str]:
    binary = _imagemagick_binary()
    return [binary, str(input_path), "-colorspace", "Gray", str(pgm_path)]


def _raster_size_args(options: dict) -> list[str]:
    args: list[str] = []
    width = _int_option(options.get("inkscape_width"))
    height = _int_option(options.get("inkscape_height"))
    dpi = _int_option(options.get("inkscape_dpi"))

    if width is not None:
        if width < 1:
            raise RuntimeError(f"inkscape_width must be positive, got {width}")
        args.append(f"--export-width={width}")
    if height is not None:
        if height < 1:
            raise RuntimeError(f"inkscape_height must be positive, got {height}")
        args.append(f"--export-height={height}")
    if dpi is not None:
        if dpi < 1:
            raise RuntimeError(f"inkscape_dpi must be positive, got {dpi}")
        args.append(f"--export-dpi={dpi}")

    return args


def _ps_level_args(options: dict) -> list[str]:
    level = _int_option(options.get("inkscape_ps_level"))
    if level is None:
        return []
    if level not in PS_LEVELS:
        raise RuntimeError(
            f"inkscape_ps_level must be one of {sorted(PS_LEVELS)}, got {level}"
        )
    return [f"--export-ps-level={level}"]


def _export_id_args(options: dict) -> list[str]:
    raw_id = options.get("inkscape_export_id")
    if raw_id is None:
        return []
    export_id = str(raw_id).strip()
    if not export_id:
        return []
    args = [f"--export-id={export_id}"]
    if _bool_option(options.get("inkscape_export_id_only")):
        args.append("--export-id-only")
    return args


def _pdf_page_args(options: dict) -> list[str]:
    page = _int_option(options.get("inkscape_pdf_page"))
    if page is None:
        return []
    if page < 1:
        raise RuntimeError(f"inkscape_pdf_page must be >= 1, got {page}")
    return [f"--pages={page}"]


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _bool_option(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(value, (int, float)):
        return bool(value)
    return False
