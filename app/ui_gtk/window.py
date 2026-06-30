"""Main application window: the GTK4 app shell.

Layout (see rewrite plan §3):

    AdwApplicationWindow
    └── AdwBreakpoint (collapse < 600sp)
        └── AdwNavigationSplitView
            ├── sidebar:  header + grouped GtkListBox of destinations
            └── content:  header (ViewSwitcher: Convert | Queue)
                          └── AdwToastOverlay
                               └── AdwViewStack
                                    ├── convert  → current destination page
                                    └── queue    → shared task queue
"""

from __future__ import annotations

from gi.repository import Adw, Gtk

from app.ui_gtk.icons import icon_name
from app.ui_gtk.navigation import (
    DASHBOARD,
    NAV_GROUPS,
    NavItem,
    find_item,
)
from app.ui_gtk.pages.audio_page import build_audio_page
from app.ui_gtk.pages.dashboard_page import build_dashboard_page
from app.ui_gtk.pages.image_page import build_image_page
from app.ui_gtk.pages.multi_input_pages import MULTI_INPUT_BUILDERS
from app.ui_gtk.pages.pdf_page import build_pdf_page
from app.ui_gtk.pages.placeholder import make_placeholder
from app.ui_gtk.pages.queue_view import QueueView
from app.ui_gtk.pages.single_input_pages import SINGLE_INPUT_BUILDERS
from app.ui_gtk.pages.video_page import build_video_page
from app.core.task import Task, TaskStatus

# Destinations with a real page. Everything else falls back to a
# placeholder until it is migrated.
_PAGE_BUILDERS = {
    "dashboard": build_dashboard_page,
    "image": build_image_page,
    "video": build_video_page,
    "audio": build_audio_page,
    "pdf": build_pdf_page,
    **MULTI_INPUT_BUILDERS,
    **SINGLE_INPUT_BUILDERS,
}


class TrexWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_title("T-Rex Converter")
        self.set_default_size(1120, 760)
        self.set_size_request(360, 480)

        # Lazily built per-destination convert pages, keyed by NavItem.id.
        self._convert_pages: dict[str, Gtk.Widget] = {}
        self._rows_by_id: dict[str, Gtk.ListBoxRow] = {}

        # Wired up by attach_queue() once the backend controller exists.
        self.queue = None
        self._dashboard = None

        self._split = Adw.NavigationSplitView()
        self._split.set_sidebar(self._build_sidebar())
        self._split.set_content(self._build_content())
        self.set_content(self._split)

        self._add_breakpoint()

        # Select the default destination once everything is wired up.
        self._select(DASHBOARD.id)

    # -- sidebar -----------------------------------------------------------

    def _build_sidebar(self) -> Adw.NavigationPage:
        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.add_css_class("navigation-sidebar")
        self._listbox.connect("row-selected", self._on_row_selected)

        self._listbox.append(self._make_item_row(DASHBOARD))
        for group in NAV_GROUPS:
            self._listbox.append(self._make_header_row(group.title))
            for item in group.items:
                self._listbox.append(self._make_item_row(item))

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self._listbox)
        scrolled.set_vexpand(True)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(scrolled)

        return Adw.NavigationPage(title="T-Rex Converter", child=toolbar)

    def _make_header_row(self, title: str) -> Gtk.ListBoxRow:
        label = Gtk.Label(label=title, xalign=0.0)
        label.add_css_class("dim-label")
        label.add_css_class("caption-heading")
        label.add_css_class("nav-group-heading")

        row = Gtk.ListBoxRow()
        row.set_selectable(False)
        row.set_activatable(False)
        row.set_child(label)
        return row

    def _make_item_row(self, item: NavItem) -> Gtk.ListBoxRow:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.append(Gtk.Image.new_from_icon_name(icon_name(item.icon)))
        box.append(Gtk.Label(label=item.title, xalign=0.0))

        row = Gtk.ListBoxRow()
        row.set_child(box)
        row._nav_id = item.id  # type: ignore[attr-defined]
        self._rows_by_id[item.id] = row
        return row

    # -- content -----------------------------------------------------------

    def _build_content(self) -> Adw.NavigationPage:
        self._stack = Adw.ViewStack()

        # Convert: a swappable holder for the selected destination's page.
        self._convert_bin = Adw.Bin()
        self._stack.add_titled_with_icon(
            self._convert_bin, "convert", "Convert", icon_name("convert")
        )

        # Queue: shared across all destinations.
        self._queue_view = QueueView(self)
        self._stack.add_titled_with_icon(
            self._queue_view.widget, "queue", "Queue", icon_name("queue")
        )

        self._toasts = Adw.ToastOverlay()
        self._toasts.set_child(self._stack)

        self._switcher = Adw.ViewSwitcher(
            stack=self._stack, policy=Adw.ViewSwitcherPolicy.WIDE
        )

        self._header = Adw.HeaderBar()
        self._header.set_title_widget(self._switcher)

        help_button = Gtk.Button(icon_name=icon_name("help"))
        help_button.set_tooltip_text("Documentation")
        help_button.connect("clicked", self._on_help_clicked)
        self._header.pack_end(self._build_primary_menu())
        self._header.pack_end(help_button)
        self._header.pack_end(self._build_theme_toggle())

        # Narrow layout: move the switcher to a bottom bar.
        self._switcher_bar = Adw.ViewSwitcherBar(stack=self._stack)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(self._header)
        toolbar.set_content(self._toasts)
        toolbar.add_bottom_bar(self._switcher_bar)

        self._content_page = Adw.NavigationPage(title="Dashboard", child=toolbar)
        return self._content_page

    def _build_primary_menu(self) -> Gtk.MenuButton:
        button = Gtk.MenuButton(icon_name=icon_name("menu"))
        button.set_tooltip_text("Main menu")
        menu = Gtk.Builder.new_from_string(_MENU_XML, -1).get_object("primary-menu")
        button.set_menu_model(menu)
        return button

    def _on_help_clicked(self, _button) -> None:
        self.show_toast("Documentation is not available yet.")

    def _build_theme_toggle(self) -> Gtk.Button:
        self._style_manager = Adw.StyleManager.get_default()
        button = Gtk.Button()
        button.set_tooltip_text("Toggle light / dark theme")
        button.connect("clicked", self._on_theme_toggle)
        self._theme_button = button
        self._style_manager.connect(
            "notify::dark", lambda *_: self._update_theme_icon()
        )
        self._update_theme_icon()
        return button

    def _update_theme_icon(self) -> None:
        # Show the icon for the theme you'd switch *to*.
        is_dark = self._style_manager.get_dark()
        self._theme_button.set_icon_name(icon_name("sun" if is_dark else "moon"))

    def _on_theme_toggle(self, _button) -> None:
        scheme = (
            Adw.ColorScheme.FORCE_LIGHT
            if self._style_manager.get_dark()
            else Adw.ColorScheme.FORCE_DARK
        )
        self._style_manager.set_color_scheme(scheme)

    def _set_converter_chrome(self, is_converter: bool) -> None:
        """Show the Convert/Queue switcher only for converter destinations.

        Non-converter pages (Dashboard, later Settings/About) have no queue
        view, so the switcher is hidden and the header shows the page title.
        """
        self._header.set_title_widget(self._switcher if is_converter else None)
        self._switcher_bar.set_visible(is_converter)

    # -- behaviour ---------------------------------------------------------

    def _add_breakpoint(self) -> None:
        condition = Adw.BreakpointCondition.parse("max-width: 600sp")
        breakpoint_ = Adw.Breakpoint.new(condition)
        breakpoint_.add_setter(self._split, "collapsed", True)
        breakpoint_.add_setter(self._switcher_bar, "reveal", True)
        self.add_breakpoint(breakpoint_)

    def _on_row_selected(
        self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None
    ) -> None:
        if row is None:
            return
        item_id = getattr(row, "_nav_id", None)
        if item_id is None:
            return
        self._show_destination(item_id)

    def _select(self, item_id: str) -> None:
        row = self._rows_by_id.get(item_id)
        if row is not None:
            self._listbox.select_row(row)

    def _show_destination(self, item_id: str) -> None:
        item = find_item(item_id)
        if item is None:
            return
        page = self._convert_pages.get(item_id)
        if page is None:
            builder = _PAGE_BUILDERS.get(item_id)
            page = builder(self) if builder is not None else make_placeholder(item)
            self._convert_pages[item_id] = page
        self._convert_bin.set_child(page)
        self._content_page.set_title(item.title)
        self._set_converter_chrome(item_id != DASHBOARD.id)
        self._stack.set_visible_child_name("convert")
        # On a collapsed split view, drill into the content pane.
        if self._split.get_collapsed():
            self._split.set_show_content(True)

    def show_toast(self, text: str) -> None:
        self._toasts.add_toast(Adw.Toast.new(text))

    # -- queue / backend ---------------------------------------------------

    def attach_queue(self, controller) -> None:
        """Connect the backend queue controller and show any existing tasks."""
        self.queue = controller
        self.on_tasks_changed(controller.snapshot())

    def register_dashboard(self, dashboard) -> None:
        """Let the dashboard receive live task counts."""
        self._dashboard = dashboard
        if self.queue is not None:
            self.on_tasks_changed(self.queue.snapshot())

    def on_tasks_changed(self, tasks: list[Task]) -> None:
        """Called on the GTK main thread when the task set changes."""
        self._queue_view.set_tasks(tasks)
        if self._dashboard is not None:
            self._dashboard.set_counts(
                total=len(tasks),
                running=sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
                success=sum(1 for t in tasks if t.status == TaskStatus.SUCCESS),
                failed=sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            )

    def enqueue(
        self,
        kind: str,
        primary,
        *,
        extra_inputs=(),
        output_dir=None,
        format_out=None,
        options=None,
        switch_to_queue: bool = False,
    ) -> bool:
        """Build a task from a page's selections and submit it to the queue."""
        if self.queue is None:
            self.show_toast("The conversion engine is not available.")
            return False
        from app.ui_gtk.backend import build_task

        task = build_task(
            kind, primary, extra_inputs=extra_inputs,
            output_dir=output_dir, format_out=format_out, options=options,
        )
        self.queue.submit(task)
        self.show_toast("Added to the queue.")
        if switch_to_queue:
            self._stack.set_visible_child_name("queue")
        return True


_MENU_XML = """
<interface>
  <menu id="primary-menu">
    <section>
      <item>
        <attribute name="label" translatable="yes">Settings</attribute>
        <attribute name="action">app.settings</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">About T-Rex Converter</attribute>
        <attribute name="action">app.about</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="label" translatable="yes">Quit</attribute>
        <attribute name="action">app.quit</attribute>
      </item>
    </section>
  </menu>
</interface>
"""
