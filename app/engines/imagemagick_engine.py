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
        binary = _imagemagick_binary()
        command = [binary]
        if binary == "magick":
            command.append(str(task.input_path))
        else:
            command.append(str(task.input_path))

        resize = task.options.get("resize")
        if resize:
            command.extend(["-resize", str(resize)])

        quality = task.options.get("quality")
        if quality is not None:
            command.extend(["-quality", str(quality)])

        if task.options.get("strip", False):
            command.append("-strip")

        command.append(str(task.output_path))
        return command


def _imagemagick_binary() -> str:
    if which("magick"):
        return "magick"
    return "convert"
