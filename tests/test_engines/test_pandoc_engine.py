import os
from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.pandoc_engine import (
    PANDOC_INPUT_FORMAT,
    PANDOC_OUTPUT_FORMAT,
    PandocEngine,
    SUPPORTED_PAIRS,
    build_command,
)


def _build(format_in: str, format_out: str, options: dict | None = None) -> list[str]:
    task = Task(
        input_path=Path(f"/tmp/in.{format_in}"),
        output_path=Path(f"/tmp/out.{format_out}"),
        format_in=format_in,
        format_out=format_out,
        engine="pandoc",
        options=options or {},
    )
    return build_command(task)


def test_supports_common_ebook_pairs() -> None:
    engine = PandocEngine()

    assert engine.supports("md", "epub")
    assert engine.supports("epub", "md")
    assert engine.supports("docx", "html")
    assert engine.supports("rst", "latex")
    assert engine.supports("html", "docx")
    assert engine.supports("epub", "txt")


def test_supports_rejects_unknown_extension() -> None:
    engine = PandocEngine()

    assert not engine.supports("xyz", "epub")
    assert not engine.supports("md", "xyz")


def test_aliases_share_pandoc_format_so_self_pair_is_skipped() -> None:
    # md and markdown map to the same pandoc format, so md→markdown is not
    # a real conversion and must not appear in SUPPORTED_PAIRS.
    assert ("md", "markdown") not in SUPPORTED_PAIRS
    assert ("markdown", "md") not in SUPPORTED_PAIRS
    assert ("latex", "tex") not in SUPPORTED_PAIRS
    assert ("html", "htm") not in SUPPORTED_PAIRS


def test_capabilities_require_pandoc_binary() -> None:
    caps = PandocEngine().capabilities

    assert caps.requires_binary == "pandoc"
    assert caps.supports_cancel is True


def test_format_aliases_resolve_to_pandoc_names() -> None:
    assert PANDOC_INPUT_FORMAT["md"] == "markdown"
    assert PANDOC_INPUT_FORMAT["markdown"] == "markdown"
    assert PANDOC_INPUT_FORMAT["latex"] == "latex"
    assert PANDOC_INPUT_FORMAT["tex"] == "latex"
    assert PANDOC_OUTPUT_FORMAT["txt"] == "plain"


def test_build_command_basic_md_to_epub() -> None:
    command = _build("md", "epub")

    assert command[0] == "pandoc"
    assert command[command.index("--from") + 1] == "markdown"
    assert command[command.index("--to") + 1] == "epub"
    assert command[command.index("--output") + 1] == "/tmp/out.epub"
    assert command[-1] == "/tmp/in.md"


def test_build_command_html_output_emits_standalone() -> None:
    command = _build("md", "html")

    assert "--standalone" in command


def test_build_command_latex_output_emits_standalone() -> None:
    command = _build("md", "latex")

    assert "--standalone" in command


def test_build_command_docx_output_does_not_force_standalone() -> None:
    # Pandoc auto-applies standalone for binary formats; we don't double up.
    command = _build("md", "docx")

    assert "--standalone" not in command


def test_metadata_options_emit_metadata_flags() -> None:
    command = _build(
        "md",
        "epub",
        {
            "ebook_title": "My Book",
            "ebook_author": "Jane Doe",
            "ebook_language": "en",
        },
    )

    metadata_pairs = [
        command[i + 1]
        for i, arg in enumerate(command)
        if arg == "--metadata"
    ]
    assert "title=My Book" in metadata_pairs
    assert "author=Jane Doe" in metadata_pairs
    assert "lang=en" in metadata_pairs


def test_table_of_contents_flag() -> None:
    command = _build("md", "epub", {"pandoc_table_of_contents": True})

    assert "--toc" in command


def test_self_contained_only_for_html() -> None:
    html_command = _build("md", "html", {"pandoc_self_contained": True})
    epub_command = _build("md", "epub", {"pandoc_self_contained": True})

    assert "--embed-resources" in html_command
    assert "--embed-resources" not in epub_command


def test_extra_args_append_to_command() -> None:
    command = _build("md", "html", {"pandoc_extra_args": ["--mathjax", "--ascii"]})

    assert "--mathjax" in command
    assert "--ascii" in command


def test_extra_args_string_split_on_spaces() -> None:
    command = _build("md", "html", {"pandoc_extra_args": "--mathjax --ascii"})

    assert "--mathjax" in command
    assert "--ascii" in command


def test_build_command_unsupported_input_raises() -> None:
    task = Task(
        input_path=Path("/tmp/in.xyz"),
        output_path=Path("/tmp/out.epub"),
        format_in="xyz",
        format_out="epub",
        engine="pandoc",
    )
    with pytest.raises(RuntimeError, match="Unsupported Pandoc input format"):
        build_command(task)


@pytest.mark.asyncio
async def test_convert_rejects_unsupported_pair(tmp_path) -> None:
    src = tmp_path / "in.xyz"
    src.write_text("hello", encoding="utf-8")
    task = Task(
        input_path=src,
        output_path=tmp_path / "out.epub",
        format_in="xyz",
        format_out="epub",
        engine="pandoc",
    )
    with pytest.raises(RuntimeError, match="Unsupported Pandoc conversion"):
        await PandocEngine().convert(task)


@pytest.mark.asyncio
async def test_convert_invokes_pandoc_subprocess(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "pandoc"
    fake.write_text(
        "#!/bin/sh\n"
        "OUT=\"\"\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--output\" ]; then OUT=\"$2\"; shift 2; continue; fi\n"
        "  shift\n"
        "done\n"
        "echo 'fake-output' > \"$OUT\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.md"
    src.write_text("# hello", encoding="utf-8")
    out = tmp_path / "out.epub"

    task = Task(
        input_path=src,
        output_path=out,
        format_in="md",
        format_out="epub",
        engine="pandoc",
        options={"ebook_title": "T"},
    )
    await PandocEngine().convert(task)

    assert out.read_text(encoding="utf-8").strip() == "fake-output"
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_convert_propagates_pandoc_failure(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "pandoc"
    fake.write_text(
        "#!/bin/sh\necho 'bad input' >&2\nexit 1\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.md"
    src.write_text("# hi", encoding="utf-8")

    task = Task(
        input_path=src,
        output_path=tmp_path / "out.epub",
        format_in="md",
        format_out="epub",
        engine="pandoc",
    )
    with pytest.raises(RuntimeError, match="pandoc exited"):
        await PandocEngine().convert(task)


@pytest.mark.asyncio
async def test_convert_raises_when_pandoc_succeeds_but_no_output(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "pandoc"
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    src = tmp_path / "in.md"
    src.write_text("# hi", encoding="utf-8")

    task = Task(
        input_path=src,
        output_path=tmp_path / "out.epub",
        format_in="md",
        format_out="epub",
        engine="pandoc",
    )
    with pytest.raises(RuntimeError, match="did not produce expected output"):
        await PandocEngine().convert(task)
