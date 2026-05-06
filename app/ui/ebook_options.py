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


class EbookOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EbookOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Optional — empty uses input filename")
        self.author_input = QLineEdit(self)
        self.author_input.setPlaceholderText("e.g. Jane Doe")
        self.language_input = QLineEdit(self)
        self.language_input.setPlaceholderText("e.g. en, id")
        self.publisher_input = QLineEdit(self)
        self.publisher_input.setPlaceholderText("Optional")
        self.date_input = QLineEdit(self)
        self.date_input.setPlaceholderText("YYYY-MM-DD")

        self.toc_check = QCheckBox(
            "Generate table of contents (--toc)", self
        )
        self.embed_resources_check = QCheckBox(
            "Embed resources in HTML (self-contained)", self
        )

        info = QLabel(
            "Title / Author / Language go through Pandoc as --metadata. "
            "Useful especially for EPUB / DOCX / PDF output where readers "
            "show that metadata. TOC adds an auto-generated table of contents. "
            "Embed resources only applies to HTML output (inlines images/CSS).",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Title", self), 0, 0)
        grid.addWidget(self.title_input, 0, 1, 1, 3)
        grid.addWidget(_field("Author", self), 1, 0)
        grid.addWidget(self.author_input, 1, 1)
        grid.addWidget(_field("Language", self), 1, 2)
        grid.addWidget(self.language_input, 1, 3)
        grid.addWidget(_field("Publisher", self), 2, 0)
        grid.addWidget(self.publisher_input, 2, 1)
        grid.addWidget(_field("Date", self), 2, 2)
        grid.addWidget(self.date_input, 2, 3)
        grid.addWidget(self.toc_check, 3, 0, 1, 4)
        grid.addWidget(self.embed_resources_check, 4, 0, 1, 4)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)

    def collect_options(self) -> dict:
        options: dict[str, object] = {}
        title = self.title_input.text().strip()
        if title:
            options["ebook_title"] = title
        author = self.author_input.text().strip()
        if author:
            options["ebook_author"] = author
        language = self.language_input.text().strip()
        if language:
            options["ebook_language"] = language
        publisher = self.publisher_input.text().strip()
        if publisher:
            options["ebook_publisher"] = publisher
        date = self.date_input.text().strip()
        if date:
            options["ebook_date"] = date
        if self.toc_check.isChecked():
            options["pandoc_table_of_contents"] = True
        if self.embed_resources_check.isChecked():
            options["pandoc_self_contained"] = True
        return options


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label
