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
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = QPixmap = None
    QHBoxLayout = QHeaderView = QLabel = QProgressBar = QTableWidget = QTableWidgetItem = QToolButton = QVBoxLayout = QWidget = None


class QueuePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._on_cancel: Callable[[str], None] | None = None
        self._on_retry: Callable[[str], None] | None = None
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels(["Input", "Output", "Engine", "Status", "Progress", "", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

    def set_handlers(
        self,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
    ) -> None:
        self._on_cancel = on_cancel
        self._on_retry = on_retry

    def set_tasks(self, tasks: list[Task]) -> None:
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

    def _cancel(self, task_id: str) -> None:
        if self._on_cancel:
            self._on_cancel(task_id)

    def _retry(self, task_id: str) -> None:
        if self._on_retry:
            self._on_retry(task_id)


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
