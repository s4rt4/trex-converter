# SVG / Vector

Konversi SVG dan vector format via **Inkscape** plus pixmap-to-SVG trace via **potrace**.

## Deskripsi

Modul **SVG / Vector** support 18 pair format:

- **Wave 1** (rendering): svg ke png (dpi/width/height), svg ke pdf, svg ke svg (cleanup atau trim).
- **Wave 2** (interop): svg ke eps/ps (dengan ps_level dan text_to_path), svg ke emf/wmf, pdf ke svg.
- **Wave 3** (utilities): export-by-id, svg ke dxf (R14/R12), dxf ke svg, 8 bitmap (png/jpg/jpeg/bmp/tif/tiff/gif/webp) ke svg via potrace trace.

Panel options 3 tab: **Raster** (DPI, Width, Height), **Vector** (operation, PS level, PDF page, DXF format, text-to-path, export-id), **Trace** (threshold, turdsize).

## Cara pakai

1. Klik **Browse** atau drop file (svg, pdf, dxf, atau bitmap).
2. Pilih **Output format**.
3. Atur opsi di tab yang relevan:
   - **Raster** untuk PNG output: set DPI atau Width/Height.
   - **Vector** untuk SVG cleanup/trim, PS level, DXF format, text-to-path checkbox.
   - **Trace** untuk bitmap ke SVG: threshold (0 sampai 1, default 0.5) dan turdsize (noise filter).
4. Klik **Add to Queue**.

## Tips & Trick

- **SVG cleanup** strip namespace `inkscape:` dan `sodipodi:`, hapus `<defs>` yang tidak terpakai. Cocok sebelum upload ke web.
- **SVG trim** crop viewBox ke bounding box drawing. Berguna kalau SVG punya canvas oversized.
- **Text to paths** di EPS/PS/PDF/SVG output embed glyph as path, jadi font tidak perlu installed di target system.
- **DXF R14** default untuk Desktop Cutting Plotter (laser cut, vinyl cut). R12 untuk legacy CAD software.
- **Trace threshold** lebih rendah (0.3) jadikan output detail tapi noisy. Lebih tinggi (0.7) lebih clean tapi kehilangan detail.

## Troubleshooting

**SVG to DXF gagal "Failed to save".** Inkscape extension butuh `python3-tinycss2`. Install: `apt install python3-tinycss2`.

**Trace output kosong.** Source image low contrast atau pure white. Pre-process di modul **Image** Color tab: threshold lalu trace.

**SVG to PNG terlalu kecil.** Default DPI 96. Set Width 1920 atau DPI 300 untuk crisp output.
