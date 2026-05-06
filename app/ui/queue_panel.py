from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.core.task import Task, TaskStatus
from app.engines.imagemagick_engine import IMAGE_FORMATS
from app.ui.icons import ICON_SIZE, icon, surface_icon

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPlainTextEdit,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = QPixmap = None
    QDialog = QDialogButtonBox = QHBoxLayout = QHeaderView = QLabel = QPlainTextEdit = QProgressBar = QTableWidget = QTableWidgetItem = QToolButton = QVBoxLayout = QWidget = None


class QueuePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._on_cancel: Callable[[str], None] | None = None
        self._on_retry: Callable[[str], None] | None = None
        self._tasks: list[Task] = []
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 8, self)
        self.table.setHorizontalHeaderLabels(
            ["Input", "Output", "Engine", "Status", "Progress", "", "", ""]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, 8):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.cellDoubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)

    def set_handlers(
        self,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
    ) -> None:
        self._on_cancel = on_cancel
        self._on_retry = on_retry

    def set_tasks(self, tasks: list[Task]) -> None:
        self._tasks = list(tasks)
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self.table.setCellWidget(row, 0, FileCell(task.input_path, self.table))
            self.table.setCellWidget(row, 1, FileCell(task.output_path, self.table))

            values = [task.engine, task.status.value]
            for offset, value in enumerate(values):
                column = offset + 2
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)

            progress = QProgressBar(self.table)
            progress.setObjectName("QueueProgress")
            progress.setRange(0, 100)
            progress.setValue(int(task.progress * 100))
            progress.setTextVisible(True)
            self.table.setCellWidget(row, 4, progress)

            cancel_button = QToolButton(self.table)
            cancel_button.setObjectName("QueueActionButton")
            cancel_button.setIcon(surface_icon("fa5s.times-circle"))
            cancel_button.setIconSize(ICON_SIZE)
            cancel_button.setToolTip("Cancel task")
            cancel_button.setEnabled(task.status in {TaskStatus.PENDING, TaskStatus.RUNNING})
            cancel_button.clicked.connect(lambda _, task_id=task.id: self._cancel(task_id))
            self.table.setCellWidget(row, 5, cancel_button)

            retry_button = QToolButton(self.table)
            retry_button.setObjectName("QueueActionButton")
            retry_button.setIcon(surface_icon("fa5s.redo"))
            retry_button.setIconSize(ICON_SIZE)
            retry_button.setToolTip("Retry task")
            retry_button.setEnabled(task.can_retry())
            retry_button.clicked.connect(lambda _, task_id=task.id: self._retry(task_id))
            self.table.setCellWidget(row, 6, retry_button)

            details_button = QToolButton(self.table)
            details_button.setObjectName("QueueActionButton")
            details_button.setIcon(surface_icon("fa5s.info-circle"))
            details_button.setIconSize(ICON_SIZE)
            details_button.setToolTip("Show details (log + previews)")
            details_button.clicked.connect(
                lambda _, idx=row: self._show_details(idx)
            )
            self.table.setCellWidget(row, 7, details_button)

    def _cancel(self, task_id: str) -> None:
        if self._on_cancel:
            self._on_cancel(task_id)

    def _retry(self, task_id: str) -> None:
        if self._on_retry:
            self._on_retry(task_id)

    def _on_row_double_click(self, row: int, _column: int) -> None:
        self._show_details(row)

    def _show_details(self, row: int) -> None:
        if not 0 <= row < len(self._tasks):
            return
        TaskDetailsDialog(self._tasks[row], self).exec()


class FileCell(QWidget):
    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        path = Path(path)
        self.setToolTip(str(path))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        preview = QLabel(self)
        preview.setObjectName("QueueFilePreview")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = _preview_pixmap(path)
        if pixmap is not None:
            preview.setPixmap(
                pixmap.scaled(
                    36,
                    36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            preview.setPixmap(icon(_file_icon_name(path)).pixmap(22, 22))
        layout.addWidget(preview)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        name = QLabel(path.name or str(path), self)
        name.setObjectName("QueueFileName")
        name.setToolTip(str(path))
        name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(name)

        folder = QLabel(str(path.parent), self)
        folder.setObjectName("QueueFilePath")
        folder.setToolTip(str(path))
        folder.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(folder)

        layout.addLayout(text_layout, 1)


def _preview_pixmap(path: Path) -> QPixmap | None:
    if path.suffix.lower().lstrip(".") not in IMAGE_FORMATS or not path.exists():
        return None
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    return pixmap


class TaskDetailsDialog(QDialog):
    def __init__(self, task: Task, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Task details — {Path(task.input_path).name}")
        self.setObjectName("TaskDetailsDialog")
        self.resize(720, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(16)

        in_thumb = _thumb_label(task.input_path, self)
        out_thumb = _thumb_label(task.output_path, self)

        header.addWidget(_thumb_block("Input", task.input_path, in_thumb, self))
        header.addWidget(_thumb_block("Output", task.output_path, out_thumb, self))
        header.addStretch(1)
        root.addLayout(header)

        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(2)
        meta_layout.addWidget(_meta("Engine", task.engine, self))
        meta_layout.addWidget(_meta(
            "Format", f"{task.format_in} → {task.format_out}", self
        ))
        meta_layout.addWidget(_meta("Status", task.status.value, self))
        meta_layout.addWidget(_meta("Progress", f"{int(task.progress * 100)}%", self))
        if task.error:
            meta_layout.addWidget(_meta("Error", task.error, self, is_error=True))
        root.addLayout(meta_layout)

        log_label = QLabel("Log", self)
        log_label.setObjectName("FieldLabel")
        root.addWidget(log_label)

        log_view = QPlainTextEdit(self)
        log_view.setObjectName("TaskLogView")
        log_view.setReadOnly(True)
        log_view.setPlainText("\n".join(task.log) if task.log else "(no log entries)")
        root.addWidget(log_view, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)


def _thumb_label(path: Path, parent: QWidget) -> QLabel:
    label = QLabel(parent)
    label.setObjectName("TaskDetailsThumb")
    label.setFixedSize(120, 120)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pixmap = _preview_pixmap(Path(path))
    if pixmap is not None:
        label.setPixmap(
            pixmap.scaled(
                120,
                120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    else:
        label.setPixmap(icon(_file_icon_name(Path(path))).pixmap(60, 60))
    return label


def _thumb_block(title: str, path: Path, thumb: QLabel, parent: QWidget) -> QWidget:
    block = QWidget(parent)
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title_label = QLabel(title, parent)
    title_label.setObjectName("FieldLabel")
    layout.addWidget(title_label)
    layout.addWidget(thumb)
    name = QLabel(Path(path).name, parent)
    name.setObjectName("TaskDetailsName")
    name.setToolTip(str(path))
    name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    layout.addWidget(name)
    return block


def _meta(key: str, value: str, parent: QWidget, *, is_error: bool = False) -> QLabel:
    label = QLabel(f"{key}: {value}", parent)
    label.setObjectName("TaskDetailsError" if is_error else "TaskDetailsMeta")
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setWordWrap(True)
    return label


def _file_icon_name(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"mp4", "mov", "webm", "mkv"}:
        return "fa5s.film"
    if suffix in {"pdf"}:
        return "fa5s.file-pdf"
    if suffix in {"doc", "docx", "odt", "rtf"}:
        return "fa5s.file-word"
    if suffix in {"xls", "xlsx", "ods"}:
        return "fa5s.file-excel"
    if suffix in {"ppt", "pptx", "odp"}:
        return "fa5s.file-powerpoint"
    return "fa5s.file"
