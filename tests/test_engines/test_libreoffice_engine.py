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


def test_libreoffice_supports_document_to_pdf_formats() -> None:
    engine = LibreOfficeEngine()

    assert engine.supports("docx", "pdf")
    assert engine.supports("xlsx", "pdf")
    assert engine.supports("pptx", "pdf")
    assert engine.supports("rtf", "pdf")
    assert not engine.supports("docx", "txt")
