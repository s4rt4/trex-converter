from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from shutil import which


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    binary: str
    available: bool
    path: str | None


PYTHON_MODULE_ALIASES: dict[str, tuple[str, ...]] = {
    # PyMuPDF: Debian Trixie ships only `pymupdf`; older pip wheels only
    # ship `fitz`; modern wheels ship both. Either satisfies the dep.
    "fitz": ("pymupdf", "fitz"),
    "pymupdf": ("pymupdf", "fitz"),
}


class DependencyChecker:
    def __init__(self, aliases: dict[str, tuple[str, ...]] | None = None) -> None:
        self.aliases = aliases or {
            "imagemagick": ("magick", "convert"),
            "magick": ("magick", "convert"),
        }

    def check(self, binary: str) -> DependencyStatus:
        if not binary:
            return DependencyStatus(binary="", available=True, path="builtin")

        if binary.startswith("python:"):
            module_name = binary.split(":", 1)[1]
            candidates = PYTHON_MODULE_ALIASES.get(module_name, (module_name,))
            for candidate in candidates:
                if find_spec(candidate) is not None:
                    return DependencyStatus(
                        binary=binary, available=True, path=candidate
                    )
            return DependencyStatus(binary=binary, available=False, path=None)

        candidates = self.aliases.get(binary, (binary,))
        for candidate in candidates:
            resolved = which(candidate)
            if resolved:
                return DependencyStatus(binary=binary, available=True, path=resolved)
        return DependencyStatus(binary=binary, available=False, path=None)

    def check_many(self, binaries: list[str] | set[str] | tuple[str, ...]) -> dict[str, DependencyStatus]:
        return {binary: self.check(binary) for binary in sorted(set(binaries))}
