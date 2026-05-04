from __future__ import annotations

from app.core.settings import Settings, get_settings, set_settings

try:
    from PySide6.QtWidgets import (
        QAbstractSpinBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
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
    QAbstractSpinBox = QFileDialog = QFrame = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QMessageBox = QPushButton = QSlider = QSpinBox = QVBoxLayout = QWidget = None


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
        grid.setColumnMinimumWidth(0, 170)
        grid.setColumnStretch(1, 1)

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
        self.concurrency_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.concurrency_input.setAccelerated(True)

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
        self.pdf_dpi_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.pdf_dpi_input.setAccelerated(True)

        grid.addWidget(_field("Default output folder", panel), 0, 0)
        grid.addLayout(output_row, 0, 1)
        grid.addWidget(_field("Max concurrent tasks", panel), 1, 0)
        grid.addWidget(self.concurrency_input, 1, 1)
        grid.addWidget(_field("Default image quality", panel), 2, 0)
        grid.addLayout(quality_row, 2, 1)
        grid.addWidget(_field("Default PDF render DPI", panel), 3, 0)
        grid.addWidget(self.pdf_dpi_input, 3, 1)

        info = QLabel(
            "Concurrency change applies on next launch. "
            "Image quality and PDF DPI seed each conversion page on next selection.",
            panel,
        )
        info.setWordWrap(True)
        grid.addWidget(info, 4, 0, 1, 2)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        save_button = QPushButton("Save", panel)
        save_button.clicked.connect(self._save)
        reset_button = QPushButton("Reset", panel)
        reset_button.clicked.connect(self._reset_form)
        action_row.addWidget(reset_button)
        action_row.addWidget(save_button)
        grid.addLayout(action_row, 5, 0, 1, 2)

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

    def _reset_form(self) -> None:
        current = get_settings()
        self.output_dir_input.setText(current.output_dir)
        self.concurrency_input.setValue(current.max_concurrency)
        self.image_quality_slider.setValue(current.default_image_quality)
        self.pdf_dpi_input.setValue(current.default_pdf_dpi)

    def _save(self) -> None:
        new_settings = Settings(
            output_dir=self.output_dir_input.text().strip(),
            max_concurrency=self.concurrency_input.value(),
            default_image_quality=self.image_quality_slider.value(),
            default_pdf_dpi=self.pdf_dpi_input.value(),
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
