from __future__ import annotations

from app.core.dependency import DependencyChecker, dependency_label
from app.core.queue import TaskQueue
from app.core.registry import ConversionRegistry
from app.core.task import Task
from app.data.database import TaskRepository
from app.engines.imagemagick_engine import IMAGE_FORMATS
from app.engines.libreoffice_engine import SUPPORTED_INPUT_FORMATS
from app.ui.about_page import AboutPage
from app.ui.conversion_page import ConversionPage, ConversionPageConfig
from app.ui.dashboard_page import DashboardPage
from app.ui.audio_options import AudioOptionsPanel
from app.ui.document_options import DocumentOptionsPanel
from app.ui.image_options import ImageOptionsPanel
from app.ui.multi_input_options import (
    AudioMixOptionsPanel,
    ImageMontageOptionsPanel,
    PDFNumberingOptionsPanel,
    PDFSplitOptionsPanel,
    SlidesToImagesOptionsPanel,
    SubtitleMergeOptionsPanel,
)
from app.ui.ocr_options import OCROptionsPanel
from app.ui.pdf_operations import PDFOperationsPanel
from app.ui.ebook_options import EbookOptionsPanel
from app.ui.help_page import HelpPage
from app.ui.metadata_options import MetadataOptionsPanel
from app.ui.qr_options import QROptionsPanel
from app.ui.svg_options import SVGOptionsPanel
from app.ui.settings_page import SettingsPage
from app.ui.subtitle_options import SubtitleOptionsPanel
from app.ui.video_options import VideoOptionsPanel
from app.ui.icons import ICON_SIZE, SIDEBAR_ICON_SIZE, accent_icon, app_icon, icon, nav_icon, surface_icon
from app.ui.theme import build_stylesheet
from app.utils.paths import asset_path

try:
    from PySide6.QtCore import Qt, QTimer
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
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QTimer = QPixmap = None
    QFrame = QHBoxLayout = QLabel = QListWidget = QListWidgetItem = QMainWindow = QMessageBox = QPushButton = QStackedWidget = QToolButton = QTreeWidget = QTreeWidgetItem = QVBoxLayout = QWidget = None


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
        input_formats=("mp4", "mov", "mkv", "webm"),
        default_output="mp4",
        engine_name="ffmpeg",
        kind="video",
        show_bitrate=True,
        extra_options_factory=VideoOptionsPanel,
    ),
    ConversionPageConfig(
        title="Audio",
        input_formats=(
            "mp3", "wav", "aac", "flac", "m4a", "opus", "ogg",
            "mp4", "mov", "mkv", "webm",
        ),
        default_output="mp3",
        engine_name="ffmpeg",
        kind="audio",
        show_bitrate=True,
        extra_options_factory=AudioOptionsPanel,
    ),
    ConversionPageConfig(
        title="Document",
        input_formats=tuple(sorted(SUPPORTED_INPUT_FORMATS)),
        default_output="pdf",
        engine_name="libreoffice",
        kind="document",
        extra_options_factory=DocumentOptionsPanel,
    ),
    ConversionPageConfig(
        title="Subtitle",
        input_formats=("srt", "vtt", "ass"),
        default_output="vtt",
        engine_name="subtitle",
        kind="subtitle",
        force_engine=True,
        extra_options_factory=SubtitleOptionsPanel,
    ),
    ConversionPageConfig(
        title="OCR",
        input_formats=("png", "jpg", "jpeg", "tif", "tiff", "bmp", "pdf"),
        default_output="txt",
        engine_name="tesseract",
        kind="ocr",
        force_engine=True,
        extra_options_factory=OCROptionsPanel,
    ),
    ConversionPageConfig(
        title="PDF Tools",
        input_formats=("pdf",),
        default_output="pdf",
        engine_name="pdf",
        kind="pdf",
        extra_options_factory=PDFOperationsPanel,
    ),
    ConversionPageConfig(
        title="PDF Merge",
        input_formats=("pdf",),
        default_output="pdf",
        engine_name="pdf",
        kind="pdf-merge",
        force_engine=True,
        multi_input=True,
        default_options=(("operation", "merge"),),
    ),
    ConversionPageConfig(
        title="PDF Split",
        input_formats=("pdf",),
        default_output="folder",
        engine_name="pdf",
        kind="pdf-split",
        force_engine=True,
        directory_output=True,
        extra_options_factory=PDFSplitOptionsPanel,
    ),
    ConversionPageConfig(
        title="PDF Numbering",
        input_formats=("pdf",),
        default_output="pdf",
        engine_name="pdf",
        kind="pdf-numbering",
        force_engine=True,
        extra_options_factory=PDFNumberingOptionsPanel,
    ),
    ConversionPageConfig(
        title="PDF Extract Images",
        input_formats=("pdf",),
        default_output="folder",
        engine_name="pdf",
        kind="pdf-extract-images",
        force_engine=True,
        directory_output=True,
        default_options=(("operation", "extract_images"),),
    ),
    ConversionPageConfig(
        title="PDF Extract Attachments",
        input_formats=("pdf",),
        default_output="folder",
        engine_name="pdf",
        kind="pdf-extract-attachments",
        force_engine=True,
        directory_output=True,
        default_options=(("operation", "extract_attachments"),),
    ),
    ConversionPageConfig(
        title="Slides to Images",
        input_formats=("pptx", "ppt", "odp"),
        default_output="folder",
        engine_name="libreoffice",
        kind="slides-to-images",
        force_engine=True,
        directory_output=True,
        extra_options_factory=SlidesToImagesOptionsPanel,
    ),
    ConversionPageConfig(
        title="Document Merge",
        input_formats=tuple(sorted({*SUPPORTED_INPUT_FORMATS, "pdf"})),
        default_output="pdf",
        engine_name="libreoffice",
        kind="document-merge",
        force_engine=True,
        multi_input=True,
        default_options=(("operation", "bulk_merge_to_pdf"),),
    ),
    ConversionPageConfig(
        title="Video Concat",
        input_formats=("mp4", "mov", "mkv", "webm"),
        default_output="mp4",
        engine_name="ffmpeg",
        kind="video-concat",
        force_engine=True,
        multi_input=True,
        default_options=(("operation", "concat"),),
    ),
    ConversionPageConfig(
        title="Audio Mix",
        input_formats=("mp3", "wav", "aac", "flac", "m4a", "opus", "ogg"),
        default_output="mp3",
        engine_name="ffmpeg",
        kind="audio-mix",
        force_engine=True,
        multi_input=True,
        default_options=(("operation", "mix"),),
        extra_options_factory=AudioMixOptionsPanel,
    ),
    ConversionPageConfig(
        title="Image Montage",
        input_formats=IMAGE_FORMATS,
        default_output="png",
        engine_name="imagemagick",
        kind="image-montage",
        force_engine=True,
        multi_input=True,
        default_options=(("operation", "montage"),),
        extra_options_factory=ImageMontageOptionsPanel,
    ),
    ConversionPageConfig(
        title="Subtitle Merge",
        input_formats=("srt", "vtt", "ass"),
        default_output="srt",
        engine_name="subtitle",
        kind="subtitle-merge",
        force_engine=True,
        multi_input=True,
        default_options=(("operation", "merge"),),
        extra_options_factory=SubtitleMergeOptionsPanel,
    ),
    ConversionPageConfig(
        title="Archive",
        input_formats=("zip", "tar", "tgz", "tbz", "txz", "gz", "bz2", "xz"),
        default_output="folder",
        engine_name="archive",
        kind="archive",
        force_engine=True,
        directory_output=True,
    ),
    ConversionPageConfig(
        title="Archive Compress",
        input_formats=("folder",),
        default_output="zip",
        engine_name="archive",
        kind="archive-compress",
        force_engine=True,
        directory_input=True,
    ),
    ConversionPageConfig(
        title="QR / Barcode",
        input_formats=(
            "txt",
            "png", "jpg", "jpeg", "bmp", "tif", "tiff", "gif", "webp",
        ),
        default_output="png",
        engine_name="qr",
        kind="qr",
        force_engine=True,
        extra_options_factory=QROptionsPanel,
    ),
    ConversionPageConfig(
        title="SVG / Vector",
        input_formats=(
            "svg",
            "pdf",
            "dxf",
            "png", "jpg", "jpeg", "bmp", "tif", "tiff", "gif", "webp",
        ),
        default_output="png",
        engine_name="inkscape",
        kind="svg",
        force_engine=True,
        extra_options_factory=SVGOptionsPanel,
    ),
    ConversionPageConfig(
        title="Subtitle Extract",
        input_formats=("mkv", "mp4", "mov", "webm"),
        default_output="srt",
        engine_name="ffmpeg",
        kind="subtitle-extract",
        force_engine=True,
    ),
    ConversionPageConfig(
        title="PDF Compare",
        input_formats=("pdf",),
        default_output="folder",
        engine_name="pdf",
        kind="pdf-compare",
        multi_input=True,
        force_engine=True,
        directory_output=True,
        default_options=(("operation", "compare"),),
    ),
    ConversionPageConfig(
        title="Ebook",
        input_formats=(
            "epub", "docx", "odt", "html", "htm",
            "md", "markdown", "rst", "latex", "tex", "org", "fb2",
        ),
        default_output="epub",
        engine_name="pandoc",
        kind="ebook",
        force_engine=True,
        extra_options_factory=EbookOptionsPanel,
    ),
    ConversionPageConfig(
        title="Metadata",
        input_formats=(
            "jpg", "jpeg", "png", "tif", "tiff", "heic", "webp", "gif",
            "mp3", "m4a", "flac", "wav", "ogg",
            "mp4", "mov", "mkv", "webm",
            "pdf",
        ),
        default_output="jpg",
        engine_name="exiftool",
        kind="metadata",
        force_engine=True,
        extra_options_factory=MetadataOptionsPanel,
    ),
)


# Sidebar grouping: each conversion page (by `kind`) belongs to one category.
# Categories render as collapsible parents in the sidebar tree. Order here is
# the display order; every PAGE_CONFIGS kind must appear exactly once.
SIDEBAR_GROUPS = (
    ("Image", ("image", "image-montage", "svg")),
    ("Video", ("video", "video-concat")),
    ("Audio", ("audio", "audio-mix")),
    ("Document", ("document", "document-merge", "ebook", "slides-to-images")),
    ("PDF", (
        "pdf", "pdf-merge", "pdf-split", "pdf-numbering",
        "pdf-extract-images", "pdf-extract-attachments", "pdf-compare",
    )),
    ("Subtitle", ("subtitle", "subtitle-merge", "subtitle-extract")),
    ("Archive", ("archive", "archive-compress")),
    ("Utility", ("ocr", "qr", "metadata")),
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("T-Rex Converter")
        self.setWindowIcon(app_icon())
        self.resize(1120, 720)
        self.registry = ConversionRegistry()
        from app.core.settings import get_settings as _get_settings

        self.repository = TaskRepository()
        self.queue = TaskQueue(
            self.registry.resolve,
            max_concurrency=max(1, _get_settings().max_concurrency),
            repository=self.repository,
            resume_pending=True,
            engine_by_name=self.registry.engine_by_name,
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
        # HelpPage is constructed early so the sidebar's docs-mode list can
        # query its topic metas during sidebar construction.
        self.help_page = HelpPage(self.stack)

        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        dashboard = DashboardPage(
            on_cancel=self.queue.cancel,
            on_retry=self._retry_task,
            repository=self.repository,
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
            page.help_requested.connect(self._open_help_for_kind)
            self.pages.append(page)
            self.task_views.append(page)
            self.stack.addWidget(page)

        settings = SettingsPage(self.stack)
        self.task_views.append(settings)
        self.stack.addWidget(settings)

        about = AboutPage(self.stack)
        self.task_views.append(about)
        self.stack.addWidget(about)

        self.help_page_index = self.stack.addWidget(self.help_page)

        layout.addWidget(self.stack, 1)

        self.setCentralWidget(root)
        self._apply_style()

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(232)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(self._build_sidebar_brand(sidebar))

        self.nav_stack = QStackedWidget(sidebar)
        self.nav_stack.setObjectName("SidebarStack")
        layout.addWidget(self.nav_stack, 1)

        self.nav_stack.addWidget(self._build_main_nav(sidebar))
        self.nav_stack.addWidget(self._build_docs_nav(sidebar))

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

        # Default: main mode, Dashboard selected, Image group expanded.
        self.nav.topLevelItem(1).setExpanded(True)
        self.nav.setCurrentItem(self._dashboard_item)
        return sidebar

    def _build_main_nav(self, parent: QWidget) -> QWidget:
        self.nav = QTreeWidget(parent)
        self.nav.setObjectName("SidebarNav")
        self.nav.setHeaderHidden(True)
        self.nav.setColumnCount(1)
        self.nav.setIconSize(SIDEBAR_ICON_SIZE)
        self.nav.setIndentation(16)
        # We hide Qt's default branch arrows and use ▸/▾ text prefixes instead,
        # which render predictably on the dark sidebar without image assets.
        self.nav.setRootIsDecorated(False)
        self.nav.setExpandsOnDoubleClick(False)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)

        # Map each page kind to its index in the right-hand QStackedWidget.
        # The stack is built as: Dashboard(0), PAGE_CONFIGS(1..N), then
        # Settings, About, Help — see _build_shell.
        stack_index = {config.kind: i + 1 for i, config in enumerate(PAGE_CONFIGS)}
        title_for = {config.kind: config.title for config in PAGE_CONFIGS}

        self._nav_index_items: dict[int, QTreeWidgetItem] = {}
        self._dashboard_item = self._add_nav_leaf(
            None, "Dashboard", _page_icon("dashboard"), 0
        )

        for group_title, kinds in SIDEBAR_GROUPS:
            group_item = QTreeWidgetItem(self.nav, [f"▸ {group_title}"])
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # header: not selectable
            group_item.setData(0, Qt.ItemDataRole.UserRole + 1, group_title)
            font = group_item.font(0)
            font.setBold(True)
            group_item.setFont(0, font)
            for kind in kinds:
                self._add_nav_leaf(
                    group_item, title_for[kind], _page_icon(kind), stack_index[kind]
                )

        settings_index = len(PAGE_CONFIGS) + 1
        self._add_nav_leaf(None, "Settings", _page_icon("settings"), settings_index)
        self._add_nav_leaf(None, "About", _page_icon("about"), settings_index + 1)
        # Sentinel: "Need Help ?" — selecting it switches the sidebar to docs
        # mode and the right pane to the HelpPage.
        help_item = self._add_nav_leaf(None, "Need Help ?", _page_icon("help"), None)
        help_item.setData(0, Qt.ItemDataRole.UserRole, "help-entry")

        self.nav.currentItemChanged.connect(self._nav_item_changed)
        self.nav.itemClicked.connect(self._nav_item_clicked)
        self.nav.itemExpanded.connect(self._nav_group_toggled)
        self.nav.itemCollapsed.connect(self._nav_group_toggled)
        return self.nav

    def _add_nav_leaf(
        self, parent, label: str, page_icon, target_index: int | None
    ) -> "QTreeWidgetItem":
        item = QTreeWidgetItem(parent or self.nav, [label])
        item.setIcon(0, page_icon)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        if target_index is not None:
            item.setData(0, Qt.ItemDataRole.UserRole, target_index)
            self._nav_index_items[target_index] = item
        return item

    def _nav_group_toggled(self, item: "QTreeWidgetItem") -> None:
        # Keep the ▸/▾ prefix in sync with the expanded state.
        group_title = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if group_title:
            item.setText(0, f"{'▾' if item.isExpanded() else '▸'} {group_title}")

    def _nav_item_clicked(self, item: "QTreeWidgetItem", _column: int) -> None:
        # Clicking a category header (anywhere on the row) toggles it.
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _nav_item_changed(self, current, _previous) -> None:
        if current is None:
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if data == "help-entry":
            self._enter_docs_mode()
            return
        if isinstance(data, int):
            self._last_main_stack_index = data
            self.stack.setCurrentIndex(data)

    def _build_docs_nav(self, parent: QWidget) -> QWidget:
        container = QWidget(parent)
        container.setObjectName("DocsNavContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        back_button = QPushButton("← Back to main menu", container)
        back_button.setObjectName("DocsBackButton")
        back_button.clicked.connect(self._exit_docs_mode)
        layout.addWidget(back_button)

        self.docs_nav = QListWidget(container)
        self.docs_nav.setObjectName("SidebarNav")
        self.docs_nav.setIconSize(SIDEBAR_ICON_SIZE)
        self.docs_nav.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.docs_nav.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.docs_nav.currentRowChanged.connect(self._docs_nav_changed)
        layout.addWidget(self.docs_nav, 1)

        self._populate_docs_nav()
        return container

    def _populate_docs_nav(self) -> None:
        """Rebuild the docs sidebar list using HelpPage's current language."""
        self.docs_nav.blockSignals(True)
        self.docs_nav.clear()
        self._docs_nav_slugs: list[str] = []
        for topic in self.help_page.topic_metas():
            self.docs_nav.addItem(QListWidgetItem(topic.title))
            self._docs_nav_slugs.append(topic.slug)
        self.docs_nav.blockSignals(False)

    def _enter_docs_mode(self, slug: str | None = None) -> None:
        # Refresh in case the language toggle changed the topic list.
        self._populate_docs_nav()
        self.nav_stack.setCurrentIndex(1)
        self.stack.setCurrentIndex(self.help_page_index)
        target = slug or "_index"
        if target in self._docs_nav_slugs:
            self.docs_nav.blockSignals(True)
            self.docs_nav.setCurrentRow(self._docs_nav_slugs.index(target))
            self.docs_nav.blockSignals(False)
        self.help_page.show_topic(target)

    def _exit_docs_mode(self) -> None:
        self.nav_stack.setCurrentIndex(0)
        # Restore the last non-help page, defaulting to Dashboard.
        target_index = getattr(self, "_last_main_stack_index", 0)
        item = self._nav_index_items.get(target_index, self._dashboard_item)
        if item.parent() is not None:
            item.parent().setExpanded(True)
        self.nav.blockSignals(True)
        self.nav.setCurrentItem(item)
        self.nav.blockSignals(False)
        self.stack.setCurrentIndex(target_index)

    def _docs_nav_changed(self, row: int) -> None:
        if 0 <= row < len(self._docs_nav_slugs):
            self.help_page.show_topic(self._docs_nav_slugs[row])

    def _open_help_for_kind(self, kind: str) -> None:
        # Most page kinds match the doc slug 1:1; record exceptions here.
        slug_map = {
            "pdf": "pdf-tools",
        }
        slug = slug_map.get(kind, kind)
        self._enter_docs_mode(slug=slug)

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
            f"{dependency_label(name)}: {'OK' if status.available else 'missing'}"
            for name, status in statuses.items()
        ]

        accels = _detect_hwaccels_sync()
        if accels:
            lines.append("")
            lines.append("FFmpeg hardware accel: " + ", ".join(accels))
        else:
            lines.append("")
            lines.append("FFmpeg hardware accel: none detected")

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
        self.setStyleSheet(build_stylesheet())

    def closeEvent(self, event) -> None:
        # The asyncio task is cancelled by qasync during application shutdown.
        event.accept()


def _detect_hwaccels_sync() -> list[str]:
    """Synchronous wrapper around `ffmpeg -hwaccels`.

    Used from GUI handlers that don't have an event loop available.
    """
    import shutil
    import subprocess

    if shutil.which("ffmpeg") is None:
        return []
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    if result.returncode != 0:
        return []
    accels: list[str] = []
    for line in result.stdout.splitlines():
        token = line.strip()
        if not token or ":" in token:
            continue
        accels.append(token)
    return accels


def _page_icon(kind: str):
    icons = {
        "image": "fa5s.image",
        "video": "fa5s.video",
        "audio": "fa5s.music",
        "ocr": "fa5s.font",
        "subtitle": "fa5s.closed-captioning",
        "settings": "fa5s.cog",
        "document": "fa5s.file-alt",
        "pdf": "fa5s.file-pdf",
        "pdf-merge": "fa5s.copy",
        "pdf-split": "fa5s.cut",
        "pdf-numbering": "fa5s.list-ol",
        "pdf-extract-images": "fa5s.images",
        "pdf-extract-attachments": "fa5s.paperclip",
        "slides-to-images": "fa5s.images",
        "document-merge": "fa5s.file-medical",
        "video-concat": "fa5s.film",
        "audio-mix": "fa5s.compact-disc",
        "image-montage": "fa5s.th",
        "subtitle-merge": "fa5s.layer-group",
        "dashboard": "fa5s.chart-pie",
        "about": "fa5s.info-circle",
        "archive": "fa5s.file-archive",
        "archive-compress": "fa5s.compress",
        "qr": "fa5s.qrcode",
        "svg": "fa5s.bezier-curve",
        "subtitle-extract": "fa5s.closed-captioning",
        "ebook": "fa5s.book",
        "pdf-compare": "fa5s.balance-scale",
        "metadata": "fa5s.tags",
        "help": "fa5s.question-circle",
        "docs-topic": "fa5s.book-open",
    }
    return nav_icon(icons.get(kind, "fa5s.file"))
