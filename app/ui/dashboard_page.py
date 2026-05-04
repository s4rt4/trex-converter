from __future__ import annotations

from collections.abc import Callable

from app.core.task import Task, TaskStatus
from app.ui.queue_panel import QueuePanel

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = None
    QFrame = QGridLayout = QLabel = QVBoxLayout = QWidget = None


class DashboardPage(QWidget):
    def __init__(
        self,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.summary_values: dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Dashboard", self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        for index, (key, label) in enumerate(
            (
                ("total", "Total tasks"),
                ("running", "Running"),
                ("success", "Completed"),
                ("failed", "Needs attention"),
            )
        ):
            card = SummaryCard(label, self)
            self.summary_values[key] = card.value_label
            grid.addWidget(card, index // 4, index % 4)
        root.addLayout(grid)

        recent_title = QLabel("All Tasks", self)
        recent_title.setObjectName("SectionTitle")
        root.addWidget(recent_title)

        self.queue_panel = QueuePanel(self)
        self.queue_panel.set_handlers(on_cancel, on_retry)
        root.addWidget(self.queue_panel, 1)

    def set_tasks(self, tasks: list[Task]) -> None:
        counts = {
            "total": len(tasks),
            "running": len([task for task in tasks if task.status == TaskStatus.RUNNING]),
            "success": len([task for task in tasks if task.status == TaskStatus.SUCCESS]),
            "failed": len([task for task in tasks if task.status == TaskStatus.FAILED]),
        }
        for key, value in counts.items():
            self.summary_values[key].setText(str(value))
        self.queue_panel.set_tasks(tasks)


class SummaryCard(QFrame):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SummaryCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.value_label = QLabel("0", self)
        self.value_label.setObjectName("SummaryValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.value_label)

        label_widget = QLabel(label, self)
        label_widget.setObjectName("SummaryLabel")
        layout.addWidget(label_widget)
