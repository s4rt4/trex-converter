"""Small shared row builders used across converter pages.

Keeps the per-page code declarative: a value-based combo row, a numeric
spin row, and a file-browse suffix button — the building blocks every
operation checklist reaches for.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from gi.repository import Adw, GLib, Gtk


class ChoiceRow:
    """AdwComboRow wrapper with value-based get/set.

    ``choices`` is a sequence of ``(label, value)`` pairs; the value is
    what the page stores in its options dict.
    """

    def __init__(
        self,
        title: str,
        choices: Sequence[tuple[str, object]],
        default: object,
    ) -> None:
        self.row = Adw.ComboRow(title=title)
        self.row.set_model(Gtk.StringList.new([label for label, _ in choices]))
        self._values = [value for _, value in choices]
        self.set_value(default)

    def get_value(self) -> object:
        return self._values[self.row.get_selected()]

    def set_value(self, value: object) -> None:
        if value in self._values:
            self.row.set_selected(self._values.index(value))


def spin_row(
    title: str,
    lo: float,
    hi: float,
    default: float,
    *,
    step: float = 1,
    digits: int = 0,
) -> Adw.SpinRow:
    adjustment = Gtk.Adjustment(
        lower=lo, upper=hi, value=default,
        step_increment=step, page_increment=step * 10,
    )
    row = Adw.SpinRow(title=title, adjustment=adjustment, digits=digits)
    row.set_numeric(True)
    return row


def wire_change(control: Gtk.Widget, callback: Callable[[], None]) -> None:
    """Call ``callback`` whenever the row's value changes."""
    fire = lambda *_a: callback()
    if isinstance(control, Adw.SpinRow):
        control.get_adjustment().connect("value-changed", fire)
    elif isinstance(control, Adw.ComboRow):
        control.connect("notify::selected", fire)
    elif isinstance(control, Adw.EntryRow):
        control.connect("changed", fire)
    elif isinstance(control, Adw.SwitchRow):
        control.connect("notify::active", fire)


def attach_file_browse(
    entry: Adw.EntryRow,
    get_root: Callable[[], Gtk.Window | None],
    *,
    title: str = "Choose file",
) -> Gtk.Button:
    """Add a flat 'Browse' suffix that fills ``entry`` with a chosen path."""
    button = Gtk.Button(label="Browse")
    button.add_css_class("flat")
    button.set_valign(Gtk.Align.CENTER)

    def on_click(_button) -> None:
        dialog = Gtk.FileDialog(title=title)

        def done(dlg, result) -> None:
            try:
                gfile = dlg.open_finish(result)
            except GLib.Error:
                return
            if gfile and gfile.get_path():
                entry.set_text(gfile.get_path())

        dialog.open(get_root(), None, done)

    button.connect("clicked", on_click)
    entry.add_suffix(button)
    return button
