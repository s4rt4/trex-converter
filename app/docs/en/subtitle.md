# Subtitle

Subtitle format conversion (SRT, VTT, ASS) with time shift via a pure Python parser.

## Description

The **Subtitle** module needs no external binary. The `SubtitleEngine` parses and formats SRT, VTT, ASS round-trip plus optional time shift (offsets every cue by plus or minus N seconds).

The ASS parser supports a useful subset: section dispatcher `[Events]`, Format header detection, Dialogue rows with commas inside the Text field, escape sequences `\N` and `\n`, Comment lines are skipped. The ASS formatter emits a minimal Script Info plus V4+ Styles plus Events with a default Arial 32 white style.

## How to use

1. Click **Browse** to pick a subtitle file.
2. Pick an **Output format** (srt, vtt, or ass).
3. (Optional) Set a **Time shift** in seconds (positive shifts forward, negative shifts back, clamped to minus 3600 to 3600).
4. Click **Add to Queue**.

## Tips & Trick

- **Time shift** clamps to 0 when a negative shift would push a cue's start time below zero.
- **VTT to SRT** drops cue identifiers and WEBVTT/NOTE/STYLE blocks.
- **ASS round-trip** preserves text with commas and multi-line via `\N`.
- To **merge** many subtitle files, use the **Subtitle Merge** module.
- To **burn-in** subtitles into video, use the **Subtitles** tab in the **Video** module.
- To **extract** subtitles from MKV/MP4, use the **Subtitle Extract** module.

## Troubleshooting

**ASS output looks corrupt in the player.** The player needs the font referenced in the Style. The default Arial should always be present. With a custom style, check font availability.

**SRT to VTT has cue identifiers.** VTT supports an optional identifier before the timestamp. Our parser drops identifiers on VTT output.

**Time shift fails with "negative cue start".** The negative shift is too large for the earliest cue. Lower the shift value.
