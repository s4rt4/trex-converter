# OCR

Optical character recognition via **Tesseract**.

## Description

The **OCR** module wraps `tesseract` to extract text from images or PDF into txt, searchable PDF, hOCR (HTML), or TSV. Input formats: png, jpg, jpeg, tif, tiff, bmp, plus pdf (auto-renders each page to PNG at a configurable DPI, OCRs per page, then stitches).

Options panel: **Language** (preset eng, ind, eng+ind, or custom), **PSM** (page segmentation mode, 13 modes), **OEM** (engine mode, 4 modes), **PDF render DPI** (72 to 600), **Auto-rotate** (OSD pre-pass).

## How to use

1. Click **Browse** to pick an image or PDF.
2. Pick an **Output format** (txt, pdf, hocr, tsv).
3. Set **Language**:
   - Preset eng for English only.
   - Preset ind for Indonesian only.
   - Preset eng+ind for dual-language.
   - Custom for other combos (such as `eng+jpn` or `eng+ara`).
4. Set **DPI** (default 300, raise for tiny text).
5. Tick **Auto-rotate** for skewed scans (OSD pre-pass detects rotation and re-renders before OCR).
6. Click **Add to Queue**.

## Tips & Trick

- **Searchable PDF** keeps the original layout and adds an invisible text layer. Great for archiving scans as searchable PDFs.
- **hOCR output** carries per-word bounding boxes, handy if you want to import into another PDF editor.
- **TSV output** carries per-word confidence scores, useful for filtering low-quality OCR.
- **Language packs** install via `apt install tesseract-ocr-{code}` (such as `tesseract-ocr-ind` for Indonesian).
- **Auto-rotate** is accurate for 90-degree multiples, less accurate for small skew (under 5 degrees).

## Troubleshooting

**Output is empty or garbage.** Tesseract needs high contrast. Pre-process the image: grayscale plus threshold in the **Image** module (Color tab plus Filter tab).

**Language pack missing error.** Run `tesseract --list-langs` to see installed packs. Install the missing one via `apt install tesseract-ocr-<code>`.

**PDF input is slow.** Tesseract re-renders every page at high DPI. Drop **DPI** to 200 or 250 when the input is already crisp.
