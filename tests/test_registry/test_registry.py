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
