"""Settings dialog — GTK4 port of the old Qt settings page.

A modal :class:`Adw.Dialog` with a header bar (Restore defaults · Save) over
a clamped preferences page. It reads and writes the shared on-disk settings
(:mod:`app.core.settings`) — the same store the conversion pages seed their
defaults from. Concurrency changes take effect on next launch, matching the
old behaviour (feature-map §D).
"""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

from app import __version__
from app.core.settings import (
    CONFIG_DIR,
    SETTINGS_PATH,
    Settings,
    get_settings,
    set_settings,
)
from app.ui_gtk.widgets.rows import ChoiceRow, spin_row

OCR_LANGUAGES = (
    ("English (eng)", "eng"),
    ("Indonesian (ind)", "ind"),
    ("English + Indonesian", "eng+ind"),
    ("Custom…", "__custom__"),
)
VIDEO_PRESETS = tuple(
    (p, p) for p in (
        "ultrafast", "superfast", "veryfast", "faster", "fast",
        "medium", "slow", "slower", "veryslow",
    )
)


class SettingsDialog(Adw.Dialog):
    def __init__(self, window) -> None:
        super().__init__()
        self._window = window
        self.set_title("Settings")
        self.set_content_width(560)
        self.set_content_height(720)

        header = Adw.HeaderBar()
        restore = Gtk.Button(label="Restore defaults")
        restore.connect("clicked", lambda _b: self._populate(Settings()))
        header.pack_start(restore)
        save = Gtk.Button(label="Save")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda _b: self._save())
        header.pack_end(save)

        page = Adw.PreferencesPage()
        page.add(self._build_general())
        page.add(self._build_defaults())
        page.add(self._build_system())

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(page)
        self.set_child(toolbar)

        self._populate(get_settings())

    # -- groups ------------------------------------------------------------

    def _build_general(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="General")

        self.output_dir = Adw.EntryRow(title="Default output folder")
        browse = Gtk.Button(label="Browse")
        browse.add_css_class("flat")
        browse.set_valign(Gtk.Align.CENTER)
        browse.connect("clicked", lambda _b: self._browse_output_dir())
        self.output_dir.add_suffix(browse)
        group.add(self.output_dir)

        self.concurrency = spin_row("Max concurrent tasks", 1, 16, 2)
        self.concurrency.set_subtitle("Applies on next launch")
        group.add(self.concurrency)
        return group

    def _build_defaults(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(
            title="Conversion defaults",
            description="Seed each conversion page; the per-page panel still wins.",
        )
        self.image_quality = spin_row("Image quality", 1, 100, 82)
        self.pdf_dpi = spin_row("PDF render DPI", 72, 600, 200)
        self.ocr_language = ChoiceRow("OCR language", OCR_LANGUAGES, "eng")
        self.ocr_custom = Adw.EntryRow(title="OCR custom code — e.g. eng+jpn")
        self.video_crf = spin_row("Video CRF (0 = off)", 0, 51, 0)
        self.video_preset = ChoiceRow("Video x264 preset", VIDEO_PRESETS, "medium")
        self.audio_bitrate = Adw.EntryRow(title="Audio bitrate — e.g. 192k")
        for row in (
            self.image_quality, self.pdf_dpi, self.ocr_language.row,
            self.ocr_custom, self.video_crf, self.video_preset.row,
            self.audio_bitrate,
        ):
            group.add(row)
        self.ocr_language.row.connect("notify::selected", lambda *_: self._sync())
        return group

    def _build_system(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="System and maintenance")

        version = Adw.ActionRow(title="Version", subtitle=__version__)
        version.set_activatable(False)
        group.add(version)

        config_row = Adw.ActionRow(title="Config folder", subtitle=str(CONFIG_DIR))
        config_row.set_subtitle_selectable(True)
        open_config = Gtk.Button(label="Open")
        open_config.add_css_class("flat")
        open_config.set_valign(Gtk.Align.CENTER)
        open_config.connect("clicked", lambda _b: self._open_folder(CONFIG_DIR, create=True))
        config_row.add_suffix(open_config)
        group.add(config_row)

        settings_row = Adw.ActionRow(title="Settings file", subtitle=str(SETTINGS_PATH))
        settings_row.set_subtitle_selectable(True)
        group.add(settings_row)

        output_row = Adw.ActionRow(
            title="Output folder", subtitle="Open the configured output folder"
        )
        open_output = Gtk.Button(label="Open")
        open_output.add_css_class("flat")
        open_output.set_valign(Gtk.Align.CENTER)
        open_output.connect("clicked", lambda _b: self._open_output_dir())
        output_row.add_suffix(open_output)
        group.add(output_row)
        return group

    # -- behaviour ---------------------------------------------------------

    def _sync(self) -> None:
        self.ocr_custom.set_visible(self.ocr_language.get_value() == "__custom__")

    def _populate(self, settings: Settings) -> None:
        self.output_dir.set_text(settings.output_dir)
        self.concurrency.set_value(settings.max_concurrency)
        self.image_quality.set_value(settings.default_image_quality)
        self.pdf_dpi.set_value(settings.default_pdf_dpi)
        if settings.default_ocr_language in {v for _, v in OCR_LANGUAGES}:
            self.ocr_language.set_value(settings.default_ocr_language)
            self.ocr_custom.set_text("")
        else:
            self.ocr_language.set_value("__custom__")
            self.ocr_custom.set_text(settings.default_ocr_language)
        self.video_crf.set_value(settings.default_video_crf)
        self.video_preset.set_value(settings.default_video_preset)
        self.audio_bitrate.set_text(settings.default_audio_bitrate)
        self._sync()

    def _save(self) -> None:
        if self.ocr_language.get_value() == "__custom__":
            ocr_value = self.ocr_custom.get_text().strip()
            if not ocr_value:
                self._window.show_toast("Custom OCR language code is empty.")
                return
        else:
            ocr_value = str(self.ocr_language.get_value())

        # Pages silently fall back to "same folder as input" when this dir
        # doesn't exist, so create it now (and fail loudly if we can't)
        # rather than letting a typo or a not-yet-created folder be a no-op.
        output_dir = self.output_dir.get_text().strip()
        if output_dir:
            resolved = Path(output_dir).expanduser()
            try:
                resolved.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                self._window.show_toast(
                    f"Default output folder is not usable: {error}"
                )
                return
            output_dir = str(resolved)

        new_settings = Settings(
            output_dir=output_dir,
            max_concurrency=int(self.concurrency.get_value()),
            default_image_quality=int(self.image_quality.get_value()),
            default_pdf_dpi=int(self.pdf_dpi.get_value()),
            default_ocr_language=ocr_value,
            default_video_crf=int(self.video_crf.get_value()),
            default_video_preset=str(self.video_preset.get_value()),
            default_audio_bitrate=self.audio_bitrate.get_text().strip() or "192k",
            # Preserve the theme choice (owned by the header toggle, not this
            # dialog) so saving general settings doesn't reset it.
            color_scheme=get_settings().color_scheme,
        )
        try:
            set_settings(new_settings)
        except OSError as error:
            self._window.show_toast(f"Could not save settings: {error}")
            return
        self._window.show_toast("Settings saved. Concurrency applies on next launch.")
        self.close()

    # -- folder helpers ----------------------------------------------------

    def _browse_output_dir(self) -> None:
        dialog = Gtk.FileDialog(title="Select default output folder")
        current = self.output_dir.get_text().strip()
        if current and Path(current).is_dir():
            dialog.set_initial_folder(Gio.File.new_for_path(current))
        dialog.select_folder(self._root(), None, self._on_browse_done)

    def _on_browse_done(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            gfile = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if gfile and gfile.get_path():
            self.output_dir.set_text(gfile.get_path())

    def _open_output_dir(self) -> None:
        target = self.output_dir.get_text().strip() or str(Path.home())
        self._open_folder(Path(target))

    def _open_folder(self, path: Path, *, create: bool = False) -> None:
        if create:
            path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            self._window.show_toast(f"Folder does not exist yet: {path}")
            return
        launcher = Gtk.FileLauncher.new(Gio.File.new_for_path(str(path)))
        launcher.launch(self._root(), None, None)

    def _root(self) -> Gtk.Window | None:
        return self._window if isinstance(self._window, Gtk.Window) else None


def present_settings(window) -> None:
    SettingsDialog(window).present(window)
