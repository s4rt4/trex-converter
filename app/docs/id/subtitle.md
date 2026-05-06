# Subtitle

Konversi format subtitle (SRT, VTT, ASS) dengan time shift via Python parser pure.

## Deskripsi

Modul **Subtitle** tidak butuh binary external. Engine `SubtitleEngine` parse dan format SRT, VTT, ASS round-trip plus optional time shift (geser semua cue plus atau minus N detik).

ASS parser support full subset: section dispatcher `[Events]`, Format header detection, Dialogue rows dengan koma di Text field, escape sequences `\N` dan `\n`, Comment lines diskip. Formatter ASS emit minimal Script Info plus V4+ Styles plus Events dengan default Arial 32 white.

## Cara pakai

1. Klik **Browse** untuk pilih file subtitle.
2. Pilih **Output format** (srt, vtt, atau ass).
3. (Opsional) Atur **Time shift** dalam seconds (positif geser maju, negatif geser mundur, dibatasi minus 3600 sampai 3600).
4. Klik **Add to Queue**.

## Tips & Trick

- **Time shift** clamp ke 0 saat negatif overshoot (cue tidak boleh start time negatif).
- **VTT to SRT** drop cue identifier dan WEBVTT/NOTE/STYLE blocks.
- **ASS round-trip** preserve text dengan koma dan multi-line via `\N`.
- Untuk **merge** banyak file subtitle, pakai modul **Subtitle Merge**.
- Untuk **burn-in** subtitle ke video, pakai tab **Subtitles** di modul **Video**.
- Untuk **extract** subtitle dari MKV/MP4, pakai modul **Subtitle Extract**.

## Troubleshooting

**ASS output corrupt di player.** Player butuh font yang di-reference di Style. Default Arial harusnya selalu ada. Kalau pakai custom style, cek font availability.

**SRT to VTT punya cue identifier.** VTT support optional identifier sebelum timestamp. Parser kita drop identifier saat output VTT.

**Time shift gagal "negative cue start".** Negatif shift terlalu besar untuk cue paling awal. Kurangi nilai shift.
