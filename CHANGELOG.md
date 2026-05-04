# Changelog

## Unreleased

- Reworked the main UI into a sidebar layout with separate Image, Video, Document, and PDF Tools pages.
- Added category-specific task forms and filtered task queues per page.
- Added real async LibreOffice document-to-PDF conversion with timeout, cancel, and output renaming.
- Added PyMuPDF-based PDF page extraction to PNG/JPG with multi-page output naming, plus PDF→TXT text extraction.
- Added PDF operations engine for extract pages (range syntax `1-3,5,8-10`), rotate, compress (garbage + deflate + clean), encrypt/decrypt with AES-256, strip metadata, and text watermark with 9-position gravity and opacity.
- Added a tabbed `PDFOperationsPanel` to the PDF Tools page (Pages / Security / Compress / Watermark / Metadata).
- Routed `pdf→pdf` and `pdf→txt` to the PyMuPDF engine; the dependency checker now supports a `python:<module>` prefix to verify Python module availability.
- Expanded the ImageMagick engine with transform (rotate, flip, flop, auto-trim, free crop, aspect crop), resize modes (dimension, longest edge, percent, megapixel), color (grayscale, sepia, negate, normalize, brightness, contrast, gamma), filter (blur, sharpen, denoise, vignette), border/frame, text watermark with gravity and opacity, output density, and ICO multi-resolution auto-resize.
- Added a tabbed `ImageOptionsPanel` to the Image page exposing all advanced ImageMagick options.
- Added `extra_options_factory` hook to `ConversionPageConfig` so any page can attach a category-specific options panel.
- Added Dashboard and About sidebar pages; each conversion page now has Convert / Queue tabs and the queue panel shows file thumbnails or mime icons.
- Added a roadmap document at `next-development.md` tracking advanced features per module and proposed new modules (Audio, Subtitle, Ebook, Archive, QR/Barcode, Metadata).

## 0.3.0

- Added real async ImageMagick engine execution with resize, quality, and strip options.
- Added SQLite task repository for history and restart recovery.
- Added persistent queue integration and GUI startup resume hook.
- Added tests for ImageMagick execution and SQLite task persistence.

## 0.2.0

- Added real async FFmpeg engine execution with `asyncio.create_subprocess_exec`.
- Added FFmpeg progress parsing from `-progress pipe:2`.
- Added FFmpeg cancellation that terminates the subprocess.
- Connected the PySide6 queue UI to the in-memory task queue.
- Added per-task progress bars plus cancel and retry buttons.
- Added tests for FFmpeg command execution, progress parsing, queue cancel, retry, registry, dependency checks, and presets.

## 0.1.0

- Added core project structure, task model, in-memory queue, dependency checker, registry, engine abstraction, UI skeleton, preset loading, Debian packaging placeholders, and baseline tests.
