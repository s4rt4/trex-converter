# Archive Compress

Compress folder ke archive (zip, tar, tgz, tbz, txz) via Python stdlib.

## Deskripsi

Modul **Archive Compress** terima folder input (bukan file) dan output ke archive. Pakai stdlib `zipfile.ZipFile` dengan `ZIP_DEFLATED` untuk zip, atau `tarfile.open(mode=w/w:gz/w:bz2/w:xz)` untuk tar variants. Iterate `Path.rglob("*")` untuk file-only entries dengan POSIX relative arcname.

## Cara pakai

1. Klik **Browse** untuk pilih folder source (folder picker, bukan file picker).
2. Pilih **Output format**: zip, tar, tgz, tbz, atau txz.
3. Klik **Select Location** untuk archive output path.
4. Klik **Add to Queue**.

## Tips & Trick

- **zip** paling kompatibel cross-platform (Windows native support).
- **tgz** (tar plus gzip) standard di Linux/macOS, compression rasio menengah, fast.
- **txz** (tar plus xz) compression rasio terbaik tapi lambat. Cocok untuk archival.
- **tbz** (tar plus bzip2) compromise antara tgz dan txz.
- File-only iteration: empty subfolder tidak masuk archive.

## Troubleshooting

**"Source folder is empty".** Folder source kosong. Tambah file atau pilih folder lain.

**Archive size sama dengan total file size.** Source berisi file yang sudah pre-compressed (jpg, mp4, zip nested). Compression tidak bisa shrink lagi.

**Path encoding aneh di Windows extract.** zip support file path UTF-8, tapi Windows zip default cp1252. Extract di Linux atau pakai 7-Zip di Windows.
