# PDF Extract Attachments

Extract embedded file attachments from a PDF into a folder.

## Description

PDF supports attached files (similar to a ZIP container). The **PDF Extract Attachments** module walks `Document.embfile_count`, `embfile_info`, `embfile_get` to dump each attachment with the original filename (sanitized via `_safe_attachment_name`).

## How to use

1. Click **Browse** to pick a PDF.
2. Click **Select Location** to pick the output folder.
3. Click **Add to Queue**.

## Tips & Trick

- Useful for PDFs that attach source files (such as academic papers attaching CSV datasets, or forms attaching signed copies).
- Filenames are sanitized: `/` and `\` become underscores, leading dots are stripped. Prevents path traversal.
- Bytes are written as-is, no decode or decompress.
- To extract embedded images (not attached files), use the **PDF Extract Images** module.

## Troubleshooting

**Output folder is empty with "No embedded attachments found".** The PDF has no attached files. Check in Adobe Reader: View > Show/Hide > Navigation Panes > Attachments.

**Attachment name looks like mojibake.** The source PDF used non-UTF-8 encoding for the filename. The sanitizer replaces invalid characters, but the original name might already be corrupt in the source.

**Output file is smaller than expected.** The embedded file is compressed with an algorithm that extract doesn't decompress. Decompress manually (gzip, zip, etc.) per the file extension.
