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
FOLDER_OUTPUT = "folder"
SUPPORTED_PAIRS = {
    (fmt_in, FOLDER_OUTPUT) for fmt_in in ARCHIVE_INPUT_FORMATS
}

_TAR_FORMATS = {"tar", "tgz", "tbz", "txz", "gz", "bz2", "xz"}


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
        if (format_in, task.format_out.lower()) not in SUPPORTED_PAIRS:
            raise RuntimeError(
                f"Unsupported archive conversion: {task.format_in} -> {task.format_out}"
            )

        target_dir = Path(task.output_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        input_path = Path(task.input_path)
        task.append_log(f"Extracting {input_path.name} to {target_dir}")

        if format_in == "zip":
            await asyncio.to_thread(_extract_zip, input_path, target_dir, task)
        elif format_in in _TAR_FORMATS:
            await asyncio.to_thread(_extract_tar, input_path, target_dir, task)
        else:
            raise RuntimeError(f"Unsupported archive format: {format_in}")

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
