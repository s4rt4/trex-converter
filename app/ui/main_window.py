from __future__ import annotations

from string import Template

from app.core.dependency import DependencyChecker
from app.core.queue import TaskQueue
from app.core.registry import ConversionRegistry
from app.core.task import Task
from app.data.database import TaskRepository
from app.engines.imagemagick_engine import IMAGE_FORMATS
from app.engines.libreoffice_engine import SUPPORTED_INPUT_FORMATS
from app.ui.about_page import AboutPage
from app.ui.conversion_page import ConversionPage, ConversionPageConfig
from app.ui.dashboard_page import DashboardPage
from app.ui.image_options import ImageOptionsPanel
from app.ui.pdf_operations import PDFOperationsPanel
from app.ui.video_options import VideoOptionsPanel
from app.ui.icons import ICON_SIZE, accent_icon, app_icon, icon, surface_icon
from app.ui.theme import (
    BRAND_ACCENT,
    BRAND_DARK,
    BRAND_DARK_SOFT,
    BRAND_SURFACE,
    BRAND_SURFACE_MUTED,
    BRAND_SURFACE_SOFT,
    BRAND_TEXT,
)
from app.utils.paths import asset_path

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QStackedWidget,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QTimer = QPixmap = None
    QFrame = QHBoxLayout = QLabel = QListWidget = QListWidgetItem = QMainWindow = QMessageBox = QPushButton = QStackedWidget = QToolButton = QVBoxLayout = QWidget = None


PAGE_CONFIGS = (
    ConversionPageConfig(
        title="Image",
        input_formats=IMAGE_FORMATS,
        default_output="webp",
        engine_name="imagemagick",
        kind="image",
        show_quality=True,
        extra_options_factory=ImageOptionsPanel,
    ),
    ConversionPageConfig(
        title="Video",
        input_formats=("mp4", "mov", "mkv", "webm", "wav", "flac", "mp3"),
        default_output="mp4",
        engine_name="ffmpeg",
        kind="video",
        show_bitrate=True,
        extra_options_factory=VideoOptionsPanel,
    ),
    ConversionPageConfig(
        title="Document",
        input_formats=tuple(sorted(SUPPORTED_INPUT_FORMATS)),
        default_output="pdf",
        engine_name="libreoffice",
        kind="document",
    ),
    ConversionPageConfig(
        title="PDF Tools",
        input_formats=("pdf", "jpg", "jpeg", "png"),
        default_output="png",
        engine_name="pdf",
        kind="pdf",
        extra_options_factory=PDFOperationsPanel,
    ),
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("T-Rex Converter")
        self.setWindowIcon(app_icon())
        self.resize(1120, 720)
        self.registry = ConversionRegistry()
        self.queue = TaskQueue(
            self.registry.resolve,
            repository=TaskRepository(),
            resume_pending=True,
        )
        self.queue.subscribe(lambda _task: self._refresh_tasks())
        self.pages: list[ConversionPage] = []
        self.task_views = []

        self._build_shell()
        self._build_status_bar()
        self._refresh_tasks()
        QTimer.singleShot(0, self.queue.start)

    def _build_shell(self) -> None:
        root = QWidget(self)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget(root)
        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        dashboard = DashboardPage(
            on_cancel=self.queue.cancel,
            on_retry=self._retry_task,
            parent=self.stack,
        )
        self.task_views.append(dashboard)
        self.stack.addWidget(dashboard)

        for config in PAGE_CONFIGS:
            page = ConversionPage(
                config=config,
                registry=self.registry,
                on_enqueue=self._enqueue_task,
                on_cancel=self.queue.cancel,
                on_retry=self._retry_task,
                parent=self.stack,
            )
            self.pages.append(page)
            self.task_views.append(page)
            self.stack.addWidget(page)

        about = AboutPage(self.stack)
        self.task_views.append(about)
        self.stack.addWidget(about)
        layout.addWidget(self.stack, 1)

        self.setCentralWidget(root)
        self._apply_style()

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(204)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(self._build_sidebar_brand(sidebar))

        self.nav = QListWidget(sidebar)
        self.nav.setObjectName("SidebarNav")
        self.nav.addItem(QListWidgetItem(_page_icon("dashboard"), "Dashboard"))
        for config in PAGE_CONFIGS:
            self.nav.addItem(QListWidgetItem(_page_icon(config.kind), config.title))
        self.nav.addItem(QListWidgetItem(_page_icon("about"), "About"))
        self.nav.currentRowChanged.connect(self.stack_index_changed)
        layout.addWidget(self.nav, 1)

        footer = QWidget(sidebar)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.addStretch(1)
        deps_button = QToolButton(footer)
        deps_button.setObjectName("DependenciesButton")
        deps_button.setIcon(accent_icon("fa5s.check-circle"))
        deps_button.setIconSize(ICON_SIZE)
        deps_button.setToolTip("Check dependencies")
        deps_button.clicked.connect(self._show_dependencies)
        footer_layout.addWidget(deps_button)
        layout.addWidget(footer)

        self.nav.setCurrentRow(0)
        return sidebar

    def _build_sidebar_brand(self, parent: QWidget) -> QWidget:
        brand = QWidget(parent)
        brand.setObjectName("SidebarBrand")
        layout = QHBoxLayout(brand)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(10)

        logo = QLabel(brand)
        logo.setObjectName("SidebarLogo")
        pixmap = QPixmap(str(asset_path("trex-logo.svg")))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(34, 34))
        layout.addWidget(logo)

        title = QLabel("T-Rex Converter", brand)
        title.setObjectName("SidebarTitle")
        layout.addWidget(title, 1)
        return brand

    def stack_index_changed(self, row: int) -> None:
        if row >= 0:
            self.stack.setCurrentIndex(row)

    def _build_status_bar(self) -> None:
        self.statusBar().showMessage("Ready")

    def _enqueue_task(self, task: Task) -> None:
        self.queue.add(task)
        self.statusBar().showMessage(f"Queued {task.input_path.name}")
        self._refresh_tasks()

    def _show_dependencies(self) -> None:
        checker = DependencyChecker()
        statuses = checker.check_many(self.registry.required_binaries())
        lines = [
            f"{name}: {'OK' if status.available else 'missing'}"
            for name, status in statuses.items()
        ]
        QMessageBox.information(self, "Dependencies", "\n".join(lines))

    def _retry_task(self, task_id: str) -> None:
        try:
            self.queue.retry(task_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Retry Unavailable", str(exc))

    def _refresh_tasks(self) -> None:
        tasks = self.queue.all()
        for view in self.task_views:
            view.set_tasks(tasks)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            Template(
                """
            QMainWindow {
                background: $BRAND_SURFACE;
                color: $BRAND_TEXT;
            }
            #Sidebar {
                background: rgba(12, 44, 85, 236);
                border: 0;
                border-right: 1px solid rgba(86, 182, 198, 84);
            }
            #SidebarTitle {
                color: $BRAND_ACCENT;
                font-size: 15px;
                font-weight: 650;
                padding: 0;
            }
            #SidebarLogo {
                min-width: 34px;
                min-height: 34px;
                max-width: 34px;
                max-height: 34px;
            }
            #SidebarNav {
                background: transparent;
                border: 0;
                color: $BRAND_SURFACE;
                outline: 0;
            }
            #SidebarNav::item {
                min-height: 38px;
                padding: 6px 10px 6px 12px;
                border-radius: 8px;
                border-left: 3px solid transparent;
            }
            #SidebarNav::item:selected {
                background: rgba(86, 182, 198, 38);
                color: $BRAND_ACCENT;
                border-left: 3px solid $BRAND_ACCENT;
            }
            #SidebarNav::item:hover {
                background: rgba(239, 227, 202, 24);
            }
            #Sidebar QPushButton {
                background: rgba(36, 21, 143, 128);
                color: $BRAND_ACCENT;
                border: 1px solid rgba(86, 182, 198, 128);
                border-radius: 8px;
                padding: 9px 10px;
            }
            #DependenciesButton {
                background: rgba(86, 182, 198, 24);
                border: 1px solid rgba(86, 182, 198, 120);
                border-radius: 8px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0;
            }
            #PageTitle {
                color: $BRAND_TEXT;
                font-size: 24px;
                font-weight: 700;
            }
            #SectionTitle {
                color: $BRAND_TEXT;
                font-size: 15px;
                font-weight: 700;
            }
            #SummaryCard,
            #AboutPanel {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid rgba(86, 182, 198, 150);
                border-radius: 8px;
            }
            #SummaryValue {
                color: $BRAND_DARK;
                font-size: 28px;
                font-weight: 800;
            }
            #SummaryLabel,
            #AboutMeta,
            #AboutDescription {
                color: $BRAND_DARK_SOFT;
                font-size: 12px;
            }
            #AboutName {
                color: $BRAND_TEXT;
                font-size: 22px;
                font-weight: 800;
            }
            #AboutLogo {
                min-width: 78px;
                min-height: 78px;
            }
            #ToolPanel {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
                padding: 0;
            }
            QLabel {
                color: $BRAND_TEXT;
            }
            #FieldLabel {
                color: $BRAND_DARK;
                font-size: 12px;
                font-weight: 650;
            }
            QLineEdit,
            QComboBox {
                background: $BRAND_SURFACE;
                color: $BRAND_TEXT;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
                padding: 6px 9px;
                min-height: 26px;
                selection-background-color: $BRAND_ACCENT;
                selection-color: $BRAND_DARK;
            }
            QSpinBox,
            QDoubleSpinBox {
                background: $BRAND_SURFACE;
                color: $BRAND_TEXT;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
                padding: 6px 8px;
                min-height: 26px;
                selection-background-color: $BRAND_ACCENT;
                selection-color: $BRAND_DARK;
            }
            #PageTabs {
                background: transparent;
                border: 0;
            }
            #PageTabs::pane {
                background: transparent;
                border: 0;
                top: 0;
            }
            #PageTabs QTabBar::tab {
                background: rgba(228, 215, 189, 150);
                color: $BRAND_DARK;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
                padding: 8px 24px;
                margin-right: 8px;
                font-size: 13px;
                font-weight: 700;
            }
            #PageTabs QTabBar::tab:selected {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
                border: 1px solid $BRAND_DARK;
            }
            #PageTabs QTabBar::tab:hover:!selected {
                background: $BRAND_SURFACE_SOFT;
            }
            #ImageOptionsTabs,
            #PDFOperationsTabs,
            #VideoOptionsTabs {
                background: transparent;
                border: 0;
            }
            #ImageOptionsTabs::pane,
            #PDFOperationsTabs::pane,
            #VideoOptionsTabs::pane {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
                top: 10px;
            }
            #ImageOptionsTabs QTabBar,
            #PDFOperationsTabs QTabBar,
            #VideoOptionsTabs QTabBar {
                background: transparent;
                border: 0;
            }
            #ImageOptionsTabs QTabBar::tab,
            #PDFOperationsTabs QTabBar::tab,
            #VideoOptionsTabs QTabBar::tab {
                background: rgba(228, 215, 189, 150);
                color: $BRAND_DARK;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
                padding: 7px 18px;
                margin: 0 6px 6px 0;
                font-weight: 650;
            }
            #ImageOptionsTabs QTabBar::tab:selected,
            #PDFOperationsTabs QTabBar::tab:selected,
            #VideoOptionsTabs QTabBar::tab:selected {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
                border: 1px solid $BRAND_DARK;
            }
            #ImageOptionsTabs QTabBar::tab:hover:!selected,
            #PDFOperationsTabs QTabBar::tab:hover:!selected,
            #VideoOptionsTabs QTabBar::tab:hover:!selected {
                background: $BRAND_SURFACE_SOFT;
            }
            #ImageOptionsPanel QWidget,
            #PDFOperationsPanel QWidget,
            #VideoOptionsPanel QWidget {
                background: $BRAND_SURFACE_SOFT;
            }
            #ImageOptionsPanel QSlider::groove:horizontal,
            #PDFOperationsPanel QSlider::groove:horizontal,
            #VideoOptionsPanel QSlider::groove:horizontal {
                background: $BRAND_SURFACE_MUTED;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 4px;
                height: 8px;
            }
            #ImageOptionsPanel QSlider::handle:horizontal,
            #PDFOperationsPanel QSlider::handle:horizontal,
            #VideoOptionsPanel QSlider::handle:horizontal {
                background: $BRAND_DARK;
                border: 2px solid $BRAND_ACCENT;
                border-radius: 8px;
                width: 16px;
                margin: -5px 0;
            }
            QLineEdit:read-only {
                background: $BRAND_SURFACE_MUTED;
            }
            QLineEdit::placeholder {
                color: $BRAND_DARK_SOFT;
            }
            #OutputFormatCombo {
                border-right: 0;
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
            }
            QComboBox::drop-down {
                border: 0;
                width: 0;
            }
            QComboBox QAbstractItemView {
                background: $BRAND_SURFACE;
                color: $BRAND_TEXT;
                border: 1px solid $BRAND_ACCENT;
                selection-background-color: $BRAND_DARK;
                selection-color: $BRAND_SURFACE;
                outline: 0;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 26px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView::item:selected {
                background: $BRAND_DARK;
                color: $BRAND_SURFACE;
            }
            #OutputFormatButton {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
                border: 1px solid $BRAND_ACCENT;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
                min-width: 34px;
                min-height: 34px;
                padding: 0;
                font-size: 15px;
                font-weight: 700;
            }
            QCheckBox {
                color: $BRAND_TEXT;
                spacing: 8px;
            }
            QCheckBox::indicator {
                background: $BRAND_SURFACE;
                border: 1px solid $BRAND_DARK;
                border-radius: 3px;
                width: 14px;
                height: 14px;
            }
            QCheckBox::indicator:hover {
                border: 1px solid $BRAND_ACCENT;
            }
            QCheckBox::indicator:checked {
                background: $BRAND_DARK;
                border: 1px solid $BRAND_ACCENT;
            }
            QCheckBox::indicator:checked:hover {
                background: $BRAND_DARK_SOFT;
            }
            QPushButton {
                background: $BRAND_DARK;
                color: $BRAND_SURFACE;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
                padding: 5px 10px;
                min-height: 28px;
            }
            QToolButton {
                background: $BRAND_DARK;
                color: $BRAND_SURFACE;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
            }
            QToolButton:hover {
                background: $BRAND_DARK_SOFT;
            }
            QToolButton:disabled {
                background: $BRAND_SURFACE_MUTED;
                color: $BRAND_DARK_SOFT;
                border-color: $BRAND_SURFACE_MUTED;
            }
            QPushButton:hover {
                background: $BRAND_DARK_SOFT;
                color: $BRAND_ACCENT;
            }
            QPushButton:pressed {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
            }
            QPushButton:disabled {
                background: $BRAND_SURFACE_MUTED;
                color: $BRAND_DARK_SOFT;
                border-color: $BRAND_SURFACE_MUTED;
            }
            #QualitySlider::groove:horizontal {
                background: $BRAND_SURFACE_MUTED;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 4px;
                height: 8px;
            }
            #QualitySlider::handle:horizontal {
                background: $BRAND_DARK;
                border: 2px solid $BRAND_ACCENT;
                border-radius: 8px;
                width: 16px;
                margin: -5px 0;
            }
            #QualityValue {
                background: $BRAND_SURFACE;
                color: $BRAND_TEXT;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
                min-width: 34px;
                padding: 5px 8px;
            }
            QTableWidget {
                background: $BRAND_SURFACE_SOFT;
                color: $BRAND_TEXT;
                border: 1px solid $BRAND_ACCENT;
                selection-background-color: $BRAND_SURFACE_MUTED;
                selection-color: $BRAND_TEXT;
                border-radius: 8px;
            }
            QHeaderView::section {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
                border: 0;
                border-right: 1px solid rgba(86, 182, 198, 120);
                border-bottom: 1px solid rgba(86, 182, 198, 120);
                padding: 7px;
            }
            #QueueFilePreview {
                background: $BRAND_SURFACE;
                border: 1px solid $BRAND_SURFACE_MUTED;
                border-radius: 8px;
                min-width: 42px;
                min-height: 42px;
                max-width: 42px;
                max-height: 42px;
            }
            #QueueFileName {
                color: $BRAND_TEXT;
                font-size: 13px;
                font-weight: 700;
            }
            #QueueFilePath {
                color: $BRAND_DARK_SOFT;
                font-size: 11px;
            }
            QProgressBar {
                background: $BRAND_SURFACE_MUTED;
                color: $BRAND_TEXT;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 8px;
                text-align: center;
            }
            #QueueProgress {
                min-width: 82px;
                max-height: 22px;
                margin: 14px 6px;
            }
            QProgressBar::chunk {
                background: $BRAND_ACCENT;
                border-radius: 7px;
            }
            #QueueActionButton {
                border-radius: 8px;
                min-height: 28px;
                max-height: 28px;
                min-width: 32px;
                max-width: 32px;
                padding: 2px;
                margin: 12px 4px;
            }
            QStatusBar {
                background: $BRAND_SURFACE;
                color: $BRAND_TEXT;
            }
            """
            ).substitute(
                BRAND_ACCENT=BRAND_ACCENT,
                BRAND_DARK=BRAND_DARK,
                BRAND_DARK_SOFT=BRAND_DARK_SOFT,
                BRAND_SURFACE=BRAND_SURFACE,
                BRAND_SURFACE_MUTED=BRAND_SURFACE_MUTED,
                BRAND_SURFACE_SOFT=BRAND_SURFACE_SOFT,
                BRAND_TEXT=BRAND_TEXT,
            )
        )

    def closeEvent(self, event) -> None:
        # The asyncio task is cancelled by qasync during application shutdown.
        event.accept()


def _page_icon(kind: str):
    icons = {
        "image": "fa5s.image",
        "video": "fa5s.video",
        "document": "fa5s.file-alt",
        "pdf": "fa5s.file-pdf",
        "dashboard": "fa5s.chart-pie",
        "about": "fa5s.info-circle",
    }
    return surface_icon(icons.get(kind, "fa5s.file"))
