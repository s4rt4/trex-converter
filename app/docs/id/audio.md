# Audio

Konversi audio dan ekstraksi audio dari video via **FFmpeg**.

## Deskripsi

Modul **Audio** mendukung full matrix audio ke audio (mp3, wav, aac, flac, m4a, opus, ogg) plus extract dari video (mp4, mov, mkv, webm). Panel options 4 tab: **Trim**, **Effects**, **Output**, **Tags**.

Filter chain order: atempo, afade-in, afade-out, volume, vocal-remove, loudnorm, areverse.

## Cara pakai

1. Klik **Browse** untuk pilih file audio atau video.
2. Pilih **Output format** dari dropdown.
3. Atur opsi:
   - **Trim** untuk start dan end timestamp.
   - **Effects** untuk fade-in, fade-out, gain (-20 sampai +20 dB), loudness normalize EBU R128, vocal remove (center channel cancel).
   - **Output** untuk channel down-mix (mono/stereo) dan sample rate (22.05k, 44.1k, 48k, 96k).
   - **Tags** untuk ID3 metadata (title, artist, album, year, genre, track) plus cover art picker.
4. Klik **Add to Queue**.

## Tips & Trick

- **Loudnorm** pakai preset broadcast standard `I=-16:TP=-1.5:LRA=11`. Cocok untuk podcast dan streaming.
- **Vocal remove** pakai `pan=stereo|c0=c0-c1|c1=c1-c0`. Hasilnya tergantung mixing original, kadang vokal masih sisa.
- **Cover art** di tab Tags emit `-i cover.jpg -map 0:a -map 1 -c:v copy -disposition:v attached_pic`. Embed langsung ke ID3v2.3.
- **Sample rate** 44.1k untuk musik, 48k untuk video, 22.05k untuk voice memo low-bitrate.

## Troubleshooting

**Output mp3 lebih besar dari source.** Bitrate mp3 default 192k. Set lebih rendah lewat **Bitrate** field di main form (misal `128k` atau `96k`).

**Cover art tidak muncul di player.** Pastikan output mp3 atau m4a, dan player support attached pic. flac dan ogg pakai metadata berbeda untuk cover art.

**Loudnorm hasilnya distorted.** Source sudah ke-normalize sebelumnya atau source punya peak yang sangat tinggi. Coba turunkan **Gain** sebelum loudnorm.
