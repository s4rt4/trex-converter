"""Dashboard — the app's home: stats, shortcuts, history, engines.

Top to bottom: four summary cards (Total · Running · Completed · Needs
attention), a quick-convert drop card that routes any file to the right
converter page, shortcut chips for the most-used destinations, the
activity chart, the most recent tasks from the persistent history, and
the engine-availability grid (probed with ``shutil.which`` plus an
FFmpeg hardware-acceleration line, feature-map §D).

This is the only non-converter sidebar destination, so it carries no
output/footer chrome — just the content.
"""

from __future__ import annotations

import math
import subprocess
import threading
from pathlib import Path
from shutil import which

from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango, PangoCairo

from app.core.task import TaskStatus
from app.ui_gtk.icons import icon_name
from app.ui_gtk.navigation import find_item

# (binary, what it powers) — mirrors the old dashboard's ENGINE_BINARIES.
ENGINE_BINARIES: tuple[tuple[str, str], ...] = (
    ("ffmpeg", "Video / Audio"),
    ("magick", "Image / Trace"),
    ("libreoffice", "Document"),
    ("qpdf", "PDF repair / linearize"),
    ("tesseract", "OCR"),
    ("inkscape", "SVG / Vector"),
    ("potrace", "Pixmap → SVG"),
    ("pandoc", "Ebook"),
    ("exiftool", "Metadata"),
    ("qrencode", "QR generate"),
    ("zbarimg", "QR / Barcode decode"),
)

# (key, caption, metric css class) — each card gets a Lucide glyph
# (icon_name("stat-<key>")) tinted by its metric colour.
SUMMARY_CARDS: tuple[tuple[str, str, str], ...] = (
    ("total", "Total tasks", "metric-total"),
    ("running", "Running", "metric-running"),
    ("success", "Completed", "metric-success"),
    ("failed", "Needs attention", "metric-failed"),
)

# (label, count_by_period granularity) — mirrors the old dashboard.
GRANULARITIES: tuple[tuple[str, str], ...] = (
    ("Per day", "day"),
    ("Per week", "week"),
    ("Per month", "month"),
    ("Per year", "year"),
)

# Sidebar destinations surfaced as one-click shortcuts.
QUICK_ACTIONS: tuple[str, ...] = (
    "image", "video", "audio", "document",
    "pdf", "pdf-merge", "ocr", "qr",
)

_RECENT_LIMIT = 6

_STATUS_LABEL = {
    TaskStatus.PENDING: "Pending",
    TaskStatus.RUNNING: "Running",
    TaskStatus.SUCCESS: "Completed",
    TaskStatus.FAILED: "Failed",
    TaskStatus.CANCELLED: "Cancelled",
}
_STATUS_CSS = {
    TaskStatus.SUCCESS: "engine-ok",
    TaskStatus.FAILED: "engine-missing",
}

# Keep the chart readable when there's a long history.
MAX_BUCKETS = 24


class DashboardPage:
    def __init__(self, window) -> None:
        self._window = window
        self._values: dict[str, Gtk.Label] = {}
        self._anim: dict[str, int] = {}  # key -> GLib timeout source id
        self._status: dict[str, Gtk.Label] = {}
        # Bumped per refresh and on destroy so a slow `ffmpeg -hwaccels`
        # probe can't write into stale (or disposed) rows.
        self._hwaccel_generation = 0

        self._chart_buckets: list[tuple[str, int]] = []
        self._granularity = GRANULARITIES[0][1]
        self._recent_rows: list[Gtk.Widget] = []

        page = Adw.PreferencesPage()
        page.add(self._build_summary_group())
        page.add(self._build_convert_group())
        page.add(self._build_activity_group())
        page.add(self._build_recent_group())
        page.add(self._build_engines_group())

        self.widget = page
        self.widget.connect("destroy", self._on_destroy)
        self.refresh_engines()
        self._refresh_chart()
        if hasattr(window, "register_dashboard"):
            window.register_dashboard(self)

    # -- summary cards -----------------------------------------------------

    def _build_summary_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup()

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_column_spacing(12)
        flow.set_row_spacing(12)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(4)
        for key, label, metric in SUMMARY_CARDS:
            flow.append(self._make_card(key, label, metric))
        group.add(flow)
        return group

    def _make_card(self, key: str, label: str, metric: str) -> Gtk.Widget:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("card")
        card.add_css_class("stat-card")
        card.add_css_class(metric)

        icon = Gtk.Image.new_from_icon_name(icon_name(f"stat-{key}"))
        icon.set_pixel_size(22)
        icon.set_halign(Gtk.Align.START)
        icon.add_css_class("stat-icon")
        card.append(icon)

        value = Gtk.Label(label="0", xalign=0.0)
        value.add_css_class("stat-value")
        self._values[key] = value
        card.append(value)

        caption = Gtk.Label(label=label, xalign=0.0)
        caption.add_css_class("dim-label")
        caption.add_css_class("caption")
        card.append(caption)
        return card

    # -- quick convert -------------------------------------------------------

    def _build_convert_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="Start converting")

        drop = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        drop.add_css_class("dropzone")
        drop.add_css_class("empty")
        drop.add_css_class("quick-drop")
        drop.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
        icon = Gtk.Image.new_from_icon_name(icon_name("convert"))
        icon.set_pixel_size(28)
        drop.append(icon)
        title = Gtk.Label(label="Drop any file here — or click to choose")
        title.add_css_class("heading")
        drop.append(title)
        subtitle = Gtk.Label(
            label="It opens in the right converter automatically"
        )
        subtitle.add_css_class("dim-label")
        subtitle.add_css_class("caption")
        drop.append(subtitle)
        drop.update_property(
            [Gtk.AccessibleProperty.LABEL],
            ["Drop any file to open it in its converter"],
        )

        target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        target.connect("drop", self._on_quick_drop)
        target.connect("enter", lambda *_: (
            drop.add_css_class("drag-over"), Gdk.DragAction.COPY
        )[1])
        target.connect("leave", lambda *_: drop.remove_css_class("drag-over"))
        drop.add_controller(target)
        click = Gtk.GestureClick()
        click.connect("released", self._on_quick_click)
        drop.add_controller(click)
        self._quick_drop = drop
        group.add(drop)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_column_spacing(8)
        flow.set_row_spacing(8)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(4)
        flow.set_margin_top(10)
        for item_id in QUICK_ACTIONS:
            item = find_item(item_id)
            if item is None:
                continue
            button = Gtk.Button()
            button.add_css_class("card")
            button.add_css_class("quick-action")
            inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            inner.set_halign(Gtk.Align.CENTER)
            inner.append(Gtk.Image.new_from_icon_name(icon_name(item.icon)))
            inner.append(Gtk.Label(label=item.title))
            button.set_child(inner)
            button.connect(
                "clicked",
                lambda _b, dest=item_id: self._window.navigate_to(dest),
            )
            flow.append(button)
        group.add(flow)
        return group

    def _on_quick_drop(self, _target, value, _x, _y) -> bool:
        self._quick_drop.remove_css_class("drag-over")
        files = value.get_files() if value is not None else []
        for gfile in files:
            local = gfile.get_path()
            if local:
                return self._window.open_with_file(Path(local))
        return False

    def _on_quick_click(self, _gesture, _n_press, _x, _y) -> None:
        dialog = Gtk.FileDialog(title="Choose a file to convert")
        dialog.open(
            self._window if isinstance(self._window, Gtk.Window) else None,
            None,
            self._on_quick_open_done,
        )

    def _on_quick_open_done(self, dialog: Gtk.FileDialog, result) -> None:
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return
        local = gfile.get_path() if gfile else None
        if local:
            self._window.open_with_file(Path(local))

    # -- recent tasks --------------------------------------------------------

    def _build_recent_group(self) -> Adw.PreferencesGroup:
        self._recent_group = Adw.PreferencesGroup(
            title="Recent tasks",
            description="The latest conversions, newest first.",
        )
        self._refresh_recent()
        return self._recent_group

    def _refresh_recent(self) -> None:
        for row in self._recent_rows:
            self._recent_group.remove(row)
        self._recent_rows = []

        queue = getattr(self._window, "queue", None)
        tasks = queue.recent_tasks(_RECENT_LIMIT) if queue is not None else []

        if not tasks:
            placeholder = Adw.ActionRow(title="No tasks yet")
            placeholder.set_use_markup(False)
            placeholder.set_subtitle(
                "Converted files will show up here once you start a task."
            )
            placeholder.set_activatable(False)
            placeholder.add_css_class("dim-label")
            self._recent_group.add(placeholder)
            self._recent_rows.append(placeholder)
            return

        for task in tasks:
            row = Adw.ActionRow(
                title=f"{task.input_path.name}  →  {task.output_path.name}"
            )
            row.set_use_markup(False)  # file names are user data, not markup
            row.set_subtitle(task.engine)
            row.set_activatable(False)

            status = Gtk.Label(
                label=_STATUS_LABEL.get(task.status, str(task.status))
            )
            status.set_valign(Gtk.Align.CENTER)
            status.add_css_class("caption-heading")
            css = _STATUS_CSS.get(task.status)
            if css:
                status.add_css_class(css)
            else:
                status.add_css_class("dim-label")
            row.add_suffix(status)

            if task.status == TaskStatus.SUCCESS:
                reveal = Gtk.Button(icon_name=icon_name("folder"))
                reveal.add_css_class("flat")
                reveal.set_valign(Gtk.Align.CENTER)
                reveal.set_tooltip_text("Show the output folder")
                reveal.connect(
                    "clicked",
                    lambda _b, p=task.output_path: self._open_folder(p.parent),
                )
                row.add_suffix(reveal)

            self._recent_group.add(row)
            self._recent_rows.append(row)

    def _open_folder(self, folder: Path) -> None:
        if not folder.is_dir():
            return
        launcher = Gtk.FileLauncher.new(Gio.File.new_for_path(str(folder)))
        root = self._window if isinstance(self._window, Gtk.Window) else None
        launcher.launch(root, None, None)

    # -- activity chart ----------------------------------------------------

    def _build_activity_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(
            title="Activity",
            description="Tasks recorded over time, grouped by period.",
        )

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._granularity_dropdown = Gtk.DropDown.new_from_strings(
            [label for label, _value in GRANULARITIES]
        )
        self._granularity_dropdown.set_valign(Gtk.Align.CENTER)
        self._granularity_dropdown.connect("notify::selected", self._on_granularity)
        controls.append(self._granularity_dropdown)

        refresh = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh.add_css_class("flat")
        refresh.set_valign(Gtk.Align.CENTER)
        refresh.set_tooltip_text("Re-read task history")
        refresh.connect("clicked", lambda _b: self._refresh_chart())
        controls.append(refresh)
        group.set_header_suffix(controls)

        card = Gtk.Frame()
        card.add_css_class("activity-chart")
        self._chart_area = Gtk.DrawingArea()
        self._chart_area.set_content_height(200)
        self._chart_area.set_hexpand(True)
        self._chart_area.set_draw_func(self._draw_chart)
        card.set_child(self._chart_area)
        group.add(card)
        return group

    def _on_granularity(self, dropdown: Gtk.DropDown, _param) -> None:
        index = dropdown.get_selected()
        if 0 <= index < len(GRANULARITIES):
            self._granularity = GRANULARITIES[index][1]
            self._refresh_chart()

    def _refresh_chart(self) -> None:
        queue = getattr(self._window, "queue", None)
        if queue is not None:
            self._chart_buckets = queue.count_by_period(self._granularity)[-MAX_BUCKETS:]
        else:
            self._chart_buckets = []
        if hasattr(self, "_chart_area"):
            self._chart_area.queue_draw()

    def _draw_chart(self, _area, cr, width: int, height: int, *_args) -> None:
        fg = self._chart_area.get_color()  # themed foreground
        accent = self._accent_color()

        if not self._chart_buckets:
            self._draw_centered(cr, width, height, fg, "No tasks recorded yet")
            return

        pad_left, pad_right, pad_top, pad_bottom = 8, 8, 12, 22
        plot_w = max(1, width - pad_left - pad_right)
        plot_h = max(1, height - pad_top - pad_bottom)
        baseline = pad_top + plot_h

        # Axis baseline.
        cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.25)
        cr.set_line_width(1)
        cr.move_to(pad_left, baseline + 0.5)
        cr.line_to(width - pad_right, baseline + 0.5)
        cr.stroke()

        n = len(self._chart_buckets)
        max_count = max(count for _label, count in self._chart_buckets) or 1
        slot = plot_w / n
        bar_w = max(2.0, min(slot * 0.6, 40.0))
        label_step = max(1, n // 8)

        for index, (bucket, count) in enumerate(self._chart_buckets):
            slot_x = pad_left + slot * index
            bar_x = slot_x + (slot - bar_w) / 2
            bar_h = (count / max_count) * plot_h
            bar_y = baseline - bar_h

            cr.set_source_rgba(accent.red, accent.green, accent.blue, 1.0)
            _rounded_rect(cr, bar_x, bar_y, bar_w, bar_h, 3)
            cr.fill()

            # Value on top of the bar.
            self._draw_label(
                cr, str(count), slot_x + slot / 2, bar_y - 7, fg, 0.7, size=9
            )
            # Sparse x-axis labels so they don't overlap.
            if index % label_step == 0 or index == n - 1:
                short = _short_label(bucket, self._granularity)
                self._draw_label(
                    cr, short, slot_x + slot / 2, baseline + 11, fg, 0.55, size=9
                )

    def _draw_label(self, cr, text, cx, cy, color, alpha, *, size) -> None:
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(Pango.FontDescription(f"Sans {size}"))
        layout.set_text(text, -1)
        ink, _logical = layout.get_pixel_extents()
        cr.set_source_rgba(color.red, color.green, color.blue, alpha)
        cr.move_to(cx - ink.width / 2 - ink.x, cy - ink.height / 2 - ink.y)
        PangoCairo.show_layout(cr, layout)

    def _draw_centered(self, cr, width, height, color, text) -> None:
        self._draw_label(cr, text, width / 2, height / 2, color, 0.5, size=11)

    def _accent_color(self) -> Gdk.RGBA:
        ok, rgba = self._chart_area.get_style_context().lookup_color("accent_bg_color")
        if ok:
            return rgba
        fallback = Gdk.RGBA()
        fallback.parse("#3584e4")
        return fallback

    # -- engines -----------------------------------------------------------

    def _build_engines_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup()

        # A single collapsible header row so the whole engine list can be
        # hidden when it's not needed; the refresh button rides alongside the
        # expand arrow and toggles independently of the disclosure.
        self._engines_expander = Adw.ExpanderRow(
            title="Engines",
            subtitle="External tools this app drives, probed on your PATH.",
        )
        self._engines_expander.set_expanded(False)

        refresh = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh.add_css_class("flat")
        refresh.set_valign(Gtk.Align.CENTER)
        refresh.set_tooltip_text("Re-check installed engines")
        refresh.connect("clicked", lambda _b: self.refresh_engines())
        self._engines_expander.add_suffix(refresh)

        for binary, module in ENGINE_BINARIES:
            row = Adw.ActionRow(title=binary, subtitle=module)
            row.set_activatable(False)
            status = Gtk.Label(label="…")
            status.set_valign(Gtk.Align.CENTER)
            self._status[binary] = status
            row.add_suffix(status)
            self._engines_expander.add_row(row)

        self._hwaccel_row = Adw.ActionRow(title="FFmpeg hardware acceleration")
        self._hwaccel_row.set_subtitle("Checking…")
        self._hwaccel_row.set_activatable(False)
        self._engines_expander.add_row(self._hwaccel_row)

        group.add(self._engines_expander)
        return group

    def refresh_engines(self) -> None:
        installed = 0
        for binary, status in self._status.items():
            available = which(binary) is not None
            installed += available
            status.set_label("Installed" if available else "Missing")
            status.remove_css_class("engine-ok")
            status.remove_css_class("engine-missing")
            status.add_css_class("engine-ok" if available else "engine-missing")
        self._engines_expander.set_subtitle(
            f"{installed} of {len(self._status)} installed · probed on your PATH"
        )

        # `ffmpeg -hwaccels` spawns a subprocess (up to 3 s on a slow or
        # broken install) — never on the GTK main thread: the dashboard is
        # the default page, so this used to block the window from mapping.
        self._hwaccel_row.set_subtitle("Checking…")
        self._hwaccel_generation += 1
        generation = self._hwaccel_generation

        def worker() -> None:
            accels = _detect_hwaccels()
            GLib.idle_add(self._apply_hwaccels, generation, accels)

        threading.Thread(target=worker, name="hwaccel-probe", daemon=True).start()

    def _apply_hwaccels(self, generation: int, accels: list[str]) -> bool:
        if generation == self._hwaccel_generation:
            if accels:
                self._hwaccel_row.set_subtitle(", ".join(accels))
            else:
                self._hwaccel_row.set_subtitle("None detected (or ffmpeg missing)")
        return False  # one-shot idle callback

    def _on_destroy(self, _widget) -> None:
        self._hwaccel_generation += 1
        for source_id in self._anim.values():
            GLib.source_remove(source_id)
        self._anim.clear()

    # -- counts (wired to the queue later) --------------------------------

    def set_counts(self, *, total: int, running: int, success: int, failed: int) -> None:
        for key, count in (
            ("total", total), ("running", running),
            ("success", success), ("failed", failed),
        ):
            if key in self._values:
                self._animate_count(key, count)
        # Task counts changed, so the history did too — keep the chart and
        # the recent list live.
        self._refresh_chart()
        self._refresh_recent()

    def _animate_count(self, key: str, target: int) -> None:
        """Tick a card's number up/down to ``target`` for a lively feel."""
        label = self._values[key]
        try:
            current = int(label.get_label())
        except ValueError:
            current = 0
        if key in self._anim:
            GLib.source_remove(self._anim[key])
            del self._anim[key]
        if current == target:
            label.set_label(str(target))
            return

        steps = min(12, abs(target - current))
        delta = (target - current) / steps
        state = {"value": float(current), "left": steps}

        def step() -> bool:
            state["left"] -= 1
            if state["left"] <= 0:
                label.set_label(str(target))
                self._anim.pop(key, None)
                return False
            state["value"] += delta
            label.set_label(str(round(state["value"])))
            return True

        self._anim[key] = GLib.timeout_add(28, step)


def _short_label(bucket: str, granularity: str) -> str:
    """Trim an ISO bucket label to something compact for the x-axis."""
    if granularity == "day":          # 2026-06-30 → 06-30
        return bucket[5:] if len(bucket) >= 10 else bucket
    if granularity == "week":         # 2026-W26 → W26
        return bucket.split("-", 1)[1] if "-" in bucket else bucket
    if granularity == "month":        # 2026-06 → keep
        return bucket
    return bucket                     # year → 2026


def _rounded_rect(cr, x, y, w, h, radius) -> None:
    """Path a rectangle with rounded top corners (flat against the axis)."""
    r = min(radius, w / 2, h) if h > 0 else 0
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.line_to(x + w, y + h)
    cr.line_to(x, y + h)
    cr.line_to(x, y + r)
    cr.arc(x + r, y + r, r, math.pi, -math.pi / 2)
    cr.close_path()


def _detect_hwaccels() -> list[str]:
    if which("ffmpeg") is None:
        return []
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True, text=True, timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    lines = [line.strip() for line in result.stdout.splitlines()]
    # First line is the "Hardware acceleration methods:" header.
    return [line for line in lines[1:] if line]


def build_dashboard_page(window) -> Gtk.Widget:
    return DashboardPage(window).widget
