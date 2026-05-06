# Slides to Images

Render every presentation slide into PNG or JPG files in a folder.

## Description

The **Slides to Images** module takes PPT, PPTX, ODP files and outputs a folder of PNG or JPG per slide. The `_slides_to_images` engine in **LibreOfficeEngine** converts to PDF in a tempdir first, then PyMuPDF Pixmap renders each page to an image at a configurable DPI.

Output naming: `<stem>-001.<ext>`, `<stem>-002.<ext>`, and so on.

## How to use

1. Click **Browse** to pick a presentation file.
2. Click **Select Location** to pick the output folder.
3. Adjust options:
   - **Image format** (png or jpg).
   - **DPI** (72 to 600, default 200).
4. Click **Add to Queue**.

## Tips & Trick

- **PNG** for slides with text and diagrams (lossless, transparency support).
- **JPG** for slides with many photos (smaller file size).
- **DPI 200** for on-screen view, 300 for print preview, 600 for archival quality.
- Naming `001/002/003` is zero-padded to 3 digits, supports up to 999 slides.

## Troubleshooting

**LibreOffice times out on complex slides.** Slides with lots of embedded media need a long render time. Raise the timeout in code (temporarily) or split the presentation into smaller files.

**JPG output has black edges.** The slide has a transparent background, jpg doesn't support transparency. Use PNG.

**File naming isn't ordered.** OS file managers sometimes sort `slide-1, slide-10, slide-2`. Our zero-padded naming keeps the sort consistent.
