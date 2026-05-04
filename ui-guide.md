# T-Rex Converter UI Guide

Gunakan dokumen ini sebagai panduan visual saat membuka session Codex/Claude baru. Tujuannya menjaga UI tetap konsisten dengan arah desain terbaru.

## Prinsip Umum

- Aplikasi adalah desktop utility, bukan landing page. Prioritaskan workflow yang jelas, padat, dan cepat dipakai.
- Gunakan sidebar sebagai navigasi utama. Jangan menambahkan toolbar global baru kecuali benar-benar diperlukan.
- UI harus terasa modern tetapi tetap native PySide6/Qt. Hindari dekorasi berlebihan.
- Jaga kontras dan keterbacaan di atas background beige `BRAND_SURFACE`.
- Gunakan icon untuk action ringkas seperti dependency check, cancel, retry, dropdown, dan browse.
- Rounded corner konsisten: mayoritas kontrol memakai radius `8px`.

## Warna Brand

Token utama ada di `app/ui/theme.py`.

- Surface: `#EFE3CA`
- Dark: `#0C2C55`
- Accent: `#56B6C6`
- Muted surface: `#E4D7BD`
- Soft surface: `#F6EBD4`
- Soft dark: `#24158F`

Aturan pemakaian:

- Background utama: `BRAND_SURFACE`.
- Panel/form/card: `BRAND_SURFACE_SOFT`.
- Tombol utama: solid `BRAND_DARK`, teks `BRAND_SURFACE`, border `BRAND_ACCENT`.
- Sidebar: dark semi-transparan/soft, jangan terlalu berat.
- Aksen cyan dipakai untuk border tipis, selected state, icon, dan highlight.

## Sidebar

Sidebar saat ini berisi:

- Dashboard
- Image
- Video
- Document
- PDF Tools
- About

Panduan:

- Width sekitar `204px`.
- Logo tetap kecil, teks `T-Rex Converter` jangan terlalu dominan.
- Active item memakai highlight halus dan indikator kiri cyan.
- Dependency check hanya icon kecil di pojok bawah sidebar, bukan tombol besar.
- Gunakan `qtawesome` melalui helper `app/ui/icons.py`.

## Page Structure

Setiap halaman conversion memakai pola:

- Title di atas.
- Tab utama bergaya segmented/pill: `Convert` dan `Queue`.
- `Convert` berisi form input/output dan opsi.
- `Queue` berisi queue table terfilter sesuai kategori halaman.

Jangan kembalikan tab ke gaya klasik yang menempel pada garis border. Tab harus terasa seperti segmented control modern:

- Background tab nonaktif muted/transparan.
- Tab aktif dark dengan teks accent.
- Radius `8px`.
- Ada jarak antar tab.

## Form Layout

Form conversion berada di `ToolPanel`.

Panduan spacing:

- Jangan biarkan elemen saling menempel.
- Row layout harus punya spacing `8-14px`.
- Input panjang boleh stretch, tapi tombol seperti `Browse` dan `Select Location` harus punya jarak jelas.
- Label field memakai `#FieldLabel`, kecil, tebal, dark.
- Form sebaiknya memakai `QGridLayout` atau row layout yang rapi, bukan horizontal penuh yang membuat mata bergerak terlalu jauh.

Input fields:

- `QLineEdit`, `QComboBox`, `QSpinBox`, `QDoubleSpinBox` memakai border accent dan radius `8px`.
- Jangan custom spinbox arrow dengan CSS segitiga. Biarkan Qt/Fusion menggambar `UpDownArrows`; custom CSS subcontrol pernah membuat area kanan terlihat seperti blok kosong.
- Placeholder harus singkat dan praktis, contoh `1280x1280>`, `192k`, `WxH+X+Y (advanced)`.

Checkbox:

- Indicator checkbox harus punya border gelap agar terlihat di background beige.
- Checked state memakai dark fill dan accent border.
- Jangan pakai default checkbox putih tanpa border.

## Image Options

Panel image options ada di `app/ui/image_options.py`.

Tab opsi:

- `Transform`
- `Color`
- `Filter`
- `Border`
- `Watermark`

Panduan:

- Tab image options juga harus bergaya segmented/pill, bukan tab klasik.
- Pane memakai soft surface dengan border accent transparan.
- Opsi dikelompokkan rapat tapi tetap punya grid spacing.
- Jangan menaruh semua opsi image di form utama; form utama hanya untuk conversion basics, opsi lanjutan tetap di panel image options.

## Queue Table

Queue table adalah komponen penting.

Panduan:

- Gunakan `QueuePanel` sebagai styling global. Jangan buat table custom per halaman kecuali perlu.
- Queue harus terfilter berdasarkan kategori task, bukan hanya extension. Extension seperti `png/jpg` bisa dipakai Image dan PDF Tools, jadi filter berdasarkan `task.options["category"]`.
- Input/output cell memakai `FileCell`:
  - thumbnail untuk image jika file ada;
  - icon file untuk format lain;
  - nama file tebal;
  - parent path kecil di bawahnya;
  - full path di tooltip.
- Tombol action queue icon-only:
  - Cancel: icon `times-circle`
  - Retry: icon `redo`
  - Pakai tooltip, jangan teks tombol panjang.

## Dashboard

Dashboard adalah halaman pertama.

Panduan:

- Tampilkan summary cards untuk total/running/completed/failed.
- Di bawahnya tampilkan all-task queue.
- Summary card harus tenang dan utilitarian: soft surface, border accent halus, angka besar dark.

## About

About page sederhana:

- Logo.
- Nama aplikasi.
- Versi.
- Deskripsi singkat.

Jangan dibuat seperti landing page/marketing page.

## Dependency Check

- Tetap tersedia di sidebar sebagai icon-only button.
- Dialog dependency boleh berupa list sederhana `name: OK/missing`.
- Dependency Python module ditulis dengan format `python:module`, contoh `python:fitz`.

## Jangan Dilakukan

- Jangan membuat sidebar terlalu kontras/berat.
- Jangan membuat tombol dependency besar lagi.
- Jangan mengembalikan queue action ke tombol teks `Cancel`/`Retry`.
- Jangan membuat tab klasik dengan border bawah yang terlihat seperti table header.
- Jangan custom spinbox arrow memakai CSS triangle/subcontrol yang menutupi panah.
- Jangan filter PDF/Image queue hanya berdasarkan extension.
- Jangan memakai card bertumpuk di dalam card.
- Jangan menambah hero/landing section.

## File UI Penting

- `app/ui/main_window.py`: shell, sidebar, stylesheet global.
- `app/ui/conversion_page.py`: layout halaman conversion, tab Convert/Queue, category tagging.
- `app/ui/image_options.py`: advanced image option tabs.
- `app/ui/queue_panel.py`: table queue, file cell, action buttons.
- `app/ui/dashboard_page.py`: summary cards dan all-task queue.
- `app/ui/about_page.py`: about page.
- `app/ui/theme.py`: token warna brand.
- `app/ui/icons.py`: helper icon `qtawesome`.

## Checklist Setelah Mengubah UI

Jalankan:

```bash
.venv/bin/python -m compileall app
.venv/bin/python -m pytest
```

Lalu restart GUI:

```bash
pkill -f t-rex-converter
setsid .venv/bin/t-rex-converter >/tmp/trex-converter.log 2>&1 &
```

Pastikan secara visual:

- Tidak ada elemen form yang menempel.
- Checkbox terlihat jelas.
- Spinbox tidak memiliki area kanan kosong.
- Tab terlihat seperti segmented/pill.
- Queue Image tidak muncul di PDF Tools, dan sebaliknya.
