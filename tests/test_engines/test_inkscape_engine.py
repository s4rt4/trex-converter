import os
from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.inkscape_engine import (
    InkscapeEngine,
    SUPPORTED_PAIRS,
    build_command,
)


def _build(format_out: str, options: dict | None = None) -> list[str]:
    task = Task(
        input_path=Path("/tmp/in.svg"),
        output_path=Path(f"/tmp/out.{format_out}"),
        format_in="svg",
        format_out=format_out,
        engine="inkscape",
        options=options or {},
    )
    return build_command(task)


def test_supports_pairs() -> None:
    engine = InkscapeEngine()

    assert engine.supports("svg", "png")
    assert engine.supports("svg", "pdf")
    assert engine.supports("svg", "svg")
    assert engine.supports("svg", "eps")
    assert engine.supports("svg", "ps")
    assert engine.supports("svg", "emf")
    assert engine.supports("svg", "wmf")
    assert engine.supports("pdf", "svg")
    assert not engine.supports("png", "svg")
    assert not engine.supports("pdf", "png")
    assert not engine.supports("svg", "jpg")


def test_supported_pairs_constant_matches_engine() -> None:
    assert SUPPORTED_PAIRS == {
        ("svg", "png"),
        ("svg", "pdf"),
        ("svg", "svg"),
        ("svg", "eps"),
        ("svg", "ps"),
        ("svg", "emf"),
        ("svg", "wmf"),
        ("pdf", "svg"),
    }


def test_capabilities_require_inkscape_binary() -> None:
    caps = InkscapeEngine().capabilities

    assert caps.requires_binary == "inkscape"
    assert caps.supports_cancel is True


def test_rasterize_default_emits_export_type_png_and_filename() -> None:
    command = _build("png")

    assert command[0] == "inkscape"
    assert "--export-type=png" in command
    assert "--export-filename=/tmp/out.png" in command
    assert command[-1] == "/tmp/in.svg"
    # No size flags when no options
    assert not any(arg.startswith("--export-dpi") for arg in command)
    assert not any(arg.startswith("--export-width") for arg in command)
    assert not any(arg.startswith("--export-height") for arg in command)


def test_rasterize_with_dpi_emits_export_dpi_flag() -> None:
    command = _build("png", {"inkscape_dpi": 300})

    assert "--export-dpi=300" in command


def test_rasterize_with_width_and_height_emits_both_flags() -> None:
    command = _build("png", {"inkscape_width": 1024, "inkscape_height": 768})

    assert "--export-width=1024" in command
    assert "--export-height=768" in command


def test_rasterize_invalid_width_raises() -> None:
    with pytest.raises(RuntimeError, match="inkscape_width"):
        _build("png", {"inkscape_width": 0})


def test_rasterize_invalid_dpi_raises() -> None:
    with pytest.raises(RuntimeError, match="inkscape_dpi"):
        _build("png", {"inkscape_dpi": -50})


def test_pdf_export_uses_export_type_pdf() -> None:
    command = _build("pdf")

    assert "--export-type=pdf" in command
    assert "--export-filename=/tmp/out.pdf" in command
    # PDF export should not emit raster-specific flags
    assert not any(arg.startswith("--export-dpi") for arg in command)
    assert "--export-area-drawing" not in command


def test_svg_cleanup_default_emits_plain_svg_and_vacuum_defs() -> None:
    command = _build("svg")

    assert "--export-type=svg" in command
    assert "--export-plain-svg" in command
    assert "--vacuum-defs" in command
    # cleanup must NOT crop to drawing
    assert "--export-area-drawing" not in command


def test_svg_trim_emits_export_area_drawing_plus_plain_svg() -> None:
    command = _build("svg", {"operation": "trim"})

    assert "--export-area-drawing" in command
    assert "--export-plain-svg" in command
    assert "--vacuum-defs" in command


def test_svg_unknown_operation_raises() -> None:
    with pytest.raises(RuntimeError, match="Unsupported SVG operation"):
        _build("svg", {"operation": "magic"})


def test_unsupported_input_format_raises_in_builder() -> None:
    task = Task(
        input_path=Path("/tmp/in.png"),
        output_path=Path("/tmp/out.svg"),
        format_in="png",
        format_out="svg",
        engine="inkscape",
    )
    with pytest.raises(RuntimeError, match="Unsupported Inkscape pair"):
        build_command(task)


def test_eps_export_uses_export_type_eps() -> None:
    command = _build("eps")

    assert "--export-type=eps" in command
    assert "--export-filename=/tmp/out.eps" in command
    assert not any(arg.startswith("--export-ps-level") for arg in command)


def test_ps_export_uses_export_type_ps() -> None:
    command = _build("ps")

    assert "--export-type=ps" in command


def test_ps_level_option_emits_export_ps_level_flag() -> None:
    command = _build("ps", {"inkscape_ps_level": 2})

    assert "--export-ps-level=2" in command


def test_eps_level_3_also_works() -> None:
    command = _build("eps", {"inkscape_ps_level": 3})

    assert "--export-ps-level=3" in command


def test_invalid_ps_level_raises() -> None:
    with pytest.raises(RuntimeError, match="inkscape_ps_level"):
        _build("ps", {"inkscape_ps_level": 4})


def test_emf_export_uses_export_type_emf() -> None:
    command = _build("emf")

    assert "--export-type=emf" in command


def test_wmf_export_uses_export_type_wmf() -> None:
    command = _build("wmf")

    assert "--export-type=wmf" in command


def test_text_to_path_emits_flag_for_pdf() -> None:
    command = _build("pdf", {"text_to_path": True})

    assert "--export-text-to-path" in command


def test_text_to_path_emits_flag_for_eps() -> None:
    command = _build("eps", {"text_to_path": True})

    assert "--export-text-to-path" in command


def test_text_to_path_emits_flag_for_svg_cleanup() -> None:
    command = _build("svg", {"text_to_path": True})

    assert "--export-text-to-path" in command


def test_text_to_path_omitted_by_default() -> None:
    assert "--export-text-to-path" not in _build("pdf")
    assert "--export-text-to-path" not in _build("eps")


def test_text_to_path_not_emitted_for_emf() -> None:
    # EMF/WMF do not support text-to-path, builder must not emit the flag.
    command = _build("emf", {"text_to_path": True})

    assert "--export-text-to-path" not in command


def test_pdf_to_svg_emits_export_type_svg_and_plain_svg() -> None:
    task = Task(
        input_path=Path("/tmp/in.pdf"),
        output_path=Path("/tmp/out.svg"),
        format_in="pdf",
        format_out="svg",
        engine="inkscape",
    )
    command = build_command(task)

    assert "--export-type=svg" in command
    assert "--export-plain-svg" in command
    assert command[-1] == "/tmp/in.pdf"
    # No --pages by default (means page 1)
    assert not any(arg.startswith("--pages=") for arg in command)


def test_pdf_to_svg_with_page_option_emits_pages_flag() -> None:
    task = Task(
        input_path=Path("/tmp/in.pdf"),
        output_path=Path("/tmp/out.svg"),
        format_in="pdf",
        format_out="svg",
        engine="inkscape",
        options={"inkscape_pdf_page": 3},
    )
    command = build_command(task)

    assert "--pages=3" in command


def test_pdf_page_zero_or_negative_raises() -> None:
    task = Task(
        input_path=Path("/tmp/in.pdf"),
        output_path=Path("/tmp/out.svg"),
        format_in="pdf",
        format_out="svg",
        engine="inkscape",
        options={"inkscape_pdf_page": 0},
    )
    with pytest.raises(RuntimeError, match="inkscape_pdf_page"):
        build_command(task)


@pytest.mark.asyncio
async def test_convert_rejects_unsupported_pair(tmp_path) -> None:
    input_path = tmp_path / "in.svg"
    input_path.write_text("<svg/>", encoding="utf-8")

    task = Task(
        input_path=input_path,
        output_path=tmp_path / "out.jpg",
        format_in="svg",
        format_out="jpg",
        engine="inkscape",
    )
    with pytest.raises(RuntimeError, match="Unsupported SVG conversion"):
        await InkscapeEngine().convert(task)


@pytest.mark.asyncio
async def test_convert_invokes_inkscape_subprocess(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "inkscape"
    fake.write_text(
        "#!/bin/sh\n"
        "OUT=\"\"\n"
        "for arg in \"$@\"; do\n"
        "  case \"$arg\" in\n"
        "    --export-filename=*) OUT=\"${arg#--export-filename=}\" ;;\n"
        "  esac\n"
        "done\n"
        "echo 'fake-png' > \"$OUT\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.svg"
    input_path.write_text("<svg/>", encoding="utf-8")
    output_path = tmp_path / "out.png"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="svg",
        format_out="png",
        engine="inkscape",
        options={"inkscape_dpi": 300},
    )

    await InkscapeEngine().convert(task)

    assert output_path.read_text(encoding="utf-8").strip() == "fake-png"
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_convert_propagates_inkscape_failure(tmp_path, monkeypatch) -> None:
    fake = tmp_path / "inkscape"
    fake.write_text(
        "#!/bin/sh\necho 'boom' >&2\nexit 1\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.svg"
    input_path.write_text("<svg/>", encoding="utf-8")

    task = Task(
        input_path=input_path,
        output_path=tmp_path / "out.png",
        format_in="svg",
        format_out="png",
        engine="inkscape",
    )
    with pytest.raises(RuntimeError, match="inkscape exited"):
        await InkscapeEngine().convert(task)


@pytest.mark.asyncio
async def test_convert_raises_when_inkscape_succeeds_but_no_output(
    tmp_path, monkeypatch
) -> None:
    fake = tmp_path / "inkscape"
    # Exit 0 but never create the output file
    fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")

    input_path = tmp_path / "in.svg"
    input_path.write_text("<svg/>", encoding="utf-8")

    task = Task(
        input_path=input_path,
        output_path=tmp_path / "out.png",
        format_in="svg",
        format_out="png",
        engine="inkscape",
    )
    with pytest.raises(RuntimeError, match="did not produce expected output"):
        await InkscapeEngine().convert(task)
