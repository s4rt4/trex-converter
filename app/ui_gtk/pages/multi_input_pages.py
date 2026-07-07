"""Multi-input converter pages.

These destinations take several files and produce one output: Video
concat, Audio mix, Image montage, Document / PDF / Subtitle merge, and
PDF compare. They all share one anatomy — a :class:`FileListInput` for
the inputs, an Output group, an optional small options group, and the
standard footer — so a :class:`MultiInputPage` base captures it and each
kind is a thin subclass declaring its formats, operation, and extras.

Option keys, defaults, and the "emit only when changed/non-empty" rule
mirror the old Qt ``*OptionsPanel`` classes (see feature-map §C, sub-PDF
& multi-input). The first file is the primary input; the rest are passed
as ``extra_inputs``. Convert / Add to queue validate the file count but
are not wired to the engine until the Queue step.
"""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gtk

from app.core.settings import get_settings
from app.ui_gtk.formats import picker_args
from app.ui_gtk.widgets.destination_row import DestinationRow
from app.ui_gtk.widgets.file_list_input import FileListInput
from app.ui_gtk.widgets.format_picker import FormatPicker
from app.ui_gtk.widgets.page_scaffold import PageScaffold
from app.ui_gtk.widgets.preset_bar import PresetBar
from app.ui_gtk.widgets.rows import ChoiceRow, spin_row, wire_change


class MultiInputPage:
    # -- per-kind declaration (overridden by subclasses) ------------------
    KIND: str = ""
    OPERATION: str = ""
    FILE_ICON: str = "document"
    EMPTY_SUBTITLE: str = "Add or drop files to convert"
    REORDERABLE: bool = True
    MIN_FILES: int = 2
    NEED_MORE_MESSAGE: str = "Add at least two files."

    OUTPUT_FORMATS: tuple[str, ...] = ()
    COMMON_FORMATS: tuple[str, ...] | None = None
    DEFAULT_FORMAT: str | None = None
    FIXED_FORMAT: str | None = None  # output is always this format (e.g. pdf)
    DIRECTORY_OUTPUT: bool = False
    DEST_TITLE: str = "Save to"

    def __init__(self, window) -> None:
        self._window = window
        self.format_picker: FormatPicker | None = None

        # --- Files --------------------------------------------------------
        self.files = FileListInput(
            self._refresh_summaries,
            title="Files",
            reorderable=self.REORDERABLE,
            empty_subtitle=self.EMPTY_SUBTITLE,
        )

        # --- Output -------------------------------------------------------
        output_group = Adw.PreferencesGroup(title="Output")
        if self.OUTPUT_FORMATS:
            self.format_picker = FormatPicker(
                **picker_args(
                    self.KIND, self.OUTPUT_FORMATS,
                    common=self.COMMON_FORMATS, default=self.DEFAULT_FORMAT,
                ),
                title="Format",
            )
            output_group.add(self.format_picker.row)
        elif self.FIXED_FORMAT:
            fixed = Adw.ActionRow(title="Format")
            fixed.set_subtitle(self.FIXED_FORMAT.upper())
            fixed.set_activatable(False)
            output_group.add(fixed)
        self.destination = DestinationRow(
            title=self.DEST_TITLE, initial=_default_output_dir()
        )
        output_group.add(self.destination.row)

        # --- Options (optional, per kind) ---------------------------------
        self._options_group = self._build_options()

        # --- Footer -------------------------------------------------------
        preset_bar = PresetBar(
            kind=self.KIND,
            get_options=self.collect_options,
            apply_options=self.apply_options,
            toast=window.show_toast,
        )
        self.scaffold = PageScaffold(
            on_convert=self._on_convert,
            on_add_to_queue=self._on_add_to_queue,
            preset_bar=preset_bar,
        )
        self.scaffold.add_group(self.files.group)
        self.scaffold.add_group(output_group)
        if self._options_group is not None:
            self.scaffold.add_group(self._options_group)

        self.widget = self.scaffold
        self._refresh_summaries()

    # -- hooks for subclasses ---------------------------------------------

    def _build_options(self) -> Adw.PreferencesGroup | None:
        """Return a preferences group for kind-specific options, or None."""
        return None

    def _collect_extra(self, opts: dict) -> None:
        """Add kind-specific option keys to ``opts`` (emit-if-changed)."""

    def _apply_extra(self, payload: dict) -> None:
        """Restore kind-specific controls from a saved preset payload."""

    def _refresh_summaries(self, *_args) -> None:
        """Update any live summaries; default is a no-op."""

    # -- options round-trip -----------------------------------------------

    def collect_options(self) -> dict:
        opts: dict[str, object] = {
            "category": self.KIND,
            "operation": self.OPERATION,
        }
        if self.format_picker is not None:
            opts["format_out"] = self.format_picker.get_format()
        elif self.FIXED_FORMAT:
            opts["format_out"] = self.FIXED_FORMAT
        self._collect_extra(opts)
        return opts

    def apply_options(self, payload: dict) -> None:
        if self.format_picker is not None:
            # Reset to the page default when the preset carries no format,
            # so loading never inherits a previously chosen format.
            fmt = payload.get("format_out", self.DEFAULT_FORMAT)
            if fmt:
                self.format_picker.set_format(str(fmt))
        self._apply_extra(payload)
        self._refresh_summaries()

    # -- actions -----------------------------------------------------------

    def _has_enough_files(self) -> bool:
        if len(self.files.paths) < self.MIN_FILES:
            self._window.show_toast(self.NEED_MORE_MESSAGE)
            return False
        return True

    def _on_convert(self) -> None:
        self._enqueue(switch=True)

    def _on_add_to_queue(self) -> None:
        self._enqueue(switch=False)

    def _enqueue(self, *, switch: bool) -> None:
        if not self._has_enough_files():
            return
        options = self.collect_options()
        fmt = options.pop("format_out", None)
        self._window.enqueue(
            self.KIND, self.files.primary,
            extra_inputs=self.files.extra_inputs,
            output_dir=self.destination.directory,
            format_out=fmt, options=options, switch_to_queue=switch,
        )


# --- concrete pages ------------------------------------------------------


class VideoConcatPage(MultiInputPage):
    KIND = "video-concat"
    OPERATION = "concat"
    FILE_ICON = "video"
    EMPTY_SUBTITLE = "Clips are joined in this order — drag in MP4, MOV, MKV, WebM"
    OUTPUT_FORMATS = ("mp4", "mov", "mkv", "webm")
    COMMON_FORMATS = ("mp4", "mov", "mkv", "webm")
    DEFAULT_FORMAT = "mp4"


class AudioMixPage(MultiInputPage):
    KIND = "audio-mix"
    OPERATION = "mix"
    FILE_ICON = "audio"
    EMPTY_SUBTITLE = "Tracks are overlaid into one — add audio files"
    OUTPUT_FORMATS = ("mp3", "wav", "aac", "flac", "m4a", "opus", "ogg")
    COMMON_FORMATS = ("mp3", "wav", "m4a", "flac")
    DEFAULT_FORMAT = "mp3"

    _DURATIONS = (
        ("Longest input", "longest"),
        ("Shortest input", "shortest"),
        ("First input", "first"),
    )

    def _build_options(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(
            title="Mix",
            description="Overlay tracks with FFmpeg amix.",
        )
        self.mix_duration = ChoiceRow("Output duration", self._DURATIONS, "longest")
        self.mix_normalize = Adw.SwitchRow(
            title="Normalize",
            subtitle="Scale the sum to 1/N to avoid clipping",
            active=True,
        )
        group.add(self.mix_duration.row)
        group.add(self.mix_normalize)
        return group

    def _collect_extra(self, opts: dict) -> None:
        if self.mix_duration.get_value() != "longest":
            opts["mix_duration"] = self.mix_duration.get_value()
        if not self.mix_normalize.get_active():
            opts["mix_normalize"] = False

    def _apply_extra(self, payload: dict) -> None:
        self.mix_duration.set_value(str(payload.get("mix_duration", "longest")))
        self.mix_normalize.set_active(bool(payload.get("mix_normalize", True)))


class ImageMontagePage(MultiInputPage):
    KIND = "image-montage"
    OPERATION = "montage"
    FILE_ICON = "image"
    EMPTY_SUBTITLE = "Tiles are laid out in this order — add images"
    OUTPUT_FORMATS = ("png", "jpg", "jpeg", "webp", "tiff", "bmp")
    COMMON_FORMATS = ("png", "jpg", "webp")
    DEFAULT_FORMAT = "png"

    def _build_options(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(
            title="Montage",
            description="Leave a field blank for the ImageMagick default.",
        )
        self.montage_tile = Adw.EntryRow(title="Tile — e.g. 3x3 (blank = auto)")
        self.montage_geometry = Adw.EntryRow(title="Geometry — WxH+padX+padY")
        self.montage_background = Adw.EntryRow(title="Background — e.g. white, #0c2c55")
        for row in (
            self.montage_tile, self.montage_geometry, self.montage_background
        ):
            group.add(row)
        return group

    def _collect_extra(self, opts: dict) -> None:
        tile = self.montage_tile.get_text().strip()
        if tile:
            opts["montage_tile"] = tile
        geometry = self.montage_geometry.get_text().strip()
        if geometry:
            opts["montage_geometry"] = geometry
        background = self.montage_background.get_text().strip()
        if background:
            opts["montage_background"] = background

    def _apply_extra(self, payload: dict) -> None:
        self.montage_tile.set_text(str(payload.get("montage_tile", "")))
        self.montage_geometry.set_text(str(payload.get("montage_geometry", "")))
        self.montage_background.set_text(str(payload.get("montage_background", "")))


class SubtitleMergePage(MultiInputPage):
    KIND = "subtitle-merge"
    OPERATION = "merge"
    FILE_ICON = "subtitle"
    EMPTY_SUBTITLE = "Files are merged in this order — add SRT, VTT, ASS"
    OUTPUT_FORMATS = ("srt", "vtt", "ass")
    COMMON_FORMATS = ("srt", "vtt", "ass")
    DEFAULT_FORMAT = "srt"

    _MODES = (
        ("Shift each file (sequential)", "shift"),
        ("Append + sort by time", "append"),
    )

    def _build_options(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="Merge")
        self.merge_mode = ChoiceRow("Mode", self._MODES, "shift")
        self.merge_gap = spin_row(
            "Gap between files (s)", 0.0, 600.0, 0.0, step=0.5, digits=2
        )
        group.add(self.merge_mode.row)
        group.add(self.merge_gap)
        return group

    def _collect_extra(self, opts: dict) -> None:
        if self.merge_mode.get_value() != "shift":
            opts["subtitle_merge_mode"] = self.merge_mode.get_value()
        gap = round(self.merge_gap.get_value(), 3)
        if gap > 0:
            opts["subtitle_merge_gap"] = gap

    def _apply_extra(self, payload: dict) -> None:
        self.merge_mode.set_value(str(payload.get("subtitle_merge_mode", "shift")))
        self.merge_gap.set_value(_as_float(payload.get("subtitle_merge_gap", 0.0), 0.0))


class DocumentMergePage(MultiInputPage):
    KIND = "document-merge"
    OPERATION = "bulk_merge_to_pdf"
    FILE_ICON = "document"
    EMPTY_SUBTITLE = "Documents are merged into one PDF, in this order"
    FIXED_FORMAT = "pdf"


class PdfMergePage(MultiInputPage):
    KIND = "pdf-merge"
    OPERATION = "merge"
    FILE_ICON = "pdf"
    EMPTY_SUBTITLE = "PDFs are merged into one, in this order"
    FIXED_FORMAT = "pdf"


class PdfComparePage(MultiInputPage):
    KIND = "pdf-compare"
    OPERATION = "compare"
    FILE_ICON = "pdf"
    EMPTY_SUBTITLE = "Add the two PDFs to compare"
    REORDERABLE = False
    MIN_FILES = 2
    NEED_MORE_MESSAGE = "Add two PDFs to compare."
    DIRECTORY_OUTPUT = True
    DEST_TITLE = "Save report to"


# --- helpers / builders --------------------------------------------------


def _as_float(value, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _default_output_dir() -> Path | None:
    configured = get_settings().output_dir.strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_dir():
            return path
    return None


def _make_builder(page_cls):
    def build(window) -> Gtk.Widget:
        page = page_cls(window)
        page.widget._trex_page = page  # lets window.open_with_file reach it
        return page.widget

    return build


# kind -> page builder, consumed by the window's _PAGE_BUILDERS.
MULTI_INPUT_BUILDERS = {
    cls.KIND: _make_builder(cls)
    for cls in (
        VideoConcatPage,
        AudioMixPage,
        ImageMontagePage,
        SubtitleMergePage,
        DocumentMergePage,
        PdfMergePage,
        PdfComparePage,
    )
}
