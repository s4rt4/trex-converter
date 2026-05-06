# PDF Tools

Full PDF operations via **PyMuPDF** (fitz) plus **qpdf** plus **pdf2docx**.

## Description

The **PDF Tools** module accepts PDF input and outputs to whatever the task needs: png, jpg, txt, html, docx, epub, or pdf (PDF-to-PDF operations).

Options panel has 6 tabs:

- **Pages**: extract pages with range syntax (`1-3,5,8-10`), reorder with an explicit list, rotate (90/180/270 degrees).
- **Security**: encrypt AES-256, decrypt, set user and owner passwords.
- **Compress**: PyMuPDF garbage collection plus deflate, compress images with DPI downsample plus JPEG re-encode, qpdf linearize for web-fast PDF, repair via qpdf round-trip.
- **Watermark**: text watermark with 9-position gravity and opacity, or PNG image watermark with page width fraction.
- **Redact**: search terms (comma-separated) then apply redaction (glyphs are actually removed, not just covered), color preset (black, white, red, yellow) or hex.
- **Metadata**: strip everything or edit specific fields (title, author, subject, keywords, creator, producer).

## How to use

1. Click **Browse** to pick a PDF.
2. Pick an **Output format** (most often pdf for in-place ops, or png/jpg for render, or docx/epub for conversion).
3. Open the relevant tab and pick an **Action**.
4. Adjust sub-options for the action.
5. Click **Add to Queue**.

## Tips & Trick

- **Compress images** with target DPI 150 is fine for on-screen reading. Drop to 100 for web sharing.
- **Linearize** makes a byte-streamed PDF (first page loads first when browsers open it). Good for hosting.
- **Redact** removes glyphs permanently. Save a copy before redacting the original.
- **PDF to DOCX** uses pdf2docx, with best results on text-based PDFs, less reliable on scans.
- **PDF to EPUB** uses PyMuPDF HTML extraction then wraps a minimal EPUB 2 (mimetype, container.xml, content.opf, toc.ncx, one chapter per page).

## Troubleshooting

**"PDF is encrypted, provide password".** Open the Security tab and enter the **User password** to decrypt before another operation.

**Output PDF is larger than the input.** PyMuPDF compress doesn't always shrink an already-optimized source. Try **Compress images** action with target 100 DPI.

**Redaction doesn't remove text.** Make sure **Search terms** match the exact text in the PDF (case-sensitive). Verify by extracting text first to confirm exact wording.

**Linearize fails with "qpdf exited with code 2".** The PDF is already corrupt before linearize. Run the **Repair** action first.
