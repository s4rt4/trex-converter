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
