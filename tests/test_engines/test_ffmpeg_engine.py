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
    # Wave 2 outputs: animated and still image from video
    assert engine.supports("mp4", "gif")
    assert engine.supports("mp4", "webp")
    assert engine.supports("mp4", "png")
    assert engine.supports("mov", "jpg")
    # but image inputs (still or animated) are not video sources
    assert not engine.supports("png", "mp4")
    assert not engine.supports("gif", "mp4")
    assert not engine.supports("webp", "mp4")


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


def test_supports_audio_to_audio_pairs() -> None:
    engine = FFmpegEngine()

    assert engine.supports("mp3", "mp3")
    assert engine.supports("flac", "wav")
    assert engine.supports("ogg", "opus")
    assert engine.supports("m4a", "mp3")
    assert engine.supports("mp4", "flac")  # extract from video
    assert engine.supports("webm", "ogg")


def test_volume_db_emits_filter_with_sign() -> None:
    command_up = _build({"volume_db": 6}, format_in="mp3", format_out="mp3")
    command_down = _build({"volume_db": -3.5}, format_in="mp3", format_out="mp3")

    af_up = command_up[command_up.index("-af") + 1]
    af_down = command_down[command_down.index("-af") + 1]
    assert af_up == "volume=+6dB"
    assert af_down == "volume=-3.5dB"


def test_volume_db_zero_does_not_emit_filter() -> None:
    command = _build({"volume_db": 0}, format_in="mp3", format_out="mp3")

    assert "-af" not in command


def test_fade_in_emits_afade() -> None:
    command = _build({"fade_in_duration": 2.5}, format_in="mp3", format_out="mp3")

    af = command[command.index("-af") + 1]
    assert af == "afade=t=in:st=0:d=2.5"


def test_fade_out_requires_start_when_duration_set() -> None:
    with pytest.raises(RuntimeError, match="fade_out_start"):
        _build({"fade_out_duration": 3}, format_in="mp3", format_out="mp3")


def test_fade_out_emits_afade_with_start() -> None:
    command = _build(
        {"fade_out_duration": 3, "fade_out_start": 117},
        format_in="mp3",
        format_out="mp3",
    )

    af = command[command.index("-af") + 1]
    assert af == "afade=t=out:st=117:d=3"


def test_loudnorm_appended_at_end_of_chain() -> None:
    command = _build(
        {"volume_db": 4, "loudnorm": True},
        format_in="mp3",
        format_out="mp3",
    )

    af = command[command.index("-af") + 1]
    chain = af.split(",")
    assert chain[0].startswith("volume=")
    assert chain[1].startswith("loudnorm=")


def test_audio_filter_chain_order() -> None:
    command = _build(
        {
            "speed": 1.25,
            "fade_in_duration": 1,
            "fade_out_duration": 2,
            "fade_out_start": 60,
            "volume_db": -2,
            "loudnorm": True,
        },
        format_in="mp3",
        format_out="mp3",
    )

    af = command[command.index("-af") + 1]
    chain = af.split(",")
    assert chain[0].startswith("atempo=")
    assert chain[1].startswith("afade=t=in")
    assert chain[2].startswith("afade=t=out")
    assert chain[3].startswith("volume=")
    assert chain[4].startswith("loudnorm=")


def test_audio_channels_emits_ac_flag() -> None:
    command = _build({"audio_channels": "1"}, format_in="mp3", format_out="mp3")

    assert command[command.index("-ac") + 1] == "1"


def test_sample_rate_emits_ar_flag() -> None:
    command = _build({"sample_rate": "44100"}, format_in="mp3", format_out="mp3")

    assert command[command.index("-ar") + 1] == "44100"


def test_vocal_remove_appends_pan_filter() -> None:
    command = _build({"vocal_remove": True}, format_in="mp3", format_out="mp3")

    af = command[command.index("-af") + 1]
    assert af == "pan=stereo|c0=c0-c1|c1=c1-c0"


def test_vocal_remove_chains_before_loudnorm() -> None:
    command = _build(
        {"vocal_remove": True, "loudnorm": True},
        format_in="mp3",
        format_out="mp3",
    )

    af = command[command.index("-af") + 1]
    chain = af.split(",")
    assert chain[0].startswith("pan=stereo")
    assert chain[1].startswith("loudnorm=")


def test_id3_metadata_options_pass_through() -> None:
    command = _build(
        {
            "id3_title": "Bohemian Rhapsody",
            "id3_artist": "Queen",
            "id3_album": "A Night at the Opera",
            "id3_year": "1975",
            "id3_genre": "Rock",
            "id3_track": "11/12",
        },
        format_in="mp3",
        format_out="mp3",
    )

    metadata_args: list[str] = []
    for index, arg in enumerate(command):
        if arg == "-metadata":
            metadata_args.append(command[index + 1])

    assert "title=Bohemian Rhapsody" in metadata_args
    assert "artist=Queen" in metadata_args
    assert "album=A Night at the Opera" in metadata_args
    # year is mapped to ffmpeg "date" key
    assert "date=1975" in metadata_args
    assert "genre=Rock" in metadata_args
    assert "track=11/12" in metadata_args


def test_id3_skips_empty_fields() -> None:
    command = _build(
        {"id3_title": "Only Title", "id3_artist": ""},
        format_in="mp3",
        format_out="mp3",
    )

    metadata_args = [
        command[index + 1] for index, arg in enumerate(command) if arg == "-metadata"
    ]
    assert metadata_args == ["title=Only Title"]


def test_gif_output_uses_palettegen_filter_complex() -> None:
    command = _build({}, format_in="mp4", format_out="gif")

    assert "-filter_complex" in command
    fc = command[command.index("-filter_complex") + 1]
    assert "palettegen=max_colors=256" in fc
    assert "paletteuse=" in fc
    assert "fps=12" in fc
    assert "scale=480:-1:flags=lanczos" in fc
    # GIF output should loop infinitely and drop audio
    assert "-loop" in command
    assert command[command.index("-loop") + 1] == "0"
    assert "-an" in command
    # GIF path bypasses default -vf/-af pipeline
    assert "-vf" not in command
    assert "-af" not in command


def test_gif_fps_and_width_overrides() -> None:
    command = _build(
        {"gif_fps": 24, "gif_width": 720},
        format_in="mp4",
        format_out="gif",
    )

    fc = command[command.index("-filter_complex") + 1]
    assert "fps=24" in fc
    assert "scale=720:-1:flags=lanczos" in fc


def test_gif_preserves_video_filter_chain_before_palette() -> None:
    command = _build(
        {"gif_fps": 10, "crop": "320x240+0+0", "rotation_degrees": 90},
        format_in="mp4",
        format_out="gif",
    )

    fc = command[command.index("-filter_complex") + 1]
    # crop and transpose appear BEFORE the palette pipeline (fps=10)
    crop_idx = fc.index("crop=320:240:0:0")
    transpose_idx = fc.index("transpose=1")
    fps_idx = fc.index("fps=10")
    assert crop_idx < transpose_idx < fps_idx


def test_webp_output_uses_libwebp_codec_and_loop() -> None:
    command = _build({}, format_in="mp4", format_out="webp")

    vf = command[command.index("-vf") + 1]
    assert "fps=15" in vf
    assert "scale=480:-1:flags=lanczos" in vf
    assert command[command.index("-c:v") + 1] == "libwebp"
    assert command[command.index("-loop") + 1] == "0"
    assert "-an" in command


def test_webp_quality_override() -> None:
    command = _build({"webp_quality": 90}, format_in="mp4", format_out="webp")

    assert command[command.index("-q:v") + 1] == "90"


def test_thumbnail_grid_filter_uses_select_scale_tile() -> None:
    command = _build(
        {"thumbnail_grid": True, "thumbnail_rows": 3, "thumbnail_cols": 5,
         "thumbnail_interval": 30, "thumbnail_tile_width": 200},
        format_in="mp4",
        format_out="png",
    )

    vf = command[command.index("-vf") + 1]
    assert "select='not(mod(n\\,30))'" in vf
    assert "scale=200:-1" in vf
    assert "tile=5x3" in vf
    assert "-frames:v" in command
    assert command[command.index("-frames:v") + 1] == "1"
    assert "-an" in command


def test_image_output_without_thumbnail_grid_uses_single_frame() -> None:
    command = _build({}, format_in="mp4", format_out="jpg")

    # No thumbnail_grid → no select/tile filter, just single frame
    assert "-frames:v" in command
    assert command[command.index("-frames:v") + 1] == "1"
    assert "-an" in command
    assert "-vf" not in command  # no filter chain by default


def test_image_output_respects_video_filter_chain() -> None:
    command = _build(
        {"resolution_preset": "720p"},
        format_in="mp4",
        format_out="png",
    )

    vf = command[command.index("-vf") + 1]
    assert vf == "scale=1280:-2"
    assert "-frames:v" in command


def test_logo_overlay_emits_filter_complex_with_overlay() -> None:
    command = _build(
        {"logo_path": "/tmp/logo.png"},
        format_in="mp4",
        format_out="mp4",
    )

    # Second -i should be the logo
    inputs = [command[i + 1] for i, arg in enumerate(command) if arg == "-i"]
    assert inputs == ["in.mp4", "/tmp/logo.png"]
    fc = command[command.index("-filter_complex") + 1]
    assert "[1:v]scale=120:-1" in fc
    assert "[logo]" in fc
    assert "overlay=W-w-20:H-h-20" in fc
    assert "[vout]" in fc
    # Map both video and optional audio
    map_args = [command[i + 1] for i, arg in enumerate(command) if arg == "-map"]
    assert "[vout]" in map_args
    assert "0:a?" in map_args


def test_logo_overlay_position_and_opacity() -> None:
    command = _build(
        {"logo_path": "/tmp/logo.png", "logo_position": "northwest",
         "logo_width": 200, "logo_opacity": 50},
        format_in="mp4",
        format_out="mp4",
    )

    fc = command[command.index("-filter_complex") + 1]
    assert "scale=200:-1" in fc
    assert "colorchannelmixer=aa=0.50" in fc
    assert "overlay=20:20" in fc


def test_logo_overlay_chains_existing_video_filters() -> None:
    command = _build(
        {"logo_path": "/tmp/logo.png", "resolution_preset": "1080p",
         "rotation_degrees": 90},
        format_in="mp4",
        format_out="mp4",
    )

    fc = command[command.index("-filter_complex") + 1]
    # video chain processes [0:v] first, producing [v0], then logo overlays on [v0]
    assert fc.startswith("[0:v]")
    assert "transpose=1" in fc
    assert "scale=1920:-2" in fc
    assert "[v0]" in fc
    assert "[v0][logo]overlay=" in fc


def test_logo_overlay_skipped_for_audio_only_output() -> None:
    command = _build(
        {"logo_path": "/tmp/logo.png"},
        format_in="mp4",
        format_out="mp3",
    )

    # Audio-only output ignores logo overlay
    inputs = [command[i + 1] for i, arg in enumerate(command) if arg == "-i"]
    assert inputs == ["in.mp4"]
    assert "-filter_complex" not in command


def test_reverse_video_appends_reverse_and_areverse() -> None:
    command = _build({"reverse_video": True}, format_in="mp4", format_out="mp4")

    vf = command[command.index("-vf") + 1]
    assert vf == "reverse"
    af = command[command.index("-af") + 1]
    assert af == "areverse"


def test_reverse_video_chains_after_other_filters() -> None:
    command = _build(
        {"reverse_video": True, "resolution_preset": "720p"},
        format_in="mp4",
        format_out="mp4",
    )

    vf = command[command.index("-vf") + 1]
    chain = vf.split(",")
    assert chain[-1] == "reverse"
    assert chain[0] == "scale=1280:-2"


def test_subtitle_burn_in_for_srt_uses_subtitles_filter() -> None:
    command = _build(
        {"burn_subtitle_path": "/path/to/sub.srt"},
        format_in="mp4",
        format_out="mp4",
    )

    vf = command[command.index("-vf") + 1]
    assert vf.startswith("subtitles=")
    assert "/path/to/sub.srt" in vf or "/path/to/sub.srt".replace(":", "\\:") in vf


def test_subtitle_burn_in_for_ass_uses_ass_filter() -> None:
    command = _build(
        {"burn_subtitle_path": "/path/to/sub.ass"},
        format_in="mp4",
        format_out="mp4",
    )

    vf = command[command.index("-vf") + 1]
    assert vf.startswith("ass=")


def test_subtitle_burn_in_escapes_colons_in_path() -> None:
    command = _build(
        {"burn_subtitle_path": "C:/videos/sub.srt"},
        format_in="mp4",
        format_out="mp4",
    )

    vf = command[command.index("-vf") + 1]
    assert "C\\:/videos/sub.srt" in vf


def test_audio_output_skips_video_filters_but_keeps_audio_filters() -> None:
    command = _build(
        {
            "rotation_degrees": 90,
            "resolution_preset": "1080p",
            "watermark_text": "x",
            "volume_db": 5,
            "fade_in_duration": 1,
        },
        format_in="mp4",
        format_out="mp3",
    )

    assert "-vf" not in command
    af = command[command.index("-af") + 1]
    assert "volume=" in af
    assert "afade=t=in" in af
