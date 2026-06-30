"""Queue view — live list of conversion tasks.

Replaces the placeholder Queue page. Shows one row per task with its
input → output, engine, status, and a progress bar, plus Cancel / Retry /
Details actions (feature-map §D). Rebuilt wholesale whenever the
:class:`~app.ui_gtk.backend.QueueController` reports a change — task
counts are small and rebuilding keeps the state trivially correct.
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


def _load_thumbnail(path: Path) -> Gdk.Texture | None:
    """A small thumbnail for raster image inputs; None for everything else."""
    if path.suffix.lower().lstrip(".") not in _IMAGE_EXTS:
        return None
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), 72, 72, True)
    except GLib.Error:
        return None
    return Gdk.Texture.new_for_pixbuf(pixbuf)


class QueueView:
    def __init__(self, window) -> None:
        self._window = window

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
        self._clear()
        if not tasks:
            self.widget.set_visible_child_name("empty")
            return
        self.widget.set_visible_child_name("list")
        # Newest first.
        for task in reversed(tasks):
            self._list.append(self._make_row(task))

    def _clear(self) -> None:
        child = self._list.get_first_child()
        while child is not None:
            self._list.remove(child)
            child = self._list.get_first_child()

    def _make_row(self, task: Task) -> Gtk.Widget:
        row = Gtk.ListBoxRow()
        row.set_activatable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)

        box.append(self._thumb(task))

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info.set_hexpand(True)
        info.set_valign(Gtk.Align.CENTER)

        title = Gtk.Label(
            label=f"{task.input_path.name}  →  {task.output_path.name}", xalign=0.0
        )
        title.add_css_class("heading")
        title.set_ellipsize(3)  # Pango.EllipsizeMode.END
        info.append(title)

        meta = Gtk.Label(label=self._meta_text(task), xalign=0.0)
        meta.add_css_class("caption")
        meta.add_css_class("dim-label")
        meta.set_ellipsize(3)
        info.append(meta)

        if task.status == TaskStatus.RUNNING:
            bar = Gtk.ProgressBar()
            bar.set_fraction(task.progress)
            bar.add_css_class("queue-progress")
            info.append(bar)

        box.append(info)
        box.append(self._status_pill(task))
        box.append(self._actions(task))

        row.set_child(box)
        return row

    def _thumb(self, task: Task) -> Gtk.Widget:
        tile = Gtk.Box()
        tile.add_css_class("queue-thumb")
        tile.set_overflow(Gtk.Overflow.HIDDEN)
        tile.set_size_request(36, 36)
        tile.set_valign(Gtk.Align.CENTER)
        tile.set_halign(Gtk.Align.CENTER)

        texture = _load_thumbnail(task.input_path)
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

    def _meta_text(self, task: Task) -> str:
        parts = [task.engine, _STATUS_LABEL.get(task.status, str(task.status))]
        if task.status == TaskStatus.RUNNING and task.progress > 0:
            parts.append(f"{int(task.progress * 100)}%")
        if task.status == TaskStatus.FAILED and task.error:
            parts.append(task.error)
        return " · ".join(parts)

    def _status_pill(self, task: Task) -> Gtk.Widget:
        pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pill.set_valign(Gtk.Align.CENTER)
        pill.add_css_class("status-pill")
        pill.add_css_class(_STATUS_CSS.get(task.status, "status-pending"))

        if task.status == TaskStatus.RUNNING:
            spinner = Gtk.Spinner()
            spinner.set_spinning(True)
            pill.append(spinner)

        label = Gtk.Label(label=_STATUS_LABEL.get(task.status, str(task.status)))
        label.add_css_class("caption-heading")
        pill.append(label)
        return pill

    def _actions(self, task: Task) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_valign(Gtk.Align.CENTER)

        if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            box.append(self._button("Cancel", task, self._on_cancel, destructive=True))
        if task.can_retry():
            box.append(self._button("Retry", task, self._on_retry))
        box.append(self._button("Details", task, self._on_details))
        return box

    def _button(self, label, task, handler, *, destructive=False) -> Gtk.Button:
        button = Gtk.Button(label=label)
        button.add_css_class("flat")
        if destructive:
            button.add_css_class("destructive-action")
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", lambda _b, t=task: handler(t))
        return button

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
            row = Adw.ActionRow(title=title, subtitle=value or "—")
            row.set_subtitle_selectable(True)
            row.set_activatable(False)
            fields.add(row)
        if task.error:
            error_row = Adw.ActionRow(title="Error", subtitle=task.error)
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
