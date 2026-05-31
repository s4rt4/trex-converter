from __future__ import annotations

from app import __version__
from app.utils.paths import asset_path

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = QPixmap = None
    QFrame = QGridLayout = QHBoxLayout = QLabel = QVBoxLayout = QWidget = None


# Engines the app dispatches to, paired with what they power. Shown so users
# know which system packages each capability needs.
ENGINES = (
    ("FFmpeg", "Video & audio convert, trim, compress, filters, GIF/WebP, contact sheets"),
    ("ImageMagick", "Image convert, resize, crop, color, filters, montage, ICO"),
    ("LibreOffice", "Documents & spreadsheets & slides ↔ DOCX/ODT/XLSX/PDF/…"),
    ("PyMuPDF + qpdf", "PDF render, extract, merge/split, encrypt, watermark, redact"),
    ("Tesseract", "OCR: image/PDF → searchable PDF / TXT / hOCR / TSV"),
    ("Pandoc", "Ebook & markup: Markdown/RST/LaTeX/HTML/DOCX/EPUB/…"),
    ("Inkscape + potrace", "SVG/vector convert and bitmap → SVG trace"),
    ("ExifTool", "Read / strip / edit media & PDF metadata"),
    ("qrencode + zbar", "QR / barcode generate and decode"),
)


class AboutPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("About", self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        root.addWidget(self._build_identity_panel())
        root.addWidget(self._build_engines_panel())
        root.addWidget(self._build_meta_panel())
        root.addStretch(1)

    def _build_identity_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("AboutPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        logo = QLabel(panel)
        logo.setObjectName("AboutLogo")
        pixmap = QPixmap(str(asset_path("trex-logo.svg")))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    78, 78,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(6)
        name = QLabel("T-Rex Converter", panel)
        name.setObjectName("AboutName")
        text.addWidget(name)

        version = QLabel(f"Version {__version__}", panel)
        version.setObjectName("AboutMeta")
        text.addWidget(version)

        description = QLabel(
            "A native Debian GUI for converting files locally across images, "
            "video, audio, documents, PDFs, ebooks, SVG/vector, archives, OCR, "
            "subtitles, QR codes, and media metadata. Every job runs on your "
            "machine — nothing is uploaded to the cloud.",
            panel,
        )
        description.setObjectName("AboutDescription")
        description.setWordWrap(True)
        text.addWidget(description)
        text.addStretch(1)

        layout.addLayout(text, 1)
        return panel

    def _build_engines_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("AboutPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        heading = QLabel("Conversion engines", panel)
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(1, 1)
        for row, (engine, powers) in enumerate(ENGINES):
            name = QLabel(engine, panel)
            name.setObjectName("EngineStatusName")
            powers_label = QLabel(powers, panel)
            powers_label.setObjectName("AboutMeta")
            powers_label.setWordWrap(True)
            grid.addWidget(name, row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(powers_label, row, 1)
        layout.addLayout(grid)
        return panel

    def _build_meta_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("AboutPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(6)
        layout.setColumnMinimumWidth(0, 150)
        layout.setColumnStretch(1, 1)

        rows = (
            ("Built with", "Python 3 · PySide6 (Qt 6) · qtawesome"),
            ("Privacy", "100% on-device — no network access, no telemetry."),
            ("Project", "https://github.com/s4rt4/trex-converter"),
            ("License", "See the repository LICENSE."),
        )
        for row, (label, value) in enumerate(rows):
            key = QLabel(label, panel)
            key.setObjectName("EngineStatusName")
            val = QLabel(value, panel)
            val.setObjectName("AboutMeta")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            val.setOpenExternalLinks(True)
            layout.addWidget(key, row, 0, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(val, row, 1)
        return panel

    def set_tasks(self, _tasks) -> None:
        return
