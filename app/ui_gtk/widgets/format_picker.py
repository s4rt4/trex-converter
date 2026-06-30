"""Single-select output-format picker: common chips + overflow.

The mockup uses segmented chips. For converters with many formats
(Image has 12) we show the most common ones as chips plus a "More…"
button whose popover holds the rest — chips stay scannable without
wrapping into several rows. Selection is single across both.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from gi.repository import Adw, Gtk

# How many formats to show as chips when no explicit `common` list is given.
DEFAULT_CHIP_COUNT = 5


class FormatPicker:
    """Holds a row widget (``.row``) plus get/set for the chosen format.

    ``formats`` are lowercase extensions; the selected value is returned
    in that same lowercase form. ``common`` (optional) chooses which
    formats become chips — the rest go under "More…".
    """

    def __init__(
        self,
        formats: Sequence[str],
        *,
        common: Sequence[str] | None = None,
        default: str | None = None,
        title: str = "Format",
        uppercase: bool = True,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._all = [f.lower() for f in formats]
        self._uppercase = uppercase
        self._on_change = on_change
        self._selected = (default or self._all[0]).lower()

        if common is not None:
            chips = [f.lower() for f in common if f.lower() in self._all]
        else:
            chips = self._all[:DEFAULT_CHIP_COUNT]
        # Make sure the default is reachable as a chip if it would otherwise
        # be buried in the overflow on first paint.
        self._chip_formats = chips
        self._overflow = [f for f in self._all if f not in chips]

        self.row = Adw.ActionRow(title=title)
        self.row.set_activatable(False)

        box = Gtk.Box(spacing=0)
        box.add_css_class("linked")
        box.add_css_class("format-chips")
        box.set_valign(Gtk.Align.CENTER)

        self._chips: dict[str, Gtk.ToggleButton] = {}
        for fmt in self._chip_formats:
            button = Gtk.ToggleButton(label=self._label(fmt))
            button.connect("clicked", self._on_chip_clicked, fmt)
            self._chips[fmt] = button
            box.append(button)

        self._more: Gtk.MenuButton | None = None
        if self._overflow:
            self._more = Gtk.MenuButton(label="More")
            self._more.set_popover(self._build_overflow_popover())
            box.append(self._more)

        self.row.add_suffix(box)
        self._sync()

    # -- overflow popover --------------------------------------------------

    def _build_overflow_popover(self) -> Gtk.Popover:
        # Plain flat buttons: each sizes to its label, so format names
        # never collapse into one-letter-per-line columns.
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_margin_start(4)
        box.set_margin_end(4)
        for fmt in self._overflow:
            button = Gtk.Button(label=self._label(fmt))
            button.add_css_class("flat")
            button.set_halign(Gtk.Align.FILL)
            label = button.get_child()
            if isinstance(label, Gtk.Label):
                label.set_xalign(0.0)
            button.connect("clicked", self._on_overflow_clicked, fmt)
            box.append(button)

        popover = Gtk.Popover()
        popover.set_child(box)
        return popover

    def _on_overflow_clicked(self, _button, fmt: str) -> None:
        self._select(fmt)
        if self._more is not None and self._more.get_popover() is not None:
            self._more.get_popover().popdown()

    # -- selection ---------------------------------------------------------

    def _on_chip_clicked(self, _button, fmt: str) -> None:
        self._select(fmt)

    def _select(self, fmt: str) -> None:
        if fmt == self._selected:
            self._sync()  # keep the active chip from toggling itself off
            return
        self._selected = fmt
        self._sync()
        if self._on_change is not None:
            self._on_change(fmt)

    def _sync(self) -> None:
        for fmt, button in self._chips.items():
            button.set_active(fmt == self._selected)
        if self._more is not None:
            if self._selected in self._overflow:
                self._more.set_label(self._label(self._selected))
                self._more.add_css_class("overflow-selected")
            else:
                self._more.set_label("More")
                self._more.remove_css_class("overflow-selected")

    def _label(self, fmt: str) -> str:
        return fmt.upper() if self._uppercase else fmt

    # -- value -------------------------------------------------------------

    def get_format(self) -> str:
        return self._selected

    def set_format(self, fmt: str) -> None:
        fmt = fmt.lower()
        if fmt in self._all:
            self._select(fmt)
