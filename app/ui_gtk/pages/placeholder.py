"""Placeholder content for destinations that are not built yet."""

from __future__ import annotations

from gi.repository import Adw

from app.ui_gtk.icons import icon_name
from app.ui_gtk.navigation import NavItem


def make_placeholder(item: NavItem) -> Adw.StatusPage:
    """A friendly empty state standing in for an unbuilt converter page."""
    page = Adw.StatusPage(
        title=item.title,
        description="This converter is not available in the new interface yet.",
        icon_name=icon_name(item.icon),
    )
    page.add_css_class("compact")
    return page
