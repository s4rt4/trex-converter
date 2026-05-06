from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


METADATA_INPUT_FORMATS = (
    "jpg", "jpeg", "png", "tif", "tiff", "heic", "webp", "gif",
    "mp3", "m4a", "flac", "wav", "ogg",
    "mp4", "mov", "mkv", "webm",
    "pdf",
)

METADATA_OPERATIONS = {"read", "strip", "edit"}

# Logical option key → exiftool tag name. We use generic, well-known tag
# names so they apply across the major media types exiftool supports.
TAG_FIELDS = (
    ("metadata_title", "Title"),
    ("metadata_artist", "Artist"),
    ("metadata_author", "Author"),
    ("metadata_subject", "Subject"),
    ("metadata_description", "Description"),
    ("metadata_comment", "Comment"),
    ("metadata_copyright", "Copyright"),
    ("metadata_keywords", "Keywords"),
)

SUPPORTED_PAIRS = {
    (fmt, fmt) for fmt in METADATA_INPUT_FORMATS
} | {
    (fmt, "txt") for fmt in METADATA_INPUT_FORMATS
}


class ExifToolEngine(BaseEngine):
    name = "exiftool"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="exiftool",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        pair = (task.format_in.lower(), task.format_out.lower())
        if pair not in SUPPORTED_PAIRS:
            raise RuntimeError(
                f"Unsupported metadata conversion: {task.format_in} -> {task.format_out}"
            )

        operation = str(task.options.get("operation") or _default_operation(pair)).lower()
        if operation not in METADATA_OPERATIONS:
            raise RuntimeError(
                f"Unsupported metadata operation: {operation} "
                f"(expected one of {sorted(METADATA_OPERATIONS)})"
            )

        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if operation == "read":
            await self._run_read(task, output_path)
            return

        # strip / edit both copy the input to output then rewrite tags.
        shutil.copyfile(task.input_path, output_path)
        if operation == "strip":
            await self._run_strip(task, output_path)
        else:
            await self._run_edit(task, output_path)

        if not output_path.exists():
            raise RuntimeError(f"exiftool did not produce expected output: {output_path}")
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

    async def _run_read(self, task: Task, output_path: Path) -> None:
        command = build_read_command(task)
        task.append_log("Running: " + " ".join(command))
        stdout = await self._run_capture(command, task)
        output_path.write_bytes(stdout)
        task.append_log(f"Wrote metadata dump: {output_path}")
        task.progress = 1.0

    async def _run_strip(self, task: Task, output_path: Path) -> None:
        command = build_strip_command(output_path)
        task.append_log("Running: " + " ".join(command))
        await self._run_quiet(command, task)
        task.append_log("Stripped all metadata tags")

    async def _run_edit(self, task: Task, output_path: Path) -> None:
        command = build_edit_command(task, output_path)
        if not _has_tag_writes(command):
            raise RuntimeError(
                "metadata edit requires at least one of: "
                + ", ".join(key for key, _ in TAG_FIELDS)
            )
        task.append_log("Running: " + " ".join(command))
        await self._run_quiet(command, task)
        edited = sum(1 for arg in command if arg.startswith("-") and "=" in arg)
        task.append_log(f"Edited {edited} tag(s)")

    async def _run_capture(self, command: list[str], task: Task) -> bytes:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            stdout_bytes, stderr_bytes = await process.communicate()
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

        if process.returncode != 0:
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"exiftool exited with code {process.returncode}: {stderr_text}"
            )
        return stdout_bytes

    async def _run_quiet(self, command: list[str], task: Task) -> None:
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
                f"exiftool exited with code {process.returncode}: {stderr_text}"
            )


def _default_operation(pair: tuple[str, str]) -> str:
    return "read" if pair[1] == "txt" else "strip"


def build_read_command(task: Task) -> list[str]:
    fmt = str(task.options.get("metadata_format") or "json").lower()
    if fmt == "json":
        return ["exiftool", "-a", "-G1", "-j", str(task.input_path)]
    if fmt == "text":
        return ["exiftool", "-a", "-G1", str(task.input_path)]
    raise RuntimeError(f"Unsupported metadata_format: {fmt} (expected json or text)")


def build_strip_command(target: Path) -> list[str]:
    return ["exiftool", "-overwrite_original", "-all=", str(target)]


def build_edit_command(task: Task, target: Path) -> list[str]:
    command: list[str] = ["exiftool", "-overwrite_original"]
    options = task.options
    for option_key, tag_name in TAG_FIELDS:
        value = options.get(option_key)
        if value is None or value == "":
            continue
        command.append(f"-{tag_name}={value}")
    command.append(str(target))
    return command


def _has_tag_writes(command: list[str]) -> bool:
    return any("=" in arg and arg.startswith("-") for arg in command)
