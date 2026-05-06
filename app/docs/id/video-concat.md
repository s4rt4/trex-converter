# Video Concat

Gabung banyak video atau audio jadi satu file via **FFmpeg** concat filter.

## Deskripsi

Modul **Video Concat** terima multi-input video (atau audio) dan output satu file. Engine emit FFmpeg `concat` filter complex: `[0:v:0][0:a:0]...concat=n=N:v=1:a=1[outv][outa]` plus `-map [outv] -map [outa]`. Audio-only output pakai `v=0:a=1`.

Format input: mp4, mov, mkv, webm. Output sama (atau audio mp3, m4a, dst.).

## Cara pakai

1. Klik **Add files** atau drop banyak video.
2. Atur urutan dengan **Remove** dan re-add.
3. Pilih **Output format**.
4. Klik **Select Location** untuk output path.
5. Klik **Add to Queue**.

## Tips & Trick

- Concat filter **re-encode** output (bukan stream copy). Cocok untuk source dengan codec berbeda.
- Untuk concat tanpa re-encode (super cepat, tapi butuh codec sama), pakai FFmpeg manual: `ffmpeg -f concat -i list.txt -c copy out.mp4`.
- Order files matters. Pertama di list = pertama di timeline.
- Resolusi atau frame rate yang berbeda otomatis di-normalize oleh concat filter (slowest dan smallest wins).

## Troubleshooting

**Output choppy di transition antar clip.** Source punya frame rate atau resolution mismatch. Pre-normalize source ke setting sama via modul **Video** Resize tab.

**Audio out-of-sync.** Source punya sample rate beda. Force audio resample dulu via modul **Audio** Output tab.

**Concat gagal "could not seek".** Salah satu input corrupt atau format tidak support seeking. Re-mux dulu via `ffmpeg -i input.mp4 -c copy fixed.mp4`.
