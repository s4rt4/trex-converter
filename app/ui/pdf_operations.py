from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QPushButton,
        QSlider,
        QSpinBox,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QAbstractSpinBox = QCheckBox = QComboBox = QFileDialog = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QPushButton = QSlider = QSpinBox = QTabWidget = QVBoxLayout = QWidget = None


PAGE_ACTIONS = (
    ("Extract pages", "extract_pages"),
    ("Reorder pages", "reorder"),
    ("Rotate pages", "rotate"),
)
SECURITY_ACTIONS = (
    ("Encrypt", "encrypt"),
    ("Decrypt", "decrypt"),
)
COMPRESS_ACTIONS = (
    ("Compress (PyMuPDF garbage + deflate)", "compress"),
    ("Repair (qpdf round-trip)", "repair"),
)
METADATA_ACTIONS = (
    ("Strip all metadata", "strip_metadata"),
    ("Edit metadata fields", "edit_metadata"),
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
REDACT_COLORS = (
    ("Black", "black"),
    ("White", "white"),
    ("Red", "red"),
    ("Yellow", "yellow"),
)
TAB_OPERATIONS = ("pages", "security", "compress", "watermark", "redact", "metadata")


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
        self.tabs.addTab(self._build_redact_tab(self.tabs), "Redact")
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

        self.compress_action_combo = _combo(page, COMPRESS_ACTIONS)

        info = QLabel(
            "Compress: PyMuPDF garbage-collect + dedupe + deflate.\n"
            "Repair: round-trip through qpdf to recover from minor corruption.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Action", page), 0, 0)
        grid.addWidget(self.compress_action_combo, 0, 1)
        grid.addWidget(info, 1, 0, 1, 2)
        return page

    def _build_watermark_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.watermark_text_input = QLineEdit(page)
        self.watermark_text_input.setPlaceholderText("e.g. CONFIDENTIAL")

        self.watermark_image_input = QLineEdit(page)
        self.watermark_image_input.setPlaceholderText("/path/to/logo.png (empty = text watermark)")
        self.watermark_image_browse = QPushButton("Browse", page)
        self.watermark_image_browse.clicked.connect(self._choose_watermark_image)

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

        self.watermark_image_width_input = QSpinBox(page)
        self.watermark_image_width_input.setRange(5, 100)
        self.watermark_image_width_input.setValue(25)
        self.watermark_image_width_input.setSuffix(" % page")
        _use_stepper(self.watermark_image_width_input)

        self.watermark_opacity_slider, self.watermark_opacity_label = _slider(
            page, 5, 100, 35, suffix="%"
        )

        grid.addWidget(_field("Text", page), 0, 0)
        grid.addWidget(self.watermark_text_input, 0, 1, 1, 3)
        grid.addWidget(_field("Image", page), 1, 0)
        image_row = QHBoxLayout()
        image_row.setSpacing(8)
        image_row.addWidget(self.watermark_image_input, 1)
        image_row.addWidget(self.watermark_image_browse)
        grid.addLayout(image_row, 1, 1, 1, 3)
        grid.addWidget(_field("Position", page), 2, 0)
        grid.addWidget(self.watermark_position_combo, 2, 1)
        grid.addWidget(_field("Text size", page), 2, 2)
        grid.addWidget(self.watermark_size_input, 2, 3)
        grid.addWidget(_field("Image width", page), 3, 0)
        grid.addWidget(self.watermark_image_width_input, 3, 1)
        grid.addWidget(_field("Opacity", page), 4, 0)
        grid.addLayout(
            _slider_row(self.watermark_opacity_slider, self.watermark_opacity_label),
            4,
            1,
            1,
            3,
        )
        return page

    def _choose_watermark_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose watermark image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if path:
            self.watermark_image_input.setText(path)

    def _build_redact_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.redact_terms_input = QLineEdit(page)
        self.redact_terms_input.setPlaceholderText(
            "Comma-separated, e.g. John Doe, 555-0100, secret"
        )
        self.redact_color_combo = _combo(page, REDACT_COLORS)
        self.redact_pages_input = QLineEdit(page)
        self.redact_pages_input.setPlaceholderText("1-3,5 (empty = all pages)")

        info = QLabel(
            "Search-and-redact: each term is located on every page (case-sensitive) "
            "and overwritten with the chosen fill color. The original glyphs are "
            "removed via apply_redactions, not just covered.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Search terms", page), 0, 0)
        grid.addWidget(self.redact_terms_input, 0, 1, 1, 3)
        grid.addWidget(_field("Color", page), 1, 0)
        grid.addWidget(self.redact_color_combo, 1, 1)
        grid.addWidget(_field("Pages", page), 1, 2)
        grid.addWidget(self.redact_pages_input, 1, 3)
        grid.addWidget(info, 2, 0, 1, 4)
        return page

    def _build_metadata_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.metadata_action_combo = _combo(page, METADATA_ACTIONS)
        self.meta_title_input = QLineEdit(page)
        self.meta_author_input = QLineEdit(page)
        self.meta_subject_input = QLineEdit(page)
        self.meta_keywords_input = QLineEdit(page)
        self.meta_creator_input = QLineEdit(page)

        info = QLabel(
            "Strip clears all metadata. Edit writes only the fields you fill in; "
            "empty fields are skipped.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Action", page), 0, 0)
        grid.addWidget(self.metadata_action_combo, 0, 1, 1, 3)
        grid.addWidget(_field("Title", page), 1, 0)
        grid.addWidget(self.meta_title_input, 1, 1, 1, 3)
        grid.addWidget(_field("Author", page), 2, 0)
        grid.addWidget(self.meta_author_input, 2, 1)
        grid.addWidget(_field("Subject", page), 2, 2)
        grid.addWidget(self.meta_subject_input, 2, 3)
        grid.addWidget(_field("Keywords", page), 3, 0)
        grid.addWidget(self.meta_keywords_input, 3, 1, 1, 3)
        grid.addWidget(_field("Creator", page), 4, 0)
        grid.addWidget(self.meta_creator_input, 4, 1, 1, 3)
        grid.addWidget(info, 5, 0, 1, 4)
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

        if tab == "compress":
            return {
                "operation": self.compress_action_combo.currentData() or "compress",
            }

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

        if tab == "watermark":
            text = self.watermark_text_input.text().strip()
            image_path = self.watermark_image_input.text().strip()
            position = self.watermark_position_combo.currentData() or "center"
            opacity = self.watermark_opacity_slider.value()
            if image_path:
                options = {
                    "operation": "watermark_image",
                    "watermark_image_path": image_path,
                    "watermark_position": position,
                    "watermark_image_width_fraction": (
                        self.watermark_image_width_input.value() / 100.0
                    ),
                    "watermark_opacity": opacity,
                }
                if text:
                    options["watermark_text"] = text
                return options
            options = {"operation": "watermark_text"}
            if text:
                options["watermark_text"] = text
                options["watermark_position"] = position
                options["watermark_size"] = self.watermark_size_input.value()
                options["watermark_opacity"] = opacity
            return options

        if tab == "redact":
            terms = self.redact_terms_input.text().strip()
            options = {
                "operation": "redact",
                "redact_terms": terms,
                "redact_color": self.redact_color_combo.currentData() or "black",
            }
            pages = self.redact_pages_input.text().strip()
            if pages:
                options["pages"] = pages
            return options

        if tab == "metadata":
            action = self.metadata_action_combo.currentData() or "strip_metadata"
            options = {"operation": action}
            if action == "edit_metadata":
                for option_key, widget in (
                    ("title", self.meta_title_input),
                    ("author", self.meta_author_input),
                    ("subject", self.meta_subject_input),
                    ("keywords", self.meta_keywords_input),
                    ("creator", self.meta_creator_input),
                ):
                    value = widget.text().strip()
                    if value:
                        options[f"meta_{option_key}"] = value
            return options

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
