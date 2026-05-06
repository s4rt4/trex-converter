# Metadata

Cross-cut metadata editor untuk image, audio, video, PDF via **exiftool**.

## Deskripsi

Modul **Metadata** wrap `exiftool` untuk tiga operasi:

- **Read**: dump semua tag ke `.txt` (JSON atau plain text).
- **Strip**: hapus semua tag (`-overwrite_original -all=`).
- **Edit**: set tag specific (Title, Artist, Author, Subject, Description, Comment, Copyright, Keywords).

Format input cross-cut: image (jpg, jpeg, png, tif, tiff, heic, webp, gif), audio (mp3, m4a, flac, wav, ogg), video (mp4, mov, mkv, webm), pdf.

## Cara pakai

1. Klik **Browse** untuk pilih file (apa saja dari format support).
2. Pilih **Operation**:
   - **Strip** untuk hapus semua metadata. Output sama format dengan input.
   - **Edit** untuk set fields. Output sama format dengan input.
   - **Read** untuk dump metadata. Output `.txt`.
3. Kalau **Edit**: isi fields yang mau di-set (kosong = skip).
4. Kalau **Read**: pilih **Read format** (JSON atau Plain text).
5. Klik **Add to Queue**.

## Tips & Trick

- **Strip** sebelum upload foto ke web untuk hapus EXIF GPS, camera serial, dll. (privacy).
- **Edit Title plus Artist** untuk MP3 collection. Tag exiftool standard work cross-format (Title, Artist sama untuk MP3, M4A, FLAC).
- **Read JSON** machine-readable, cocok kalau mau script lanjutan. Plain text human-readable.
- **Cross-format**: tag name exiftool generic. `-Title=` work di JPG (XMP), MP3 (ID3), MP4 (iTunes metadata), PDF (DocInfo).
- **Output sama format**: Strip dan Edit copy file dulu lalu modify. Source tidak berubah.

## Troubleshooting

**"exiftool exited with code 1".** Tag name typo atau tag tidak applicable untuk format target. Cek log untuk error message.

**Strip tidak hapus tertentu.** Beberapa tag protected (Container metadata di MP4, color profile di image). Pakai exiftool flag `-charset filename=utf8` atau filter specific.

**Output file lebih besar dari source.** Strip tidak shrink file kalau metadata sebagian kecil dari total size. Untuk shrink (re-encode), pakai modul format-specific (Image, Audio).
