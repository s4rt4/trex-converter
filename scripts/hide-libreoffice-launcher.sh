#!/bin/sh
# Hide LibreOffice from the application launcher while keeping it installed
# for headless document conversion (the LibreOffice engine T-Rex Converter
# uses). Useful when you run another office suite (e.g. OnlyOffice) as your
# daily GUI and don't want two office suites cluttering the menu.
#
# It writes user-level NoDisplay overrides into ~/.local/share/applications/.
# Those take precedence over /usr/share/applications/ by XDG desktop-ID rules
# and survive `apt upgrade` (unlike editing the system .desktop files).
#
# Run AFTER installing LibreOffice. Re-run any time; it is idempotent.
# To undo: delete the matching files from ~/.local/share/applications/.
set -e

SYS_DIR=/usr/share/applications
USER_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$USER_DIR"

found=0
for src in "$SYS_DIR"/libreoffice-*.desktop; do
    [ -f "$src" ] || continue
    found=1
    name=$(basename "$src")
    dest="$USER_DIR/$name"
    # Drop any existing NoDisplay line, then force NoDisplay=true right after
    # the [Desktop Entry] header so it lands in the main group (not an action).
    grep -v '^NoDisplay=' "$src" \
        | awk 'BEGIN{d=0}{print}/^\[Desktop Entry\]/&&!d{print "NoDisplay=true";d=1}' \
        > "$dest"
    echo "hidden: $name"
done

if [ "$found" -eq 0 ]; then
    echo "No LibreOffice .desktop entries found in $SYS_DIR." >&2
    echo "Install LibreOffice first, then re-run this script." >&2
    exit 1
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$USER_DIR" 2>/dev/null || true
fi

echo "Done. LibreOffice stays available for headless conversion but is hidden"
echo "from the application launcher. Log out/in if the menu doesn't refresh."
