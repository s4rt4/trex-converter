# Subtitle Extract

Extract subtitles from a video container (MKV, MP4, MOV, WEBM) into a standalone file.

## Description

The **Subtitle Extract** module wraps FFmpeg with `ffmpeg -i input -map 0:s:N -c:s codec output`. Codec map: srt to srt, ass to ass, vtt to webvtt. Stream index is configurable (default 0 for the first subtitle stream).

## How to use

1. Click **Browse** to pick a video file.
2. Pick an **Output format** (srt, ass, vtt).
3. (No special options panel in the UI, default stream index is 0.)
4. Click **Select Location**.
5. Click **Add to Queue**.

## Tips & Trick

- Many MKV files carry multiple subtitle streams (English, Indonesian, Japanese, etc.). Default extracts the first stream. To pick another stream, set the `subtitle_stream_index` option on the task (needs code edit or preset).
- **SRT** is most compatible with players. Pick it when you only need text.
- **ASS** keeps original styling (colors, fonts, position). Pick it when anime/movie uses styled signs/songs.
- **VTT** is for web (HTML5 video element).

## Troubleshooting

**"could not find stream of type 's'".** The video has no subtitle stream. Check with `ffprobe input.mkv` or mediainfo.

**Output is empty.** Stream index is wrong (greater than the number of streams). Check with `ffprobe -v error -select_streams s -show_entries stream=index input.mkv`.

**ASS output loses styling.** The source uses a different codec that doesn't preserve styling (such as mov_text from MP4). Re-encode with `-c:s ass` via raw FFmpeg.
