# QR / Barcode

Generate QR codes from text and decode QR/barcodes from images.

## Description

The **QR / Barcode** module wraps two binaries:

- **Generate**: `qrencode` for text to png or svg with size, margin, error correction level.
- **Decode**: `zbarimg` for images (png, jpg, jpeg, bmp, tif, tiff, gif, webp) to txt. Decodes many 1D and 2D barcode types, not just QR.

## How to use

### Generate (txt to png/svg)

1. Click **Browse** to pick a `.txt` file with the content to encode.
2. Pick an **Output format** of png or svg.
3. Adjust options:
   - **Module size** (px per dot, 1 to 50, default 8).
   - **Margin** (dots, 0 to 32, default 2).
   - **Error correction**: L (~7%), M (~15%, default), Q (~25%), H (~30%).
4. Click **Add to Queue**.

### Decode (image to txt)

1. Click **Browse** to pick an image with a QR or barcode.
2. Pick an **Output format** of txt.
3. Click **Add to Queue**. Output txt contains the first decoded payload.

## Tips & Trick

- **Error correction H** when the QR will be printed and likely to get dirty or damaged. Larger but more reliable.
- **Module size 8** is standard for on-screen view, 12 to 16 for A4 print.
- **Margin 4** is the minimum for QR scanners to work reliably (quiet zone).
- **zbarimg** decodes many formats: QR, EAN-13, UPC-A, Code 128, Code 39, ITF, etc. Not just QR.
- To decode multiple barcodes in one image, you need a more advanced tool (zbarimg returns only the first).

## Troubleshooting

**Generate "qr_size must be between 1 and 50".** Module size is out of range. Set 1 to 50.

**Decode "no barcodes" error.** Image quality is low, contrast is poor, or there really is no barcode. Pre-process: use the **Image** Color tab for grayscale plus contrast boost.

**Decoded text looks like mojibake.** The QR uses a non-UTF-8 encoding. zbarimg `--raw` outputs as-is, could be shift-jis (Japanese) or another encoding.
