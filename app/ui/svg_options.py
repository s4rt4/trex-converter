from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QCheckBox,
        QComboBox,
        QGridLayout,
        QLabel,
        QLineEdit,
        QListView,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QAbstractSpinBox = QCheckBox = QComboBox = QGridLayout = QLabel = QLineEdit = QListView = QSpinBox = QVBoxLayout = QWidget = None


SVG_SVG_OPERATIONS = (
    ("Cleanup (plain SVG + vacuum defs)", "cleanup"),
    ("Trim to content (crop viewBox to drawing)", "trim"),
)

PS_LEVELS = (
    ("Auto (3)", 0),
    ("PostScript level 2", 2),
    ("PostScript level 3", 3),
)


class SVGOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SVGOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.dpi_input = QSpinBox(self)
        self.dpi_input.setRange(0, 2400)
        self.dpi_input.setValue(0)
        self.dpi_input.setSuffix(" dpi")
        self.dpi_input.setSpecialValueText("auto (96)")
        _use_stepper(self.dpi_input)

        self.width_input = QSpinBox(self)
        self.width_input.setRange(0, 32768)
        self.width_input.setValue(0)
        self.width_input.setSuffix(" px")
        self.width_input.setSpecialValueText("auto")
        _use_stepper(self.width_input)

        self.height_input = QSpinBox(self)
        self.height_input.setRange(0, 32768)
        self.height_input.setValue(0)
        self.height_input.setSuffix(" px")
        self.height_input.setSpecialValueText("auto")
        _use_stepper(self.height_input)

        self.operation_combo = QComboBox(self)
        self.operation_combo.setView(QListView(self.operation_combo))
        for label, value in SVG_SVG_OPERATIONS:
            self.operation_combo.addItem(label, value)

        self.ps_level_combo = QComboBox(self)
        self.ps_level_combo.setView(QListView(self.ps_level_combo))
        for label, value in PS_LEVELS:
            self.ps_level_combo.addItem(label, value)

        self.pdf_page_input = QSpinBox(self)
        self.pdf_page_input.setRange(1, 9999)
        self.pdf_page_input.setValue(1)
        self.pdf_page_input.setSuffix("")
        _use_stepper(self.pdf_page_input)

        self.text_to_path_check = QCheckBox("Convert text → paths (PDF/EPS/PS/SVG)", self)

        self.export_id_input = QLineEdit(self)
        self.export_id_input.setPlaceholderText("e.g. logo (leave empty to export full document)")

        self.export_id_only_check = QCheckBox(
            "Hide other objects (export selected ID only)", self
        )

        info = QLabel(
            "DPI / Width / Height apply when output is PNG. "
            "Width/Height override DPI. SVG operation applies when output is SVG: "
            "cleanup strips Inkscape namespaces and unused defs; trim also crops "
            "the viewBox to the drawing's bounding box. PS level applies to EPS/PS "
            "output. PDF page applies when input is a PDF (which page to import). "
            "Text → paths embeds outlined glyphs so the output renders without the "
            "original font installed. Export ID restricts the output to a single "
            "object/layer by SVG id.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Raster DPI", self), 0, 0)
        grid.addWidget(self.dpi_input, 0, 1)
        grid.addWidget(_field("Width", self), 0, 2)
        grid.addWidget(self.width_input, 0, 3)
        grid.addWidget(_field("Height", self), 1, 2)
        grid.addWidget(self.height_input, 1, 3)
        grid.addWidget(_field("SVG operation", self), 2, 0)
        grid.addWidget(self.operation_combo, 2, 1, 1, 3)
        grid.addWidget(_field("PS level", self), 3, 0)
        grid.addWidget(self.ps_level_combo, 3, 1)
        grid.addWidget(_field("PDF page", self), 3, 2)
        grid.addWidget(self.pdf_page_input, 3, 3)
        grid.addWidget(self.text_to_path_check, 4, 0, 1, 4)
        grid.addWidget(_field("Export ID", self), 5, 0)
        grid.addWidget(self.export_id_input, 5, 1, 1, 3)
        grid.addWidget(self.export_id_only_check, 6, 0, 1, 4)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        dpi = self.dpi_input.value()
        if dpi > 0:
            options["inkscape_dpi"] = dpi
        width = self.width_input.value()
        if width > 0:
            options["inkscape_width"] = width
        height = self.height_input.value()
        if height > 0:
            options["inkscape_height"] = height
        operation = self.operation_combo.currentData()
        if operation:
            options["operation"] = operation
        ps_level = self.ps_level_combo.currentData()
        if ps_level:
            options["inkscape_ps_level"] = ps_level
        page = self.pdf_page_input.value()
        if page > 1:
            options["inkscape_pdf_page"] = page
        if self.text_to_path_check.isChecked():
            options["text_to_path"] = True
        export_id = self.export_id_input.text().strip()
        if export_id:
            options["inkscape_export_id"] = export_id
            if self.export_id_only_check.isChecked():
                options["inkscape_export_id_only"] = True
        return options


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


def _use_stepper(spinbox: QAbstractSpinBox) -> None:
    spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spinbox.setAccelerated(True)
