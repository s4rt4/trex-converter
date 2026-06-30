"""Audio converter page — full parity with the old Qt Audio page.

Anatomy (house style §6): File (drop zone) → Output (format chips ·
destination · audio-bitrate chips · channels · sample rate) → Operations
(3-row checklist: Trim, Effects, Tags) → footer.

The old 4-tab ``AudioOptionsPanel`` maps to three operation rows plus the
two "Output" tab fields (channels, sample rate), which live in the Output
group since they describe the output, not an optional transform. Option
emission mirrors the old "emit only when changed/non-empty" rule (see
feature-map §C-Audio).
"""

from __future__ import annotations

from pathlib import Path

from gi.repository import Adw, Gtk

from app.core.settings import get_settings
from app.ui_gtk.widgets.destination_row import DestinationRow
from app.ui_gtk.widgets.dropzone import DropZone
from app.ui_gtk.widgets.format_picker import FormatPicker
from app.ui_gtk.widgets.operations import OperationRow, OperationsGroup
from app.ui_gtk.widgets.page_scaffold import PageScaffold
from app.ui_gtk.widgets.preset_bar import PresetBar
from app.ui_gtk.widgets.rows import ChoiceRow, attach_file_browse, spin_row, wire_change

KIND = "audio"

OUTPUT_FORMATS = ("mp3", "wav", "aac", "flac", "m4a", "opus", "ogg")
COMMON_FORMATS = ("mp3", "wav", "m4a", "flac")
DEFAULT_FORMAT = "mp3"

AUDIO_BITRATES = ("128k", "192k", "256k", "320k")

CHANNELS = (("Source", ""), ("Mono", "1"), ("Stereo", "2"))
SAMPLE_RATES = (
    ("Source", ""), ("22 050 Hz", "22050"), ("44 100 Hz", "44100"),
    ("48 000 Hz", "48000"), ("96 000 Hz", "96000"),
)


class AudioPage:
    def __init__(self, window) -> None:
        self._window = window
        settings = get_settings()

        # --- File ---------------------------------------------------------
        self.dropzone = DropZone(
            self._on_file_changed,
            icon="drop-audio",
            empty_title="Drop an audio file here or click to choose",
            empty_subtitle="MP3, WAV, FLAC, M4A, OGG",
        )
        file_group = Adw.PreferencesGroup(title="File")
        file_group.add(self.dropzone)

        # --- Output -------------------------------------------------------
        self.format_picker = FormatPicker(
            OUTPUT_FORMATS, common=COMMON_FORMATS,
            default=DEFAULT_FORMAT, title="Format",
        )
        self.destination = DestinationRow(initial=_default_output_dir())
        bitrate_default = (
            settings.default_audio_bitrate
            if settings.default_audio_bitrate in AUDIO_BITRATES
            else "192k"
        )
        self.bitrate = FormatPicker(
            AUDIO_BITRATES, default=bitrate_default,
            title="Audio bitrate", uppercase=False,
        )
        self.channels = ChoiceRow("Channels", CHANNELS, "")
        self.sample_rate = ChoiceRow("Sample rate", SAMPLE_RATES, "")
        output_group = Adw.PreferencesGroup(title="Output")
        for row in (
            self.format_picker.row, self.destination.row, self.bitrate.row,
            self.channels.row, self.sample_rate.row,
        ):
            output_group.add(row)

        # --- Operations ---------------------------------------------------
        self.operations = OperationsGroup(title="Operations")
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
        self.op_trim = OperationRow(
            icon="trim", title="Trim", description="Cut a section (HH:MM:SS or seconds)"
        )
        self.trim_start = Adw.EntryRow(title="Start — e.g. 00:00:10")
        self.trim_end = Adw.EntryRow(title="End — e.g. 00:01:30")
        for c in (self.trim_start, self.trim_end):
            self._add(self.op_trim, c)

        self.op_effects = OperationRow(
            icon="effects", title="Effects", description="Fade, volume, normalize"
        )
        self.fade_in = spin_row("Fade in (s)", 0.0, 60.0, 0.0, step=0.5, digits=2)
        self.fade_out_start = spin_row(
            "Fade out start (s)", 0.0, 86400.0, 0.0, step=0.5, digits=2
        )
        self.fade_out = spin_row("Fade out (s)", 0.0, 60.0, 0.0, step=0.5, digits=2)
        self.volume = spin_row("Volume (dB)", -20, 20, 0)
        self.loudnorm = Adw.SwitchRow(
            title="Loudness normalize", subtitle="EBU R128, target −16 LUFS"
        )
        self.vocal_remove = Adw.SwitchRow(
            title="Vocal remove", subtitle="Cancel the center channel"
        )
        for c in (
            self.fade_in, self.fade_out_start, self.fade_out,
            self.volume, self.loudnorm, self.vocal_remove,
        ):
            self._add(self.op_effects, c)

        self.op_tags = OperationRow(
            icon="document", title="Tags", description="ID3 metadata and cover art"
        )
        self.tag_title = Adw.EntryRow(title="Title")
        self.tag_artist = Adw.EntryRow(title="Artist")
        self.tag_album = Adw.EntryRow(title="Album")
        self.tag_year = Adw.EntryRow(title="Year")
        self.tag_genre = Adw.EntryRow(title="Genre")
        self.tag_track = Adw.EntryRow(title="Track — e.g. 11/12")
        self.cover_art = Adw.EntryRow(title="Cover art")
        attach_file_browse(self.cover_art, self._root_window, title="Choose cover art")
        for c in (
            self.tag_title, self.tag_artist, self.tag_album, self.tag_year,
            self.tag_genre, self.tag_track, self.cover_art,
        ):
            self._add(self.op_tags, c)

        for op in (self.op_trim, self.op_effects, self.op_tags):
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
        self.op_effects.set_summary(self._sum_effects())
        self.op_tags.set_summary(self._sum_tags())

    def _sum_trim(self) -> str | None:
        start = self.trim_start.get_text().strip()
        end = self.trim_end.get_text().strip()
        if start or end:
            return f"{start or 'start'} → {end or 'end'}"
        return None

    def _sum_effects(self) -> str | None:
        parts = []
        if self.fade_in.get_value() > 0:
            parts.append("Fade in")
        if self.fade_out.get_value() > 0:
            parts.append("Fade out")
        if int(self.volume.get_value()) != 0:
            parts.append(f"{int(self.volume.get_value()):+d} dB")
        if self.loudnorm.get_active():
            parts.append("Loudnorm")
        if self.vocal_remove.get_active():
            parts.append("Vocal remove")
        return " · ".join(parts) or None

    def _sum_tags(self) -> str | None:
        for entry in (self.tag_title, self.tag_artist, self.tag_album):
            if entry.get_text().strip():
                return entry.get_text().strip()
        return None

    # -- options -----------------------------------------------------------

    def collect_options(self) -> dict:
        opts: dict[str, object] = {
            "category": KIND,
            "format_out": self.format_picker.get_format(),
            "bitrate": self.bitrate.get_format(),
        }
        if self.channels.get_value():
            opts["audio_channels"] = self.channels.get_value()
        if self.sample_rate.get_value():
            opts["sample_rate"] = self.sample_rate.get_value()

        if self.op_trim.enabled:
            if self.trim_start.get_text().strip():
                opts["trim_start"] = self.trim_start.get_text().strip()
            if self.trim_end.get_text().strip():
                opts["trim_end"] = self.trim_end.get_text().strip()

        if self.op_effects.enabled:
            fade_in = round(self.fade_in.get_value(), 3)
            if fade_in > 0:
                opts["fade_in_duration"] = fade_in
            fade_out = round(self.fade_out.get_value(), 3)
            if fade_out > 0:
                opts["fade_out_duration"] = fade_out
                opts["fade_out_start"] = round(self.fade_out_start.get_value(), 3)
            volume = int(self.volume.get_value())
            if volume != 0:
                opts["volume_db"] = volume
            if self.loudnorm.get_active():
                opts["loudnorm"] = True
            if self.vocal_remove.get_active():
                opts["vocal_remove"] = True

        if self.op_tags.enabled:
            for key, entry in self._tag_entries():
                value = entry.get_text().strip()
                if value:
                    opts[key] = value
            cover = self.cover_art.get_text().strip()
            if cover:
                opts["cover_art_path"] = cover

        return opts

    def _tag_entries(self):
        return (
            ("id3_title", self.tag_title),
            ("id3_artist", self.tag_artist),
            ("id3_album", self.tag_album),
            ("id3_year", self.tag_year),
            ("id3_genre", self.tag_genre),
            ("id3_track", self.tag_track),
        )

    def apply_options(self, payload: dict) -> None:
        if "format_out" in payload:
            self.format_picker.set_format(str(payload["format_out"]))
        if "bitrate" in payload:
            self.bitrate.set_format(str(payload["bitrate"]))
        if "audio_channels" in payload:
            self.channels.set_value(str(payload["audio_channels"]))
        if "sample_rate" in payload:
            self.sample_rate.set_value(str(payload["sample_rate"]))

        if {"trim_start", "trim_end"} & payload.keys():
            self.op_trim.row.set_enable_expansion(True)
            self.trim_start.set_text(str(payload.get("trim_start", "")))
            self.trim_end.set_text(str(payload.get("trim_end", "")))

        effects_keys = {
            "fade_in_duration", "fade_out_duration", "fade_out_start",
            "volume_db", "loudnorm", "vocal_remove",
        }
        if effects_keys & payload.keys():
            self.op_effects.row.set_enable_expansion(True)
            self.fade_in.set_value(_as_float(payload.get("fade_in_duration", 0.0), 0.0))
            self.fade_out.set_value(_as_float(payload.get("fade_out_duration", 0.0), 0.0))
            self.fade_out_start.set_value(
                _as_float(payload.get("fade_out_start", 0.0), 0.0)
            )
            self.volume.set_value(_as_float(payload.get("volume_db", 0), 0))
            self.loudnorm.set_active(bool(payload.get("loudnorm")))
            self.vocal_remove.set_active(bool(payload.get("vocal_remove")))

        tag_keys = {key for key, _ in self._tag_entries()} | {"cover_art_path"}
        if tag_keys & payload.keys():
            self.op_tags.row.set_enable_expansion(True)
            for key, entry in self._tag_entries():
                entry.set_text(str(payload.get(key, "")))
            self.cover_art.set_text(str(payload.get("cover_art_path", "")))

        self._refresh_summaries()

    # -- actions -----------------------------------------------------------

    def _on_file_changed(self, _path: Path | None) -> None:
        pass

    def _require_file(self) -> bool:
        if self.dropzone.path is None:
            self._window.show_toast("Choose an audio file first.")
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


def build_audio_page(window) -> Gtk.Widget:
    return AudioPage(window).widget
