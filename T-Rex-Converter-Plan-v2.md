# T-Rex Converter

## Project Overview

T-Rex Converter adalah aplikasi native Debian berbasis GUI untuk konversi berbagai jenis file (media, gambar, dokumen, PDF) menggunakan engine backend seperti FFmpeg, ImageMagick, LibreOffice, dan lainnya.

Fokus utama:
- Local processing (tanpa cloud)
- Cepat, modular, dan scalable
- UI modern dengan PySide6
- Engine-based architecture

---

## Tech Stack

| Komponen | Library/Tool | Keterangan |
|---|---|---|
| Language | Python 3.11+ | |
| GUI | PySide6 (Qt6) | Native Debian feel |
| Async | qasync + asyncio | Non-blocking UI |
| Subprocess | `asyncio.create_subprocess_exec` | Konsisten dengan asyncio, bukan QProcess |
| Database | SQLite (via `sqlite3`) | Aktif mulai V0.3+, V0.1 cukup in-memory |
| Video/Audio | FFmpeg | |
| Gambar/Vektor | ImageMagick, Inkscape | |
| Dokumen | LibreOffice headless | |
| PDF | QPDF / PyMuPDF | |
| OCR | Tesseract (via `pytesseract`) | Abstract via `BaseOCREngine` |

> **Keputusan arsitektur:** Gunakan `asyncio.create_subprocess_exec` secara konsisten untuk semua subprocess. Hindari QProcess agar tidak ada coupling Qt di layer engine. Engine harus bisa ditest tanpa GUI.

---

## Folder Structure

```
t-rex-converter/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ task.py           # Task model + TaskStatus enum
│  │  ├─ queue.py          # TaskQueue (in-memory → SQLite)
│  │  ├─ runner.py         # Async task executor
│  │  ├─ dependency.py     # Cek ketersediaan engine di sistem
│  │  ├─ preset.py         # Load/save preset (JSON/TOML)
│  │  └─ registry.py       # Mapping format → engine + kapabilitas
│  ├─ engines/
│  │  ├─ base.py           # BaseEngine abstract class
│  │  ├─ ffmpeg_engine.py
│  │  ├─ imagemagick_engine.py
│  │  ├─ libreoffice_engine.py
│  │  ├─ pdf_engine.py
│  │  └─ ocr_engine.py     # Implements BaseOCREngine
│  ├─ ui/
│  │  ├─ main_window.py
│  │  ├─ queue_panel.py
│  │  ├─ preset_panel.py
│  │  └─ settings_dialog.py
│  ├─ data/
│  │  ├─ database.py       # Aktif mulai V0.3
│  │  └─ models.py
│  └─ utils/
│     ├─ logger.py
│     └─ paths.py
├─ presets/                # Built-in preset files (.toml)
├─ packaging/              # .deb build scripts
├─ tests/
│  ├─ test_engines/
│  ├─ test_queue/
│  └─ test_registry/
├─ README.md
└─ pyproject.toml
```

---

## Core Architecture

### Task Model

Setiap konversi adalah sebuah `Task`. Fields yang diperlukan:

```python
@dataclass
class Task:
    id: str                    # UUID
    input_path: Path
    output_path: Path
    format_in: str             # e.g. "mp4"
    format_out: str            # e.g. "mp3"
    engine: str                # e.g. "ffmpeg"
    options: dict              # Parameter engine-specific (bitrate, quality, dsb)
    status: TaskStatus         # pending | running | success | failed | cancelled
    progress: float            # 0.0 – 1.0
    log: list[str]
    error: str | None          # Pesan error jika status = failed
    retries: int               # Jumlah retry yang sudah dilakukan
    max_retries: int           # Default: 2
```

**TaskStatus enum:**
```
pending → running → success
                  → failed → (retry) → running
                           → cancelled
```

### Queue System

`TaskQueue` mengelola siklus hidup semua task:
- **V0.1:** In-memory queue (list + asyncio.Queue)
- **V0.3+:** Persistent ke SQLite (task history, resume setelah app restart)

Fitur wajib:
- Add, cancel, retry task
- Concurrency limit (max N task berjalan bersamaan, configurable)
- Event emitter untuk update UI (sinyal Qt)

### Engine System

Semua engine inherit dari `BaseEngine`:

```python
class BaseEngine(ABC):
    @abstractmethod
    async def convert(self, task: Task) -> None: ...

    @abstractmethod
    def supports(self, format_in: str, format_out: str) -> bool: ...

    @property
    def capabilities(self) -> EngineCapabilities: ...
```

`EngineCapabilities` menyimpan metadata engine:
```python
@dataclass
class EngineCapabilities:
    supports_progress: bool     # Apakah bisa parse progress realtime
    supports_cancel: bool       # Apakah bisa di-interrupt
    requires_binary: str        # e.g. "ffmpeg", "libreoffice"
```

Ini memungkinkan `runner.py` tahu engine mana yang bisa di-cancel atau ditampilkan progress-nya.

### Registry System

`registry.py` adalah single source of truth untuk routing konversi:

```python
# Contoh mapping
REGISTRY = {
    ("mp4", "mp3"): ("ffmpeg", FFmpegEngine),
    ("jpg", "png"): ("imagemagick", ImageMagickEngine),
    ("docx", "pdf"): ("libreoffice", LibreOfficeEngine),
    ("pdf", "jpg"): ("pdf", PDFEngine),
    ...
}
```

Fungsi utama:
- `resolve(format_in, format_out) → BaseEngine`
- `list_supported_outputs(format_in) → list[str]`
- `is_supported(format_in, format_out) → bool`

### Preset System

Preset adalah named configuration yang bisa disimpan dan di-share:

```toml
# presets/mp3-high-quality.toml
[preset]
name = "MP3 High Quality"
format_in = "mp4"
format_out = "mp3"
engine = "ffmpeg"

[options]
bitrate = "320k"
sample_rate = 44100
```

Preset bisa dibuat user dari UI dan disimpan di `~/.config/t-rex-converter/presets/`.

---

## Roadmap

### V0.1 – Core Foundation
- `BaseEngine` abstract class
- `Task` dataclass + `TaskStatus` enum
- `TaskQueue` (in-memory)
- `DependencyChecker` — deteksi ffmpeg, imagemagick, dll di PATH
- `Registry` dengan stub engine
- UI skeleton (MainWindow + QueuePanel kosong)
- Logging per-task

### V0.2 – Media Engine + Error Handling
- `FFmpegEngine` — MP4→MP3, basic video/audio convert
- Progress parsing dari stdout FFmpeg
- Retry logic di TaskQueue
- Cancel task yang sedang berjalan
- UI: progress bar per task, tombol cancel & retry

### V0.3 – Image Engine + SQLite
- `ImageMagickEngine` — JPG/PNG/WebP, resize, compress
- SVG convert via Inkscape
- Migrasi queue ke SQLite (task history)
- UI: filter task by status, history view

### V0.4 – PDF Tools
- `PDFEngine` — merge, split, compress
- Image ↔ PDF conversion
- Test install `.deb` pertama kali (smoke test packaging)

### V0.5 – Document Engine
- `LibreOfficeEngine` — DOCX/XLSX/PPTX → PDF
- Handle LibreOffice headless edge cases (timeout, lock file)

### V0.6 – Advanced Features
- `OCREngine` via Tesseract (`BaseOCREngine` interface)
- Preset system (create, save, load, export/import JSON)
- Batch processing dengan drag-and-drop multi-file
- Settings dialog (concurrency limit, output folder default, dsb)

### V1.0 – Stable Release
- Full `.deb` packaging dengan `dpkg-buildpackage`
- `postinst` script untuk install dependencies (ffmpeg, libreoffice, tesseract)
- UI polish & accessibility
- README + user documentation

---

## Notes for Development

- Jangan taruh logic di UI — UI hanya emit sinyal dan render state
- Semua konversi lewat engine, semua job lewat queue
- Gunakan `asyncio.create_subprocess_exec` (bukan QProcess) untuk konsistensi
- Engine harus bisa diinstansiasi dan ditest **tanpa** GUI berjalan
- Logging wajib ada di setiap task (append ke `task.log`)
- Buat modular — tiap engine adalah unit independen
- Preset harus portable (bisa di-copy antar mesin)
- SQLite schema harus versioned (siapkan migration dari awal)

---

## Philosophy

> "Fun branding, serious engineering."

T-Rex Converter terlihat fun, tapi di dalamnya harus solid dan scalable. Setiap keputusan arsitektur dibuat untuk kemudahan maintenance jangka panjang, bukan kecepatan development jangka pendek.
