# Document

Office document conversion via **LibreOffice** headless.

## Description

The **Document** module wraps `libreoffice --headless --convert-to ...` with a full format matrix (52 pairs):

- Text: doc, docx, odt, rtf to docx, odt, rtf, html, epub, txt, pdf.
- Spreadsheet: xls, xlsx, ods to xlsx, ods, csv, html, pdf.
- Presentation: ppt, pptx, odp to pptx, odp, pdf.

Single-pane options panel for PDF/A archival and password-protected PDF.

## How to use

1. Click **Browse** to pick a document file.
2. Pick an **Output format**.
3. Adjust options (when output is PDF):
   - **PDF/A-1a archival** checkbox for long-term archive.
   - **User password** to lock open access.
   - **Owner password** to restrict permissions (print, copy, edit).
4. Click **Add to Queue**.

## Tips & Trick

- **Headless mode** spins up a background LibreOffice instance on first use, so the first conversion is a bit slow (5 to 10 seconds). Subsequent runs are fast.
- **PDF/A-1a** triggers filter `pdf:writer_pdf_Export:{"SelectPdfVersion":{"type":"long","value":"1"}}`. Suitable for ISO 19005 archives.
- **User password** locks open access, **owner password** locks permissions. Both can be used together.
- The **Output format** dropdown auto-swaps the extension on the output path.

## Troubleshooting

**Conversion stuck or times out.** A previous LibreOffice headless instance is still running. Kill it: `pkill -f soffice`. Restart the conversion.

**PDF/A fails with a filter error.** Older LibreOffice (<7.0) uses different filter syntax. Upgrade to LibreOffice 7.x.

**Fonts missing in output.** The source document uses fonts not installed on the system. Install a font pack: `apt install fonts-noto fonts-liberation`.
