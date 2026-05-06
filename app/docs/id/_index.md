# Selamat Datang

T-Rex Converter adalah converter file lokal untuk Debian. Semua proses jalan di mesin kamu, tidak ada upload ke cloud.

## Deskripsi

Sidebar di kiri berisi modul yang sudah disusun per kategori: gambar, video, audio, dokumen, PDF, OCR, subtitle, archive, QR/barcode, SVG/vector, ebook, dan metadata. Setiap modul punya halaman sendiri dengan opsi yang relevan.

Engine yang dipakai semua tool standar di Debian: `ffmpeg`, `magick` (ImageMagick), `libreoffice`, `qpdf`, `tesseract`, `inkscape`, `potrace`, `pandoc`, `exiftool`, `qrencode`, `zbarimg`. Kalau salah satu hilang, dependency dialog di footer sidebar akan kasih tau.

## Cara pakai

1. Pilih modul di sidebar (misal **Image**).
2. Klik **Browse** atau drop file ke window.
3. Pilih **Output format** dari dropdown.
4. Atur opsi di panel bawah form (kalau ada).
5. Klik **Add to Queue**.
6. Pantau progress di tab **Queue**.

## Tips & Trick

- **Drag-and-drop** jalan di setiap halaman conversion. Multi-input page menerima banyak file sekaligus.
- **Preset** di setiap halaman bisa simpan kombinasi opsi favorit ke `~/.config/trex-converter/presets/`.
- **Dashboard** punya tab **Activity** dengan chart per hari, per minggu, per bulan, atau per tahun.
- Tombol **Info** atau double-click row di queue table buka dialog detail dengan log lengkap dan thumbnail.

## Troubleshooting

**Engine missing.** Cek footer sidebar (tombol cog), lihat daftar binary. Install yang merah lewat `apt install <nama>`.

**App crash saat pertama buka.** Cek `~/.config/trex-converter/`. Kalau settings.json corrupt, hapus file itu dan default akan dipakai ulang.

**Output ke-clip di layar kecil.** Convert tab punya scroll vertical sekarang, geser scrollbar di kanan.
