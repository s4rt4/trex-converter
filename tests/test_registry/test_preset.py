from pathlib import Path

from app.core.preset import load_preset


def test_load_builtin_preset() -> None:
    preset = load_preset(Path("presets/mp3-high-quality.toml"))

    assert preset.name == "MP3 High Quality"
    assert preset.format_in == "mp4"
    assert preset.options["bitrate"] == "320k"
