# Metadata

Cross-cut metadata editor for image, audio, video, PDF via **exiftool**.

## Description

The **Metadata** module wraps `exiftool` for three operations:

- **Read**: dump every tag to `.txt` (JSON or plain text).
- **Strip**: remove every tag (`-overwrite_original -all=`).
- **Edit**: set specific tags (Title, Artist, Author, Subject, Description, Comment, Copyright, Keywords).

Cross-cut input formats: image (jpg, jpeg, png, tif, tiff, heic, webp, gif), audio (mp3, m4a, flac, wav, ogg), video (mp4, mov, mkv, webm), pdf.

## How to use

1. Click **Browse** to pick a file (anything from the supported formats).
2. Pick an **Operation**:
   - **Strip** to remove all metadata. Output keeps the input format.
   - **Edit** to set fields. Output keeps the input format.
   - **Read** to dump metadata. Output is `.txt`.
3. For **Edit**: fill in the fields to set (empty = skip).
4. For **Read**: pick **Read format** (JSON or Plain text).
5. Click **Add to Queue**.

## Tips & Trick

- **Strip** before uploading photos to remove EXIF GPS, camera serial, etc. (privacy).
- **Edit Title plus Artist** for an MP3 collection. exiftool tags are generic and work across formats (Title and Artist are the same on MP3, M4A, FLAC).
- **Read JSON** is machine-readable for further scripting. Plain text is human-readable.
- **Cross-format**: tag names are generic. `-Title=` works on JPG (XMP), MP3 (ID3), MP4 (iTunes metadata), PDF (DocInfo).
- **Same output format**: Strip and Edit copy the file first then modify. The source stays untouched.

## Troubleshooting

**"exiftool exited with code 1".** Tag name typo or the tag isn't applicable to the target format. Check the log for the error message.

**Strip doesn't remove certain tags.** Some tags are protected (container metadata in MP4, color profiles in images). Use the exiftool `-charset filename=utf8` flag or a more specific filter.

**Output file is larger than the source.** Strip doesn't shrink files when metadata is a small fraction of total size. To actually shrink (re-encode), use a format-specific module (Image, Audio).
