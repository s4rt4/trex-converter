from __future__ import annotations

from pathlib import Path


APP_NAME = "t-rex-converter"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    """Return the on-disk path of an asset.

    Looks first in the source-checkout layout (`<repo>/assets/...`), then
    in the system layout shipped by the .deb (`/usr/share/t-rex-converter/
    assets/...`). Returns the source-checkout path even when missing so
    callers that only consume it for `QPixmap` (which silently no-ops on
    a missing path) keep their existing behavior.
    """
    relative = Path(*parts)
    dev = project_root() / "assets" / relative
    if dev.exists():
        return dev
    system = Path("/usr/share/t-rex-converter/assets") / relative
    if system.exists():
        return system
    return dev


def config_dir() -> Path:
    return Path.home() / ".config" / APP_NAME


def user_presets_dir() -> Path:
    return config_dir() / "presets"


def ensure_user_dirs() -> None:
    user_presets_dir().mkdir(parents=True, exist_ok=True)
