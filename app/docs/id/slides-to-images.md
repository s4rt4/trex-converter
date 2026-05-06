# Slides to Images

Render setiap slide presentation jadi PNG atau JPG ke folder.

## Deskripsi

Modul **Slides to Images** terima file PPT, PPTX, ODP dan output ke folder berisi PNG atau JPG per slide. Engine `_slides_to_images` di **LibreOfficeEngine**: convert ke PDF di tempdir dulu, lalu PyMuPDF Pixmap render setiap halaman ke image di DPI configurable.

Output naming `<stem>-001.<ext>`, `<stem>-002.<ext>`, dst.

## Cara pakai

1. Klik **Browse** untuk pilih file presentation.
2. Klik **Select Location** untuk pilih output folder.
3. Atur opsi:
   - **Image format** (png atau jpg).
   - **DPI** (72 sampai 600, default 200).
4. Klik **Add to Queue**.

## Tips & Trick

- **PNG** untuk slide dengan teks dan diagram (lossless, transparency support).
- **JPG** untuk slide dengan banyak photo (smaller file size).
- **DPI 200** untuk on-screen view, 300 untuk print preview, 600 untuk archival quality.
- Naming `001/002/003` zero-padded 3 digit, support sampai 999 slides.

## Troubleshooting

**LibreOffice timeout di slide kompleks.** Slide dengan banyak embedded media butuh waktu render lama. Naikkan timeout di code (sementara) atau split presentation jadi file lebih kecil.

**JPG output ada hitam di edge.** Slide pakai background transparent, jpg tidak support transparency. Pakai PNG.

**File naming tidak urut.** OS file manager kadang sort `slide-1, slide-10, slide-2`. Naming kita zero-padded jadi sort konsisten.
