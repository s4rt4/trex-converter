# OCR

Optical character recognition via **Tesseract**.

## Deskripsi

Modul **OCR** wrap `tesseract` untuk extract teks dari image atau PDF ke txt, searchable PDF, hOCR (HTML), atau TSV. Input formats: png, jpg, jpeg, tif, tiff, bmp, plus pdf (auto-render setiap halaman ke PNG @ DPI configurable lalu OCR per halaman lalu stitch).

Panel options: **Language** (preset eng, ind, eng+ind, atau custom), **PSM** (page segmentation mode 13 modes), **OEM** (engine mode 4 modes), **PDF render DPI** (72 sampai 600), **Auto-rotate** (OSD pre-pass).

## Cara pakai

1. Klik **Browse** untuk pilih image atau PDF.
2. Pilih **Output format** (txt, pdf, hocr, tsv).
3. Atur **Language**:
   - Preset eng untuk English saja.
   - Preset ind untuk Indonesian saja.
   - Preset eng+ind untuk dual-language.
   - Custom untuk kombinasi lain (misal `eng+jpn` atau `eng+ara`).
4. Atur **DPI** (default 300, naikkan untuk teks kecil).
5. Centang **Auto-rotate** kalau scan miring (OSD pre-pass detect rotation lalu rotate sebelum OCR).
6. Klik **Add to Queue**.

## Tips & Trick

- **Searchable PDF** retain layout original plus tambah invisible text layer. Pas untuk archive scan ke PDF yang bisa di-search.
- **hOCR output** punya bounding box per word, cocok kalau perlu export ke editor PDF lain.
- **TSV output** punya konfidence score per word, useful untuk filter low-quality OCR.
- **Language pack** install via `apt install tesseract-ocr-{kode}` (misal `tesseract-ocr-ind` untuk Indonesian).
- **Auto-rotate** akurat untuk scan rotation kelipatan 90, kurang akurat untuk skew kecil (kurang dari 5 derajat).

## Troubleshooting

**Output kosong atau garbage.** Tesseract butuh contrast tinggi. Pre-process image: grayscale plus threshold di modul **Image** (Color tab plus Filter tab).

**Language pack missing error.** `tesseract --list-langs` lihat installed packs. Install yang hilang via `apt install tesseract-ocr-<kode>`.

**PDF input lambat.** Tesseract render ulang setiap halaman di DPI tinggi. Turunkan **DPI** ke 200 atau 250 kalau input sudah jelas terbaca.
