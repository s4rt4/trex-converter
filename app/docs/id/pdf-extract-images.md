# PDF Extract Images

Extract semua embedded image dari PDF ke folder.

## Deskripsi

Modul **PDF Extract Images** terima PDF input dan output ke folder berisi image dengan naming `<stem>-pageNNN-imgMM.<ext>`. Engine iterate halaman pakai `Page.get_images(full=True)`, dedupe by xref antar halaman, lalu `Document.extract_image(xref)` keluarkan original bytes plus extension (PNG, JPG, atau format lain).

## Cara pakai

1. Klik **Browse** untuk pilih PDF.
2. Klik **Select Location** untuk pilih output folder.
3. Klik **Add to Queue**.

## Tips & Trick

- **Dedupe by xref** (default ON): image yang sama di-reference dari banyak halaman cuma di-extract sekali. Disable kalau perlu copy per-occurrence.
- Extension keluar sesuai format embedded original (JPG biasanya untuk photo, PNG untuk diagram).
- Naming `pageNNN-imgMM` zero-padded (page 3-digit, image 2-digit).
- Untuk render full page sebagai image (bukan extract embedded), pakai **PDF Tools** dengan output png atau jpg.

## Troubleshooting

**Output folder kosong "No embedded images found".** PDF tidak punya raster image, hanya teks atau vector. Pakai **PDF Tools** render ke PNG kalau perlu image dari halaman.

**Image quality rendah.** Embedded image memang resolution rendah. Extract preserve original quality, tidak ada upscale.

**Banyak duplicate image.** Disable dedupe via option `extract_dedupe=False` (kalau exposed di panel). Default dedupe ON.
