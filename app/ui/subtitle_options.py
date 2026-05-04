from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QDoubleSpinBox,
        QGridLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QAbstractSpinBox = QDoubleSpinBox = QGridLayout = QLabel = QVBoxLayout = QWidget = None


class SubtitleOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SubtitleOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(1, 1)

        self.time_shift_input = QDoubleSpinBox(self)
        self.time_shift_input.setRange(-3600.0, 3600.0)
        self.time_shift_input.setSingleStep(0.5)
        self.time_shift_input.setDecimals(2)
        self.time_shift_input.setValue(0.0)
        self.time_shift_input.setSuffix(" s")
        self.time_shift_input.setSpecialValueText("none")
        self.time_shift_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.time_shift_input.setAccelerated(True)

        info = QLabel(
            "Positive shift moves cues later, negative shift moves them earlier. "
            "Conversion preserves cue text; styling tags are passed through unchanged.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Time shift", self), 0, 0)
        grid.addWidget(self.time_shift_input, 0, 1)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        offset = round(self.time_shift_input.value(), 3)
        if abs(offset) > 1e-3:
            options["time_shift_seconds"] = offset
        return options


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label
