"""Lightweight input probing for the drop zone metadata line.

These helpers turn a dropped file into a short, human-readable detail
string (``3840 × 2160``, ``04:12``, ``12 pages``). Everything here is
*synchronous and potentially slow* (ffprobe spawns a subprocess), so the
drop zone calls :func:`probe_details` from a worker thread and marshals
the result back with ``GLib.idle_add`` — never on the GTK main loop.

Only facts we can read cheaply and reliably are returned; anything
unknown yields ``None`` so the UI shows file size alone rather than a
guess (house style §7.1, "no blank placeholders").
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from gi.repository import GdkPixbuf, GLib

IMAGE_EXTS = frozenset(
    {"png", "jpg", "jpeg", "webp", "avif", "heic", "heif", "gif",
     "bmp", "tiff", "tif", "ico", "svg"}
)
VIDEO_EXTS = frozenset(
    {"mp4", "mkv", "mov", "avi", "webm", "flv", "wmv", "m4v", "mpg",
     "mpeg", "ts", "3gp", "ogv"}
)
AUDIO_EXTS = frozenset(
    {"mp3", "wav", "m4a", "flac", "aac", "opus", "ogg", "wma", "aiff", "aif"}
)


def probe_details(path: Path) -> str | None:
    """Return a short detail string for ``path``, or ``None`` if unknown."""
    suffix = path.suffix.lower().lstrip(".")
    if suffix in IMAGE_EXTS:
        return _image_dimensions(path)
    if suffix in VIDEO_EXTS:
        return _media_details(path, want_dimensions=True)
    if suffix in AUDIO_EXTS:
        return _media_details(path, want_dimensions=False)
    if suffix == "pdf":
        return _pdf_pages(path)
    return None


def _image_dimensions(path: Path) -> str | None:
    # get_file_info reads only the header — no full decode of huge images.
    try:
        info = GdkPixbuf.Pixbuf.get_file_info(str(path))
    except GLib.Error:
        return None
    if not info or info[0] is None:
        return None
    _format, width, height = info
    if width <= 0 or height <= 0:
        return None
    return f"{width} × {height}"


def _media_details(path: Path, *, want_dimensions: bool) -> str | None:
    data = _ffprobe(path)
    if data is None:
        return None
    parts: list[str] = []

    if want_dimensions:
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width")
                height = stream.get("height")
                if width and height:
                    parts.append(f"{width} × {height}")
                break

    duration = _duration_seconds(data)
    if duration is not None:
        parts.append(_format_clock(duration))

    return " · ".join(parts) if parts else None


def _ffprobe(path: Path) -> dict | None:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(path),
            ],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _duration_seconds(data: dict) -> float | None:
    raw = data.get("format", {}).get("duration")
    if raw is None:
        for stream in data.get("streams", []):
            raw = stream.get("duration")
            if raw is not None:
                break
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        return None
    return seconds if seconds > 0 else None


def _format_clock(seconds: float) -> str:
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _pdf_pages(path: Path) -> str | None:
    try:
        import fitz  # PyMuPDF; present in the app venv
    except ImportError:
        return None
    try:
        with fitz.open(str(path)) as document:
            count = document.page_count
    except Exception:
        return None
    if count <= 0:
        return None
    return f"{count} page" if count == 1 else f"{count} pages"
