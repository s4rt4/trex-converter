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
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QAbstractSpinBox = QCheckBox = QComboBox = QDoubleSpinBox = QGridLayout = QLabel = QLineEdit = QListView = QSpinBox = QTabWidget = QVBoxLayout = QWidget = None


SVG_SVG_OPERATIONS = (
    ("Cleanup (plain SVG + vacuum defs)", "cleanup"),
    ("Trim to content (crop viewBox to drawing)", "trim"),
)

PS_LEVELS = (
    ("Auto (3)", 0),
    ("PostScript level 2", 2),
    ("PostScript level 3", 3),
)

DXF_FORMATS = (
    ("DXF R14 (Desktop Cutting Plotter)", "r14"),
    ("DXF R12 (legacy)", "r12"),
)


class SVGOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SVGOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(self)
        tabs.setObjectName("SVGOptionsTabs")
        tabs.addTab(self._build_raster_tab(), "Raster")
        tabs.addTab(self._build_vector_tab(), "Vector")
        tabs.addTab(self._build_trace_tab(), "Trace")
        layout.addWidget(tabs)

    def _build_raster_tab(self) -> QWidget:
        tab = QWidget(self)
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        grid = _grid()

        self.dpi_input = QSpinBox(tab)
        self.dpi_input.setRange(0, 2400)
        self.dpi_input.setValue(0)
        self.dpi_input.setSuffix(" dpi")
        self.dpi_input.setSpecialValueText("auto (96)")
        _use_stepper(self.dpi_input)

        self.width_input = QSpinBox(tab)
        self.width_input.setRange(0, 32768)
        self.width_input.setValue(0)
        self.width_input.setSuffix(" px")
        self.width_input.setSpecialValueText("auto")
        _use_stepper(self.width_input)

        self.height_input = QSpinBox(tab)
        self.height_input.setRange(0, 32768)
        self.height_input.setValue(0)
        self.height_input.setSuffix(" px")
        self.height_input.setSpecialValueText("auto")
        _use_stepper(self.height_input)

        grid.addWidget(_field("Raster DPI", tab), 0, 0)
        grid.addWidget(self.dpi_input, 0, 1)
        grid.addWidget(_field("Width", tab), 1, 0)
        grid.addWidget(self.width_input, 1, 1)
        grid.addWidget(_field("Height", tab), 2, 0)
        grid.addWidget(self.height_input, 2, 1)

        outer.addLayout(grid)
        outer.addWidget(_hint(
            "Applies to PNG output. Width/Height (px) override DPI when set.",
            tab,
        ))
        outer.addStretch(1)
        return tab

    def _build_vector_tab(self) -> QWidget:
        tab = QWidget(self)
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        grid = _grid()

        self.operation_combo = QComboBox(tab)
        self.operation_combo.setView(QListView(self.operation_combo))
        for label, value in SVG_SVG_OPERATIONS:
            self.operation_combo.addItem(label, value)

        self.ps_level_combo = QComboBox(tab)
        self.ps_level_combo.setView(QListView(self.ps_level_combo))
        for label, value in PS_LEVELS:
            self.ps_level_combo.addItem(label, value)

        self.pdf_page_input = QSpinBox(tab)
        self.pdf_page_input.setRange(1, 9999)
        self.pdf_page_input.setValue(1)
        _use_stepper(self.pdf_page_input)

        self.dxf_format_combo = QComboBox(tab)
        self.dxf_format_combo.setView(QListView(self.dxf_format_combo))
        for label, value in DXF_FORMATS:
            self.dxf_format_combo.addItem(label, value)

        self.text_to_path_check = QCheckBox(
            "Convert text → paths (PDF / EPS / PS / SVG output)", tab
        )

        self.export_id_input = QLineEdit(tab)
        self.export_id_input.setPlaceholderText(
            "e.g. logo (leave empty to export full document)"
        )
        self.export_id_only_check = QCheckBox(
            "Hide other objects (export selected ID only)", tab
        )

        grid.addWidget(_field("SVG operation", tab), 0, 0)
        grid.addWidget(self.operation_combo, 0, 1)
        grid.addWidget(_field("PS level", tab), 1, 0)
        grid.addWidget(self.ps_level_combo, 1, 1)
        grid.addWidget(_field("PDF page", tab), 2, 0)
        grid.addWidget(self.pdf_page_input, 2, 1)
        grid.addWidget(_field("DXF format", tab), 3, 0)
        grid.addWidget(self.dxf_format_combo, 3, 1)
        grid.addWidget(self.text_to_path_check, 4, 0, 1, 2)
        grid.addWidget(_field("Export ID", tab), 5, 0)
        grid.addWidget(self.export_id_input, 5, 1)
        grid.addWidget(self.export_id_only_check, 6, 0, 1, 2)

        outer.addLayout(grid)
        outer.addWidget(_hint(
            "SVG operation applies to SVG output. PS level → EPS/PS. "
            "PDF page → PDF input. DXF format → DXF output.",
            tab,
        ))
        outer.addStretch(1)
        return tab

    def _build_trace_tab(self) -> QWidget:
        tab = QWidget(self)
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        grid = _grid()

        self.trace_threshold_input = QDoubleSpinBox(tab)
        self.trace_threshold_input.setRange(0.0, 1.0)
        self.trace_threshold_input.setSingleStep(0.05)
        self.trace_threshold_input.setDecimals(2)
        self.trace_threshold_input.setValue(0.5)

        self.trace_turdsize_input = QSpinBox(tab)
        self.trace_turdsize_input.setRange(0, 1000)
        self.trace_turdsize_input.setValue(2)
        self.trace_turdsize_input.setSuffix(" px²")
        _use_stepper(self.trace_turdsize_input)

        grid.addWidget(_field("Threshold", tab), 0, 0)
        grid.addWidget(self.trace_threshold_input, 0, 1)
        grid.addWidget(_field("Turdsize", tab), 1, 0)
        grid.addWidget(self.trace_turdsize_input, 1, 1)

        outer.addLayout(grid)
        outer.addWidget(_hint(
            "Applies when input is a bitmap image and output is SVG. "
            "Threshold (0–1) sets black/white cutoff; turdsize filters tiny noise specks.",
            tab,
        ))
        outer.addStretch(1)
        return tab

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
        dxf_format = self.dxf_format_combo.currentData()
        if dxf_format and dxf_format != "r14":
            options["inkscape_dxf_format"] = dxf_format
        threshold = self.trace_threshold_input.value()
        if abs(threshold - 0.5) > 1e-6:
            options["trace_threshold"] = threshold
        turdsize = self.trace_turdsize_input.value()
        if turdsize != 2:
            options["trace_turdsize"] = turdsize
        return options


def _grid() -> QGridLayout:
    grid = QGridLayout()
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(10)
    grid.setColumnMinimumWidth(0, 110)
    grid.setColumnStretch(1, 1)
    return grid


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


def _hint(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("HintLabel")
    label.setWordWrap(True)
    return label


def _use_stepper(spinbox: QAbstractSpinBox) -> None:
    spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spinbox.setAccelerated(True)
