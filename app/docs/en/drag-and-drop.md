# Drag and Drop

Drop files from your file manager straight into the app window.

## Description

Every **ConversionPage** accepts drop events. Extensions are filtered automatically against `config.input_formats`. Multi-input pages append all valid files; single-input pages take the first valid file.

Implementation via Qt: `setAcceptDrops(True)` plus `dragEnterEvent`, `dragMoveEvent`, `dropEvent`. Routed through the shared `_accept_paths(paths)` helper.

## How to use

1. Open any conversion page (such as **Image**).
2. Drag a file from the file manager onto the window.
3. Drop. The file shows up in the **Input** field (or in the list for multi-input pages).

## Tips & Trick

- **Multi-input pages** (PDF Merge, Video Concat, Image Montage, etc.) accept many files in a single drop.
- **Single-input pages** take the first valid file when multiple are dropped. An info dialog appears when extras are skipped.
- **Folder drop** on the Archive Compress page accepts a folder (not individual files).
- **Mixed extensions**: files with invalid extensions are rejected with a warning dialog.
- Drag from anywhere: GNOME Files, Dolphin, Thunar, terminal via `xdg-mime`, etc.

## Troubleshooting

**Drop doesn't detect files.** Some file managers send URLs instead of paths. The Qt driver usually handles this, but if it fails try a different file manager.

**"No supported files in selection".** All dropped files have extensions that don't match `input_formats`. Check the target page's extensions (such as Image accepts jpg/png/etc, not mp4).

**Drop on single-input page but many files.** Only the first valid file is used, the rest are ignored with an info dialog. For batches, pick a multi-input page (such as Image Montage instead of Image).
