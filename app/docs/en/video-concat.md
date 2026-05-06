# Video Concat

Join several videos or audio files into one via **FFmpeg** concat filter.

## Description

The **Video Concat** module takes multi-input video (or audio) and outputs one file. The engine emits an FFmpeg `concat` filter_complex: `[0:v:0][0:a:0]...concat=n=N:v=1:a=1[outv][outa]` plus `-map [outv] -map [outa]`. Audio-only output uses `v=0:a=1`.

Input formats: mp4, mov, mkv, webm. Output is the same (or audio mp3, m4a, etc.).

## How to use

1. Click **Add files** or drop several videos.
2. Reorder via **Remove** and re-add.
3. Pick an **Output format**.
4. Click **Select Location** for the output path.
5. Click **Add to Queue**.

## Tips & Trick

- The concat filter **re-encodes** the output (not stream copy). Suits sources with different codecs.
- For concat without re-encoding (super fast, but requires identical codecs), use raw FFmpeg: `ffmpeg -f concat -i list.txt -c copy out.mp4`.
- File order matters. First in the list is first on the timeline.
- Different resolutions or frame rates are auto-normalized by the concat filter (slowest and smallest win).

## Troubleshooting

**Output is choppy at clip transitions.** Sources have mismatched frame rate or resolution. Pre-normalize sources to the same settings via the **Video** module's Resize tab.

**Audio is out of sync.** Sources have different sample rates. Force resample first via the **Audio** module's Output tab.

**Concat fails with "could not seek".** One of the inputs is corrupt or its format doesn't support seeking. Re-mux first via `ffmpeg -i input.mp4 -c copy fixed.mp4`.
