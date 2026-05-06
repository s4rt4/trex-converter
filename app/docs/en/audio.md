# Audio

Audio conversion and audio extraction from video via **FFmpeg**.

## Description

The **Audio** module supports a full audio-to-audio matrix (mp3, wav, aac, flac, m4a, opus, ogg) plus extract from video (mp4, mov, mkv, webm). The options panel has 4 tabs: **Trim**, **Effects**, **Output**, **Tags**.

Filter chain order: atempo, afade-in, afade-out, volume, vocal-remove, loudnorm, areverse.

## How to use

1. Click **Browse** to pick an audio or video file.
2. Pick an **Output format** from the dropdown.
3. Adjust options:
   - **Trim** for start and end timestamp.
   - **Effects** for fade-in, fade-out, gain (-20 to +20 dB), EBU R128 loudness normalize, vocal remove (center channel cancel).
   - **Output** for channel down-mix (mono/stereo) and sample rate (22.05k, 44.1k, 48k, 96k).
   - **Tags** for ID3 metadata (title, artist, album, year, genre, track) plus cover art picker.
4. Click **Add to Queue**.

## Tips & Trick

- **Loudnorm** uses the broadcast standard preset `I=-16:TP=-1.5:LRA=11`. Good for podcasts and streaming.
- **Vocal remove** uses `pan=stereo|c0=c0-c1|c1=c1-c0`. Results depend on the original mix, sometimes vocals still leak through.
- **Cover art** on the Tags tab emits `-i cover.jpg -map 0:a -map 1 -c:v copy -disposition:v attached_pic`. Embedded directly into ID3v2.3.
- **Sample rate** 44.1k for music, 48k for video, 22.05k for low-bitrate voice memos.

## Troubleshooting

**MP3 output is larger than the source.** The default mp3 bitrate is 192k. Lower it via the **Bitrate** field on the main form (such as `128k` or `96k`).

**Cover art doesn't show in players.** Make sure output is mp3 or m4a, and the player supports attached pic. flac and ogg use a different metadata block for cover art.

**Loudnorm output is distorted.** The source is already normalized or has very high peaks. Try lowering **Gain** before loudnorm.
