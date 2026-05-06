# Image

Raster format conversion and image transforms via **ImageMagick**.

## Description

The **Image** module wraps `magick input output` and supports jpg, jpeg, png, gif, bmp, ico, tif, tiff, heic, webp, avif, pdf. The tabbed options panel exposes **Transform**, **Resize**, **Color**, **Filter**, **Border**, **Watermark**, **Output**.

## How to use

1. Click **Browse** or drop a file onto the window.
2. Pick an **Output format** from the dropdown.
3. Adjust the **Quality** slider (JPG, WebP, AVIF) and **Resize** as needed.
4. Open the relevant option tab:
   - **Transform** for rotate, flip, free crop, aspect crop, fit-to-canvas.
   - **Color** for grayscale, sepia, negate, brightness, contrast, gamma.
   - **Filter** for blur, sharpen, denoise, vignette.
   - **Border** to add a bordered frame with a color.
   - **Watermark** for text watermark or PNG image overlay.
5. Click **Add to Queue**.

## Tips & Trick

- **Resize** accepts native ImageMagick syntax: `1280x1280>` (preserve aspect, only shrink), `800x` (width only), `50%` (percent), `2MP` (megapixel target).
- **ICO multi-resolution** is auto-generated via `-define icon:auto-resize=256,128,96,64,48,32,16` whenever output is `.ico`.
- **Strip metadata** is on by default. Disable it to keep EXIF.
- **Fit canvas** under Transform letterboxes the image into a target size with a configurable background color.

## Troubleshooting

**Output blank or black.** Check the input isn't an animated GIF. The Image module handles only the first frame. Use the **Video** module for animated content.

**HEIC files won't open.** ImageMagick needs the heif codec: `apt install libheif-examples`. Usually pulled in with a full ImageMagick install.

**JPG output looks washed out.** Check the **Quality** slider. Below 70 quality drops noticeably. Default 82 is fine for web.
