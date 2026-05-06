# Presets

Simpan dan load kombinasi opsi favorit per conversion page.

## Deskripsi

Tiap conversion page punya **Preset** combo plus tombol **Load**, **Save**, **Delete** di bawah panel options. Preset disimpan sebagai JSON di `~/.config/trex-converter/presets/<kind>/<name>.json`.

Save capture `_options()` (semua field di panel + main form fields kayak quality dan resize) minus auto-injected `category` field. Load apply scalar fields ke main form, lalu delegate ke `extra_options_widget.apply_preset(payload)` kalau panel support hook itu.

## Cara pakai

### Save preset

1. Buka conversion page (misal **Image**).
2. Atur opsi sesuai keinginan (misal Quality 95, Resize `1920x>`, Strip metadata ON).
3. Klik **Save**. Masukkan nama preset (1 sampai 40 karakter, alphanumeric plus space, hyphen, underscore).
4. Preset muncul di combo.

### Load preset

1. Pilih preset di combo.
2. Klik **Load**. Field yang saved di-apply.
3. Browse input file.
4. Klik **Add to Queue**.

### Delete preset

1. Pilih preset di combo.
2. Klik **Delete** dan konfirmasi.

## Tips & Trick

- Preset per page (kind), bukan global. Image preset terpisah dari Video preset, dst.
- Naming: deskriptif tapi pendek. Misal `web-jpg`, `archive-pdf`, `4k-720p`, `mp3-320k`.
- File JSON readable, bisa di-edit manual lewat editor di `~/.config/trex-converter/presets/<kind>/`.
- Sync ke machine lain: copy folder `~/.config/trex-converter/presets/` ke target.

## Troubleshooting

**"Preset name must be 1-40 characters of letters, digits, spaces, hyphens, or underscores".** Karakter invalid (misal `/`, `\`, koma). Pakai alphanumeric plus space, hyphen, underscore.

**Preset tidak muncul setelah Save.** Refresh page (klik sidebar entry lagi). Atau cek file JSON di config folder, mungkin ke-write tapi listing belum re-load.

**Load tidak apply semua field.** Panel tidak implement `apply_preset` hook. Cuma scalar fields (quality, resize, strip, bitrate) yang di-apply by default.
