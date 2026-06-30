"""Dashboard — at-a-glance stats and engine availability.

Four summary cards (Total · Running · Completed · Needs attention) over a
grid of the command-line engines the app drives, each probed live with
``shutil.which`` plus an FFmpeg hardware-acceleration line (feature-map
§D). The card counts stay at zero until the task queue is wired up; the
engine grid is fully functional now since it only inspects ``PATH``.

This is the only non-converter sidebar destination, so it carries no
output/footer chrome — just the content.
"""

from __future__ import annotations

import math
import subprocess
from shutil import which

from gi.repository import Adw, Gdk, Gtk, Pango, PangoCairo

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

SUMMARY_CARDS: tuple[tuple[str, str], ...] = (
    ("total", "Total tasks"),
    ("running", "Running"),
    ("success", "Completed"),
    ("failed", "Needs attention"),
)

# (label, count_by_period granularity) — mirrors the old dashboard.
GRANULARITIES: tuple[tuple[str, str], ...] = (
    ("Per day", "day"),
    ("Per week", "week"),
    ("Per month", "month"),
    ("Per year", "year"),
)

# Keep the chart readable when there's a long history.
MAX_BUCKETS = 24


class DashboardPage:
    def __init__(self, window) -> None:
        self._window = window
        self._values: dict[str, Gtk.Label] = {}
        self._status: dict[str, Gtk.Label] = {}

        self._chart_buckets: list[tuple[str, int]] = []
        self._granularity = GRANULARITIES[0][1]

        page = Adw.PreferencesPage()
        page.add(self._build_summary_group())
        page.add(self._build_activity_group())
        page.add(self._build_engines_group())

        self.widget = page
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
        for key, label in SUMMARY_CARDS:
            flow.append(self._make_card(key, label))
        group.add(flow)
        return group

    def _make_card(self, key: str, label: str) -> Gtk.Widget:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.add_css_class("card")
        card.add_css_class("stat-card")

        value = Gtk.Label(label="0", xalign=0.0)
        value.add_css_class("stat-value")
        self._values[key] = value
        card.append(value)

        caption = Gtk.Label(label=label, xalign=0.0)
        caption.add_css_class("dim-label")
        caption.add_css_class("caption")
        card.append(caption)
        return card

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
        for binary, status in self._status.items():
            available = which(binary) is not None
            status.set_label("Installed" if available else "Missing")
            status.remove_css_class("engine-ok")
            status.remove_css_class("engine-missing")
            status.add_css_class("engine-ok" if available else "engine-missing")

        accels = _detect_hwaccels()
        if accels:
            self._hwaccel_row.set_subtitle(", ".join(accels))
        else:
            self._hwaccel_row.set_subtitle("None detected (or ffmpeg missing)")

    # -- counts (wired to the queue later) --------------------------------

    def set_counts(self, *, total: int, running: int, success: int, failed: int) -> None:
        for key, count in (
            ("total", total), ("running", running),
            ("success", success), ("failed", failed),
        ):
            if key in self._values:
                self._values[key].set_label(str(count))
        # Task counts changed, so the history did too — keep the chart live.
        self._refresh_chart()


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
