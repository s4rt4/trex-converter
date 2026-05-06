# Subtitle Merge

Concat several subtitle files (SRT, VTT, ASS) into one with two modes.

## Description

The **Subtitle Merge** module takes multi-input subtitles and outputs one file. The `_collect_merged_cues` helper in **SubtitleEngine** supports modes:

- **Shift each file (sequential)**: cumulative offset plus optional gap. The first file starts at 00:00, the second starts after the first ends plus the gap.
- **Append + sort by time**: parse every cue from every file, sort by start time. Good when each file already has correct absolute timestamps.

Input formats can mix (SRT plus VTT plus ASS). Output uses the selected format.

## How to use

1. Click **Add files** or drop several subtitle files.
2. Pick an **Output format** (srt, vtt, or ass).
3. Pick a **Mode**:
   - **Shift each file (sequential)** plus set **Gap** (seconds between files, default 1).
   - **Append + sort by time**.
4. Click **Select Location**.
5. Click **Add to Queue**.

## Tips & Trick

- **Shift mode** is great for joining subtitles from a multi-part video (Episode 1, 2, 3 concatenated into a season pack).
- **Append mode** is great for subtitles built per-scene with absolute timestamps (rare case).
- **Mixed format input** works fine, the parser handles SRT, VTT, ASS round-trip.
- **Gap** can be 0 for seamless transitions.

## Troubleshooting

**Cues overlap in Shift mode output.** Gap is too small or the last cue in the first file is longer than expected. Raise **Gap** to 2 or 3 seconds.

**Append mode output is out-of-order.** Sources have inconsistent timestamps. Verify each file in a player first.

**ASS output loses styles.** Merge keeps the first file's styles. To preserve per-file styles, output as ASS and edit the style block manually after merging.
