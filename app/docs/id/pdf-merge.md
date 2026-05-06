# PDF Merge

Gabung beberapa PDF jadi satu file via **PyMuPDF** `Document.insert_pdf`.

## Deskripsi

Modul **PDF Merge** terima multi-input PDF dan output satu file PDF dengan halaman dari semua source di-concat sesuai urutan list. Engine `_run_merge` iterate `task.inputs` dan panggil `Document.insert_pdf(source)` per file.

## Cara pakai

1. Klik **Add files** atau drop banyak PDF ke window.
2. Atur urutan dengan **Remove** dan re-add (urutan list = urutan output).
3. Klik **Select Location** untuk pilih output PDF path.
4. Klik **Add to Queue**.

## Tips & Trick

- **Drag-and-drop** banyak file sekaligus untuk batch quick.
- **Order matters**: file pertama di list jadi halaman 1 sampai N, file kedua melanjutkan, dst.
- **Encrypted PDF** ditolak: decrypt dulu di **PDF Tools** Security tab.
- Output di-save dengan `garbage=4 deflate=True` untuk minimize size.

## Troubleshooting

**"PDF merge requires at least two input PDFs".** Cuma satu file di list. Tambah file kedua atau pakai modul **PDF Tools** untuk operasi single-file.

**"Source PDF is encrypted".** Salah satu input encrypted. Decrypt dulu lewat **PDF Tools** Security tab Decrypt action.

**Output corrupt atau halaman hilang.** PDF source punya struktur incremental update yang corrupt. Repair source via **PDF Tools** Compress tab Repair action sebelum merge.
