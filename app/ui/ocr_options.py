from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QAbstractSpinBox = QCheckBox = QComboBox = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QSpinBox = QVBoxLayout = QWidget = None


PSM_MODES = (
    ("3 — Auto (default)", 3),
    ("0 — OSD only", 0),
    ("1 — Auto with OSD", 1),
    ("4 — Single column", 4),
    ("6 — Single block", 6),
    ("7 — Single line", 7),
    ("8 — Single word", 8),
    ("11 — Sparse text", 11),
    ("13 — Raw line", 13),
)
OEM_MODES = (
    ("3 — Default (LSTM + Legacy)", 3),
    ("0 — Legacy only", 0),
    ("1 — LSTM only", 1),
    ("2 — Legacy + LSTM", 2),
)
LANGUAGE_PRESETS = (
    ("English (eng)", "eng"),
    ("Indonesian (ind)", "ind"),
    ("English + Indonesian", "eng+ind"),
    ("Custom…", "__custom__"),
)


class OCROptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("OCROptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.language_combo = _combo(self, LANGUAGE_PRESETS)
        self.language_combo.currentIndexChanged.connect(self._toggle_custom_language)
        self.language_custom_input = QLineEdit(self)
        self.language_custom_input.setPlaceholderText("e.g. ind+eng+jpn")
        self.language_custom_input.setEnabled(False)

        self.psm_combo = _combo(self, PSM_MODES)
        self.oem_combo = _combo(self, OEM_MODES)

        self.dpi_input = QSpinBox(self)
        self.dpi_input.setRange(72, 600)
        self.dpi_input.setValue(300)
        self.dpi_input.setSuffix(" DPI")
        self.dpi_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.dpi_input.setAccelerated(True)

        self.auto_rotate_check = QCheckBox(
            "Auto-rotate pages via OSD pre-pass (PDF input only)", self
        )

        info = QLabel(
            "Languages depend on installed `tesseract-ocr-<lang>` packages "
            "(default install ships eng + osd). PSM tunes page segmentation; "
            "use 6 for a single block, 7 for a single line. DPI and auto-rotate "
            "apply only when the input is a PDF.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Language", self), 0, 0)
        grid.addWidget(self.language_combo, 0, 1)
        grid.addWidget(_field("Custom", self), 0, 2)
        grid.addWidget(self.language_custom_input, 0, 3)
        grid.addWidget(_field("Page mode", self), 1, 0)
        grid.addWidget(self.psm_combo, 1, 1)
        grid.addWidget(_field("Engine mode", self), 1, 2)
        grid.addWidget(self.oem_combo, 1, 3)
        grid.addWidget(_field("PDF render DPI", self), 2, 0)
        grid.addWidget(self.dpi_input, 2, 1)
        grid.addWidget(self.auto_rotate_check, 2, 2, 1, 2)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def _toggle_custom_language(self, _index: int) -> None:
        is_custom = self.language_combo.currentData() == "__custom__"
        self.language_custom_input.setEnabled(is_custom)
        if not is_custom:
            self.language_custom_input.clear()

    def collect_options(self) -> dict:
        options: dict[str, object] = {}

        language = self.language_combo.currentData()
        if language == "__custom__":
            language = self.language_custom_input.text().strip() or "eng"
        if language and language != "eng":
            options["ocr_language"] = language

        psm = self.psm_combo.currentData()
        if psm is not None and psm != 3:
            options["ocr_psm"] = psm

        oem = self.oem_combo.currentData()
        if oem is not None and oem != 3:
            options["ocr_oem"] = oem

        dpi = self.dpi_input.value()
        if dpi != 300:
            options["ocr_dpi"] = dpi

        if self.auto_rotate_check.isChecked():
            options["ocr_auto_rotate"] = True

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
