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
- [x] Montage: grid kolase dari N gambar — Image Montage page (multi_input + force_engine + default_options=operation:montage) → ImageMagick `montage` subcommand dengan tile (auto sqrt-ish atau eksplisit `3x3`), geometry, background color.
- [ ] EXIF granular: strip GPS only, baca/edit tag tertentu (butuh exiftool atau PyExifTool)
- [ ] Batch drag-and-drop banyak gambar sekaligus

## 2. Video Module (FFmpeg)

- [~] Trim/cut by timestamp (start/end), copy codec kalau bisa — trim selesai (re-encode); auto stream-copy belum
- [x] Concat multi-file — Video Concat page (multi_input + force_engine + default_options=operation:concat) → FFmpeg `concat` filter complex (re-encode, v=1:a=1 untuk video, v=0:a=1 untuk audio output).
- [~] Compress dengan target ukuran (two-pass) atau target CRF — CRF + preset selesai; two-pass target size belum
- [x] Resolution preset 4K → 1080p / 720p / 480p (plus 1440p, 360p)
- [x] GIF / WebP creator dari clip video (palette gen untuk GIF) — palettegen + paletteuse untuk GIF, libwebp + loop=0 untuk WebP animasi
- [x] Thumbnail / contact sheet (N frame jadi grid) — `select=not(mod(n,N))` + `tile=ColsxRows` ke PNG/JPG
- [x] Watermark logo overlay (posisi, waktu mulai, opacity) — overlay via `-filter_complex` dengan gravity 9-arah, scale, dan opacity (`colorchannelmixer=aa`); watermark teks tetap tersedia
- [x] Subtitle burn-in (SRT/ASS hardcode) — `subtitles=` filter (.srt/.vtt) atau `ass=` filter (.ass/.ssa) di video filter chain
- [ ] Subtitle extract dari MKV
- [ ] Hardware acceleration detect (vaapi / nvenc / qsv)
- [x] Speed change (slowmo / timelapse) — 0.5x–2.0x via setpts + atempo
- [x] Rotate / flip / crop video
- [x] Reverse video — `reverse` + `areverse` filter (terakhir di chain)

## 3. Audio Module (FFmpeg) — modul baru

Pisahkan dari Video supaya alur pengguna fokus.

- [x] Audio extract dari video (mp3/wav/flac/opus/aac/m4a/ogg) — full matrix video → audio
- [x] Format convert antar codec audio (mp3/wav/aac/flac/m4a/opus/ogg)
- [x] Loudness normalize (EBU R128 `loudnorm`) atau peak normalize — loudnorm I=-16/TP=-1.5/LRA=11
- [x] Trim, fade in/out, gain — gain ±20 dB, fade-in/out via `afade`
- [x] Stereo↔mono, sample-rate / bitrate convert — `-ac` 1/2, `-ar` 22.05k/44.1k/48k/96k, bitrate via main form
- [x] Merge / mix multi-track — Audio Mix page (multi_input + force_engine + default_options=operation:mix) → FFmpeg `amix` filter dengan opsi duration (longest/shortest/first) dan toggle normalize.
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

- [x] Merge beberapa PDF jadi satu — POC pertama dari refactor multi-input Task model. PDF Merge sidebar page (multi_input + force_engine + default_options=operation:merge) feed `task.inputs` ke `PDFEngine._run_merge` yang iterate `Document.insert_pdf` per source.
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
- [x] PDF → searchable PDF (render → OCR layer per halaman → tempel via PyMuPDF) — render dengan PyMuPDF Pixmap @ 300 DPI default, OCR per halaman ke tmpfile, stitch via `Document.insert_pdf`
- [x] Image/PDF → TXT / hOCR / TSV — image input (png/jpg/jpeg/tif/tiff/bmp) plus PDF input dengan stitcher (form-feed untuk TXT, ocr_page divs untuk hOCR, header tunggal + rows untuk TSV)
- [x] Pemilih multi-language (ind+eng, dst.) — preset eng/ind/eng+ind plus custom field
- [x] Auto-rotate halaman sebelum OCR — pre-pass `tesseract -- --psm 0` per halaman, parse `Rotate: N`, apply via `page.set_rotation` lalu re-render

## 7. Modul baru

| Modul | Engine | Status |
|---|---|---|
| Audio | FFmpeg | lihat #3 |
| Subtitle Tools | Python parser + FFmpeg | [x] SRT↔VTT↔ASS round-trip selesai (parser ASS minimal subset Dialogue events), burn-in via FFmpeg `subtitles=`/`ass=` filter di Video page, dan Subtitle Merge page (multi_input) dengan mode shift (cumulative offset + gap) atau append (sort by start) — terima campuran format input |
| Ebook | Pandoc / Calibre | [ ] EPUB↔MOBI↔DOCX↔PDF↔HTML |
| Archive | tar / zip (stdlib) | [~] extract zip/tar/tgz/tbz/txz/gz/bz2/xz → folder selesai (path-traversal & absolute-path guard, `tarfile.extract(filter='data')`); compress folder → archive belum |
| QR / Barcode | `qrencode` + `zbarimg` | [x] generate (txt → png/svg dengan size/margin/ECC L-M-Q-H) + decode (png/jpg/jpeg/bmp/tif/tiff/gif/webp → txt via zbarimg `--raw`) |
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
- 2026-05-05 — Video Module gelombang 2 selesai: GIF creator via `palettegen`+`paletteuse` filter graph (fps + width + Lanczos scale), animated WebP via `libwebp -loop 0` codec dengan quality 0–100, contact sheet (N frame jadi grid via `select='not(mod(n,interval))',scale,tile=COLSxROWS`) ke PNG/JPG, single-frame still extraction tanpa thumbnail_grid, logo overlay watermark dengan gravity 9-arah + scale + opacity (`colorchannelmixer=aa`) via `-filter_complex` (input kedua + map [vout] + map 0:a?), reverse video (`reverse`+`areverse` di akhir chain), dan subtitle burn-in (`subtitles=`/`ass=` filter dengan path escaping). FFmpegEngine SUPPORTED_PAIRS diperluas: video → gif/webp/png/jpg/jpeg. Panel `VideoOptionsPanel` dapat 4 tab baru: Effects (reverse + logo), Animation (GIF/WebP fps/width/quality), Thumbnails (grid rows/cols/interval/tile-width), Subtitles (burn-in path picker). Conversion page `_output_belongs_to_page` video kind diperluas ke {mp4, mov, mkv, webm, gif, webp, png, jpg, jpeg}. Test +17 (GIF palettegen, GIF override + chain, WebP libwebp, thumbnail grid, single-frame image, image with vf chain, logo basic + position/opacity + chain + audio-skip, reverse + chain, subtitle burn srt/ass + escape).
- 2026-05-05 — OCR Module gelombang 2: PDF input pipeline lengkap. Render setiap halaman PDF → PNG via PyMuPDF Pixmap (default 300 DPI, range 72–600), OCR per halaman ke tmpfile, lalu stitch ke target output. Stitching: PDF via `Document.insert_pdf`, TXT dengan `\f` form-feed antar halaman, hOCR dengan `<div class='ocr_page'>` divs di-renumber ID page_1..N, TSV dengan header tunggal + rows concat. Auto-rotate via OSD pre-pass (`tesseract image - --psm 0`) parsing `Rotate: N` (normalize ke {0,90,180,270}, fallback 0 untuk non-canonical), apply via `page.set_rotation` lalu re-render. SUPPORTED_PAIRS naik: pdf × {txt, pdf, hocr, tsv} ditambahkan. Helper `parse_osd_rotation`, `stitch_text_pages`, `stitch_hocr_pages`, `stitch_tsv_pages` di-expose. OCROptionsPanel dapat field DPI (72–600) dan checkbox Auto-rotate. OCR page input formats `pdf` ditambah. Test +12 (osd parse 3 cases, stitch txt/hocr/tsv 5 cases, full pdf pipeline, failure propagation, support-pair check).
- 2026-05-05 — Archive Module gelombang 1: extraction-only via stdlib `zipfile`+`tarfile` (no extra dependency, `requires_binary=""`). Input formats: zip, tar, tgz, tbz, txz, plus gz/bz2/xz aliases (Python `tarfile.open(mode="r:*")` auto-detects compression). Output is selalu `folder` (sentinel), engine extract ke `Path(output_path)` dan create directory. Security: `_ensure_safe_member` reject absolute paths dan path-traversal entries (`../escape.txt`); tar extract pakai `filter='data'` (Python 3.14 default-safe). New `directory_output` flag di `ConversionPageConfig` membuat `_choose_output` pakai `QFileDialog.getExistingDirectory` dan `_update_output_path` taruh hasil di `<base>/<input_stem>` (no extension). Sidebar entri "Archive" (ikon `fa5s.file-archive`). `_output_belongs_to_page` archive kind cuma allow `folder`. Test +8 (zip basic, traversal reject, absolute reject, tar plain, tgz, tar.xz alias, supports matrix, unsupported pair). Test 170 → 178 passed.
- 2026-05-05 — Multi-input wave: 4 page baru pakai foundation `Task.extra_inputs`. **Video Concat** (`mp4/mov/mkv/webm` × N → `mp4/mov/mkv/webm`) dispatch via `options.operation=concat` → FFmpeg `concat` filter complex (`[0:v:0][0:a:0]…concat=n=N:v=1:a=1[outv][outa]` + `-map`). Audio-only output gunakan `v=0:a=1`. **Audio Mix** (audio × N → audio) dispatch via `options.operation=mix` → FFmpeg `amix` filter (`amix=inputs=N:duration=<longest|shortest|first>:normalize=<0|1>`). **Image Montage** (image × N → image) dispatch via `options.operation=montage` → ImageMagick `montage` subcommand (auto-tile via `sqrt(N)` ceil, atau eksplisit `WxH`), `-geometry WxH+X+Y` validation, `-background` color. **Subtitle Merge** (subtitle × N → subtitle, terima campuran format) dispatch via `options.operation=merge` atau implicit kalau `extra_inputs` non-empty → Python concat cues dengan mode `shift` (cumulative offset + gap, default) atau `append` (sort by start). Subtitle merge handler refactor jadi `_collect_merged_cues` reusable. New panel `app/ui/multi_input_options.py` (`AudioMixOptionsPanel` / `ImageMontageOptionsPanel` / `SubtitleMergeOptionsPanel`); Video Concat tanpa panel (defaults). Sidebar dapat 4 entri baru (`fa5s.film` / `fa5s.compact-disc` / `fa5s.th` / `fa5s.layer-group`). `_output_belongs_to_page` cover 4 kind baru. Test +17 (concat video/audio + count guard, mix default + override + invalid duration, montage 4-input auto-tile + explicit + bg + min-input + invalid tile/geometry, subtitle shift + gap + append sort + mixed format + min-input + unknown mode). Test 207 → 224 passed.
- 2026-05-05 — Refactor `Task` untuk multi-input + POC PDF Merge. `Task.extra_inputs: list[Path]` (default empty) ditambahkan; `__post_init__` coerce ke `Path`. Property baru `Task.inputs` (primary + extras) dan `Task.formats_in` (suffix per input). DB `tasks` dapat kolom `extra_inputs TEXT NOT NULL DEFAULT '[]'`; `_migrate` jalankan `ALTER TABLE ADD COLUMN` saat detect kolom hilang via `PRAGMA table_info`. `task_to_record`/`task_from_row` JSON-encode/decode list path; row helper `_row_get` defensive untuk legacy DB. `ConversionPageConfig` dapat `multi_input: bool` (UI: `QListWidget` + Add/Remove/Clear, multi-select dialog `getOpenFileNames`) dan `default_options: tuple[tuple[str, object], ...]` (force-inject option seperti `operation=merge`). `ConversionPage` refactor: `_input_path` → `_input_paths: list[Path]`, helper `_primary_input()`. POC: `PDFEngine._run_merge` iterate `task.inputs` dan pakai `Document.insert_pdf` per source, validasi minimum 2 input + reject encrypted PDF. Sidebar entri "PDF Merge" (ikon `fa5s.copy`, multi_input + force_engine + default_options=operation:merge). Test +12 (Task multi-input properties, DB extra_inputs persistence + legacy migration, merge 2/3 PDF, ordering follows task.inputs, encrypted reject). Test 195 → 207 passed.
- 2026-05-05 — QR/Barcode modul baru: `QREngine` wrapping `qrencode` (generate) dan `zbarimg` (decode). Generate: txt → png/svg dengan opsi `qr_size` (1–50 px/dot), `qr_margin` (0–32 dots), `qr_ecc_level` (L/M/Q/H, normalize lowercase ke uppercase). Pakai `qrencode -r INPUT -o OUTPUT -t (PNG|SVG) [-s] [-m] [-l]`. Decode: png/jpg/jpeg/bmp/tif/tiff/gif/webp → txt via `zbarimg --raw -q INPUT`, exit code 4 (no barcodes) di-translate jadi "no barcodes" error, payload non-empty ditulis ke output `.txt`. `EngineCapabilities` dapat field baru `extra_binaries: tuple[str, ...] = ()` untuk advertise binary sekunder; `requires_binary="qrencode"` + `extra_binaries=("zbarimg",)`. `registry.required_binaries()` sekarang collect both primary + extras. Sidebar entri "QR / Barcode" (ikon `fa5s.qrcode`) dengan `force_engine=True` supaya png→txt di QR page route ke qr (bukan tesseract default). Panel single-pane (Module size / Margin / Error correction). `_output_belongs_to_page` qr kind allow {png, svg, txt}. Test +14 untuk qr engine + 4 registry. Test 178 → 195 passed.
- 2026-05-05 — Subtitle Module gelombang 2: ASS support penuh. Parser ASS minimal subset menangani section dispatcher `[Events]` + Format header detection (cari kolom `text`) + Dialogue rows dengan split bounded oleh text-field index (preserve koma di Text), `\N`/`\n` escape sequences, Comment lines diskip. Formatter ASS emit Script Info + V4+ Styles + Events dengan default Style "Arial 32px white" dan Dialogue per cue. Time format ASS: `H:MM:SS.cc` (centiseconds 2-digit). Round-trip ASS↔ASS preserve cues. SubtitleEngine dispatch table jadi `parsers/formatters` map (srt/vtt/ass) supaya pasangan format tinggal lookup. Subtitle page input formats sekarang `(srt, vtt, ass)`, output filter halaman juga ditambahkan ASS. Burn-in selesai di Video module (lihat di atas). Test +8 (ASS parse + comma-in-text + Comment skip, format script-info + newline-escape + centisecond pad, round-trip, srt→ass + ass→srt+shift). Test suite final 135 → 170 passed.
