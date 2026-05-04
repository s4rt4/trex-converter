from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.ffmpeg_engine import FFmpegEngine


@pytest.mark.asyncio
async def test_ffmpeg_engine_runs_subprocess_and_updates_progress(tmp_path, monkeypatch) -> None:
    fake_ffmpeg = tmp_path / "ffmpeg"
    fake_ffmpeg.write_text(
        "#!/bin/sh\n"
        "echo 'Duration: 00:00:10.00, start: 0.000000' >&2\n"
        "echo 'out_time_ms=5000000' >&2\n"
        "echo 'progress=end' >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ffmpeg.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    task = Task(
        input_path=Path("input.mp4"),
        output_path=Path("output.mp3"),
        format_in="mp4",
        format_out="mp3",
        engine="ffmpeg",
        options={"bitrate": "192k"},
    )

    await FFmpegEngine().convert(task)

    assert task.progress == 1.0
    assert any("Running: ffmpeg" in line for line in task.log)


def _build(options: dict, *, format_in: str = "mp4", format_out: str = "mp4") -> list[str]:
    task = Task(
        input_path=Path("in." + format_in),
        output_path=Path("out." + format_out),
        format_in=format_in,
        format_out=format_out,
        engine="ffmpeg",
        options=options,
    )
    return FFmpegEngine()._build_command(task)


def test_supports_video_to_video_and_extract() -> None:
    engine = FFmpegEngine()

    assert engine.supports("mp4", "mp4")
    assert engine.supports("mp4", "webm")
    assert engine.supports("mov", "mkv")
    assert engine.supports("mp4", "mp3")
    assert engine.supports("mkv", "wav")
    assert not engine.supports("mp4", "png")
    assert not engine.supports("png", "mp4")


def test_default_command_has_no_filters() -> None:
    command = _build({})

    assert "-vf" not in command
    assert "-af" not in command
    assert "-ss" not in command
    assert "-to" not in command
    # always-present scaffolding
    assert command[0] == "ffmpeg"
    assert "-i" in command
    assert "-progress" in command


def test_trim_options_inserted_after_input() -> None:
    command = _build({"trim_start": "00:00:05", "trim_end": "00:00:25"})

    assert "-ss" in command
    assert command[command.index("-ss") + 1] == "00:00:05"
    assert "-to" in command
    assert command[command.index("-to") + 1] == "00:00:25"


def test_resolution_preset_emits_scale_filter() -> None:
    command = _build({"resolution_preset": "720p"})

    vf = command[command.index("-vf") + 1]
    assert vf == "scale=1280:-2"


def test_unknown_resolution_preset_raises() -> None:
    with pytest.raises(RuntimeError, match="Unknown resolution preset"):
        _build({"resolution_preset": "8k"})


def test_rotation_90_emits_transpose() -> None:
    command = _build({"rotation_degrees": 90})

    vf = command[command.index("-vf") + 1]
    assert vf == "transpose=1"


def test_rotation_180_chains_two_transposes() -> None:
    command = _build({"rotation_degrees": 180})

    vf = command[command.index("-vf") + 1]
    assert vf == "transpose=2,transpose=2"


def test_rotation_270_emits_ccw_transpose() -> None:
    command = _build({"rotation_degrees": 270})

    vf = command[command.index("-vf") + 1]
    assert vf == "transpose=2"


def test_invalid_rotation_raises() -> None:
    with pytest.raises(RuntimeError, match="multiple of 90"):
        _build({"rotation_degrees": 45})


def test_flip_horizontal_and_vertical_chain() -> None:
    command = _build({"flip_horizontal": True, "flip_vertical": True})

    vf = command[command.index("-vf") + 1]
    assert vf == "hflip,vflip"


def test_crop_free_syntax_converts_to_colon_form() -> None:
    command = _build({"crop": "640x480+10+20"})

    vf = command[command.index("-vf") + 1]
    assert vf == "crop=640:480:10:20"


def test_crop_colon_syntax_passes_through() -> None:
    command = _build({"crop": "iw/2:ih/2:0:0"})

    vf = command[command.index("-vf") + 1]
    assert vf == "crop=iw/2:ih/2:0:0"


def test_invalid_crop_spec_raises() -> None:
    with pytest.raises(RuntimeError, match="Invalid crop spec"):
        _build({"crop": "garbage"})


def test_filter_chain_orders_crop_transpose_flip_scale_setpts() -> None:
    command = _build(
        {
            "crop": "640x480+0+0",
            "rotation_degrees": 90,
            "flip_horizontal": True,
            "resolution_preset": "1080p",
            "speed": 2.0,
        }
    )

    vf = command[command.index("-vf") + 1]
    chain = vf.split(",")
    assert chain[0].startswith("crop=")
    assert chain[1].startswith("transpose=")
    assert chain[2] == "hflip"
    assert chain[3].startswith("scale=")
    assert chain[4].startswith("setpts=")


def test_speed_emits_setpts_and_atempo() -> None:
    command = _build({"speed": 1.5})

    vf = command[command.index("-vf") + 1]
    assert vf.startswith("setpts=")
    af = command[command.index("-af") + 1]
    assert af == "atempo=1.500000"


def test_speed_out_of_range_raises() -> None:
    with pytest.raises(RuntimeError, match="speed must be between"):
        _build({"speed": 3.0})


def test_speed_one_is_noop() -> None:
    command = _build({"speed": 1.0})

    assert "-vf" not in command
    assert "-af" not in command


def test_crf_forces_libx264_when_no_codec_set() -> None:
    command = _build({"crf": 23})

    assert "-c:v" in command
    assert command[command.index("-c:v") + 1] == "libx264"
    assert command[command.index("-crf") + 1] == "23"


def test_crf_does_not_override_explicit_video_codec() -> None:
    command = _build({"crf": 28, "video_codec": "libx265"})

    codec_idx = command.index("-c:v")
    assert command[codec_idx + 1] == "libx265"
    # libx264 should not be added a second time
    assert command.count("-c:v") == 1


def test_crf_skipped_for_audio_output() -> None:
    command = _build({"crf": 23}, format_in="mp4", format_out="mp3")

    assert "-crf" not in command


def test_compress_preset_emitted() -> None:
    command = _build({"crf": 22, "compress_preset": "veryfast"})

    assert command[command.index("-preset") + 1] == "veryfast"


def test_unknown_compress_preset_raises() -> None:
    with pytest.raises(RuntimeError, match="Unknown compress preset"):
        _build({"compress_preset": "warpspeed"})


def test_audio_only_output_skips_video_filters() -> None:
    command = _build(
        {"resolution_preset": "1080p", "rotation_degrees": 90},
        format_in="mp4",
        format_out="mp3",
    )

    assert "-vf" not in command
    assert "-vn" in command


def test_watermark_drawtext_uses_southeast_by_default() -> None:
    command = _build({"watermark_text": "DRAFT"})

    vf = command[command.index("-vf") + 1]
    assert vf.startswith("drawtext=text='DRAFT'")
    assert "x=w-text_w-20" in vf
    assert "y=h-text_h-20" in vf
    assert "fontcolor=white@0.60" in vf


def test_watermark_position_and_opacity_apply() -> None:
    command = _build(
        {
            "watermark_text": "Top",
            "watermark_position": "north",
            "watermark_size": 64,
            "watermark_opacity": 25,
        }
    )

    vf = command[command.index("-vf") + 1]
    assert "x=(w-text_w)/2" in vf
    assert "y=20" in vf
    assert "fontsize=64" in vf
    assert "fontcolor=white@0.25" in vf


def test_watermark_text_escapes_quotes_and_backslashes() -> None:
    command = _build({"watermark_text": r"O'Reilly \ Co"})

    vf = command[command.index("-vf") + 1]
    assert r"text='O\'Reilly \\ Co'" in vf


def test_watermark_unknown_position_raises() -> None:
    with pytest.raises(RuntimeError, match="Unknown watermark position"):
        _build({"watermark_text": "x", "watermark_position": "middle"})


def test_bitrate_and_codec_options_still_apply() -> None:
    command = _build(
        {"bitrate": "192k", "audio_codec": "aac", "video_codec": "libx264"},
        format_in="mp4",
        format_out="mp4",
    )

    assert command[command.index("-b:a") + 1] == "192k"
    assert command[command.index("-c:a") + 1] == "aac"
    assert command[command.index("-c:v") + 1] == "libx264"


def test_audio_filter_set_only_when_speed_changes() -> None:
    command = _build({"watermark_text": "x"})

    assert "-af" not in command
