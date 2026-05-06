# Subtitle Extract

Extract subtitle dari container video (MKV, MP4, MOV, WEBM) ke file standalone.

## Deskripsi

Modul **Subtitle Extract** wrap FFmpeg dengan command `ffmpeg -i input -map 0:s:N -c:s codec output`. Codec map: srt ke srt, ass ke ass, vtt ke webvtt. Stream index configurable (default 0 untuk subtitle stream pertama).

## Cara pakai

1. Klik **Browse** untuk pilih video file.
2. Pilih **Output format** (srt, ass, vtt).
3. (Tidak ada panel options khusus di UI, default stream index 0.)
4. Klik **Select Location**.
5. Klik **Add to Queue**.

## Tips & Trick

- Banyak MKV punya multiple subtitle stream (English, Indonesian, Japanese, dll.). Default extract stream pertama. Untuk pilih stream lain, set option `subtitle_stream_index` di task (perlu edit code atau preset).
- **SRT** paling kompatibel dengan player. Pilih kalau cuma butuh teks.
- **ASS** retain styling original (warna, font, position). Pilih kalau anime/movie pakai signs/songs styled subtitles.
- **VTT** untuk web (HTML5 video element).

## Troubleshooting

**"could not find stream of type 's'".** Video tidak punya subtitle stream. Cek dengan `ffprobe input.mkv` atau pakai mediainfo.

**Output kosong.** Stream index salah (lebih besar dari jumlah stream). Cek dengan `ffprobe -v error -select_streams s -show_entries stream=index input.mkv`.

**Output ASS kehilangan style.** Source dipakai codec berbeda yang tidak preserve styling (misal mov_text dari MP4). Re-encode dengan `-c:s ass` di FFmpeg manual.
