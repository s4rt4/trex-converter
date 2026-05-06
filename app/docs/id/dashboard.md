# Dashboard

Halaman ringkasan semua aktivitas conversion plus status sistem.

## Deskripsi

Dashboard punya empat **summary card** di atas (Total, Running, Completed, Needs attention) plus tab **All Tasks**, **Activity**, dan **Engines** di bawah.

**All Tasks** isinya queue table semua task lintas modul, di-update real-time via subscriber `TaskQueue`.

**Activity** isinya bar chart **QtCharts** dengan filter **Per day**, **Per week**, **Per month**, **Per year**. Otomatis ambil 24 bucket terakhir biar tetap readable kalau histori panjang.

**Engines** isinya grid 11 binary engine dengan status `installed` (hijau) atau `missing` (merah), plus FFmpeg hardware accel detected (`vaapi`, `cuda`, `qsv`, dst.).

## Cara pakai

1. Buka **Dashboard** dari sidebar (default page saat app start).
2. Pantau jumlah task di summary cards.
3. Klik tab **Activity** dan pilih **Bucket** untuk lihat chart.
4. Klik tab **Engines** untuk audit engine apa yang missing, install via `apt`.
5. Klik tombol **Refresh** kalau baru install engine baru.

## Tips & Trick

- Klik **Info** atau double-click row di **All Tasks** buat buka dialog detail (input/output thumbnail plus full log).
- Chart auto-refresh setiap kali ada task baru selesai, tidak perlu manual refresh.
- Bucket label `2026-W18` artinya minggu ke-18 tahun 2026 (ISO week format dari SQLite `strftime`).

## Troubleshooting

**Chart kosong.** Belum ada task di database. Coba run satu conversion dulu, dashboard akan auto-update.

**Hardware accel "none detected".** Bisa karena `ffmpeg` belum terinstall, atau driver GPU kamu memang tidak support hardware encoding. Cek `ffmpeg -hwaccels` di terminal.
