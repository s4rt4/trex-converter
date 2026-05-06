# Document Merge

Merge several Office documents (DOCX, ODT, RTF, etc.) into a single PDF.

## Description

The **Document Merge** module takes multi-input Office documents and outputs a single PDF. The `_bulk_merge_to_pdf` engine in **LibreOfficeEngine** converts each input to PDF in a tempdir (skipping inputs that are already PDF), then PyMuPDF's `Document.insert_pdf` concatenates everything into the output.

Input formats: doc, docx, odt, rtf, xls, xlsx, ods, ppt, pptx, odp, pdf.

## How to use

1. Click **Add files** or drop several documents.
2. Reorder via **Remove** and re-add.
3. Click **Select Location** for the output PDF path.
4. Click **Add to Queue**.

## Tips & Trick

- Mix input formats: DOCX, ODT, RTF, PDF can all be combined in one queue. The engine converts per-input then concatenates.
- PDF inputs pass through without re-conversion (saves time).
- Output uses `garbage=4 deflate=True` to minimize size.
- For PDF-only merging (no Office inputs), use **PDF Merge** which is faster (skips LibreOffice spin-up).

## Troubleshooting

**The first conversion is slow.** LibreOffice headless is starting. Subsequent runs are fast (the instance is reused).

**Input format "unsupported".** Check the extension. This module accepts Office formats, not arbitrary text files. For markdown/html, use **Ebook**.

**Output PDF order is wrong.** List order is output order. Re-add files in the correct order.
