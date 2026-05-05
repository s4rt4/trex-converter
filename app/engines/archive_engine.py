from __future__ import annotations

import asyncio
import tarfile
import zipfile
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


ARCHIVE_INPUT_FORMATS = (
    "zip",
    "tar",
    "tgz",
    "tbz",
    "txz",
    "gz",
    "bz2",
    "xz",
)
FOLDER_INPUT = "folder"
FOLDER_OUTPUT = "folder"
COMPRESS_FORMATS = ("zip", "tar", "tgz", "tbz", "txz")
SUPPORTED_PAIRS = (
    {(fmt_in, FOLDER_OUTPUT) for fmt_in in ARCHIVE_INPUT_FORMATS}
    | {(FOLDER_INPUT, fmt_out) for fmt_out in COMPRESS_FORMATS}
)

_TAR_EXTRACT_FORMATS = {"tar", "tgz", "tbz", "txz", "gz", "bz2", "xz"}
_TAR_COMPRESS_MODES = {
    "tar": "w",
    "tgz": "w:gz",
    "tbz": "w:bz2",
    "txz": "w:xz",
}


class ArchiveEngine(BaseEngine):
    name = "archive"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=True,
            supports_cancel=False,
            requires_binary="",
        )

    async def convert(self, task: Task) -> None:
        format_in = task.format_in.lower()
        format_out = task.format_out.lower()
        if (format_in, format_out) not in SUPPORTED_PAIRS:
            raise RuntimeError(
                f"Unsupported archive conversion: {task.format_in} -> {task.format_out}"
            )

        if format_in == FOLDER_INPUT:
            await self._compress(task, format_out)
            return

        target_dir = Path(task.output_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        input_path = Path(task.input_path)
        task.append_log(f"Extracting {input_path.name} to {target_dir}")

        if format_in == "zip":
            await asyncio.to_thread(_extract_zip, input_path, target_dir, task)
        elif format_in in _TAR_EXTRACT_FORMATS:
            await asyncio.to_thread(_extract_tar, input_path, target_dir, task)
        else:
            raise RuntimeError(f"Unsupported archive format: {format_in}")

        task.progress = 1.0

    async def _compress(self, task: Task, format_out: str) -> None:
        source_dir = Path(task.input_path)
        if not source_dir.exists():
            raise RuntimeError(f"Source folder does not exist: {source_dir}")
        if not source_dir.is_dir():
            raise RuntimeError(f"Compress requires a folder, got file: {source_dir}")

        archive_path = Path(task.output_path)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        task.append_log(
            f"Compressing folder {source_dir} -> {archive_path} ({format_out})"
        )

        if format_out == "zip":
            await asyncio.to_thread(_compress_zip, source_dir, archive_path, task)
        elif format_out in _TAR_COMPRESS_MODES:
            mode = _TAR_COMPRESS_MODES[format_out]
            await asyncio.to_thread(_compress_tar, source_dir, archive_path, mode, task)
        else:
            raise RuntimeError(f"Unsupported compress format: {format_out}")

        task.progress = 1.0

    def supports(self, format_in: str, format_out: str) -> bool:
        return (format_in.lower(), format_out.lower()) in SUPPORTED_PAIRS

    @property
    def capabilities(self) -> EngineCapabilities:
        return self._capabilities


def _extract_zip(archive_path: Path, target_dir: Path, task: Task) -> None:
    with zipfile.ZipFile(archive_path, "r") as zf:
        members = zf.namelist()
        total = max(1, len(members))
        for index, member in enumerate(members, start=1):
            _ensure_safe_member(member, target_dir)
            zf.extract(member, target_dir)
            task.progress = 0.05 + 0.9 * (index / total)
        task.append_log(f"Extracted {len(members)} entry/entries from ZIP")


def _extract_tar(archive_path: Path, target_dir: Path, task: Task) -> None:
    with tarfile.open(archive_path, "r:*") as tf:
        members = tf.getmembers()
        total = max(1, len(members))
        for index, member in enumerate(members, start=1):
            _ensure_safe_member(member.name, target_dir)
            tf.extract(member, target_dir, filter="data")
            task.progress = 0.05 + 0.9 * (index / total)
        task.append_log(f"Extracted {len(members)} entry/entries from tar archive")


def _compress_zip(source_dir: Path, archive_path: Path, task: Task) -> None:
    files = sorted(p for p in source_dir.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError(f"Source folder is empty: {source_dir}")

    total = len(files)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, file_path in enumerate(files, start=1):
            arcname = file_path.relative_to(source_dir).as_posix()
            zf.write(file_path, arcname)
            task.progress = 0.05 + 0.9 * (index / total)
    task.append_log(f"Wrote {total} file(s) into ZIP")


def _compress_tar(
    source_dir: Path, archive_path: Path, mode: str, task: Task
) -> None:
    files = sorted(p for p in source_dir.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError(f"Source folder is empty: {source_dir}")

    total = len(files)
    with tarfile.open(archive_path, mode) as tf:
        for index, file_path in enumerate(files, start=1):
            arcname = file_path.relative_to(source_dir).as_posix()
            tf.add(file_path, arcname=arcname, recursive=False)
            task.progress = 0.05 + 0.9 * (index / total)
    task.append_log(f"Wrote {total} file(s) into tar ({mode})")


def _ensure_safe_member(name: str, target_dir: Path) -> None:
    if not name:
        return
    if Path(name).is_absolute():
        raise RuntimeError(f"Refusing to extract absolute path entry: {name}")
    candidate = (target_dir / name).resolve()
    base = target_dir.resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise RuntimeError(
            f"Refusing to extract entry outside target folder: {name}"
        ) from exc
