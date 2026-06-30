"""Single-input converter pages without an operations checklist.

The image / video / audio / pdf pages each warranted a bespoke module
(rich checklists or an operation picker). The remaining converters are
simpler: one input, an output target, and a short flat set of options —
or none at all. :class:`SingleInputPage` captures that shape so each kind
is a thin declaration of its formats, operation, and option rows.

Input can be a single file (drop zone) or a folder (Archive compress).
Output can be format chips, a fixed format, or a directory. Option keys,
defaults, and emit-if-changed rules mirror the old Qt ``*OptionsPanel``
classes (feature-map §C). Convert / Add to queue validate input but are
not wired to the engine until the Queue step.
"""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

from app.core.settings import get_settings
from app.ui_gtk.widgets.destination_row import DestinationRow
from app.ui_gtk.widgets.dropzone import DropZone
from app.ui_gtk.widgets.format_picker import FormatPicker
from app.ui_gtk.widgets.page_scaffold import PageScaffold
from app.ui_gtk.widgets.preset_bar import PresetBar
from app.ui_gtk.widgets.rows import ChoiceRow, attach_file_browse, spin_row


class SingleInputPage:
    # -- per-kind declaration ---------------------------------------------
    KIND: str = ""
    OPERATION: str = ""  # emitted verbatim when set (base-only / fixed-op pages)
    FILE_ICON: str = "document"
    EMPTY_TITLE: str = "Drop a file here or click to choose"
    EMPTY_SUBTITLE: str = ""
    INPUT_MODE: str = "file"  # "file" | "folder"
    NEED_INPUT_MESSAGE: str = "Choose a file first."

    OUTPUT_FORMATS: tuple[str, ...] = ()
    COMMON_FORMATS: tuple[str, ...] | None = None
    DEFAULT_FORMAT: str | None = None
    FIXED_FORMAT: str | None = None
    DIRECTORY_OUTPUT: bool = False
    DEST_TITLE: str = "Save to"

    def __init__(self, window) -> None:
        self._window = window
        self.format_picker: FormatPicker | None = None
        self._folder: Path | None = None

        input_group = self._build_input_group()
        output_group = self._build_output_group()
        option_groups = self._build_option_groups()

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
        self.scaffold.add_group(input_group)
        self.scaffold.add_group(output_group)
        for group in option_groups:
            self.scaffold.add_group(group)

        self.widget = self.scaffold
        self._sync()

    # -- input -------------------------------------------------------------

    def _build_input_group(self) -> Adw.PreferencesGroup:
        if self.INPUT_MODE == "folder":
            group = Adw.PreferencesGroup(title="Source")
            self._folder_row = Adw.ActionRow(title="Source folder")
            self._folder_row.set_subtitle("No folder selected")
            button = Gtk.Button(label="Select folder")
            button.add_css_class("flat")
            button.set_valign(Gtk.Align.CENTER)
            button.connect("clicked", self._choose_folder)
            self._folder_row.add_suffix(button)
            self._folder_row.set_activatable_widget(button)
            group.add(self._folder_row)
            return group

        self.dropzone = DropZone(
            self._on_file_changed,
            icon=self.FILE_ICON,
            empty_title=self.EMPTY_TITLE,
            empty_subtitle=self.EMPTY_SUBTITLE,
        )
        group = Adw.PreferencesGroup(title="File")
        group.add(self.dropzone)
        return group

    def _choose_folder(self, _button) -> None:
        dialog = Gtk.FileDialog(title="Choose source folder")
        dialog.select_folder(self._root_window(), None, self._on_folder_done)

    def _on_folder_done(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            gfile = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        local = gfile.get_path() if gfile else None
        if local:
            self._folder = Path(local)
            self._folder_row.set_subtitle(local)

    # -- output ------------------------------------------------------------

    def _build_output_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="Output")
        if self.OUTPUT_FORMATS:
            self.format_picker = FormatPicker(
                self.OUTPUT_FORMATS, common=self.COMMON_FORMATS,
                default=self.DEFAULT_FORMAT, title="Format",
            )
            group.add(self.format_picker.row)
        elif self.FIXED_FORMAT:
            fixed = Adw.ActionRow(title="Format")
            fixed.set_subtitle(self.FIXED_FORMAT.upper())
            fixed.set_activatable(False)
            group.add(fixed)
        self.destination = DestinationRow(
            title=self.DEST_TITLE, initial=_default_output_dir()
        )
        group.add(self.destination.row)
        return group

    # -- hooks for subclasses ---------------------------------------------

    def _build_option_groups(self) -> list[Adw.PreferencesGroup]:
        return []

    def _collect_extra(self, opts: dict) -> None:
        pass

    def _apply_extra(self, payload: dict) -> None:
        pass

    def _sync(self) -> None:
        """Re-evaluate any conditional row visibility. Default no-op."""

    # -- options round-trip -----------------------------------------------

    def collect_options(self) -> dict:
        opts: dict[str, object] = {"category": self.KIND}
        if self.OPERATION:
            opts["operation"] = self.OPERATION
        if self.format_picker is not None:
            opts["format_out"] = self.format_picker.get_format()
        elif self.FIXED_FORMAT:
            opts["format_out"] = self.FIXED_FORMAT
        self._collect_extra(opts)
        return opts

    def apply_options(self, payload: dict) -> None:
        if self.format_picker is not None and "format_out" in payload:
            self.format_picker.set_format(str(payload["format_out"]))
        self._apply_extra(payload)
        self._sync()

    # -- actions -----------------------------------------------------------

    def _on_file_changed(self, _path: Path | None) -> None:
        pass

    def _has_input(self) -> bool:
        if self.INPUT_MODE == "folder":
            return self._folder is not None
        return self.dropzone.path is not None

    def _require_input(self) -> bool:
        if not self._has_input():
            self._window.show_toast(self.NEED_INPUT_MESSAGE)
            return False
        return True

    def _on_convert(self) -> None:
        if self._require_input():
            self._window.show_toast("The conversion engine is not connected yet.")

    def _on_add_to_queue(self) -> None:
        if self._require_input():
            self._window.show_toast("The queue is not connected yet.")

    def _root_window(self) -> Gtk.Window | None:
        return self._window if isinstance(self._window, Gtk.Window) else None


# --- helpers -------------------------------------------------------------


def _as_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


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


# --- Document ------------------------------------------------------------


class DocumentPage(SingleInputPage):
    KIND = "document"
    FILE_ICON = "document"
    EMPTY_TITLE = "Drop a document here or click to choose"
    EMPTY_SUBTITLE = "DOCX, ODT, XLSX, PPTX, HTML, TXT…"
    OUTPUT_FORMATS = ("pdf", "docx", "odt", "rtf", "txt", "html", "epub")
    COMMON_FORMATS = ("pdf", "docx", "odt")
    DEFAULT_FORMAT = "pdf"

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(
            title="PDF options", description="Applied when the output is PDF."
        )
        self.pdf_a = Adw.SwitchRow(
            title="PDF/A-1a", subtitle="Archival output"
        )
        self.pdf_user = Adw.PasswordEntryRow(title="User password")
        self.pdf_owner = Adw.PasswordEntryRow(title="Owner password")
        for row in (self.pdf_a, self.pdf_user, self.pdf_owner):
            group.add(row)
        return [group]

    def _collect_extra(self, opts):
        if self.pdf_a.get_active():
            opts["pdf_a"] = True
        if self.pdf_user.get_text():
            opts["pdf_password_user"] = self.pdf_user.get_text()
        if self.pdf_owner.get_text():
            opts["pdf_password_owner"] = self.pdf_owner.get_text()

    def _apply_extra(self, payload):
        self.pdf_a.set_active(bool(payload.get("pdf_a")))
        self.pdf_user.set_text(str(payload.get("pdf_password_user", "")))
        self.pdf_owner.set_text(str(payload.get("pdf_password_owner", "")))


# --- Subtitle ------------------------------------------------------------


class SubtitlePage(SingleInputPage):
    KIND = "subtitle"
    FILE_ICON = "subtitle"
    EMPTY_TITLE = "Drop a subtitle here or click to choose"
    EMPTY_SUBTITLE = "SRT, VTT, ASS"
    OUTPUT_FORMATS = ("srt", "vtt", "ass")
    COMMON_FORMATS = ("srt", "vtt", "ass")
    DEFAULT_FORMAT = "vtt"

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(title="Timing")
        self.time_shift = spin_row(
            "Time shift (s)", -3600.0, 3600.0, 0.0, step=0.5, digits=2
        )
        group.add(self.time_shift)
        return [group]

    def _collect_extra(self, opts):
        offset = round(self.time_shift.get_value(), 3)
        if abs(offset) > 1e-3:
            opts["time_shift_seconds"] = offset

    def _apply_extra(self, payload):
        self.time_shift.set_value(_as_float(payload.get("time_shift_seconds", 0.0), 0.0))


# --- Subtitle extract ----------------------------------------------------


class SubtitleExtractPage(SingleInputPage):
    KIND = "subtitle-extract"
    FILE_ICON = "subtitle"
    EMPTY_TITLE = "Drop a video here or click to choose"
    EMPTY_SUBTITLE = "MKV, MP4, MOV, WebM"
    OUTPUT_FORMATS = ("srt", "vtt", "ass")
    COMMON_FORMATS = ("srt", "vtt", "ass")
    DEFAULT_FORMAT = "srt"


# --- OCR -----------------------------------------------------------------


class OcrPage(SingleInputPage):
    KIND = "ocr"
    FILE_ICON = "utility"
    EMPTY_TITLE = "Drop an image or PDF here or click to choose"
    EMPTY_SUBTITLE = "PNG, JPG, TIFF, BMP, PDF"
    OUTPUT_FORMATS = ("txt", "pdf", "hocr", "tsv")
    COMMON_FORMATS = ("txt", "pdf", "hocr", "tsv")
    DEFAULT_FORMAT = "txt"

    _LANGUAGES = (
        ("English (eng)", "eng"),
        ("Indonesian (ind)", "ind"),
        ("English + Indonesian", "eng+ind"),
        ("Custom…", "__custom__"),
    )
    _PSM = (
        ("3 — Auto", 3), ("0 — OSD only", 0), ("1 — Auto + OSD", 1),
        ("4 — Single column", 4), ("6 — Single block", 6),
        ("7 — Single line", 7), ("8 — Single word", 8),
        ("11 — Sparse text", 11), ("13 — Raw line", 13),
    )
    _OEM = (
        ("3 — Default (LSTM + Legacy)", 3), ("0 — Legacy only", 0),
        ("1 — LSTM only", 1), ("2 — Legacy + LSTM", 2),
    )

    def _build_option_groups(self):
        settings = get_settings()
        group = Adw.PreferencesGroup(title="Recognition")
        self.language = ChoiceRow("Language", self._LANGUAGES, "eng")
        self.language_custom = Adw.EntryRow(title="Custom languages — e.g. ind+eng+jpn")
        self.psm = ChoiceRow("Page mode", self._PSM, 3)
        self.oem = ChoiceRow("Engine mode", self._OEM, 3)
        self.dpi = spin_row("PDF render DPI", 72, 600, settings.default_pdf_dpi)
        self.auto_rotate = Adw.SwitchRow(
            title="Auto-rotate pages", subtitle="OSD pre-pass (PDF input only)"
        )
        # Seed from the saved default language.
        if settings.default_ocr_language in {v for _, v in self._LANGUAGES}:
            self.language.set_value(settings.default_ocr_language)
        elif settings.default_ocr_language:
            self.language.set_value("__custom__")
            self.language_custom.set_text(settings.default_ocr_language)
        for row in (
            self.language.row, self.language_custom, self.psm.row,
            self.oem.row, self.dpi, self.auto_rotate,
        ):
            group.add(row)
        self.language.row.connect("notify::selected", lambda *_: self._sync())
        return [group]

    def _sync(self):
        self.language_custom.set_visible(self.language.get_value() == "__custom__")

    def _resolved_language(self) -> str:
        value = self.language.get_value()
        if value == "__custom__":
            return self.language_custom.get_text().strip() or "eng"
        return str(value)

    def _collect_extra(self, opts):
        language = self._resolved_language()
        if language and language != "eng":
            opts["ocr_language"] = language
        if self.psm.get_value() != 3:
            opts["ocr_psm"] = self.psm.get_value()
        if self.oem.get_value() != 3:
            opts["ocr_oem"] = self.oem.get_value()
        if int(self.dpi.get_value()) != 300:
            opts["ocr_dpi"] = int(self.dpi.get_value())
        if self.auto_rotate.get_active():
            opts["ocr_auto_rotate"] = True

    def _apply_extra(self, payload):
        language = str(payload.get("ocr_language", "eng"))
        if language in {v for _, v in self._LANGUAGES}:
            self.language.set_value(language)
            self.language_custom.set_text("")
        else:
            self.language.set_value("__custom__")
            self.language_custom.set_text(language)
        self.psm.set_value(_as_int(payload.get("ocr_psm", 3), 3))
        self.oem.set_value(_as_int(payload.get("ocr_oem", 3), 3))
        self.dpi.set_value(_as_int(payload.get("ocr_dpi", 300), 300))
        self.auto_rotate.set_active(bool(payload.get("ocr_auto_rotate")))


# --- Ebook ---------------------------------------------------------------


class EbookPage(SingleInputPage):
    KIND = "ebook"
    FILE_ICON = "document"
    EMPTY_TITLE = "Drop an ebook or document here or click to choose"
    EMPTY_SUBTITLE = "EPUB, DOCX, HTML, Markdown…"
    OUTPUT_FORMATS = ("epub", "pdf", "docx", "html", "fb2", "odt", "txt")
    COMMON_FORMATS = ("epub", "pdf", "docx")
    DEFAULT_FORMAT = "epub"

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(
            title="Metadata", description="Passed to Pandoc as --metadata."
        )
        self.title = Adw.EntryRow(title="Title")
        self.author = Adw.EntryRow(title="Author")
        self.language = Adw.EntryRow(title="Language — e.g. en, id")
        self.publisher = Adw.EntryRow(title="Publisher")
        self.date = Adw.EntryRow(title="Date — YYYY-MM-DD")
        self.toc = Adw.SwitchRow(title="Table of contents", subtitle="Generate --toc")
        self.self_contained = Adw.SwitchRow(
            title="Embed resources", subtitle="Self-contained HTML output"
        )
        for row in (
            self.title, self.author, self.language, self.publisher,
            self.date, self.toc, self.self_contained,
        ):
            group.add(row)
        return [group]

    def _collect_extra(self, opts):
        for key, entry in self._entries():
            value = entry.get_text().strip()
            if value:
                opts[key] = value
        if self.toc.get_active():
            opts["pandoc_table_of_contents"] = True
        if self.self_contained.get_active():
            opts["pandoc_self_contained"] = True

    def _entries(self):
        return (
            ("ebook_title", self.title),
            ("ebook_author", self.author),
            ("ebook_language", self.language),
            ("ebook_publisher", self.publisher),
            ("ebook_date", self.date),
        )

    def _apply_extra(self, payload):
        for key, entry in self._entries():
            entry.set_text(str(payload.get(key, "")))
        self.toc.set_active(bool(payload.get("pandoc_table_of_contents")))
        self.self_contained.set_active(bool(payload.get("pandoc_self_contained")))


# --- QR / Barcode --------------------------------------------------------


class QrPage(SingleInputPage):
    KIND = "qr"
    FILE_ICON = "utility"
    EMPTY_TITLE = "Drop a .txt or image here or click to choose"
    EMPTY_SUBTITLE = "TXT → QR · image → decoded text"
    OUTPUT_FORMATS = ("png", "svg", "txt")
    COMMON_FORMATS = ("png", "svg", "txt")
    DEFAULT_FORMAT = "png"

    _ECC = (
        ("L — ~7%", "L"), ("M — ~15%", "M"), ("Q — ~25%", "Q"), ("H — ~30%", "H"),
    )

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(
            title="Generate", description="Applied when encoding a .txt input."
        )
        self.size = spin_row("Module size (px/dot)", 1, 50, 8)
        self.margin = spin_row("Margin (dots)", 0, 32, 2)
        self.ecc = ChoiceRow("Error correction", self._ECC, "M")
        for row in (self.size, self.margin, self.ecc.row):
            group.add(row)
        return [group]

    def _collect_extra(self, opts):
        if int(self.size.get_value()) != 8:
            opts["qr_size"] = int(self.size.get_value())
        if int(self.margin.get_value()) != 2:
            opts["qr_margin"] = int(self.margin.get_value())
        if self.ecc.get_value() != "M":
            opts["qr_ecc_level"] = self.ecc.get_value()

    def _apply_extra(self, payload):
        self.size.set_value(_as_int(payload.get("qr_size", 8), 8))
        self.margin.set_value(_as_int(payload.get("qr_margin", 2), 2))
        self.ecc.set_value(str(payload.get("qr_ecc_level", "M")))


# --- SVG / Vector --------------------------------------------------------


class SvgPage(SingleInputPage):
    KIND = "svg"
    FILE_ICON = "image"
    EMPTY_TITLE = "Drop a vector or image here or click to choose"
    EMPTY_SUBTITLE = "SVG, PDF, DXF, PNG, JPG…"
    OUTPUT_FORMATS = ("png", "pdf", "svg", "eps", "ps", "dxf")
    COMMON_FORMATS = ("png", "pdf", "svg")
    DEFAULT_FORMAT = "png"

    _SVG_OPS = (
        ("Cleanup (plain SVG)", "cleanup"),
        ("Trim to content", "trim"),
    )
    _PS_LEVELS = (("Auto (3)", 0), ("PostScript level 2", 2), ("PostScript level 3", 3))
    _DXF = (("DXF R14", "r14"), ("DXF R12 (legacy)", "r12"))

    def _build_option_groups(self):
        raster = Adw.PreferencesGroup(
            title="Raster", description="PNG output — width/height override DPI."
        )
        self.dpi = spin_row("Raster DPI (0 = auto)", 0, 2400, 0)
        self.width = spin_row("Width (px, 0 = auto)", 0, 32768, 0)
        self.height = spin_row("Height (px, 0 = auto)", 0, 32768, 0)
        for row in (self.dpi, self.width, self.height):
            raster.add(row)

        vector = Adw.PreferencesGroup(title="Vector")
        self.svg_op = ChoiceRow("SVG operation", self._SVG_OPS, "cleanup")
        self.ps_level = ChoiceRow("PS level", self._PS_LEVELS, 0)
        self.pdf_page = spin_row("PDF page", 1, 9999, 1)
        self.dxf_format = ChoiceRow("DXF format", self._DXF, "r14")
        self.text_to_path = Adw.SwitchRow(
            title="Text → paths", subtitle="PDF / EPS / PS / SVG output"
        )
        self.export_id = Adw.EntryRow(title="Export ID — e.g. logo (blank = full)")
        self.export_id_only = Adw.SwitchRow(
            title="Hide other objects", subtitle="Export the selected ID only"
        )
        for row in (
            self.svg_op.row, self.ps_level.row, self.pdf_page,
            self.dxf_format.row, self.text_to_path, self.export_id,
            self.export_id_only,
        ):
            vector.add(row)

        trace = Adw.PreferencesGroup(
            title="Trace", description="Bitmap → SVG outlining."
        )
        self.trace_threshold = spin_row(
            "Threshold", 0.0, 1.0, 0.5, step=0.05, digits=2
        )
        self.trace_turdsize = spin_row("Turdsize (px²)", 0, 1000, 2)
        for row in (self.trace_threshold, self.trace_turdsize):
            trace.add(row)
        return [raster, vector, trace]

    def _collect_extra(self, opts):
        if int(self.dpi.get_value()) > 0:
            opts["inkscape_dpi"] = int(self.dpi.get_value())
        if int(self.width.get_value()) > 0:
            opts["inkscape_width"] = int(self.width.get_value())
        if int(self.height.get_value()) > 0:
            opts["inkscape_height"] = int(self.height.get_value())
        opts["operation"] = self.svg_op.get_value()
        if self.ps_level.get_value():
            opts["inkscape_ps_level"] = self.ps_level.get_value()
        if int(self.pdf_page.get_value()) > 1:
            opts["inkscape_pdf_page"] = int(self.pdf_page.get_value())
        if self.text_to_path.get_active():
            opts["text_to_path"] = True
        export_id = self.export_id.get_text().strip()
        if export_id:
            opts["inkscape_export_id"] = export_id
            if self.export_id_only.get_active():
                opts["inkscape_export_id_only"] = True
        if self.dxf_format.get_value() != "r14":
            opts["inkscape_dxf_format"] = self.dxf_format.get_value()
        threshold = round(self.trace_threshold.get_value(), 3)
        if abs(threshold - 0.5) > 1e-6:
            opts["trace_threshold"] = threshold
        if int(self.trace_turdsize.get_value()) != 2:
            opts["trace_turdsize"] = int(self.trace_turdsize.get_value())

    def _apply_extra(self, payload):
        self.dpi.set_value(_as_int(payload.get("inkscape_dpi", 0), 0))
        self.width.set_value(_as_int(payload.get("inkscape_width", 0), 0))
        self.height.set_value(_as_int(payload.get("inkscape_height", 0), 0))
        if payload.get("operation") in {v for _, v in self._SVG_OPS}:
            self.svg_op.set_value(payload["operation"])
        self.ps_level.set_value(_as_int(payload.get("inkscape_ps_level", 0), 0))
        self.pdf_page.set_value(_as_int(payload.get("inkscape_pdf_page", 1), 1))
        self.text_to_path.set_active(bool(payload.get("text_to_path")))
        self.export_id.set_text(str(payload.get("inkscape_export_id", "")))
        self.export_id_only.set_active(bool(payload.get("inkscape_export_id_only")))
        self.dxf_format.set_value(str(payload.get("inkscape_dxf_format", "r14")))
        self.trace_threshold.set_value(_as_float(payload.get("trace_threshold", 0.5), 0.5))
        self.trace_turdsize.set_value(_as_int(payload.get("trace_turdsize", 2), 2))


# --- PDF numbering -------------------------------------------------------


class PdfNumberingPage(SingleInputPage):
    KIND = "pdf-numbering"
    OPERATION = "page_numbering"
    FILE_ICON = "pdf"
    EMPTY_TITLE = "Drop a PDF here or click to choose"
    EMPTY_SUBTITLE = "PDF"
    FIXED_FORMAT = "pdf"

    _POSITIONS = (
        ("Bottom", "south"), ("Bottom-right", "southeast"),
        ("Bottom-left", "southwest"), ("Top", "north"),
        ("Top-right", "northeast"), ("Top-left", "northwest"),
    )

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(
            title="Numbering",
            description="Placeholders: {n} number, {total} page count.",
        )
        self.fmt = Adw.EntryRow(title="Format")
        self.fmt.set_text("Page {n} of {total}")
        self.position = ChoiceRow("Position", self._POSITIONS, "south")
        self.size = spin_row("Size (pt)", 6, 72, 14)
        self.start = spin_row("Start at", 0, 100000, 1)
        self.skip = spin_row("Skip first", 0, 100000, 0)
        for row in (self.fmt, self.position.row, self.size, self.start, self.skip):
            group.add(row)
        return [group]

    def _collect_extra(self, opts):
        text = self.fmt.get_text().strip()
        if text:
            opts["page_number_format"] = text
        if self.position.get_value() != "south":
            opts["page_number_position"] = self.position.get_value()
        if int(self.size.get_value()) != 14:
            opts["page_number_size"] = int(self.size.get_value())
        if int(self.start.get_value()) != 1:
            opts["page_number_start"] = int(self.start.get_value())
        if int(self.skip.get_value()) > 0:
            opts["page_number_skip"] = int(self.skip.get_value())

    def _apply_extra(self, payload):
        self.fmt.set_text(str(payload.get("page_number_format", "Page {n} of {total}")))
        self.position.set_value(str(payload.get("page_number_position", "south")))
        self.size.set_value(_as_int(payload.get("page_number_size", 14), 14))
        self.start.set_value(_as_int(payload.get("page_number_start", 1), 1))
        self.skip.set_value(_as_int(payload.get("page_number_skip", 0), 0))


# --- PDF split -----------------------------------------------------------


class PdfSplitPage(SingleInputPage):
    KIND = "pdf-split"
    FILE_ICON = "pdf"
    EMPTY_TITLE = "Drop a PDF here or click to choose"
    EMPTY_SUBTITLE = "PDF"
    DIRECTORY_OUTPUT = True
    DEST_TITLE = "Save parts to"

    _MODES = (
        ("Every N pages", "every_n"),
        ("Custom ranges", "range"),
        ("By file size (MB)", "size"),
    )

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(title="Split")
        self.mode = ChoiceRow("Mode", self._MODES, "every_n")
        self.pages_per_file = spin_row("Pages per file", 1, 1000, 1)
        self.ranges = Adw.EntryRow(title="Ranges — e.g. 1-5, 6-10, 11-20")
        self.size_mb = spin_row("Max chunk size (MB)", 0.1, 10240.0, 10.0, step=1, digits=1)
        for row in (self.mode.row, self.pages_per_file, self.ranges, self.size_mb):
            group.add(row)
        self.mode.row.connect("notify::selected", lambda *_: self._sync())
        return [group]

    def _sync(self):
        mode = self.mode.get_value()
        self.pages_per_file.set_visible(mode == "every_n")
        self.ranges.set_visible(mode == "range")
        self.size_mb.set_visible(mode == "size")

    def _collect_extra(self, opts):
        mode = self.mode.get_value()
        opts["split_mode"] = mode
        if mode == "range":
            ranges = self.ranges.get_text().strip()
            if ranges:
                opts["split_ranges"] = ranges
        elif mode == "size":
            opts["split_size_mb"] = round(self.size_mb.get_value(), 1)
        else:
            opts["split_pages_per_file"] = int(self.pages_per_file.get_value())

    def _apply_extra(self, payload):
        if payload.get("split_mode") in {v for _, v in self._MODES}:
            self.mode.set_value(payload["split_mode"])
        self.pages_per_file.set_value(_as_int(payload.get("split_pages_per_file", 1), 1))
        self.ranges.set_text(str(payload.get("split_ranges", "")))
        self.size_mb.set_value(_as_float(payload.get("split_size_mb", 10.0), 10.0))


# --- PDF extract images / attachments (base-only, dir-out) ---------------


class PdfExtractImagesPage(SingleInputPage):
    KIND = "pdf-extract-images"
    OPERATION = "extract_images"
    FILE_ICON = "pdf"
    EMPTY_TITLE = "Drop a PDF here or click to choose"
    EMPTY_SUBTITLE = "PDF"
    DIRECTORY_OUTPUT = True
    DEST_TITLE = "Save images to"


class PdfExtractAttachmentsPage(SingleInputPage):
    KIND = "pdf-extract-attachments"
    OPERATION = "extract_attachments"
    FILE_ICON = "pdf"
    EMPTY_TITLE = "Drop a PDF here or click to choose"
    EMPTY_SUBTITLE = "PDF"
    DIRECTORY_OUTPUT = True
    DEST_TITLE = "Save attachments to"


# --- Slides to images ----------------------------------------------------


class SlidesToImagesPage(SingleInputPage):
    KIND = "slides-to-images"
    OPERATION = "slides_to_images"
    FILE_ICON = "document"
    EMPTY_TITLE = "Drop a slide deck here or click to choose"
    EMPTY_SUBTITLE = "PPTX, PPT, ODP"
    DIRECTORY_OUTPUT = True
    DEST_TITLE = "Save images to"

    _FORMATS = (("PNG", "png"), ("JPG", "jpg"))

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(title="Rendering")
        self.image_format = ChoiceRow("Image format", self._FORMATS, "png")
        self.dpi = spin_row("Render DPI", 72, 600, 200)
        group.add(self.image_format.row)
        group.add(self.dpi)
        return [group]

    def _collect_extra(self, opts):
        if self.image_format.get_value() != "png":
            opts["slides_image_format"] = self.image_format.get_value()
        if int(self.dpi.get_value()) != 200:
            opts["slides_dpi"] = int(self.dpi.get_value())

    def _apply_extra(self, payload):
        self.image_format.set_value(str(payload.get("slides_image_format", "png")))
        self.dpi.set_value(_as_int(payload.get("slides_dpi", 200), 200))


# --- Archive (extract) / Archive compress --------------------------------


class ArchivePage(SingleInputPage):
    KIND = "archive"
    OPERATION = ""
    FILE_ICON = "archive"
    EMPTY_TITLE = "Drop an archive here or click to choose"
    EMPTY_SUBTITLE = "ZIP, TAR, GZ, BZ2, XZ…"
    DIRECTORY_OUTPUT = True
    DEST_TITLE = "Extract to"


class ArchiveCompressPage(SingleInputPage):
    KIND = "archive-compress"
    FILE_ICON = "archive"
    INPUT_MODE = "folder"
    NEED_INPUT_MESSAGE = "Choose a folder first."
    OUTPUT_FORMATS = ("zip", "tar", "tgz", "tbz", "txz")
    COMMON_FORMATS = ("zip", "tar", "tgz")
    DEFAULT_FORMAT = "zip"


# --- Metadata ------------------------------------------------------------


class MetadataPage(SingleInputPage):
    KIND = "metadata"
    FILE_ICON = "utility"
    EMPTY_TITLE = "Drop a file here or click to choose"
    EMPTY_SUBTITLE = "Image · audio · video · PDF"

    _OPERATIONS = (
        ("Strip all metadata", "strip"),
        ("Edit selected fields", "edit"),
        ("Read metadata → file", "read"),
    )
    _READ_FORMATS = (("JSON", "json"), ("Plain text", "text"))

    def _build_output_group(self):
        # Output is driven by the operation, not a format picker; keep just
        # the destination row.
        group = Adw.PreferencesGroup(title="Output")
        self.destination = DestinationRow(
            title=self.DEST_TITLE, initial=_default_output_dir()
        )
        group.add(self.destination.row)
        return group

    def _build_option_groups(self):
        group = Adw.PreferencesGroup(title="Metadata")
        self.operation = ChoiceRow("Operation", self._OPERATIONS, "strip")
        self.read_format = ChoiceRow("Read format", self._READ_FORMATS, "json")
        self._fields = {
            "metadata_title": Adw.EntryRow(title="Title"),
            "metadata_artist": Adw.EntryRow(title="Artist"),
            "metadata_author": Adw.EntryRow(title="Author"),
            "metadata_subject": Adw.EntryRow(title="Subject"),
            "metadata_description": Adw.EntryRow(title="Description"),
            "metadata_comment": Adw.EntryRow(title="Comment"),
            "metadata_copyright": Adw.EntryRow(title="Copyright"),
            "metadata_keywords": Adw.EntryRow(title="Keywords"),
        }
        group.add(self.operation.row)
        group.add(self.read_format.row)
        for row in self._fields.values():
            group.add(row)
        self.operation.row.connect("notify::selected", lambda *_: self._sync())
        return [group]

    def _sync(self):
        op = self.operation.get_value()
        self.read_format.row.set_visible(op == "read")
        for row in self._fields.values():
            row.set_visible(op == "edit")

    def _collect_extra(self, opts):
        op = self.operation.get_value()
        opts["operation"] = op
        if op == "read":
            opts["metadata_format"] = self.read_format.get_value()
        elif op == "edit":
            for key, entry in self._fields.items():
                value = entry.get_text().strip()
                if value:
                    opts[key] = value

    def _apply_extra(self, payload):
        op = payload.get("operation", "strip")
        if op in {v for _, v in self._OPERATIONS}:
            self.operation.set_value(op)
        if "metadata_format" in payload:
            self.read_format.set_value(str(payload["metadata_format"]))
        for key, entry in self._fields.items():
            entry.set_text(str(payload.get(key, "")))


# --- builder registry ----------------------------------------------------


def _make_builder(page_cls):
    def build(window) -> Gtk.Widget:
        return page_cls(window).widget

    return build


SINGLE_INPUT_BUILDERS = {
    cls.KIND: _make_builder(cls)
    for cls in (
        DocumentPage,
        SubtitlePage,
        SubtitleExtractPage,
        OcrPage,
        EbookPage,
        QrPage,
        SvgPage,
        PdfNumberingPage,
        PdfSplitPage,
        PdfExtractImagesPage,
        PdfExtractAttachmentsPage,
        SlidesToImagesPage,
        ArchivePage,
        ArchiveCompressPage,
        MetadataPage,
    )
}
