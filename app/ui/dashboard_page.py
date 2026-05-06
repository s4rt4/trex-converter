from __future__ import annotations

from collections.abc import Callable

from app.core.task import Task, TaskStatus
from app.data.database import TaskRepository
from app.ui.queue_panel import QueuePanel

try:
    from PySide6.QtCharts import (
        QBarCategoryAxis,
        QBarSeries,
        QBarSet,
        QChart,
        QChartView,
        QValueAxis,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPainter
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QListView,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = QPainter = None
    QBarCategoryAxis = QBarSeries = QBarSet = QChart = QChartView = QValueAxis = None
    QComboBox = QFrame = QGridLayout = QHBoxLayout = QLabel = QListView = QPushButton = QTabWidget = QVBoxLayout = QWidget = None


# (binary, "module label shown to the user")
ENGINE_BINARIES: tuple[tuple[str, str], ...] = (
    ("ffmpeg", "Video / Audio"),
    ("magick", "Image / Trace"),
    ("libreoffice", "Document"),
    ("qpdf", "PDF Repair / Linearize"),
    ("tesseract", "OCR"),
    ("inkscape", "SVG / Vector"),
    ("potrace", "Pixmap → SVG"),
    ("pandoc", "Ebook"),
    ("exiftool", "Metadata"),
    ("qrencode", "QR generate"),
    ("zbarimg", "QR / Barcode decode"),
)

GRANULARITIES: tuple[tuple[str, str], ...] = (
    ("Per day", "day"),
    ("Per week", "week"),
    ("Per month", "month"),
    ("Per year", "year"),
)


class DashboardPage(QWidget):
    def __init__(
        self,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
        repository: TaskRepository | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.summary_values: dict[str, QLabel] = {}
        self._engine_status_labels: dict[str, QLabel] = {}
        self._hwaccel_label: QLabel | None = None
        self._repository = repository

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("Dashboard", self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # Summary cards
        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(12)
        summary_grid.setVerticalSpacing(12)
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
            summary_grid.addWidget(card, index // 4, index % 4)
        root.addLayout(summary_grid)

        # Tabs: All Tasks + Activity chart + Engine availability
        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("DashboardTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(False)

        # ---- Tab 1: All Tasks ----
        self.queue_panel = QueuePanel(self)
        self.queue_panel.set_handlers(on_cancel, on_retry)
        self.tabs.addTab(self.queue_panel, "All Tasks")

        # ---- Tab 2: Activity chart ----
        self.tabs.addTab(self._build_chart_tab(), "Activity")

        # ---- Tab 3: Engine availability ----
        self.tabs.addTab(self._build_engine_tab(), "Engines")

        root.addWidget(self.tabs, 1)

    def _build_engine_tab(self) -> QWidget:
        page = QWidget(self)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header = QLabel("Engine availability", page)
        header.setObjectName("SectionTitle")
        header_row.addWidget(header)
        header_row.addStretch(1)
        refresh = QPushButton("Refresh", page)
        refresh.clicked.connect(self.refresh_engine_status)
        header_row.addWidget(refresh)
        outer.addLayout(header_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        cols = 3
        for index, (binary, module_label) in enumerate(ENGINE_BINARIES):
            row = index // cols
            col = index % cols
            card = EngineStatusCard(binary, module_label, page)
            self._engine_status_labels[binary] = card.status_label
            grid.addWidget(card, row, col)
        outer.addLayout(grid)

        self._hwaccel_label = QLabel("FFmpeg hardware accel: …", page)
        self._hwaccel_label.setObjectName("HintLabel")
        self._hwaccel_label.setWordWrap(True)
        outer.addWidget(self._hwaccel_label)
        outer.addStretch(1)

        self.refresh_engine_status()
        return page

    def _build_chart_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addWidget(_field("Bucket", page))

        self.granularity_combo = QComboBox(page)
        self.granularity_combo.setView(QListView(self.granularity_combo))
        for label, value in GRANULARITIES:
            self.granularity_combo.addItem(label, value)
        self.granularity_combo.currentIndexChanged.connect(self._refresh_chart)
        controls.addWidget(self.granularity_combo)

        controls.addStretch(1)
        refresh_button = QPushButton("Refresh", page)
        refresh_button.clicked.connect(self._refresh_chart)
        controls.addWidget(refresh_button)
        layout.addLayout(controls)

        self._chart = QChart()
        self._chart.setTitle("Tasks per bucket")
        self._chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._chart.legend().setVisible(False)

        self._chart_view = QChartView(self._chart, page)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._chart_view.setObjectName("DashboardChartView")
        layout.addWidget(self._chart_view, 1)

        self._refresh_chart()
        return page

    # ---- Updaters --------------------------------------------------------

    def refresh_engine_status(self) -> None:
        from shutil import which
        from app.ui.main_window import _detect_hwaccels_sync

        for binary, label in self._engine_status_labels.items():
            available = which(binary) is not None
            if available:
                label.setText("✔ installed")
                label.setObjectName("EngineStatusOk")
            else:
                label.setText("✘ missing")
                label.setObjectName("EngineStatusMissing")
            label.style().unpolish(label)
            label.style().polish(label)

        if self._hwaccel_label is not None:
            accels = _detect_hwaccels_sync()
            if accels:
                self._hwaccel_label.setText(
                    "FFmpeg hardware accel: " + ", ".join(accels)
                )
            else:
                self._hwaccel_label.setText(
                    "FFmpeg hardware accel: none detected (or ffmpeg missing)"
                )

    def _refresh_chart(self, *_args) -> None:
        if self._repository is None:
            return
        granularity = self.granularity_combo.currentData() or "day"
        try:
            buckets = self._repository.count_by_period(granularity)
        except Exception:  # pragma: no cover - defensive against schema drift
            buckets = []

        # Cap to the most recent 24 buckets so the chart stays readable when
        # there are years of history.
        buckets = buckets[-24:]

        # Replace the series.
        self._chart.removeAllSeries()
        for axis in list(self._chart.axes()):
            self._chart.removeAxis(axis)

        if not buckets:
            self._chart.setTitle("No tasks recorded yet")
            return

        bar_set = QBarSet("Tasks")
        labels = []
        max_count = 1
        for label, count in buckets:
            bar_set.append(count)
            labels.append(label)
            if count > max_count:
                max_count = count

        series = QBarSeries()
        series.append(bar_set)
        self._chart.addSeries(series)
        self._chart.setTitle(f"Tasks per {granularity} (last {len(buckets)})")

        category_axis = QBarCategoryAxis()
        category_axis.append(labels)
        self._chart.addAxis(category_axis, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(category_axis)

        value_axis = QValueAxis()
        # Round up to a sensible upper bound so bars don't kiss the top edge.
        upper = max(2, _round_up_axis(max_count))
        value_axis.setRange(0, upper)
        value_axis.setTickCount(min(upper + 1, 6))
        value_axis.setLabelFormat("%d")
        self._chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(value_axis)

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
        # Tasks list changed → chart should update if the user is sitting on
        # that tab. Also refresh in the background so revisiting is instant.
        self._refresh_chart()


# ---- Cards & helpers -----------------------------------------------------


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


class EngineStatusCard(QFrame):
    def __init__(self, binary: str, module_label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("EngineStatusCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        name = QLabel(binary, self)
        name.setObjectName("EngineStatusName")
        text_layout.addWidget(name)

        module = QLabel(module_label, self)
        module.setObjectName("EngineStatusModule")
        text_layout.addWidget(module)

        layout.addLayout(text_layout, 1)

        self.status_label = QLabel("…", self)
        self.status_label.setObjectName("EngineStatusPending")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.status_label)


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label


def _round_up_axis(value: int) -> int:
    """Round to a humane upper bound for the value axis."""
    if value <= 5:
        return 5
    if value <= 10:
        return 10
    # For larger counts, round to the next multiple of 5.
    return ((value + 4) // 5) * 5
