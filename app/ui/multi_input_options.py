from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QGridLayout,
        QLabel,
        QLineEdit,
        QListView,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QAbstractSpinBox = QCheckBox = QComboBox = QDoubleSpinBox = QGridLayout = QLabel = QLineEdit = QListView = QSpinBox = QVBoxLayout = QWidget = None


MIX_DURATIONS = (
    ("Longest input (default)", "longest"),
    ("Shortest input", "shortest"),
    ("First input", "first"),
)
MERGE_MODES = (
    ("Shift each file (sequential)", "shift"),
    ("Append + sort by time", "append"),
)


class AudioMixOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AudioMixOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(1, 1)

        self.duration_combo = _combo(self, MIX_DURATIONS)
        self.normalize_check = QCheckBox("Normalize sum to 1/N (default on)", self)
        self.normalize_check.setChecked(True)

        info = QLabel(
            "Audio Mix overlays multiple tracks via FFmpeg `amix`. Choose how the "
            "output duration is computed when input lengths differ. Disable "
            "normalize if inputs are already at safe levels.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Duration", self), 0, 0)
        grid.addWidget(self.duration_combo, 0, 1)
        grid.addWidget(self.normalize_check, 1, 0, 1, 2)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        duration = self.duration_combo.currentData()
        if duration and duration != "longest":
            options["mix_duration"] = duration
        # `normalize` defaults to True in the engine; only emit when user disables.
        if not self.normalize_check.isChecked():
            options["mix_normalize"] = False
        return options


class ImageMontageOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ImageMontageOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.tile_input = QLineEdit(self)
        self.tile_input.setPlaceholderText("auto (e.g. 3x3)")

        self.geometry_input = QLineEdit(self)
        self.geometry_input.setPlaceholderText("200x200+5+5")

        self.background_input = QLineEdit(self)
        self.background_input.setPlaceholderText("white")

        info = QLabel(
            "Tile is empty/auto for square-ish layout based on input count. "
            "Geometry sets per-tile size and spacing (`WxH+padX+padY`). "
            "Background is any ImageMagick color (`white`, `#0c2c55`, …).",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Tile", self), 0, 0)
        grid.addWidget(self.tile_input, 0, 1)
        grid.addWidget(_field("Geometry", self), 0, 2)
        grid.addWidget(self.geometry_input, 0, 3)
        grid.addWidget(_field("Background", self), 1, 0)
        grid.addWidget(self.background_input, 1, 1, 1, 3)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        tile = self.tile_input.text().strip()
        if tile:
            options["montage_tile"] = tile
        geometry = self.geometry_input.text().strip()
        if geometry:
            options["montage_geometry"] = geometry
        background = self.background_input.text().strip()
        if background:
            options["montage_background"] = background
        return options


class SubtitleMergeOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SubtitleMergeOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(1, 1)

        self.mode_combo = _combo(self, MERGE_MODES)

        self.gap_input = QDoubleSpinBox(self)
        self.gap_input.setRange(0.0, 600.0)
        self.gap_input.setSingleStep(0.5)
        self.gap_input.setDecimals(2)
        self.gap_input.setValue(0.0)
        self.gap_input.setSuffix(" s")
        self.gap_input.setSpecialValueText("none")
        self.gap_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.gap_input.setAccelerated(True)

        info = QLabel(
            "Shift mode (default) plays each file sequentially: every subsequent "
            "file's cues are offset by the cumulative end of the previous files "
            "plus the gap. Append mode keeps each file's original timing and "
            "sorts cues by start time (overlaps possible).",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Mode", self), 0, 0)
        grid.addWidget(self.mode_combo, 0, 1)
        grid.addWidget(_field("Gap (shift mode)", self), 1, 0)
        grid.addWidget(self.gap_input, 1, 1)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        mode = self.mode_combo.currentData()
        if mode and mode != "shift":
            options["subtitle_merge_mode"] = mode
        gap = round(self.gap_input.value(), 3)
        if gap > 0:
            options["subtitle_merge_gap"] = gap
        return options


SPLIT_MODES = (
    ("Every N pages", "every_n"),
    ("Custom ranges", "range"),
)
PAGE_NUMBER_GRAVITIES = (
    ("Bottom (south)", "south"),
    ("Bottom-Right", "southeast"),
    ("Bottom-Left", "southwest"),
    ("Top (north)", "north"),
    ("Top-Right", "northeast"),
    ("Top-Left", "northwest"),
)
SLIDES_FORMATS = (
    ("PNG", "png"),
    ("JPG", "jpg"),
)


class PDFNumberingOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PDFNumberingOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.format_input = QLineEdit(self)
        self.format_input.setText("Page {n} of {total}")
        self.format_input.setPlaceholderText("Page {n} of {total}")

        self.position_combo = _combo(self, PAGE_NUMBER_GRAVITIES)

        self.size_input = QSpinBox(self)
        self.size_input.setRange(6, 72)
        self.size_input.setValue(14)
        self.size_input.setSuffix(" pt")
        _use_stepper(self.size_input)

        self.start_input = QSpinBox(self)
        self.start_input.setRange(0, 100000)
        self.start_input.setValue(1)
        _use_stepper(self.start_input)

        self.skip_input = QSpinBox(self)
        self.skip_input.setRange(0, 100000)
        self.skip_input.setValue(0)
        _use_stepper(self.skip_input)

        info = QLabel(
            "Format placeholders: `{n}` is the printed number, `{total}` is the "
            "page count after skipped pages. For Bates numbering use a fixed-width "
            "format like `BATES{n:06}`. Skip leaves the first N pages untouched.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Format", self), 0, 0)
        grid.addWidget(self.format_input, 0, 1, 1, 3)
        grid.addWidget(_field("Position", self), 1, 0)
        grid.addWidget(self.position_combo, 1, 1)
        grid.addWidget(_field("Size", self), 1, 2)
        grid.addWidget(self.size_input, 1, 3)
        grid.addWidget(_field("Start at", self), 2, 0)
        grid.addWidget(self.start_input, 2, 1)
        grid.addWidget(_field("Skip first", self), 2, 2)
        grid.addWidget(self.skip_input, 2, 3)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {"operation": "page_numbering"}
        text = self.format_input.text().strip()
        if text:
            options["page_number_format"] = text
        position = self.position_combo.currentData()
        if position and position != "south":
            options["page_number_position"] = position
        size = self.size_input.value()
        if size != 14:
            options["page_number_size"] = size
        start = self.start_input.value()
        if start != 1:
            options["page_number_start"] = start
        skip = self.skip_input.value()
        if skip > 0:
            options["page_number_skip"] = skip
        return options


class SlidesToImagesOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SlidesToImagesOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(1, 1)

        self.format_combo = _combo(self, SLIDES_FORMATS)

        self.dpi_input = QSpinBox(self)
        self.dpi_input.setRange(72, 600)
        self.dpi_input.setValue(200)
        self.dpi_input.setSuffix(" DPI")
        _use_stepper(self.dpi_input)

        info = QLabel(
            "LibreOffice converts the deck to PDF first, then PyMuPDF renders each "
            "page at the chosen DPI. Higher DPI = sharper but larger files.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Image format", self), 0, 0)
        grid.addWidget(self.format_combo, 0, 1)
        grid.addWidget(_field("Render DPI", self), 1, 0)
        grid.addWidget(self.dpi_input, 1, 1)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {"operation": "slides_to_images"}
        image_format = self.format_combo.currentData() or "png"
        if image_format != "png":
            options["slides_image_format"] = image_format
        dpi = self.dpi_input.value()
        if dpi != 200:
            options["slides_dpi"] = dpi
        return options


class PDFSplitOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PDFSplitOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 140)
        grid.setColumnStretch(1, 1)

        self.mode_combo = _combo(self, SPLIT_MODES)
        self.mode_combo.currentIndexChanged.connect(self._toggle_inputs)

        self.pages_per_file_input = QSpinBox(self)
        self.pages_per_file_input.setRange(1, 1000)
        self.pages_per_file_input.setValue(1)
        self.pages_per_file_input.setSuffix(" pages")
        self.pages_per_file_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)

        self.ranges_input = QLineEdit(self)
        self.ranges_input.setPlaceholderText("e.g. 1-5, 6-10, 11-20")
        self.ranges_input.setEnabled(False)

        info = QLabel(
            "Every N pages: each output covers consecutive N pages. "
            "Custom ranges: comma-separated 1-based ranges; each range becomes "
            "one output file. Outputs land in the chosen folder as "
            "`<stem>-001.pdf`, `<stem>-002.pdf`, …",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Mode", self), 0, 0)
        grid.addWidget(self.mode_combo, 0, 1)
        grid.addWidget(_field("Pages per file", self), 1, 0)
        grid.addWidget(self.pages_per_file_input, 1, 1)
        grid.addWidget(_field("Ranges", self), 2, 0)
        grid.addWidget(self.ranges_input, 2, 1)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def _toggle_inputs(self, _index: int) -> None:
        is_range = self.mode_combo.currentData() == "range"
        self.ranges_input.setEnabled(is_range)
        self.pages_per_file_input.setEnabled(not is_range)

    def collect_options(self) -> dict:
        options: dict[str, object] = {"split_mode": self.mode_combo.currentData() or "every_n"}
        if options["split_mode"] == "range":
            ranges = self.ranges_input.text().strip()
            if ranges:
                options["split_ranges"] = ranges
        else:
            options["split_pages_per_file"] = self.pages_per_file_input.value()
        return options


def _combo(parent: QWidget, items: tuple[tuple[str, object], ...]) -> QComboBox:
    combo = QComboBox(parent)
    combo.setView(QListView(combo))
    for label, value in items:
        combo.addItem(label, value)
    return combo


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label
