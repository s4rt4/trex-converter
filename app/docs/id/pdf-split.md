# PDF Split

Pecah satu PDF jadi banyak file dengan tiga mode: every-N, custom range, atau by file size.

## Deskripsi

Modul **PDF Split** terima satu PDF input dan output ke folder berisi banyak file `<stem>-001.pdf`, `<stem>-002.pdf`, dst. Engine `_run_split` di **PDFEngine** dispatch by mode:

- **Every N pages**: chunk consecutive N halaman per file.
- **Custom ranges**: comma-separated 1-based ranges (`1-5, 6-10, 11-20`), tiap range jadi satu file.
- **By file size**: pack halaman ke chunk doc, serialize, kalau exceeds limit rollback halaman terakhir dan finalize chunk sebelumnya.

## Cara pakai

1. Klik **Browse** untuk pilih PDF.
2. Klik **Select Location** untuk pilih output folder.
3. Pilih **Mode**:
   - **Every N pages** dan set **Pages per file**.
   - **Custom ranges** dan set **Ranges** (misal `1-3, 4-6, 7-10`).
   - **By file size (MB)** dan set **Max chunk size**.
4. Klik **Add to Queue**.

## Tips & Trick

- **By file size** berguna untuk email attachment limit (misal 25 MB Gmail). Set **Max chunk size** ke 24 MB.
- **Custom ranges** boleh overlap atau gap. Engine tidak validasi consistency, hanya minta tiap range valid.
- Output naming `<stem>-NNN.pdf` zero-padded 3 digit, support sampai 999 chunks.
- Untuk extract halaman tertentu (bukan pecah jadi banyak file), pakai **PDF Tools** Pages tab Extract action.

## Troubleshooting

**Output folder kosong.** Mode **By file size** dengan limit terlalu besar (lebih besar dari source). Output cuma 1 file (= source) yang langsung saved.

**"split_size_mb requires positive number".** Lupa isi **Max chunk size** atau set 0. Set ke nilai positif misal 5 atau 10.

**Halaman ke-skip atau duplikat di Custom ranges.** Range salah atau overlap. Verifikasi dulu dengan view source PDF di reader, lalu adjust range.
