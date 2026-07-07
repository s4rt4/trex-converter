"""Image converter page — full parity with the old Qt Image page.

Anatomy (house style §6): File (rich drop zone) → Output (format chips ·
destination · quality slider · remove-metadata) → Transform (operations
checklist) → footer (presets · Add to queue · Convert).

Every control from the old 5-tab ``ImageOptionsPanel`` is preserved,
reorganised into six operation rows. See `feature-map-old-ui` §C-Image /
§F for the control-to-key mapping; option emission mirrors the old
"emit only when changed/non-empty" rule, additionally gated by each
operation's enable switch.

Convert / Add to queue submit through ``window.enqueue`` to the shared
TaskQueue (see app.ui_gtk.backend).
"""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gtk

from app.core.settings import get_settings
from app.ui_gtk.formats import picker_args
from app.ui_gtk.widgets.destination_row import DestinationRow
from app.ui_gtk.widgets.dropzone import DropZone
from app.ui_gtk.widgets.format_picker import FormatPicker
from app.ui_gtk.widgets.operations import OperationRow, OperationsGroup
from app.ui_gtk.widgets.page_scaffold import PageScaffold
from app.ui_gtk.widgets.preset_bar import PresetBar
from app.ui_gtk.widgets.quality_row import QualityRow
from app.ui_gtk.widgets.rows import ChoiceRow, attach_file_browse, spin_row

KIND = "image"

OUTPUT_FORMATS = (
    "png", "jpg", "webp", "avif", "heic", "gif", "bmp", "tiff", "ico", "pdf",
)
COMMON_FORMATS = ("png", "jpg", "webp", "avif", "gif")
DEFAULT_FORMAT = "webp"

ROTATIONS = (("0°", 0), ("90° CW", 90), ("180°", 180), ("90° CCW", -90))
ASPECTS = (
    ("Free", "free"), ("Square 1:1", "1:1"), ("Portrait 4:5", "4:5"),
    ("Portrait 2:3", "2:3"), ("Portrait 9:16", "9:16"),
    ("Landscape 3:2", "3:2"), ("Landscape 16:9", "16:9"),
    ("Landscape 4:3", "4:3"),
)
RESIZE_MODES = (
    ("Dimension (e.g. 1280x720>)", "dimension"),
    ("Longest edge (px)", "longest_edge"),
    ("Percent (%)", "percent"),
    ("Megapixel target", "megapixel"),
)
RESIZE_PLACEHOLDERS = {
    "dimension": "1280x1280>", "longest_edge": "1024",
    "percent": "75", "megapixel": "2.0",
}
GRAVITIES = (
    ("Top-left", "northwest"), ("Top", "north"), ("Top-right", "northeast"),
    ("Left", "west"), ("Center", "center"), ("Right", "east"),
    ("Bottom-left", "southwest"), ("Bottom", "south"),
    ("Bottom-right", "southeast"),
)


class ImagePage:
    def __init__(self, window) -> None:
        self._window = window

        # --- File ---------------------------------------------------------
        self.dropzone = DropZone(
            self._on_file_changed,
            icon="drop-image",
            empty_title="Drop an image here or click to choose",
            empty_subtitle="PNG, JPEG, WebP, AVIF, HEIC, GIF, TIFF, BMP, ICO, PDF",
        )
        file_group = Adw.PreferencesGroup(title="File")
        file_group.add(self.dropzone)

        # --- Output -------------------------------------------------------
        self.format_picker = FormatPicker(
            **picker_args(KIND, OUTPUT_FORMATS, common=COMMON_FORMATS,
                          default=DEFAULT_FORMAT),
            title="Format",
        )
        self.destination = DestinationRow(initial=_default_output_dir())
        self.quality = QualityRow(
            default=get_settings().default_image_quality,
        )
        self.strip_row = Adw.SwitchRow(
            title="Remove metadata",
            subtitle="Strip EXIF and other embedded data",
            active=True,  # the Qt app shipped with strip on; keep that default
        )
        output_group = Adw.PreferencesGroup(title="Output")
        output_group.add(self.format_picker.row)
        output_group.add(self.destination.row)
        output_group.add(self.quality.row)
        output_group.add(self.strip_row)

        # --- Transform (operations checklist) -----------------------------
        self.operations = OperationsGroup(title="Transform")
        self._build_operations()

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
        self.scaffold.add_group(self.operations.group)

        self.widget = self.scaffold
        self._refresh_summaries()

    # -- operations build --------------------------------------------------

    def _build_operations(self) -> None:
        self.op_rotate = OperationRow(
            icon="rotate", title="Rotate & flip", description="Rotate or mirror"
        )
        self.rotate = ChoiceRow("Rotate", ROTATIONS, 0)
        self.flip_v = Adw.SwitchRow(title="Flip vertical")
        self.flip_h = Adw.SwitchRow(title="Flip horizontal")
        for control in (self.rotate.row, self.flip_v, self.flip_h):
            self._add(self.op_rotate, control)

        self.op_resize = OperationRow(
            icon="resize", title="Resize & crop",
            description="Dimensions, cropping and canvas",
        )
        self.resize_mode = ChoiceRow("Resize mode", RESIZE_MODES, "dimension")
        self.resize_mode.row.connect("notify::selected", self._on_resize_mode)
        self.resize_value = Adw.EntryRow(title="Resize value")
        self.aspect = ChoiceRow("Aspect crop", ASPECTS, "free")
        self.crop_free = Adw.EntryRow(title="Free crop")
        self.auto_trim = Adw.SwitchRow(title="Auto-trim borders")
        self.density = spin_row("Density (dpi, 0 = default)", 0, 1200, 0)
        self.fit_canvas = Adw.EntryRow(title="Fit canvas")
        self.fit_canvas_bg = Adw.EntryRow(title="Canvas background")
        for control in (
            self.resize_mode.row, self.resize_value, self.aspect.row,
            self.crop_free, self.auto_trim, self.density,
            self.fit_canvas, self.fit_canvas_bg,
        ):
            self._add(self.op_resize, control)
        self._on_resize_mode()

        self.op_color = OperationRow(
            icon="color", title="Color", description="Tone and adjustments"
        )
        self.grayscale = Adw.SwitchRow(title="Grayscale")
        self.negate = Adw.SwitchRow(title="Negate (invert)")
        self.normalize = Adw.SwitchRow(title="Normalize histogram")
        self.sepia = spin_row("Sepia (%)", 0, 100, 0)
        self.brightness = spin_row("Brightness", -100, 100, 0)
        self.contrast = spin_row("Contrast", -100, 100, 0)
        self.gamma = spin_row("Gamma", 0.1, 5.0, 1.0, step=0.1, digits=2)
        for control in (
            self.grayscale, self.negate, self.normalize, self.sepia,
            self.brightness, self.contrast, self.gamma,
        ):
            self._add(self.op_color, control)

        self.op_filter = OperationRow(
            icon="filter", title="Filter", description="Blur, sharpen, denoise"
        )
        self.blur = spin_row("Blur sigma", 0.0, 20.0, 0.0, step=0.5, digits=1)
        self.sharpen = spin_row("Sharpen sigma", 0.0, 10.0, 0.0, step=0.5, digits=1)
        self.denoise = Adw.SwitchRow(title="Denoise")
        self.vignette = Adw.SwitchRow(title="Vignette")
        for control in (self.blur, self.sharpen, self.denoise, self.vignette):
            self._add(self.op_filter, control)

        self.op_border = OperationRow(
            icon="border", title="Border", description="Frame and padding"
        )
        self.border_size = spin_row("Border size (px)", 0, 200, 0)
        self.border_color = Adw.EntryRow(title="Border color")
        self.frame_size = spin_row("Frame size (px)", 0, 200, 0)
        for control in (self.border_size, self.border_color, self.frame_size):
            self._add(self.op_border, control)

        self.op_watermark = OperationRow(
            icon="watermark", title="Watermark", description="Text or image overlay"
        )
        self.wm_text = Adw.EntryRow(title="Text")
        self.wm_position = ChoiceRow("Position", GRAVITIES, "southeast")
        self.wm_size = spin_row("Text size (pt)", 8, 200, 36)
        self.wm_opacity = spin_row("Opacity (%)", 0, 100, 60)
        self.wm_image = Adw.EntryRow(title="Image path")
        attach_file_browse(
            self.wm_image, self._root_window, title="Choose watermark image"
        )
        self.wm_image_width = spin_row("Image width (px, 0 = source)", 0, 4096, 0)
        for control in (
            self.wm_text, self.wm_position.row, self.wm_size, self.wm_opacity,
            self.wm_image, self.wm_image_width,
        ):
            self._add(self.op_watermark, control)

        for op in (
            self.op_rotate, self.op_resize, self.op_color,
            self.op_filter, self.op_border, self.op_watermark,
        ):
            op.on_toggle = self._refresh_summaries
            self.operations.add_operation(op)

    def _add(self, op: OperationRow, control: Gtk.Widget) -> None:
        op.add(control)
        self._wire(control)

    def _wire(self, control: Gtk.Widget) -> None:
        refresh = lambda *_a: self._refresh_summaries()
        if isinstance(control, Adw.SpinRow):
            control.get_adjustment().connect("value-changed", refresh)
        elif isinstance(control, Adw.ComboRow):
            control.connect("notify::selected", refresh)
        elif isinstance(control, Adw.EntryRow):
            control.connect("changed", refresh)
        elif isinstance(control, Adw.SwitchRow):
            control.connect("notify::active", refresh)

    def _root_window(self) -> Gtk.Window | None:
        return self._window if isinstance(self._window, Gtk.Window) else None

    def _on_resize_mode(self, *_args) -> None:
        placeholder = RESIZE_PLACEHOLDERS.get(self.resize_mode.get_value(), "")
        # AdwEntryRow has no placeholder API; reflect the hint in the title.
        self.resize_value.set_title(f"Resize value — e.g. {placeholder}")

    # -- summaries ---------------------------------------------------------

    def _refresh_summaries(self, *_args) -> None:
        self.op_rotate.set_summary(self._summary_rotate())
        self.op_resize.set_summary(self._summary_resize())
        self.op_color.set_summary(self._summary_color())
        self.op_filter.set_summary(self._summary_filter())
        self.op_border.set_summary(self._summary_border())
        self.op_watermark.set_summary(self._summary_watermark())

    def _summary_rotate(self) -> str | None:
        parts = []
        rotation = self.rotate.get_value()
        if rotation:
            parts.append(dict(ROTATIONS).get(rotation, f"{rotation}°"))
        if self.flip_v.get_active():
            parts.append("Flip V")
        if self.flip_h.get_active():
            parts.append("Flip H")
        return " · ".join(parts) or None

    def _summary_resize(self) -> str | None:
        value = self.resize_value.get_text().strip()
        if value:
            return f"{self.resize_mode.get_value()}: {value}"
        if self.aspect.get_value() != "free":
            return f"Crop {self.aspect.get_value()}"
        if self.crop_free.get_text().strip():
            return "Custom crop"
        if self.fit_canvas.get_text().strip():
            return f"Fit {self.fit_canvas.get_text().strip()}"
        if self.density.get_value() > 0:
            return f"{int(self.density.get_value())} dpi"
        if self.auto_trim.get_active():
            return "Auto-trim"
        return None

    def _summary_color(self) -> str | None:
        parts = []
        if self.grayscale.get_active():
            parts.append("Grayscale")
        if self.negate.get_active():
            parts.append("Negate")
        if self.normalize.get_active():
            parts.append("Normalize")
        if self.sepia.get_value() > 0:
            parts.append(f"Sepia {int(self.sepia.get_value())}%")
        if self.brightness.get_value():
            parts.append(f"B{int(self.brightness.get_value()):+d}")
        if self.contrast.get_value():
            parts.append(f"C{int(self.contrast.get_value()):+d}")
        if abs(self.gamma.get_value() - 1.0) > 1e-3:
            parts.append(f"γ{self.gamma.get_value():.1f}")
        return " · ".join(parts) or None

    def _summary_filter(self) -> str | None:
        parts = []
        if self.blur.get_value() > 0:
            parts.append(f"Blur {self.blur.get_value():.1f}")
        if self.sharpen.get_value() > 0:
            parts.append(f"Sharpen {self.sharpen.get_value():.1f}")
        if self.denoise.get_active():
            parts.append("Denoise")
        if self.vignette.get_active():
            parts.append("Vignette")
        return " · ".join(parts) or None

    def _summary_border(self) -> str | None:
        parts = []
        if self.border_size.get_value() > 0:
            color = self.border_color.get_text().strip() or "black"
            parts.append(f"Border {int(self.border_size.get_value())}px {color}")
        if self.frame_size.get_value() > 0:
            parts.append(f"Frame {int(self.frame_size.get_value())}px")
        return " · ".join(parts) or None

    def _summary_watermark(self) -> str | None:
        text = self.wm_text.get_text().strip()
        if text:
            return f"“{text}”"
        if self.wm_image.get_text().strip():
            return "Image overlay"
        return None

    # -- options -----------------------------------------------------------

    def collect_options(self) -> dict:
        opts: dict[str, object] = {
            "category": KIND,
            "format_out": self.format_picker.get_format(),
            "quality": self.quality.get_value(),
            "strip": self.strip_row.get_active(),
        }

        if self.op_rotate.enabled:
            if self.rotate.get_value():
                opts["rotate"] = self.rotate.get_value()
            if self.flip_v.get_active():
                opts["flip"] = True
            if self.flip_h.get_active():
                opts["flop"] = True

        if self.op_resize.enabled:
            if self.auto_trim.get_active():
                opts["auto_trim"] = True
            if self.aspect.get_value() != "free":
                opts["crop_aspect"] = self.aspect.get_value()
            crop = self.crop_free.get_text().strip()
            if crop:
                opts["crop"] = crop
            value = self.resize_value.get_text().strip()
            if value:
                opts["resize"] = value
                opts["resize_mode"] = self.resize_mode.get_value()
            if self.density.get_value() > 0:
                opts["density"] = int(self.density.get_value())
            fit = self.fit_canvas.get_text().strip()
            if fit:
                opts["fit_canvas"] = fit
                bg = self.fit_canvas_bg.get_text().strip()
                if bg:
                    opts["fit_canvas_background"] = bg

        if self.op_color.enabled:
            if self.grayscale.get_active():
                opts["grayscale"] = True
            if self.negate.get_active():
                opts["negate"] = True
            if self.normalize.get_active():
                opts["normalize"] = True
            if self.sepia.get_value() > 0:
                opts["sepia"] = int(self.sepia.get_value())
            if self.brightness.get_value():
                opts["brightness"] = int(self.brightness.get_value())
            if self.contrast.get_value():
                opts["contrast"] = int(self.contrast.get_value())
            if abs(self.gamma.get_value() - 1.0) > 1e-3:
                opts["gamma"] = round(self.gamma.get_value(), 3)

        if self.op_filter.enabled:
            if self.blur.get_value() > 0:
                opts["blur"] = round(self.blur.get_value(), 3)
            if self.sharpen.get_value() > 0:
                opts["sharpen"] = round(self.sharpen.get_value(), 3)
            if self.denoise.get_active():
                opts["denoise"] = True
            if self.vignette.get_active():
                opts["vignette"] = True

        if self.op_border.enabled:
            if self.border_size.get_value() > 0:
                opts["border_size"] = int(self.border_size.get_value())
                color = self.border_color.get_text().strip()
                if color:
                    opts["border_color"] = color
            if self.frame_size.get_value() > 0:
                opts["frame_size"] = int(self.frame_size.get_value())

        if self.op_watermark.enabled:
            text = self.wm_text.get_text().strip()
            position = self.wm_position.get_value()
            opacity = int(self.wm_opacity.get_value())
            if text:
                opts["watermark_text"] = text
                opts["watermark_position"] = position
                opts["watermark_opacity"] = opacity
                opts["watermark_size"] = int(self.wm_size.get_value())
            image = self.wm_image.get_text().strip()
            if image:
                opts["watermark_image_path"] = image
                opts["watermark_image_position"] = position
                opts["watermark_image_opacity"] = opacity
                if self.wm_image_width.get_value() > 0:
                    opts["watermark_image_width"] = int(
                        self.wm_image_width.get_value()
                    )

        return opts

    def apply_options(self, payload: dict) -> None:
        """Restore the exact state a preset was saved from.

        Every control is reset to its default when its key is absent, and
        every operation is enabled *iff* the payload carries one of its
        keys — loading a preset must never leave a previously configured
        operation active on top of it.
        """
        self.format_picker.set_format(str(payload.get("format_out", DEFAULT_FORMAT)))
        self.quality.set_value(_as_int(
            payload.get("quality", get_settings().default_image_quality),
            get_settings().default_image_quality,
        ))
        self.strip_row.set_active(bool(payload.get("strip", True)))

        rotate_keys = {"rotate", "flip", "flop"}
        self.op_rotate.row.set_enable_expansion(bool(rotate_keys & payload.keys()))
        self.rotate.set_value(_as_int(payload.get("rotate", 0), 0))
        self.flip_v.set_active(bool(payload.get("flip")))
        self.flip_h.set_active(bool(payload.get("flop")))

        resize_keys = {
            "auto_trim", "crop_aspect", "crop", "resize", "resize_mode",
            "density", "fit_canvas", "fit_canvas_background",
        }
        self.op_resize.row.set_enable_expansion(bool(resize_keys & payload.keys()))
        self.auto_trim.set_active(bool(payload.get("auto_trim")))
        self.aspect.set_value(str(payload.get("crop_aspect", "free")))
        self.crop_free.set_text(str(payload.get("crop", "")))
        self.resize_mode.set_value(str(payload.get("resize_mode", "dimension")))
        self.resize_value.set_text(str(payload.get("resize", "")))
        self.density.set_value(_as_int(payload.get("density", 0), 0))
        self.fit_canvas.set_text(str(payload.get("fit_canvas", "")))
        self.fit_canvas_bg.set_text(str(payload.get("fit_canvas_background", "")))

        color_keys = {
            "grayscale", "negate", "normalize", "sepia",
            "brightness", "contrast", "gamma",
        }
        self.op_color.row.set_enable_expansion(bool(color_keys & payload.keys()))
        self.grayscale.set_active(bool(payload.get("grayscale")))
        self.negate.set_active(bool(payload.get("negate")))
        self.normalize.set_active(bool(payload.get("normalize")))
        self.sepia.set_value(_as_int(payload.get("sepia", 0), 0))
        self.brightness.set_value(_as_int(payload.get("brightness", 0), 0))
        self.contrast.set_value(_as_int(payload.get("contrast", 0), 0))
        self.gamma.set_value(_as_float(payload.get("gamma", 1.0), 1.0))

        filter_keys = {"blur", "sharpen", "denoise", "vignette"}
        self.op_filter.row.set_enable_expansion(bool(filter_keys & payload.keys()))
        self.blur.set_value(_as_float(payload.get("blur", 0.0), 0.0))
        self.sharpen.set_value(_as_float(payload.get("sharpen", 0.0), 0.0))
        self.denoise.set_active(bool(payload.get("denoise")))
        self.vignette.set_active(bool(payload.get("vignette")))

        border_keys = {"border_size", "border_color", "frame_size"}
        self.op_border.row.set_enable_expansion(bool(border_keys & payload.keys()))
        self.border_size.set_value(_as_int(payload.get("border_size", 0), 0))
        self.border_color.set_text(str(payload.get("border_color", "")))
        self.frame_size.set_value(_as_int(payload.get("frame_size", 0), 0))

        watermark_keys = {
            "watermark_text", "watermark_position", "watermark_opacity",
            "watermark_size", "watermark_image_path", "watermark_image_width",
            "watermark_image_position", "watermark_image_opacity",
        }
        self.op_watermark.row.set_enable_expansion(bool(watermark_keys & payload.keys()))
        self.wm_text.set_text(str(payload.get("watermark_text", "")))
        # Position/opacity are shared controls; an image-only watermark
        # stores them under the watermark_image_* keys.
        position = payload.get(
            "watermark_position", payload.get("watermark_image_position", "southeast")
        )
        opacity = payload.get(
            "watermark_opacity", payload.get("watermark_image_opacity", 60)
        )
        self.wm_position.set_value(str(position))
        self.wm_opacity.set_value(_as_int(opacity, 60))
        self.wm_size.set_value(_as_int(payload.get("watermark_size", 36), 36))
        self.wm_image.set_text(str(payload.get("watermark_image_path", "")))
        self.wm_image_width.set_value(_as_int(payload.get("watermark_image_width", 0), 0))

        self._refresh_summaries()

    # -- actions -----------------------------------------------------------

    def _on_file_changed(self, _path: Path | None) -> None:
        pass

    def _require_file(self) -> bool:
        if self.dropzone.path is None:
            self._window.show_toast("Choose an image first.")
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


def build_image_page(window) -> Gtk.Widget:
    """Builder used by the window's destination registry."""
    return ImagePage(window).widget
