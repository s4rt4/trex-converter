from string import Template

from app.utils.paths import asset_path

BRAND_SURFACE = "#EFE3CA"
BRAND_DARK = "#0C2C55"
BRAND_ACCENT = "#56B6C6"
BRAND_SURFACE_MUTED = "#E4D7BD"
BRAND_SURFACE_SOFT = "#F6EBD4"
BRAND_DARK_SOFT = "#24158F"
BRAND_TEXT = "#0C2C55"

_STYLESHEET = Template(
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
                /* Confine selection paint to the item content (icon+text) only.
                   show-decoration-selected:0 stops the row/indent column from
                   being painted, and a transparent selection color leaves the
                   rounded ::item:selected rule as the only highlight. */
                show-decoration-selected: 0;
                selection-background-color: transparent;
                selection-color: $BRAND_ACCENT;
            }
            #SidebarNav::item {
                min-height: 30px;
                padding: 4px 8px 4px 10px;
                border: 0;
                border-radius: 8px;
            }
            #SidebarNav::item:selected {
                background: rgba(86, 182, 198, 38);
                color: $BRAND_ACCENT;
            }
            #SidebarNav::item:hover:!selected {
                background: rgba(239, 227, 202, 24);
            }
            /* Hide Qt's default expand/collapse arrows (▸/▾ text prefixes are
               used instead) and keep the indentation/branch column transparent
               in every state, otherwise a selected child paints a solid bar in
               the indent region at the far left. */
            #SidebarNav::branch,
            #SidebarNav::branch:selected,
            #SidebarNav::branch:hover,
            #SidebarNav::branch:has-children,
            #SidebarNav::branch:has-siblings {
                background: transparent;
                border-image: none;
                image: none;
            }
            #SidebarNav QScrollBar:vertical,
            #ConvertScroll QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px 2px;
                border: 0;
            }
            #SidebarNav QScrollBar::handle:vertical,
            #ConvertScroll QScrollBar::handle:vertical {
                background: rgba(86, 182, 198, 64);
                border-radius: 3px;
                min-height: 24px;
            }
            #SidebarNav QScrollBar::handle:vertical:hover,
            #ConvertScroll QScrollBar::handle:vertical:hover {
                background: rgba(86, 182, 198, 140);
            }
            #SidebarNav QScrollBar::add-line:vertical,
            #SidebarNav QScrollBar::sub-line:vertical,
            #ConvertScroll QScrollBar::add-line:vertical,
            #ConvertScroll QScrollBar::sub-line:vertical {
                background: transparent;
                height: 0;
                border: 0;
            }
            #SidebarNav QScrollBar::add-page:vertical,
            #SidebarNav QScrollBar::sub-page:vertical,
            #ConvertScroll QScrollBar::add-page:vertical,
            #ConvertScroll QScrollBar::sub-page:vertical {
                background: transparent;
            }
            #ConvertScroll,
            #ConvertScrollContent {
                background: transparent;
                border: 0;
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
            #EngineStatusCard {
                background: rgba(228, 215, 189, 80);
                border: 1px solid rgba(86, 182, 198, 100);
                border-radius: 6px;
            }
            #EngineStatusName {
                color: $BRAND_DARK;
                font-size: 12px;
                font-weight: 700;
            }
            #EngineStatusModule {
                color: $BRAND_DARK_SOFT;
                font-size: 11px;
            }
            #EngineStatusOk {
                color: #1f7a3d;
                font-size: 11px;
                font-weight: 700;
            }
            #EngineStatusMissing {
                color: #b1382e;
                font-size: 11px;
                font-weight: 700;
            }
            #EngineStatusPending {
                color: $BRAND_DARK_SOFT;
                font-size: 11px;
            }
            #HintLabel {
                color: $BRAND_DARK_SOFT;
                font-size: 11px;
            }
            #DocsBackButton {
                background: rgba(36, 21, 143, 128);
                color: $BRAND_ACCENT;
                border: 1px solid rgba(86, 182, 198, 128);
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: 650;
                text-align: left;
            }
            #DocsBackButton:hover {
                background: rgba(86, 182, 198, 90);
                color: $BRAND_SURFACE;
            }
            #PageHelpButton {
                background: rgba(86, 182, 198, 60);
                color: $BRAND_DARK;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 14px;
                min-width: 26px;
                min-height: 26px;
                font-weight: 800;
            }
            #PageHelpButton:hover {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
            }
            #HelpLanguageButton {
                padding: 6px 14px;
                border-radius: 8px;
                border: 1px solid rgba(86, 182, 198, 145);
                background: rgba(228, 215, 189, 150);
                color: $BRAND_DARK;
                font-weight: 650;
            }
            #HelpLanguageButton:checked {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
                border: 1px solid $BRAND_DARK;
            }
            #HelpSearch {
                padding: 6px 10px;
                border-radius: 8px;
            }
            #HelpBrowser {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
                padding: 8px 12px;
                color: $BRAND_DARK;
            }
            #HelpBrowser a {
                color: $BRAND_DARK;
                text-decoration: underline;
            }
            #HelpSearchPopup {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
                padding: 4px;
            }
            #HelpSearchPopup::item {
                padding: 6px 8px;
                color: $BRAND_DARK;
            }
            #HelpSearchPopup::item:selected {
                background: $BRAND_DARK;
                color: $BRAND_ACCENT;
                border-radius: 6px;
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
                background: transparent;
                border: 0;
                padding: 0;
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
                padding-right: 22px;
                min-height: 26px;
                selection-background-color: $BRAND_ACCENT;
                selection-color: $BRAND_DARK;
            }
            /* Spin (increment/decrement) buttons: flush to the field's right
               edge, sharing its rounded corners, with CSS-triangle arrows so
               no image assets are needed. */
            QSpinBox::up-button,
            QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid $BRAND_ACCENT;
                border-top-right-radius: 8px;
                background: $BRAND_SURFACE_MUTED;
            }
            QSpinBox::down-button,
            QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                border-left: 1px solid $BRAND_ACCENT;
                border-bottom-right-radius: 8px;
                background: $BRAND_SURFACE_MUTED;
            }
            QSpinBox::up-button:hover,
            QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover,
            QDoubleSpinBox::down-button:hover {
                background: $BRAND_ACCENT;
            }
            /* Styling the buttons suppresses Qt's native arrows, so we supply
               explicit caret images (paths injected by build_stylesheet). */
            QSpinBox::up-arrow,
            QDoubleSpinBox::up-arrow {
                image: url($SPIN_UP_ICON);
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow,
            QDoubleSpinBox::down-arrow {
                image: url($SPIN_DOWN_ICON);
                width: 10px;
                height: 10px;
            }
            #PageTabs {
                background: transparent;
                border: 0;
            }
            /* Underline tab style: flat text tabs sitting on a single baseline
               (the pane's top border); the active tab is marked by an accent
               underline that overlaps the baseline via the -1px bottom margin. */
            #PageTabs::pane {
                background: transparent;
                border: 0;
                border-top: 1px solid rgba(86, 182, 198, 90);
                top: -1px;
            }
            #PageTabs QTabBar {
                background: transparent;
                border: 0;
            }
            #PageTabs QTabBar::tab {
                background: transparent;
                color: $BRAND_DARK_SOFT;
                border: 0;
                border-bottom: 2px solid transparent;
                padding: 8px 18px;
                margin: 0 6px -1px 0;
                font-size: 13px;
                font-weight: 600;
            }
            #PageTabs QTabBar::tab:selected {
                color: $BRAND_DARK;
                border-bottom: 2px solid $BRAND_ACCENT;
                font-weight: 800;
            }
            #PageTabs QTabBar::tab:hover:!selected {
                color: $BRAND_DARK;
                border-bottom: 2px solid rgba(86, 182, 198, 110);
            }
            #ImageOptionsTabs,
            #PDFOperationsTabs,
            #VideoOptionsTabs,
            #AudioOptionsTabs {
                background: transparent;
                border: 0;
            }
            #OCROptionsPanel,
            #SubtitleOptionsPanel,
            #AudioMixOptionsPanel,
            #ImageMontageOptionsPanel,
            #SubtitleMergeOptionsPanel,
            #PDFSplitOptionsPanel,
            #PDFNumberingOptionsPanel,
            #SlidesToImagesOptionsPanel,
            #DocumentOptionsPanel,
            #QROptionsPanel,
            #EbookOptionsPanel,
            #MetadataOptionsPanel {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
            }
            #ImageOptionsTabs::pane,
            #PDFOperationsTabs::pane,
            #VideoOptionsTabs::pane,
            #AudioOptionsTabs::pane,
            #SVGOptionsTabs::pane,
            #DashboardTabs::pane {
                background: $BRAND_SURFACE_SOFT;
                border: 1px solid rgba(86, 182, 198, 145);
                border-radius: 8px;
                top: 6px;
            }
            #ImageOptionsTabs QTabBar,
            #PDFOperationsTabs QTabBar,
            #VideoOptionsTabs QTabBar,
            #AudioOptionsTabs QTabBar,
            #SVGOptionsTabs QTabBar,
            #DashboardTabs QTabBar {
                background: transparent;
                border: 0;
            }
            /* Underline tabs (flat text, accent underline on the active tab)
               floating above the content card — no boxes, nothing covers the
               card's border. */
            #ImageOptionsTabs QTabBar::tab,
            #PDFOperationsTabs QTabBar::tab,
            #VideoOptionsTabs QTabBar::tab,
            #AudioOptionsTabs QTabBar::tab,
            #SVGOptionsTabs QTabBar::tab,
            #DashboardTabs QTabBar::tab {
                background: transparent;
                color: $BRAND_DARK_SOFT;
                border: 0;
                border-bottom: 2px solid transparent;
                padding: 7px 14px;
                margin: 0 4px 0 0;
                font-weight: 600;
            }
            #ImageOptionsTabs QTabBar::tab:selected,
            #PDFOperationsTabs QTabBar::tab:selected,
            #VideoOptionsTabs QTabBar::tab:selected,
            #AudioOptionsTabs QTabBar::tab:selected,
            #SVGOptionsTabs QTabBar::tab:selected,
            #DashboardTabs QTabBar::tab:selected {
                color: $BRAND_DARK;
                border-bottom: 2px solid $BRAND_ACCENT;
                font-weight: 800;
            }
            #ImageOptionsTabs QTabBar::tab:hover:!selected,
            #PDFOperationsTabs QTabBar::tab:hover:!selected,
            #VideoOptionsTabs QTabBar::tab:hover:!selected,
            #AudioOptionsTabs QTabBar::tab:hover:!selected,
            #SVGOptionsTabs QTabBar::tab:hover:!selected,
            #DashboardTabs QTabBar::tab:hover:!selected {
                color: $BRAND_DARK;
                border-bottom: 2px solid rgba(86, 182, 198, 110);
            }
            #ImageOptionsPanel QWidget,
            #PDFOperationsPanel QWidget,
            #VideoOptionsPanel QWidget,
            #AudioOptionsPanel QWidget,
            #SVGOptionsPanel QWidget,
            #OCROptionsPanel,
            #OCROptionsPanel QWidget,
            #SubtitleOptionsPanel,
            #SubtitleOptionsPanel QWidget,
            #AudioMixOptionsPanel,
            #AudioMixOptionsPanel QWidget,
            #ImageMontageOptionsPanel,
            #ImageMontageOptionsPanel QWidget,
            #SubtitleMergeOptionsPanel,
            #SubtitleMergeOptionsPanel QWidget,
            #PDFSplitOptionsPanel,
            #PDFSplitOptionsPanel QWidget,
            #PDFNumberingOptionsPanel,
            #PDFNumberingOptionsPanel QWidget,
            #SlidesToImagesOptionsPanel,
            #SlidesToImagesOptionsPanel QWidget,
            #DocumentOptionsPanel,
            #DocumentOptionsPanel QWidget,
            #QROptionsPanel,
            #QROptionsPanel QWidget,
            #SVGOptionsPanel,
            #SVGOptionsPanel QWidget,
            #EbookOptionsPanel,
            #EbookOptionsPanel QWidget,
            #MetadataOptionsPanel,
            #MetadataOptionsPanel QWidget {
                background: $BRAND_SURFACE_SOFT;
            }
            #ImageOptionsPanel QSlider::groove:horizontal,
            #PDFOperationsPanel QSlider::groove:horizontal,
            #VideoOptionsPanel QSlider::groove:horizontal,
            #AudioOptionsPanel QSlider::groove:horizontal {
                background: $BRAND_SURFACE_MUTED;
                border: 1px solid $BRAND_ACCENT;
                border-radius: 4px;
                height: 8px;
            }
            #ImageOptionsPanel QSlider::handle:horizontal,
            #PDFOperationsPanel QSlider::handle:horizontal,
            #VideoOptionsPanel QSlider::handle:horizontal,
            #AudioOptionsPanel QSlider::handle:horizontal {
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
)


def build_stylesheet() -> str:
    """Return the application QSS with brand colors and asset paths injected."""
    return _STYLESHEET.substitute(
        BRAND_ACCENT=BRAND_ACCENT,
        BRAND_DARK=BRAND_DARK,
        BRAND_DARK_SOFT=BRAND_DARK_SOFT,
        BRAND_SURFACE=BRAND_SURFACE,
        BRAND_SURFACE_MUTED=BRAND_SURFACE_MUTED,
        BRAND_SURFACE_SOFT=BRAND_SURFACE_SOFT,
        BRAND_TEXT=BRAND_TEXT,
        SPIN_UP_ICON=asset_path("spin-up.png").as_posix(),
        SPIN_DOWN_ICON=asset_path("spin-down.png").as_posix(),
    )
