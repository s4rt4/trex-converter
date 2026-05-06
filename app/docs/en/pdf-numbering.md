# PDF Numbering

Add page numbering or Bates numbering to a PDF.

## Description

The **PDF Numbering** module inserts text into every page with a configurable template. The `_op_page_numbering` engine in **PDFEngine** uses `Page.insert_text` per page.

Format string templates support placeholders `{n}` (current page number), `{total}` (total pages), `{page}` (alias for `{n}`). Python format specs work for Bates-style padding (such as `{n:06d}`).

## How to use

1. Click **Browse** to pick a PDF.
2. Adjust options:
   - **Format** template (such as `Page {n} of {total}` or `Bates {n:06d}`).
   - **Position** (9-position gravity, default southeast).
   - **Font size** (default 12).
   - **Start number** (default 1).
   - **Skip first N** pages (to skip cover or ToC).
   - **Opacity** (0 to 100, default 60).
3. Click **Add to Queue**.

## Tips & Trick

- **Bates numbering** for legal docs: use format `BATES{n:06d}` or `EXHIBIT-A-{n:04d}`. Zero-padded so name-sort keeps order.
- **Skip first N** for documents with a cover or Table of Contents (numbering usually starts on page 3).
- **Position** southeast is the most common (bottom-right). South for a centered footer.
- **Opacity** 30 to 60 is most readable without overpowering content.

## Troubleshooting

**Format error "unknown placeholder".** Template misspells `{n}`, `{total}`, or `{page}`. Check for stray backslashes or curly braces.

**Numbering clipped at the page edge.** Pick a non-corner **Position** (such as south or north). The default edge margin is 5% of page width/height.

**Number shows on pages that should be skipped.** **Skip first N** counts from page 1 inclusive. Set to 2 to skip pages 1 and 2 (cover plus blank).
