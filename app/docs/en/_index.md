# Welcome

T-Rex Converter is a local file converter for Debian. Everything runs on your machine, nothing is uploaded to the cloud.

## Description

The left sidebar groups modules by category: image, video, audio, document, PDF, OCR, subtitle, archive, QR/barcode, SVG/vector, ebook, and metadata. Each module gets its own page with the options that matter for that workflow.

Engines are all standard Debian tools: `ffmpeg`, `magick` (ImageMagick), `libreoffice`, `qpdf`, `tesseract`, `inkscape`, `potrace`, `pandoc`, `exiftool`, `qrencode`, `zbarimg`. If anything is missing, the dependency dialog in the sidebar footer flags it.

## How to use

1. Pick a module in the sidebar (such as **Image**).
2. Click **Browse** or drop a file onto the window.
3. Pick an **Output format** from the dropdown.
4. Tweak any options in the panel below the form.
5. Click **Add to Queue**.
6. Watch progress in the **Queue** tab.

## Tips & Trick

- **Drag-and-drop** works on every conversion page. Multi-input pages accept several files at once.
- **Presets** on each page save favorite option combos to `~/.config/trex-converter/presets/`.
- The **Dashboard** has an **Activity** tab with a per-day, per-week, per-month, or per-year chart.
- The **Info** button or double-click on a queue row opens a details dialog with full log and thumbnails.

## Troubleshooting

**Engine missing.** Check the sidebar footer (cog button), look at the binary list. Install missing ones with `apt install <name>`.

**App crashes on launch.** Check `~/.config/trex-converter/`. If `settings.json` is corrupt, delete it and defaults will be used.

**Output clipped on small screens.** The convert tab now scrolls vertically, drag the scrollbar on the right.
