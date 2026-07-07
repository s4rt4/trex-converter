"""Footer preset controls: a dropdown plus Load / Save / Delete.

Wired to the shared on-disk preset store (:mod:`app.core.presets`), which
keys presets by page ``kind`` — the same store the Qt UI uses, so presets
saved in one interface show up in the other.
"""

from __future__ import annotations

from collections.abc import Callable

from gi.repository import Adw, Gtk

from app.core import presets

_PLACEHOLDER = "No presets"


class PresetBar(Gtk.Box):
    def __init__(
        self,
        *,
        kind: str,
        get_options: Callable[[], dict],
        apply_options: Callable[[dict], None],
        toast: Callable[[str], None],
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._kind = kind
        self._get_options = get_options
        self._apply_options = apply_options
        self._toast = toast
        self._names: list[str] = []

        self._dropdown = Gtk.DropDown.new_from_strings([_PLACEHOLDER])
        self._dropdown.set_valign(Gtk.Align.CENTER)
        self.append(self._dropdown)

        self._load_button = self._flat_button("Load", self._on_load)
        self.append(self._load_button)
        self.append(self._flat_button("Save", self._on_save))
        self._delete_button = self._flat_button("Delete", self._on_delete)
        self._delete_button.add_css_class("destructive-action")
        self.append(self._delete_button)

        self._refresh()

    def _flat_button(self, label: str, handler) -> Gtk.Button:
        button = Gtk.Button(label=label)
        button.add_css_class("flat")
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", handler)
        return button

    # -- store -------------------------------------------------------------

    def _refresh(self, select: str | None = None) -> None:
        self._names = presets.list_presets(self._kind)
        labels = self._names or [_PLACEHOLDER]
        self._dropdown.set_model(Gtk.StringList.new(labels))
        if select and select in self._names:
            self._dropdown.set_selected(self._names.index(select))
        has_presets = bool(self._names)
        self._load_button.set_sensitive(has_presets)
        self._delete_button.set_sensitive(has_presets)

    def _selected_name(self) -> str | None:
        if not self._names:
            return None
        index = self._dropdown.get_selected()
        if 0 <= index < len(self._names):
            return self._names[index]
        return None

    # -- actions -----------------------------------------------------------

    def _on_load(self, _button) -> None:
        name = self._selected_name()
        if name is None:
            return
        try:
            payload = presets.load_preset(self._kind, name)
        except ValueError as error:
            self._toast(str(error))
            return
        if not payload:
            self._toast("Could not read that preset.")
            return
        self._apply_options(payload)
        self._toast(f"Loaded preset “{name}”")

    def _on_save(self, _button) -> None:
        dialog = Adw.AlertDialog(
            heading="Save preset", body="Name this preset."
        )
        entry = Gtk.Entry(placeholder_text="My preset", activates_default=True)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_save_response, entry)
        dialog.present(self.get_root())

    def _on_save_response(self, _dialog, response: str, entry: Gtk.Entry) -> None:
        if response != "save":
            return
        name = entry.get_text().strip()
        if not name:
            return
        try:
            presets.save_preset(self._kind, name, self._get_options())
        except ValueError as error:
            self._toast(str(error))
            return
        self._refresh(select=name)
        self._toast(f"Saved preset “{name}”")

    def _on_delete(self, _button) -> None:
        name = self._selected_name()
        if name is None:
            return
        dialog = Adw.AlertDialog(
            heading="Delete preset?",
            body=f"“{name}” will be removed permanently.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance(
            "delete", Adw.ResponseAppearance.DESTRUCTIVE
        )
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_delete_response, name)
        dialog.present(self.get_root())

    def _on_delete_response(self, _dialog, response: str, name: str) -> None:
        if response != "delete":
            return
        try:
            deleted = presets.delete_preset(self._kind, name)
        except ValueError as error:
            self._toast(str(error))
            return
        if deleted:
            self._refresh()
            self._toast(f"Deleted preset “{name}”")
