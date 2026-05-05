from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.imagemagick_engine import ImageMagickEngine


@pytest.mark.asyncio
async def test_imagemagick_engine_runs_subprocess(tmp_path, monkeypatch) -> None:
    fake_magick = tmp_path / "magick"
    fake_magick.write_text(
        "#!/bin/sh\n"
        "echo converted >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_magick.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    task = Task(
        input_path=Path("input.png"),
        output_path=Path("output.webp"),
        format_in="png",
        format_out="webp",
        engine="imagemagick",
        options={"quality": 82, "strip": True, "resize": "1280x1280>"},
    )

    await ImageMagickEngine().convert(task)

    assert task.progress == 1.0
    assert any("Running: magick input.png -resize 1280x1280> -strip -quality 82 output.webp" in line for line in task.log)
    assert "converted" in task.log


def test_imagemagick_supports_registered_pairs() -> None:
    engine = ImageMagickEngine()

    assert engine.supports("png", "webp")
    assert engine.supports("png", "jpeg")
    assert engine.supports("png", "avif")
    assert engine.supports("webp", "tiff")
    assert not engine.supports("mp4", "png")


def _build(options: dict, format_out: str = "webp") -> list[str]:
    task = Task(
        input_path=Path("input.png"),
        output_path=Path(f"output.{format_out}"),
        format_in="png",
        format_out=format_out,
        engine="imagemagick",
        options=options,
    )
    return ImageMagickEngine()._build_command(task)


def test_transform_options_emit_expected_args() -> None:
    command = _build(
        {
            "rotate": 90,
            "flip": True,
            "flop": True,
            "auto_trim": True,
            "crop_aspect": "16:9",
            "crop": "200x100+10+5",
            "density": 300,
        }
    )

    assert command[command.index("input.png") - 2 : command.index("input.png")] == [
        "-density",
        "300",
    ]
    assert "-rotate" in command and command[command.index("-rotate") + 1] == "90"
    assert "-flip" in command
    assert "-flop" in command
    assert "-trim" in command
    assert "-crop" in command
    crop_indices = [i for i, value in enumerate(command) if value == "-crop"]
    assert command[crop_indices[0] + 1] == "16:9"
    assert command[crop_indices[1] + 1] == "200x100+10+5"


def test_resize_modes_translate_correctly() -> None:
    longest = _build({"resize": "1024", "resize_mode": "longest_edge"})
    assert "1024x1024>" in longest

    percent = _build({"resize": "75", "resize_mode": "percent"})
    assert "75%" in percent

    megapixel = _build({"resize": "2", "resize_mode": "megapixel"})
    assert "@2000000" in megapixel

    dimension = _build({"resize": "1280x720>", "resize_mode": "dimension"})
    assert "1280x720>" in dimension


def test_color_options_emit_expected_args() -> None:
    command = _build(
        {
            "grayscale": True,
            "sepia": 80,
            "negate": True,
            "normalize": True,
            "brightness": 10,
            "contrast": -5,
            "gamma": 1.4,
        }
    )

    assert "-colorspace" in command and command[command.index("-colorspace") + 1] == "Gray"
    assert "-sepia-tone" in command and command[command.index("-sepia-tone") + 1] == "80%"
    assert "-negate" in command
    assert "-normalize" in command
    assert "-brightness-contrast" in command
    assert command[command.index("-brightness-contrast") + 1] == "10x-5"
    assert "-gamma" in command and command[command.index("-gamma") + 1] == "1.4"


def test_filter_and_border_options_emit_expected_args() -> None:
    command = _build(
        {
            "blur": 1.5,
            "sharpen": 0.8,
            "denoise": True,
            "vignette": True,
            "border_size": 8,
            "border_color": "#ffaa00",
            "frame_size": 4,
        }
    )

    assert "-blur" in command and command[command.index("-blur") + 1] == "0x1.5"
    assert "-sharpen" in command and command[command.index("-sharpen") + 1] == "0x0.8"
    assert "-enhance" in command
    assert "-vignette" in command
    assert "-bordercolor" in command
    assert command[command.index("-bordercolor") + 1] == "#ffaa00"
    assert command[command.index("-border") + 1] == "8x8"
    assert command[command.index("-frame") + 1] == "4x4"


def test_watermark_options_emit_expected_args() -> None:
    command = _build(
        {
            "watermark_text": "T-Rex",
            "watermark_position": "northwest",
            "watermark_opacity": 40,
            "watermark_size": 24,
        }
    )

    assert "-annotate" in command
    annotate_index = command.index("-annotate")
    assert command[annotate_index + 1] == "+12+12"
    assert command[annotate_index + 2] == "T-Rex"
    assert "-pointsize" in command and command[command.index("-pointsize") + 1] == "24"
    fill_index = command.index("-fill")
    assert command[fill_index + 1] == "rgba(255,255,255,0.4)"
    gravity_indices = [i for i, value in enumerate(command) if value == "-gravity"]
    assert command[gravity_indices[0] + 1] == "northwest"


def test_ico_output_adds_auto_resize_when_no_resize() -> None:
    command = _build({}, format_out="ico")
    assert "-define" in command
    assert any("icon:auto-resize=" in arg for arg in command)


def test_ico_output_skips_auto_resize_when_resize_set() -> None:
    command = _build({"resize": "64x64"}, format_out="ico")
    assert not any(arg.startswith("icon:auto-resize=") for arg in command)


def test_invalid_crop_aspect_is_ignored() -> None:
    command = _build({"crop_aspect": "weird"})
    assert "-crop" not in command


def test_unset_options_produce_minimal_command() -> None:
    command = _build({})
    assert command == ["magick", "input.png", "output.webp"] or command == [
        "convert",
        "input.png",
        "output.webp",
    ]


# ---- Multi-input wave: montage ----


def _build_montage(options: dict, inputs: list[Path]) -> list[str]:
    task = Task(
        input_path=inputs[0],
        output_path=Path("out.png"),
        format_in="png",
        format_out="png",
        engine="imagemagick",
        options={**options, "operation": "montage"},
        extra_inputs=inputs[1:],
    )
    return ImageMagickEngine()._build_command(task)


def test_montage_uses_montage_subcommand_with_all_inputs() -> None:
    command = _build_montage(
        {},
        [Path("a.png"), Path("b.png"), Path("c.png"), Path("d.png")],
    )

    # binary may be either `magick montage` (v7) or `montage` (v6)
    assert command[0] in {"magick", "montage"}
    if command[0] == "magick":
        assert command[1] == "montage"
        body = command[2:]
    else:
        body = command[1:]

    # First N args are inputs in order
    assert body[:4] == ["a.png", "b.png", "c.png", "d.png"]
    # Tile auto -> 2x2 for 4 inputs
    assert "-tile" in body
    assert body[body.index("-tile") + 1] == "2x2"
    assert command[-1] == "out.png"


def test_montage_explicit_tile_geometry_and_background() -> None:
    command = _build_montage(
        {
            "montage_tile": "3x2",
            "montage_geometry": "150x150+10+10",
            "montage_background": "#0c2c55",
        },
        [Path("a.png"), Path("b.png")],
    )

    assert command[command.index("-tile") + 1] == "3x2"
    assert command[command.index("-geometry") + 1] == "150x150+10+10"
    assert command[command.index("-background") + 1] == "#0c2c55"


def test_montage_requires_at_least_two_inputs() -> None:
    with pytest.raises(RuntimeError, match="at least two"):
        _build_montage({}, [Path("only.png")])


def test_montage_invalid_tile_raises() -> None:
    with pytest.raises(RuntimeError, match="montage_tile"):
        _build_montage(
            {"montage_tile": "garbage"},
            [Path("a.png"), Path("b.png")],
        )


def test_montage_invalid_geometry_raises() -> None:
    with pytest.raises(RuntimeError, match="montage_geometry"):
        _build_montage(
            {"montage_geometry": "not-geometry"},
            [Path("a.png"), Path("b.png")],
        )


# ---- Image watermark (PNG overlay) ----


def test_watermark_image_appends_paren_block_and_composite() -> None:
    command = _build({"watermark_image_path": "/tmp/logo.png"})

    assert "(" in command
    assert ")" in command
    paren_open = command.index("(")
    paren_close = command.index(")")
    assert command[paren_open + 1] == "/tmp/logo.png"
    assert paren_close > paren_open
    # After ): gravity, geometry, compose, composite
    assert command[paren_close + 1] == "-gravity"
    assert command[command.index("-compose") + 1] == "over"
    assert "-composite" in command


def test_watermark_image_position_size_and_opacity() -> None:
    command = _build(
        {
            "watermark_image_path": "/tmp/logo.png",
            "watermark_image_position": "northwest",
            "watermark_image_width": 200,
            "watermark_image_opacity": 50,
            "watermark_image_margin_x": 12,
            "watermark_image_margin_y": 8,
        }
    )

    paren_open = command.index("(")
    paren_close = command.index(")")
    inside = command[paren_open + 1 : paren_close]
    assert "/tmp/logo.png" in inside
    assert inside[inside.index("-resize") + 1] == "200x"
    # Opacity multiplier applied via colorchannel evaluate
    assert "-evaluate" in inside
    assert inside[inside.index("multiply") + 1] == "0.5"

    assert command[command.index("-gravity") + 1] == "northwest"
    assert command[command.index("-geometry") + 1] == "+12+8"


def test_watermark_image_falls_back_to_text_position_when_image_position_missing() -> None:
    command = _build(
        {
            "watermark_image_path": "/tmp/logo.png",
            "watermark_position": "south",
        }
    )

    assert command[command.index("-gravity") + 1] == "south"


def test_watermark_image_full_opacity_skips_evaluate_block() -> None:
    command = _build({"watermark_image_path": "/tmp/logo.png"})

    paren_open = command.index("(")
    paren_close = command.index(")")
    inside = command[paren_open + 1 : paren_close]
    # Default opacity is 100 -> no alpha channel manipulation
    assert "-evaluate" not in inside
