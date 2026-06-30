"""Multi-file input list: add, remove, and (optionally) reorder.

Used by the multi-input converters (Video concat, PDF/Document/Subtitle
merge, Audio mix, Image montage, PDF compare) where several files feed a
single output. The first file is the *primary* input; the rest are passed
as ``extra_inputs`` (feature-map §C, "Input multi").

The list lives in an :class:`AdwPreferencesGroup` so it matches the other
form groups: an "Add files" action in the header, one row per file, and a
quiet empty state. Order is the input order; for operations where order
matters (concat, merge) each row can be moved up or down.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from gi.repository import Adw, Gdk, GLib, Gtk

from app.ui_gtk.icons import icon_name
from app.ui_gtk.widgets.dropzone import human_size


class FileListInput:
    """Holds a preferences ``group`` plus the ordered list of chosen paths.

    ``on_change`` is called (no args) whenever the set or order of files
    changes. Set ``reorderable=True`` to show per-row move up/down.
    """

    def __init__(
        self,
        on_change: Callable[[], None] | None = None,
        *,
        title: str = "Files",
        reorderable: bool = False,
        empty_subtitle: str = "Add or drop files to convert",
    ) -> None:
        self._on_change = on_change
        self._reorderable = reorderable
        self._empty_subtitle = empty_subtitle
        self._paths: list[Path] = []
        self._rows: list[Gtk.Widget] = []

        self.group = Adw.PreferencesGroup(title=title)

        suffix = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._clear_button = self._flat("Clear", self._on_clear)
        self._clear_button.add_css_class("destructive-action")
        suffix.append(self._clear_button)
        suffix.append(self._build_add_button())
        self.group.set_header_suffix(suffix)

        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", self._on_drop)
        self.group.add_controller(drop)

        self._rebuild()

    # -- public -----------------------------------------------------------

    @property
    def paths(self) -> list[Path]:
        return list(self._paths)

    @property
    def primary(self) -> Path | None:
        return self._paths[0] if self._paths else None

    @property
    def extra_inputs(self) -> list[Path]:
        return self._paths[1:]

    def set_paths(self, paths: Iterable[Path]) -> None:
        self._paths = [Path(p) for p in paths]
        self._changed()

    # -- buttons ----------------------------------------------------------

    def _build_add_button(self) -> Gtk.Button:
        button = Gtk.Button()
        button.add_css_class("flat")
        button.set_valign(Gtk.Align.CENTER)
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        content.append(Gtk.Image.new_from_icon_name(icon_name("add")))
        content.append(Gtk.Label(label="Add files"))
        button.set_child(content)
        button.connect("clicked", self._on_add)
        return button

    def _flat(self, label: str, handler) -> Gtk.Button:
        button = Gtk.Button(label=label)
        button.add_css_class("flat")
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", handler)
        return button

    # -- rows -------------------------------------------------------------

    def _rebuild(self) -> None:
        for row in self._rows:
            self.group.remove(row)
        self._rows = []

        if not self._paths:
            empty = Adw.ActionRow(title="No files yet")
            empty.set_subtitle(self._empty_subtitle)
            empty.add_prefix(Gtk.Image.new_from_icon_name(icon_name("folder")))
            empty.set_sensitive(False)
            self._add_row(empty)
        else:
            last = len(self._paths) - 1
            for index, path in enumerate(self._paths):
                self._add_row(self._make_file_row(index, path, last))

        self._clear_button.set_sensitive(bool(self._paths))

    def _add_row(self, row: Gtk.Widget) -> None:
        self.group.add(row)
        self._rows.append(row)

    def _make_file_row(self, index: int, path: Path, last: int) -> Adw.ActionRow:
        row = Adw.ActionRow()
        row.set_use_markup(False)  # file names may contain '&'
        row.set_title(path.name)
        row.set_subtitle(self._subtitle(path))

        number = Gtk.Label(label=str(index + 1))
        number.add_css_class("dim-label")
        number.add_css_class("numeric")
        number.set_valign(Gtk.Align.CENTER)
        row.add_prefix(number)

        if self._reorderable:
            up = self._icon_button(
                "move-up", "Move up", lambda _b, i=index: self._move(i, -1)
            )
            up.set_sensitive(index > 0)
            down = self._icon_button(
                "move-down", "Move down", lambda _b, i=index: self._move(i, 1)
            )
            down.set_sensitive(index < last)
            row.add_suffix(up)
            row.add_suffix(down)

        row.add_suffix(
            self._icon_button(
                "remove", "Remove", lambda _b, i=index: self._remove(i)
            )
        )
        return row

    def _icon_button(self, icon: str, tooltip: str, handler) -> Gtk.Button:
        button = Gtk.Button(icon_name=icon_name(icon))
        button.add_css_class("flat")
        button.set_valign(Gtk.Align.CENTER)
        button.set_tooltip_text(tooltip)
        button.connect("clicked", handler)
        return button

    def _subtitle(self, path: Path) -> str:
        try:
            return human_size(path.stat().st_size)
        except OSError:
            return str(path.parent)

    # -- mutation ---------------------------------------------------------

    def _append_paths(self, new_paths: Iterable[Path]) -> None:
        existing = {str(p) for p in self._paths}
        added = False
        for path in new_paths:
            key = str(path)
            if key not in existing:
                self._paths.append(path)
                existing.add(key)
                added = True
        if added:
            self._changed()

    def _move(self, index: int, delta: int) -> None:
        target = index + delta
        if 0 <= target < len(self._paths):
            self._paths[index], self._paths[target] = (
                self._paths[target],
                self._paths[index],
            )
            self._changed()

    def _remove(self, index: int) -> None:
        if 0 <= index < len(self._paths):
            del self._paths[index]
            self._changed()

    def _on_clear(self, _button) -> None:
        if self._paths:
            self._paths = []
            self._changed()

    def _changed(self) -> None:
        self._rebuild()
        if self._on_change is not None:
            self._on_change()

    # -- file dialog ------------------------------------------------------

    def _on_add(self, _button) -> None:
        dialog = Gtk.FileDialog(title="Add files")
        dialog.open_multiple(self._root(), None, self._on_add_done)

    def _on_add_done(self, dialog: Gtk.FileDialog, result) -> None:
        try:
            files = dialog.open_multiple_finish(result)
        except GLib.Error:
            return  # cancelled
        paths = []
        for i in range(files.get_n_items()):
            gfile = files.get_item(i)
            local = gfile.get_path() if gfile else None
            if local:
                paths.append(Path(local))
        self._append_paths(paths)

    def _on_drop(self, _target, value, _x, _y) -> bool:
        files = value.get_files() if hasattr(value, "get_files") else []
        paths = [Path(f.get_path()) for f in files if f.get_path()]
        if not paths:
            return False
        self._append_paths(paths)
        return True

    def _root(self) -> Gtk.Window | None:
        root = self.group.get_root()
        return root if isinstance(root, Gtk.Window) else None
