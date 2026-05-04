from __future__ import annotations

from app.utils.paths import asset_path

try:
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QPixmap = None
    QFrame = QHBoxLayout = QLabel = QVBoxLayout = QWidget = None


class AboutPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("About", self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        panel = QFrame(self)
        panel.setObjectName("AboutPanel")
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(16)

        logo = QLabel(panel)
        logo.setObjectName("AboutLogo")
        pixmap = QPixmap(str(asset_path("trex-logo.svg")))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(72, 72))
        panel_layout.addWidget(logo)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        name = QLabel("T-Rex Converter", panel)
        name.setObjectName("AboutName")
        text_layout.addWidget(name)

        version = QLabel("Version 0.3.0", panel)
        version.setObjectName("AboutMeta")
        text_layout.addWidget(version)

        description = QLabel(
            "Native Debian file converter for local image, video, document, and PDF workflows.",
            panel,
        )
        description.setObjectName("AboutDescription")
        description.setWordWrap(True)
        text_layout.addWidget(description)
        text_layout.addStretch(1)

        panel_layout.addLayout(text_layout, 1)
        root.addWidget(panel)
        root.addStretch(1)

    def set_tasks(self, _tasks) -> None:
        return
