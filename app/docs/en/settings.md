# Settings

Default app behavior and per-module preferences.

## Description

The **Settings** page persists settings to `~/.config/trex-converter/settings.json`. Available fields:

- **Default output folder**: when filled, every page suggests its output path inside this folder. Empty = same folder as input.
- **Max concurrent tasks**: parallel queue workers (1 to 16). Applies on next launch.
- **Image quality**: default JPG/WebP/AVIF quality slider (1 to 100).
- **PDF render DPI**: default DPI when rendering PDF to image.
- **OCR language**: preset eng, ind, eng+ind, or custom (such as `eng+jpn`).
- **Video CRF**: default CRF for video output (0 = off).
- **Video x264 preset**: default speed/quality preset.
- **Audio bitrate**: default bitrate for audio output (such as `192k`).

## How to use

1. Open **Settings** from the sidebar.
2. Adjust the relevant fields.
3. Click **Save**. Most settings apply immediately except **Max concurrent tasks** (applies on next launch).
4. Click **Reset** to revert to saved values (not factory defaults).
5. Click **Open config folder** to open `~/.config/trex-converter/` in your file manager.

## Tips & Trick

- **Output folder** is honored by every conversion page when suggesting an output path. You can still override per task.
- **Max concurrent** 1 for debugging or a low-RAM machine. 4 or 8 for batch processing on a workstation.
- **OCR language Custom** accepts Tesseract format: combine language codes with `+`. Make sure the language pack is installed (`apt install tesseract-ocr-<code>`).
- **Video CRF default 0** means off. Set 23 if you want every video conversion to default to medium quality.

## Troubleshooting

**Settings don't save.** Check permissions on `~/.config/trex-converter/settings.json`. Should be writable by your user. If corrupt, delete the file and defaults will be used.

**Concurrency doesn't change after save.** Applies on next launch only. Restart the app.

**Open config folder fails.** Linux needs `xdg-open`. macOS uses `open`. Windows uses `explorer`. Install xdg-utils on Linux if it's missing.
