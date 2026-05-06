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


def test_zip_to_folder_routes_to_archive_engine() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("zip", "folder").name == "archive"
    assert registry.resolve("tgz", "folder").name == "archive"


def test_txt_to_png_routes_to_qr_engine() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("txt", "png").name == "qr"
    assert registry.resolve("txt", "svg").name == "qr"


def test_required_binaries_includes_qr_extras() -> None:
    registry = ConversionRegistry()

    binaries = registry.required_binaries()
    # qrencode is the primary binary; zbarimg is registered as an extra
    assert "qrencode" in binaries
    assert "zbarimg" in binaries


def test_svg_to_png_routes_to_inkscape() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("svg", "png").name == "inkscape"
    assert registry.resolve("svg", "pdf").name == "inkscape"
    assert registry.resolve("svg", "svg").name == "inkscape"
    assert registry.resolve("svg", "eps").name == "inkscape"
    assert registry.resolve("svg", "ps").name == "inkscape"
    assert registry.resolve("svg", "emf").name == "inkscape"
    assert registry.resolve("svg", "wmf").name == "inkscape"


def test_pdf_to_svg_routes_to_inkscape() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("pdf", "svg").name == "inkscape"


def test_dxf_pairs_route_to_inkscape() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("svg", "dxf").name == "inkscape"
    assert registry.resolve("dxf", "svg").name == "inkscape"


def test_bitmap_to_svg_routes_to_inkscape_for_trace() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("png", "svg").name == "inkscape"
    assert registry.resolve("jpg", "svg").name == "inkscape"
    assert registry.resolve("bmp", "svg").name == "inkscape"
    assert registry.resolve("webp", "svg").name == "inkscape"


def test_required_binaries_includes_potrace_for_trace() -> None:
    registry = ConversionRegistry()

    assert "potrace" in registry.required_binaries()


def test_md_to_epub_routes_to_pandoc() -> None:
    registry = ConversionRegistry()

    assert registry.resolve("md", "epub").name == "pandoc"
    assert registry.resolve("epub", "md").name == "pandoc"
    assert registry.resolve("rst", "latex").name == "pandoc"


def test_required_binaries_includes_pandoc() -> None:
    registry = ConversionRegistry()

    assert "pandoc" in registry.required_binaries()


def test_required_binaries_includes_exiftool() -> None:
    registry = ConversionRegistry()

    assert "exiftool" in registry.required_binaries()


def test_required_binaries_includes_inkscape() -> None:
    registry = ConversionRegistry()

    assert "inkscape" in registry.required_binaries()
