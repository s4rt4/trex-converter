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

import subprocess
from shutil import which

from gi.repository import Adw, Gtk

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


class DashboardPage:
    def __init__(self, window) -> None:
        self._window = window
        self._values: dict[str, Gtk.Label] = {}
        self._status: dict[str, Gtk.Label] = {}

        page = Adw.PreferencesPage()
        page.add(self._build_summary_group())
        page.add(self._build_engines_group())

        self.widget = page
        self.refresh_engines()

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

    # -- engines -----------------------------------------------------------

    def _build_engines_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(
            title="Engines",
            description="External tools this app drives, probed on your PATH.",
        )
        refresh = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh.add_css_class("flat")
        refresh.set_valign(Gtk.Align.CENTER)
        refresh.set_tooltip_text("Re-check installed engines")
        refresh.connect("clicked", lambda _b: self.refresh_engines())
        group.set_header_suffix(refresh)

        for binary, module in ENGINE_BINARIES:
            row = Adw.ActionRow(title=binary, subtitle=module)
            row.set_activatable(False)
            status = Gtk.Label(label="…")
            status.set_valign(Gtk.Align.CENTER)
            self._status[binary] = status
            row.add_suffix(status)
            group.add(row)

        self._hwaccel_row = Adw.ActionRow(title="FFmpeg hardware acceleration")
        self._hwaccel_row.set_subtitle("Checking…")
        self._hwaccel_row.set_activatable(False)
        group.add(self._hwaccel_row)
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
