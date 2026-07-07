"""Adw.Application subclass — the GTK4 entry object."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from app.ui_gtk import APP_ID  # noqa: E402
from app.ui_gtk.style import load_css  # noqa: E402
from app.ui_gtk.window import TrexWindow  # noqa: E402
from app.utils.paths import asset_path  # noqa: E402


class TrexApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self._window: TrexWindow | None = None

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        from app.core.settings import migrate_legacy_config

        migrate_legacy_config()
        self._register_icons()
        load_css()
        self._install_actions()

    def _register_icons(self) -> None:
        """Make the bundled app icon resolvable by name.

        Adds ``assets/icons`` to the icon theme search path so the brand
        logo (``t-rex-converter`` / the app id) renders in the sidebar,
        the About dialog, and the window/taskbar.
        """
        display = Gdk.Display.get_default()
        if display is not None:
            theme = Gtk.IconTheme.get_for_display(display)
            theme.add_search_path(str(asset_path("icons")))

    def do_activate(self) -> None:
        if self._window is None:
            self._window = TrexWindow(application=self)
            self._attach_queue()
        self._window.present()

    def _attach_queue(self) -> None:
        from app.ui_gtk.backend import QueueController

        try:
            self._queue = QueueController(on_change=self._window.on_tasks_changed)
        except RuntimeError as exc:
            # Corrupt task DB / bad settings: keep the window usable and
            # explain, instead of dying (or, worse, hanging) before it maps.
            self._queue = None
            cause = exc.__cause__ or exc
            dialog = Adw.AlertDialog(
                heading="Conversion queue unavailable",
                body=(
                    "The background conversion queue failed to start, so "
                    "converting is disabled.\n\nDetails: "
                    f"{cause.__class__.__name__}: {cause}"
                ),
            )
            dialog.add_response("close", "Close")
            dialog.present(self._window)
            return
        self._window.attach_queue(self._queue)

    def do_shutdown(self) -> None:
        queue = getattr(self, "_queue", None)
        if queue is not None:
            queue.shutdown()
        Adw.Application.do_shutdown(self)

    def _install_actions(self) -> None:
        for name, handler in (
            ("quit", self._on_quit),
            ("about", self._on_about),
            ("settings", self._on_settings),
        ):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def _on_quit(self, _action, _param) -> None:
        self.quit()

    def _on_settings(self, _action, _param) -> None:
        if self._window is not None:
            from app.ui_gtk.pages.settings_dialog import present_settings

            present_settings(self._window)

    def _on_about(self, _action, _param) -> None:
        from app import __version__

        about = Adw.AboutDialog(
            application_name="T-Rex Converter",
            application_icon=APP_ID,
            version=__version__,
            developer_name="s4rt4",
            comments="Convert images, video, audio, documents and more — "
            "a single front-end over best-in-class command-line engines.",
            website="https://github.com/s4rt4/trex-converter",
            issue_url="https://github.com/s4rt4/trex-converter/issues",
            license_type=Gtk.License.GPL_3_0,
        )
        about.set_copyright("© s4rt4")
        # The conversion engines this app drives (feature-map §D).
        about.add_acknowledgement_section(
            "Powered by",
            (
                "FFmpeg — audio & video",
                "ImageMagick — images",
                "LibreOffice — documents & slides",
                "Pandoc — ebooks & markup",
                "Inkscape — SVG & vector",
                "Tesseract — OCR",
                "PyMuPDF & qpdf — PDF tools",
                "ExifTool — metadata",
                "qrencode & zbar — QR / barcode",
            ),
        )
        about.present(self._window)
