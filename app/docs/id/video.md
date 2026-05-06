# Video

Konversi video dan audio via **FFmpeg** dengan trim, compress, watermark, GIF/WebP creator, contact sheet, dan banyak lagi.

## Deskripsi

Modul **Video** wrap perintah `ffmpeg -i input ... output` dengan filter chain order: crop, transpose, flip, scale, setpts, subtitles, drawtext, reverse. Panel options 9 tab: **Trim**, **Transform**, **Resize**, **Compress**, **Watermark**, **Effects**, **Animation**, **Thumbnails**, **Subtitles**.

Output formats: video (mp4, mov, mkv, webm), audio (mp3, wav, aac, flac, m4a, opus, ogg), animated (gif, webp), still image (png, jpg).

## Cara pakai

1. Klik **Browse** untuk pilih file video.
2. Pilih **Output format**.
3. Atur opsi di tab yang relevan:
   - **Trim** untuk start dan end timestamp plus opsional **Stream copy** (skip re-encoding, super cepat).
   - **Resize** untuk preset 4K, 1440p, 1080p, 720p, 480p, 360p.
   - **Compress** untuk CRF 0 sampai 51, x264 preset, atau **Target size (MB)** untuk two-pass encode.
   - **Effects** untuk reverse dan logo overlay PNG dengan posisi 9-arah.
   - **Animation** untuk fps, width, quality di GIF/WebP creator.
   - **Thumbnails** untuk contact sheet (rows × cols) atau single-frame still.
   - **Subtitles** untuk burn-in SRT, VTT, atau ASS.
4. Klik **Add to Queue**.

## Tips & Trick

- **Stream copy** di tab Trim emit `-c copy` dan skip filter chain. Pakai kalau hanya cut tanpa transcoding (instant).
- **Target size** di tab Compress trigger two-pass: probe duration via `ffprobe`, hitung bitrate, jalankan pass 1 (`-an -f null /dev/null`) lalu pass 2 (`-b:v Xk`).
- **GIF creator** pakai `palettegen` plus `paletteuse` filter untuk warna bagus (16M warna jadi 256 palette tetap hidup).
- **Contact sheet** efektif buat preview file panjang via `select=not(mod(n,N))` plus `tile=ColsxRows`.

## Troubleshooting

**Output choppy setelah Stream copy.** Cut points tidak align ke keyframe. Re-encode mode (uncheck Stream copy) bakal smooth tapi lebih lambat.

**Two-pass gagal "could not determine duration".** Input corrupt atau format tidak punya duration metadata. Re-mux input dulu via `ffmpeg -i bad.mp4 -c copy fixed.mp4`.

**Subtitle burn-in tidak muncul.** Pastikan path file SRT atau ASS valid dan tidak ada karakter spesial. FFmpeg butuh path yang escaped.
