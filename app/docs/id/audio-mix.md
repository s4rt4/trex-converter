# Audio Mix

Mix banyak track audio jadi satu file via **FFmpeg** amix filter.

## Deskripsi

Modul **Audio Mix** terima multi-input audio dan output satu file. Engine emit FFmpeg `amix` filter: `amix=inputs=N:duration=<longest|shortest|first>:normalize=<0|1>`. Format input dan output sama dengan modul **Audio** standalone.

Panel options: **Duration** (longest, shortest, first) dan **Normalize sum to 1/N** (default ON).

## Cara pakai

1. Klik **Add files** atau drop banyak audio file.
2. Pilih **Output format**.
3. Atur opsi:
   - **Duration**: longest (output sepanjang clip terpanjang), shortest (output sepanjang clip terpendek), first (output sepanjang clip pertama).
   - **Normalize**: divide sum dengan N untuk avoid clipping.
4. Klik **Select Location**.
5. Klik **Add to Queue**.

## Tips & Trick

- **Normalize ON** (default) cocok untuk mix vocals plus music tanpa clipping. **OFF** kalau setiap track sudah pre-leveled dan ingin sum direct.
- **Duration first** cocok untuk overlay narrator track atas background music (output panjang = panjang narrator).
- Untuk mix dengan volume per-track berbeda, pre-process tiap track via modul **Audio** Effects tab Gain dulu.
- Format mismatch (bitrate, sample rate beda) di-normalize otomatis oleh amix.

## Troubleshooting

**Output volume rendah.** Normalize ON divide N. Kalau cuma butuh sum, set Normalize OFF (resiko clipping).

**Hanya satu track terdengar.** Order files mungkin salah, atau salah satu file corrupt. Test tiap file individual di player dulu.

**Mix asymmetric (left/right beda).** Source punya channel layout beda (mono vs stereo). Force convert ke stereo dulu via modul **Audio** Output tab Channels.
