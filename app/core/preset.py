from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Preset:
    name: str
    format_in: str
    format_out: str
    engine: str
    options: dict = field(default_factory=dict)


def load_preset(path: Path) -> Preset:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    preset = data["preset"]
    return Preset(
        name=preset["name"],
        format_in=preset["format_in"],
        format_out=preset["format_out"],
        engine=preset["engine"],
        options=data.get("options", {}),
    )
