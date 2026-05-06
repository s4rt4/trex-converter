# Subtitle Merge

Concat banyak subtitle file (SRT, VTT, ASS) jadi satu file dengan dua mode.

## Deskripsi

Modul **Subtitle Merge** terima multi-input subtitle dan output satu file. Engine `_collect_merged_cues` di **SubtitleEngine** support mode:

- **Shift each file (sequential)**: cumulative offset plus optional gap. File pertama mulai dari 00:00, file kedua mulai setelah file pertama selesai plus gap.
- **Append + sort by time**: parse semua cue dari semua file, sort by start time. Cocok kalau setiap file punya timestamp absolut yang sudah benar.

Format input boleh campur (SRT plus VTT plus ASS). Output sesuai format yang dipilih.

## Cara pakai

1. Klik **Add files** atau drop banyak subtitle file.
2. Pilih **Output format** (srt, vtt, atau ass).
3. Pilih **Mode**:
   - **Shift each file (sequential)** plus set **Gap** (detik antar file, default 1).
   - **Append + sort by time**.
4. Klik **Select Location**.
5. Klik **Add to Queue**.

## Tips & Trick

- **Shift mode** cocok untuk gabung subtitle dari multi-part video (Episode 1, 2, 3 di-concat jadi season pack).
- **Append mode** cocok untuk subtitle yang dibuat per-scene dengan timestamp absolut (rare case).
- **Mixed format input** tidak masalah, parser handle SRT, VTT, ASS round-trip.
- **Gap** boleh 0 untuk seamless transition.

## Troubleshooting

**Cue overlap di output Shift mode.** Gap terlalu kecil atau cue terakhir di file pertama lebih panjang dari expected. Naikkan **Gap** ke 2 atau 3 detik.

**Output Append mode out-of-order.** Source punya timestamp tidak konsisten. Verifikasi tiap file di player dulu.

**ASS output kehilangan style.** Merge keep first file's style. Untuk preserve per-file style, output ke ASS dan edit manual style block setelah merge.
