from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.ocr_engine import TesseractOCREngine


def _build(options: dict, *, format_in: str = "png", format_out: str = "txt") -> list[str]:
    task = Task(
        input_path=Path(f"in.{format_in}"),
        output_path=Path(f"out.{format_out}"),
        format_in=format_in,
        format_out=format_out,
        engine="tesseract",
        options=options,
    )
    return TesseractOCREngine()._build_command(task)


def test_supports_image_to_text_and_pdf() -> None:
    engine = TesseractOCREngine()

    assert engine.supports("png", "txt")
    assert engine.supports("jpg", "pdf")
    assert engine.supports("jpeg", "txt")
    assert engine.supports("tif", "pdf")
    assert engine.supports("tiff", "hocr")
    assert engine.supports("bmp", "tsv")
    assert not engine.supports("pdf", "txt")
    assert not engine.supports("png", "webp")


def test_default_command_for_txt_uses_eng_and_no_config() -> None:
    command = _build({})

    assert command[0] == "tesseract"
    assert command[1] == "in.png"
    # output stem strips extension
    assert command[2] == "out"
    assert command[command.index("-l") + 1] == "eng"
    # no positional config for txt; no PSM/OEM by default
    assert "pdf" not in command
    assert "hocr" not in command
    assert "--psm" not in command
    assert "--oem" not in command


def test_pdf_output_appends_pdf_config() -> None:
    command = _build({}, format_in="png", format_out="pdf")

    assert command[-1] == "pdf"
    assert command[2] == "out"


def test_hocr_and_tsv_outputs_append_their_configs() -> None:
    hocr_command = _build({}, format_in="png", format_out="hocr")
    tsv_command = _build({}, format_in="png", format_out="tsv")

    assert hocr_command[-1] == "hocr"
    assert tsv_command[-1] == "tsv"


def test_custom_language_passes_through() -> None:
    command = _build({"ocr_language": "ind+eng"})

    assert command[command.index("-l") + 1] == "ind+eng"


def test_blank_language_falls_back_to_eng() -> None:
    command = _build({"ocr_language": "   "})

    assert command[command.index("-l") + 1] == "eng"


def test_psm_and_oem_options_emit_flags() -> None:
    command = _build({"ocr_psm": 6, "ocr_oem": 1})

    assert command[command.index("--psm") + 1] == "6"
    assert command[command.index("--oem") + 1] == "1"


def test_invalid_psm_raises() -> None:
    with pytest.raises(RuntimeError, match="Invalid PSM"):
        _build({"ocr_psm": 99})


def test_invalid_oem_raises() -> None:
    with pytest.raises(RuntimeError, match="Invalid OEM"):
        _build({"ocr_oem": 7})


def test_pdf_output_combines_all_options() -> None:
    command = _build(
        {"ocr_language": "eng+ind", "ocr_psm": 7, "ocr_oem": 1},
        format_in="jpg",
        format_out="pdf",
    )

    assert command[1] == "in.jpg"
    assert command[2] == "out"
    assert command[command.index("-l") + 1] == "eng+ind"
    assert command[command.index("--psm") + 1] == "7"
    assert command[command.index("--oem") + 1] == "1"
    assert command[-1] == "pdf"
