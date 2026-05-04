import pytest

from app.core.registry import ConversionRegistry, normalize_format


def test_registry_resolves_engine_and_outputs() -> None:
    registry = ConversionRegistry()

    engine = registry.resolve(".MP4", "mp3")

    assert engine.name == "ffmpeg"
    assert registry.is_supported("jpg", "png")
    assert registry.is_supported("png", "avif")
    assert registry.is_supported("webp", "tiff")
    assert "mp3" in registry.list_supported_outputs("mp4")


def test_registry_raises_for_unsupported_pair() -> None:
    registry = ConversionRegistry()

    with pytest.raises(KeyError):
        registry.resolve("zip", "mp3")


def test_normalize_format_rejects_empty() -> None:
    with pytest.raises(ValueError):
        normalize_format(".")


def test_registry_engine_by_name_returns_named_engine() -> None:
    registry = ConversionRegistry()

    assert registry.engine_by_name("tesseract").name == "tesseract"
    assert registry.engine_by_name("imagemagick").name == "imagemagick"
    assert registry.engine_by_name("ffmpeg").name == "ffmpeg"


def test_registry_engine_by_name_raises_for_unknown() -> None:
    registry = ConversionRegistry()

    with pytest.raises(KeyError):
        registry.engine_by_name("nope")


def test_png_to_pdf_routes_to_imagemagick_by_default() -> None:
    registry = ConversionRegistry()

    # OCR has png->pdf too but image_pairs is listed first, so default is imagemagick.
    # OCR page bypasses this via force_engine + engine_by_name lookup.
    assert registry.resolve("png", "pdf").name == "imagemagick"


def test_png_to_txt_routes_to_tesseract() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("png", "txt").name == "tesseract"
