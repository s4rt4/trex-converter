from __future__ import annotations

from collections.abc import Callable

from app.core.task import Task, TaskStatus
from app.ui.icons import ICON_SIZE, surface_icon

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QHeaderView,
        QProgressBar,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QHeaderView = QProgressBar = QPushButton = QTableWidget = QTableWidgetItem = QVBoxLayout = QWidget = None


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
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
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
            values = [
                str(task.input_path),
                str(task.output_path),
                task.engine,
                task.status.value,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)

            progress = QProgressBar(self.table)
            progress.setObjectName("QueueProgress")
            progress.setRange(0, 100)
            progress.setValue(int(task.progress * 100))
            progress.setTextVisible(True)
            self.table.setCellWidget(row, 4, progress)

            cancel_button = QPushButton("Cancel", self.table)
            cancel_button.setObjectName("QueueActionButton")
            cancel_button.setIcon(surface_icon("fa5s.times-circle"))
            cancel_button.setIconSize(ICON_SIZE)
            cancel_button.setEnabled(task.status in {TaskStatus.PENDING, TaskStatus.RUNNING})
            cancel_button.clicked.connect(lambda _, task_id=task.id: self._cancel(task_id))
            self.table.setCellWidget(row, 5, cancel_button)

            retry_button = QPushButton("Retry", self.table)
            retry_button.setObjectName("QueueActionButton")
            retry_button.setIcon(surface_icon("fa5s.redo"))
            retry_button.setIconSize(ICON_SIZE)
            retry_button.setEnabled(task.can_retry())
            retry_button.clicked.connect(lambda _, task_id=task.id: self._retry(task_id))
            self.table.setCellWidget(row, 6, retry_button)

    def _cancel(self, task_id: str) -> None:
        if self._on_cancel:
            self._on_cancel(task_id)

    def _retry(self, task_id: str) -> None:
        if self._on_retry:
            self._on_retry(task_id)
