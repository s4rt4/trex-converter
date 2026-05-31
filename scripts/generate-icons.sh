#!/bin/sh
set -e

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SRC="$ROOT_DIR/assets/trex-logo.svg"
DEST="$ROOT_DIR/assets/icons/hicolor"

# -background none + -alpha background keep the SVG's transparency; without
# them ImageMagick flattens onto an opaque white canvas (white box behind the
# logo in window/title-bar icons).
for size in 16 32 48 64 128 256; do
    mkdir -p "$DEST/${size}x${size}/apps"
    magick -background none "$SRC" -resize "${size}x${size}" \
        -alpha background "$DEST/${size}x${size}/apps/t-rex-converter.png"
done

mkdir -p "$DEST/scalable/apps"
cp "$SRC" "$DEST/scalable/apps/t-rex-converter.svg"
