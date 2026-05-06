# Image

Konversi format raster dan transformasi gambar via **ImageMagick**.

## Deskripsi

Modul **Image** wrap perintah `magick input output` dan mendukung format jpg, jpeg, png, gif, bmp, ico, tif, tiff, heic, webp, avif, pdf. Panel options bertabs lengkap: **Transform**, **Resize**, **Color**, **Filter**, **Border**, **Watermark**, **Output**.

## Cara pakai

1. Klik **Browse** atau drop file ke window.
2. Pilih **Output format** dari dropdown.
3. Atur **Quality** slider (untuk JPG, WebP, AVIF) dan **Resize** kalau perlu.
4. Buka tab opsi yang relevan:
   - **Transform** untuk rotate, flip, free crop, aspect crop, fit-to-canvas.
   - **Color** untuk grayscale, sepia, negate, brightness, contrast, gamma.
   - **Filter** untuk blur, sharpen, denoise, vignette.
   - **Border** untuk add bordered frame dengan warna.
   - **Watermark** untuk text watermark atau image overlay PNG.
5. Klik **Add to Queue**.

## Tips & Trick

- **Resize** menerima syntax ImageMagick: `1280x1280>` (preserve aspect, only shrink), `800x` (width only), `50%` (percent), `2MP` (megapixel target).
- **ICO multi-resolution** otomatis di-generate via `-define icon:auto-resize=256,128,96,64,48,32,16` saat output `.ico`.
- **Strip metadata** ON secara default. Non-aktifkan kalau ingin retain EXIF.
- **Fit canvas** di tab Transform letterbox gambar ke ukuran target dengan background warna pilihan.

## Troubleshooting

**Output kosong atau hitam.** Pastikan input bukan animated GIF. Image module hanya tangani frame pertama. Untuk animated, pakai modul **Video**.

**File HEIC tidak bisa dibuka.** ImageMagick perlu codec heif: `apt install libheif-examples`. Biasanya sudah ikut waktu install ImageMagick lengkap.

**Warna keluar pucat di JPG.** Cek **Quality** slider. Di bawah 70 kualitas drop signifikan. Default 82 cocok untuk web.
