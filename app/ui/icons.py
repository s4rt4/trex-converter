from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.ui.theme import BRAND_ACCENT, BRAND_DARK, BRAND_SURFACE
from app.utils.paths import asset_path


ICON_SIZE = QSize(18, 18)
SMALL_ICON_SIZE = QSize(14, 14)
SIDEBAR_ICON_SIZE = QSize(22, 22)


def icon(
    name: str,
    color: str = BRAND_DARK,
    *,
    color_selected: str | None = None,
    color_active: str | None = None,
):
    import qtawesome as qta

    kwargs = {"color": color}
    if color_selected is not None:
        kwargs["color_selected"] = color_selected
    if color_active is not None:
        kwargs["color_active"] = color_active
    return qta.icon(name, **kwargs)


def accent_icon(name: str):
    return icon(name, BRAND_ACCENT)


def surface_icon(name: str):
    return icon(name, BRAND_SURFACE)


def nav_icon(name: str):
    """Sidebar-style icon: surface tint by default, accent when the row is selected."""
    return icon(name, BRAND_SURFACE, color_selected=BRAND_ACCENT)


def app_icon() -> QIcon:
    logo_path = asset_path("trex-logo.svg")
    if logo_path.exists():
        return QIcon(str(logo_path))
    return accent_icon("fa5s.exchange-alt")
