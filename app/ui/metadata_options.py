from __future__ import annotations

try:
    from PySide6.QtWidgets import (
        QComboBox,
        QGridLayout,
        QLabel,
        QLineEdit,
        QListView,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QComboBox = QGridLayout = QLabel = QLineEdit = QListView = QVBoxLayout = QWidget = None


METADATA_OPERATIONS = (
    ("Strip all metadata (write to copy)", "strip"),
    ("Edit selected fields (write to copy)", "edit"),
    ("Read metadata → output file", "read"),
)

READ_FORMATS = (
    ("JSON (machine-readable)", "json"),
    ("Plain text (human-readable)", "text"),
)


class MetadataOptionsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetadataOptionsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self.operation_combo = _combo(self, METADATA_OPERATIONS)
        self.operation_combo.currentIndexChanged.connect(self._toggle_inputs)

        self.read_format_combo = _combo(self, READ_FORMATS)

        self.title_input = QLineEdit(self)
        self.artist_input = QLineEdit(self)
        self.author_input = QLineEdit(self)
        self.subject_input = QLineEdit(self)
        self.description_input = QLineEdit(self)
        self.comment_input = QLineEdit(self)
        self.copyright_input = QLineEdit(self)
        self.keywords_input = QLineEdit(self)

        info = QLabel(
            "Strip removes every tag exiftool can see. Edit writes only the "
            "fields below (empty fields are left untouched). Read dumps the "
            "metadata into the chosen output file (txt). Cross-cut: works on "
            "image / audio / video / pdf via the same exiftool tag names.",
            self,
        )
        info.setWordWrap(True)

        grid.addWidget(_field("Operation", self), 0, 0)
        grid.addWidget(self.operation_combo, 0, 1, 1, 3)
        grid.addWidget(_field("Read format", self), 1, 0)
        grid.addWidget(self.read_format_combo, 1, 1, 1, 3)
        grid.addWidget(_field("Title", self), 2, 0)
        grid.addWidget(self.title_input, 2, 1)
        grid.addWidget(_field("Artist", self), 2, 2)
        grid.addWidget(self.artist_input, 2, 3)
        grid.addWidget(_field("Author", self), 3, 0)
        grid.addWidget(self.author_input, 3, 1)
        grid.addWidget(_field("Subject", self), 3, 2)
        grid.addWidget(self.subject_input, 3, 3)
        grid.addWidget(_field("Description", self), 4, 0)
        grid.addWidget(self.description_input, 4, 1, 1, 3)
        grid.addWidget(_field("Comment", self), 5, 0)
        grid.addWidget(self.comment_input, 5, 1, 1, 3)
        grid.addWidget(_field("Copyright", self), 6, 0)
        grid.addWidget(self.copyright_input, 6, 1)
        grid.addWidget(_field("Keywords", self), 6, 2)
        grid.addWidget(self.keywords_input, 6, 3)

        layout.addLayout(grid)
        layout.addWidget(info)
        layout.addStretch(1)
        self._toggle_inputs(self.operation_combo.currentIndex())

    def _toggle_inputs(self, _index: int) -> None:
        op = self.operation_combo.currentData()
        edit_enabled = op == "edit"
        for widget in (
            self.title_input, self.artist_input, self.author_input,
            self.subject_input, self.description_input, self.comment_input,
            self.copyright_input, self.keywords_input,
        ):
            widget.setEnabled(edit_enabled)
        self.read_format_combo.setEnabled(op == "read")

    def collect_options(self) -> dict:
        op = self.operation_combo.currentData() or "strip"
        options: dict[str, object] = {"operation": op}
        if op == "read":
            fmt = self.read_format_combo.currentData() or "json"
            options["metadata_format"] = fmt
            return options
        if op != "edit":
            return options
        pairs = (
            ("metadata_title", self.title_input),
            ("metadata_artist", self.artist_input),
            ("metadata_author", self.author_input),
            ("metadata_subject", self.subject_input),
            ("metadata_description", self.description_input),
            ("metadata_comment", self.comment_input),
            ("metadata_copyright", self.copyright_input),
            ("metadata_keywords", self.keywords_input),
        )
        for key, widget in pairs:
            value = widget.text().strip()
            if value:
                options[key] = value
        return options


def _combo(parent: QWidget, items: tuple[tuple[str, object], ...]) -> QComboBox:
    combo = QComboBox(parent)
    combo.setView(QListView(combo))
    for label, value in items:
        combo.addItem(label, value)
    return combo


def _field(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    return label
