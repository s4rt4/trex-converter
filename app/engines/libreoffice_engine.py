from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


SUPPORTED_INPUT_FORMATS = {
    "doc",
    "docx",
    "odp",
    "ods",
    "odt",
    "ppt",
    "pptx",
    "rtf",
    "xls",
    "xlsx",
}
SUPPORTED_PAIRS = {
    (format_in, "pdf")
    for format_in in SUPPORTED_INPUT_FORMATS
}
DEFAULT_TIMEOUT_SECONDS = 120


class LibreOfficeEngine(BaseEngine):
    name = "libreoffice"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="libreoffice",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="trex-libreoffice-") as temp_dir:
            temp_output_dir = Path(temp_dir)
            command = self._build_command(task, temp_output_dir)
            task.append_log("Running: " + " ".join(command))
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._processes[task.id] = process

            try:
                timeout = _timeout_seconds(task)
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                _append_output(task, stdout)
                _append_output(task, stderr)

                if process.returncode != 0:
                    raise RuntimeError(
                        f"LibreOffice exited with code {process.returncode}"
                    )

                produced_path = _find_converted_pdf(task.input_path, temp_output_dir)
                shutil.move(str(produced_path), str(output_path))
                task.progress = 1.0
            except asyncio.TimeoutError as exc:
                await self.cancel(task)
                raise RuntimeError(
                    f"LibreOffice timed out after {_timeout_seconds(task)} seconds"
                ) from exc
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

    def _build_command(self, task: Task, output_dir: Path) -> list[str]:
        return [
            "libreoffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            task.format_out,
            "--outdir",
            str(output_dir),
            str(task.input_path),
        ]


def _timeout_seconds(task: Task) -> float:
    timeout = task.options.get("timeout", DEFAULT_TIMEOUT_SECONDS)
    try:
        return float(timeout)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS


def _append_output(task: Task, output: bytes) -> None:
    text = output.decode("utf-8", errors="replace").strip()
    if text:
        task.append_log(text)


def _find_converted_pdf(input_path: Path, output_dir: Path) -> Path:
    expected_path = output_dir / f"{Path(input_path).stem}.pdf"
    if expected_path.exists():
        return expected_path

    pdf_outputs = sorted(output_dir.glob("*.pdf"))
    if len(pdf_outputs) == 1:
        return pdf_outputs[0]

    raise RuntimeError("LibreOffice did not produce a PDF output file")
