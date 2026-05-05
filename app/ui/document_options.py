from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QGridLayout,
        QLabel,
        QLineEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QCheckBox = QGridLayout = QLabel = QLineEdit = QVBoxLayout = QWidget = None


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
        grid.setColumnStretch(1, 1)

        self.pdf_a_check = QCheckBox(
            "PDF/A-1a archival output (only applies when output is PDF)", self
        )

        self.user_password_input = QLineEdit(self)
        self.user_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.user_password_input.setPlaceholderText(
            "Password to open the PDF (leave empty to skip)"
        )

        self.owner_password_input = QLineEdit(self)
        self.owner_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.owner_password_input.setPlaceholderText(
            "Permission password (restricts edit/copy)"
        )

        info = QLabel(
            "PDF/A is the ISO archival flavor: embeds fonts, disallows audio/video, "
            "and locks the document for long-term reading. Larger file size.\n"
            "Passwords use the LibreOffice writer_pdf_Export filter (AES-256).",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(self.pdf_a_check, 0, 0, 1, 2)
        grid.addWidget(_field("User password", self), 1, 0)
        grid.addWidget(self.user_password_input, 1, 1)
        grid.addWidget(_field("Owner password", self), 2, 0)
        grid.addWidget(self.owner_password_input, 2, 1)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        if self.pdf_a_check.isChecked():
            options["pdf_a"] = True
        user_pw = self.user_password_input.text()
        if user_pw:
            options["pdf_password_user"] = user_pw
        owner_pw = self.owner_password_input.text()
        if owner_pw:
            options["pdf_password_owner"] = owner_pw
        return options


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label
