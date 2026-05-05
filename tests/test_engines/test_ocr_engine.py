from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.ocr_engine import (
    TesseractOCREngine,
    parse_osd_rotation,
    stitch_hocr_pages,
    stitch_text_pages,
    stitch_tsv_pages,
)


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
    # Wave 2: PDF input is now supported (routed through render → tesseract → stitch)
    assert engine.supports("pdf", "txt")
    assert engine.supports("pdf", "pdf")
    assert engine.supports("pdf", "hocr")
    assert engine.supports("pdf", "tsv")
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


# ---- Wave 2: PDF input pipeline helpers ----


def test_parse_osd_rotation_extracts_rotate_value() -> None:
    text = (
        "Page number: 0\n"
        "Orientation in degrees: 270\n"
        "Rotate: 90\n"
        "Orientation confidence: 13.30\n"
    )
    assert parse_osd_rotation(text) == 90


def test_parse_osd_rotation_returns_zero_when_missing() -> None:
    assert parse_osd_rotation("no osd info here") == 0


def test_parse_osd_rotation_normalizes_to_canonical_set() -> None:
    # 360 -> 0, negative wraps, non-canonical drops to 0
    assert parse_osd_rotation("Rotate: 360") == 0
    assert parse_osd_rotation("Rotate: -90") == 270
    assert parse_osd_rotation("Rotate: 45") == 0


def test_stitch_text_pages_uses_form_feed_separator() -> None:
    output = stitch_text_pages(["Page 1 text\n", "Page 2 text\n"])

    assert output == "Page 1 text\n\f\nPage 2 text\n"


def test_stitch_text_pages_handles_empty_list() -> None:
    assert stitch_text_pages([]) == "\n"


def test_stitch_tsv_pages_keeps_single_header_then_concatenates_rows() -> None:
    chunk_one = "level\tpage_num\ttext\n5\t1\tHello\n"
    chunk_two = "level\tpage_num\ttext\n5\t1\tWorld\n"

    output = stitch_tsv_pages([chunk_one, chunk_two])
    lines = output.strip().split("\n")
    assert lines[0] == "level\tpage_num\ttext"
    assert lines[1] == "5\t1\tHello"
    assert lines[2] == "5\t1\tWorld"


def test_stitch_hocr_pages_concatenates_page_divs_with_unique_ids() -> None:
    chunk_one = (
        "<html><head></head><body>\n"
        "<div class='ocr_page' id='page_1'>page-one-content</div>\n"
        "</body></html>"
    )
    chunk_two = (
        "<html><head></head><body>\n"
        "<div class='ocr_page' id='page_1'>page-two-content</div>\n"
        "</body></html>"
    )

    output = stitch_hocr_pages([chunk_one, chunk_two])

    assert "page-one-content" in output
    assert "page-two-content" in output
    # IDs renumbered to avoid clash
    assert "id='page_1'" in output
    assert "id='page_2'" in output
    # Single closing body/html
    assert output.count("</body>") == 1
    assert output.count("</html>") == 1


def test_stitch_hocr_pages_returns_empty_for_empty_input() -> None:
    assert stitch_hocr_pages([]) == ""


@pytest.mark.asyncio
async def test_pdf_input_runs_render_ocr_stitch_pipeline(tmp_path, monkeypatch) -> None:
    fitz = pytest.importorskip("fitz")

    input_pdf = tmp_path / "in.pdf"
    document = fitz.open()
    for page_index in range(2):
        page = document.new_page(width=400, height=600)
        page.insert_text((50, 100), f"PAGE {page_index + 1}")
    document.save(str(input_pdf))
    document.close()

    fake_tesseract = tmp_path / "tesseract"
    fake_tesseract.write_text(
        "#!/bin/sh\n"
        "# args: ... INPUT OUTPUT_STEM ...\n"
        "INPUT=\"$1\"\n"
        "OUTPUT=\"$2\"\n"
        "echo \"OCR text from $(basename $INPUT)\" > \"$OUTPUT.txt\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_tesseract.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{__import__('os').environ.get('PATH', '')}")

    output_path = tmp_path / "out.txt"
    task = Task(
        input_path=input_pdf,
        output_path=output_path,
        format_in="pdf",
        format_out="txt",
        engine="tesseract",
    )

    await TesseractOCREngine().convert(task)

    output = output_path.read_text(encoding="utf-8")
    assert "OCR text from page-0001.png" in output
    assert "OCR text from page-0002.png" in output
    assert "\f" in output
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_pdf_input_propagates_tesseract_failure(tmp_path, monkeypatch) -> None:
    fitz = pytest.importorskip("fitz")

    input_pdf = tmp_path / "in.pdf"
    document = fitz.open()
    document.new_page(width=200, height=200)
    document.save(str(input_pdf))
    document.close()

    fake_tesseract = tmp_path / "tesseract"
    fake_tesseract.write_text(
        "#!/bin/sh\necho 'bad config' >&2\nexit 1\n", encoding="utf-8"
    )
    fake_tesseract.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{__import__('os').environ.get('PATH', '')}")

    task = Task(
        input_path=input_pdf,
        output_path=tmp_path / "out.txt",
        format_in="pdf",
        format_out="txt",
        engine="tesseract",
    )

    with pytest.raises(RuntimeError, match="tesseract page 1 failed"):
        await TesseractOCREngine().convert(task)
