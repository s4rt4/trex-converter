import os
from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.qr_engine import (
    QREngine,
    build_decode_command,
    build_generate_command,
)


def _build_generate(options: dict, *, format_out: str = "png") -> list[str]:
    task = Task(
        input_path=Path("/tmp/in.txt"),
        output_path=Path("/tmp/out." + format_out),
        format_in="txt",
        format_out=format_out,
        engine="qr",
        options=options,
    )
    return build_generate_command(task)


def test_supports_generate_and_decode_pairs() -> None:
    engine = QREngine()

    assert engine.supports("txt", "png")
    assert engine.supports("txt", "svg")
    assert engine.supports("png", "txt")
    assert engine.supports("jpg", "txt")
    assert engine.supports("jpeg", "txt")
    assert engine.supports("bmp", "txt")
    assert engine.supports("tif", "txt")
    assert not engine.supports("txt", "txt")
    assert not engine.supports("png", "png")


def test_generate_command_default_options_uses_qrencode_with_input_file() -> None:
    command = _build_generate({})

    assert command[0] == "qrencode"
    assert command[command.index("-r") + 1] == "/tmp/in.txt"
    assert command[command.index("-o") + 1] == "/tmp/out.png"
    assert command[command.index("-t") + 1] == "PNG"


def test_generate_command_svg_output_passes_svg_type() -> None:
    command = _build_generate({}, format_out="svg")

    assert command[command.index("-t") + 1] == "SVG"


def test_generate_command_size_margin_and_ecc() -> None:
    command = _build_generate(
        {"qr_size": 12, "qr_margin": 4, "qr_ecc_level": "H"}
    )

    assert command[command.index("-s") + 1] == "12"
    assert command[command.index("-m") + 1] == "4"
    assert command[command.index("-l") + 1] == "H"


def test_generate_command_normalizes_lowercase_ecc_level() -> None:
    command = _build_generate({"qr_ecc_level": "q"})

    assert command[command.index("-l") + 1] == "Q"


def test_generate_command_invalid_ecc_level_raises() -> None:
    with pytest.raises(RuntimeError, match="qr_ecc_level"):
        _build_generate({"qr_ecc_level": "X"})


def test_generate_command_invalid_size_raises() -> None:
    with pytest.raises(RuntimeError, match="qr_size"):
        _build_generate({"qr_size": 99})


def test_generate_command_invalid_margin_raises() -> None:
    with pytest.raises(RuntimeError, match="qr_margin"):
        _build_generate({"qr_margin": 100})


def test_decode_command_uses_zbarimg_with_raw_quiet_flags() -> None:
    task = Task(
        input_path=Path("/tmp/in.png"),
        output_path=Path("/tmp/out.txt"),
        format_in="png",
        format_out="txt",
        engine="qr",
    )
    command = build_decode_command(task)

    assert command[0] == "zbarimg"
    assert "--raw" in command
    assert "-q" in command
    assert command[-1] == "/tmp/in.png"


@pytest.mark.asyncio
async def test_generate_invokes_qrencode_subprocess(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "qrencode"
    fake.write_text(
        "#!/bin/sh\n"
        "# qrencode mock: echo args, write a fake output via -o\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"-o\" ]; then\n"
        "    OUT=\"$2\"; shift 2; continue\n"
        "  fi\n"
        "  shift\n"
        "done\n"
        "echo 'fake-png' > \"$OUT\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.txt"
    input_path.write_text("hello qr", encoding="utf-8")
    output_path = tmp_path / "out.png"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="txt",
        format_out="png",
        engine="qr",
    )

    await QREngine().convert(task)

    assert output_path.read_text(encoding="utf-8").strip() == "fake-png"
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_generate_propagates_qrencode_failure(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "qrencode"
    fake.write_text("#!/bin/sh\necho 'nope' >&2\nexit 2\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.txt"
    input_path.write_text("x", encoding="utf-8")

    task = Task(
        input_path=input_path,
        output_path=tmp_path / "out.png",
        format_in="txt",
        format_out="png",
        engine="qr",
    )
    with pytest.raises(RuntimeError, match="qrencode exited"):
        await QREngine().convert(task)


@pytest.mark.asyncio
async def test_decode_writes_zbarimg_stdout_to_text_file(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "zbarimg"
    fake.write_text(
        "#!/bin/sh\necho 'decoded payload'\nexit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.png"
    input_path.write_bytes(b"fake-png")
    output_path = tmp_path / "out.txt"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="png",
        format_out="txt",
        engine="qr",
    )

    await QREngine().convert(task)

    assert output_path.read_text(encoding="utf-8") == "decoded payload\n"
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_decode_raises_when_no_barcode_found(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "zbarimg"
    # zbarimg exits with 4 when no barcode is detected; stdout is empty
    fake.write_text(
        "#!/bin/sh\nexit 4\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.png"
    input_path.write_bytes(b"fake")

    task = Task(
        input_path=input_path,
        output_path=tmp_path / "out.txt",
        format_in="png",
        format_out="txt",
        engine="qr",
    )
    with pytest.raises(RuntimeError, match="no barcodes"):
        await QREngine().convert(task)


def test_capabilities_advertise_both_qrencode_and_zbarimg() -> None:
    caps = QREngine().capabilities

    assert caps.requires_binary == "qrencode"
    assert "zbarimg" in caps.extra_binaries
