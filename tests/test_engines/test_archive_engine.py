import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.archive_engine import ArchiveEngine


def _make_zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)


def _make_tar(path: Path, entries: dict[str, bytes], *, mode: str = "w") -> None:
    with tarfile.open(path, mode) as tf:
        for name, content in entries.items():
            data = content
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))


def test_supports_archive_to_folder_pairs() -> None:
    engine = ArchiveEngine()

    assert engine.supports("zip", "folder")
    assert engine.supports("tar", "folder")
    assert engine.supports("tgz", "folder")
    assert engine.supports("tbz", "folder")
    assert engine.supports("txz", "folder")
    assert engine.supports("gz", "folder")
    assert engine.supports("bz2", "folder")
    assert engine.supports("xz", "folder")
    assert not engine.supports("zip", "zip")
    assert not engine.supports("zip", "tar")


@pytest.mark.asyncio
async def test_extract_zip_writes_files_into_target_directory(tmp_path) -> None:
    archive = tmp_path / "bundle.zip"
    _make_zip(
        archive,
        {
            "readme.txt": b"hello world",
            "src/main.py": b"print('hi')\n",
        },
    )
    target = tmp_path / "out"

    task = Task(
        input_path=archive,
        output_path=target,
        format_in="zip",
        format_out="folder",
        engine="archive",
    )
    await ArchiveEngine().convert(task)

    assert (target / "readme.txt").read_bytes() == b"hello world"
    assert (target / "src" / "main.py").read_bytes() == b"print('hi')\n"
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_extract_zip_rejects_path_traversal_entries(tmp_path) -> None:
    archive = tmp_path / "evil.zip"
    _make_zip(archive, {"../escape.txt": b"x"})
    target = tmp_path / "out"

    task = Task(
        input_path=archive,
        output_path=target,
        format_in="zip",
        format_out="folder",
        engine="archive",
    )
    with pytest.raises(RuntimeError, match="outside target folder"):
        await ArchiveEngine().convert(task)


@pytest.mark.asyncio
async def test_extract_zip_rejects_absolute_path_entry(tmp_path) -> None:
    archive = tmp_path / "abs.zip"
    _make_zip(archive, {"/etc/passwd": b"x"})
    target = tmp_path / "out"

    task = Task(
        input_path=archive,
        output_path=target,
        format_in="zip",
        format_out="folder",
        engine="archive",
    )
    with pytest.raises(RuntimeError, match="absolute path"):
        await ArchiveEngine().convert(task)


@pytest.mark.asyncio
async def test_extract_plain_tar(tmp_path) -> None:
    archive = tmp_path / "bundle.tar"
    _make_tar(archive, {"a.txt": b"alpha", "b.txt": b"beta"})
    target = tmp_path / "out"

    task = Task(
        input_path=archive,
        output_path=target,
        format_in="tar",
        format_out="folder",
        engine="archive",
    )
    await ArchiveEngine().convert(task)

    assert (target / "a.txt").read_bytes() == b"alpha"
    assert (target / "b.txt").read_bytes() == b"beta"


@pytest.mark.asyncio
async def test_extract_tgz_uses_gzip_decompression(tmp_path) -> None:
    archive = tmp_path / "bundle.tgz"
    _make_tar(archive, {"x.bin": b"\x00\x01\x02"}, mode="w:gz")
    target = tmp_path / "out"

    task = Task(
        input_path=archive,
        output_path=target,
        format_in="tgz",
        format_out="folder",
        engine="archive",
    )
    await ArchiveEngine().convert(task)

    assert (target / "x.bin").read_bytes() == b"\x00\x01\x02"


@pytest.mark.asyncio
async def test_extract_tar_xz_via_xz_format_alias(tmp_path) -> None:
    archive = tmp_path / "bundle.tar.xz"
    _make_tar(archive, {"deep/file.txt": b"deep"}, mode="w:xz")
    target = tmp_path / "out"

    task = Task(
        input_path=archive,
        output_path=target,
        format_in="xz",
        format_out="folder",
        engine="archive",
    )
    await ArchiveEngine().convert(task)

    assert (target / "deep" / "file.txt").read_bytes() == b"deep"


@pytest.mark.asyncio
async def test_unsupported_format_raises(tmp_path) -> None:
    archive = tmp_path / "f.zip"
    _make_zip(archive, {"a.txt": b"a"})

    task = Task(
        input_path=archive,
        output_path=tmp_path / "out",
        format_in="zip",
        format_out="zip",  # not supported (output must be folder)
        engine="archive",
    )
    with pytest.raises(RuntimeError, match="Unsupported archive conversion"):
        await ArchiveEngine().convert(task)
