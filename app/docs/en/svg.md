# SVG / Vector

SVG and vector format conversion via **Inkscape** plus pixmap-to-SVG trace via **potrace**.

## Description

The **SVG / Vector** module supports 18 format pairs:

- **Wave 1** (rendering): svg to png (dpi/width/height), svg to pdf, svg to svg (cleanup or trim).
- **Wave 2** (interop): svg to eps/ps (with ps_level and text_to_path), svg to emf/wmf, pdf to svg.
- **Wave 3** (utilities): export-by-id, svg to dxf (R14/R12), dxf to svg, 8 bitmap formats (png/jpg/jpeg/bmp/tif/tiff/gif/webp) to svg via potrace trace.

Options panel has 3 tabs: **Raster** (DPI, Width, Height), **Vector** (operation, PS level, PDF page, DXF format, text-to-path, export-id), **Trace** (threshold, turdsize).

## How to use

1. Click **Browse** or drop a file (svg, pdf, dxf, or bitmap).
2. Pick an **Output format**.
3. Adjust options in the relevant tab:
   - **Raster** for PNG output: set DPI or Width/Height.
   - **Vector** for SVG cleanup/trim, PS level, DXF format, text-to-path checkbox.
   - **Trace** for bitmap to SVG: threshold (0 to 1, default 0.5) and turdsize (noise filter).
4. Click **Add to Queue**.

## Tips & Trick

- **SVG cleanup** strips `inkscape:` and `sodipodi:` namespaces, drops unused `<defs>`. Good before uploading to the web.
- **SVG trim** crops the viewBox to the drawing's bounding box. Useful for SVGs with oversized canvases.
- **Text to paths** in EPS/PS/PDF/SVG output embeds glyphs as paths, so the font doesn't need to be installed on the target system.
- **DXF R14** is the default for Desktop Cutting Plotter (laser cut, vinyl cut). R12 is for legacy CAD software.
- **Trace threshold** lower (0.3) gives detailed but noisy output. Higher (0.7) is cleaner but loses detail.

## Troubleshooting

**SVG to DXF fails with "Failed to save".** Inkscape's extension needs `python3-tinycss2`. Install: `apt install python3-tinycss2`.

**Trace output is empty.** The source image has low contrast or is pure white. Pre-process in the **Image** Color tab: threshold then trace.

**SVG to PNG is too small.** The default DPI is 96. Set Width 1920 or DPI 300 for crisp output.
