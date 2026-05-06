# Document

Konversi dokumen office via **LibreOffice** headless.

## Deskripsi

Modul **Document** wrap `libreoffice --headless --convert-to ...` dengan format matrix penuh (52 pair):

- Text: doc, docx, odt, rtf ke docx, odt, rtf, html, epub, txt, pdf.
- Spreadsheet: xls, xlsx, ods ke xlsx, ods, csv, html, pdf.
- Presentation: ppt, pptx, odp ke pptx, odp, pdf.

Panel options single-pane untuk PDF/A archival dan password-protected PDF.

## Cara pakai

1. Klik **Browse** untuk pilih file dokumen.
2. Pilih **Output format**.
3. Atur opsi (saat output PDF):
   - **PDF/A-1a archival** checkbox untuk arsip jangka panjang.
   - **User password** untuk lock open access.
   - **Owner password** untuk restrict permissions (print, copy, edit).
4. Klik **Add to Queue**.

## Tips & Trick

- **Headless mode** start LibreOffice background instance pertama kali, jadi conversion pertama agak lambat (5 sampai 10 detik). Berikutnya cepat.
- **PDF/A-1a** trigger filter `pdf:writer_pdf_Export:{"SelectPdfVersion":{"type":"long","value":"1"}}`. Cocok untuk archive ISO 19005.
- **Password user** lock open access, **password owner** lock permissions. Bisa dipakai bareng.
- Output di subfolder: combo dropdown **Output format** otomatis ganti extension di output path.

## Troubleshooting

**Conversion stuck atau timeout.** LibreOffice headless instance sebelumnya masih jalan. Kill: `pkill -f soffice`. Restart conversion.

**PDF/A gagal dengan error filter.** LibreOffice version lama (<7.0) butuh syntax filter berbeda. Upgrade ke LibreOffice 7.x.

**Font hilang di output.** Source dokumen pakai font yang tidak terinstall di sistem. Install font pack: `apt install fonts-noto fonts-liberation`.
