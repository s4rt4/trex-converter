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

- [ ] Audio extract dari video (mp3/wav/flac/opus/aac)
- [ ] Format convert antar codec audio
- [ ] Loudness normalize (EBU R128 `loudnorm`) atau peak normalize
- [ ] Trim, fade in/out, gain
- [ ] Stereo↔mono, sample-rate / bitrate convert
- [ ] Merge / mix multi-track
- [ ] Tag editor ID3 (title/artist/album/cover art)
- [ ] Vocal remove sederhana (center-channel cancel)

## 4. Document Module (LibreOffice)

Saat ini hanya `*→PDF`.

- [ ] Output multi-format: DOCX/ODT ↔ DOCX/ODT/RTF/HTML/EPUB/TXT
- [ ] XLSX/ODS ↔ CSV/HTML/PDF
- [ ] PPTX/ODP → PNG/JPG slides per-slide
- [ ] PDF/A archival output
- [ ] Password-protected PDF export
- [ ] Bulk merge banyak DOCX → 1 PDF

## 5. PDF Tools (PyMuPDF + qpdf)

ROI tertinggi karena tool gratis dan use-case-nya luas.

- [ ] Merge beberapa PDF jadi satu
- [ ] Split by range / by N-pages / by ukuran file
- [x] Extract pages dengan range syntax (`1-3,5,8-10`)
- [~] Reorder & rotate halaman — rotate selesai, reorder belum
- [x] Compress (PyMuPDF garbage + deflate + clean) — image downsample dan linearize via qpdf belum
- [x] Encrypt / decrypt (password owner & user) — AES-256
- [~] Watermark teks atau gambar — watermark teks selesai, watermark gambar belum
- [ ] Page numbering / Bates numbering
- [~] Metadata edit (title/author/subject/keywords) atau strip — strip selesai, edit belum
- [ ] Repair PDF korup (qpdf)
- [ ] PDF → DOCX (LibreOffice atau `pdf2docx`)
- [~] PDF → HTML / TXT / EPUB (PyMuPDF native) — TXT selesai, HTML/EPUB belum
- [ ] Extract embedded images
- [ ] Extract embedded attachments
- [ ] Redaction (PyMuPDF `add_redact_annot`)
- [ ] A/B compare dua PDF (visual diff)

## 6. OCR Module (Tesseract) — naikkan dari stub

- [ ] Image → searchable PDF (`tesseract input output pdf`)
- [ ] PDF → searchable PDF (render → OCR layer per halaman → tempel via PyMuPDF)
- [ ] Image/PDF → TXT / hOCR / TSV
- [ ] Pemilih multi-language (ind+eng, dst.)
- [ ] Auto-rotate halaman sebelum OCR

## 7. Modul baru

| Modul | Engine | Status |
|---|---|---|
| Audio | FFmpeg | lihat #3 |
| Subtitle Tools | FFmpeg + parser teks | [ ] convert SRT↔VTT↔ASS, shift timing, merge, burn-in |
| Ebook | Pandoc / Calibre | [ ] EPUB↔MOBI↔DOCX↔PDF↔HTML |
| Archive | tar / zip / 7z | [ ] compress/extract sebagai bagian alur batch |
| QR / Barcode | `qrencode` + `zbarimg` | [ ] generate QR, decode dari image |
| Metadata | exiftool | [ ] cross-cut: edit EXIF/ID3/PDF metadata di satu tempat |

## 8. Cross-cutting

- [ ] Settings page: default output dir, concurrency, default DPI, default kualitas
- [ ] Preview/details panel untuk task terpilih (log + thumbnail output)
- [ ] Batch drag-and-drop multi-file
- [ ] Preset save/load per modul
- [ ] Packaging `.deb` final dengan dependency listing

---

## Catatan progres

- 2026-05-04 — Roadmap dibuat. Image module gelombang 1 selesai: transform, color, filter, watermark teks, border/frame, density, ICO auto-resize. UI panel `ImageOptionsPanel` di-mount ke Image page via hook `extra_options_factory` baru di `ConversionPageConfig`. Test suite naik dari 20 ke 29 passed. Item lanjutan image (watermark gambar, ICC profile, animated optimize, montage, EXIF granular, fit-to-canvas, batch drag-drop) tertunda untuk gelombang berikutnya.
- 2026-05-04 — PDF Tools gelombang 1 selesai: extract pages (range syntax), rotate, compress, encrypt/decrypt AES-256, strip metadata, watermark teks (gravity 9-arah + opacity). Engine `PDFEngine` diperluas, panel `PDFOperationsPanel` 5-tab (Pages / Security / Compress / Watermark / Metadata) di-mount ke PDF Tools page lewat `extra_options_factory`. Routing `pdf→pdf` dan `pdf→txt` pindah dari Tesseract ke PDFEngine. Dependency checker mendukung prefix `python:` untuk modul Python. Test suite naik dari 29 ke 45 passed (16 tes baru untuk operasi PDF). Sidebar dapat halaman Dashboard dan About; setiap halaman konversi sekarang punya tab `Convert` / `Queue` dan queue panel dapat thumbnail file.
- 2026-05-04 — Video Module gelombang 1 selesai: trim (start/end), resolution preset 4K/1440p/1080p/720p/480p/360p, compress (CRF + libx264 preset), rotate (0/90/180/270), flip H/V, free crop `WxH+X+Y`, speed change 0.5x–2.0x (setpts + atempo), watermark teks via drawtext (gravity 9-arah, size, opacity). Filter chain order: crop → transpose → flip → scale → setpts → drawtext. Engine `FFmpegEngine` SUPPORTED_PAIRS diperluas ke matrix mp4/mov/mkv/webm + audio extract; registry sekarang generate ffmpeg pairs dari engine constant. Panel `VideoOptionsPanel` 5-tab (Trim / Transform / Resize / Compress / Watermark) di-mount ke Video page. Bug `_output_belongs_to_page` PDF yang menyembunyikan output `pdf` dari combo (akibatnya semua operasi PDF Tools tidak bisa di-trigger dari UI) ikut diperbaiki. Test suite naik dari 45 ke 74 passed (29 tes baru untuk arg builder FFmpeg).
