# Archive

Extract archive (zip, tar, tgz, tbz, txz, gz, bz2, xz) ke folder via Python stdlib.

## Deskripsi

Modul **Archive** pure Python (no external binary needed) pakai stdlib `zipfile` dan `tarfile`. Engine reject path traversal (`../escape.txt`) dan absolute paths. Tar extract pakai `filter='data'` (Python 3.14 default-safe).

## Cara pakai

1. Klik **Browse** untuk pilih archive.
2. Klik **Select Location** untuk pilih output folder.
3. Klik **Add to Queue**.

## Tips & Trick

- Format auto-detect dari extension. `.zip`, `.tar`, `.tar.gz` (alias `.tgz`), `.tar.bz2` (alias `.tbz`), `.tar.xz` (alias `.txz`), plus single-file `.gz`, `.bz2`, `.xz`.
- **Path-traversal protection**: entries dengan `../` atau absolute path di-reject sebelum extract.
- Output folder di-create kalau belum ada.
- Untuk compress folder ke archive, pakai modul **Archive Compress**.

## Troubleshooting

**"Refusing to extract entry outside target folder".** Archive berisi malicious entry. Bisa jadi corrupt atau crafted attack. Tidak di-extract.

**Output folder ada file aneh.** Archive normal tapi struktur folder source kompleks. Cek archive content dulu via `unzip -l` atau `tar -tf`.

**Permission denied.** Output folder tidak writable. Pilih folder lain atau `chmod` dulu.
