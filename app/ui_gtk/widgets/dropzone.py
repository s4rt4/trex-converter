"""Single-file drop zone with a rich filled preview (mockup style).

Empty state: a dashed card, click or drop to choose. Filled state: a
thumbnail tile with a format badge, the file name, a metadata line, and
Replace / Remove actions, plus an optional output-size estimate on the
right.

Metadata beyond file size (dimensions, duration) and the size estimate
require backend probing; they are shown only when that data is supplied
via :meth:`set_details` / :meth:`set_estimate`, and hidden otherwise —
never a blank placeholder (house style §7.1).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

from app.ui_gtk.icons import icon_name
from app.ui_gtk.probe import probe_details


def human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class DropZone(Gtk.Box):
    """A droppable card that holds one file.

    ``on_change`` is called with the selected :class:`~pathlib.Path`, or
    ``None`` when cleared.
    """

    def __init__(
        self,
        on_change: Callable[[Path | None], None],
        *,
        icon: str = "image",
        empty_title: str = "Drop a file here or click to choose",
        empty_subtitle: str = "",
        probe: bool = True,
    ) -> None:
        super().__init__()
        self.add_css_class("dropzone")
        self.set_hexpand(True)
        self._on_change = on_change
        self._icon = icon
        self._empty_title = empty_title
        self._empty_subtitle = empty_subtitle
        self._probe = probe
        self._path: Path | None = None
        self._details: str | None = None
        # Bumped on every path change so a slow probe for a replaced file
        # can't overwrite the metadata of the file now shown. Also bumped
        # on destroy, so a probe finishing after teardown (ffprobe can take
        # seconds) can't call into disposed widgets.
        self._probe_generation = 0
        self.connect("destroy", self._on_destroy)

        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", self._on_drop)
        drop.connect("enter", self._on_drag_enter)
        drop.connect("leave", self._on_drag_leave)
        self.add_controller(drop)

        self._click = Gtk.GestureClick()
        self._click.connect("released", self._on_click)
        self.add_controller(self._click)

        self._render_empty()

    @property
    def path(self) -> Path | None:
        return self._path

    def set_path(self, path: Path | None) -> None:
        """Programmatically load a file, as if it had been dropped."""
        self._set_path(path)

    # -- empty state -------------------------------------------------------

    def _render_empty(self) -> None:
        self._clear_children()
        self.add_css_class("empty")
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.update_property([Gtk.AccessibleProperty.LABEL], [self._empty_title])
        self.set_cursor(Gdk.Cursor.new_from_name("pointer", None))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)

        image = Gtk.Image.new_from_icon_name(icon_name(self._icon))
        image.set_pixel_size(44)
        image.add_css_class("dim-label")
        box.append(image)

        title = Gtk.Label(label=self._empty_title)
        title.add_css_class("heading")
        box.append(title)

        if self._empty_subtitle:
            subtitle = Gtk.Label(label=self._empty_subtitle)
            subtitle.add_css_class("caption")
            subtitle.add_css_class("dim-label")
            subtitle.set_wrap(True)
            subtitle.set_justify(Gtk.Justification.CENTER)
            box.append(subtitle)

        self.append(box)

    # -- filled state ------------------------------------------------------

    def _render_filled(self, path: Path) -> None:
        self._clear_children()
        self.remove_css_class("empty")
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_cursor(None)
        self.update_property([Gtk.AccessibleProperty.LABEL], [path.name])

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        row.set_hexpand(True)
        row.append(self._build_thumb(path))
        row.append(self._build_info(path))
        self._estimate_box = self._build_estimate()
        row.append(self._estimate_box)
        self.append(row)

    def _build_thumb(self, path: Path) -> Gtk.Widget:
        overlay = Gtk.Overlay()
        overlay.set_valign(Gtk.Align.CENTER)

        tile = Gtk.Box()
        tile.add_css_class("dz-thumb")
        tile.set_overflow(Gtk.Overflow.HIDDEN)  # clip the picture to rounded corners
        tile.set_halign(Gtk.Align.CENTER)
        tile.set_valign(Gtk.Align.CENTER)
        tile.set_size_request(78, 78)

        texture = self._load_thumbnail(path)
        if texture is not None:
            picture = Gtk.Picture.new_for_paintable(texture)
            picture.set_content_fit(Gtk.ContentFit.COVER)
            picture.set_size_request(78, 78)
            tile.append(picture)
        else:
            image = Gtk.Image.new_from_icon_name(icon_name(self._icon))
            image.set_pixel_size(30)
            image.set_hexpand(True)
            image.set_vexpand(True)
            tile.append(image)
        overlay.set_child(tile)

        badge = Gtk.Label(label=path.suffix.lstrip(".").upper() or "FILE")
        badge.add_css_class("dz-badge")
        badge.set_halign(Gtk.Align.END)
        badge.set_valign(Gtk.Align.END)
        overlay.add_overlay(badge)
        return overlay

    def _load_thumbnail(self, path: Path) -> Gdk.Texture | None:
        """Decode a small thumbnail for raster images; None for others.

        Uses GdkPixbuf's scale-on-load so a huge source image is never
        fully decoded. Formats without a pixbuf loader (some AVIF/HEIC)
        fall back to the type icon.
        """
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(path), 156, 156, True
            )
        except GLib.Error:
            return None
        return Gdk.Texture.new_for_pixbuf(pixbuf)

    def _build_info(self, path: Path) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        box.set_valign(Gtk.Align.CENTER)
        box.set_hexpand(True)

        name = Gtk.Label(label=path.name, xalign=0.0)
        name.add_css_class("heading")
        name.set_ellipsize(Pango.EllipsizeMode.END)
        box.append(name)

        self._meta = Gtk.Label(label=self._meta_text(), xalign=0.0)
        self._meta.add_css_class("caption")
        self._meta.add_css_class("dim-label")
        box.append(self._meta)

        links = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        links.set_margin_top(6)
        replace = self._link_button("replace", "Replace", self._on_replace)
        remove = self._link_button("remove", "Remove", self._on_remove)
        links.append(replace)
        links.append(remove)
        box.append(links)
        return box

    def _build_estimate(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.END)

        caption = Gtk.Label(label="Estimate", xalign=1.0)
        caption.add_css_class("caption")
        caption.add_css_class("dim-label")
        self._estimate_caption = caption

        value = Gtk.Label(label="", xalign=1.0)
        value.add_css_class("title-4")
        value.add_css_class("dz-estimate")
        self._estimate_value = value

        box.append(caption)
        box.append(value)
        box.set_visible(False)  # hidden until an estimate is provided
        return box

    def _link_button(
        self, icon: str, label: str, handler
    ) -> Gtk.Button:
        button = Gtk.Button()
        button.add_css_class("flat")
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        content.append(Gtk.Image.new_from_icon_name(icon_name(icon)))
        content.append(Gtk.Label(label=label))
        button.set_child(content)
        button.connect("clicked", handler)
        return button

    def _meta_text(self) -> str:
        parts: list[str] = []
        if self._path is not None:
            try:
                parts.append(human_size(self._path.stat().st_size))
            except OSError:
                pass
        if self._details:
            parts.insert(0, self._details)
        return " · ".join(parts) if parts else "—"

    # -- public hooks (backend-fed) ---------------------------------------

    def set_details(self, text: str | None) -> None:
        """Set extra metadata (e.g. ``3840 × 2160`` or ``04:12``)."""
        self._details = text
        if self._path is not None and hasattr(self, "_meta"):
            self._meta.set_label(self._meta_text())

    def set_estimate(self, text: str | None) -> None:
        """Show or hide the output-size estimate."""
        if self._path is None or not hasattr(self, "_estimate_box"):
            return
        if text:
            self._estimate_value.set_label(text)
            self._estimate_box.set_visible(True)
        else:
            self._estimate_box.set_visible(False)

    # -- input handling ----------------------------------------------------

    def _set_path(self, path: Path | None) -> None:
        self._path = path
        self._details = None
        self._probe_generation += 1
        if path is None:
            self._render_empty()
        else:
            self._render_filled(path)
            if self._probe:
                self._start_probe(path, self._probe_generation)
        self._on_change(path)

    # -- background probe --------------------------------------------------

    def _start_probe(self, path: Path, generation: int) -> None:
        """Probe the file's dimensions / duration off the UI thread."""
        def worker() -> None:
            details = probe_details(path)
            if details is not None:
                GLib.idle_add(self._apply_probe, generation, details)

        threading.Thread(target=worker, name="dropzone-probe", daemon=True).start()

    def _on_destroy(self, _widget) -> None:
        self._probe_generation += 1

    def _apply_probe(self, generation: int, details: str) -> bool:
        # Discard results for a file that's already been replaced/removed.
        if generation == self._probe_generation and self._path is not None:
            self.set_details(details)
        return False  # one-shot idle callback

    def _on_click(self, _gesture, _n_press, _x, _y) -> None:
        # Only the empty card is click-to-choose; the filled card uses its
        # own Replace / Remove buttons.
        if self._path is None:
            self._open_dialog()

    def _on_replace(self, _button) -> None:
        self._open_dialog()

    def _on_remove(self, _button) -> None:
        self._set_path(None)

    def _on_drag_enter(self, _target, _x, _y) -> Gdk.DragAction:
        self.add_css_class("drag-over")
        return Gdk.DragAction.COPY

    def _on_drag_leave(self, _target) -> None:
        self.remove_css_class("drag-over")

    def _on_drop(self, _target, value, _x, _y) -> bool:
        self.remove_css_class("drag-over")
        files = value.get_files() if hasattr(value, "get_files") else []
        if not files:
            return False
        local = files[0].get_path()
        if not local:
            return False
        self._set_path(Path(local))
        return True

    def _open_dialog(self) -> None:
        dialog = Gtk.FileDialog(title="Choose a file")
        dialog.open(self._root_window(), None, self._on_open_done)

    def _on_open_done(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return  # cancelled or dismissed
        local = gfile.get_path() if gfile else None
        if local:
            self._set_path(Path(local))

    def _root_window(self) -> Gtk.Window | None:
        root = self.get_root()
        return root if isinstance(root, Gtk.Window) else None

    def _clear_children(self) -> None:
        child = self.get_first_child()
        while child is not None:
            self.remove(child)
            child = self.get_first_child()
