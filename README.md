# T-Rex Converter

T-Rex Converter adalah aplikasi GUI native Debian untuk konversi file lokal. Versi awal ini menyediakan fondasi arsitektur: task queue in-memory, registry format ke engine, dependency checker, engine stub, dan UI skeleton PySide6.

## Status

Current version: `0.3.0`

Implemented:
- Core task model dan status lifecycle.
- Queue in-memory async dengan concurrency limit, cancel, retry, dan event callback.
- Dependency checker berbasis `PATH`.
- Registry untuk routing format ke engine.
- Tesseract OCR engine: image (png/jpg/jpeg/tif/tiff/bmp) DAN PDF input → searchable PDF / TXT / hOCR / TSV dengan pemilih bahasa, PSM, OEM, render DPI 72–600 (default 300), dan auto-rotate via OSD pre-pass.
- LibreOffice document engine dengan format matrix penuh: text docs ↔ DOCX/ODT/RTF/HTML/EPUB/TXT/PDF, spreadsheets ↔ XLSX/ODS/CSV/HTML/PDF, presentations ↔ PPTX/ODP/PDF. Plus PDF/A archival output, password-protected PDF export (user/owner), dan slide rendering (presentation → folder PNG/JPG dengan DPI configurable).
- Subtitle engine Python-pure: SRT ↔ VTT ↔ ASS round-trip dengan time shift; ASS parser handle Format header detection, Dialogue rows, escape `\N`, dan Comment skip.
- Archive engine Python-pure (stdlib `zipfile` + `tarfile`): extract zip/tar/tgz/tbz/txz/gz/bz2/xz → folder dengan path-traversal guard, plus compress folder → zip/tar/tgz/tbz/txz.
- QR / Barcode engine: `qrencode` (txt → png/svg dengan size/margin/ECC L-M-Q-H) + `zbarimg` (image → txt, `--raw`).
- Settings page dengan persisten JSON: default output folder, concurrency, image quality, PDF DPI.
- FFmpeg engine via `asyncio.create_subprocess_exec` dengan progress parser, cancel, trim (start/end), resolution preset 4K/1440p/1080p/720p/480p/360p, compress (CRF + libx264 preset), rotate, flip H/V, free crop, speed change 0.5x–2.0x, watermark teks (drawtext, gravity 9-arah + opacity), reverse video (`reverse`+`areverse`), logo overlay watermark via `-filter_complex` dengan 9-arah + scale + opacity, GIF creator (palettegen+paletteuse), animated WebP (libwebp+loop), contact sheet ke PNG/JPG (select+tile), single-frame still, dan subtitle burn-in (`subtitles=`/`ass=` filter).
- Audio module: full audio↔audio matrix (mp3/wav/aac/flac/m4a/opus/ogg) plus video→audio extract; trim, fade-in/out, gain ±20 dB, EBU R128 loudness normalize, vocal remove (center-channel cancel), channel down-mix, sample-rate convert, dan ID3 tag editor (title/artist/album/year/genre/track).
- ImageMagick engine lengkap dengan transform (rotate/flip/flop/trim/crop/aspect crop), resize modes (dimension/longest-edge/percent/megapixel), fit-to-canvas dengan letterbox + background color, color (grayscale/sepia/negate/normalize/brightness/contrast/gamma), filter (blur/sharpen/denoise/vignette), border & frame, text watermark, density, dan ICO multi-resolution.
- PDF engine via PyMuPDF + qpdf: render halaman ke PNG/JPG, ekstrak ke TXT/HTML, operasi PDF→PDF (extract pages, reorder, rotate, compress, repair via qpdf, encrypt/decrypt AES-256, strip/edit metadata, watermark teks/gambar, page numbering / Bates dengan template `{n}`/`{total}`/`{page}`, redact via search-and-apply), plus operasi pdf→folder (split, extract embedded images, extract embedded attachments).
- SQLite task repository untuk history dan resume pending/running task.
- UI skeleton terhubung ke queue: progress bar per task, tombol cancel dan retry.
- App logo SVG plus hicolor PNG assets untuk integrasi desktop Debian.
- Tests untuk core queue, registry, dependency, dan base engine behavior.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run GUI:

```bash
t-rex-converter
```

Atau:

```bash
python -m app.main
```

Regenerate PNG icon assets from the SVG logo:

```bash
scripts/generate-icons.sh
```

## Runtime Dependencies

Engine asli membutuhkan binary sistem sesuai fitur:
- `ffmpeg`
- `magick` atau `convert`
- `libreoffice`
- `qpdf`
- `tesseract`
- `qrencode` (QR generate)
- `zbarimg` (QR/barcode decode, paket `zbar-tools`)

PDF extract membutuhkan dependency Python `PyMuPDF` dari `pyproject.toml`.

Install di Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install ffmpeg imagemagick libreoffice qpdf tesseract-ocr qrencode zbar-tools
```

ImageMagick bisa tersedia sebagai `magick` atau `convert`, tergantung versi distro.
