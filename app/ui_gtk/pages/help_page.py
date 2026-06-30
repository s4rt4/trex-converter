"""In-app documentation, presented as a dialog from the header Help button.

A bilingual (English / Bahasa) docs browser: a topic list on the left, the
rendered topic on the right, and a language toggle in the header. Topic
content is the same bundled markdown the old Qt help page used
(:mod:`app.docs.loader`).

The bundled docs use a small markdown subset — ATX headings, ``**bold**``,
inline ```code```, and ordered / unordered lists — so they're rendered to
native widgets with Pango markup (:func:`render_markdown`) rather than
pulling in a markdown library or a WebKit view.
"""

from __future__ import annotations

import re

from gi.repository import Adw, GLib, Gtk, Pango

from app.docs.loader import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    list_topics,
    load_topic,
)

LANGUAGES: tuple[tuple[str, str], ...] = (("id", "Bahasa"), ("en", "English"))


class HelpDialog(Adw.Dialog):
    def __init__(self) -> None:
        super().__init__()
        self.set_title("Documentation")
        self.set_content_width(920)
        self.set_content_height(640)

        self._language = DEFAULT_LANGUAGE
        self._current_slug = "_index"
        self._rows: list[Gtk.ListBoxRow] = []

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(self._build_language_toggle())
        toolbar.add_top_bar(header)

        split = Adw.OverlaySplitView()
        split.set_min_sidebar_width(220)
        split.set_max_sidebar_width(280)
        split.set_sidebar(self._build_sidebar())
        split.set_content(self._build_content())
        toolbar.set_content(split)

        self.set_child(toolbar)
        self._reload_topics()
        self.show_topic(self._current_slug)

    # -- header language toggle -------------------------------------------

    def _build_language_toggle(self) -> Gtk.Widget:
        box = Gtk.Box(spacing=0)
        box.add_css_class("linked")
        self._lang_buttons: dict[str, Gtk.ToggleButton] = {}
        first: Gtk.ToggleButton | None = None
        for code, label in LANGUAGES:
            button = Gtk.ToggleButton(label=label)
            if first is None:
                first = button
            else:
                button.set_group(first)
            button.set_active(code == self._language)
            button.connect("toggled", self._on_language_toggled, code)
            self._lang_buttons[code] = button
            box.append(button)
        return box

    def _on_language_toggled(self, button: Gtk.ToggleButton, code: str) -> None:
        if not button.get_active() or code == self._language:
            return
        if code not in SUPPORTED_LANGUAGES:
            return
        self._language = code
        self._reload_topics()
        self.show_topic(self._current_slug)

    # -- sidebar (topic list) ---------------------------------------------

    def _build_sidebar(self) -> Adw.NavigationPage:
        self._search = Gtk.SearchEntry()
        self._search.set_placeholder_text("Filter topics")
        self._search.connect("search-changed", lambda _e: self._listbox.invalidate_filter())

        self._listbox = Gtk.ListBox()
        self._listbox.add_css_class("navigation-sidebar")
        self._listbox.set_filter_func(self._filter_row)
        self._listbox.connect("row-selected", self._on_row_selected)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_child(self._listbox)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        search_wrap = Gtk.Box()
        search_wrap.set_margin_top(6)
        search_wrap.set_margin_bottom(6)
        search_wrap.set_margin_start(6)
        search_wrap.set_margin_end(6)
        self._search.set_hexpand(True)
        search_wrap.append(self._search)
        box.append(search_wrap)
        box.append(scrolled)

        toolbar = Adw.ToolbarView()
        toolbar.set_content(box)
        return Adw.NavigationPage(title="Topics", child=toolbar)

    def _filter_row(self, row: Gtk.ListBoxRow) -> bool:
        text = self._search.get_text().strip().lower()
        if not text:
            return True
        return text in row.get_title().lower() if hasattr(row, "get_title") else True

    def _reload_topics(self) -> None:
        child = self._listbox.get_first_child()
        while child is not None:
            self._listbox.remove(child)
            child = self._listbox.get_first_child()
        self._rows = []
        for topic in list_topics(self._language):
            row = Adw.ActionRow(title=topic.title)
            row.slug = topic.slug  # type: ignore[attr-defined]
            self._listbox.append(row)
            self._rows.append(row)
            if topic.slug == self._current_slug:
                self._listbox.select_row(row)

    def _on_row_selected(self, _listbox, row: Gtk.ListBoxRow | None) -> None:
        if row is not None and hasattr(row, "slug"):
            self.show_topic(row.slug)

    # -- content -----------------------------------------------------------

    def _build_content(self) -> Adw.NavigationPage:
        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._content_box.set_margin_top(24)
        self._content_box.set_margin_bottom(24)
        self._content_box.set_margin_start(24)
        self._content_box.set_margin_end(24)

        clamp = Adw.Clamp(maximum_size=720)
        clamp.set_child(self._content_box)

        self._content_scroll = Gtk.ScrolledWindow()
        self._content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._content_scroll.set_vexpand(True)
        self._content_scroll.set_child(clamp)

        toolbar = Adw.ToolbarView()
        toolbar.set_content(self._content_scroll)
        return Adw.NavigationPage(title="Documentation", child=toolbar)

    def show_topic(self, slug: str) -> None:
        self._current_slug = slug
        try:
            text = load_topic(slug, self._language)
        except FileNotFoundError:
            text = f"# {slug}\n\nTopic is missing."

        child = self._content_box.get_first_child()
        while child is not None:
            self._content_box.remove(child)
            child = self._content_box.get_first_child()
        for block in render_markdown(text):
            self._content_box.append(block)

        # Scroll back to the top for the new topic.
        adjustment = self._content_scroll.get_vadjustment()
        if adjustment is not None:
            adjustment.set_value(adjustment.get_lower())


def present_help(window) -> None:
    HelpDialog().present(window)


# ---- markdown → widgets ----------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")
_ORDERED_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
_HEADING_SIZES = {1: "title-1", 2: "title-2", 3: "title-3", 4: "title-4"}


def render_markdown(text: str) -> list[Gtk.Widget]:
    """Render a markdown subset into a list of block widgets."""
    widgets: list[Gtk.Widget] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            widgets.append(_paragraph(" ".join(paragraph)))
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            widgets.append(_list_block(list_items))
            list_items.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            flush_list()
            widgets.append(_heading(len(heading.group(1)), heading.group(2)))
            continue

        bullet = _BULLET_RE.match(line)
        ordered = _ORDERED_RE.match(line)
        if bullet or ordered:
            flush_paragraph()
            if bullet:
                indent = len(bullet.group(1))
                marker = "•"
                body = bullet.group(2)
            else:
                indent = len(ordered.group(1))
                marker = f"{ordered.group(2)}."
                body = ordered.group(3)
            list_items.append(f"{indent}\x00{marker}\x00{body}")
            continue

        flush_list()
        paragraph.append(line.strip())

    flush_paragraph()
    flush_list()
    return widgets


def _heading(level: int, body: str) -> Gtk.Label:
    label = Gtk.Label(xalign=0.0)
    label.set_wrap(True)
    label.set_markup(_inline(body))
    label.add_css_class(_HEADING_SIZES.get(level, "title-4"))
    label.set_margin_top(6)
    return label


def _paragraph(body: str) -> Gtk.Label:
    label = Gtk.Label(xalign=0.0)
    label.set_wrap(True)
    label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    label.set_markup(_inline(body))
    label.set_selectable(True)
    return label


def _list_block(items: list[str]) -> Gtk.Widget:
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    for item in items:
        indent_str, marker, body = item.split("\x00", 2)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_start(8 + int(indent_str) * 2)

        bullet = Gtk.Label(xalign=0.0)
        bullet.set_markup(GLib.markup_escape_text(marker))
        bullet.add_css_class("dim-label")
        bullet.set_valign(Gtk.Align.START)
        row.append(bullet)

        content = Gtk.Label(xalign=0.0)
        content.set_wrap(True)
        content.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        content.set_markup(_inline(body))
        content.set_hexpand(True)
        content.set_selectable(True)
        row.append(content)
        box.append(row)
    return box


_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")


def _inline(text: str) -> str:
    """Convert inline markdown to Pango markup (escaping literal text)."""
    escaped = GLib.markup_escape_text(text)
    escaped = _CODE_RE.sub(lambda m: f"<tt>{m.group(1)}</tt>", escaped)
    escaped = _BOLD_RE.sub(lambda m: f"<b>{m.group(1)}</b>", escaped)
    escaped = _ITALIC_RE.sub(lambda m: f"<i>{m.group(1)}</i>", escaped)
    return escaped
