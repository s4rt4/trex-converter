from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


# Map of file extension → Pandoc format name. We accept several common
# extensions for the same logical format (md/markdown, latex/tex).
PANDOC_INPUT_FORMAT = {
    "epub": "epub",
    "docx": "docx",
    "odt": "odt",
    "html": "html",
    "htm": "html",
    "md": "markdown",
    "markdown": "markdown",
    "rst": "rst",
    "latex": "latex",
    "tex": "latex",
    "org": "org",
    "fb2": "fb2",
}

PANDOC_OUTPUT_FORMAT = dict(PANDOC_INPUT_FORMAT)
# `txt` output uses Pandoc's "plain" writer. We don't accept .txt as input
# because plain text has no structure for Pandoc's markdown reader to grip.
PANDOC_OUTPUT_FORMAT["txt"] = "plain"

INPUT_EXTENSIONS = tuple(sorted(PANDOC_INPUT_FORMAT.keys()))
OUTPUT_EXTENSIONS = tuple(sorted(PANDOC_OUTPUT_FORMAT.keys()))

SUPPORTED_PAIRS = {
    (fmt_in, fmt_out)
    for fmt_in in INPUT_EXTENSIONS
    for fmt_out in OUTPUT_EXTENSIONS
    if fmt_in != fmt_out
    and PANDOC_INPUT_FORMAT[fmt_in] != PANDOC_OUTPUT_FORMAT.get(fmt_out)
}


class PandocEngine(BaseEngine):
    name = "pandoc"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="pandoc",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        pair = (task.format_in.lower(), task.format_out.lower())
        if pair not in SUPPORTED_PAIRS:
            raise RuntimeError(
                f"Unsupported Pandoc conversion: {task.format_in} -> {task.format_out}"
            )

        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        command = build_command(task)
        task.append_log("Running: " + " ".join(command))
        await self._run(command, task)

        if not output_path.exists():
            raise RuntimeError(
                f"Pandoc did not produce expected output: {output_path}"
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

    async def _run(self, command: list[str], task: Task) -> None:
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
                f"pandoc exited with code {process.returncode}: {stderr_text}"
            )


def build_command(task: Task) -> list[str]:
    fmt_in = task.format_in.lower()
    fmt_out = task.format_out.lower()
    if fmt_in not in PANDOC_INPUT_FORMAT:
        raise RuntimeError(f"Unsupported Pandoc input format: {fmt_in}")
    if fmt_out not in PANDOC_OUTPUT_FORMAT:
        raise RuntimeError(f"Unsupported Pandoc output format: {fmt_out}")

    options = task.options
    pandoc_in = PANDOC_INPUT_FORMAT[fmt_in]
    pandoc_out = PANDOC_OUTPUT_FORMAT[fmt_out]

    command: list[str] = [
        "pandoc",
        "--from",
        pandoc_in,
        "--to",
        pandoc_out,
        "--output",
        str(task.output_path),
    ]

    # Standalone makes most output formats actually open-able. Pandoc enables
    # it automatically for binary formats (docx/epub/odt) but not for html,
    # latex, or plain text — be explicit so the output is consistent.
    if fmt_out in ("html", "htm", "latex", "tex"):
        command.append("--standalone")

    metadata = _metadata_args(options)
    command.extend(metadata)

    if _bool_option(options.get("pandoc_self_contained")) and pandoc_out == "html":
        # pandoc 3+ uses --embed-resources --standalone for what used to be
        # --self-contained. We emit both so older pandocs still work.
        command.append("--embed-resources")

    if _bool_option(options.get("pandoc_table_of_contents")):
        command.append("--toc")

    extra_raw = options.get("pandoc_extra_args")
    if extra_raw:
        if isinstance(extra_raw, (list, tuple)):
            command.extend(str(arg) for arg in extra_raw)
        else:
            command.extend(str(extra_raw).split())

    command.append(str(task.input_path))
    return command


def _metadata_args(options: dict) -> list[str]:
    args: list[str] = []
    fields = (
        ("ebook_title", "title"),
        ("ebook_author", "author"),
        ("ebook_language", "lang"),
        ("ebook_publisher", "publisher"),
        ("ebook_date", "date"),
    )
    for option_key, pandoc_key in fields:
        value = options.get(option_key)
        if value is None or value == "":
            continue
        args.extend(["--metadata", f"{pandoc_key}={value}"])
    return args


def _bool_option(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(value, (int, float)):
        return bool(value)
    return False
