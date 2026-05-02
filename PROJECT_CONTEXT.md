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
- FFmpeg engine nyata dengan progress parsing dan cancel subprocess.
- ImageMagick engine nyata dengan opsi `resize`, `quality`, dan `strip`.
- Stub engine untuk LibreOffice, PDF, dan OCR.
- UI PySide6 dengan sidebar.
- Icon pack `qtawesome`.
- App logo SVG and hicolor PNG icon assets.
- Test suite pytest.

## UI Direction

UI memakai sidebar, bukan toolbar utama.

Sidebar menu:
- Image
- Video
- Document
- PDF Tools

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
- `app/ui/conversion_page.py`: reusable page per category.
- `app/ui/queue_panel.py`: global queue table.
- `app/core/task.py`: task dataclass and status.
- `app/core/queue.py`: async task queue.
- `app/core/registry.py`: conversion registry.
- `app/data/database.py`: SQLite task repository.
- `app/engines/ffmpeg_engine.py`: real FFmpeg engine.
- `app/engines/imagemagick_engine.py`: real ImageMagick engine and image format list.
- `assets/trex-logo.svg`: source app logo.
- `assets/icons/hicolor/`: generated app icons for desktop packaging.

## Run

From project root:

```bash
cd /home/sarta/Downloads/trex-converter
.venv/bin/t-rex-converter
```

Alternative:

```bash
.venv/bin/python -m app.main
```

## Test

```bash
cd /home/sarta/Downloads/trex-converter
.venv/bin/python -m pytest
```

Current expected result:

```text
15 passed
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
- `qasync`
- `qtawesome`

Development dependencies:
- `pytest`
- `pytest-asyncio`

## Next Likely Work

Useful next tasks:
- Implement real LibreOffice engine for document to PDF.
- Implement real PDF tools with QPDF/PyMuPDF.
- Add settings page for default output directory and concurrency.
- Improve queue filtering/history UI.
- Add drag-and-drop file input.
- Add preview/details panel for selected task logs.
- Package `.deb` properly.

## Codex Session Handoff

At the start of a new Codex CLI session, say:

```text
Baca PROJECT_CONTEXT.md dulu, lalu lanjutkan project ini.
```

Then ask for the specific next change.
