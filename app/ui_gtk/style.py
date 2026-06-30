"""Load the application CSS into the default display."""

from __future__ import annotations

from pathlib import Path

from gi.repository import Gdk, Gtk

_CSS_PATH = Path(__file__).with_name("style.css")


def load_css() -> None:
    """Register the app stylesheet at application priority.

    Application priority sits below user/theme overrides for most
    properties, which keeps our additions from fighting the system
    theme — exactly what the house style asks for.
    """
    provider = Gtk.CssProvider()
    provider.load_from_path(str(_CSS_PATH))
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
