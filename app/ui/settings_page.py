from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.core.settings import CONFIG_DIR, Settings, get_settings, set_settings

try:
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QMessageBox,
        QPushButton,
        QSlider,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError:  # pragma: no cover
    Qt = None
    QAbstractSpinBox = QComboBox = QFileDialog = QFrame = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QMessageBox = QPushButton = QSlider = QSpinBox = QVBoxLayout = QWidget = None


OCR_LANGUAGE_PRESETS = (
    ("English (eng)", "eng"),
    ("Indonesian (ind)", "ind"),
    ("English + Indonesian (eng+ind)", "eng+ind"),
    ("Custom — see field below", "custom"),
)

VIDEO_PRESETS = (
    "ultrafast", "superfast", "veryfast", "faster", "fast",
    "medium", "slow", "slower", "veryslow",
)


class SettingsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        title = QLabel("Settings", self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        panel = QFrame(self)
        panel.setObjectName("ToolPanel")
        grid = QGridLayout(panel)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 190)
        grid.setColumnStretch(1, 1)

        # ---- Output / concurrency ----
        self.output_dir_input = QLineEdit(panel)
        self.output_dir_input.setPlaceholderText("Empty = same folder as input file")
        browse_button = QPushButton("Browse", panel)
        browse_button.clicked.connect(self._browse_output_dir)
        output_row = QHBoxLayout()
        output_row.setSpacing(8)
        output_row.addWidget(self.output_dir_input, 1)
        output_row.addWidget(browse_button)

        self.concurrency_input = QSpinBox(panel)
        self.concurrency_input.setRange(1, 16)
        self.concurrency_input.setSuffix(" workers")
        _use_stepper(self.concurrency_input)

        # ---- Image / PDF ----
        self.image_quality_slider = QSlider(Qt.Orientation.Horizontal, panel)
        self.image_quality_slider.setRange(1, 100)
        self.image_quality_label = QLabel("82", panel)
        self.image_quality_slider.valueChanged.connect(
            lambda value: self.image_quality_label.setText(str(value))
        )
        quality_row = QHBoxLayout()
        quality_row.setSpacing(8)
        quality_row.addWidget(self.image_quality_slider, 1)
        quality_row.addWidget(self.image_quality_label)

        self.pdf_dpi_input = QSpinBox(panel)
        self.pdf_dpi_input.setRange(72, 600)
        self.pdf_dpi_input.setSuffix(" dpi")
        _use_stepper(self.pdf_dpi_input)

        # ---- OCR ----
        self.ocr_language_combo = QComboBox(panel)
        self.ocr_language_combo.setView(QListView(self.ocr_language_combo))
        for label, value in OCR_LANGUAGE_PRESETS:
            self.ocr_language_combo.addItem(label, value)
        self.ocr_language_combo.currentIndexChanged.connect(self._ocr_lang_changed)
        self.ocr_language_custom = QLineEdit(panel)
        self.ocr_language_custom.setPlaceholderText("e.g. eng+jpn (only when 'Custom' is selected)")
        self.ocr_language_custom.setEnabled(False)

        # ---- Video defaults ----
        self.video_crf_slider = QSlider(Qt.Orientation.Horizontal, panel)
        self.video_crf_slider.setRange(0, 51)
        self.video_crf_label = QLabel("0", panel)
        self.video_crf_slider.valueChanged.connect(
            lambda value: self.video_crf_label.setText(
                str(value) if value > 0 else "off"
            )
        )
        crf_row = QHBoxLayout()
        crf_row.setSpacing(8)
        crf_row.addWidget(self.video_crf_slider, 1)
        crf_row.addWidget(self.video_crf_label)

        self.video_preset_combo = QComboBox(panel)
        self.video_preset_combo.setView(QListView(self.video_preset_combo))
        for preset in VIDEO_PRESETS:
            self.video_preset_combo.addItem(preset, preset)

        # ---- Audio defaults ----
        self.audio_bitrate_input = QLineEdit(panel)
        self.audio_bitrate_input.setPlaceholderText("e.g. 192k, 320k")

        row = 0
        grid.addWidget(_field("Default output folder", panel), row, 0)
        grid.addLayout(output_row, row, 1)
        row += 1
        grid.addWidget(_field("Max concurrent tasks", panel), row, 0)
        grid.addWidget(self.concurrency_input, row, 1)
        row += 1
        grid.addWidget(_section("Conversion defaults", panel), row, 0, 1, 2)
        row += 1
        grid.addWidget(_field("Image quality", panel), row, 0)
        grid.addLayout(quality_row, row, 1)
        row += 1
        grid.addWidget(_field("PDF render DPI", panel), row, 0)
        grid.addWidget(self.pdf_dpi_input, row, 1)
        row += 1
        grid.addWidget(_field("OCR language", panel), row, 0)
        grid.addWidget(self.ocr_language_combo, row, 1)
        row += 1
        grid.addWidget(_field("OCR custom language code", panel), row, 0)
        grid.addWidget(self.ocr_language_custom, row, 1)
        row += 1
        grid.addWidget(_field("Video CRF (0 = off)", panel), row, 0)
        grid.addLayout(crf_row, row, 1)
        row += 1
        grid.addWidget(_field("Video x264 preset", panel), row, 0)
        grid.addWidget(self.video_preset_combo, row, 1)
        row += 1
        grid.addWidget(_field("Audio bitrate", panel), row, 0)
        grid.addWidget(self.audio_bitrate_input, row, 1)
        row += 1

        info = QLabel(
            "Concurrency change applies on next launch. Defaults seed each "
            "conversion page when an input is selected — the per-page panel "
            "still wins if the user changes it.",
            panel,
        )
        info.setWordWrap(True)
        info.setObjectName("HintLabel")
        grid.addWidget(info, row, 0, 1, 2)
        row += 1

        # ---- Action row ----
        action_row = QHBoxLayout()
        reveal_button = QPushButton("Open config folder", panel)
        reveal_button.clicked.connect(self._open_config_dir)
        action_row.addWidget(reveal_button)
        action_row.addStretch(1)
        save_button = QPushButton("Save", panel)
        save_button.clicked.connect(self._save)
        reset_button = QPushButton("Reset", panel)
        reset_button.clicked.connect(self._reset_form)
        action_row.addWidget(reset_button)
        action_row.addWidget(save_button)
        grid.addLayout(action_row, row, 0, 1, 2)

        root.addWidget(panel)
        root.addStretch(1)

        self._reset_form()

    def set_tasks(self, _tasks: list) -> None:
        # Settings page is not task-driven; satisfy the page protocol.
        return

    def _browse_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select default output folder",
            self.output_dir_input.text() or "",
        )
        if directory:
            self.output_dir_input.setText(directory)

    def _open_config_dir(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        opener = self._file_opener()
        if opener is None:
            QMessageBox.information(
                self,
                "Config folder",
                f"Config folder:\n{CONFIG_DIR}",
            )
            return
        try:
            subprocess.Popen([opener, str(CONFIG_DIR)])
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Open failed",
                f"Could not launch file manager: {exc}\n\n{CONFIG_DIR}",
            )

    @staticmethod
    def _file_opener() -> str | None:
        if sys.platform == "darwin":
            return "open"
        if sys.platform.startswith("win"):
            return "explorer"
        # Linux / *BSD: xdg-open is the standard front-end.
        from shutil import which
        if which("xdg-open"):
            return "xdg-open"
        return None

    def _ocr_lang_changed(self, _index: int) -> None:
        is_custom = self.ocr_language_combo.currentData() == "custom"
        self.ocr_language_custom.setEnabled(is_custom)
        if not is_custom:
            self.ocr_language_custom.clear()

    def _reset_form(self) -> None:
        current = get_settings()
        self.output_dir_input.setText(current.output_dir)
        self.concurrency_input.setValue(current.max_concurrency)
        self.image_quality_slider.setValue(current.default_image_quality)
        self.pdf_dpi_input.setValue(current.default_pdf_dpi)

        # OCR language: pick a preset entry if it matches, otherwise "Custom".
        match_index = -1
        for index in range(self.ocr_language_combo.count()):
            value = self.ocr_language_combo.itemData(index)
            if value == current.default_ocr_language:
                match_index = index
                break
        if match_index >= 0:
            self.ocr_language_combo.setCurrentIndex(match_index)
            self.ocr_language_custom.clear()
        else:
            for index in range(self.ocr_language_combo.count()):
                if self.ocr_language_combo.itemData(index) == "custom":
                    self.ocr_language_combo.setCurrentIndex(index)
                    break
            self.ocr_language_custom.setText(current.default_ocr_language)

        self.video_crf_slider.setValue(current.default_video_crf)
        self.video_crf_label.setText(
            str(current.default_video_crf) if current.default_video_crf > 0 else "off"
        )
        preset_index = self.video_preset_combo.findData(current.default_video_preset)
        if preset_index >= 0:
            self.video_preset_combo.setCurrentIndex(preset_index)
        self.audio_bitrate_input.setText(current.default_audio_bitrate)

    def _save(self) -> None:
        ocr_choice = self.ocr_language_combo.currentData()
        if ocr_choice == "custom":
            ocr_value = self.ocr_language_custom.text().strip()
            if not ocr_value:
                QMessageBox.warning(
                    self,
                    "OCR language",
                    "Custom OCR language code is empty. Pick a preset or fill in a value like 'eng+jpn'.",
                )
                return
        else:
            ocr_value = ocr_choice or "eng"

        new_settings = Settings(
            output_dir=self.output_dir_input.text().strip(),
            max_concurrency=self.concurrency_input.value(),
            default_image_quality=self.image_quality_slider.value(),
            default_pdf_dpi=self.pdf_dpi_input.value(),
            default_ocr_language=ocr_value,
            default_video_crf=self.video_crf_slider.value(),
            default_video_preset=self.video_preset_combo.currentData() or "medium",
            default_audio_bitrate=self.audio_bitrate_input.text().strip() or "192k",
        )
        try:
            set_settings(new_settings)
        except OSError as exc:
            QMessageBox.warning(self, "Settings", f"Could not save settings: {exc}")
            return
        QMessageBox.information(
            self,
            "Settings",
            "Settings saved. Concurrency change takes effect on next launch.",
        )


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


def _section(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("SectionTitle")
    return label


def _use_stepper(spinbox: QAbstractSpinBox) -> None:
    spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spinbox.setAccelerated(True)
