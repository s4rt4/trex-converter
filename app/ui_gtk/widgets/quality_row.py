"""Quality control: a slider with a live value badge (mockup style).

House style §7.5 allows either a scale or a spin row; the mockup uses a
slider with an accent value pill, so that is what we build. The
``on_change`` callback lets a page recompute things like an output-size
estimate as the user drags.
"""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, Gtk


class QualityRow:
    def __init__(
        self,
        *,
        title: str = "Quality",
        minimum: int = 1,
        maximum: int = 100,
        default: int = 85,
        on_change: Callable[[int], None] | None = None,
    ) -> None:
        self._on_change = on_change

        self.row = Adw.ActionRow(title=title)
        self.row.set_activatable(False)

        self._scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, minimum, maximum, 1
        )
        self._scale.set_value(default)
        self._scale.set_draw_value(False)
        self._scale.set_hexpand(True)
        self._scale.set_size_request(160, -1)
        self._scale.set_valign(Gtk.Align.CENTER)
        self._scale.connect("value-changed", self._on_scale_changed)

        self._badge = Gtk.Label(label=str(default))
        self._badge.add_css_class("value-badge")
        self._badge.add_css_class("numeric")
        self._badge.set_valign(Gtk.Align.CENTER)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_hexpand(True)
        box.append(self._scale)
        box.append(self._badge)
        self.row.add_suffix(box)

    def _on_scale_changed(self, scale: Gtk.Scale) -> None:
        value = int(scale.get_value())
        self._badge.set_label(str(value))
        if self._on_change is not None:
            self._on_change(value)

    def get_value(self) -> int:
        return int(self._scale.get_value())

    def set_value(self, value: int) -> None:
        self._scale.set_value(value)
