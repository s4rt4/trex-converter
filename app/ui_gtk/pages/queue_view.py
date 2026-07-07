"""Queue view — live list of conversion tasks.

Replaces the placeholder Queue page. Shows one row per task with its
input → output, engine, status, and a progress bar, plus Cancel / Retry /
Details actions (feature-map §D). Rows are updated in place when the
task set is unchanged (the hot path: progress ticks arrive twice a
second while converting) and only rebuilt when tasks appear or vanish —
a wholesale rebuild re-decoded every thumbnail from disk and recreated
the action buttons under the pointer, losing clicks.
"""

from __future__ import annotations

from pathlib import Path

from app.core.task import Task, TaskStatus
from app.ui_gtk.icons import icon_name

from gi.repository import Adw, Gdk, GdkPixbuf, GLib, Gtk

_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif", "ico"}
_FAMILY_ICON = {
    **{ext: "image" for ext in _IMAGE_EXTS},
    **{ext: "video" for ext in ("mp4", "mkv", "mov", "avi", "webm", "m4v")},
    **{ext: "audio" for ext in ("mp3", "wav", "m4a", "flac", "aac", "opus", "ogg")},
    **{ext: "subtitle" for ext in ("srt", "vtt", "ass")},
    "pdf": "pdf", "svg": "svg",
}

_STATUS_CSS = {
    TaskStatus.PENDING: "status-pending",
    TaskStatus.RUNNING: "status-running",
    TaskStatus.SUCCESS: "status-success",
    TaskStatus.FAILED: "status-failed",
    TaskStatus.CANCELLED: "status-cancelled",
}
_STATUS_LABEL = {
    TaskStatus.PENDING: "Pending",
    TaskStatus.RUNNING: "Running",
    TaskStatus.SUCCESS: "Completed",
    TaskStatus.FAILED: "Failed",
    TaskStatus.CANCELLED: "Cancelled",
}


class _ThumbnailCache:
    """Decoded thumbnails keyed by path; one disk decode per input file."""

    def __init__(self) -> None:
        self._by_path: dict[str, Gdk.Texture | None] = {}

    def get(self, path: Path) -> Gdk.Texture | None:
        key = str(path)
        if key not in self._by_path:
            self._by_path[key] = self._load(path)
        return self._by_path[key]

    @staticmethod
    def _load(path: Path) -> Gdk.Texture | None:
        """A small thumbnail for raster image inputs; None otherwise."""
        if path.suffix.lower().lstrip(".") not in _IMAGE_EXTS:
            return None
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), 72, 72, True)
        except GLib.Error:
            return None
        return Gdk.Texture.new_for_pixbuf(pixbuf)


class _TaskRow(Gtk.ListBoxRow):
    """One queue entry; ``update()`` mutates it in place on progress ticks."""

    def __init__(self, view: "QueueView", task: Task) -> None:
        super().__init__()
        self.set_activatable(False)
        self._view = view
        self.task = task
        self._shown_status: TaskStatus | None = None
        self._shown_retry: bool | None = None

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)

        box.append(self._build_thumb(task))

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info.set_hexpand(True)
        info.set_valign(Gtk.Align.CENTER)

        self._title = Gtk.Label(
            label=f"{task.input_path.name}  →  {task.output_path.name}", xalign=0.0
        )
        self._title.add_css_class("heading")
        self._title.set_ellipsize(3)  # Pango.EllipsizeMode.END
        info.append(self._title)

        self._meta = Gtk.Label(xalign=0.0)
        self._meta.add_css_class("caption")
        self._meta.add_css_class("dim-label")
        self._meta.set_ellipsize(3)
        info.append(self._meta)

        self._bar = Gtk.ProgressBar()
        self._bar.add_css_class("queue-progress")
        info.append(self._bar)

        box.append(info)

        self._pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._pill.set_valign(Gtk.Align.CENTER)
        self._pill.add_css_class("status-pill")
        self._spinner = Gtk.Spinner()
        self._pill.append(self._spinner)
        self._pill_label = Gtk.Label()
        self._pill_label.add_css_class("caption-heading")
        self._pill.append(self._pill_label)
        box.append(self._pill)

        self._actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._actions.set_valign(Gtk.Align.CENTER)
        box.append(self._actions)

        self.set_child(box)
        self.update(task)

    def _build_thumb(self, task: Task) -> Gtk.Widget:
        tile = Gtk.Box()
        tile.add_css_class("queue-thumb")
        tile.set_overflow(Gtk.Overflow.HIDDEN)
        tile.set_size_request(36, 36)
        tile.set_valign(Gtk.Align.CENTER)
        tile.set_halign(Gtk.Align.CENTER)

        texture = self._view.thumbnails.get(task.input_path)
        if texture is not None:
            picture = Gtk.Picture.new_for_paintable(texture)
            picture.set_content_fit(Gtk.ContentFit.COVER)
            picture.set_size_request(36, 36)
            tile.append(picture)
        else:
            family = _FAMILY_ICON.get(task.format_in.lower(), "document")
            image = Gtk.Image.new_from_icon_name(icon_name(family))
            image.set_pixel_size(18)
            image.set_hexpand(True)
            image.set_vexpand(True)
            tile.append(image)
        return tile

    def update(self, task: Task) -> None:
        self.task = task
        running = task.status == TaskStatus.RUNNING

        self._meta.set_label(self._meta_text(task))
        self._bar.set_visible(running)
        if running:
            self._bar.set_fraction(task.progress)

        if task.status != self._shown_status:
            if self._shown_status is not None:
                self._pill.remove_css_class(
                    _STATUS_CSS.get(self._shown_status, "status-pending")
                )
            self._pill.add_css_class(_STATUS_CSS.get(task.status, "status-pending"))
            self._pill_label.set_label(
                _STATUS_LABEL.get(task.status, str(task.status))
            )
            self._spinner.set_visible(running)
            self._spinner.set_spinning(running)

        # Rebuild the buttons only when the applicable set changes, so a
        # click can't land on a widget that was just destroyed underneath.
        retry = task.can_retry()
        if task.status != self._shown_status or retry != self._shown_retry:
            child = self._actions.get_first_child()
            while child is not None:
                self._actions.remove(child)
                child = self._actions.get_first_child()
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                self._actions.append(
                    self._button("Cancel", self._view._on_cancel, destructive=True)
                )
            if retry:
                self._actions.append(self._button("Retry", self._view._on_retry))
            self._actions.append(self._button("Details", self._view._on_details))

        self._shown_status = task.status
        self._shown_retry = retry

    @staticmethod
    def _meta_text(task: Task) -> str:
        parts = [task.engine, _STATUS_LABEL.get(task.status, str(task.status))]
        if task.status == TaskStatus.RUNNING and task.progress > 0:
            parts.append(f"{int(task.progress * 100)}%")
        if task.status == TaskStatus.FAILED and task.error:
            parts.append(task.error)
        return " · ".join(parts)

    def _button(self, label, handler, *, destructive=False) -> Gtk.Button:
        button = Gtk.Button(label=label)
        button.add_css_class("flat")
        if destructive:
            button.add_css_class("destructive-action")
        button.set_valign(Gtk.Align.CENTER)
        # self.task, not a bound task: the row outlives many task snapshots.
        button.connect("clicked", lambda _b: handler(self.task))
        return button


class QueueView:
    def __init__(self, window) -> None:
        self._window = window
        self.thumbnails = _ThumbnailCache()
        self._rows: dict[str, _TaskRow] = {}

        self._empty = Adw.StatusPage(
            title="Queue is empty",
            description="Converted files will appear here once you start a task.",
            icon_name=icon_name("queue"),
        )

        self._list = Gtk.ListBox()
        self._list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list.add_css_class("boxed-list")
        self._list.set_valign(Gtk.Align.START)
        clamp = Adw.Clamp(maximum_size=900, child=self._list)
        clamp.set_margin_top(18)
        clamp.set_margin_bottom(18)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        self._scroller = Gtk.ScrolledWindow()
        self._scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroller.set_child(clamp)

        self.widget = Gtk.Stack()
        self.widget.add_named(self._empty, "empty")
        self.widget.add_named(self._scroller, "list")
        self.widget.set_visible_child_name("empty")

    # -- updates -----------------------------------------------------------

    def set_tasks(self, tasks: list[Task]) -> None:
        if not tasks:
            self._clear()
            self.widget.set_visible_child_name("empty")
            return
        self.widget.set_visible_child_name("list")

        ordered = list(reversed(tasks))  # newest first
        if [t.id for t in ordered] == list(self._rows):
            # Same task set: the hot path — update rows in place.
            for task in ordered:
                self._rows[task.id].update(task)
            return

        # Task set changed (add/remove/reorder): rebuild the list, reusing
        # nothing but the thumbnail cache — this is the rare path.
        self._clear()
        for task in ordered:
            row = _TaskRow(self, task)
            self._rows[task.id] = row
            self._list.append(row)

    def _clear(self) -> None:
        self._rows.clear()
        child = self._list.get_first_child()
        while child is not None:
            self._list.remove(child)
            child = self._list.get_first_child()

    # -- actions -----------------------------------------------------------

    def _on_cancel(self, task: Task) -> None:
        if self._window.queue is not None:
            self._window.queue.cancel(task.id)

    def _on_retry(self, task: Task) -> None:
        if self._window.queue is not None:
            self._window.queue.retry(task.id)

    def _on_details(self, task: Task) -> None:
        TaskDetailsDialog(task).present(self._window)


class TaskDetailsDialog(Adw.Dialog):
    def __init__(self, task: Task) -> None:
        super().__init__()
        self.set_title("Task details")
        self.set_content_width(560)
        self.set_content_height(560)

        page = Adw.PreferencesPage()
        fields = Adw.PreferencesGroup()
        for title, value in (
            ("Input", str(task.input_path)),
            ("Output", str(task.output_path)),
            ("Engine", task.engine),
            ("Format", f"{task.format_in} → {task.format_out}"),
            ("Status", _STATUS_LABEL.get(task.status, str(task.status))),
            ("Progress", f"{int(task.progress * 100)}%"),
        ):
            row = Adw.ActionRow(title=title)
            # File paths are user data — never Pango markup ('&' etc.).
            # Disable markup *before* setting the subtitle: the setter
            # parses immediately and a raw '&' fails (blank row + warning).
            row.set_use_markup(False)
            row.set_subtitle(value or "—")
            row.set_subtitle_selectable(True)
            row.set_activatable(False)
            fields.add(row)
        if task.error:
            error_row = Adw.ActionRow(title="Error")
            # Engine errors routinely contain '<', '>', '&' (ffmpeg filters,
            # command lines) — parsed as markup the row would go blank.
            error_row.set_use_markup(False)
            error_row.set_subtitle(task.error)
            error_row.set_subtitle_selectable(True)
            error_row.add_css_class("error")
            fields.add(error_row)
        page.add(fields)

        if task.log:
            log_group = Adw.PreferencesGroup(title="Log")
            text = Gtk.TextView(editable=False, monospace=True, cursor_visible=False)
            text.get_buffer().set_text("\n".join(task.log))
            text.set_left_margin(8)
            text.set_right_margin(8)
            scroller = Gtk.ScrolledWindow()
            scroller.set_min_content_height(160)
            scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scroller.set_child(text)
            scroller.add_css_class("card")
            log_group.add(scroller)
            page.add(log_group)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(page)
        self.set_child(toolbar)
