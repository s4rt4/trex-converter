#!/bin/sh
set -e

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SRC="$ROOT_DIR/assets/trex-logo.svg"
DEST="$ROOT_DIR/assets/icons/hicolor"

for size in 16 32 48 64 128 256; do
    mkdir -p "$DEST/${size}x${size}/apps"
    magick "$SRC" -resize "${size}x${size}" "$DEST/${size}x${size}/apps/t-rex-converter.png"
done

mkdir -p "$DEST/scalable/apps"
cp "$SRC" "$DEST/scalable/apps/t-rex-converter.svg"
