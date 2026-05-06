# PDF Compare

Visual diff between two PDFs, output one diff image per page.

## Description

The **PDF Compare** module takes two PDFs (left and right), renders each page from both via PyMuPDF Pixmap at a configurable DPI, then runs `magick compare -metric AE -fuzz N% L.png R.png diff.png`. The diff image highlights pixels that differ.

Output goes to a folder with naming `<stem>-pageNNN-diff.png`. Page-count mismatch is capped to `min(left_pages, right_pages)` and logged.

## How to use

1. Click **Add files** and pick two PDFs (left and right). Order: first file in the list is left, second is right.
2. Click **Select Location** to pick the output folder.
3. (No special options panel, default DPI 150 and fuzz 5%.)
4. Click **Add to Queue**.

## Tips & Trick

- The engine's **Fuzz** parameter (default 5%) tolerates small color shifts from rendering. Raise it to ignore minor anti-aliasing diffs.
- Higher **DPI** means more detailed diffs but slower processing. Default 150 is enough for visual review.
- The AE metric (absolute error) in the task log shows the count of differing pixels per page. Useful for regression tests.
- For text-level diff (not pixels), use `pdftotext` then `diff` in a terminal.

## Troubleshooting

**Output folder is empty.** Only one file in the list. PDF Compare needs two inputs.

**"Both PDFs must have at least one page".** One of the PDFs is empty or corrupt. Verify in a reader.

**Diff image is all red / many false diffs.** Page rotation or page size differs between PDFs. Make sure both PDFs were generated with the same settings, or rotate first in **PDF Tools**.

**ImageMagick compare isn't installed.** Install: `apt install imagemagick`. Compare ships with that package, not as a separate binary.
