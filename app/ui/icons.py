from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.ui.theme import BRAND_ACCENT, BRAND_DARK, BRAND_SURFACE
from app.utils.paths import asset_path


ICON_SIZE = QSize(18, 18)
SMALL_ICON_SIZE = QSize(14, 14)


def icon(name: str, color: str = BRAND_DARK):
    import qtawesome as qta

    return qta.icon(name, color=color)


def accent_icon(name: str):
    return icon(name, BRAND_ACCENT)


def surface_icon(name: str):
    return icon(name, BRAND_SURFACE)


def app_icon() -> QIcon:
    logo_path = asset_path("trex-logo.svg")
    if logo_path.exists():
        return QIcon(str(logo_path))
    return accent_icon("fa5s.exchange-alt")
