# T-Rex Converter

T-Rex Converter adalah aplikasi GUI native Debian untuk konversi file lokal. Versi awal ini menyediakan fondasi arsitektur: task queue in-memory, registry format ke engine, dependency checker, engine stub, dan UI skeleton PySide6.

## Status

Current version: `0.3.0`

Implemented:
- Core task model dan status lifecycle.
- Queue in-memory async dengan concurrency limit, cancel, retry, dan event callback.
- Dependency checker berbasis `PATH`.
- Registry untuk routing format ke engine.
- Engine abstraction plus stub engine untuk LibreOffice, PDF, dan OCR.
- FFmpeg engine dasar via `asyncio.create_subprocess_exec`, progress parser, cancel, dan option audio/video sederhana.
- ImageMagick engine dasar via `asyncio.create_subprocess_exec`, dengan opsi `resize`, `quality`, dan `strip`.
- SQLite task repository untuk history dan resume pending/running task.
- UI skeleton terhubung ke queue: progress bar per task, tombol cancel dan retry.
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

## Runtime Dependencies

Engine asli membutuhkan binary sistem sesuai fitur:
- `ffmpeg`
- `magick` atau `convert`
- `libreoffice`
- `qpdf`
- `tesseract`

Install di Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install ffmpeg imagemagick libreoffice qpdf tesseract-ocr
```

ImageMagick bisa tersedia sebagai `magick` atau `convert`, tergantung versi distro.
