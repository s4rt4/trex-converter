# PDF Split

Split one PDF into many files with three modes: every-N, custom range, or by file size.

## Description

The **PDF Split** module takes one PDF input and outputs to a folder filled with `<stem>-001.pdf`, `<stem>-002.pdf`, and so on. The `_run_split` engine in **PDFEngine** dispatches by mode:

- **Every N pages**: chunks of consecutive N pages per file.
- **Custom ranges**: comma-separated 1-based ranges (`1-5, 6-10, 11-20`), one file per range.
- **By file size**: packs pages into a chunk doc, serializes, and when the size exceeds the limit rolls back the last page and finalizes the previous chunk.

## How to use

1. Click **Browse** to pick a PDF.
2. Click **Select Location** to pick the output folder.
3. Pick a **Mode**:
   - **Every N pages** and set **Pages per file**.
   - **Custom ranges** and set **Ranges** (such as `1-3, 4-6, 7-10`).
   - **By file size (MB)** and set **Max chunk size**.
4. Click **Add to Queue**.

## Tips & Trick

- **By file size** is great for email attachment limits (such as Gmail's 25 MB). Set **Max chunk size** to 24 MB.
- **Custom ranges** can overlap or have gaps. The engine doesn't validate consistency, only that each range is valid.
- Output naming `<stem>-NNN.pdf` is zero-padded to 3 digits, supports up to 999 chunks.
- To extract specific pages (not split into many files), use **PDF Tools** Pages tab Extract action.

## Troubleshooting

**Output folder is empty.** **By file size** mode with a limit too large (bigger than the source). The output is just 1 file (the source) saved directly.

**"split_size_mb requires positive number".** You forgot to fill **Max chunk size** or set it to 0. Set a positive value like 5 or 10.

**Pages skipped or duplicated in Custom ranges.** The range is wrong or has overlaps. Verify by viewing the source PDF in a reader, then adjust the range.
