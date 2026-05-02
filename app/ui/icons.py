from __future__ import annotations

from PySide6.QtCore import QSize

from app.ui.theme import BRAND_ACCENT, BRAND_DARK, BRAND_SURFACE


ICON_SIZE = QSize(18, 18)
SMALL_ICON_SIZE = QSize(14, 14)


def icon(name: str, color: str = BRAND_DARK):
    import qtawesome as qta

    return qta.icon(name, color=color)


def accent_icon(name: str):
    return icon(name, BRAND_ACCENT)


def surface_icon(name: str):
    return icon(name, BRAND_SURFACE)
