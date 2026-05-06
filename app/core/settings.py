from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "trex-converter"
SETTINGS_PATH = CONFIG_DIR / "settings.json"


@dataclass(slots=True)
class Settings:
    output_dir: str = ""
    max_concurrency: int = 2
    default_image_quality: int = 82
    default_pdf_dpi: int = 200
    default_ocr_language: str = "eng"
    default_video_crf: int = 0
    default_video_preset: str = "medium"
    default_audio_bitrate: str = "192k"

    @classmethod
    def load(cls, path: Path = SETTINGS_PATH) -> "Settings":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        valid_keys = {field.name for field in fields(cls)}
        kwargs = {key: value for key, value in data.items() if key in valid_keys}
        instance = cls()
        for key, value in kwargs.items():
            try:
                setattr(instance, key, value)
            except (TypeError, ValueError):
                continue
        return instance

    def save(self, path: Path = SETTINGS_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


_current: Settings | None = None


def get_settings() -> Settings:
    global _current
    if _current is None:
        _current = Settings.load()
    return _current


def set_settings(settings: Settings, *, persist: bool = True) -> Settings:
    global _current
    _current = settings
    if persist:
        settings.save()
    return settings


def reset_for_tests() -> None:
    """Reset the in-memory cache. Test helper only."""
    global _current
    _current = None
