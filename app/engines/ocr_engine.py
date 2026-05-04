from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


OCR_INPUT_FORMATS = ("png", "jpg", "jpeg", "tif", "tiff", "bmp")
OCR_OUTPUT_FORMATS = ("txt", "pdf", "hocr", "tsv")
SUPPORTED_PAIRS = {
    (fmt_in, fmt_out)
    for fmt_in in OCR_INPUT_FORMATS
    for fmt_out in OCR_OUTPUT_FORMATS
}

VALID_PSM = set(range(0, 14))
VALID_OEM = {0, 1, 2, 3}


class TesseractOCREngine(BaseEngine):
    name = "tesseract"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="tesseract",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        command = self._build_command(task)
        task.append_log("Running: " + " ".join(command))

        Path(task.output_path).parent.mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process

        try:
            stdout_bytes, stderr_bytes = await process.communicate()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            if stderr_text:
                for line in stderr_text.splitlines():
                    if line.strip():
                        task.append_log(line.strip())

            if process.returncode != 0:
                raise RuntimeError(f"tesseract exited with code {process.returncode}")
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
        output_path = Path(task.output_path)
        output_stem = str(output_path.with_suffix(""))

        command = ["tesseract", str(task.input_path), output_stem]

        language = (task.options.get("ocr_language") or "eng").strip()
        if not language:
            language = "eng"
        command.extend(["-l", language])

        psm = _int_option(task.options.get("ocr_psm"))
        if psm is not None:
            if psm not in VALID_PSM:
                raise RuntimeError(f"Invalid PSM (expected 0-13): {psm}")
            command.extend(["--psm", str(psm)])

        oem = _int_option(task.options.get("ocr_oem"))
        if oem is not None:
            if oem not in VALID_OEM:
                raise RuntimeError(f"Invalid OEM (expected 0-3): {oem}")
            command.extend(["--oem", str(oem)])

        format_out = task.format_out.lower()
        if format_out == "pdf":
            command.append("pdf")
        elif format_out == "hocr":
            command.append("hocr")
        elif format_out == "tsv":
            command.append("tsv")
        # txt is tesseract's default; no positional config needed

        return command


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
