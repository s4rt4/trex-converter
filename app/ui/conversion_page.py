from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.core.registry import ConversionRegistry
from app.core.task import Task
from app.engines.imagemagick_engine import IMAGE_FORMATS
from app.ui.icons import ICON_SIZE, accent_icon, surface_icon
from app.ui.queue_panel import QueuePanel

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSlider,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QCheckBox = QComboBox = QFileDialog = QFormLayout = QFrame = QHBoxLayout = QLabel = QLineEdit = QMessageBox = QPushButton = QSlider = QToolButton = QVBoxLayout = QWidget = None


@dataclass(frozen=True, slots=True)
class ConversionPageConfig:
    title: str
    input_formats: tuple[str, ...]
    default_output: str
    engine_name: str
    kind: str
    show_quality: bool = False
    show_resize: bool = False
    show_bitrate: bool = False


class ConversionPage(QWidget):
    def __init__(
        self,
        config: ConversionPageConfig,
        registry: ConversionRegistry,
        on_enqueue: Callable[[Task], None],
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.registry = registry
        self._on_enqueue = on_enqueue
        self._input_path: Path | None = None
        self.quality_input: QSlider | None = None
        self.quality_value_label: QLabel | None = None
        self.resize_input: QLineEdit | None = None
        self.bitrate_input: QLineEdit | None = None
        self.strip_input: QCheckBox | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel(config.title, self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        form_shell = QFrame(self)
        form_shell.setObjectName("ToolPanel")
        form = QFormLayout(form_shell)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        input_row = QHBoxLayout()
        self.input_display = QLineEdit(self)
        self.input_display.setReadOnly(True)
        browse_button = QPushButton("Browse", self)
        browse_button.setIcon(surface_icon("fa5s.folder-open"))
        browse_button.setIconSize(ICON_SIZE)
        browse_button.clicked.connect(self._choose_input)
        input_row.addWidget(self.input_display)
        input_row.addWidget(browse_button)
        form.addRow("Input", input_row)

        output_format_row = QHBoxLayout()
        output_format_row.setSpacing(0)
        self.output_combo = QComboBox(form_shell)
        self.output_combo.setObjectName("OutputFormatCombo")
        self.output_combo.currentTextChanged.connect(self._update_output_path)
        output_format_button = QToolButton(form_shell)
        output_format_button.setObjectName("OutputFormatButton")
        output_format_button.setIcon(accent_icon("fa5s.chevron-down"))
        output_format_button.setIconSize(ICON_SIZE)
        output_format_button.setToolTip("Show output formats")
        output_format_button.clicked.connect(self.output_combo.showPopup)
        output_format_row.addWidget(self.output_combo, 1)
        output_format_row.addWidget(output_format_button)
        form.addRow("Output format", output_format_row)

        output_row = QHBoxLayout()
        self.output_display = QLineEdit(self)
        output_button = QPushButton("Select Location", self)
        output_button.setIcon(surface_icon("fa5s.save"))
        output_button.setIconSize(ICON_SIZE)
        output_button.clicked.connect(self._choose_output)
        output_row.addWidget(self.output_display)
        output_row.addWidget(output_button)
        form.addRow("Output", output_row)

        if config.show_quality:
            quality_row = QHBoxLayout()
            self.quality_input = QSlider(Qt.Orientation.Horizontal, form_shell)
            self.quality_input.setObjectName("QualitySlider")
            self.quality_input.setRange(1, 100)
            self.quality_input.setValue(85)
            self.quality_value_label = QLabel("85", form_shell)
            self.quality_value_label.setObjectName("QualityValue")
            self.quality_input.valueChanged.connect(
                lambda value: self.quality_value_label.setText(str(value))
            )
            quality_row.addWidget(self.quality_input, 1)
            quality_row.addWidget(self.quality_value_label)
            form.addRow("Quality", quality_row)

        if config.show_resize:
            self.resize_input = QLineEdit(form_shell)
            self.resize_input.setPlaceholderText("1280x1280>")
            form.addRow("Resize", self.resize_input)

        if config.show_bitrate:
            self.bitrate_input = QLineEdit(form_shell)
            self.bitrate_input.setPlaceholderText("192k")
            form.addRow("Audio bitrate", self.bitrate_input)

        if config.show_quality or config.show_resize:
            self.strip_input = QCheckBox("Remove metadata", form_shell)
            self.strip_input.setChecked(True)
            form.addRow("", self.strip_input)

        enqueue_button = QPushButton("Add to Queue", self)
        enqueue_button.setIcon(surface_icon("fa5s.plus-circle"))
        enqueue_button.setIconSize(ICON_SIZE)
        enqueue_button.clicked.connect(self._enqueue)
        form.addRow("", enqueue_button)

        root.addWidget(form_shell)

        self.queue_panel = QueuePanel(self)
        self.queue_panel.set_handlers(on_cancel, on_retry)
        root.addWidget(self.queue_panel, 1)

    def set_tasks(self, tasks: list[Task]) -> None:
        self.queue_panel.set_tasks([task for task in tasks if self._matches(task)])

    def _choose_input(self) -> None:
        filters = " ".join(f"*.{fmt}" for fmt in self.config.input_formats)
        input_name = _get_open_file_name(
            self,
            "Select input file",
            f"{self.config.title} ({filters})",
        )
        if not input_name:
            return
        input_path = Path(input_name)
        if input_path.suffix.lower().lstrip(".") not in self.config.input_formats:
            QMessageBox.warning(self, "Unsupported Format", f"{input_path.suffix} is not supported in {self.config.title}")
            return
        self._input_path = input_path
        self.input_display.setText(str(input_path))
        self._populate_outputs(input_path)
        self._update_output_path()

    def _choose_output(self) -> None:
        if not self._input_path:
            QMessageBox.warning(self, "Input Required", "Choose an input file first.")
            return
        output_name = _get_save_file_name(
            self,
            "Select output file",
            self.output_display.text(),
        )
        if output_name:
            self.output_display.setText(output_name)

    def _populate_outputs(self, input_path: Path) -> None:
        outputs = [
            output
            for output in self.registry.list_supported_outputs(input_path.suffix)
            if self._output_belongs_to_page(output)
        ]
        if self.config.default_output in outputs:
            outputs.remove(self.config.default_output)
            outputs.insert(0, self.config.default_output)
        self.output_combo.clear()
        self.output_combo.addItems(outputs)

    def _update_output_path(self) -> None:
        if not self._input_path or not self.output_combo.currentText():
            return
        self.output_display.setText(str(self._input_path.with_suffix(f".{self.output_combo.currentText()}")))

    def _enqueue(self) -> None:
        if not self._input_path:
            QMessageBox.warning(self, "Input Required", "Choose an input file first.")
            return
        format_out = self.output_combo.currentText()
        if not format_out:
            QMessageBox.warning(self, "Output Required", "No output format is available for this input.")
            return
        output_path = Path(self.output_display.text())
        engine = self.registry.resolve(self._input_path.suffix, format_out)
        self._on_enqueue(
            Task(
                input_path=self._input_path,
                output_path=output_path,
                format_in=self._input_path.suffix,
                format_out=format_out,
                engine=engine.name,
                options=self._options(),
            )
        )

    def _options(self) -> dict:
        options: dict[str, object] = {}
        if self.config.show_quality and self.quality_input is not None:
            options["quality"] = self.quality_input.value()
        if self.config.show_resize and self.resize_input is not None and self.resize_input.text().strip():
            options["resize"] = self.resize_input.text().strip()
        if (self.config.show_quality or self.config.show_resize) and self.strip_input is not None:
            options["strip"] = self.strip_input.isChecked()
        if self.config.show_bitrate and self.bitrate_input is not None and self.bitrate_input.text().strip():
            options["bitrate"] = self.bitrate_input.text().strip()
        return options

    def _matches(self, task: Task) -> bool:
        return task.format_in in self.config.input_formats or task.engine == self.config.engine_name

    def _output_belongs_to_page(self, output: str) -> bool:
        if self.config.kind == "image":
            return output in set(IMAGE_FORMATS)
        if self.config.kind == "video":
            return output in {"mp3", "mp4", "webm"}
        if self.config.kind == "document":
            return output in {"pdf"}
        if self.config.kind == "pdf":
            return output in {*IMAGE_FORMATS, "txt"}
        return True


def _get_open_file_name(parent: QWidget, title: str, file_filter: str) -> str:
    dialog = QFileDialog(parent, title)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setNameFilter(file_filter)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return ""
    selected = dialog.selectedFiles()
    return selected[0] if selected else ""


def _get_save_file_name(parent: QWidget, title: str, initial_path: str) -> str:
    dialog = QFileDialog(parent, title)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setDirectory(str(Path(initial_path).parent))
    dialog.selectFile(Path(initial_path).name)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return ""
    selected = dialog.selectedFiles()
    return selected[0] if selected else ""
