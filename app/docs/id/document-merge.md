# Document Merge

Gabung banyak dokumen Office (DOCX, ODT, RTF, dll.) jadi satu PDF.

## Deskripsi

Modul **Document Merge** terima multi-input dokumen Office dan output satu PDF. Engine `_bulk_merge_to_pdf` di **LibreOfficeEngine**: per-input convert ke PDF di tempdir (skip kalau sudah PDF), lalu PyMuPDF `Document.insert_pdf` concat semuanya ke output.

Format input: doc, docx, odt, rtf, xls, xlsx, ods, ppt, pptx, odp, pdf.

## Cara pakai

1. Klik **Add files** atau drop banyak dokumen.
2. Atur urutan dengan **Remove** dan re-add.
3. Klik **Select Location** untuk output PDF path.
4. Klik **Add to Queue**.

## Tips & Trick

- Mix berbagai format input: DOCX, ODT, RTF, PDF bisa digabung dalam satu queue. Engine convert per-input dulu lalu concat.
- PDF input pass-through tanpa re-convert (hemat waktu).
- Output `garbage=4 deflate=True` untuk minimize size.
- Untuk merge PDF only (tanpa Office input), pakai modul **PDF Merge** lebih cepat (skip LibreOffice spinup).

## Troubleshooting

**Conversion lambat untuk file pertama.** LibreOffice headless instance baru start. Run berikutnya cepat (instance reused).

**Format input "unsupported".** Cek extension. Modul ini terima format Office, bukan random text file. Untuk markdown/html, pakai **Ebook**.

**Output PDF order salah.** Order list = order output. Re-add file dalam urutan yang benar.
