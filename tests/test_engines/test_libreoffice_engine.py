from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.libreoffice_engine import LibreOfficeEngine


@pytest.mark.asyncio
async def test_libreoffice_engine_runs_subprocess_and_moves_pdf(tmp_path, monkeypatch) -> None:
    fake_libreoffice = tmp_path / "libreoffice"
    fake_libreoffice.write_text(
        "#!/bin/sh\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--outdir\" ]; then\n"
        "    shift\n"
        "    outdir=\"$1\"\n"
        "  fi\n"
        "  input=\"$1\"\n"
        "  shift\n"
        "done\n"
        "base=$(basename \"$input\")\n"
        "stem=${base%.*}\n"
        "echo converted\n"
        "printf 'pdf-data' > \"$outdir/$stem.pdf\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_libreoffice.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    input_path = tmp_path / "report.docx"
    input_path.write_text("document", encoding="utf-8")
    output_path = tmp_path / "exports" / "final.pdf"
    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="docx",
        format_out="pdf",
        engine="libreoffice",
    )

    await LibreOfficeEngine().convert(task)

    assert task.progress == 1.0
    assert output_path.read_text(encoding="utf-8") == "pdf-data"
    assert any("Running: libreoffice --headless" in line for line in task.log)
    assert "converted" in task.log


def test_libreoffice_supports_text_document_outputs() -> None:
    engine = LibreOfficeEngine()

    for fmt_out in {"docx", "odt", "rtf", "html", "epub", "txt", "pdf"}:
        assert engine.supports("docx", fmt_out), f"docx -> {fmt_out}"
        assert engine.supports("odt", fmt_out), f"odt -> {fmt_out}"


def test_libreoffice_supports_spreadsheet_outputs() -> None:
    engine = LibreOfficeEngine()

    for fmt_out in {"xlsx", "ods", "csv", "html", "pdf"}:
        assert engine.supports("xlsx", fmt_out), f"xlsx -> {fmt_out}"
        assert engine.supports("ods", fmt_out), f"ods -> {fmt_out}"


def test_libreoffice_supports_presentation_outputs() -> None:
    engine = LibreOfficeEngine()

    for fmt_out in {"pptx", "odp", "pdf"}:
        assert engine.supports("pptx", fmt_out)
        assert engine.supports("odp", fmt_out)


def test_libreoffice_rejects_cross_category_pairs() -> None:
    engine = LibreOfficeEngine()

    assert not engine.supports("docx", "csv")
    assert not engine.supports("xlsx", "epub")
    assert not engine.supports("pptx", "txt")


@pytest.mark.asyncio
async def test_libreoffice_engine_handles_non_pdf_output(tmp_path, monkeypatch) -> None:
    fake_libreoffice = tmp_path / "libreoffice"
    fake_libreoffice.write_text(
        "#!/bin/sh\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--outdir\" ]; then\n"
        "    shift\n"
        "    outdir=\"$1\"\n"
        "  elif [ \"$1\" = \"--convert-to\" ]; then\n"
        "    shift\n"
        "    target=\"$1\"\n"
        "  fi\n"
        "  input=\"$1\"\n"
        "  shift\n"
        "done\n"
        "base=$(basename \"$input\")\n"
        "stem=${base%.*}\n"
        "printf 'html-data' > \"$outdir/$stem.$target\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_libreoffice.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    input_path = tmp_path / "report.docx"
    input_path.write_text("doc", encoding="utf-8")
    output_path = tmp_path / "out" / "report.html"
    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="docx",
        format_out="html",
        engine="libreoffice",
    )

    await LibreOfficeEngine().convert(task)

    assert output_path.read_text(encoding="utf-8") == "html-data"
    assert any("--convert-to html" in line for line in task.log)


# ---- Bulk merge to PDF ----


def _install_fake_libreoffice(tmp_path, monkeypatch, template_pdf) -> None:
    """Stand up a fake `libreoffice` that copies a template PDF to outdir/stem.pdf."""
    fake = tmp_path / "libreoffice"
    fake.write_text(
        "#!/bin/sh\n"
        f"TEMPLATE='{template_pdf}'\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --outdir) shift; outdir=\"$1\";;\n"
        "    --convert-to) shift ;;\n"
        "    --headless|--nologo|--nofirststartwizard) ;;\n"
        "    -*) ;;\n"
        "    *) input=\"$1\" ;;\n"
        "  esac\n"
        "  shift\n"
        "done\n"
        "base=$(basename \"$input\")\n"
        "stem=${base%.*}\n"
        "cp \"$TEMPLATE\" \"$outdir/$stem.pdf\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{__import__('os').environ.get('PATH', '')}")


def _make_template_pdf(path, fitz, page_count: int = 1) -> None:
    document = fitz.open()
    for _ in range(page_count):
        document.new_page(width=200, height=200)
    document.save(str(path))
    document.close()


@pytest.mark.asyncio
async def test_bulk_merge_converts_each_input_then_concatenates(tmp_path, monkeypatch) -> None:
    fitz = pytest.importorskip("fitz")
    template = tmp_path / "_template.pdf"
    _make_template_pdf(template, fitz, page_count=1)
    _install_fake_libreoffice(tmp_path, monkeypatch, template)

    a = tmp_path / "a.docx"
    a.write_text("doc-a", encoding="utf-8")
    b = tmp_path / "b.docx"
    b.write_text("doc-b", encoding="utf-8")
    output = tmp_path / "out.pdf"

    task = Task(
        input_path=a,
        output_path=output,
        format_in="docx",
        format_out="pdf",
        engine="libreoffice",
        options={"operation": "bulk_merge_to_pdf"},
        extra_inputs=[b],
    )

    await LibreOfficeEngine().convert(task)

    merged = fitz.open(str(output))
    try:
        assert len(merged) == 2  # 1 page per source × 2 sources
    finally:
        merged.close()
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_bulk_merge_passes_through_existing_pdf_inputs(tmp_path, monkeypatch) -> None:
    fitz = pytest.importorskip("fitz")
    pdf_in = tmp_path / "first.pdf"
    _make_template_pdf(pdf_in, fitz, page_count=3)

    template = tmp_path / "_template.pdf"
    _make_template_pdf(template, fitz, page_count=1)
    _install_fake_libreoffice(tmp_path, monkeypatch, template)

    docx_in = tmp_path / "second.docx"
    docx_in.write_text("doc", encoding="utf-8")
    output = tmp_path / "out.pdf"

    task = Task(
        input_path=pdf_in,
        output_path=output,
        format_in="pdf",
        format_out="pdf",
        engine="libreoffice",
        options={"operation": "bulk_merge_to_pdf"},
        extra_inputs=[docx_in],
    )

    await LibreOfficeEngine().convert(task)

    merged = fitz.open(str(output))
    try:
        # 3 pages from PDF + 1 from DOCX
        assert len(merged) == 4
    finally:
        merged.close()


@pytest.mark.asyncio
async def test_bulk_merge_requires_at_least_two_inputs(tmp_path) -> None:
    only = tmp_path / "only.docx"
    only.write_text("doc", encoding="utf-8")

    task = Task(
        input_path=only,
        output_path=tmp_path / "out.pdf",
        format_in="docx",
        format_out="pdf",
        engine="libreoffice",
        options={"operation": "bulk_merge_to_pdf"},
    )

    with pytest.raises(RuntimeError, match="at least two"):
        await LibreOfficeEngine().convert(task)


# ---- PDF/A archival flag ----


@pytest.mark.asyncio
async def test_pdf_a_option_routes_through_writer_pdf_filter(tmp_path, monkeypatch) -> None:
    fake_libreoffice = tmp_path / "libreoffice"
    fake_libreoffice.write_text(
        "#!/bin/sh\n"
        "echo \"$@\" > \"$0.args\"\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --outdir) shift; outdir=\"$1\";;\n"
        "    --convert-to) shift; ;;\n"
        "    *) input=\"$1\" ;;\n"
        "  esac\n"
        "  shift\n"
        "done\n"
        "base=$(basename \"$input\")\n"
        "stem=${base%.*}\n"
        "printf 'pdf-a-data' > \"$outdir/$stem.pdf\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_libreoffice.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    src = tmp_path / "report.docx"
    src.write_text("doc", encoding="utf-8")
    out = tmp_path / "out.pdf"

    task = Task(
        input_path=src,
        output_path=out,
        format_in="docx",
        format_out="pdf",
        engine="libreoffice",
        options={"pdf_a": True},
    )

    await LibreOfficeEngine().convert(task)

    assert out.read_bytes() == b"pdf-a-data"
    args = (tmp_path / "libreoffice.args").read_text(encoding="utf-8")
    assert 'pdf:writer_pdf_Export:' in args
    assert 'SelectPdfVersion' in args


# ---- Slides to images ----


@pytest.mark.asyncio
async def test_slides_to_images_renders_each_page_to_png(tmp_path, monkeypatch) -> None:
    fitz = pytest.importorskip("fitz")
    template = tmp_path / "_template.pdf"
    _make_template_pdf(template, fitz, page_count=3)
    _install_fake_libreoffice(tmp_path, monkeypatch, template)

    src = tmp_path / "deck.pptx"
    src.write_text("ppt", encoding="utf-8")
    out_dir = tmp_path / "slides"

    task = Task(
        input_path=src,
        output_path=out_dir,
        format_in="pptx",
        format_out="folder",
        engine="libreoffice",
        options={"operation": "slides_to_images"},
    )

    await LibreOfficeEngine().convert(task)

    files = sorted(out_dir.glob("*.png"))
    assert [f.name for f in files] == ["deck-001.png", "deck-002.png", "deck-003.png"]
    # Each file should be a real PNG (PyMuPDF Pixmap.save produces a non-empty file)
    for f in files:
        assert f.stat().st_size > 0


@pytest.mark.asyncio
async def test_slides_to_images_supports_jpg_format(tmp_path, monkeypatch) -> None:
    fitz = pytest.importorskip("fitz")
    template = tmp_path / "_template.pdf"
    _make_template_pdf(template, fitz, page_count=2)
    _install_fake_libreoffice(tmp_path, monkeypatch, template)

    src = tmp_path / "deck.pptx"
    src.write_text("ppt", encoding="utf-8")
    out_dir = tmp_path / "slides"

    task = Task(
        input_path=src,
        output_path=out_dir,
        format_in="pptx",
        format_out="folder",
        engine="libreoffice",
        options={"operation": "slides_to_images", "slides_image_format": "jpg"},
    )

    await LibreOfficeEngine().convert(task)

    files = sorted(out_dir.glob("*.jpg"))
    assert [f.name for f in files] == ["deck-001.jpg", "deck-002.jpg"]


@pytest.mark.asyncio
async def test_slides_to_images_invalid_format_raises(tmp_path) -> None:
    src = tmp_path / "deck.pptx"
    src.write_text("ppt", encoding="utf-8")
    task = Task(
        input_path=src,
        output_path=tmp_path / "slides",
        format_in="pptx",
        format_out="folder",
        engine="libreoffice",
        options={"operation": "slides_to_images", "slides_image_format": "tiff"},
    )

    with pytest.raises(RuntimeError, match="slides_image_format"):
        await LibreOfficeEngine().convert(task)


# ---- Password-protected PDF export ----


@pytest.mark.asyncio
async def test_pdf_password_routes_through_writer_pdf_filter(tmp_path, monkeypatch) -> None:
    fake_libreoffice = tmp_path / "libreoffice"
    fake_libreoffice.write_text(
        "#!/bin/sh\n"
        "echo \"$@\" > \"$0.args\"\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --outdir) shift; outdir=\"$1\";;\n"
        "    --convert-to) shift; ;;\n"
        "    *) input=\"$1\" ;;\n"
        "  esac\n"
        "  shift\n"
        "done\n"
        "base=$(basename \"$input\")\n"
        "stem=${base%.*}\n"
        "printf 'pwd-data' > \"$outdir/$stem.pdf\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_libreoffice.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    src = tmp_path / "secret.docx"
    src.write_text("secret", encoding="utf-8")
    out = tmp_path / "out.pdf"

    task = Task(
        input_path=src,
        output_path=out,
        format_in="docx",
        format_out="pdf",
        engine="libreoffice",
        options={"pdf_password_user": "open-me", "pdf_password_owner": "edit-me"},
    )

    await LibreOfficeEngine().convert(task)

    args = (tmp_path / "libreoffice.args").read_text(encoding="utf-8")
    assert "EncryptFile" in args
    assert "DocumentOpenPassword" in args
    assert "open-me" in args
    assert "RestrictPermissions" in args
    assert "PermissionPassword" in args
    assert "edit-me" in args


@pytest.mark.asyncio
async def test_pdf_password_combines_with_pdf_a_flag(tmp_path, monkeypatch) -> None:
    fake_libreoffice = tmp_path / "libreoffice"
    fake_libreoffice.write_text(
        "#!/bin/sh\n"
        "echo \"$@\" > \"$0.args\"\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --outdir) shift; outdir=\"$1\";;\n"
        "    --convert-to) shift; ;;\n"
        "    *) input=\"$1\" ;;\n"
        "  esac\n"
        "  shift\n"
        "done\n"
        "base=$(basename \"$input\")\n"
        "stem=${base%.*}\n"
        "printf 'data' > \"$outdir/$stem.pdf\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_libreoffice.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    src = tmp_path / "doc.docx"
    src.write_text("x", encoding="utf-8")
    task = Task(
        input_path=src,
        output_path=tmp_path / "out.pdf",
        format_in="docx",
        format_out="pdf",
        engine="libreoffice",
        options={"pdf_a": True, "pdf_password_user": "p1"},
    )

    await LibreOfficeEngine().convert(task)
    args = (tmp_path / "libreoffice.args").read_text(encoding="utf-8")
    assert "SelectPdfVersion" in args
    assert "EncryptFile" in args
    assert "p1" in args
