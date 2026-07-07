from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from app.utils.paths import config_dir

# Single canonical config directory (~/.config/t-rex-converter), shared with
# the task database. Settings and presets used to live in a second dir
# (~/.config/trex-converter, no hyphen); migrate_legacy_config() folds that
# legacy location in on startup.
CONFIG_DIR = config_dir()
SETTINGS_PATH = CONFIG_DIR / "settings.json"

_LEGACY_CONFIG_DIR = Path.home() / ".config" / "trex-converter"


def migrate_legacy_config() -> None:
    """One-time move of settings + presets from the old config dir.

    Safe no-op when there's nothing to move (the common case). Never
    overwrites data already present at the canonical location.
    """
    if not _LEGACY_CONFIG_DIR.exists() or _LEGACY_CONFIG_DIR == CONFIG_DIR:
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    legacy_settings = _LEGACY_CONFIG_DIR / "settings.json"
    if legacy_settings.is_file() and not SETTINGS_PATH.exists():
        shutil.move(str(legacy_settings), str(SETTINGS_PATH))

    # Merge presets per file: an all-or-nothing move would strand every
    # legacy preset the moment anything creates the new presets dir first
    # (e.g. saving one preset in a fresh install before migration ran).
    legacy_presets = _LEGACY_CONFIG_DIR / "presets"
    new_presets = CONFIG_DIR / "presets"
    if legacy_presets.is_dir():
        for kind_dir in legacy_presets.iterdir():
            if not kind_dir.is_dir():
                continue
            target_dir = new_presets / kind_dir.name
            target_dir.mkdir(parents=True, exist_ok=True)
            for preset in kind_dir.glob("*.json"):
                target = target_dir / preset.name
                if not target.exists():
                    shutil.move(str(preset), str(target))


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
    # UI theme: "default" follows the system, "light" / "dark" force it.
    color_scheme: str = "default"

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
        instance = cls()
        for field in fields(cls):
            if field.name not in data:
                continue
            value = data[field.name]
            # JSON can hold any type and setattr on a dataclass never
            # validates; only accept values of the declared type (exact —
            # bool is not an acceptable int) so one hand-edited entry
            # can't crash consumers like max(1, max_concurrency).
            if type(value) is type(getattr(instance, field.name)):
                setattr(instance, field.name, value)
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
