# QR / Barcode

Generate QR code dari teks plus decode QR/barcode dari image.

## Deskripsi

Modul **QR / Barcode** wrap dua binary:

- **Generate**: `qrencode` untuk teks ke png atau svg dengan size, margin, error correction level.
- **Decode**: `zbarimg` untuk image (png, jpg, jpeg, bmp, tif, tiff, gif, webp) ke txt. Decode banyak jenis barcode 1D dan 2D, bukan QR saja.

## Cara pakai

### Generate (txt ke png/svg)

1. Klik **Browse** untuk pilih file `.txt` berisi konten yang mau di-encode.
2. Pilih **Output format** png atau svg.
3. Atur opsi:
   - **Module size** (px per dot, 1 sampai 50, default 8).
   - **Margin** (dots, 0 sampai 32, default 2).
   - **Error correction**: L (~7%), M (~15%, default), Q (~25%), H (~30%).
4. Klik **Add to Queue**.

### Decode (image ke txt)

1. Klik **Browse** untuk pilih image yang ada QR atau barcode.
2. Pilih **Output format** txt.
3. Klik **Add to Queue**. Output txt berisi payload pertama yang ke-decode.

## Tips & Trick

- **Error correction H** kalau QR akan di-print dan kemungkinan kotor/rusak. Lebih besar tapi lebih reliable.
- **Module size 8** standard untuk on-screen view, 12 sampai 16 untuk print A4.
- **Margin 4** minimum untuk QR scanner work reliably (zona quiet zone).
- **zbarimg** decode banyak format: QR, EAN-13, UPC-A, Code 128, Code 39, ITF, dll. Tidak cuma QR.
- Untuk decode multiple barcode di satu image, perlu tool lebih advanced (zbarimg cuma return pertama).

## Troubleshooting

**Generate "qr_size must be between 1 and 50".** Module size out of range. Set 1 sampai 50.

**Decode "no barcodes" error.** Image quality rendah, kontras kurang, atau memang tidak ada barcode. Pre-process: pakai modul **Image** Color tab untuk grayscale plus contrast boost.

**Decoded text aneh / mojibake.** QR pakai encoding non-UTF-8. zbarimg `--raw` output as-is, bisa jadi shift-jis (Japanese) atau encoding lain.
