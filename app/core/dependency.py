from __future__ import annotations

from dataclasses import dataclass
from shutil import which


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    binary: str
    available: bool
    path: str | None


class DependencyChecker:
    def __init__(self, aliases: dict[str, tuple[str, ...]] | None = None) -> None:
        self.aliases = aliases or {
            "imagemagick": ("magick", "convert"),
            "magick": ("magick", "convert"),
        }

    def check(self, binary: str) -> DependencyStatus:
        candidates = self.aliases.get(binary, (binary,))
        for candidate in candidates:
            resolved = which(candidate)
            if resolved:
                return DependencyStatus(binary=binary, available=True, path=resolved)
        return DependencyStatus(binary=binary, available=False, path=None)

    def check_many(self, binaries: list[str] | set[str] | tuple[str, ...]) -> dict[str, DependencyStatus]:
        return {binary: self.check(binary) for binary in sorted(set(binaries))}
