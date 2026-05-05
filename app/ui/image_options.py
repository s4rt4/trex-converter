from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
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
    QAbstractSpinBox = QCheckBox = QComboBox = QDoubleSpinBox = QFileDialog = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QPushButton = QSlider = QSpinBox = QTabWidget = QVBoxLayout = QWidget = None


RESIZE_MODES = (
    ("Dimension (e.g. 1280x720>)", "dimension"),
    ("Longest edge (px)", "longest_edge"),
    ("Percent (%)", "percent"),
    ("Megapixel target", "megapixel"),
)
ROTATIONS = (
    ("0°", 0),
    ("90° CW", 90),
    ("180°", 180),
    ("90° CCW", -90),
)
ASPECTS = (
    ("Free", "free"),
    ("Square 1:1", "1:1"),
    ("Portrait 4:5", "4:5"),
    ("Portrait 2:3", "2:3"),
    ("Portrait 9:16", "9:16"),
    ("Landscape 3:2", "3:2"),
    ("Landscape 16:9", "16:9"),
    ("Landscape 4:3", "4:3"),
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


class ImageOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ImageOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(self)
        tabs.setObjectName("ImageOptionsTabs")
        tabs.setDocumentMode(True)
        tabs.setUsesScrollButtons(False)
        layout.addWidget(tabs)

        tabs.addTab(self._build_transform_page(tabs), "Transform")
        tabs.addTab(self._build_color_page(tabs), "Color")
        tabs.addTab(self._build_filter_page(tabs), "Filter")
        tabs.addTab(self._build_border_page(tabs), "Border")
        tabs.addTab(self._build_watermark_page(tabs), "Watermark")

    def _build_transform_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.rotate_combo = _combo(page, ROTATIONS)
        self.crop_aspect_combo = _combo(page, ASPECTS)
        self.flip_check = QCheckBox("Flip vertical", page)
        self.flop_check = QCheckBox("Flip horizontal", page)
        self.auto_trim_check = QCheckBox("Auto-trim borders", page)
        self.crop_free_input = QLineEdit(page)
        self.crop_free_input.setPlaceholderText("WxH+X+Y (advanced)")

        self.resize_mode_combo = _combo(page, RESIZE_MODES)
        self.resize_input = QLineEdit(page)
        self.resize_input.setPlaceholderText("1280x1280>")
        self.resize_mode_combo.currentIndexChanged.connect(self._update_resize_placeholder)
        self.density_input = QSpinBox(page)
        self.density_input.setRange(0, 1200)
        self.density_input.setSpecialValueText("default")
        self.density_input.setValue(0)
        self.density_input.setSuffix(" dpi")
        _use_stepper(self.density_input)

        grid.addWidget(_field("Rotate", page), 0, 0)
        grid.addWidget(self.rotate_combo, 0, 1)
        grid.addWidget(_field("Aspect crop", page), 0, 2)
        grid.addWidget(self.crop_aspect_combo, 0, 3)

        grid.addWidget(self.flip_check, 1, 0, 1, 2)
        grid.addWidget(self.flop_check, 1, 2, 1, 2)
        grid.addWidget(self.auto_trim_check, 2, 0, 1, 2)
        grid.addWidget(_field("Free crop", page), 2, 2)
        grid.addWidget(self.crop_free_input, 2, 3)

        grid.addWidget(_field("Resize mode", page), 3, 0)
        grid.addWidget(self.resize_mode_combo, 3, 1)
        grid.addWidget(_field("Resize value", page), 3, 2)
        grid.addWidget(self.resize_input, 3, 3)
        grid.addWidget(_field("Density", page), 4, 0)
        grid.addWidget(self.density_input, 4, 1)

        return page

    def _build_color_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.grayscale_check = QCheckBox("Grayscale", page)
        self.negate_check = QCheckBox("Negate (invert)", page)
        self.normalize_check = QCheckBox("Normalize histogram", page)

        self.sepia_slider, self.sepia_label = _slider(page, 0, 100, 0, suffix="%")
        self.brightness_slider, self.brightness_label = _slider(page, -100, 100, 0)
        self.contrast_slider, self.contrast_label = _slider(page, -100, 100, 0)

        self.gamma_input = QDoubleSpinBox(page)
        self.gamma_input.setRange(0.1, 5.0)
        self.gamma_input.setSingleStep(0.1)
        self.gamma_input.setValue(1.0)
        _use_stepper(self.gamma_input)

        grid.addWidget(self.grayscale_check, 0, 0, 1, 2)
        grid.addWidget(self.negate_check, 0, 2, 1, 2)
        grid.addWidget(self.normalize_check, 1, 0, 1, 2)

        grid.addWidget(_field("Sepia", page), 2, 0)
        grid.addLayout(_slider_row(self.sepia_slider, self.sepia_label), 2, 1, 1, 3)
        grid.addWidget(_field("Brightness", page), 3, 0)
        grid.addLayout(_slider_row(self.brightness_slider, self.brightness_label), 3, 1, 1, 3)
        grid.addWidget(_field("Contrast", page), 4, 0)
        grid.addLayout(_slider_row(self.contrast_slider, self.contrast_label), 4, 1, 1, 3)
        grid.addWidget(_field("Gamma", page), 5, 0)
        grid.addWidget(self.gamma_input, 5, 1)

        return page

    def _build_filter_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.blur_input = QDoubleSpinBox(page)
        self.blur_input.setRange(0.0, 20.0)
        self.blur_input.setSingleStep(0.5)
        self.blur_input.setValue(0.0)
        _use_stepper(self.blur_input)

        self.sharpen_input = QDoubleSpinBox(page)
        self.sharpen_input.setRange(0.0, 10.0)
        self.sharpen_input.setSingleStep(0.5)
        self.sharpen_input.setValue(0.0)
        _use_stepper(self.sharpen_input)

        self.denoise_check = QCheckBox("Denoise (-enhance)", page)
        self.vignette_check = QCheckBox("Vignette", page)

        grid.addWidget(_field("Blur sigma", page), 0, 0)
        grid.addWidget(self.blur_input, 0, 1)
        grid.addWidget(_field("Sharpen sigma", page), 0, 2)
        grid.addWidget(self.sharpen_input, 0, 3)
        grid.addWidget(self.denoise_check, 1, 0, 1, 2)
        grid.addWidget(self.vignette_check, 1, 2, 1, 2)

        return page

    def _build_border_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.border_size_input = QSpinBox(page)
        self.border_size_input.setRange(0, 200)
        self.border_size_input.setSpecialValueText("none")
        self.border_size_input.setSuffix(" px")
        _use_stepper(self.border_size_input)

        self.border_color_input = QLineEdit(page)
        self.border_color_input.setPlaceholderText("black or #RRGGBB")

        self.frame_size_input = QSpinBox(page)
        self.frame_size_input.setRange(0, 200)
        self.frame_size_input.setSpecialValueText("none")
        self.frame_size_input.setSuffix(" px")
        _use_stepper(self.frame_size_input)

        grid.addWidget(_field("Border size", page), 0, 0)
        grid.addWidget(self.border_size_input, 0, 1)
        grid.addWidget(_field("Border color", page), 0, 2)
        grid.addWidget(self.border_color_input, 0, 3)
        grid.addWidget(_field("Frame size", page), 1, 0)
        grid.addWidget(self.frame_size_input, 1, 1)

        return page

    def _build_watermark_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.watermark_text_input = QLineEdit(page)
        self.watermark_text_input.setPlaceholderText("Leave empty to skip watermark")

        self.watermark_position_combo = _combo(page, GRAVITIES)
        for index, (_, value) in enumerate(GRAVITIES):
            if value == "southeast":
                self.watermark_position_combo.setCurrentIndex(index)
                break

        self.watermark_opacity_slider, self.watermark_opacity_label = _slider(
            page, 0, 100, 60, suffix="%"
        )
        self.watermark_size_input = QSpinBox(page)
        self.watermark_size_input.setRange(8, 200)
        self.watermark_size_input.setValue(36)
        self.watermark_size_input.setSuffix(" pt")
        _use_stepper(self.watermark_size_input)

        self.watermark_image_input = QLineEdit(page)
        self.watermark_image_input.setPlaceholderText("/path/to/logo.png (empty = no image)")
        self.watermark_image_browse = QPushButton("Browse", page)
        self.watermark_image_browse.clicked.connect(self._choose_watermark_image)

        self.watermark_image_width_input = QSpinBox(page)
        self.watermark_image_width_input.setRange(0, 4096)
        self.watermark_image_width_input.setValue(0)
        self.watermark_image_width_input.setSpecialValueText("source")
        self.watermark_image_width_input.setSuffix(" px")
        _use_stepper(self.watermark_image_width_input)

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
        grid.addWidget(_field("Image", page), 3, 0)
        image_row = QHBoxLayout()
        image_row.setSpacing(8)
        image_row.addWidget(self.watermark_image_input, 1)
        image_row.addWidget(self.watermark_image_browse)
        grid.addLayout(image_row, 3, 1, 1, 3)
        grid.addWidget(_field("Image width", page), 4, 0)
        grid.addWidget(self.watermark_image_width_input, 4, 1)

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

    def _update_resize_placeholder(self, _index: int) -> None:
        mode = self.resize_mode_combo.currentData()
        placeholders = {
            "dimension": "1280x1280>",
            "longest_edge": "1024",
            "percent": "75",
            "megapixel": "2.0",
        }
        self.resize_input.setPlaceholderText(placeholders.get(mode, ""))

    def collect_options(self) -> dict:
        options: dict[str, object] = {}

        rotate = self.rotate_combo.currentData()
        if rotate:
            options["rotate"] = rotate

        if self.flip_check.isChecked():
            options["flip"] = True
        if self.flop_check.isChecked():
            options["flop"] = True
        if self.auto_trim_check.isChecked():
            options["auto_trim"] = True

        aspect = self.crop_aspect_combo.currentData()
        if aspect and aspect != "free":
            options["crop_aspect"] = aspect

        crop_free = self.crop_free_input.text().strip()
        if crop_free:
            options["crop"] = crop_free

        resize_text = self.resize_input.text().strip()
        if resize_text:
            options["resize"] = resize_text
            options["resize_mode"] = self.resize_mode_combo.currentData() or "dimension"

        if self.density_input.value() > 0:
            options["density"] = self.density_input.value()

        if self.grayscale_check.isChecked():
            options["grayscale"] = True
        if self.negate_check.isChecked():
            options["negate"] = True
        if self.normalize_check.isChecked():
            options["normalize"] = True
        if self.sepia_slider.value() > 0:
            options["sepia"] = self.sepia_slider.value()
        if self.brightness_slider.value() != 0:
            options["brightness"] = self.brightness_slider.value()
        if self.contrast_slider.value() != 0:
            options["contrast"] = self.contrast_slider.value()
        if abs(self.gamma_input.value() - 1.0) > 1e-3:
            options["gamma"] = round(self.gamma_input.value(), 3)

        if self.blur_input.value() > 0:
            options["blur"] = round(self.blur_input.value(), 3)
        if self.sharpen_input.value() > 0:
            options["sharpen"] = round(self.sharpen_input.value(), 3)
        if self.denoise_check.isChecked():
            options["denoise"] = True
        if self.vignette_check.isChecked():
            options["vignette"] = True

        if self.border_size_input.value() > 0:
            options["border_size"] = self.border_size_input.value()
            color = self.border_color_input.text().strip()
            if color:
                options["border_color"] = color
        if self.frame_size_input.value() > 0:
            options["frame_size"] = self.frame_size_input.value()

        watermark_text = self.watermark_text_input.text().strip()
        if watermark_text:
            options["watermark_text"] = watermark_text
            options["watermark_position"] = (
                self.watermark_position_combo.currentData() or "southeast"
            )
            options["watermark_opacity"] = self.watermark_opacity_slider.value()
            options["watermark_size"] = self.watermark_size_input.value()

        watermark_image = self.watermark_image_input.text().strip()
        if watermark_image:
            options["watermark_image_path"] = watermark_image
            options["watermark_image_position"] = (
                self.watermark_position_combo.currentData() or "southeast"
            )
            options["watermark_image_opacity"] = self.watermark_opacity_slider.value()
            width = self.watermark_image_width_input.value()
            if width > 0:
                options["watermark_image_width"] = width

        return options


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
    grid.setColumnMinimumWidth(0, 96)
    grid.setColumnMinimumWidth(2, 96)
    grid.setColumnStretch(1, 1)
    grid.setColumnStretch(3, 1)
