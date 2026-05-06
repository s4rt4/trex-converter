# PDF Extract Images

Extract every embedded image from a PDF into a folder.

## Description

The **PDF Extract Images** module takes a PDF input and outputs a folder of images named `<stem>-pageNNN-imgMM.<ext>`. The engine iterates pages with `Page.get_images(full=True)`, dedupes by xref across pages, then calls `Document.extract_image(xref)` to dump the original bytes plus the extension (PNG, JPG, or whatever the embedding used).

## How to use

1. Click **Browse** to pick a PDF.
2. Click **Select Location** to pick the output folder.
3. Click **Add to Queue**.

## Tips & Trick

- **Dedupe by xref** (default on): images shared across pages are extracted once. Disable when you want a copy per occurrence.
- The extension follows the embedded format (JPG typically for photos, PNG for diagrams).
- Naming `pageNNN-imgMM` is zero-padded (page 3 digits, image 2 digits).
- To render a whole page as an image (not extract embeds), use **PDF Tools** with png or jpg output.

## Troubleshooting

**Output folder is empty "No embedded images found".** The PDF has no raster images, only text or vectors. Use **PDF Tools** to render the page to PNG instead.

**Image quality is low.** The embedded image just is low resolution. Extract preserves original quality, there's no upscale.

**Lots of duplicate images.** Disable dedupe via option `extract_dedupe=False` (when exposed in the panel). Default dedupe is on.
