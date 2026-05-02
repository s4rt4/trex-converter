from __future__ import annotations

from pathlib import Path


APP_NAME = "t-rex-converter"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    return project_root() / "assets" / Path(*parts)


def config_dir() -> Path:
    return Path.home() / ".config" / APP_NAME


def user_presets_dir() -> Path:
    return config_dir() / "presets"


def ensure_user_dirs() -> None:
    user_presets_dir().mkdir(parents=True, exist_ok=True)
