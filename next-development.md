# T-Rex Converter — Next Development Roadmap

Roadmap fitur lanjutan untuk memaksimalkan kemampuan engine yang sudah dipakai (ImageMagick, FFmpeg, LibreOffice, PyMuPDF, Tesseract, qpdf) ditambah usulan modul baru.

Format checklist: `[ ]` belum, `[x]` selesai, `[~]` sebagian.

Setiap task yang selesai ditandai `[x]` dan diberi catatan tanggal/commit pendek bila relevan.

---

## 1. Image Module (ImageMagick)

Tujuan: ekspos kemampuan ImageMagick di luar resize/quality/strip dasar.

- [x] Engine: terjemahkan opsi lanjutan ke argumen ImageMagick (transform, color, filter, watermark, border)
- [x] Engine: ICO multi-resolution otomatis via `-define icon:auto-resize=...`
- [x] UI: `ImageOptionsPanel` dengan section Transform / Color / Filter / Watermark / Output
- [x] Transform: rotate, flip, flop, auto-trim, free-crop `WxH+X+Y`, crop aspect (`1:1`, `4:5`, `16:9`, `3:2`)
- [x] Resize mode: dimension langsung, longest-edge, percent, megapixel target
- [x] Color: grayscale, sepia, negate, normalize, brightness, contrast, gamma
- [x] Filter: blur, sharpen, denoise (-enhance), vignette
- [x] Border & frame: ukuran + warna border
- [x] Watermark teks: konten, posisi (gravity), opacity
- [x] Density (DPI) untuk output raster
- [ ] Watermark gambar (PNG overlay) dengan resize & opacity
- [ ] Smart fit-to-canvas dengan letterbox + warna background
- [ ] Color profile: convert ke sRGB, embed/strip ICC
- [ ] Animated GIF/WebP optimize: dedupe frame, set loop, extract frame ke-N
- [ ] Montage: grid kolase dari N gambar (butuh task multi-input)
- [ ] EXIF granular: strip GPS only, baca/edit tag tertentu (butuh exiftool atau PyExifTool)
- [ ] Batch drag-and-drop banyak gambar sekaligus

## 2. Video Module (FFmpeg)

- [~] Trim/cut by timestamp (start/end), copy codec kalau bisa — trim selesai (re-encode); auto stream-copy belum
- [ ] Concat multi-file (same codec)
- [~] Compress dengan target ukuran (two-pass) atau target CRF — CRF + preset selesai; two-pass target size belum
- [x] Resolution preset 4K → 1080p / 720p / 480p (plus 1440p, 360p)
- [ ] GIF / WebP creator dari clip video (palette gen untuk GIF)
- [ ] Thumbnail / contact sheet (N frame jadi grid)
- [~] Watermark logo overlay (posisi, waktu mulai, opacity) — watermark teks (drawtext) selesai dengan gravity 9-arah dan opacity; logo overlay belum
- [ ] Subtitle burn-in (SRT/ASS hardcode)
- [ ] Subtitle extract dari MKV
- [ ] Hardware acceleration detect (vaapi / nvenc / qsv)
- [x] Speed change (slowmo / timelapse) — 0.5x–2.0x via setpts + atempo
- [x] Rotate / flip / crop video
- [ ] Reverse video

## 3. Audio Module (FFmpeg) — modul baru

Pisahkan dari Video supaya alur pengguna fokus.

- [x] Audio extract dari video (mp3/wav/flac/opus/aac/m4a/ogg) — full matrix video → audio
- [x] Format convert antar codec audio (mp3/wav/aac/flac/m4a/opus/ogg)
- [x] Loudness normalize (EBU R128 `loudnorm`) atau peak normalize — loudnorm I=-16/TP=-1.5/LRA=11
- [x] Trim, fade in/out, gain — gain ±20 dB, fade-in/out via `afade`
- [x] Stereo↔mono, sample-rate / bitrate convert — `-ac` 1/2, `-ar` 22.05k/44.1k/48k/96k, bitrate via main form
- [ ] Merge / mix multi-track
- [~] Tag editor ID3 (title/artist/album/cover art) — title/artist/album/year/genre/track via `-metadata`; cover art belum
- [x] Vocal remove sederhana (center-channel cancel) — `pan=stereo|c0=c0-c1|c1=c1-c0`

## 4. Document Module (LibreOffice)

Saat ini hanya `*→PDF`.

- [x] Output multi-format: DOCX/ODT ↔ DOCX/ODT/RTF/HTML/EPUB/TXT/PDF
- [x] XLSX/ODS ↔ XLSX/ODS/CSV/HTML/PDF
- [~] PPTX/ODP → PNG/JPG slides per-slide — PPTX/ODP↔PPTX/ODP/PDF selesai; render slide ke PNG/JPG belum
- [ ] PDF/A archival output
- [ ] Password-protected PDF export
- [ ] Bulk merge banyak DOCX → 1 PDF

## 5. PDF Tools (PyMuPDF + qpdf)

ROI tertinggi karena tool gratis dan use-case-nya luas.

- [ ] Merge beberapa PDF jadi satu
- [ ] Split by range / by N-pages / by ukuran file
- [x] Extract pages dengan range syntax (`1-3,5,8-10`)
- [x] Reorder & rotate halaman
- [x] Compress (PyMuPDF garbage + deflate + clean) — image downsample dan linearize via qpdf belum
- [x] Encrypt / decrypt (password owner & user) — AES-256
- [~] Watermark teks atau gambar — watermark teks selesai, watermark gambar belum
- [ ] Page numbering / Bates numbering
- [x] Metadata edit (title/author/subject/keywords) atau strip — keduanya selesai (action combo Strip / Edit)
- [x] Repair PDF korup (qpdf) — `qpdf input output` round-trip; treats exit 3 (warnings) as success
- [ ] PDF → DOCX (LibreOffice atau `pdf2docx`)
- [~] PDF → HTML / TXT / EPUB (PyMuPDF native) — TXT dan HTML selesai; EPUB belum
- [ ] Extract embedded images
- [ ] Extract embedded attachments
- [ ] Redaction (PyMuPDF `add_redact_annot`)
- [ ] A/B compare dua PDF (visual diff)

## 6. OCR Module (Tesseract) — naikkan dari stub

- [x] Image → searchable PDF (`tesseract input output pdf`)
- [ ] PDF → searchable PDF (render → OCR layer per halaman → tempel via PyMuPDF)
- [~] Image/PDF → TXT / hOCR / TSV — image (png/jpg/jpeg/tif/tiff/bmp) → TXT/PDF/hOCR/TSV selesai; PDF input belum
- [x] Pemilih multi-language (ind+eng, dst.) — preset eng/ind/eng+ind plus custom field
- [ ] Auto-rotate halaman sebelum OCR

## 7. Modul baru

| Modul | Engine | Status |
|---|---|---|
| Audio | FFmpeg | lihat #3 |
| Subtitle Tools | Python parser + FFmpeg | [~] convert SRT↔VTT selesai dengan shift timing; ASS, merge, burn-in belum |
| Ebook | Pandoc / Calibre | [ ] EPUB↔MOBI↔DOCX↔PDF↔HTML |
| Archive | tar / zip / 7z | [ ] compress/extract sebagai bagian alur batch |
| QR / Barcode | `qrencode` + `zbarimg` | [ ] generate QR, decode dari image |
| Metadata | exiftool | [ ] cross-cut: edit EXIF/ID3/PDF metadata di satu tempat |

## 8. Cross-cutting

- [x] Settings page: default output dir, concurrency, default DPI, default kualitas — disimpan di `~/.config/trex-converter/settings.json`. Concurrency apply on next launch; output_dir apply ke auto-suggested output path immediately
- [ ] Preview/details panel untuk task terpilih (log + thumbnail output)
- [ ] Batch drag-and-drop multi-file
- [ ] Preset save/load per modul
- [ ] Packaging `.deb` final dengan dependency listing

---

## Catatan progres

- 2026-05-04 — Roadmap dibuat. Image module gelombang 1 selesai: transform, color, filter, watermark teks, border/frame, density, ICO auto-resize. UI panel `ImageOptionsPanel` di-mount ke Image page via hook `extra_options_factory` baru di `ConversionPageConfig`. Test suite naik dari 20 ke 29 passed. Item lanjutan image (watermark gambar, ICC profile, animated optimize, montage, EXIF granular, fit-to-canvas, batch drag-drop) tertunda untuk gelombang berikutnya.
- 2026-05-04 — PDF Tools gelombang 1 selesai: extract pages (range syntax), rotate, compress, encrypt/decrypt AES-256, strip metadata, watermark teks (gravity 9-arah + opacity). Engine `PDFEngine` diperluas, panel `PDFOperationsPanel` 5-tab (Pages / Security / Compress / Watermark / Metadata) di-mount ke PDF Tools page lewat `extra_options_factory`. Routing `pdf→pdf` dan `pdf→txt` pindah dari Tesseract ke PDFEngine. Dependency checker mendukung prefix `python:` untuk modul Python. Test suite naik dari 29 ke 45 passed (16 tes baru untuk operasi PDF). Sidebar dapat halaman Dashboard dan About; setiap halaman konversi sekarang punya tab `Convert` / `Queue` dan queue panel dapat thumbnail file.
- 2026-05-04 — Video Module gelombang 1 selesai: trim (start/end), resolution preset 4K/1440p/1080p/720p/480p/360p, compress (CRF + libx264 preset), rotate (0/90/180/270), flip H/V, free crop `WxH+X+Y`, speed change 0.5x–2.0x (setpts + atempo), watermark teks via drawtext (gravity 9-arah, size, opacity). Filter chain order: crop → transpose → flip → scale → setpts → drawtext. Engine `FFmpegEngine` SUPPORTED_PAIRS diperluas ke matrix mp4/mov/mkv/webm + audio extract; registry sekarang generate ffmpeg pairs dari engine constant. Panel `VideoOptionsPanel` 5-tab (Trim / Transform / Resize / Compress / Watermark) di-mount ke Video page. Bug `_output_belongs_to_page` PDF yang menyembunyikan output `pdf` dari combo (akibatnya semua operasi PDF Tools tidak bisa di-trigger dari UI) ikut diperbaiki. Test suite naik dari 45 ke 74 passed (29 tes baru untuk arg builder FFmpeg).
- 2026-05-04 — Audio Module gelombang 1 selesai: trim (start/end), fade-in/out via `afade`, gain ±20 dB via `volume`, loudness normalize (`loudnorm` EBU R128), channel down-mix (`-ac` 1/2), sample-rate convert (`-ar` 22.05k/44.1k/48k/96k), full audio format matrix (mp3/wav/aac/flac/m4a/opus/ogg) plus video → audio extract. Audio filter chain order: atempo → afade-in → afade-out → volume → loudnorm. Panel `AudioOptionsPanel` 3-tab (Trim / Effects / Output) ditambah; sidebar dapat entri Audio (ikon `fa5s.music`). Video page di-trim ke output video-only (mp4/mov/mkv/webm) untuk hindari overlap dengan Audio page. Test suite naik dari 74 ke 85 passed (11 tes baru untuk filter audio + supports).
- 2026-05-04 — OCR Module gelombang 1 selesai: `TesseractOCREngine` naik dari stub ke implementasi nyata (subprocess `tesseract`), input image (png/jpg/jpeg/tif/tiff/bmp) → output txt/pdf/hocr/tsv, pemilih bahasa (preset eng/ind/eng+ind + custom field), PSM 13 mode dan OEM 4 mode picker. Sidebar dapat entri OCR (ikon `fa5s.font`); panel `OCROptionsPanel` (single-pane) di-mount via flag baru `force_engine` di `ConversionPageConfig`. Routing per-page: `ConversionRegistry.engine_by_name(name)` baru, `TaskQueue` menerima callable opsional `engine_by_name` yang dipakai duluan saat `task.engine` di-set; kombinasinya membuat png→pdf bisa di-route ke ImageMagick (Image page) atau Tesseract (OCR page) tanpa konflik di registry. Test suite naik dari 85 ke 101 passed (10 tes OCR engine + 4 registry + 2 queue).
- 2026-05-04 — Document Module gelombang 1 selesai: LibreOffice engine sekarang punya format matrix penuh — text doc (doc/docx/odt/rtf) ↔ docx/odt/rtf/html/epub/txt/pdf, spreadsheet (xls/xlsx/ods) ↔ xlsx/ods/csv/html/pdf, presentation (ppt/pptx/odp) ↔ pptx/odp/pdf (52 pairs total). Helper `_find_converted_file` digeneralisasi dari `_find_converted_pdf` untuk handle ekstensi apa pun. Document page output filter di-tweak agar combo menampilkan semua format dokumen relevan. Test naik 101 → 105 (4 tes baru: text/spreadsheet/presentation supports + non-PDF subprocess flow).
- 2026-05-04 — Subtitle Tools modul baru: engine Python-pure `SubtitleEngine` (no external dep) untuk SRT↔VTT dengan parser regex robust (skip WEBVTT/NOTE/STYLE blocks, optional cue identifier), time shift +/-3600s (clamp ke 0 saat negatif overshoot), `EngineCapabilities.requires_binary=""` ditambah dukungan di `DependencyChecker` (return available untuk binary kosong). Sidebar entri "Subtitle" (ikon `fa5s.closed-captioning`) + panel single-pane time-shift. Test suite +11 (parser, formatter, engine flow).
- 2026-05-04 — Settings page (cross-cutting §8) selesai: `app/core/settings.py` Settings dataclass + JSON persistence di `~/.config/trex-converter/settings.json` + module-level cache (`get_settings`/`set_settings`); fields: `output_dir`, `max_concurrency`, `default_image_quality`, `default_pdf_dpi`. SettingsPage di sidebar (ikon `fa5s.cog`, sebelum About). `runner.create_default_queue` baca `max_concurrency` dari settings (apply on launch); `MainWindow.__init__` juga; `ConversionPage._update_output_path` honor `output_dir` saat suggest path output. Test +6 (load defaults, corrupt JSON, round-trip, unknown keys, non-dict payload). Test suite final 101 → 122 passed.
- 2026-05-05 — Audio Module gelombang 2 mini: ID3 tag editor (title/artist/album/year→date/genre/track via `-metadata`) dan vocal remove (`pan=stereo|c0=c0-c1|c1=c1-c0`). Panel `AudioOptionsPanel` dapat tab "Tags" baru + checkbox "Vocal remove" di tab Effects. Test +4.
- 2026-05-05 — PDF Tools gelombang 2 mini-batch: page reorder (operasi baru, pakai explicit list `3,1,2,4`), edit metadata (title/author/subject/keywords/creator via PyMuPDF `set_metadata`), PDF → HTML (PyMuPDF `get_text("html")` di-wrap dalam dokumen HTML5), repair via qpdf (round-trip, treats exit code 3/warnings sebagai success). Panel `PDFOperationsPanel`: Pages tab dapat aksi "Reorder", Compress tab dapat action combo (Compress/Repair), Metadata tab di-redesign jadi form (action Strip/Edit + 5 field). PDF Tools page input direstrict ke `pdf` only (sebelumnya menerima png/jpg/jpeg yang duplikasi Image page). Test +9 (reorder, edit metadata, html extraction, repair success/warning/error). Test suite final 122 → 135 passed.
