from __future__ import annotations

try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    QLabel = QVBoxLayout = QWidget = None


class PresetPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Preset management will be enabled in a later milestone."))
