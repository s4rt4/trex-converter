from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QComboBox,
        QGridLayout,
        QLabel,
        QListView,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QAbstractSpinBox = QComboBox = QGridLayout = QLabel = QListView = QSpinBox = QVBoxLayout = QWidget = None


ECC_LEVELS = (
    ("L — ~7% recovery", "L"),
    ("M — ~15% recovery (default)", "M"),
    ("Q — ~25% recovery", "Q"),
    ("H — ~30% recovery", "H"),
)


class QROptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("QROptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.size_input = QSpinBox(self)
        self.size_input.setRange(1, 50)
        self.size_input.setValue(8)
        self.size_input.setSuffix(" px/dot")
        _use_stepper(self.size_input)

        self.margin_input = QSpinBox(self)
        self.margin_input.setRange(0, 32)
        self.margin_input.setValue(2)
        self.margin_input.setSuffix(" dots")
        _use_stepper(self.margin_input)

        self.ecc_combo = QComboBox(self)
        self.ecc_combo.setView(QListView(self.ecc_combo))
        for label, value in ECC_LEVELS:
            self.ecc_combo.addItem(label, value)
        # Default to "M"
        for index in range(self.ecc_combo.count()):
            if self.ecc_combo.itemData(index) == "M":
                self.ecc_combo.setCurrentIndex(index)
                break

        info = QLabel(
            "Generate options apply when input is a .txt file (output PNG/SVG). "
            "Decode options have no effect — the input image is scanned by zbarimg "
            "and the first decoded payload is written to the .txt output. "
            "Both directions require external binaries: qrencode for generate, "
            "zbarimg for decode.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Module size", self), 0, 0)
        grid.addWidget(self.size_input, 0, 1)
        grid.addWidget(_field("Margin", self), 0, 2)
        grid.addWidget(self.margin_input, 0, 3)
        grid.addWidget(_field("Error correction", self), 1, 0)
        grid.addWidget(self.ecc_combo, 1, 1, 1, 3)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        size = self.size_input.value()
        if size != 8:
            options["qr_size"] = size
        margin = self.margin_input.value()
        if margin != 2:
            options["qr_margin"] = margin
        level = self.ecc_combo.currentData()
        if level and level != "M":
            options["qr_ecc_level"] = level
        return options


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


def _use_stepper(spinbox: QAbstractSpinBox) -> None:
    spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spinbox.setAccelerated(True)
