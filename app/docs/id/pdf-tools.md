# PDF Tools

Operasi PDF lengkap via **PyMuPDF** (fitz) plus **qpdf** plus **pdf2docx**.

## Deskripsi

Modul **PDF Tools** terima input PDF dan output ke format apapun yang tugas butuhkan: png, jpg, txt, html, docx, epub, atau pdf (operasi PDF ke PDF).

Panel options 6 tab:

- **Pages**: extract pages dengan range syntax (`1-3,5,8-10`), reorder dengan explicit list, rotate (90/180/270 derajat).
- **Security**: encrypt AES-256, decrypt, set user dan owner password.
- **Compress**: PyMuPDF garbage collection plus deflate, compress images dengan downsample DPI plus JPEG re-encode, qpdf linearize untuk web-fast PDF, repair via qpdf round-trip.
- **Watermark**: text watermark dengan gravity 9-arah dan opacity, atau image watermark PNG dengan width fraction halaman.
- **Redact**: search terms (comma-separated) lalu apply redaction (glyphs benar-benar dihapus, bukan ditutup), color preset (black, white, red, yellow) atau hex.
- **Metadata**: strip semua atau edit specific fields (title, author, subject, keywords, creator, producer).

## Cara pakai

1. Klik **Browse** untuk pilih PDF.
2. Pilih **Output format** (paling sering pdf untuk operasi internal, atau png/jpg untuk render, atau docx/epub untuk konversi).
3. Buka tab yang relevan dan pilih **Action**.
4. Atur sub-options sesuai action.
5. Klik **Add to Queue**.

## Tips & Trick

- **Compress images** target DPI 150 sudah cukup untuk on-screen reading. Drop ke 100 untuk web sharing.
- **Linearize** bikin PDF byte-streamed (pertama page muat duluan saat browser open). Cocok untuk hosting.
- **Redact** hapus glyphs permanent. Save copy dulu sebelum redact source asli.
- **PDF to DOCX** pakai pdf2docx, hasil paling baik untuk PDF text-based, kurang reliable untuk scan.
- **PDF to EPUB** pakai PyMuPDF HTML extraction lalu wrap minimal EPUB 2 (mimetype, container.xml, content.opf, toc.ncx, chapter per halaman).

## Troubleshooting

**"PDF is encrypted, provide password".** Centang Security tab dan masukkan **User password** untuk decrypt sebelum proses lain.

**Output PDF lebih besar dari input.** Compress dengan PyMuPDF tidak selalu shrink kalau source sudah optimized. Coba **Compress images** action dengan target 100 DPI.

**Redaction tidak hapus teks.** Pastikan **Search terms** sesuai exact teks di PDF (case-sensitive). Cek dengan extract text dulu untuk verifikasi exact wording.

**Linearize gagal "qpdf exited with code 2".** PDF sudah corrupt sebelum linearize. Run **Repair** action dulu.
