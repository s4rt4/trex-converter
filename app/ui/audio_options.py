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
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QAbstractSpinBox = QCheckBox = QComboBox = QDoubleSpinBox = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QSlider = QTabWidget = QVBoxLayout = QWidget = None


CHANNEL_LAYOUTS = (
    ("Source", ""),
    ("Mono", "1"),
    ("Stereo", "2"),
)
SAMPLE_RATES = (
    ("Source", ""),
    ("22 050 Hz", "22050"),
    ("44 100 Hz", "44100"),
    ("48 000 Hz", "48000"),
    ("96 000 Hz", "96000"),
)


class AudioOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AudioOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(self)
        tabs.setObjectName("AudioOptionsTabs")
        tabs.setDocumentMode(True)
        tabs.setUsesScrollButtons(False)
        layout.addWidget(tabs)

        tabs.addTab(self._build_trim_page(tabs), "Trim")
        tabs.addTab(self._build_effects_page(tabs), "Effects")
        tabs.addTab(self._build_output_page(tabs), "Output")

    def _build_trim_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.trim_start_input = QLineEdit(page)
        self.trim_start_input.setPlaceholderText("00:00:10 (empty = from start)")
        self.trim_end_input = QLineEdit(page)
        self.trim_end_input.setPlaceholderText("00:01:30 (empty = until end)")

        info = QLabel("Use HH:MM:SS or seconds.", page)
        info.setWordWrap(True)

        grid.addWidget(_field("Start", page), 0, 0)
        grid.addWidget(self.trim_start_input, 0, 1)
        grid.addWidget(_field("End", page), 1, 0)
        grid.addWidget(self.trim_end_input, 1, 1)
        grid.addWidget(info, 2, 0, 1, 2)
        return page

    def _build_effects_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.fade_in_input = _seconds_spinbox(page, maximum=60.0)
        self.fade_out_start_input = _seconds_spinbox(page, maximum=86400.0)
        self.fade_out_duration_input = _seconds_spinbox(page, maximum=60.0)

        self.volume_slider, self.volume_label = _slider(page, -20, 20, 0, suffix=" dB")
        self.loudnorm_check = QCheckBox("Loudness normalize (EBU R128)", page)

        grid.addWidget(_field("Fade in", page), 0, 0)
        grid.addWidget(self.fade_in_input, 0, 1)
        grid.addWidget(_field("Fade out start", page), 0, 2)
        grid.addWidget(self.fade_out_start_input, 0, 3)
        grid.addWidget(_field("Fade out", page), 1, 0)
        grid.addWidget(self.fade_out_duration_input, 1, 1)
        grid.addWidget(_field("Volume", page), 2, 0)
        grid.addLayout(_slider_row(self.volume_slider, self.volume_label), 2, 1, 1, 3)
        grid.addWidget(self.loudnorm_check, 3, 0, 1, 4)

        info = QLabel(
            "Fade out start = seconds from clip start where fade-out begins. "
            "Loudnorm targets I=-16 LUFS.",
            page,
        )
        info.setWordWrap(True)
        grid.addWidget(info, 4, 0, 1, 4)
        return page

    def _build_output_page(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        grid = QGridLayout(page)
        _grid_setup(grid)

        self.channels_combo = _combo(page, CHANNEL_LAYOUTS)
        self.sample_rate_combo = _combo(page, SAMPLE_RATES)

        info = QLabel(
            "Bitrate input lives on the main convert form (top of the page).",
            page,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Channels", page), 0, 0)
        grid.addWidget(self.channels_combo, 0, 1)
        grid.addWidget(_field("Sample rate", page), 1, 0)
        grid.addWidget(self.sample_rate_combo, 1, 1)
        grid.addWidget(info, 2, 0, 1, 2)
        return page

    def collect_options(self) -> dict:
        options: dict[str, object] = {}

        start = self.trim_start_input.text().strip()
        if start:
            options["trim_start"] = start
        end = self.trim_end_input.text().strip()
        if end:
            options["trim_end"] = end

        fade_in = round(self.fade_in_input.value(), 3)
        if fade_in > 0:
            options["fade_in_duration"] = fade_in
        fade_out_dur = round(self.fade_out_duration_input.value(), 3)
        if fade_out_dur > 0:
            options["fade_out_duration"] = fade_out_dur
            options["fade_out_start"] = round(self.fade_out_start_input.value(), 3)

        volume = self.volume_slider.value()
        if volume != 0:
            options["volume_db"] = volume

        if self.loudnorm_check.isChecked():
            options["loudnorm"] = True

        channels = self.channels_combo.currentData()
        if channels:
            options["audio_channels"] = channels

        sample_rate = self.sample_rate_combo.currentData()
        if sample_rate:
            options["sample_rate"] = sample_rate

        return options


def _seconds_spinbox(parent: QWidget, *, maximum: float) -> QDoubleSpinBox:
    box = QDoubleSpinBox(parent)
    box.setRange(0.0, maximum)
    box.setSingleStep(0.5)
    box.setDecimals(2)
    box.setValue(0.0)
    box.setSuffix(" s")
    box.setSpecialValueText("off")
    box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    box.setAccelerated(True)
    return box


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


def _grid_setup(grid: QGridLayout) -> None:
    grid.setContentsMargins(12, 12, 12, 12)
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(10)
    grid.setColumnMinimumWidth(0, 110)
    grid.setColumnMinimumWidth(2, 130)
    grid.setColumnStretch(1, 1)
    grid.setColumnStretch(3, 1)
