# T-Rex Converter

T-Rex Converter adalah aplikasi GUI native Debian untuk konversi file lokal. Versi awal ini menyediakan fondasi arsitektur: task queue in-memory, registry format ke engine, dependency checker, engine stub, dan UI skeleton PySide6.

## Status

Current version: `0.3.0`

Implemented:
- Core task model dan status lifecycle.
- Queue in-memory async dengan concurrency limit, cancel, retry, dan event callback.
- Dependency checker berbasis `PATH`.
- Registry untuk routing format ke engine.
- Tesseract OCR engine: image (png/jpg/jpeg/tif/tiff/bmp) → searchable PDF / TXT / hOCR / TSV dengan pemilih bahasa, PSM, dan OEM.
- FFmpeg engine via `asyncio.create_subprocess_exec` dengan progress parser, cancel, trim (start/end), resolution preset 4K/1440p/1080p/720p/480p/360p, compress (CRF + libx264 preset), rotate, flip H/V, free crop, speed change 0.5x–2.0x, dan watermark teks (drawtext, gravity 9-arah + opacity).
- Audio module: full audio↔audio matrix (mp3/wav/aac/flac/m4a/opus/ogg) plus video→audio extract; trim, fade-in/out, gain ±20 dB, EBU R128 loudness normalize, channel down-mix, sample-rate convert.
- ImageMagick engine lengkap dengan transform (rotate/flip/flop/trim/crop/aspect crop), resize modes (dimension/longest-edge/percent/megapixel), color (grayscale/sepia/negate/normalize/brightness/contrast/gamma), filter (blur/sharpen/denoise/vignette), border & frame, text watermark, density, dan ICO multi-resolution.
- LibreOffice engine dasar via `asyncio.create_subprocess_exec` untuk document-to-PDF, timeout, cancel, dan output renaming.
- PDF engine via PyMuPDF: render halaman ke PNG/JPG, ekstrak teks ke TXT, plus operasi PDF→PDF (extract pages dengan range syntax, rotate, compress, encrypt/decrypt AES-256, strip metadata, watermark teks dengan 9-position gravity dan opacity).
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

PDF extract membutuhkan dependency Python `PyMuPDF` dari `pyproject.toml`.

Install di Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install ffmpeg imagemagick libreoffice qpdf tesseract-ocr
```

ImageMagick bisa tersedia sebagai `magick` atau `convert`, tergantung versi distro.
