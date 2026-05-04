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
        QSlider,
        QSpinBox,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QAbstractSpinBox = QCheckBox = QComboBox = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QSlider = QSpinBox = QTabWidget = QVBoxLayout = QWidget = None


PAGE_ACTIONS = (
    ("Extract pages", "extract_pages"),
    ("Rotate pages", "rotate"),
)
SECURITY_ACTIONS = (
    ("Encrypt", "encrypt"),
    ("Decrypt", "decrypt"),
)
ROTATIONS = (
    ("90° CW", 90),
    ("180°", 180),
    ("270° (90° CCW)", 270),
)
GRAVITIES = (
    ("Top-Left", "northwest"),
    ("Top", "north"),
    ("Top-Right", "northeast"),
    ("Left", "west"),
    ("Center", "center"),
    ("Right", "east"),
    ("Bottom-Left", "southwest"),
    ("Bottom", "south"),
    ("Bottom-Right", "southeast"),
)
TAB_OPERATIONS = ("pages", "security", "compress", "watermark", "metadata")


class PDFOperationsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PDFOperationsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("PDFOperationsTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(False)
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_pages_tab(self.tabs), "Pages")
        self.tabs.addTab(self._build_security_tab(self.tabs), "Security")
        self.tabs.addTab(self._build_compress_tab(self.tabs), "Compress")
        self.tabs.addTab(self._build_watermark_tab(self.tabs), "Watermark")
        self.tabs.addTab(self._build_metadata_tab(self.tabs), "Metadata")

    def _build_pages_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.pages_action_combo = _combo(page, PAGE_ACTIONS)
        self.pages_range_input = QLineEdit(page)
        self.pages_range_input.setPlaceholderText("1-3,5,8-10 (empty = all pages)")
        self.pages_rotation_combo = _combo(page, ROTATIONS)

        grid.addWidget(_field("Action", page), 0, 0)
        grid.addWidget(self.pages_action_combo, 0, 1)
        grid.addWidget(_field("Pages", page), 1, 0)
        grid.addWidget(self.pages_range_input, 1, 1)
        grid.addWidget(_field("Rotation", page), 2, 0)
        grid.addWidget(self.pages_rotation_combo, 2, 1)
        return page

    def _build_security_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.security_action_combo = _combo(page, SECURITY_ACTIONS)
        self.user_password_input = QLineEdit(page)
        self.user_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.user_password_input.setPlaceholderText("Required to open the PDF")
        self.owner_password_input = QLineEdit(page)
        self.owner_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.owner_password_input.setPlaceholderText(
            "Optional, controls editing permissions"
        )

        grid.addWidget(_field("Action", page), 0, 0)
        grid.addWidget(self.security_action_combo, 0, 1)
        grid.addWidget(_field("User password", page), 1, 0)
        grid.addWidget(self.user_password_input, 1, 1)
        grid.addWidget(_field("Owner password", page), 2, 0)
        grid.addWidget(self.owner_password_input, 2, 1)
        return page

    def _build_compress_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        info = QLabel(
            "Garbage-collect, dedupe, and deflate the PDF stream via PyMuPDF.\n"
            "No additional options for this action.",
            page,
        )
        info.setWordWrap(True)
        grid.addWidget(info, 0, 0, 1, 2)
        return page

    def _build_watermark_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.watermark_text_input = QLineEdit(page)
        self.watermark_text_input.setPlaceholderText("e.g. CONFIDENTIAL")

        self.watermark_position_combo = _combo(page, GRAVITIES)
        for index, (_, value) in enumerate(GRAVITIES):
            if value == "center":
                self.watermark_position_combo.setCurrentIndex(index)
                break

        self.watermark_size_input = QSpinBox(page)
        self.watermark_size_input.setRange(8, 200)
        self.watermark_size_input.setValue(48)
        self.watermark_size_input.setSuffix(" pt")
        _use_stepper(self.watermark_size_input)

        self.watermark_opacity_slider, self.watermark_opacity_label = _slider(
            page, 5, 100, 35, suffix="%"
        )

        grid.addWidget(_field("Text", page), 0, 0)
        grid.addWidget(self.watermark_text_input, 0, 1, 1, 3)
        grid.addWidget(_field("Position", page), 1, 0)
        grid.addWidget(self.watermark_position_combo, 1, 1)
        grid.addWidget(_field("Size", page), 1, 2)
        grid.addWidget(self.watermark_size_input, 1, 3)
        grid.addWidget(_field("Opacity", page), 2, 0)
        grid.addLayout(
            _slider_row(self.watermark_opacity_slider, self.watermark_opacity_label),
            2,
            1,
            1,
            3,
        )
        return page

    def _build_metadata_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        info = QLabel(
            "Strip all PDF metadata (title, author, subject, keywords, producer).\n"
            "No additional options for this action.",
            page,
        )
        info.setWordWrap(True)
        grid.addWidget(info, 0, 0, 1, 2)
        return page

    def collect_options(self) -> dict:
        index = self.tabs.currentIndex()
        if index < 0 or index >= len(TAB_OPERATIONS):
            return {}

        tab = TAB_OPERATIONS[index]
        if tab == "pages":
            action = self.pages_action_combo.currentData() or "extract_pages"
            options: dict[str, object] = {"operation": action}
            page_range = self.pages_range_input.text().strip()
            if page_range:
                options["pages"] = page_range
            if action == "rotate":
                options["rotation_degrees"] = self.pages_rotation_combo.currentData() or 90
            return options

        if tab == "security":
            action = self.security_action_combo.currentData() or "encrypt"
            options = {"operation": action}
            user_pw = self.user_password_input.text()
            owner_pw = self.owner_password_input.text()
            if action == "encrypt":
                if user_pw:
                    options["password_user"] = user_pw
                if owner_pw:
                    options["password_owner"] = owner_pw
            elif action == "decrypt":
                if user_pw:
                    options["password"] = user_pw
            return options

        if tab == "compress":
            return {"operation": "compress"}

        if tab == "watermark":
            text = self.watermark_text_input.text().strip()
            options = {"operation": "watermark_text"}
            if text:
                options["watermark_text"] = text
                options["watermark_position"] = (
                    self.watermark_position_combo.currentData() or "center"
                )
                options["watermark_size"] = self.watermark_size_input.value()
                options["watermark_opacity"] = self.watermark_opacity_slider.value()
            return options

        if tab == "metadata":
            return {"operation": "strip_metadata"}

        return {}


def _combo(parent: QWidget, items: tuple[tuple[str, object], ...]) -> QComboBox:
    combo = QComboBox(parent)
    combo.setView(QListView(combo))
    for label, value in items:
        combo.addItem(label, value)
    return combo


def _slider(
    parent: QWidget,
    minimum: int,
    maximum: int,
    initial: int,
    suffix: str = "",
) -> tuple[QSlider, QLabel]:
    slider = QSlider(Qt.Orientation.Horizontal, parent)
    slider.setRange(minimum, maximum)
    slider.setValue(initial)
    label = QLabel(f"{initial}{suffix}", parent)
    slider.valueChanged.connect(lambda value: label.setText(f"{value}{suffix}"))
    return slider, label


def _slider_row(slider: QSlider, label: QLabel) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)
    row.addWidget(slider, 1)
    row.addWidget(label)
    return row


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


def _use_stepper(spinbox: QAbstractSpinBox) -> None:
    spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spinbox.setAccelerated(True)


def _grid_setup(grid: QGridLayout) -> None:
    grid.setContentsMargins(12, 12, 12, 12)
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(10)
    grid.setColumnMinimumWidth(0, 110)
    grid.setColumnMinimumWidth(2, 96)
    grid.setColumnStretch(1, 1)
    grid.setColumnStretch(3, 1)
