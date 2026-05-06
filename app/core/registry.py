from __future__ import annotations

from dataclasses import dataclass

from app.engines.archive_engine import (
    ArchiveEngine,
    SUPPORTED_PAIRS as ARCHIVE_PAIRS,
)
from app.engines.base import BaseEngine
from app.engines.ffmpeg_engine import FFmpegEngine, SUPPORTED_PAIRS as FFMPEG_PAIRS
from app.engines.imagemagick_engine import IMAGE_FORMATS, ImageMagickEngine
from app.engines.inkscape_engine import (
    InkscapeEngine,
    SUPPORTED_PAIRS as INKSCAPE_PAIRS,
)
from app.engines.libreoffice_engine import (
    LibreOfficeEngine,
    SUPPORTED_INPUT_FORMATS,
    SUPPORTED_PAIRS as LIBREOFFICE_PAIRS,
)
from app.engines.ocr_engine import (
    OCR_INPUT_FORMATS,
    SUPPORTED_PAIRS as OCR_PAIRS,
    TesseractOCREngine,
)
from app.engines.pandoc_engine import (
    PandocEngine,
    SUPPORTED_PAIRS as PANDOC_PAIRS,
)
from app.engines.pdf_engine import PDF_IMAGE_FORMATS, PDFEngine
from app.engines.qr_engine import (
    QREngine,
    SUPPORTED_PAIRS as QR_PAIRS,
)
from app.engines.subtitle_engine import (
    SUPPORTED_PAIRS as SUBTITLE_PAIRS,
    SubtitleEngine,
)


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    format_in: str
    format_out: str
    engine_name: str
    engine_factory: type[BaseEngine]


class ConversionRegistry:
    def __init__(self, entries: list[RegistryEntry] | None = None) -> None:
        self._entries = entries or default_entries()
        self._engine_cache: dict[str, BaseEngine] = {}

    def resolve(self, format_in: str, format_out: str) -> BaseEngine:
        normalized = (normalize_format(format_in), normalize_format(format_out))
        for entry in self._entries:
            if (entry.format_in, entry.format_out) == normalized:
                return self._get_engine(entry)
        raise KeyError(f"Unsupported conversion: {format_in} -> {format_out}")

    def engine_by_name(self, name: str) -> BaseEngine:
        for entry in self._entries:
            if entry.engine_name == name:
                return self._get_engine(entry)
        raise KeyError(f"Unknown engine: {name}")

    def list_supported_outputs(self, format_in: str) -> list[str]:
        normalized = normalize_format(format_in)
        return sorted(
            {
                entry.format_out
                for entry in self._entries
                if entry.format_in == normalized
            }
        )

    def is_supported(self, format_in: str, format_out: str) -> bool:
        normalized = (normalize_format(format_in), normalize_format(format_out))
        return any(
            (entry.format_in, entry.format_out) == normalized
            for entry in self._entries
        )

    def required_binaries(self) -> set[str]:
        binaries: set[str] = set()
        for entry in self._entries:
            capabilities = self._get_engine(entry).capabilities
            if capabilities.requires_binary:
                binaries.add(capabilities.requires_binary)
            for extra in capabilities.extra_binaries:
                if extra:
                    binaries.add(extra)
        return binaries

    def all_entries(self) -> list[RegistryEntry]:
        return list(self._entries)

    def _get_engine(self, entry: RegistryEntry) -> BaseEngine:
        if entry.engine_name not in self._engine_cache:
            self._engine_cache[entry.engine_name] = entry.engine_factory()
        return self._engine_cache[entry.engine_name]


def normalize_format(value: str) -> str:
    normalized = value.lower().strip().lstrip(".")
    if not normalized:
        raise ValueError("Format cannot be empty")
    return normalized


def default_entries() -> list[RegistryEntry]:
    image_pairs = [
        (format_in, format_out, "imagemagick", ImageMagickEngine)
        for format_in in IMAGE_FORMATS
        for format_out in IMAGE_FORMATS
        if format_in != format_out
    ]
    document_pairs = [
        (format_in, format_out, "libreoffice", LibreOfficeEngine)
        for format_in, format_out in sorted(LIBREOFFICE_PAIRS)
    ]
    ffmpeg_pairs = [
        (format_in, format_out, "ffmpeg", FFmpegEngine)
        for format_in, format_out in sorted(FFMPEG_PAIRS)
    ]
    ocr_pairs = [
        (format_in, format_out, "tesseract", TesseractOCREngine)
        for format_in, format_out in sorted(OCR_PAIRS)
    ]
    subtitle_pairs = [
        (format_in, format_out, "subtitle", SubtitleEngine)
        for format_in, format_out in sorted(SUBTITLE_PAIRS)
    ]
    archive_pairs = [
        (format_in, format_out, "archive", ArchiveEngine)
        for format_in, format_out in sorted(ARCHIVE_PAIRS)
    ]
    qr_pairs = [
        (format_in, format_out, "qr", QREngine)
        for format_in, format_out in sorted(QR_PAIRS)
    ]
    inkscape_pairs = [
        (format_in, format_out, "inkscape", InkscapeEngine)
        for format_in, format_out in sorted(INKSCAPE_PAIRS)
    ]
    pandoc_pairs = [
        (format_in, format_out, "pandoc", PandocEngine)
        for format_in, format_out in sorted(PANDOC_PAIRS)
    ]
    mapping: list[tuple[str, str, str, type[BaseEngine]]] = [
        *[
            ("pdf", format_out, "pdf", PDFEngine)
            for format_out in PDF_IMAGE_FORMATS
        ],
        ("pdf", "pdf", "pdf", PDFEngine),
        ("pdf", "txt", "pdf", PDFEngine),
        ("pdf", "html", "pdf", PDFEngine),
        ("pdf", "folder", "pdf", PDFEngine),
    ] + ffmpeg_pairs + document_pairs + image_pairs + ocr_pairs + subtitle_pairs + archive_pairs + qr_pairs + inkscape_pairs + pandoc_pairs
    return [
        RegistryEntry(
            format_in=normalize_format(format_in),
            format_out=normalize_format(format_out),
            engine_name=engine_name,
            engine_factory=engine_factory,
        )
        for format_in, format_out, engine_name, engine_factory in mapping
    ]
