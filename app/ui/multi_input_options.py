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
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QAbstractSpinBox = QCheckBox = QComboBox = QDoubleSpinBox = QGridLayout = QLabel = QLineEdit = QListView = QVBoxLayout = QWidget = None


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
