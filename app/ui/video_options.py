from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
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
    QAbstractSpinBox = QCheckBox = QComboBox = QDoubleSpinBox = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QSlider = QSpinBox = QTabWidget = QVBoxLayout = QWidget = None


ROTATIONS = (
    ("0°", 0),
    ("90° CW", 90),
    ("180°", 180),
    ("90° CCW (270°)", 270),
)
RESOLUTION_PRESETS = (
    ("Source", ""),
    ("4K (3840w)", "4k"),
    ("1440p (2560w)", "1440p"),
    ("1080p (1920w)", "1080p"),
    ("720p (1280w)", "720p"),
    ("480p (854w)", "480p"),
    ("360p (640w)", "360p"),
)
COMPRESS_PRESETS = (
    ("ultrafast", "ultrafast"),
    ("superfast", "superfast"),
    ("veryfast", "veryfast"),
    ("faster", "faster"),
    ("fast", "fast"),
    ("medium", "medium"),
    ("slow", "slow"),
    ("slower", "slower"),
    ("veryslow", "veryslow"),
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


class VideoOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("VideoOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(self)
        tabs.setObjectName("VideoOptionsTabs")
        tabs.setDocumentMode(True)
        tabs.setUsesScrollButtons(False)
        layout.addWidget(tabs)

        tabs.addTab(self._build_trim_page(tabs), "Trim")
        tabs.addTab(self._build_transform_page(tabs), "Transform")
        tabs.addTab(self._build_resize_page(tabs), "Resize")
        tabs.addTab(self._build_compress_page(tabs), "Compress")
        tabs.addTab(self._build_watermark_page(tabs), "Watermark")

    def _build_trim_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.trim_start_input = QLineEdit(page)
        self.trim_start_input.setPlaceholderText("00:00:10 (empty = from start)")
        self.trim_end_input = QLineEdit(page)
        self.trim_end_input.setPlaceholderText("00:01:30 (empty = until end)")

        info = QLabel(
            "Use HH:MM:SS or seconds. Trim re-encodes the cut region.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Start", page), 0, 0)
        grid.addWidget(self.trim_start_input, 0, 1)
        grid.addWidget(_field("End", page), 1, 0)
        grid.addWidget(self.trim_end_input, 1, 1)
        grid.addWidget(info, 2, 0, 1, 2)
        return page

    def _build_transform_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.rotate_combo = _combo(page, ROTATIONS)
        self.flip_h_check = QCheckBox("Flip horizontal", page)
        self.flip_v_check = QCheckBox("Flip vertical", page)
        self.crop_input = QLineEdit(page)
        self.crop_input.setPlaceholderText("WxH+X+Y (empty = no crop)")

        self.speed_input = QDoubleSpinBox(page)
        self.speed_input.setRange(0.5, 2.0)
        self.speed_input.setSingleStep(0.1)
        self.speed_input.setDecimals(2)
        self.speed_input.setValue(1.0)
        self.speed_input.setSuffix("x")
        _use_stepper(self.speed_input)

        grid.addWidget(_field("Rotate", page), 0, 0)
        grid.addWidget(self.rotate_combo, 0, 1)
        grid.addWidget(_field("Speed", page), 0, 2)
        grid.addWidget(self.speed_input, 0, 3)

        grid.addWidget(self.flip_h_check, 1, 0, 1, 2)
        grid.addWidget(self.flip_v_check, 1, 2, 1, 2)

        grid.addWidget(_field("Free crop", page), 2, 0)
        grid.addWidget(self.crop_input, 2, 1, 1, 3)
        return page

    def _build_resize_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.resolution_combo = _combo(page, RESOLUTION_PRESETS)

        info = QLabel(
            "Width-locked scale; height auto-calculated to keep aspect ratio.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Preset", page), 0, 0)
        grid.addWidget(self.resolution_combo, 0, 1)
        grid.addWidget(info, 1, 0, 1, 2)
        return page

    def _build_compress_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.crf_slider, self.crf_label = _slider(page, 0, 51, 0)
        self.compress_preset_combo = _combo(page, COMPRESS_PRESETS)
        for index, (_, value) in enumerate(COMPRESS_PRESETS):
            if value == "medium":
                self.compress_preset_combo.setCurrentIndex(index)
                break

        info = QLabel(
            "CRF 0 = disabled, 18 ≈ visually lossless, 23 default, 28 small file. "
            "Forces libx264 when set on a non-audio output.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("CRF", page), 0, 0)
        grid.addLayout(_slider_row(self.crf_slider, self.crf_label), 0, 1, 1, 3)
        grid.addWidget(_field("Preset", page), 1, 0)
        grid.addWidget(self.compress_preset_combo, 1, 1)
        grid.addWidget(info, 2, 0, 1, 4)
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

        self.watermark_size_input = QSpinBox(page)
        self.watermark_size_input.setRange(8, 200)
        self.watermark_size_input.setValue(36)
        self.watermark_size_input.setSuffix(" pt")
        _use_stepper(self.watermark_size_input)

        self.watermark_opacity_slider, self.watermark_opacity_label = _slider(
            page, 0, 100, 60, suffix="%"
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

    def collect_options(self) -> dict:
        options: dict[str, object] = {}

        start = self.trim_start_input.text().strip()
        if start:
            options["trim_start"] = start
        end = self.trim_end_input.text().strip()
        if end:
            options["trim_end"] = end

        rotation = self.rotate_combo.currentData()
        if rotation:
            options["rotation_degrees"] = rotation
        if self.flip_h_check.isChecked():
            options["flip_horizontal"] = True
        if self.flip_v_check.isChecked():
            options["flip_vertical"] = True
        crop = self.crop_input.text().strip()
        if crop:
            options["crop"] = crop

        speed = round(self.speed_input.value(), 2)
        if abs(speed - 1.0) > 1e-3:
            options["speed"] = speed

        resolution = self.resolution_combo.currentData()
        if resolution:
            options["resolution_preset"] = resolution

        crf = self.crf_slider.value()
        if crf > 0:
            options["crf"] = crf
            preset = self.compress_preset_combo.currentData()
            if preset:
                options["compress_preset"] = preset

        watermark = self.watermark_text_input.text().strip()
        if watermark:
            options["watermark_text"] = watermark
            options["watermark_position"] = (
                self.watermark_position_combo.currentData() or "southeast"
            )
            options["watermark_size"] = self.watermark_size_input.value()
            options["watermark_opacity"] = self.watermark_opacity_slider.value()

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
