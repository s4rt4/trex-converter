"""Output-destination row: where converted files are written.

Empty means "same folder as the input file" — the common case — so the
control starts there and only shows an explicit path once the user picks
one.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

_SAME_AS_INPUT = "Same folder as the input file"


class DestinationRow:
    def __init__(
        self,
        *,
        title: str = "Save to",
        initial: Path | None = None,
        on_change: Callable[[Path | None], None] | None = None,
    ) -> None:
        self._dir: Path | None = initial
        self._on_change = on_change

        self.row = Adw.ActionRow(title=title)
        self.row.set_subtitle(str(initial) if initial else _SAME_AS_INPUT)

        button = Gtk.Button(label="Select location")
        button.add_css_class("flat")
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", lambda _b: self._choose())
        self.row.add_suffix(button)
        self.row.set_activatable_widget(button)

    @property
    def directory(self) -> Path | None:
        return self._dir

    def set_directory(self, path: Path | None) -> None:
        self._dir = path
        self.row.set_subtitle(str(path) if path else _SAME_AS_INPUT)
        if self._on_change is not None:
            self._on_change(path)

    def _choose(self) -> None:
        dialog = Gtk.FileDialog(title="Select output folder")
        if self._dir is not None:
            dialog.set_initial_folder(Gio.File.new_for_path(str(self._dir)))
        dialog.select_folder(self._root(), None, self._on_done)

    def _on_done(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            gfile = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        local = gfile.get_path() if gfile else None
        if local:
            self.set_directory(Path(local))

    def _root(self) -> Gtk.Window | None:
        root = self.row.get_root()
        return root if isinstance(root, Gtk.Window) else None
