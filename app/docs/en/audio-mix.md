# Audio Mix

Mix several audio tracks into one file via **FFmpeg** amix filter.

## Description

The **Audio Mix** module takes multi-input audio and outputs one file. The engine emits an FFmpeg `amix` filter: `amix=inputs=N:duration=<longest|shortest|first>:normalize=<0|1>`. Input/output formats match the standalone **Audio** module.

Options panel: **Duration** (longest, shortest, first) and **Normalize sum to 1/N** (default on).

## How to use

1. Click **Add files** or drop several audio files.
2. Pick an **Output format**.
3. Adjust options:
   - **Duration**: longest (output as long as the longest clip), shortest (output as long as the shortest clip), first (output as long as the first clip).
   - **Normalize**: divide the sum by N to avoid clipping.
4. Click **Select Location**.
5. Click **Add to Queue**.

## Tips & Trick

- **Normalize on** (default) is great for mixing vocals plus music without clipping. **Off** when every track is pre-leveled and you want a direct sum.
- **Duration first** is great for overlaying a narrator track over background music (output length matches narrator).
- For mixing with different per-track volumes, pre-process each track via the **Audio** module Effects tab Gain first.
- Format mismatches (different bitrate, sample rate) are auto-normalized by amix.

## Troubleshooting

**Output volume is low.** Normalize on divides by N. If you just need a sum, set Normalize off (risk of clipping).

**Only one track is audible.** File order might be wrong, or one of the files is corrupt. Test each file individually in a player first.

**Mix is asymmetric (left/right differ).** Sources have different channel layouts (mono vs stereo). Force convert to stereo first via the **Audio** module's Output tab Channels.
