"""Operations checklist — the signature pattern (house style §7.4).

Each operation is an :class:`AdwExpanderRow` with an enable switch in its
header (off + collapsed by default), an icon, a title, and a subtitle
that shows a short description when off and an inline summary when on.
``OperationsGroup`` collects them and shows an "N active" counter.

This replaces the old tab-based options panels: every former tab becomes
one operation row whose nested rows hold that tab's controls.
"""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, Gtk

from app.ui_gtk.icons import icon_name


class OperationRow:
    def __init__(
        self,
        *,
        icon: str,
        title: str,
        description: str,
        on_toggle: Callable[[], None] | None = None,
    ) -> None:
        self._description = description
        self.on_toggle = on_toggle

        self.row = Adw.ExpanderRow()
        # Titles like "Rotate & flip" are literal text, not Pango markup —
        # disable markup before setting the title so "&" needs no escaping.
        self.row.set_use_markup(False)
        self.row.set_title(title)
        self.row.set_subtitle(description)
        self.row.set_show_enable_switch(True)
        self.row.set_enable_expansion(False)

        image = Gtk.Image.new_from_icon_name(icon_name(icon))
        self.row.add_prefix(image)

        self.row.connect("notify::enable-expansion", self._on_enable_changed)

    def add(self, widget: Gtk.Widget) -> None:
        """Add a nested control row to this operation."""
        self.row.add_row(widget)

    @property
    def enabled(self) -> bool:
        return self.row.get_enable_expansion()

    def set_summary(self, summary: str | None) -> None:
        """Show an inline summary while enabled; falls back to the description."""
        self.row.set_subtitle(summary or self._description)

    def _on_enable_changed(self, *_args) -> None:
        if not self.enabled:
            self.row.set_subtitle(self._description)
        if self.on_toggle is not None:
            self.on_toggle()


class OperationsGroup:
    """A preferences group of operation rows with an "N active" counter."""

    def __init__(self, title: str = "Operations") -> None:
        self.group = Adw.PreferencesGroup(title=title)
        self._counter = Gtk.Label()
        self._counter.add_css_class("operations-count")
        self._counter.set_valign(Gtk.Align.CENTER)
        self.group.set_header_suffix(self._counter)
        self._operations: list[OperationRow] = []
        self._update_count()

    def add_operation(self, operation: OperationRow) -> None:
        previous = operation.on_toggle

        def chained() -> None:
            self._update_count()
            if previous is not None:
                previous()

        operation.on_toggle = chained
        self._operations.append(operation)
        self.group.add(operation.row)
        self._update_count()

    @property
    def active_count(self) -> int:
        return sum(1 for op in self._operations if op.enabled)

    def _update_count(self) -> None:
        count = self.active_count
        self._counter.set_label(f"{count} active" if count else "")
        self._counter.set_visible(count > 0)
