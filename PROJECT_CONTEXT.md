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

Versi project saat ini: `0.4.0`.

Sudah ada:
- Core task model dan task status lifecycle, plus dukungan multi-input via `Task.extra_inputs` + property `inputs`/`formats_in` (DB punya kolom `extra_inputs` dengan auto-migration ALTER TABLE).
- In-memory async `TaskQueue` dengan concurrency, cancel, retry, dan callback.
- SQLite `TaskRepository` untuk history dan resume pending/running task.
- `ConversionRegistry` untuk routing format ke engine.
- Dependency checker untuk binary system.
- FFmpeg engine nyata dengan progress parsing, cancel subprocess, plus opsi lengkap: trim, resolution preset, compress (CRF + libx264 preset, plus two-pass `target_size_mb` via ffprobe duration probe + `_run_two_pass`), rotate/flip/crop, speed change 0.5x–2.0x, watermark teks via drawtext, reverse, logo overlay (`-filter_complex`), subtitle burn-in (`subtitles=`/`ass=`), GIF creator (palettegen+paletteuse), animated WebP (libwebp + loop=0), contact sheet (select+tile) ke PNG/JPG, single-frame still extraction, stream-copy trim (`stream_copy: bool` → `-c copy` + skip filter chain), subtitle extract (`mkv|mp4|mov|webm → srt|ass|vtt` via `-map 0:s:N -c:s codec`), dan `detect_hardware_accels()` helper untuk dependency dialog.
- Audio module: full audio↔audio matrix (mp3/wav/aac/flac/m4a/opus/ogg) + video→audio extract; trim, fade-in/out, gain, loudnorm EBU R128, channel down-mix, sample-rate convert.
- Tesseract OCR engine nyata: image (png/jpg/jpeg/tif/tiff/bmp) DAN PDF input → searchable PDF / TXT / hOCR / TSV. PDF pipeline: render setiap halaman dengan PyMuPDF (default 300 DPI), OCR per halaman, stitch (PDF via `insert_pdf`, TXT dengan `\f`, hOCR concat ocr_page divs + renumber ID, TSV header tunggal + rows). Auto-rotate via OSD pre-pass (`tesseract --psm 0`) parsing `Rotate:` lalu re-render via `page.set_rotation`. Language picker (eng/ind/eng+ind plus custom), PSM, OEM. Routed via `force_engine` flag pada page + `ConversionRegistry.engine_by_name` + `TaskQueue.engine_by_name`.
- LibreOffice engine: format matrix penuh (text/spreadsheet/presentation), 52 pairs. PDF output filter di-build via `_convert_to_format` JSON dict yang gabungkan `pdf_a` (PDF/A-1a archival, SelectPdfVersion=1), `pdf_password_user` (DocumentOpenPassword + EncryptFile), dan `pdf_password_owner` (PermissionPassword + RestrictPermissions). Plus slide rendering (presentation × {folder}, dispatch `slides_to_images`: convert ke PDF tempdir, lalu PyMuPDF Pixmap render setiap halaman ke PNG/JPG di DPI configurable).
- Subtitle engine Python-pure: SRT ↔ VTT ↔ ASS round-trip dengan time shift. ASS parser handle Format header detection, Dialogue rows dengan koma di text, `\N` escape, Comment skip. ASS formatter emit Script Info + V4+ Styles + Events dengan default Arial 32 white style. Engine `requires_binary=""` di-allow oleh DependencyChecker.
- Archive engine Python-pure (stdlib `zipfile` + `tarfile`): extract zip/tar/tgz/tbz/txz/gz/bz2/xz → folder (reject absolute path dan path-traversal entries; tar extract pakai `filter='data'`). Plus compress folder → zip/tar/tgz/tbz/txz (ZIP_DEFLATED / tar mode w/w:gz/w:bz2/w:xz, file-only entries via Path.rglob, POSIX relative arcnames).
- QR engine: `qrencode` (generate txt → png/svg dengan size/margin/ECC L-M-Q-H) + `zbarimg` (decode image → txt, exit 4 = no barcode). Engine declare `requires_binary="qrencode"` + `extra_binaries=("zbarimg",)`.
- Pandoc engine (Ebook): 138 pair format matrix antara epub/docx/odt/html/md/rst/latex/org/fb2 (semua bidirectional, aliases md/markdown, latex/tex, html/htm collapsed) plus output txt via Pandoc plain writer. Subprocess `pandoc --from FROM --to TO --output OUT IN` plus optional `--metadata key=value` (title/author/lang/publisher/date), `--toc`, `--embed-resources` (HTML self-contained), `--standalone` (forced untuk html/latex). Helper `build_command(task)` dispatch. Sidebar "Ebook" force_engine.
- ExifTool engine (Metadata cross-cut): operations read (file → txt JSON/text dump), strip (`-overwrite_original -all=`), edit (`-Title=`/`-Artist=`/`-Author=`/`-Subject=`/`-Description=`/`-Comment=`/`-Copyright=`/`-Keywords=`). Pairs same-format + → txt untuk 18 input format (image jpg/png/tif/heic/webp/gif, audio mp3/m4a/flac/wav/ogg, video mp4/mov/mkv/webm, pdf). Sidebar "Metadata" force_engine.
- PDF A/B compare: multi-input PDFEngine `compare` operation (output folder). Render setiap halaman dari dua PDF via PyMuPDF Pixmap @ DPI configurable, panggil `magick compare -metric AE -fuzz N%` ke `<stem>-pageNNN-diff.png`. Helper `_run_imagemagick_compare` parse AE count dari stderr.
- Preset save/load: `app/core/presets.py` JSON persistence di `~/.config/trex-converter/presets/<kind>/<name>.json`. Setiap conversion page punya preset combo + Save/Load/Delete buttons. Panel opt-in via `apply_preset(payload)` callback.
- Drag-and-drop: ConversionPage `setAcceptDrops(True)` plus `dragEnterEvent`/`dropEvent` route ke `_accept_paths()` shared helper.
- Task details: QueuePanel Info button (kolom 8) + `cellDoubleClicked` → `TaskDetailsDialog` (input/output thumbnails + metadata block + log in QPlainTextEdit).
- Inkscape engine (SVG / Vector Tools, Wave 1 + 2 + 3 lengkap): pair `svg→png` (dpi / width / height), `svg→pdf` (vector preserved), `svg→svg` dengan operation `cleanup` (`--export-plain-svg --vacuum-defs`) atau `trim` (cleanup + `--export-area-drawing`). Wave 2: `svg→eps`, `svg→ps` dengan opsional `--export-ps-level=2|3` dan `--export-text-to-path`; `svg→emf`, `svg→wmf`; `pdf→svg` dengan `--pages=N` (default page 1) dan `--export-plain-svg`. Wave 3: export-by-id (`inkscape_export_id` + `inkscape_export_id_only` emit `--export-id=ID [--export-id-only]`); DXF round-trip (`svg→dxf` via extension `org.ekips.output.dxf_outlines` / R14 default atau `org.inkscape.output.dxf_twelve` / R12; `dxf→svg` via `--export-type=svg --export-plain-svg`); pixmap→SVG trace (8 bitmap formats → svg via pipeline `magick INPUT -colorspace Gray TEMP.pgm` lalu `potrace TEMP.pgm -s -o OUT.svg` dengan options trace_threshold/turdsize/alphamax). Engine declare `extra_binaries=("potrace", "magick")`. `convert()` dispatch ke `_run_trace` untuk bitmap pairs atau `build_command`+`_run` untuk Inkscape pairs. Subprocess via `asyncio.create_subprocess_exec` dengan `output_path.exists()` post-check.
- Settings dataclass + JSON persistence di `~/.config/trex-converter/settings.json`; di-consume runner (max_concurrency) dan conversion_page (output_dir).
- ImageMagick engine nyata dengan opsi lengkap: transform (rotate, flip, flop, auto-trim, free crop, aspect crop), resize modes (dimension, longest edge, percent, megapixel), fit-to-canvas dengan letterbox (`-resize WxH -background COLOR -gravity center -extent WxH`), color (grayscale, sepia, negate, normalize, brightness, contrast, gamma), filter (blur, sharpen, denoise, vignette), border/frame, watermark teks/gambar dengan gravity dan opacity, density, dan ICO multi-resolution auto-resize.
- PDF engine nyata via PyMuPDF + qpdf + pdf2docx: render halaman PDF ke PNG/JPG, ekstrak ke TXT/HTML, plus PDF→DOCX (pdf2docx) dan PDF→EPUB (hand-rolled minimal EPUB 2 builder `_write_epub`). Operasi PDF→PDF (extract pages, reorder, rotate, compress, compress_images dengan downsample DPI + JPEG re-encode, linearize via `qpdf --linearize`, repair via qpdf, encrypt/decrypt AES-256, strip metadata, edit metadata, watermark teks/gambar gravity 9-arah, page numbering/Bates dengan template `{n}`/`{total}`/`{page}` + skip-first-N + opacity, redact via `Page.search_for(term)` + `add_redact_annot` + `apply_redactions`). Operasi pdf→folder (split dengan tiga mode: every_n / range / size, extract_images dengan dedupe by xref, extract_attachments via `embfile_*`).
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
- PDF Merge
- PDF Split
- PDF Numbering
- PDF Extract Images
- PDF Extract Attachments
- Document Merge
- Slides to Images
- Subtitle Extract
- Ebook
- Metadata
- PDF Compare
- Video Concat
- Audio Mix
- Image Montage
- Subtitle Merge
- Archive
- Archive Compress
- QR / Barcode
- SVG / Vector
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
- `app/ui/conversion_page.py`: reusable page per category, mendukung `extra_options_factory` untuk inject panel opsi khusus, `directory_output` untuk output folder, `directory_input` untuk input folder picker (format_in derive dari config), `multi_input` untuk list widget + Add/Remove/Clear input file, dan `default_options` untuk force-inject option.
- `app/ui/image_options.py`: panel tabbed lengkap untuk opsi ImageMagick lanjutan.
- `app/ui/queue_panel.py`: global queue table.
- `app/core/task.py`: task dataclass and status.
- `app/core/queue.py`: async task queue.
- `app/core/registry.py`: conversion registry.
- `app/data/database.py`: SQLite task repository.
- `app/engines/ffmpeg_engine.py`: real FFmpeg engine — video filter chain (crop → transpose → flip → scale → setpts → subtitles/ass → drawtext → reverse), audio filter chain (atempo → afade-in → afade-out → volume → vocal-remove pan → loudnorm → areverse), CRF + preset, ID3 metadata flags, channel/sample-rate, GIF builder (palettegen+paletteuse), WebP builder (libwebp+loop), thumbnail grid (select+tile), single-frame still, logo overlay via `-filter_complex` ([0:v]…[v0]; [1:v]scale,colorchannelmixer[logo]; [v0][logo]overlay[vout]). Multi-input: `operation=concat` → concat filter complex per input ([0:v:0][0:a:0]…concat=n=N), `operation=mix` → amix filter (duration longest/shortest/first + normalize toggle).
- `app/ui/video_options.py`: panel tabbed (Trim / Transform / Resize / Compress / Watermark / Effects / Animation / Thumbnails / Subtitles) untuk Video page. Effects = reverse + logo overlay; Animation = GIF/WebP fps/width/quality; Thumbnails = grid rows/cols/interval/tile-width; Subtitles = burn-in path picker.
- `app/ui/audio_options.py`: panel tabbed (Trim / Effects / Output) untuk Audio page.
- `app/ui/ocr_options.py`: panel single-pane (Language / PSM / OEM / PDF render DPI / Auto-rotate) untuk OCR page.
- `app/ui/subtitle_options.py`: panel single-pane (Time shift) untuk Subtitle page.
- `app/ui/settings_page.py`: Settings page dengan form output folder / concurrency / quality / DPI.
- `app/core/settings.py`: Settings dataclass + JSON persistence + module-level cache.
- `app/engines/subtitle_engine.py`: Python parser untuk SRT/VTT/ASS, plus multi-input merge (`_collect_merged_cues`) dengan mode shift (cumulative offset + gap) atau append (sort by start), terima campuran format input.
- `app/engines/archive_engine.py`: stdlib zip/tar extractor dengan path-safety guard, plus folder→archive compressor (zip via ZIP_DEFLATED, tar via mode w/w:gz/w:bz2/w:xz).
- `app/engines/qr_engine.py`: qrencode (generate) + zbarimg (decode) wrapper.
- `app/ui/qr_options.py`: panel single-pane untuk QR options (size/margin/ECC).
- `app/ui/multi_input_options.py`: panels untuk `Audio Mix` (duration + normalize), `Image Montage` (tile + geometry + background), `Subtitle Merge` (mode + gap), `PDF Numbering` (format/position/size/start/skip), dan `Slides to Images` (image format + DPI).
- `app/ui/document_options.py`: panel single-pane untuk Document page (PDF/A archival checkbox).
- `app/engines/imagemagick_engine.py`: real ImageMagick engine and image format list.
- `app/engines/libreoffice_engine.py`: real LibreOffice engine — full Document format matrix (text/spreadsheet/presentation, 52 pairs); helper `_find_converted_file` handles arbitrary output extension.
- `app/engines/pdf_engine.py`: real PyMuPDF engine — render to image, extract to TXT/HTML, operasi PDF→PDF (extract_pages/reorder/rotate/compress/repair-via-qpdf/encrypt/decrypt/strip-metadata/edit-metadata/watermark-text/watermark-image/page-numbering), plus operasi pdf→folder (split / extract_images dedupe by xref / extract_attachments via `embfile_*`).
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
401 passed
```

## System Dependencies

Expected binaries:
- `ffmpeg`
- `magick`
- `libreoffice`
- `qpdf`
- `tesseract`
- `qrencode` (QR generate)
- `zbarimg` (QR/barcode decode)
- `inkscape` (SVG / Vector Tools)
- `potrace` (SVG / Vector Tools — pixmap→SVG trace)
- `pandoc` (Ebook module)
- `libimage-exiftool-perl` / `exiftool` (Metadata module)

Install command:

```bash
sudo apt-get update
sudo apt-get install ffmpeg imagemagick libreoffice qpdf tesseract-ocr qrencode zbar-tools inkscape potrace python3-tinycss2 pandoc libimage-exiftool-perl
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

Roadmap lengkap dengan checklist `[x]/[~]/[ ]` ada di `next-development.md`.

**Roadmap fully closed** untuk semua module: Image, Video, Audio, Document, OCR, PDF Tools (DOCX/EPUB/A-B compare/split-by-size/image-downsample/linearize semua selesai), Subtitle, Archive, QR, SVG/Vector (Wave 1+2+3 lengkap, 11 fitur termasuk DXF round-trip + pixmap→SVG trace), Ebook (Pandoc 138 pairs), Metadata (exiftool cross-cut). Cross-cutting items selesai: Settings, drag-and-drop multi-file, preset save/load, preview/details panel, .deb packaging final dengan `dpkg-buildpackage` build script.

Tidak ada follow-up roadmap yang tersisa kecuali optional MOBI via Calibre (di-skip — Calibre dependency 200 MB).

**Catatan arsitektur multi-input**: `Task` punya field `extra_inputs: list[Path]` plus property `inputs` (primary + extras) dan `formats_in` (suffix per input). DB `tasks.sqlite3` dapat kolom baru `extra_inputs TEXT` dengan auto-migration `ALTER TABLE` (deteksi via `PRAGMA table_info`). `ConversionPageConfig` dapat flag `multi_input: bool` (UI: list widget + Add/Remove/Clear + multi-select dialog) dan `default_options: tuple[tuple[str, object], ...]` (force-inject option). POC: PDF Merge page (multi_input=True, force_engine=True, default_options=operation:merge) → `PDFEngine._run_merge` iterate `Document.insert_pdf` untuk setiap source di `task.inputs`. Video concat / audio mix / image montage tinggal tambah engine path baca `task.inputs` + halaman multi_input=True. Multi-output masih ditangani via `directory_output` flag (pattern Archive).

## Codex Session Handoff

At the start of a new Codex CLI session, say:

```text
Baca PROJECT_CONTEXT.md dulu, lalu lanjutkan project ini.
```

Then ask for the specific next change.
