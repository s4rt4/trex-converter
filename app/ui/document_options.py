from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QGridLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QCheckBox = QGridLayout = QLabel = QVBoxLayout = QWidget = None


class DocumentOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        self.pdf_a_check = QCheckBox(
            "PDF/A-1a archival output (only applies when output is PDF)", self
        )

        info = QLabel(
            "PDF/A is the ISO archival flavor: embeds fonts, disallows audio/video, "
            "and locks the document for long-term reading. Larger file size.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(self.pdf_a_check, 0, 0)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        if self.pdf_a_check.isChecked():
            options["pdf_a"] = True
        return options
