# PDF Extract Attachments

Extract embedded file attachments dari PDF ke folder.

## Deskripsi

PDF support attached files (mirip ZIP container). Modul **PDF Extract Attachments** walk `Document.embfile_count`, `embfile_info`, `embfile_get` untuk dump tiap attachment dengan nama original (sanitized via `_safe_attachment_name`).

## Cara pakai

1. Klik **Browse** untuk pilih PDF.
2. Klik **Select Location** untuk pilih output folder.
3. Klik **Add to Queue**.

## Tips & Trick

- Cocok untuk PDF yang attach source file (misal academic paper attach dataset CSV, atau form attach signed copy).
- File name di-sanitize: replace `/` dan `\` dengan underscore, strip leading dots. Mencegah path traversal.
- Bytes ditulis as-is, tidak ada decode atau decompress.
- Untuk extract embedded image (bukan attached file), pakai modul **PDF Extract Images**.

## Troubleshooting

**Output folder kosong "No embedded attachments found".** PDF tidak punya attached file. Cek di Adobe Reader: View > Show/Hide > Navigation Panes > Attachments.

**Attachment name aneh / mojibake.** Source PDF pakai encoding non-UTF-8 untuk filename. Sanitizer replace karakter invalid, tapi name awal mungkin sudah corrupt di source.

**File output lebih kecil dari expected.** Embedded compressed dengan algoritma yang tidak di-decompress oleh extract. Coba decompress manual (gzip, zip, dst.) sesuai ext file.
