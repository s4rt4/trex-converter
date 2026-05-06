# Video

Video and audio conversion via **FFmpeg** with trim, compress, watermark, GIF/WebP creator, contact sheet, and more.

## Description

The **Video** module wraps `ffmpeg -i input ... output` with a filter chain ordered as: crop, transpose, flip, scale, setpts, subtitles, drawtext, reverse. The options panel has 9 tabs: **Trim**, **Transform**, **Resize**, **Compress**, **Watermark**, **Effects**, **Animation**, **Thumbnails**, **Subtitles**.

Output formats: video (mp4, mov, mkv, webm), audio (mp3, wav, aac, flac, m4a, opus, ogg), animated (gif, webp), still image (png, jpg).

## How to use

1. Click **Browse** to pick a video file.
2. Pick an **Output format**.
3. Adjust options in the relevant tab:
   - **Trim** for start and end timestamp plus optional **Stream copy** (skip re-encoding, super fast).
   - **Resize** for preset 4K, 1440p, 1080p, 720p, 480p, 360p.
   - **Compress** for CRF 0 to 51, x264 preset, or **Target size (MB)** for two-pass encode.
   - **Effects** for reverse and PNG logo overlay with 9-position gravity.
   - **Animation** for fps, width, quality on the GIF/WebP creator.
   - **Thumbnails** for contact sheet (rows × cols) or single-frame still.
   - **Subtitles** for burn-in SRT, VTT, or ASS.
4. Click **Add to Queue**.

## Tips & Trick

- **Stream copy** under Trim emits `-c copy` and skips the filter chain. Use it when you only need to cut without transcoding (instant).
- **Target size** under Compress triggers two-pass: probe duration via `ffprobe`, compute bitrate, run pass 1 (`-an -f null /dev/null`) then pass 2 (`-b:v Xk`).
- **GIF creator** uses `palettegen` plus `paletteuse` filter for vibrant colors (16M colors mapped to 256 palette).
- **Contact sheet** is great for previewing long files via `select=not(mod(n,N))` plus `tile=ColsxRows`.

## Troubleshooting

**Choppy output after Stream copy.** Cut points don't align to keyframes. Re-encode mode (uncheck Stream copy) will be smooth but slower.

**Two-pass fails with "could not determine duration".** Input is corrupt or its container has no duration metadata. Re-mux first via `ffmpeg -i bad.mp4 -c copy fixed.mp4`.

**Subtitle burn-in doesn't show.** Make sure the SRT or ASS path is valid and has no special characters. FFmpeg needs an escaped path.
