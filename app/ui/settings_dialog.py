from __future__ import annotations

try:
    from PySide6.QtWidgets import QDialog, QFormLayout, QSpinBox
except ImportError:  # pragma: no cover
    QDialog = QFormLayout = QSpinBox = None


class SettingsDialog(QDialog):
    def __init__(self, max_concurrency: int = 2, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QFormLayout(self)
        self.concurrency = QSpinBox(self)
        self.concurrency.setRange(1, 16)
        self.concurrency.setValue(max_concurrency)
        layout.addRow("Concurrent tasks", self.concurrency)
