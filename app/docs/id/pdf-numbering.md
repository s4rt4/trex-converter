# PDF Numbering

Tambah page numbering atau Bates numbering ke PDF.

## Deskripsi

Modul **PDF Numbering** insert teks ke setiap halaman PDF dengan template configurable. Engine `_op_page_numbering` di **PDFEngine** pakai `Page.insert_text` per halaman.

Template format string support placeholder `{n}` (current page number), `{total}` (total pages), `{page}` (alias `{n}`). Bisa pakai Python format spec untuk Bates-style padding (misal `{n:06d}`).

## Cara pakai

1. Klik **Browse** untuk pilih PDF.
2. Atur opsi:
   - **Format** template (contoh `Page {n} of {total}` atau `Bates {n:06d}`).
   - **Position** (gravity 9-arah, default southeast).
   - **Font size** (default 12).
   - **Start number** (default 1).
   - **Skip first N** halaman (untuk skip cover atau ToC).
   - **Opacity** (0 sampai 100, default 60).
3. Klik **Add to Queue**.

## Tips & Trick

- **Bates numbering** untuk legal docs: pakai format `BATES{n:06d}` atau `EXHIBIT-A-{n:04d}`. Angka zero-padded biar urutan tetap kalau di-sort by name.
- **Skip first N** untuk dokumen yang punya cover atau Table of Contents (numbering biasanya start dari halaman ke-3).
- **Position** southeast paling umum (kanan bawah). South untuk centered footer.
- **Opacity** 30 sampai 60 paling readable tanpa overpower konten.

## Troubleshooting

**Format error "unknown placeholder".** Template salah eja `{n}`, `{total}`, atau `{page}`. Cek backslash atau curly brace.

**Numbering ke-clip di edge halaman.** Pilih **Position** non-corner (misal south, north). Margin ke edge default 5% dari width/height halaman.

**Number muncul di halaman yang harusnya skip.** **Skip first N** count dari halaman 1 inclusive. Set ke 2 untuk skip halaman 1 dan 2 (cover plus blank).
