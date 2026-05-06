# Ebook

Konversi format ebook dan markup via **Pandoc** (138 pair format matrix).

## Deskripsi

Modul **Ebook** wrap `pandoc --from F --to T --output OUT IN` dengan 9 format bidirectional plus txt sebagai output-only:

- epub, docx, odt, html, markdown (md), rst, latex (tex), org, fb2.
- Output txt via Pandoc `plain` writer.

Aliases collapsed: md ke markdown, latex ke tex, html ke htm. Total 138 valid pair.

Panel options: title, author, language, publisher, date metadata fields, plus **Generate table of contents** (`--toc`) dan **Embed resources** (`--embed-resources` untuk HTML self-contained).

## Cara pakai

1. Klik **Browse** untuk pilih input file (md, docx, epub, dll.).
2. Pilih **Output format**.
3. (Opsional) Isi metadata fields (title, author, lang) untuk EPUB/DOCX yang punya metadata block.
4. (Opsional) Centang **TOC** untuk auto-generate table of contents.
5. (Opsional) Centang **Embed resources** untuk HTML self-contained output.
6. Klik **Add to Queue**.

## Tips & Trick

- **md ke epub** alur paling umum: tulis ebook di markdown, generate EPUB dengan TOC. Set title plus author untuk metadata yang ditampilkan di reader.
- **html ke pdf** tidak support oleh Pandoc langsung (perlu LaTeX engine). Pakai modul **Document** untuk html ke pdf via LibreOffice instead.
- **Embed resources** inline images plus CSS jadi single HTML file. Cocok untuk archive atau email.
- **org ke markdown** untuk migrasi dari Emacs Org-mode ke Obsidian, dst.
- **Pandoc extra args** option (advanced): set list of flags untuk advanced Pandoc features (`--mathjax`, `--ascii`, dll.).

## Troubleshooting

**"pandoc exited with code N".** Cek log task untuk Pandoc error message. Common: format input tidak match dengan extension (misal file `.md` ternyata isinya RST).

**EPUB output tidak punya cover.** Pandoc tidak embed cover image otomatis. Pakai **Pandoc extra args** dengan `--epub-cover-image=cover.jpg`.

**MOBI conversion not supported.** Pandoc tidak handle MOBI. Convert ke EPUB dulu, lalu pakai Calibre `ebook-convert` external untuk EPUB ke MOBI.
