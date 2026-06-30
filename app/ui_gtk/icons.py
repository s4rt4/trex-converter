"""Icon indirection layer.

The house style locks the final icon pack to **Lucide** (recolorable
symbolic, bundled via GResource as ``lucide-<name>-symbolic``). That set
is not wired up yet, so every UI call goes through :func:`icon_name`,
which maps a stable *logical* name to whatever concrete icon name is
available today. When the Lucide GResource lands, only this module
changes — call sites keep using the logical names.
"""

from __future__ import annotations

# Logical name -> concrete icon name currently shipped with the desktop
# icon theme. Logical names mirror Lucide's vocabulary so the eventual
# swap to ``lucide-<name>-symbolic`` is a mechanical edit here.
_FALLBACK: dict[str, str] = {
    "image": "image-x-generic-symbolic",
    "video": "video-x-generic-symbolic",
    "audio": "audio-x-generic-symbolic",
    "document": "x-office-document-symbolic",
    "pdf": "x-office-document-symbolic",
    "subtitle": "media-view-subtitles-symbolic",
    "archive": "package-x-generic-symbolic",
    "utility": "applications-utilities-symbolic",
    "dashboard": "view-grid-symbolic",
    "settings": "preferences-system-symbolic",
    "about": "help-about-symbolic",
    "menu": "open-menu-symbolic",
    "queue": "view-list-symbolic",
    "convert": "media-playback-start-symbolic",
    "help": "help-browser-symbolic",
    "sun": "weather-clear-symbolic",
    "moon": "weather-clear-night-symbolic",
    "folder": "folder-symbolic",
    "remove": "user-trash-symbolic",
    "replace": "document-open-symbolic",
    "add": "list-add-symbolic",
    "move-up": "go-up-symbolic",
    "move-down": "go-down-symbolic",
    # operation-row icons (Image/Video checklists)
    "rotate": "object-rotate-right-symbolic",
    "resize": "zoom-fit-best-symbolic",
    "color": "applications-graphics-symbolic",
    "filter": "view-more-symbolic",
    "border": "view-grid-symbolic",
    "watermark": "emblem-photos-symbolic",
    "trim": "edit-cut-symbolic",
    "compress": "drive-harddisk-symbolic",
    "effects": "starred-symbolic",
    "animation": "media-playback-start-symbolic",
    "thumbnails": "view-grid-symbolic",
    # Dashboard stat-card glyphs.
    "stat-total": "view-list-symbolic",
    "stat-running": "media-playback-start-symbolic",
    "stat-success": "emblem-ok-symbolic",
    "stat-failed": "dialog-warning-symbolic",
}

# Lucide is now bundled (assets/icons/hicolor/scalable/actions/
# lucide-<name>-symbolic.svg), converted stroke->fill so GTK recolors it.
_USE_LUCIDE = True


def icon_name(logical: str) -> str:
    """Resolve a logical icon name to a concrete, themeable icon name."""
    if _USE_LUCIDE:
        return f"lucide-{logical}-symbolic"
    return _FALLBACK.get(logical, "image-missing-symbolic")
