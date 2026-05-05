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
- FFmpeg engine nyata dengan progress parsing, cancel subprocess, plus opsi lengkap: trim, resolution preset, compress (CRF + libx264 preset), rotate/flip/crop, speed change 0.5x–2.0x, watermark teks via drawtext, reverse, logo overlay (`-filter_complex`), subtitle burn-in (`subtitles=`/`ass=`), GIF creator (palettegen+paletteuse), animated WebP (libwebp + loop=0), contact sheet (select+tile) ke PNG/JPG, single-frame still extraction.
- Audio module: full audio↔audio matrix (mp3/wav/aac/flac/m4a/opus/ogg) + video→audio extract; trim, fade-in/out, gain, loudnorm EBU R128, channel down-mix, sample-rate convert.
- Tesseract OCR engine nyata: image (png/jpg/jpeg/tif/tiff/bmp) DAN PDF input → searchable PDF / TXT / hOCR / TSV. PDF pipeline: render setiap halaman dengan PyMuPDF (default 300 DPI), OCR per halaman, stitch (PDF via `insert_pdf`, TXT dengan `\f`, hOCR concat ocr_page divs + renumber ID, TSV header tunggal + rows). Auto-rotate via OSD pre-pass (`tesseract --psm 0`) parsing `Rotate:` lalu re-render via `page.set_rotation`. Language picker (eng/ind/eng+ind plus custom), PSM, OEM. Routed via `force_engine` flag pada page + `ConversionRegistry.engine_by_name` + `TaskQueue.engine_by_name`.
- LibreOffice engine: format matrix penuh (text/spreadsheet/presentation), 52 pairs.
- Subtitle engine Python-pure: SRT ↔ VTT ↔ ASS round-trip dengan time shift. ASS parser handle Format header detection, Dialogue rows dengan koma di text, `\N` escape, Comment skip. ASS formatter emit Script Info + V4+ Styles + Events dengan default Arial 32 white style. Engine `requires_binary=""` di-allow oleh DependencyChecker.
- Settings dataclass + JSON persistence di `~/.config/trex-converter/settings.json`; di-consume runner (max_concurrency) dan conversion_page (output_dir).
- ImageMagick engine nyata dengan opsi lengkap: transform (rotate, flip, flop, auto-trim, free crop, aspect crop), resize modes (dimension, longest edge, percent, megapixel), color (grayscale, sepia, negate, normalize, brightness, contrast, gamma), filter (blur, sharpen, denoise, vignette), border/frame, watermark teks dengan gravity dan opacity, density, dan ICO multi-resolution auto-resize.
- PDF engine nyata via PyMuPDF + qpdf: render halaman PDF ke PNG/JPG, ekstrak ke TXT/HTML, plus operasi PDF→PDF (extract pages, reorder, rotate, compress, repair via qpdf, encrypt/decrypt AES-256, strip metadata, edit metadata, watermark teks gravity 9-arah).
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
- `app/engines/ffmpeg_engine.py`: real FFmpeg engine — video filter chain (crop → transpose → flip → scale → setpts → subtitles/ass → drawtext → reverse), audio filter chain (atempo → afade-in → afade-out → volume → vocal-remove pan → loudnorm → areverse), CRF + preset, ID3 metadata flags, channel/sample-rate, GIF builder (palettegen+paletteuse), WebP builder (libwebp+loop), thumbnail grid (select+tile), single-frame still, logo overlay via `-filter_complex` ([0:v]…[v0]; [1:v]scale,colorchannelmixer[logo]; [v0][logo]overlay[vout]).
- `app/ui/video_options.py`: panel tabbed (Trim / Transform / Resize / Compress / Watermark / Effects / Animation / Thumbnails / Subtitles) untuk Video page. Effects = reverse + logo overlay; Animation = GIF/WebP fps/width/quality; Thumbnails = grid rows/cols/interval/tile-width; Subtitles = burn-in path picker.
- `app/ui/audio_options.py`: panel tabbed (Trim / Effects / Output) untuk Audio page.
- `app/ui/ocr_options.py`: panel single-pane (Language / PSM / OEM / PDF render DPI / Auto-rotate) untuk OCR page.
- `app/ui/subtitle_options.py`: panel single-pane (Time shift) untuk Subtitle page.
- `app/ui/settings_page.py`: Settings page dengan form output folder / concurrency / quality / DPI.
- `app/core/settings.py`: Settings dataclass + JSON persistence + module-level cache.
- `app/engines/subtitle_engine.py`: Python parser untuk SRT/VTT.
- `app/engines/imagemagick_engine.py`: real ImageMagick engine and image format list.
- `app/engines/libreoffice_engine.py`: real LibreOffice engine — full Document format matrix (text/spreadsheet/presentation, 52 pairs); helper `_find_converted_file` handles arbitrary output extension.
- `app/engines/pdf_engine.py`: real PyMuPDF engine — render to image, extract to TXT/HTML, dan operasi PDF→PDF (extract_pages/reorder/rotate/compress/repair-via-qpdf/encrypt/decrypt/strip-metadata/edit-metadata/watermark-text).
- `app/ui/pdf_operations.py`: panel tabbed (Pages / Security / Compress / Watermark / Metadata); Pages action combo includes Extract / Reorder / Rotate; Compress action combo includes Compress / Repair; Metadata action combo includes Strip / Edit + 5-field form.
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
170 passed
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

Roadmap lengkap dengan checklist `[x]/[~]/[ ]` ada di `next-development.md`. Highlight item terbesar yang masih `[ ]`:
- PDF Tools: merge, split, watermark gambar, page numbering/Bates, PDF→DOCX/EPUB, extract embedded images/attachments, redaction, A/B compare.
- Audio: merge/mix multi-track, cover art (ID3 APIC).
- Video: stream-copy trim, two-pass target-size compress, subtitle extract dari MKV, hardware accel detect, concat multi-file.
- Document: PPTX→PNG slides, PDF/A archival, password-protected PDF, bulk merge.
- Subtitle: merge multi-file.
- Modul baru §7: Ebook (Pandoc/Calibre), Archive (tar/zip/7z), QR/Barcode (qrencode + zbarimg), Metadata cross-cut (exiftool).
- Cross-cutting §8: preview/details panel per task, batch drag-and-drop multi-file, preset save/load per modul, packaging `.deb` final.

**Catatan arsitektur untuk fitur multi-input/multi-output**: PDF merge, video concat, audio mix, image montage, dan PDF split butuh refactor `Task` model dari single-input/single-output. Itu prasyarat besar yang belum dibuat.

## Codex Session Handoff

At the start of a new Codex CLI session, say:

```text
Baca PROJECT_CONTEXT.md dulu, lalu lanjutkan project ini.
```

Then ask for the specific next change.
