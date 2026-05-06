from __future__ import annotations

import json
import re
from pathlib import Path

from app.core.settings import CONFIG_DIR


PRESETS_DIR = CONFIG_DIR / "presets"
_NAME_OK = re.compile(r"^[A-Za-z0-9 _\-]{1,40}$")


def list_presets(kind: str, base: Path = PRESETS_DIR) -> list[str]:
    """Return preset names for the given page kind, sorted alphabetically."""
    folder = base / kind
    if not folder.is_dir():
        return []
    names: list[str] = []
    for path in folder.iterdir():
        if not path.is_file() or path.suffix != ".json":
            continue
        names.append(path.stem)
    return sorted(names)


def load_preset(kind: str, name: str, base: Path = PRESETS_DIR) -> dict:
    """Load a preset payload. Returns an empty dict when missing/corrupt."""
    safe = _safe_name(name)
    path = base / kind / f"{safe}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save_preset(
    kind: str, name: str, options: dict, base: Path = PRESETS_DIR
) -> Path:
    """Persist `options` to `<base>/<kind>/<safe_name>.json`."""
    safe = _safe_name(name)
    folder = base / kind
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{safe}.json"
    target.write_text(
        json.dumps(options, indent=2, sort_keys=True), encoding="utf-8"
    )
    return target


def delete_preset(kind: str, name: str, base: Path = PRESETS_DIR) -> bool:
    safe = _safe_name(name)
    target = base / kind / f"{safe}.json"
    if not target.exists():
        return False
    target.unlink()
    return True


def _safe_name(name: str) -> str:
    text = name.strip()
    if not _NAME_OK.match(text):
        raise ValueError(
            "Preset name must be 1–40 characters of letters, digits, "
            "spaces, hyphens, or underscores"
        )
    return text
