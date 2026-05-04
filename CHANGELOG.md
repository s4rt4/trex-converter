# Changelog

## Unreleased

- PDF wave 2: page reorder action (explicit page list), edit-metadata action (title/author/subject/keywords/creator), PDF→HTML extraction via PyMuPDF, and PDF repair via qpdf round-trip. PDF Tools input restricted to PDF only (previously also accepted png/jpg, duplicating the Image page).
- Audio wave 2: ID3 tag editor (title/artist/album/year/genre/track via `-metadata`) plus vocal remove via `pan=stereo|c0=c0-c1|c1=c1-c0`.
- Added a Settings sidebar page with persisted defaults at `~/.config/trex-converter/settings.json` (output folder, max concurrency, image quality, PDF DPI). Concurrency applies on next launch; output folder is honored by every conversion page when suggesting an output path.
- Added a Subtitle sidebar page powered by a new pure-Python `SubtitleEngine` (no external binary): SRT ↔ VTT conversion with optional time shift; `EngineCapabilities.requires_binary=""` is now treated as always-available by the dependency checker.
- Expanded the LibreOffice engine to a full Document format matrix: text docs ↔ DOCX/ODT/RTF/HTML/EPUB/TXT/PDF, spreadsheets ↔ XLSX/ODS/CSV/HTML/PDF, presentations ↔ PPTX/ODP/PDF (52 pairs). Document page output combo now exposes every reachable target.
- Replaced the Tesseract OCR stub with a real engine: image (png/jpg/jpeg/tif/tiff/bmp) → searchable PDF, TXT, hOCR, or TSV with multi-language picker (eng/ind/eng+ind plus custom), PSM (13 modes), and OEM (4 modes).
- Added an OCR sidebar page with a single-pane `OCROptionsPanel`; the new `force_engine` flag on `ConversionPageConfig` plus `ConversionRegistry.engine_by_name` and a `TaskQueue.engine_by_name` resolver lets the OCR page route png→pdf to Tesseract while the Image page keeps routing png→pdf to ImageMagick.
- Added an Audio sidebar page with a tabbed `AudioOptionsPanel` (Trim / Effects / Output) covering trim, fade-in/out (`afade`), gain ±20 dB (`volume`), loudness normalize (EBU R128 `loudnorm`), channel down-mix (`-ac`), and sample-rate convert (`-ar`).
- Expanded FFmpeg supported pairs to a full audio↔audio matrix (mp3/wav/aac/flac/m4a/opus/ogg) plus video→audio extraction across mp4/mov/mkv/webm sources.
- Video page now restricted to video outputs only (mp4/mov/mkv/webm); audio extraction is handled by the new Audio page to keep workflows focused.
- Expanded the FFmpeg engine with trim (start/end), resolution presets (4K/1440p/1080p/720p/480p/360p), compress (CRF + libx264 preset), rotate (90/180/270), flip H/V, free crop, speed change 0.5x–2.0x (setpts + atempo), and text watermark via drawtext with 9-position gravity and opacity.
- Added a tabbed `VideoOptionsPanel` to the Video page (Trim / Transform / Resize / Compress / Watermark).
- Expanded FFmpeg supported format pairs to a full mp4/mov/mkv/webm matrix plus video-to-audio extract; registry derives ffmpeg routing from the engine's `SUPPORTED_PAIRS`.
- Fixed PDF Tools page output-format filter that previously hid the `pdf` output, blocking every PDF→PDF operation from the UI.
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
