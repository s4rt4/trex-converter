# Archive Compress

Compress a folder into an archive (zip, tar, tgz, tbz, txz) via Python stdlib.

## Description

The **Archive Compress** module takes a folder input (not a file) and outputs an archive. It uses stdlib `zipfile.ZipFile` with `ZIP_DEFLATED` for zip, or `tarfile.open(mode=w/w:gz/w:bz2/w:xz)` for tar variants. Iterates `Path.rglob("*")` for file-only entries with POSIX relative arcname.

## How to use

1. Click **Browse** to pick a source folder (folder picker, not file picker).
2. Pick an **Output format**: zip, tar, tgz, tbz, or txz.
3. Click **Select Location** for the archive output path.
4. Click **Add to Queue**.

## Tips & Trick

- **zip** is the most cross-platform-compatible (Windows native support).
- **tgz** (tar plus gzip) is the Linux/macOS standard, medium compression ratio, fast.
- **txz** (tar plus xz) has the best compression ratio but is slow. Good for archival.
- **tbz** (tar plus bzip2) is a compromise between tgz and txz.
- File-only iteration: empty subfolders aren't in the archive.

## Troubleshooting

**"Source folder is empty".** The source folder has no files. Add files or pick a different folder.

**Archive size matches the total file size.** The source contains already-compressed files (jpg, mp4, nested zip). Compression can't shrink them further.

**Strange path encoding on Windows extract.** zip supports UTF-8 file paths, but Windows' default zip uses cp1252. Extract on Linux or use 7-Zip on Windows.
