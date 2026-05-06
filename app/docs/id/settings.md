# Settings

Default app behavior dan per-modul preference.

## Deskripsi

Halaman **Settings** persist setting di `~/.config/trex-converter/settings.json`. Field yang tersedia:

- **Default output folder**: kalau diisi, semua page suggest path output di folder ini. Kosong = same folder dengan input.
- **Max concurrent tasks**: jumlah worker queue paralel (1 sampai 16). Apply on next launch.
- **Image quality**: default JPG/WebP/AVIF quality slider (1 sampai 100).
- **PDF render DPI**: default DPI saat render PDF ke image.
- **OCR language**: preset eng, ind, eng+ind, atau custom (misal `eng+jpn`).
- **Video CRF**: default CRF untuk video output (0 = off).
- **Video x264 preset**: default speed/quality preset.
- **Audio bitrate**: default bitrate untuk audio output (misal `192k`).

## Cara pakai

1. Buka **Settings** dari sidebar.
2. Atur field yang relevan.
3. Klik **Save**. Sebagian besar setting apply immediately, kecuali **Max concurrent tasks** (apply on next launch).
4. Klik **Reset** untuk revert ke saved values (bukan factory default).
5. Klik **Open config folder** untuk buka `~/.config/trex-converter/` di file manager.

## Tips & Trick

- **Output folder** di-honor oleh setiap conversion page saat suggest path output. Bisa di-override per task.
- **Max concurrent** 1 untuk debug atau low-RAM machine. 4 atau 8 untuk batch processing di workstation.
- **OCR language Custom** terima format Tesseract: combine kode bahasa dengan `+`. Pastikan language pack ke-install (`apt install tesseract-ocr-<kode>`).
- **Video CRF default 0** artinya off. Set 23 kalau ingin semua video conversion default ke quality medium.

## Troubleshooting

**Setting tidak ke-save.** Cek permission `~/.config/trex-converter/settings.json`. Harusnya writable oleh user. Kalau corrupt, hapus file dan default akan dipakai ulang.

**Concurrency tidak berubah setelah save.** Apply on next launch only. Restart app.

**Open config folder gagal.** Linux butuh `xdg-open`. macOS pakai `open`. Windows pakai `explorer`. Install xdg-utils kalau di Linux belum ada.
