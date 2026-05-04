# Project Context

Gunakan dokumen ini sebagai konteks awal saat membuka session Codex CLI baru.

## Project

T-Rex Converter adalah aplikasi GUI native Debian untuk konversi file lokal. Aplikasi memakai Python, PySide6, qasync, SQLite, dan engine lokal seperti FFmpeg, ImageMagick, LibreOffice, QPDF, dan Tesseract.

Prinsip utama:
- Semua proses lokal, tanpa cloud.
- Engine conversion tidak boleh bergantung pada UI.
- Semua subprocess engine memakai `asyncio.create_subprocess_exec`.
- UI hanya mengatur input user, render task, dan memanggil queue.

## Current Status

Versi project saat ini: `0.3.0`.

Sudah ada:
- Core task model dan task status lifecycle.
- In-memory async `TaskQueue` dengan concurrency, cancel, retry, dan callback.
- SQLite `TaskRepository` untuk history dan resume pending/running task.
- `ConversionRegistry` untuk routing format ke engine.
- Dependency checker untuk binary system.
- FFmpeg engine nyata dengan progress parsing, cancel subprocess, plus opsi lengkap: trim, resolution preset, compress (CRF + libx264 preset), rotate/flip/crop, speed change 0.5x–2.0x, watermark teks via drawtext.
- Audio module: full audio↔audio matrix (mp3/wav/aac/flac/m4a/opus/ogg) + video→audio extract; trim, fade-in/out, gain, loudnorm EBU R128, channel down-mix, sample-rate convert.
- Tesseract OCR engine nyata: image → searchable PDF / TXT / hOCR / TSV, language picker (eng/ind/eng+ind plus custom), PSM, OEM; routed via `force_engine` flag pada page + `ConversionRegistry.engine_by_name` + `TaskQueue.engine_by_name`.
- LibreOffice engine: format matrix penuh (text/spreadsheet/presentation), 52 pairs.
- Subtitle engine Python-pure: SRT ↔ VTT dengan time shift; engine `requires_binary=""` di-allow oleh DependencyChecker.
- Settings dataclass + JSON persistence di `~/.config/trex-converter/settings.json`; di-consume runner (max_concurrency) dan conversion_page (output_dir).
- ImageMagick engine nyata dengan opsi lengkap: transform (rotate, flip, flop, auto-trim, free crop, aspect crop), resize modes (dimension, longest edge, percent, megapixel), color (grayscale, sepia, negate, normalize, brightness, contrast, gamma), filter (blur, sharpen, denoise, vignette), border/frame, watermark teks dengan gravity dan opacity, density, dan ICO multi-resolution auto-resize.
- LibreOffice engine nyata untuk document-to-PDF dengan timeout dan cancel subprocess.
- PDF engine nyata via PyMuPDF: render halaman PDF ke PNG/JPG, ekstrak teks ke TXT, plus operasi PDF→PDF (extract pages dengan range syntax, rotate, compress, encrypt/decrypt AES-256, strip metadata, watermark teks dengan gravity 9-arah dan opacity).
- UI PySide6 dengan sidebar.
- Icon pack `qtawesome`.
- App logo SVG and hicolor PNG icon assets.
- Test suite pytest.

## UI Direction

UI memakai sidebar, bukan toolbar utama.

Sidebar menu:
- Dashboard
- Image
- Video
- Audio
- Document
- Subtitle
- OCR
- PDF Tools
- Settings
- About

Setiap menu menangani satu jenis conversion. Setiap halaman punya:
- Input selector.
- Output format selector.
- Output path.
- Tombol `Select Location`.
- Opsi yang relevan.
- Queue table terfilter sesuai kategori.

Queue table styling bersifat global melalui `QueuePanel`, jadi perubahan progress bar, tombol `Cancel`, tombol `Retry`, dan tinggi row berlaku di semua halaman.

## Branding

Warna branding utama ada di `app/ui/theme.py`.

Token saat ini:
- Surface/terang: `#EFE3CA`
- Dark/gelap: `#0C2C55`
- Accent: `#56B6C6`
- Muted surface: `#E4D7BD`
- Soft surface: `#F6EBD4`
- Soft dark: `#24158F`

Aturan desain:
- Background terang memakai surface `#EFE3CA`.
- Background gelap memakai dark `#0C2C55`.
- Aksen dipakai untuk teks di background gelap dan border tipis.
- Tombol di background terang harus solid gelap dengan icon dan teks terang.
- Komponen yang ambigu harus diberi affordance jelas, terutama dropdown dan action button.

## Icons

Icon pack: `qtawesome`.

Helper icon ada di:
- `app/ui/icons.py`

App logo:
- Source SVG: `assets/trex-logo.svg`
- Generated hicolor assets: `assets/icons/hicolor/...`
- Regeneration script: `scripts/generate-icons.sh`
- Debian desktop launcher: `packaging/t-rex-converter.desktop`
- Debian install map: `packaging/debian/install`

Icon sudah dipakai di:
- Sidebar menu.
- Window icon.
- Browse.
- Select Location.
- Add to Queue.
- Output format dropdown.
- Check Dependencies.
- Cancel.
- Retry.

## Important Files

- `app/main.py`: app startup, Qt Fusion style, light palette, non-native file dialog setting.
- `app/ui/theme.py`: brand colors.
- `app/ui/icons.py`: icon helper.
- `app/ui/main_window.py`: sidebar layout, global stylesheet.
- `app/ui/conversion_page.py`: reusable page per category, mendukung `extra_options_factory` untuk inject panel opsi khusus.
- `app/ui/image_options.py`: panel tabbed lengkap untuk opsi ImageMagick lanjutan.
- `app/ui/queue_panel.py`: global queue table.
- `app/core/task.py`: task dataclass and status.
- `app/core/queue.py`: async task queue.
- `app/core/registry.py`: conversion registry.
- `app/data/database.py`: SQLite task repository.
- `app/engines/ffmpeg_engine.py`: real FFmpeg engine — trim, scale, transpose/flip, crop, setpts/atempo, drawtext watermark, plus codec/CRF/preset.
- `app/ui/video_options.py`: panel tabbed (Trim / Transform / Resize / Compress / Watermark) untuk Video page.
- `app/ui/audio_options.py`: panel tabbed (Trim / Effects / Output) untuk Audio page.
- `app/ui/ocr_options.py`: panel single-pane (Language / PSM / OEM) untuk OCR page.
- `app/ui/subtitle_options.py`: panel single-pane (Time shift) untuk Subtitle page.
- `app/ui/settings_page.py`: Settings page dengan form output folder / concurrency / quality / DPI.
- `app/core/settings.py`: Settings dataclass + JSON persistence + module-level cache.
- `app/engines/subtitle_engine.py`: Python parser untuk SRT/VTT.
- `app/engines/imagemagick_engine.py`: real ImageMagick engine and image format list.
- `app/engines/libreoffice_engine.py`: real LibreOffice document-to-PDF engine.
- `app/engines/pdf_engine.py`: real PyMuPDF engine — render to image, extract text, dan operasi PDF→PDF (extract/rotate/compress/encrypt/decrypt/strip-metadata/watermark-text).
- `app/ui/pdf_operations.py`: panel tabbed (Pages / Security / Compress / Watermark / Metadata) untuk PDF Tools page.
- `app/ui/dashboard_page.py`: dashboard summary and all-task queue.
- `app/ui/about_page.py`: about page.
- `assets/trex-logo.svg`: source app logo.
- `assets/icons/hicolor/`: generated app icons for desktop packaging.

## Run

From project root:

```bash
cd /home/sarta/Project/trex-converter
.venv/bin/t-rex-converter
```

Alternative:

```bash
.venv/bin/python -m app.main
```

## Test

```bash
cd /home/sarta/Project/trex-converter
.venv/bin/python -m pytest
```

Current expected result:

```text
135 passed
```

## System Dependencies

Expected binaries:
- `ffmpeg`
- `magick`
- `libreoffice`
- `qpdf`
- `tesseract`

Install command:

```bash
sudo apt-get update
sudo apt-get install ffmpeg imagemagick libreoffice qpdf tesseract-ocr
```

## Python Dependencies

Project dependencies are in `pyproject.toml`.

Important runtime dependencies:
- `PySide6`
- `PyMuPDF`
- `qasync`
- `qtawesome`

Development dependencies:
- `pytest`
- `pytest-asyncio`

## Next Likely Work

Roadmap lengkap ada di `next-development.md`. Highlight berikutnya:
- PDF Tools lanjutan: merge, split, page reorder, watermark gambar, page numbering/Bates, metadata edit, repair (qpdf), PDF→DOCX/HTML/EPUB, extract embedded images/attachments, redaction.
- OCR lanjutan: PDF → searchable PDF (render + tesseract per-page + stitch via PyMuPDF), auto-rotate halaman sebelum OCR.
- Audio lanjutan: merge/mix multi-track, ID3 tag editor (title/artist/album/cover), vocal remove sederhana.
- Video lanjutan: stream-copy trim, two-pass target-size compress, GIF/WebP creator, thumbnail/contact sheet, logo watermark overlay, subtitle burn-in/extract, hardware accel detect, reverse video, concat multi-file.
- Document lanjutan: PPTX/ODP → PNG slides per-slide, PDF/A archival, password-protected PDF, bulk merge DOCX → 1 PDF.
- Subtitle lanjutan: ASS support, merge multi-file, burn-in (FFmpeg).
- Batch drag-and-drop multi-file.
- Package `.deb` properly.

## Codex Session Handoff

At the start of a new Codex CLI session, say:

```text
Baca PROJECT_CONTEXT.md dulu, lalu lanjutkan project ini.
```

Then ask for the specific next change.
