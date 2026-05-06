# Archive

Extract archives (zip, tar, tgz, tbz, txz, gz, bz2, xz) into a folder via Python stdlib.

## Description

The **Archive** module is pure Python (no external binary needed) using stdlib `zipfile` and `tarfile`. The engine rejects path-traversal entries (`../escape.txt`) and absolute paths. Tar extract uses `filter='data'` (Python 3.14 default-safe).

## How to use

1. Click **Browse** to pick an archive.
2. Click **Select Location** to pick the output folder.
3. Click **Add to Queue**.

## Tips & Trick

- Format auto-detected from the extension. `.zip`, `.tar`, `.tar.gz` (alias `.tgz`), `.tar.bz2` (alias `.tbz`), `.tar.xz` (alias `.txz`), plus single-file `.gz`, `.bz2`, `.xz`.
- **Path-traversal protection**: entries with `../` or absolute paths are rejected before extracting.
- Output folder is created if it doesn't exist.
- To compress a folder into an archive, use the **Archive Compress** module.

## Troubleshooting

**"Refusing to extract entry outside target folder".** The archive contains a malicious entry. Either corrupt or a crafted attack. Not extracted.

**Output folder has odd files.** The archive is normal but the source folder structure is complex. Inspect the archive first via `unzip -l` or `tar -tf`.

**Permission denied.** The output folder isn't writable. Pick a different folder or `chmod` first.
