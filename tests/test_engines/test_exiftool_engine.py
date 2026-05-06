import os
from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.exiftool_engine import (
    ExifToolEngine,
    SUPPORTED_PAIRS,
    build_edit_command,
    build_read_command,
    build_strip_command,
)


def test_supports_same_format_pairs() -> None:
    engine = ExifToolEngine()

    assert engine.supports("jpg", "jpg")
    assert engine.supports("mp3", "mp3")
    assert engine.supports("mp4", "mp4")
    assert engine.supports("pdf", "pdf")


def test_supports_dump_to_txt() -> None:
    engine = ExifToolEngine()

    assert engine.supports("jpg", "txt")
    assert engine.supports("pdf", "txt")
    assert engine.supports("mp4", "txt")


def test_supports_rejects_cross_format() -> None:
    engine = ExifToolEngine()

    assert not engine.supports("jpg", "png")
    assert not engine.supports("mp3", "mp4")


def test_capabilities_require_exiftool() -> None:
    caps = ExifToolEngine().capabilities

    assert caps.requires_binary == "exiftool"
    assert caps.supports_cancel is True


def test_supported_pairs_includes_dumps_for_every_input() -> None:
    # Every input format should have both same-format and txt outputs.
    inputs = sorted({fmt_in for fmt_in, _ in SUPPORTED_PAIRS})
    for fmt_in in inputs:
        assert (fmt_in, fmt_in) in SUPPORTED_PAIRS or fmt_in == "txt"
        assert (fmt_in, "txt") in SUPPORTED_PAIRS


def test_read_command_default_is_json() -> None:
    task = Task(
        input_path=Path("/tmp/in.jpg"),
        output_path=Path("/tmp/out.txt"),
        format_in="jpg",
        format_out="txt",
        engine="exiftool",
    )
    command = build_read_command(task)

    assert command[0] == "exiftool"
    assert "-j" in command  # JSON output
    assert command[-1] == "/tmp/in.jpg"


def test_read_command_text_format() -> None:
    task = Task(
        input_path=Path("/tmp/in.jpg"),
        output_path=Path("/tmp/out.txt"),
        format_in="jpg",
        format_out="txt",
        engine="exiftool",
        options={"metadata_format": "text"},
    )
    command = build_read_command(task)

    assert "-j" not in command


def test_read_command_invalid_format_raises() -> None:
    task = Task(
        input_path=Path("/tmp/in.jpg"),
        output_path=Path("/tmp/out.txt"),
        format_in="jpg",
        format_out="txt",
        engine="exiftool",
        options={"metadata_format": "yaml"},
    )
    with pytest.raises(RuntimeError, match="metadata_format"):
        build_read_command(task)


def test_strip_command_uses_overwrite_original_and_all_clear() -> None:
    command = build_strip_command(Path("/tmp/out.jpg"))

    assert "-overwrite_original" in command
    assert "-all=" in command
    assert command[-1] == "/tmp/out.jpg"


def test_edit_command_emits_tag_pairs() -> None:
    task = Task(
        input_path=Path("/tmp/in.mp3"),
        output_path=Path("/tmp/out.mp3"),
        format_in="mp3",
        format_out="mp3",
        engine="exiftool",
        options={
            "metadata_title": "Song",
            "metadata_artist": "Band",
            "metadata_keywords": "rock, live",
        },
    )
    command = build_edit_command(task, Path("/tmp/out.mp3"))

    assert "-Title=Song" in command
    assert "-Artist=Band" in command
    assert "-Keywords=rock, live" in command
    assert command[-1] == "/tmp/out.mp3"


def test_edit_command_skips_empty_fields() -> None:
    task = Task(
        input_path=Path("/tmp/in.jpg"),
        output_path=Path("/tmp/out.jpg"),
        format_in="jpg",
        format_out="jpg",
        engine="exiftool",
        options={
            "metadata_title": "",
            "metadata_artist": "Hello",
            "metadata_subject": None,
        },
    )
    command = build_edit_command(task, Path("/tmp/out.jpg"))

    assert "-Artist=Hello" in command
    assert not any(arg.startswith("-Title=") for arg in command)
    assert not any(arg.startswith("-Subject=") for arg in command)


@pytest.mark.asyncio
async def test_convert_strip_invokes_exiftool(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "exiftool"
    fake.write_text(
        "#!/bin/sh\n# Pretend to strip metadata: do nothing, exit 0.\nexit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.jpg"
    src.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")
    out = tmp_path / "out.jpg"

    task = Task(
        input_path=src,
        output_path=out,
        format_in="jpg",
        format_out="jpg",
        engine="exiftool",
        options={"operation": "strip"},
    )
    await ExifToolEngine().convert(task)

    assert out.exists()
    assert out.read_bytes() == src.read_bytes()  # copyfile preserves content
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_convert_read_writes_stdout_to_output(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "exiftool"
    fake.write_text(
        "#!/bin/sh\necho '[{\"Title\":\"x\"}]'\nexit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.jpg"
    src.write_bytes(b"fake")
    out = tmp_path / "out.txt"

    task = Task(
        input_path=src,
        output_path=out,
        format_in="jpg",
        format_out="txt",
        engine="exiftool",
        options={"operation": "read"},
    )
    await ExifToolEngine().convert(task)

    text = out.read_text(encoding="utf-8")
    assert "Title" in text


@pytest.mark.asyncio
async def test_edit_without_any_tag_raises(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "exiftool"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.mp3"
    src.write_bytes(b"id3v2")

    task = Task(
        input_path=src,
        output_path=tmp_path / "out.mp3",
        format_in="mp3",
        format_out="mp3",
        engine="exiftool",
        options={"operation": "edit"},  # no tag values
    )
    with pytest.raises(RuntimeError, match="metadata edit requires"):
        await ExifToolEngine().convert(task)


@pytest.mark.asyncio
async def test_convert_propagates_exiftool_failure(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "exiftool"
    fake.write_text("#!/bin/sh\necho 'boom' >&2\nexit 1\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.jpg"
    src.write_bytes(b"x")

    task = Task(
        input_path=src,
        output_path=tmp_path / "out.jpg",
        format_in="jpg",
        format_out="jpg",
        engine="exiftool",
        options={"operation": "strip"},
    )
    with pytest.raises(RuntimeError, match="exiftool exited"):
        await ExifToolEngine().convert(task)
