# PDF Compare

Visual diff dua PDF, output diff image per halaman.

## Deskripsi

Modul **PDF Compare** terima dua PDF (left dan right), render setiap halaman dari kedua PDF via PyMuPDF Pixmap di DPI configurable, lalu jalankan `magick compare -metric AE -fuzz N% L.png R.png diff.png`. Diff image highlight pixel yang berbeda.

Output ke folder dengan naming `<stem>-pageNNN-diff.png`. Page-count mismatch: cap ke `min(left_pages, right_pages)` dan log info.

## Cara pakai

1. Klik **Add files** dan pilih dua PDF (left dan right). Order: file pertama di list = left, kedua = right.
2. Klik **Select Location** untuk pilih output folder.
3. (Tidak ada panel options khusus, default DPI 150 dan fuzz 5%.)
4. Klik **Add to Queue**.

## Tips & Trick

- **Fuzz** parameter di engine (default 5%) tolerate small color shift dari rendering. Naikkan untuk ignore minor anti-aliasing diff.
- **DPI** lebih tinggi = diff lebih detail, tapi proses lebih lama. Default 150 cukup untuk visual review.
- AE metric (absolute error) di log task tunjukkan jumlah differing pixels per halaman. Berguna untuk regression test.
- Untuk text-level diff (bukan pixel), pakai `pdftotext` lalu `diff` di terminal.

## Troubleshooting

**Output folder kosong.** Cuma satu file di list. PDF Compare butuh dua input.

**"Both PDFs must have at least one page".** Salah satu PDF empty atau corrupt. Verifikasi di reader.

**Diff image semua merah / banyak diff palsu.** Page rotation atau page size beda antar PDF. Pastikan dua PDF generated dengan setting sama, atau rotate dulu di **PDF Tools**.

**ImageMagick compare tidak terpasang.** Install: `apt install imagemagick`. Compare adalah tool dari paket ini, bukan binary terpisah.
