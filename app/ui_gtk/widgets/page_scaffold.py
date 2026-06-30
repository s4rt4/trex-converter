"""Standard converter-page scaffold.

A clamped, scrollable ``AdwPreferencesPage`` for the content groups plus a
footer ``GtkActionBar``: preset controls on the left, the primary actions
(Add to queue / Convert) on the right. Every converter page is built on
top of this so the layout and the single suggested action are consistent
(house style §6, §7.7).
"""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, Gtk


class PageScaffold(Gtk.Box):
    def __init__(
        self,
        *,
        on_convert: Callable[[], None],
        on_add_to_queue: Callable[[], None],
        preset_bar: Gtk.Widget | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.page = Adw.PreferencesPage()
        self.page.set_vexpand(True)
        self.append(self.page)

        bar = Gtk.ActionBar()
        if preset_bar is not None:
            bar.pack_start(preset_bar)

        convert = Gtk.Button(label="Convert")
        convert.add_css_class("suggested-action")
        convert.add_css_class("pill")
        convert.connect("clicked", lambda _b: on_convert())

        add = Gtk.Button(label="Add to queue")
        add.add_css_class("pill")
        add.connect("clicked", lambda _b: on_add_to_queue())

        bar.pack_end(convert)
        bar.pack_end(add)
        self.append(bar)

    def add_group(self, group: Adw.PreferencesGroup) -> None:
        self.page.add(group)
