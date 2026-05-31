from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
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

# LibreOffice ships as a single `soffice` binary, but each document family is
# enabled by a separate component package (libreoffice-writer/-calc/-impress).
# A `libreoffice` on PATH therefore does NOT guarantee that spreadsheet or
# presentation conversion will work. We detect each component by the per-app
# launcher script (and, as a fallback, the component shared library) inside
# the LibreOffice program directory. Marker order: launcher first, lib second.
LIBREOFFICE_COMPONENT_MARKERS: dict[str, tuple[str, ...]] = {
    "writer": ("swriter", "libswlo.so"),
    "calc": ("scalc", "libsclo.so"),
    "impress": ("simpress", "libsdlo.so"),
    "draw": ("sdraw", "libsdlo.so"),
    "math": ("smath", "libsmlo.so"),
}

# Fallback program directories for distros where the binary isn't a symlink
# into the install tree (we still prefer resolving it from the binary itself).
_LIBREOFFICE_PROGRAM_DIRS: tuple[str, ...] = (
    "/usr/lib/libreoffice/program",
    "/usr/lib64/libreoffice/program",
    "/opt/libreoffice/program",
)


def _libreoffice_program_dir() -> Path | None:
    """Locate the LibreOffice `program/` directory, or None if not installed."""
    executable = which("libreoffice") or which("soffice")
    if executable:
        # On Debian /usr/bin/soffice symlinks into .../program/soffice, so the
        # resolved parent is the program directory that holds the components.
        program_dir = Path(executable).resolve().parent
        if program_dir.is_dir():
            return program_dir
    for candidate in _LIBREOFFICE_PROGRAM_DIRS:
        path = Path(candidate)
        if path.is_dir():
            return path
    return None


# Human-readable labels for the synthetic dependency tokens used in the UI.
_DEPENDENCY_LABELS: dict[str, str] = {
    "libreoffice:writer": "LibreOffice Writer (documents)",
    "libreoffice:calc": "LibreOffice Calc (spreadsheets)",
    "libreoffice:impress": "LibreOffice Impress (presentations)",
    "libreoffice:draw": "LibreOffice Draw",
    "libreoffice:math": "LibreOffice Math",
    "python:fitz": "PyMuPDF (python)",
    "python:pymupdf": "PyMuPDF (python)",
}


def dependency_label(binary: str) -> str:
    """Return a human-friendly name for a dependency token for display."""
    if binary in _DEPENDENCY_LABELS:
        return _DEPENDENCY_LABELS[binary]
    if binary.startswith("python:"):
        return f"{binary.split(':', 1)[1]} (python)"
    return binary


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

        if binary.startswith("libreoffice:"):
            component = binary.split(":", 1)[1]
            program_dir = _libreoffice_program_dir()
            if program_dir is None:
                return DependencyStatus(binary=binary, available=False, path=None)
            markers = LIBREOFFICE_COMPONENT_MARKERS.get(component, (component,))
            for marker in markers:
                candidate = program_dir / marker
                if candidate.exists():
                    return DependencyStatus(
                        binary=binary, available=True, path=str(candidate)
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
