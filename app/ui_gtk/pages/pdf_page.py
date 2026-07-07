"""PDF Tools page — full parity with the old Qt 6-tab PDF panel.

The old panel used six mutually-exclusive tabs (Pages, Security, Compress,
Watermark, Redact, Metadata); the active tab decided the operation. That
maps cleanly to a single **Operation** picker whose choice reveals just
the parameters that operation needs — the rest stay hidden (house style
§7.1: never show a control that doesn't apply).

Option keys, defaults, and the soft-exclusive watermark rule (image path
present → image watermark, else text) mirror ``pdf_operations.py`` exactly
(feature-map §C-PDF).
"""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gtk

from app.core.settings import get_settings
from app.ui_gtk.widgets.destination_row import DestinationRow
from app.ui_gtk.widgets.dropzone import DropZone
from app.ui_gtk.widgets.page_scaffold import PageScaffold
from app.ui_gtk.widgets.preset_bar import PresetBar
from app.ui_gtk.widgets.rows import ChoiceRow, attach_file_browse, spin_row

KIND = "pdf"

# Operation picker — flattened from the six old tabs. "watermark" is a UI
# token resolved to watermark_image / watermark_text at collect time;
# "convert" is a UI token for the engine's format conversions (pdf→image/
# text/document), which the old registry-driven format combo exposed.
OPERATIONS = (
    ("Convert to another format", "convert"),
    ("Extract pages", "extract_pages"),
    ("Reorder pages", "reorder"),
    ("Rotate pages", "rotate"),
    ("Encrypt", "encrypt"),
    ("Decrypt", "decrypt"),
    ("Compress", "compress"),
    ("Compress images", "compress_images"),
    ("Linearize (web-fast)", "linearize"),
    ("Repair", "repair"),
    ("Watermark", "watermark"),
    ("Redact", "redact"),
    ("Strip metadata", "strip_metadata"),
    ("Edit metadata", "edit_metadata"),
)

ROTATIONS = (("90° CW", 90), ("180°", 180), ("270° (90° CCW)", 270))
GRAVITIES = (
    ("Top-left", "northwest"), ("Top", "north"), ("Top-right", "northeast"),
    ("Left", "west"), ("Center", "center"), ("Right", "east"),
    ("Bottom-left", "southwest"), ("Bottom", "south"),
    ("Bottom-right", "southeast"),
)
REDACT_COLORS = (
    ("Black", "black"), ("White", "white"), ("Red", "red"), ("Yellow", "yellow"),
)

# Non-PDF outputs the pdf engine can produce (SUPPORTED_PAIRS, sans folder).
CONVERT_FORMATS = (
    ("PNG (one image per page)", "png"),
    ("JPG (one image per page)", "jpg"),
    ("Text (.txt)", "txt"),
    ("HTML", "html"),
    ("Word (.docx)", "docx"),
    ("EPUB", "epub"),
)
_CONVERT_IMAGE_FORMATS = {"png", "jpg", "jpeg"}

# Which parameter rows each operation reveals.
_VISIBILITY = {
    "convert": {"convert_format", "convert_dpi", "pages"},
    "extract_pages": {"pages"},
    "reorder": {"pages"},
    "rotate": {"pages", "rotation"},
    "encrypt": {"password_user", "password_owner"},
    "decrypt": {"password"},
    "compress": set(),
    "compress_images": {"dpi", "quality"},
    "linearize": set(),
    "repair": set(),
    "watermark": {
        "wm_text", "wm_image", "wm_position", "wm_size",
        "wm_image_width", "wm_opacity",
    },
    "redact": {"redact_terms", "redact_color", "redact_pages"},
    "strip_metadata": set(),
    "edit_metadata": {
        "meta_title", "meta_author", "meta_subject",
        "meta_keywords", "meta_creator",
    },
}


class PdfPage:
    def __init__(self, window) -> None:
        self._window = window

        # --- File ---------------------------------------------------------
        self.dropzone = DropZone(
            self._on_file_changed,
            icon="drop-pdf",
            empty_title="Drop a PDF here or click to choose",
            empty_subtitle="PDF",
        )
        file_group = Adw.PreferencesGroup(title="File")
        file_group.add(self.dropzone)

        # --- Output + Operation picker -------------------------------------
        # The format row mirrors the operation: PDF for the tools, the
        # chosen target for "Convert to another format".
        output_group = Adw.PreferencesGroup(title="Output")
        self._format_row = Adw.ActionRow(title="Format")
        self._format_row.set_subtitle("PDF")
        self._format_row.set_activatable(False)
        output_group.add(self._format_row)
        self.destination = DestinationRow(initial=_default_output_dir())
        output_group.add(self.destination.row)

        self.operation = ChoiceRow("Operation", OPERATIONS, "extract_pages")
        self.operation.row.set_subtitle("What to do with the PDF")
        output_group.add(self.operation.row)
        self.operation.row.connect("notify::selected", self._sync_visibility)

        # --- Parameters (visibility-toggled per operation) ----------------
        self._params = Adw.PreferencesGroup(title="Parameters")
        self._rows: dict[str, Gtk.Widget] = {}
        self._build_params()

        # --- Footer -------------------------------------------------------
        preset_bar = PresetBar(
            kind=KIND,
            get_options=self.collect_options,
            apply_options=self.apply_options,
            toast=window.show_toast,
        )
        self.scaffold = PageScaffold(
            on_convert=self._on_convert,
            on_add_to_queue=self._on_add_to_queue,
            preset_bar=preset_bar,
        )
        self.scaffold.add_group(file_group)
        self.scaffold.add_group(output_group)
        self.scaffold.add_group(self._params)

        self.widget = self.scaffold
        self._sync_visibility()

    # -- parameter rows ----------------------------------------------------

    def _build_params(self) -> None:
        self.pages = Adw.EntryRow(title="Pages — 1-3,5,8-10 (blank = all)")
        self.rotation = ChoiceRow("Rotation", ROTATIONS, 90)

        self.convert_format = ChoiceRow("Convert to", CONVERT_FORMATS, "png")
        self.convert_format.row.connect(
            "notify::selected", self._sync_visibility
        )
        self.convert_dpi = spin_row(
            "Render DPI", 72, 600, get_settings().default_pdf_dpi
        )

        self.password_user = Adw.PasswordEntryRow(title="User password")
        self.password_owner = Adw.PasswordEntryRow(title="Owner password")
        self.password = Adw.PasswordEntryRow(title="Password")

        self.dpi = spin_row("Target DPI", 36, 600, 150)
        self.quality = spin_row("JPEG quality", 1, 100, 75)

        self.wm_text = Adw.EntryRow(title="Text — e.g. CONFIDENTIAL")
        self.wm_image = Adw.EntryRow(title="Image (blank = text watermark)")
        attach_file_browse(self.wm_image, self._root_window, title="Choose image")
        self.wm_position = ChoiceRow("Position", GRAVITIES, "center")
        self.wm_size = spin_row("Text size (pt)", 8, 200, 48)
        self.wm_image_width = spin_row("Image width (% page)", 5, 100, 25)
        self.wm_opacity = spin_row("Opacity (%)", 5, 100, 35)

        self.redact_terms = Adw.EntryRow(title="Search terms — comma-separated")
        self.redact_color = ChoiceRow("Fill color", REDACT_COLORS, "black")
        self.redact_pages = Adw.EntryRow(title="Pages — 1-3,5 (blank = all)")

        self.meta_title = Adw.EntryRow(title="Title")
        self.meta_author = Adw.EntryRow(title="Author")
        self.meta_subject = Adw.EntryRow(title="Subject")
        self.meta_keywords = Adw.EntryRow(title="Keywords")
        self.meta_creator = Adw.EntryRow(title="Creator")

        self._rows = {
            "convert_format": self.convert_format.row,
            "convert_dpi": self.convert_dpi,
            "pages": self.pages,
            "rotation": self.rotation.row,
            "password_user": self.password_user,
            "password_owner": self.password_owner,
            "password": self.password,
            "dpi": self.dpi,
            "quality": self.quality,
            "wm_text": self.wm_text,
            "wm_image": self.wm_image,
            "wm_position": self.wm_position.row,
            "wm_size": self.wm_size,
            "wm_image_width": self.wm_image_width,
            "wm_opacity": self.wm_opacity,
            "redact_terms": self.redact_terms,
            "redact_color": self.redact_color.row,
            "redact_pages": self.redact_pages,
            "meta_title": self.meta_title,
            "meta_author": self.meta_author,
            "meta_subject": self.meta_subject,
            "meta_keywords": self.meta_keywords,
            "meta_creator": self.meta_creator,
        }
        for row in self._rows.values():
            self._params.add(row)

    def _sync_visibility(self, *_args) -> None:
        op = self.operation.get_value()
        visible = set(_VISIBILITY.get(op, set()))
        if op == "convert":
            fmt = self.convert_format.get_value()
            if fmt not in _CONVERT_IMAGE_FORMATS:
                visible.discard("convert_dpi")  # DPI only applies to images
            self._format_row.set_subtitle(fmt.upper())
        else:
            self._format_row.set_subtitle("PDF")
        for key, row in self._rows.items():
            row.set_visible(key in visible)
        # The Parameters group is empty for operations with no inputs.
        self._params.set_visible(bool(visible))

    def _root_window(self) -> Gtk.Window | None:
        return self._window if isinstance(self._window, Gtk.Window) else None

    # -- options -----------------------------------------------------------

    def collect_options(self) -> dict:
        op = self.operation.get_value()
        opts: dict[str, object] = {"category": KIND, "format_out": "pdf"}

        if op == "convert":
            # Plain format conversion: the engine dispatches on format_out
            # alone, no operation key.
            fmt = self.convert_format.get_value()
            opts["format_out"] = fmt
            if fmt in _CONVERT_IMAGE_FORMATS:
                opts["dpi"] = int(self.convert_dpi.get_value())
            pages = self.pages.get_text().strip()
            if pages:
                opts["pages"] = pages
            return opts

        if op == "watermark":
            return self._collect_watermark(opts)

        opts["operation"] = op
        if op in ("extract_pages", "reorder", "rotate"):
            pages = self.pages.get_text().strip()
            if pages:
                opts["pages"] = pages
            if op == "rotate":
                opts["rotation_degrees"] = self.rotation.get_value()
        elif op == "encrypt":
            if self.password_user.get_text():
                opts["password_user"] = self.password_user.get_text()
            if self.password_owner.get_text():
                opts["password_owner"] = self.password_owner.get_text()
        elif op == "decrypt":
            if self.password.get_text():
                opts["password"] = self.password.get_text()
        elif op == "compress_images":
            opts["compress_images_target_dpi"] = int(self.dpi.get_value())
            opts["compress_images_quality"] = int(self.quality.get_value())
        elif op == "redact":
            opts["redact_terms"] = self.redact_terms.get_text().strip()
            opts["redact_color"] = self.redact_color.get_value()
            pages = self.redact_pages.get_text().strip()
            if pages:
                opts["pages"] = pages
        elif op == "edit_metadata":
            for key, entry in self._meta_entries():
                value = entry.get_text().strip()
                if value:
                    opts[key] = value
        return opts

    def _collect_watermark(self, opts: dict) -> dict:
        text = self.wm_text.get_text().strip()
        image = self.wm_image.get_text().strip()
        position = self.wm_position.get_value()
        opacity = int(self.wm_opacity.get_value())
        if image:
            opts["operation"] = "watermark_image"
            opts["watermark_image_path"] = image
            opts["watermark_position"] = position
            opts["watermark_image_width_fraction"] = round(
                self.wm_image_width.get_value() / 100.0, 4
            )
            opts["watermark_opacity"] = opacity
            if text:
                opts["watermark_text"] = text
        else:
            opts["operation"] = "watermark_text"
            if text:
                opts["watermark_text"] = text
                opts["watermark_position"] = position
                opts["watermark_size"] = int(self.wm_size.get_value())
                opts["watermark_opacity"] = opacity
        return opts

    def _meta_entries(self):
        return (
            ("meta_title", self.meta_title),
            ("meta_author", self.meta_author),
            ("meta_subject", self.meta_subject),
            ("meta_keywords", self.meta_keywords),
            ("meta_creator", self.meta_creator),
        )

    def apply_options(self, payload: dict) -> None:
        """Restore the exact state a preset was saved from.

        Every field resets to its build-time default when its key is
        absent, so a loaded preset can't inherit stale values (e.g. a
        leftover page range) from whatever was configured before.
        """
        fmt = str(payload.get("format_out", "pdf")).lower()
        if "operation" in payload:
            op = str(payload["operation"])
        elif fmt != "pdf":
            op = "convert"  # plain conversion presets carry no operation key
        else:
            op = "extract_pages"

        # Convert fields.
        self.convert_format.set_value(fmt if fmt != "pdf" else "png")
        self.convert_dpi.set_value(_as_int(
            payload.get("dpi", get_settings().default_pdf_dpi),
            get_settings().default_pdf_dpi,
        ))

        # Watermark fields (shared by text/image variants).
        self.wm_image.set_text(str(payload.get("watermark_image_path", "")))
        self.wm_text.set_text(str(payload.get("watermark_text", "")))
        self.wm_position.set_value(str(payload.get("watermark_position", "center")))
        self.wm_size.set_value(_as_int(payload.get("watermark_size", 48), 48))
        self.wm_image_width.set_value(round(_as_float(
            payload.get("watermark_image_width_fraction", 0.25), 0.25
        ) * 100))
        self.wm_opacity.set_value(_as_int(payload.get("watermark_opacity", 35), 35))

        # Everything else, reset-or-restore.
        pages = str(payload.get("pages", ""))
        self.pages.set_text(pages)
        self.redact_pages.set_text(pages)
        self.rotation.set_value(_as_int(payload.get("rotation_degrees", 90), 90))
        self.password_user.set_text(str(payload.get("password_user", "")))
        self.password_owner.set_text(str(payload.get("password_owner", "")))
        self.password.set_text(str(payload.get("password", "")))
        self.dpi.set_value(_as_int(payload.get("compress_images_target_dpi", 150), 150))
        self.quality.set_value(_as_int(payload.get("compress_images_quality", 75), 75))
        self.redact_terms.set_text(str(payload.get("redact_terms", "")))
        self.redact_color.set_value(str(payload.get("redact_color", "black")))
        for key, entry in self._meta_entries():
            entry.set_text(str(payload.get(key, "")))

        if op in ("watermark_image", "watermark_text"):
            self.operation.set_value("watermark")
        else:
            self.operation.set_value(op)
        self._sync_visibility()

    # -- actions -----------------------------------------------------------

    def _on_file_changed(self, _path: Path | None) -> None:
        pass

    def _require_file(self) -> bool:
        if self.dropzone.path is None:
            self._window.show_toast("Choose a PDF first.")
            return False
        return True

    def _on_convert(self) -> None:
        self._enqueue(switch=True)

    def _on_add_to_queue(self) -> None:
        self._enqueue(switch=False)

    def _enqueue(self, *, switch: bool) -> None:
        if not self._require_file():
            return
        options = self.collect_options()
        fmt = options.pop("format_out", None)
        self._window.enqueue(
            KIND, self.dropzone.path,
            output_dir=self.destination.directory,
            format_out=fmt, options=options, switch_to_queue=switch,
        )


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


def build_pdf_page(window) -> Gtk.Widget:
    return PdfPage(window).widget
