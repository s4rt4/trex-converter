#!/usr/bin/env bash
#
# Install a development .desktop file and app-id-named icons into the user's
# ~/.local/share so GNOME Shell can resolve the app's logo and friendly name
# for notifications, the dock, and the window list. The GTK app registers an
# icon search path at runtime, but the Shell (a separate process) only looks
# in the standard XDG icon/desktop locations — hence this install step.
#
# Re-run after changing the icon. Uninstall with: packaging/install-dev.sh --uninstall
set -euo pipefail

APP_ID="io.github.s4rt4.trexconverter"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APPS_DIR="$DATA_HOME/applications"
ICONS_ROOT="$DATA_HOME/icons/hicolor"
DESKTOP_FILE="$APPS_DIR/$APP_ID.desktop"

uninstall() {
    rm -f "$DESKTOP_FILE"
    find "$ICONS_ROOT" -name "$APP_ID.*" -delete 2>/dev/null || true
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
    gtk-update-icon-cache -f -t "$ICONS_ROOT" 2>/dev/null || true
    echo "Uninstalled $APP_ID desktop entry and icons."
}

if [[ "${1:-}" == "--uninstall" ]]; then
    uninstall
    exit 0
fi

# 1. Desktop entry — launch via the repo's venv so PDF engines work, and pin
#    StartupWMClass to the app-id so the Shell matches the running window.
mkdir -p "$APPS_DIR"
PYTHON="$REPO_ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python3)"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=T-Rex Converter
Comment=Convert media, images, documents, and PDFs locally
Exec=env "PYTHONPATH=$REPO_ROOT" "$PYTHON" -m app.gtk_main
Path=$REPO_ROOT
Icon=$APP_ID
Terminal=false
Categories=Utility;
StartupWMClass=$APP_ID
EOF

# 2. Icons — install under the app-id name so Icon=$APP_ID resolves. The
#    scalable SVG already carries the app-id name; the rasters are named
#    t-rex-converter, so copy them to the app-id name at each size.
SRC_ICONS="$REPO_ROOT/assets/icons/hicolor"
install -D -m644 "$SRC_ICONS/scalable/apps/$APP_ID.svg" \
    "$ICONS_ROOT/scalable/apps/$APP_ID.svg"
for size in 16x16 32x32 48x48 64x64 128x128 256x256; do
    src="$SRC_ICONS/$size/apps/t-rex-converter.png"
    [[ -f "$src" ]] && install -D -m644 "$src" \
        "$ICONS_ROOT/$size/apps/$APP_ID.png"
done

# 3. Refresh the Shell's caches.
update-desktop-database "$APPS_DIR" 2>/dev/null || true
gtk-update-icon-cache -f -t "$ICONS_ROOT" 2>/dev/null || true

echo "Installed $DESKTOP_FILE"
echo "Installed icons under $ICONS_ROOT (as $APP_ID.*)"
echo "Notifications and the dock should now show the T-Rex logo and name."
