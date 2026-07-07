"""Video converter page — full parity with the old Qt Video page.

Anatomy (house style §6): File (drop zone) → Output (format chips ·
destination · audio-bitrate chips) → Operations (9-row checklist) →
footer (presets · Add to queue · Convert).

Every control from the old 9-tab ``VideoOptionsPanel`` is preserved as
an operation row (see `feature-map-old-ui` §C-Video). Option emission
mirrors the old "emit only when changed/non-empty" rule, gated by each
operation's enable switch. Convert / Add to queue validate input but are
not wired to the engine until the Queue step.
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
from app.ui_gtk.widgets.rows import (
    ChoiceRow,
    attach_file_browse,
    spin_row,
    wire_change,
)

KIND = "video"

OUTPUT_FORMATS = ("mp4", "mkv", "webm", "mov", "gif", "webp", "png", "jpg")
COMMON_FORMATS = ("mp4", "mkv", "webm", "mov", "gif")
DEFAULT_FORMAT = "mp4"

AUDIO_BITRATES = ("128k", "192k", "256k", "320k")
DEFAULT_BITRATE = "192k"

ROTATIONS = (("0°", 0), ("90° CW", 90), ("180°", 180), ("90° CCW (270°)", 270))
RES_PRESETS = (
    ("Source", ""), ("4K (3840w)", "4k"), ("1440p (2560w)", "1440p"),
    ("1080p (1920w)", "1080p"), ("720p (1280w)", "720p"),
    ("480p (854w)", "480p"), ("360p (640w)", "360p"),
)
COMPRESS_PRESETS = tuple(
    (p, p) for p in (
        "ultrafast", "superfast", "veryfast", "faster", "fast",
        "medium", "slow", "slower", "veryslow",
    )
)
GRAVITIES = (
    ("Top-left", "northwest"), ("Top", "north"), ("Top-right", "northeast"),
    ("Left", "west"), ("Center", "center"), ("Right", "east"),
    ("Bottom-left", "southwest"), ("Bottom", "south"),
    ("Bottom-right", "southeast"),
)


class VideoPage:
    def __init__(self, window) -> None:
        self._window = window
        settings = get_settings()

        # --- File ---------------------------------------------------------
        self.dropzone = DropZone(
            self._on_file_changed,
            icon="drop-video",
            empty_title="Drop a video here or click to choose",
            empty_subtitle="MP4, MOV, MKV, WebM",
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
        self.audio_bitrate = FormatPicker(
            AUDIO_BITRATES, default=DEFAULT_BITRATE,
            title="Audio bitrate", uppercase=False,
        )
        output_group = Adw.PreferencesGroup(title="Output")
        output_group.add(self.format_picker.row)
        output_group.add(self.destination.row)
        output_group.add(self.audio_bitrate.row)

        # --- Operations ---------------------------------------------------
        self.operations = OperationsGroup(title="Operations")
        self._build_operations(settings)

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

    def _build_operations(self, settings) -> None:
        self.op_trim = OperationRow(
            icon="trim", title="Trim", description="Cut a section"
        )
        self.trim_start = Adw.EntryRow(title="Start — e.g. 00:00:10")
        self.trim_end = Adw.EntryRow(title="End — e.g. 00:01:30")
        self.stream_copy = Adw.SwitchRow(
            title="Stream copy",
            subtitle="No re-encode — fastest, may misalign on non-keyframe cuts",
        )
        for c in (self.trim_start, self.trim_end, self.stream_copy):
            self._add(self.op_trim, c)

        self.op_transform = OperationRow(
            icon="rotate", title="Transform", description="Rotate, flip, speed"
        )
        self.rotation = ChoiceRow("Rotate", ROTATIONS, 0)
        self.speed = spin_row("Speed", 0.5, 2.0, 1.0, step=0.1, digits=2)
        self.flip_h = Adw.SwitchRow(title="Flip horizontal")
        self.flip_v = Adw.SwitchRow(title="Flip vertical")
        self.crop = Adw.EntryRow(title="Free crop — WxH+X+Y")
        for c in (self.rotation.row, self.speed, self.flip_h, self.flip_v, self.crop):
            self._add(self.op_transform, c)

        self.op_resize = OperationRow(
            icon="resize", title="Resize", description="Change resolution"
        )
        self.res_preset = ChoiceRow("Resolution", RES_PRESETS, "")
        self._add(self.op_resize, self.res_preset.row)

        self.op_compress = OperationRow(
            icon="compress", title="Compress", description="Reduce size (CRF)"
        )
        self.crf = spin_row("CRF (0 = off)", 0, 51, settings.default_video_crf)
        self.compress_preset = ChoiceRow(
            "Encoder preset", COMPRESS_PRESETS, settings.default_video_preset
        )
        self.target_size = spin_row(
            "Target size (MB, 0 = off)", 0.0, 102400.0, 0.0, step=5, digits=1
        )
        for c in (self.crf, self.compress_preset.row, self.target_size):
            self._add(self.op_compress, c)

        self.op_watermark = OperationRow(
            icon="watermark", title="Watermark", description="Text overlay"
        )
        self.wm_text = Adw.EntryRow(title="Text")
        self.wm_position = ChoiceRow("Position", GRAVITIES, "southeast")
        self.wm_size = spin_row("Text size (pt)", 8, 200, 36)
        self.wm_opacity = spin_row("Opacity (%)", 0, 100, 60)
        for c in (self.wm_text, self.wm_position.row, self.wm_size, self.wm_opacity):
            self._add(self.op_watermark, c)

        self.op_effects = OperationRow(
            icon="effects", title="Effects", description="Reverse and logo"
        )
        self.reverse = Adw.SwitchRow(title="Reverse video (and audio)")
        self.logo_path = Adw.EntryRow(title="Logo path")
        attach_file_browse(self.logo_path, self._root_window, title="Choose logo")
        self.logo_position = ChoiceRow("Logo position", GRAVITIES, "southeast")
        self.logo_width = spin_row("Logo width (px)", 16, 4096, 120)
        self.logo_opacity = spin_row("Logo opacity (%)", 0, 100, 100)
        for c in (
            self.reverse, self.logo_path, self.logo_position.row,
            self.logo_width, self.logo_opacity,
        ):
            self._add(self.op_effects, c)

        self.op_animation = OperationRow(
            icon="animation", title="Animation",
            description="GIF / WebP export tuning",
        )
        self.gif_fps = spin_row("GIF fps", 1, 60, 12)
        self.gif_width = spin_row("GIF width (px)", 64, 4096, 480)
        self.webp_fps = spin_row("WebP fps", 1, 60, 15)
        self.webp_width = spin_row("WebP width (px)", 64, 4096, 480)
        self.webp_quality = spin_row("WebP quality", 0, 100, 75)
        for c in (
            self.gif_fps, self.gif_width, self.webp_fps,
            self.webp_width, self.webp_quality,
        ):
            self._add(self.op_animation, c)

        self.op_thumbnails = OperationRow(
            icon="thumbnails", title="Thumbnails",
            description="Contact sheet of frames",
        )
        self.thumb_rows = spin_row("Rows", 1, 16, 4)
        self.thumb_cols = spin_row("Columns", 1, 16, 4)
        self.thumb_interval = spin_row("Interval (frames)", 1, 100000, 60)
        self.thumb_tile_width = spin_row("Tile width (px)", 64, 4096, 320)
        for c in (
            self.thumb_rows, self.thumb_cols,
            self.thumb_interval, self.thumb_tile_width,
        ):
            self._add(self.op_thumbnails, c)

        self.op_subtitles = OperationRow(
            icon="subtitle", title="Subtitles", description="Burn in a subtitle file"
        )
        self.burn_subtitle = Adw.EntryRow(title="Subtitle file")
        attach_file_browse(
            self.burn_subtitle, self._root_window, title="Choose subtitle"
        )
        self._add(self.op_subtitles, self.burn_subtitle)

        for op in (
            self.op_trim, self.op_transform, self.op_resize, self.op_compress,
            self.op_watermark, self.op_effects, self.op_animation,
            self.op_thumbnails, self.op_subtitles,
        ):
            op.on_toggle = self._refresh_summaries
            self.operations.add_operation(op)

    def _add(self, op: OperationRow, control: Gtk.Widget) -> None:
        op.add(control)
        wire_change(control, self._refresh_summaries)

    def _root_window(self) -> Gtk.Window | None:
        return self._window if isinstance(self._window, Gtk.Window) else None

    # -- summaries ---------------------------------------------------------

    def _refresh_summaries(self, *_args) -> None:
        self.op_trim.set_summary(self._sum_trim())
        self.op_transform.set_summary(self._sum_transform())
        self.op_resize.set_summary(self._sum_resize())
        self.op_compress.set_summary(self._sum_compress())
        self.op_watermark.set_summary(self._sum_text(self.wm_text))
        self.op_effects.set_summary(self._sum_effects())
        self.op_animation.set_summary(None)
        self.op_thumbnails.set_summary(
            f"{int(self.thumb_rows.get_value())} × "
            f"{int(self.thumb_cols.get_value())} grid"
        )
        self.op_subtitles.set_summary(self._sum_text(self.burn_subtitle))

    def _sum_trim(self) -> str | None:
        start = self.trim_start.get_text().strip()
        end = self.trim_end.get_text().strip()
        if start or end:
            return f"{start or 'start'} → {end or 'end'}"
        return None

    def _sum_transform(self) -> str | None:
        parts = []
        if self.rotation.get_value():
            parts.append(f"{self.rotation.get_value()}°")
        if abs(self.speed.get_value() - 1.0) > 1e-3:
            parts.append(f"{self.speed.get_value():.2f}×")
        if self.flip_h.get_active():
            parts.append("Flip H")
        if self.flip_v.get_active():
            parts.append("Flip V")
        return " · ".join(parts) or None

    def _sum_resize(self) -> str | None:
        value = self.res_preset.get_value()
        return value or None

    def _sum_compress(self) -> str | None:
        if self.target_size.get_value() > 0:
            return f"≤ {self.target_size.get_value():.0f} MB"
        if self.crf.get_value() > 0:
            return f"CRF {int(self.crf.get_value())}"
        return None

    def _sum_effects(self) -> str | None:
        parts = []
        if self.reverse.get_active():
            parts.append("Reverse")
        if self.logo_path.get_text().strip():
            parts.append("Logo")
        return " · ".join(parts) or None

    def _sum_text(self, entry: Adw.EntryRow) -> str | None:
        text = entry.get_text().strip()
        return text or None

    # -- options -----------------------------------------------------------

    def collect_options(self) -> dict:
        opts: dict[str, object] = {
            "category": KIND,
            "format_out": self.format_picker.get_format(),
            "bitrate": self.audio_bitrate.get_format(),
        }

        if self.op_trim.enabled:
            if self.trim_start.get_text().strip():
                opts["trim_start"] = self.trim_start.get_text().strip()
            if self.trim_end.get_text().strip():
                opts["trim_end"] = self.trim_end.get_text().strip()
            if self.stream_copy.get_active():
                opts["stream_copy"] = True

        if self.op_transform.enabled:
            if self.rotation.get_value():
                opts["rotation_degrees"] = self.rotation.get_value()
            if abs(self.speed.get_value() - 1.0) > 1e-3:
                opts["speed"] = round(self.speed.get_value(), 2)
            if self.flip_h.get_active():
                opts["flip_horizontal"] = True
            if self.flip_v.get_active():
                opts["flip_vertical"] = True
            if self.crop.get_text().strip():
                opts["crop"] = self.crop.get_text().strip()

        if self.op_resize.enabled and self.res_preset.get_value():
            opts["resolution_preset"] = self.res_preset.get_value()

        if self.op_compress.enabled:
            crf = int(self.crf.get_value())
            target = round(self.target_size.get_value(), 1)
            if crf > 0:
                opts["crf"] = crf
            if target > 0:
                opts["target_size_mb"] = target
            if crf > 0 or target > 0:
                opts["compress_preset"] = self.compress_preset.get_value()

        if self.op_watermark.enabled and self.wm_text.get_text().strip():
            opts["watermark_text"] = self.wm_text.get_text().strip()
            opts["watermark_position"] = self.wm_position.get_value()
            opts["watermark_size"] = int(self.wm_size.get_value())
            opts["watermark_opacity"] = int(self.wm_opacity.get_value())

        if self.op_effects.enabled:
            if self.reverse.get_active():
                opts["reverse_video"] = True
            logo = self.logo_path.get_text().strip()
            if logo:
                opts["logo_path"] = logo
                opts["logo_position"] = self.logo_position.get_value()
                opts["logo_width"] = int(self.logo_width.get_value())
                opts["logo_opacity"] = int(self.logo_opacity.get_value())

        if self.op_animation.enabled:
            opts["gif_fps"] = int(self.gif_fps.get_value())
            opts["gif_width"] = int(self.gif_width.get_value())
            opts["webp_fps"] = int(self.webp_fps.get_value())
            opts["webp_width"] = int(self.webp_width.get_value())
            opts["webp_quality"] = int(self.webp_quality.get_value())

        if self.op_thumbnails.enabled:
            opts["thumbnail_grid"] = True
            opts["thumbnail_rows"] = int(self.thumb_rows.get_value())
            opts["thumbnail_cols"] = int(self.thumb_cols.get_value())
            opts["thumbnail_interval"] = int(self.thumb_interval.get_value())
            opts["thumbnail_tile_width"] = int(self.thumb_tile_width.get_value())

        if self.op_subtitles.enabled and self.burn_subtitle.get_text().strip():
            opts["burn_subtitle_path"] = self.burn_subtitle.get_text().strip()

        return opts

    def apply_options(self, payload: dict) -> None:
        """Restore the exact state a preset was saved from.

        Controls reset to defaults when their key is absent and each
        operation is enabled iff the payload carries one of its keys, so
        loading a preset never leaves earlier configuration active.
        """
        self.format_picker.set_format(str(payload.get("format_out", DEFAULT_FORMAT)))
        self.audio_bitrate.set_format(str(payload.get("bitrate", DEFAULT_BITRATE)))

        trim_keys = {"trim_start", "trim_end", "stream_copy"}
        self.op_trim.row.set_enable_expansion(bool(trim_keys & payload.keys()))
        self.trim_start.set_text(str(payload.get("trim_start", "")))
        self.trim_end.set_text(str(payload.get("trim_end", "")))
        self.stream_copy.set_active(bool(payload.get("stream_copy")))

        transform_keys = {
            "rotation_degrees", "speed", "flip_horizontal", "flip_vertical", "crop",
        }
        self.op_transform.row.set_enable_expansion(bool(transform_keys & payload.keys()))
        self.rotation.set_value(_as_int(payload.get("rotation_degrees", 0), 0))
        self.speed.set_value(_as_float(payload.get("speed", 1.0), 1.0))
        self.flip_h.set_active(bool(payload.get("flip_horizontal")))
        self.flip_v.set_active(bool(payload.get("flip_vertical")))
        self.crop.set_text(str(payload.get("crop", "")))

        self.op_resize.row.set_enable_expansion("resolution_preset" in payload)
        self.res_preset.set_value(str(payload.get("resolution_preset", "")))

        compress_keys = {"crf", "target_size_mb", "compress_preset"}
        self.op_compress.row.set_enable_expansion(bool(compress_keys & payload.keys()))
        self.crf.set_value(_as_int(payload.get("crf", 0), 0))
        self.target_size.set_value(_as_float(payload.get("target_size_mb", 0.0), 0.0))
        self.compress_preset.set_value(str(
            payload.get("compress_preset", get_settings().default_video_preset)
        ))

        watermark_keys = {
            "watermark_text", "watermark_position", "watermark_size",
            "watermark_opacity",
        }
        self.op_watermark.row.set_enable_expansion(bool(watermark_keys & payload.keys()))
        self.wm_text.set_text(str(payload.get("watermark_text", "")))
        self.wm_position.set_value(str(payload.get("watermark_position", "southeast")))
        self.wm_size.set_value(_as_int(payload.get("watermark_size", 36), 36))
        self.wm_opacity.set_value(_as_int(payload.get("watermark_opacity", 60), 60))

        effects_keys = {
            "reverse_video", "logo_path", "logo_position", "logo_width",
            "logo_opacity",
        }
        self.op_effects.row.set_enable_expansion(bool(effects_keys & payload.keys()))
        self.reverse.set_active(bool(payload.get("reverse_video")))
        self.logo_path.set_text(str(payload.get("logo_path", "")))
        self.logo_position.set_value(str(payload.get("logo_position", "southeast")))
        self.logo_width.set_value(_as_int(payload.get("logo_width", 120), 120))
        self.logo_opacity.set_value(_as_int(payload.get("logo_opacity", 100), 100))

        animation_keys = {
            "gif_fps", "gif_width", "webp_fps", "webp_width", "webp_quality",
        }
        self.op_animation.row.set_enable_expansion(bool(animation_keys & payload.keys()))
        self.gif_fps.set_value(_as_int(payload.get("gif_fps", 12), 12))
        self.gif_width.set_value(_as_int(payload.get("gif_width", 480), 480))
        self.webp_fps.set_value(_as_int(payload.get("webp_fps", 15), 15))
        self.webp_width.set_value(_as_int(payload.get("webp_width", 480), 480))
        self.webp_quality.set_value(_as_int(payload.get("webp_quality", 75), 75))

        thumb_keys = {
            "thumbnail_grid", "thumbnail_rows", "thumbnail_cols",
            "thumbnail_interval", "thumbnail_tile_width",
        }
        self.op_thumbnails.row.set_enable_expansion(bool(thumb_keys & payload.keys()))
        self.thumb_rows.set_value(_as_int(payload.get("thumbnail_rows", 4), 4))
        self.thumb_cols.set_value(_as_int(payload.get("thumbnail_cols", 4), 4))
        self.thumb_interval.set_value(
            _as_int(payload.get("thumbnail_interval", 60), 60)
        )
        self.thumb_tile_width.set_value(
            _as_int(payload.get("thumbnail_tile_width", 320), 320)
        )

        self.op_subtitles.row.set_enable_expansion("burn_subtitle_path" in payload)
        self.burn_subtitle.set_text(str(payload.get("burn_subtitle_path", "")))

        self._refresh_summaries()

    # -- actions -----------------------------------------------------------

    def _on_file_changed(self, _path: Path | None) -> None:
        pass

    def _require_file(self) -> bool:
        if self.dropzone.path is None:
            self._window.show_toast("Choose a video first.")
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


def build_video_page(window) -> Gtk.Widget:
    return VideoPage(window).widget
