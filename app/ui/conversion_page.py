from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QSlider,
        QTabWidget,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QCheckBox = QComboBox = QFileDialog = QFrame = QGridLayout = QHBoxLayout = QLabel = QLineEdit = QListView = QListWidget = QListWidgetItem = QMessageBox = QPushButton = QSlider = QTabWidget = QToolButton = QVBoxLayout = QWidget = None


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
    extra_options_factory: Callable[[QWidget], QWidget] | None = None
    force_engine: bool = False
    directory_output: bool = False
    directory_input: bool = False
    multi_input: bool = False
    default_options: tuple[tuple[str, object], ...] = ()


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
        self._input_paths: list[Path] = []
        self.input_display: QLineEdit | None = None
        self.input_list: QListWidget | None = None
        self.quality_input: QSlider | None = None
        self.quality_value_label: QLabel | None = None
        self.resize_input: QLineEdit | None = None
        self.bitrate_input: QLineEdit | None = None
        self.strip_input: QCheckBox | None = None
        self.extra_options_widget: QWidget | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel(config.title, self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        self.page_tabs = QTabWidget(self)
        self.page_tabs.setObjectName("PageTabs")
        self.page_tabs.setDocumentMode(True)
        root.addWidget(self.page_tabs, 1)

        convert_tab = QWidget(self.page_tabs)
        convert_layout = QVBoxLayout(convert_tab)
        convert_layout.setContentsMargins(0, 18, 0, 0)
        convert_layout.setSpacing(12)

        form_shell = QFrame(convert_tab)
        form_shell.setObjectName("ToolPanel")
        form = QGridLayout(form_shell)
        form.setContentsMargins(12, 10, 12, 10)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        form.setColumnMinimumWidth(0, 80)
        form.setColumnStretch(1, 1)

        row = 0
        if config.multi_input:
            self.input_list = QListWidget(form_shell)
            self.input_list.setObjectName("InputList")
            self.input_list.setMinimumHeight(96)
            input_buttons = QHBoxLayout()
            input_buttons.setSpacing(8)
            add_button = QPushButton("Add files", form_shell)
            add_button.setIcon(surface_icon("fa5s.folder-open"))
            add_button.setIconSize(ICON_SIZE)
            add_button.clicked.connect(self._choose_input)
            remove_button = QPushButton("Remove", form_shell)
            remove_button.setIcon(surface_icon("fa5s.minus-circle"))
            remove_button.setIconSize(ICON_SIZE)
            remove_button.clicked.connect(self._remove_selected_inputs)
            clear_button = QPushButton("Clear", form_shell)
            clear_button.setIcon(surface_icon("fa5s.times-circle"))
            clear_button.setIconSize(ICON_SIZE)
            clear_button.clicked.connect(self._clear_inputs)
            input_buttons.addStretch(1)
            input_buttons.addWidget(add_button)
            input_buttons.addWidget(remove_button)
            input_buttons.addWidget(clear_button)
            form.addWidget(_field_label("Inputs", form_shell), row, 0)
            form.addWidget(self.input_list, row, 1)
            row += 1
            form.addLayout(input_buttons, row, 1)
            row += 1
        else:
            input_row = QHBoxLayout()
            input_row.setSpacing(10)
            self.input_display = QLineEdit(form_shell)
            self.input_display.setReadOnly(True)
            browse_button = QPushButton("Browse", form_shell)
            browse_button.setIcon(surface_icon("fa5s.folder-open"))
            browse_button.setIconSize(ICON_SIZE)
            browse_button.clicked.connect(self._choose_input)
            input_row.addWidget(self.input_display, 1)
            input_row.addWidget(browse_button)
            form.addWidget(_field_label("Input", form_shell), row, 0)
            form.addLayout(input_row, row, 1)
            row += 1

        output_format_row = QHBoxLayout()
        output_format_row.setSpacing(8)
        format_combo_row = QHBoxLayout()
        format_combo_row.setSpacing(0)
        self.output_combo = QComboBox(form_shell)
        self.output_combo.setObjectName("OutputFormatCombo")
        self.output_combo.setView(QListView(self.output_combo))
        self.output_combo.setMaxVisibleItems(12)
        self.output_combo.currentTextChanged.connect(self._update_output_path)
        output_format_button = QToolButton(form_shell)
        output_format_button.setObjectName("OutputFormatButton")
        output_format_button.setIcon(accent_icon("fa5s.chevron-down"))
        output_format_button.setIconSize(ICON_SIZE)
        output_format_button.setToolTip("Show output formats")
        output_format_button.clicked.connect(self.output_combo.showPopup)
        format_combo_row.addWidget(self.output_combo, 1)
        format_combo_row.addWidget(output_format_button)
        select_location_button = QPushButton("Select Location", form_shell)
        select_location_button.setIcon(surface_icon("fa5s.save"))
        select_location_button.setIconSize(ICON_SIZE)
        select_location_button.clicked.connect(self._choose_output)
        output_format_row.addLayout(format_combo_row, 1)
        output_format_row.addWidget(select_location_button)
        form.addWidget(_field_label("Output format", form_shell), row, 0)
        form.addLayout(output_format_row, row, 1)
        row += 1

        if config.show_bitrate:
            bitrate_row = QHBoxLayout()
            bitrate_row.setSpacing(12)
            self.bitrate_input = QLineEdit(form_shell)
            self.bitrate_input.setPlaceholderText("192k")
            bitrate_row.addWidget(self.bitrate_input)
            form.addWidget(_field_label("Audio bitrate", form_shell), row, 0)
            form.addLayout(bitrate_row, row, 1)
            row += 1

        output_row = QHBoxLayout()
        output_row.setSpacing(8)
        self.output_display = QLineEdit(form_shell)
        output_row.addWidget(self.output_display, 1)

        if config.show_quality:
            self.quality_input = QSlider(Qt.Orientation.Horizontal, form_shell)
            self.quality_input.setObjectName("QualitySlider")
            self.quality_input.setRange(1, 100)
            self.quality_input.setValue(85)
            self.quality_value_label = QLabel("85", form_shell)
            self.quality_value_label.setObjectName("QualityValue")
            self.quality_input.valueChanged.connect(
                lambda value: self.quality_value_label.setText(str(value))
            )
            output_row.addWidget(_field_label("Quality", form_shell))
            output_row.addWidget(self.quality_input, 1)
            output_row.addWidget(self.quality_value_label)

        form.addWidget(_field_label("Output", form_shell), row, 0)
        form.addLayout(output_row, row, 1)
        row += 1

        if config.show_resize:
            self.resize_input = QLineEdit(form_shell)
            self.resize_input.setPlaceholderText("1280x1280>")
            form.addWidget(_field_label("Resize", form_shell), row, 0)
            form.addWidget(self.resize_input, row, 1)
            row += 1

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addStretch(1)
        if config.show_quality or config.show_resize:
            self.strip_input = QCheckBox("Remove metadata", form_shell)
            self.strip_input.setChecked(True)
            action_row.addWidget(self.strip_input)
        enqueue_button = QPushButton("Add to Queue", form_shell)
        enqueue_button.setIcon(surface_icon("fa5s.plus-circle"))
        enqueue_button.setIconSize(ICON_SIZE)
        enqueue_button.clicked.connect(self._enqueue)
        action_row.addWidget(enqueue_button)
        form.addLayout(action_row, row, 0, 1, 2)

        convert_layout.addWidget(form_shell)

        if config.extra_options_factory is not None:
            extras = config.extra_options_factory(convert_tab)
            self.extra_options_widget = extras
            convert_layout.addWidget(extras)

        convert_layout.addStretch(1)
        self.page_tabs.addTab(convert_tab, "Convert")

        queue_tab = QWidget(self.page_tabs)
        queue_layout = QVBoxLayout(queue_tab)
        queue_layout.setContentsMargins(0, 18, 0, 0)
        queue_layout.setSpacing(0)
        self.queue_panel = QueuePanel(queue_tab)
        self.queue_panel.set_handlers(on_cancel, on_retry)
        queue_layout.addWidget(self.queue_panel, 1)
        self.page_tabs.addTab(queue_tab, "Queue")

    def set_tasks(self, tasks: list[Task]) -> None:
        self.queue_panel.set_tasks([task for task in tasks if self._matches(task)])

    def _choose_input(self) -> None:
        if self.config.directory_input:
            picked = QFileDialog.getExistingDirectory(
                self, f"Select input folder for {self.config.title}"
            )
            if not picked:
                return
            folder = Path(picked)
            self._input_paths = [folder]
            self.input_display.setText(str(folder))
            self._populate_outputs(folder)
            self._update_output_path()
            return

        filters = " ".join(f"*.{fmt}" for fmt in self.config.input_formats)
        if self.config.multi_input:
            picked = _get_open_file_names(
                self,
                "Select input files",
                f"{self.config.title} ({filters})",
            )
            if not picked:
                return
            for raw in picked:
                path = Path(raw)
                if path.suffix.lower().lstrip(".") not in self.config.input_formats:
                    QMessageBox.warning(
                        self,
                        "Unsupported Format",
                        f"{path.suffix} is not supported in {self.config.title}",
                    )
                    continue
                if path in self._input_paths:
                    continue
                self._input_paths.append(path)
                self.input_list.addItem(QListWidgetItem(str(path)))
            if not self._input_paths:
                return
            primary = self._input_paths[0]
            self._populate_outputs(primary)
            self._update_output_path()
            return

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
        self._input_paths = [input_path]
        self.input_display.setText(str(input_path))
        self._populate_outputs(input_path)
        self._update_output_path()

    def _remove_selected_inputs(self) -> None:
        if self.input_list is None:
            return
        for item in list(self.input_list.selectedItems()):
            row = self.input_list.row(item)
            self.input_list.takeItem(row)
            if 0 <= row < len(self._input_paths):
                self._input_paths.pop(row)
        self._update_output_path()

    def _clear_inputs(self) -> None:
        if self.input_list is None:
            return
        self.input_list.clear()
        self._input_paths = []

    def _primary_input(self) -> Path | None:
        return self._input_paths[0] if self._input_paths else None

    def _choose_output(self) -> None:
        primary = self._primary_input()
        if not primary:
            QMessageBox.warning(self, "Input Required", "Choose an input file first.")
            return
        if self.config.directory_output:
            current = self.output_display.text() or str(primary.parent)
            picked = QFileDialog.getExistingDirectory(
                self, "Select output folder", current
            )
            if picked:
                self.output_display.setText(picked)
            return
        output_name = _get_save_file_name(
            self,
            "Select output file",
            self.output_display.text(),
        )
        if output_name:
            self.output_display.setText(output_name)

    def _populate_outputs(self, input_path: Path) -> None:
        format_in = self._format_in_for(input_path)
        outputs = [
            output
            for output in self.registry.list_supported_outputs(format_in)
            if self._output_belongs_to_page(output)
        ]
        if self.config.force_engine:
            try:
                forced = self.registry.engine_by_name(self.config.engine_name)
            except KeyError:
                forced = None
            if forced is not None:
                outputs = [
                    output for output in outputs if forced.supports(format_in, output)
                ]
        if self.config.default_output in outputs:
            outputs.remove(self.config.default_output)
            outputs.insert(0, self.config.default_output)
        self.output_combo.clear()
        self.output_combo.addItems(outputs)

    def _update_output_path(self) -> None:
        primary = self._primary_input()
        if not primary or not self.output_combo.currentText():
            return
        from app.core.settings import get_settings

        suffix = self.output_combo.currentText()
        output_dir = get_settings().output_dir.strip()
        if self.config.directory_output:
            base = Path(output_dir) if output_dir else primary.parent
            target = base / primary.stem
        elif self.config.directory_input:
            base = Path(output_dir) if output_dir else primary.parent
            target = base / f"{primary.name}.{suffix}"
        elif output_dir:
            target = Path(output_dir) / f"{primary.stem}.{suffix}"
        else:
            target = primary.with_suffix(f".{suffix}")
        self.output_display.setText(str(target))

    def _enqueue(self) -> None:
        primary = self._primary_input()
        if not primary:
            QMessageBox.warning(self, "Input Required", "Choose an input file first.")
            return
        format_out = self.output_combo.currentText()
        if not format_out:
            QMessageBox.warning(self, "Output Required", "No output format is available for this input.")
            return
        output_path = Path(self.output_display.text())
        format_in = self._format_in_for(primary)
        if self.config.force_engine:
            engine_name = self.config.engine_name
        else:
            engine_name = self.registry.resolve(format_in, format_out).name
        extra_inputs = list(self._input_paths[1:])
        self._on_enqueue(
            Task(
                input_path=primary,
                output_path=output_path,
                format_in=format_in,
                format_out=format_out,
                engine=engine_name,
                options=self._options(),
                extra_inputs=extra_inputs,
            )
        )

    def _format_in_for(self, input_path: Path) -> str:
        if self.config.directory_input and self.config.input_formats:
            return self.config.input_formats[0]
        return input_path.suffix

    def _options(self) -> dict:
        options: dict[str, object] = dict(self.config.default_options)
        if self.config.show_quality and self.quality_input is not None:
            options["quality"] = self.quality_input.value()
        if self.config.show_resize and self.resize_input is not None and self.resize_input.text().strip():
            options["resize"] = self.resize_input.text().strip()
        if (self.config.show_quality or self.config.show_resize) and self.strip_input is not None:
            options["strip"] = self.strip_input.isChecked()
        if self.config.show_bitrate and self.bitrate_input is not None and self.bitrate_input.text().strip():
            options["bitrate"] = self.bitrate_input.text().strip()
        if self.extra_options_widget is not None:
            collector = getattr(self.extra_options_widget, "collect_options", None)
            if callable(collector):
                options.update(collector())
        options["category"] = self.config.kind
        return options

    def _matches(self, task: Task) -> bool:
        category = task.options.get("category")
        if category:
            return category == self.config.kind
        return task.engine == self.config.engine_name

    def _output_belongs_to_page(self, output: str) -> bool:
        if self.config.kind == "image":
            return output in set(IMAGE_FORMATS)
        if self.config.kind == "video":
            return output in {
                "mp4", "mov", "mkv", "webm",
                "gif", "webp", "png", "jpg", "jpeg",
            }
        if self.config.kind == "audio":
            return output in {"mp3", "wav", "aac", "flac", "m4a", "opus", "ogg"}
        if self.config.kind == "document":
            return output in {
                "docx", "odt", "rtf", "html", "epub", "txt", "pdf",
                "xlsx", "ods", "csv",
                "pptx", "odp",
            }
        if self.config.kind == "pdf":
            return output in {*IMAGE_FORMATS, "txt", "pdf", "html"}
        if self.config.kind == "pdf-merge":
            return output == "pdf"
        if self.config.kind == "pdf-split":
            return output == "folder"
        if self.config.kind == "pdf-numbering":
            return output == "pdf"
        if self.config.kind == "pdf-extract-images":
            return output == "folder"
        if self.config.kind == "pdf-extract-attachments":
            return output == "folder"
        if self.config.kind == "slides-to-images":
            return output == "folder"
        if self.config.kind == "document-merge":
            return output == "pdf"
        if self.config.kind == "video-concat":
            return output in {"mp4", "mov", "mkv", "webm"}
        if self.config.kind == "audio-mix":
            return output in {"mp3", "wav", "aac", "flac", "m4a", "opus", "ogg"}
        if self.config.kind == "image-montage":
            return output in set(IMAGE_FORMATS)
        if self.config.kind == "subtitle-merge":
            return output in {"srt", "vtt", "ass"}
        if self.config.kind == "ocr":
            return output in {"txt", "pdf", "hocr", "tsv"}
        if self.config.kind == "subtitle":
            return output in {"srt", "vtt", "ass"}
        if self.config.kind == "archive":
            return output == "folder"
        if self.config.kind == "archive-compress":
            return output in {"zip", "tar", "tgz", "tbz", "txz"}
        if self.config.kind == "qr":
            return output in {"png", "svg", "txt"}
        if self.config.kind == "svg":
            return output in {"png", "pdf", "svg", "eps", "ps", "emf", "wmf", "dxf"}
        if self.config.kind == "subtitle-extract":
            return output in {"srt", "ass", "vtt"}
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


def _get_open_file_names(parent: QWidget, title: str, file_filter: str) -> list[str]:
    dialog = QFileDialog(parent, title)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setNameFilter(file_filter)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return []
    return list(dialog.selectedFiles())


def _field_label(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


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
