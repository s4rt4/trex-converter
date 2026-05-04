from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


TEXT_INPUTS = {"doc", "docx", "odt", "rtf"}
TEXT_OUTPUTS = {"docx", "odt", "rtf", "html", "epub", "txt", "pdf"}
SPREADSHEET_INPUTS = {"xls", "xlsx", "ods"}
SPREADSHEET_OUTPUTS = {"xlsx", "ods", "csv", "html", "pdf"}
PRESENTATION_INPUTS = {"ppt", "pptx", "odp"}
PRESENTATION_OUTPUTS = {"pptx", "odp", "pdf"}

SUPPORTED_INPUT_FORMATS = TEXT_INPUTS | SPREADSHEET_INPUTS | PRESENTATION_INPUTS

SUPPORTED_PAIRS = (
    {(fmt_in, fmt_out) for fmt_in in TEXT_INPUTS for fmt_out in TEXT_OUTPUTS}
    | {(fmt_in, fmt_out) for fmt_in in SPREADSHEET_INPUTS for fmt_out in SPREADSHEET_OUTPUTS}
    | {(fmt_in, fmt_out) for fmt_in in PRESENTATION_INPUTS for fmt_out in PRESENTATION_OUTPUTS}
)
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

                produced_path = _find_converted_file(
                    task.input_path, temp_output_dir, task.format_out
                )
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


def _find_converted_file(input_path: Path, output_dir: Path, format_out: str) -> Path:
    suffix = format_out.lower()
    expected_path = output_dir / f"{Path(input_path).stem}.{suffix}"
    if expected_path.exists():
        return expected_path

    matches = sorted(output_dir.glob(f"*.{suffix}"))
    if len(matches) == 1:
        return matches[0]

    raise RuntimeError(
        f"LibreOffice did not produce a .{suffix} output file"
    )
