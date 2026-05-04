from __future__ import annotations

from dataclasses import dataclass

from app.engines.base import BaseEngine
from app.engines.ffmpeg_engine import FFmpegEngine
from app.engines.imagemagick_engine import IMAGE_FORMATS, ImageMagickEngine
from app.engines.libreoffice_engine import LibreOfficeEngine, SUPPORTED_INPUT_FORMATS
from app.engines.ocr_engine import TesseractOCREngine
from app.engines.pdf_engine import PDF_IMAGE_FORMATS, PDFEngine


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
            binaries.add(self._get_engine(entry).capabilities.requires_binary)
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
        (format_in, "pdf", "libreoffice", LibreOfficeEngine)
        for format_in in SUPPORTED_INPUT_FORMATS
    ]
    mapping: list[tuple[str, str, str, type[BaseEngine]]] = [
        ("mp4", "mp3", "ffmpeg", FFmpegEngine),
        ("mp4", "webm", "ffmpeg", FFmpegEngine),
        ("mov", "mp4", "ffmpeg", FFmpegEngine),
        ("wav", "mp3", "ffmpeg", FFmpegEngine),
        ("flac", "mp3", "ffmpeg", FFmpegEngine),
        *[
            ("pdf", format_out, "pdf", PDFEngine)
            for format_out in PDF_IMAGE_FORMATS
        ],
        ("pdf", "pdf", "pdf", PDFEngine),
        ("pdf", "txt", "pdf", PDFEngine),
        ("png", "txt", "tesseract", TesseractOCREngine),
        ("jpg", "txt", "tesseract", TesseractOCREngine),
        ("jpeg", "txt", "tesseract", TesseractOCREngine),
    ] + document_pairs + image_pairs
    return [
        RegistryEntry(
            format_in=normalize_format(format_in),
            format_out=normalize_format(format_out),
            engine_name=engine_name,
            engine_factory=engine_factory,
        )
        for format_in, format_out, engine_name, engine_factory in mapping
    ]
