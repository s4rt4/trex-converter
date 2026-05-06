from __future__ import annotations

from pathlib import Path

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
        tabs.addTab(self._build_effects_page(tabs), "Effects")
        tabs.addTab(self._build_animation_page(tabs), "Animation")
        tabs.addTab(self._build_thumbnails_page(tabs), "Thumbnails")
        tabs.addTab(self._build_subtitles_page(tabs), "Subtitles")

    def _build_trim_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.trim_start_input = QLineEdit(page)
        self.trim_start_input.setPlaceholderText("00:00:10 (empty = from start)")
        self.trim_end_input = QLineEdit(page)
        self.trim_end_input.setPlaceholderText("00:01:30 (empty = until end)")
        self.stream_copy_check = QCheckBox(
            "Stream copy (no re-encode — fastest, may misalign on non-keyframe cuts)",
            page,
        )

        info = QLabel(
            "Use HH:MM:SS or seconds. Trim re-encodes the cut region by default. "
            "Enable stream copy to skip transcoding (filters/CRF will be ignored).",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Start", page), 0, 0)
        grid.addWidget(self.trim_start_input, 0, 1)
        grid.addWidget(_field("End", page), 1, 0)
        grid.addWidget(self.trim_end_input, 1, 1)
        grid.addWidget(self.stream_copy_check, 2, 0, 1, 2)
        grid.addWidget(info, 3, 0, 1, 2)
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

        self.target_size_input = QDoubleSpinBox(page)
        self.target_size_input.setRange(0.0, 102400.0)
        self.target_size_input.setDecimals(1)
        self.target_size_input.setSingleStep(5.0)
        self.target_size_input.setSuffix(" MB")
        self.target_size_input.setSpecialValueText("off")
        _use_stepper(self.target_size_input)

        info = QLabel(
            "CRF 0 = disabled, 18 ≈ visually lossless, 23 default, 28 small file. "
            "Target size triggers two-pass encode (probes duration via ffprobe, "
            "computes bitrate). Target overrides CRF.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("CRF", page), 0, 0)
        grid.addLayout(_slider_row(self.crf_slider, self.crf_label), 0, 1, 1, 3)
        grid.addWidget(_field("Preset", page), 1, 0)
        grid.addWidget(self.compress_preset_combo, 1, 1)
        grid.addWidget(_field("Target size", page), 1, 2)
        grid.addWidget(self.target_size_input, 1, 3)
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

    def _build_effects_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.reverse_check = QCheckBox("Reverse video (and audio)", page)

        self.logo_path_input = QLineEdit(page)
        self.logo_path_input.setPlaceholderText("/path/to/logo.png (empty = no logo)")
        self.logo_browse_button = QPushButton("Browse", page)
        self.logo_browse_button.clicked.connect(self._choose_logo)

        self.logo_position_combo = _combo(page, GRAVITIES)
        for index, (_, value) in enumerate(GRAVITIES):
            if value == "southeast":
                self.logo_position_combo.setCurrentIndex(index)
                break

        self.logo_width_input = QSpinBox(page)
        self.logo_width_input.setRange(16, 4096)
        self.logo_width_input.setValue(120)
        self.logo_width_input.setSuffix(" px")
        _use_stepper(self.logo_width_input)

        self.logo_opacity_slider, self.logo_opacity_label = _slider(
            page, 0, 100, 100, suffix="%"
        )

        info = QLabel(
            "Logo overlay scales the image to the chosen width and overlays it at the "
            "selected position. Reverse keeps audio in sync via areverse.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(self.reverse_check, 0, 0, 1, 4)
        grid.addWidget(_field("Logo path", page), 1, 0)
        logo_row = QHBoxLayout()
        logo_row.setSpacing(8)
        logo_row.addWidget(self.logo_path_input, 1)
        logo_row.addWidget(self.logo_browse_button)
        grid.addLayout(logo_row, 1, 1, 1, 3)
        grid.addWidget(_field("Position", page), 2, 0)
        grid.addWidget(self.logo_position_combo, 2, 1)
        grid.addWidget(_field("Width", page), 2, 2)
        grid.addWidget(self.logo_width_input, 2, 3)
        grid.addWidget(_field("Opacity", page), 3, 0)
        grid.addLayout(
            _slider_row(self.logo_opacity_slider, self.logo_opacity_label),
            3, 1, 1, 3,
        )
        grid.addWidget(info, 4, 0, 1, 4)
        return page

    def _build_animation_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.gif_fps_input = QSpinBox(page)
        self.gif_fps_input.setRange(1, 60)
        self.gif_fps_input.setValue(12)
        self.gif_fps_input.setSuffix(" fps")
        _use_stepper(self.gif_fps_input)

        self.gif_width_input = QSpinBox(page)
        self.gif_width_input.setRange(64, 4096)
        self.gif_width_input.setValue(480)
        self.gif_width_input.setSuffix(" px")
        _use_stepper(self.gif_width_input)

        self.webp_fps_input = QSpinBox(page)
        self.webp_fps_input.setRange(1, 60)
        self.webp_fps_input.setValue(15)
        self.webp_fps_input.setSuffix(" fps")
        _use_stepper(self.webp_fps_input)

        self.webp_width_input = QSpinBox(page)
        self.webp_width_input.setRange(64, 4096)
        self.webp_width_input.setValue(480)
        self.webp_width_input.setSuffix(" px")
        _use_stepper(self.webp_width_input)

        self.webp_quality_input = QSpinBox(page)
        self.webp_quality_input.setRange(0, 100)
        self.webp_quality_input.setValue(75)
        _use_stepper(self.webp_quality_input)

        info = QLabel(
            "These options apply when output format is gif or webp. Lower fps and "
            "width keep file size down. WebP quality 0–100 (75 default).",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("GIF fps", page), 0, 0)
        grid.addWidget(self.gif_fps_input, 0, 1)
        grid.addWidget(_field("GIF width", page), 0, 2)
        grid.addWidget(self.gif_width_input, 0, 3)
        grid.addWidget(_field("WebP fps", page), 1, 0)
        grid.addWidget(self.webp_fps_input, 1, 1)
        grid.addWidget(_field("WebP width", page), 1, 2)
        grid.addWidget(self.webp_width_input, 1, 3)
        grid.addWidget(_field("WebP quality", page), 2, 0)
        grid.addWidget(self.webp_quality_input, 2, 1)
        grid.addWidget(info, 3, 0, 1, 4)
        return page

    def _build_thumbnails_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.thumbnail_grid_check = QCheckBox(
            "Build contact sheet (PNG/JPG output)", page
        )
        self.thumbnail_grid_check.setChecked(True)

        self.thumbnail_rows_input = QSpinBox(page)
        self.thumbnail_rows_input.setRange(1, 16)
        self.thumbnail_rows_input.setValue(4)
        _use_stepper(self.thumbnail_rows_input)

        self.thumbnail_cols_input = QSpinBox(page)
        self.thumbnail_cols_input.setRange(1, 16)
        self.thumbnail_cols_input.setValue(4)
        _use_stepper(self.thumbnail_cols_input)

        self.thumbnail_interval_input = QSpinBox(page)
        self.thumbnail_interval_input.setRange(1, 100000)
        self.thumbnail_interval_input.setValue(60)
        self.thumbnail_interval_input.setSuffix(" frames")
        _use_stepper(self.thumbnail_interval_input)

        self.thumbnail_tile_width_input = QSpinBox(page)
        self.thumbnail_tile_width_input.setRange(64, 4096)
        self.thumbnail_tile_width_input.setValue(320)
        self.thumbnail_tile_width_input.setSuffix(" px")
        _use_stepper(self.thumbnail_tile_width_input)

        info = QLabel(
            "Contact sheet picks every Nth frame, scales each tile, and arranges "
            "them in a grid. Disable to extract a single frame at the trim start.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(self.thumbnail_grid_check, 0, 0, 1, 4)
        grid.addWidget(_field("Rows", page), 1, 0)
        grid.addWidget(self.thumbnail_rows_input, 1, 1)
        grid.addWidget(_field("Cols", page), 1, 2)
        grid.addWidget(self.thumbnail_cols_input, 1, 3)
        grid.addWidget(_field("Interval", page), 2, 0)
        grid.addWidget(self.thumbnail_interval_input, 2, 1)
        grid.addWidget(_field("Tile width", page), 2, 2)
        grid.addWidget(self.thumbnail_tile_width_input, 2, 3)
        grid.addWidget(info, 3, 0, 1, 4)
        return page

    def _build_subtitles_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.burn_subtitle_input = QLineEdit(page)
        self.burn_subtitle_input.setPlaceholderText(
            "/path/to/sub.srt (empty = no burn-in)"
        )
        self.burn_subtitle_browse = QPushButton("Browse", page)
        self.burn_subtitle_browse.clicked.connect(self._choose_subtitle)

        info = QLabel(
            "Burn-in hardcodes subtitles into the video using FFmpeg's subtitles "
            "filter (.srt/.vtt) or ass filter (.ass/.ssa). The subtitle file is "
            "embedded into every output frame.",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Subtitle file", page), 0, 0)
        sub_row = QHBoxLayout()
        sub_row.setSpacing(8)
        sub_row.addWidget(self.burn_subtitle_input, 1)
        sub_row.addWidget(self.burn_subtitle_browse)
        grid.addLayout(sub_row, 0, 1, 1, 3)
        grid.addWidget(info, 1, 0, 1, 4)
        return page

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose logo image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if path:
            self.logo_path_input.setText(path)

    def _choose_subtitle(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose subtitle file",
            "",
            "Subtitles (*.srt *.vtt *.ass *.ssa)",
        )
        if path:
            self.burn_subtitle_input.setText(path)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}

        start = self.trim_start_input.text().strip()
        if start:
            options["trim_start"] = start
        end = self.trim_end_input.text().strip()
        if end:
            options["trim_end"] = end
        if self.stream_copy_check.isChecked():
            options["stream_copy"] = True

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

        target_size = round(self.target_size_input.value(), 1)
        if target_size > 0.0:
            options["target_size_mb"] = target_size
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

        if self.reverse_check.isChecked():
            options["reverse_video"] = True

        logo_path = self.logo_path_input.text().strip()
        if logo_path:
            options["logo_path"] = logo_path
            options["logo_position"] = (
                self.logo_position_combo.currentData() or "southeast"
            )
            options["logo_width"] = self.logo_width_input.value()
            options["logo_opacity"] = self.logo_opacity_slider.value()

        if self.thumbnail_grid_check.isChecked():
            options["thumbnail_grid"] = True
            options["thumbnail_rows"] = self.thumbnail_rows_input.value()
            options["thumbnail_cols"] = self.thumbnail_cols_input.value()
            options["thumbnail_interval"] = self.thumbnail_interval_input.value()
            options["thumbnail_tile_width"] = self.thumbnail_tile_width_input.value()

        options["gif_fps"] = self.gif_fps_input.value()
        options["gif_width"] = self.gif_width_input.value()
        options["webp_fps"] = self.webp_fps_input.value()
        options["webp_width"] = self.webp_width_input.value()
        options["webp_quality"] = self.webp_quality_input.value()

        burn_path = self.burn_subtitle_input.text().strip()
        if burn_path:
            options["burn_subtitle_path"] = burn_path

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
