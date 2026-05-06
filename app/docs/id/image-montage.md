# Image Montage

Bikin grid kolase dari banyak gambar via **ImageMagick** `montage`.

## Deskripsi

Modul **Image Montage** terima multi-input image dan output satu image yang isinya grid (mosaic) dari semua input. Engine emit ImageMagick `montage` subcommand dengan tile auto (sqrt-ish berdasarkan jumlah input) atau eksplisit, geometry per-tile, dan background color.

## Cara pakai

1. Klik **Add files** atau drop banyak image.
2. Pilih **Output format** (jpg, png, atau format image lainnya).
3. Atur opsi:
   - **Tile**: kosong/auto (sqrt-ish square layout) atau eksplisit `3x3`, `4x2`, dll.
   - **Geometry**: per-tile size plus spacing, format `WxH+padX+padY` (misal `200x200+5+5`).
   - **Background**: color name atau hex (`white`, `#0c2c55`, `#ffffff`).
4. Klik **Select Location**.
5. Klik **Add to Queue**.

## Tips & Trick

- **Auto tile** untuk 4 input jadi 2x2, 9 input jadi 3x3, dst. Hasil mendekati square.
- **Geometry** `200x200+5+5` artinya tile 200×200 px dengan 5 px padding tiap sisi.
- **Background** transparent: pakai PNG output plus geometry dengan alpha (`none`).
- Untuk thumbnail grid dari video (bukan image collection), pakai **Video** Thumbnails tab.

## Troubleshooting

**Output kosong atau hitam.** Geometry terlalu kecil atau sebagian input gagal di-render. Cek log.

**Tile spacing weird.** Pastikan format `WxH+padX+padY` benar. Contoh valid: `300x300+10+10`. `padX` dan `padY` boleh 0.

**Aspect ratio tile rusak.** Tile size force aspect tertentu. ImageMagick `montage` resize dengan distortion. Pre-crop input ke aspect target via modul **Image** Transform tab.
