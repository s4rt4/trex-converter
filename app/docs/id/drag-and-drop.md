# Drag and Drop

Drop file dari file manager langsung ke window app.

## Deskripsi

Setiap **ConversionPage** accept drop event. Filter ekstensi otomatis sesuai `config.input_formats`. Multi-input page append semua file yang valid; single-input page ambil file pertama yang valid.

Implementation via Qt: `setAcceptDrops(True)` plus `dragEnterEvent`, `dragMoveEvent`, `dropEvent`. Routed ke `_accept_paths(paths)` shared helper.

## Cara pakai

1. Buka conversion page apapun (misal **Image**).
2. Drag file dari file manager ke window.
3. Drop. File otomatis muncul di **Input** field (atau di list untuk multi-input page).

## Tips & Trick

- **Multi-input pages** (PDF Merge, Video Concat, Image Montage, dll.) accept banyak file dalam satu drop.
- **Single-input pages** ambil file pertama yang valid kalau drop banyak file. Dialog info muncul kalau ada extra yang ke-skip.
- **Folder drop** di Archive Compress page accept folder (bukan file individual).
- **Mixed extensions**: file dengan ekstensi tidak valid di-reject dengan dialog warning.
- Drag dari mana saja: GNOME Files, Dolphin, Thunar, terminal pakai `xdg-mime`, dll.

## Troubleshooting

**Drop tidak detect file.** Beberapa file manager kirim URL bukan path. Driver Qt biasanya handle, tapi kalau gagal coba file manager lain.

**"No supported files in selection".** Semua file yang di-drop ekstensinya tidak match `input_formats`. Cek ekstensi target page (misal Image accept jpg/png/dst, bukan mp4).

**Drop ke single-input page tapi banyak file.** Cuma file pertama valid yang dipakai, sisanya di-ignore dengan dialog info. Untuk batch, pilih multi-input page (misal Image Montage instead of Image).
