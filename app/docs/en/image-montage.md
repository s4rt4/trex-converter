# Image Montage

Build a grid collage from many images via **ImageMagick** `montage`.

## Description

The **Image Montage** module takes multi-input images and outputs one image whose contents are a grid (mosaic) of all inputs. The engine emits ImageMagick's `montage` subcommand with auto tile (sqrt-ish based on input count) or explicit, per-tile geometry, and a background color.

## How to use

1. Click **Add files** or drop several images.
2. Pick an **Output format** (jpg, png, or another image format).
3. Adjust options:
   - **Tile**: empty/auto (sqrt-ish square layout) or explicit `3x3`, `4x2`, etc.
   - **Geometry**: per-tile size plus spacing in `WxH+padX+padY` form (such as `200x200+5+5`).
   - **Background**: color name or hex (`white`, `#0c2c55`, `#ffffff`).
4. Click **Select Location**.
5. Click **Add to Queue**.

## Tips & Trick

- **Auto tile** for 4 inputs gives 2x2, 9 inputs gives 3x3, etc. Results are near-square.
- **Geometry** `200x200+5+5` means a 200x200 px tile with 5 px padding on each side.
- **Transparent background**: use PNG output with alpha (`none`).
- For a thumbnail grid from video (not an image collection), use the **Video** Thumbnails tab.

## Troubleshooting

**Output is blank or black.** Geometry is too small or some inputs failed to render. Check the log.

**Tile spacing looks weird.** Make sure the `WxH+padX+padY` format is correct. Valid example: `300x300+10+10`. `padX` and `padY` may be 0.

**Tile aspect ratio looks wrong.** Tile size forces a specific aspect. ImageMagick's `montage` resizes with distortion. Pre-crop inputs to the target aspect via the **Image** module's Transform tab.
