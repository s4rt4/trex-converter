"""In-app documentation page.

Topic content is bundled markdown loaded via app.docs.loader. The sidebar
swaps to a docs-mode list while this page is active (handled in MainWindow).

Search uses a QCompleter populated with "Topic — Section" rows so the
dropdown supports keyword matching and click-through navigation.
"""

from __future__ import annotations

from collections.abc import Callable

from app.docs.loader import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    TopicMeta,
    list_topics,
    load_topic,
)

try:
    from PySide6.QtCore import QStringListModel, Qt, QUrl, Signal
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QButtonGroup,
        QCompleter,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QPushButton,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    Qt = QStringListModel = QUrl = Signal = QDesktopServices = None
    QButtonGroup = QCompleter = QFrame = QHBoxLayout = QLabel = QLineEdit = QListView = QPushButton = QTextBrowser = QVBoxLayout = QWidget = None


class HelpPage(QWidget):
    """Right-pane help renderer with language toggle + search."""

    topic_changed = Signal(str)  # emits slug whenever current topic changes

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HelpPage")

        self._language = DEFAULT_LANGUAGE
        self._topics: list[TopicMeta] = []
        self._current_slug: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Need Help ?", self)
        title.setObjectName("PageTitle")
        root.addWidget(title)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        # Language toggle (segmented).
        self._lang_group = QButtonGroup(self)
        self._lang_group.setExclusive(True)
        self._lang_buttons: dict[str, QPushButton] = {}
        for code, label in (("id", "Bahasa"), ("en", "English")):
            button = QPushButton(label, self)
            button.setObjectName("HelpLanguageButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, c=code: self.set_language(c))
            controls.addWidget(button)
            self._lang_group.addButton(button)
            self._lang_buttons[code] = button

        controls.addSpacing(12)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText(
            "Cari topik atau bagian — ketik untuk lihat saran"
        )
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setObjectName("HelpSearch")
        controls.addWidget(self._search_input, 1)

        root.addLayout(controls)

        body = QFrame(self)
        body.setObjectName("HelpBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._browser = QTextBrowser(body)
        self._browser.setObjectName("HelpBrowser")
        self._browser.setOpenLinks(False)
        self._browser.anchorClicked.connect(self._on_anchor_clicked)
        body_layout.addWidget(self._browser, 1)
        root.addWidget(body, 1)

        # Search completer wires up to the line edit. Keep the setup minimal
        # so QCompleter manages its own popup as a top-level window — passing
        # a custom popup with `self` as the parent bound it inside the page
        # widget and effectively hid the suggestion list.
        self._search_model = QStringListModel(self)
        self._search_completer = QCompleter(self._search_model, self)
        self._search_completer.setCompletionMode(
            QCompleter.CompletionMode.PopupCompletion
        )
        self._search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._search_completer.setMaxVisibleItems(12)
        self._search_input.setCompleter(self._search_completer)
        self._search_completer.activated.connect(self._on_search_activated)
        # Style the auto-created popup once it exists.
        popup = self._search_completer.popup()
        if popup is not None:
            popup.setObjectName("HelpSearchPopup")

        # Initial state: load default language and welcome topic.
        self.set_language(self._language, refresh=False)
        self.show_topic("_index")
        self._lang_buttons[self._language].setChecked(True)

    # ---- Public API ------------------------------------------------------

    def topic_metas(self) -> list[TopicMeta]:
        return list(self._topics)

    def current_language(self) -> str:
        return self._language

    def show_topic(self, slug: str, *, anchor: str | None = None) -> None:
        try:
            text = load_topic(slug, self._language)
        except FileNotFoundError:
            text = f"# {slug}\n\nTopic markdown is missing."
        self._current_slug = slug
        self._browser.setMarkdown(text)
        if anchor:
            self._browser.scrollToAnchor(anchor)
        else:
            self._browser.verticalScrollBar().setValue(0)
        self.topic_changed.emit(slug)

    def set_language(self, code: str, *, refresh: bool = True) -> None:
        if code not in SUPPORTED_LANGUAGES:
            return
        self._language = code
        for lang_code, button in self._lang_buttons.items():
            button.setChecked(lang_code == code)
        self._reload_topics()
        if code == "id":
            self._search_input.setPlaceholderText(
                "Cari topik atau bagian — ketik untuk lihat saran"
            )
        else:
            self._search_input.setPlaceholderText(
                "Search topics or sections — start typing to see suggestions"
            )
        if refresh and self._current_slug:
            self.show_topic(self._current_slug)

    # ---- Internal --------------------------------------------------------

    def _reload_topics(self) -> None:
        self._topics = list_topics(self._language)
        entries: list[str] = []
        for topic in self._topics:
            entries.append(_format_search_entry(topic.slug, topic.title, ""))
            for section in topic.sections:
                entries.append(
                    _format_search_entry(topic.slug, topic.title, section.title)
                )
        self._search_model.setStringList(entries)

    def _on_search_activated(self, value) -> None:
        # PySide6's QCompleter.activated has both QString and QModelIndex
        # overloads. Accept either; resolve the index back to its display text.
        if isinstance(value, str):
            text = value
        else:
            text = value.data() if hasattr(value, "data") else str(value)
        slug, anchor = _parse_search_entry(text)
        if not slug:
            return
        self.show_topic(slug, anchor=anchor)
        self._search_input.clear()

    def _on_anchor_clicked(self, url: "QUrl") -> None:
        if url.scheme() == "topic":
            slug = url.host() or url.path().lstrip("/")
            anchor = url.fragment() or None
            self.show_topic(slug, anchor=anchor)
            return
        if url.scheme() in ("http", "https"):
            QDesktopServices.openUrl(url)
            return
        # In-page anchor (#section-slug)
        if url.scheme() == "" and url.fragment():
            self._browser.scrollToAnchor(url.fragment())
            return


# ---- Search entry encoding -------------------------------------------------
#
# We pack (slug, anchor) into the visible search-entry string so the
# QCompleter can stay a plain QStringListModel without a custom delegate. The
# trailing " ⟨slug#anchor⟩" suffix is ignored visually but the parser slices
# it back on activation.

_ENTRY_OPEN = "  ("
_ENTRY_CLOSE = ")"


def _format_search_entry(slug: str, title: str, section: str) -> str:
    if section:
        label = f"{title} > {section}"
        anchor = _slugify_for_anchor(section)
    else:
        label = title
        anchor = ""
    return f"{label}{_ENTRY_OPEN}{slug}#{anchor}{_ENTRY_CLOSE}"


def _parse_search_entry(text: str) -> tuple[str, str | None]:
    if _ENTRY_OPEN not in text or not text.endswith(_ENTRY_CLOSE):
        return "", None
    payload = text.split(_ENTRY_OPEN, 1)[1].rstrip(_ENTRY_CLOSE)
    if "#" not in payload:
        return payload, None
    slug, anchor = payload.split("#", 1)
    return slug, anchor or None


def _slugify_for_anchor(text: str) -> str:
    import re

    text = text.strip().lower()
    return re.sub(r"[^\w]+", "-", text).strip("-")
