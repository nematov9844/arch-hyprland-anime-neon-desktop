#!/usr/bin/env python3
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from services.locale_service import t
from views.appearance import AppearancePage
from views.bars import BarsPage
from views.dashboard import DashboardPage
from views.language import LanguagePage
from views.media_paths import MediaPathsPage
from views.providers import ProvidersPage
from views.system import SystemPage
from views.wallpapers import WallpapersPage


APP_ID = "com.nematov.archhypr.SettingsCenter"


class SettingsCenterWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app)
        self.set_default_size(1180, 760)
        self.rebuild_ui("dashboard")

    def rebuild_ui(self, active_key: str | None = None) -> None:
        self.set_title(t("app.title", "Settings Center"))
        split = Adw.NavigationSplitView()
        split.set_min_sidebar_width(220)
        split.set_max_sidebar_width(260)

        sidebar_page = Adw.NavigationPage(title=t("app.sections", "Sections"))
        content_page = Adw.NavigationPage(title=t("app.content", "Content"))
        split.set_sidebar(sidebar_page)
        split.set_content(content_page)

        self.sidebar_list = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.connect("row-selected", self.on_row_selected)

        sections = [
            (t("sidebar.dashboard", "Dashboard"), "dashboard"),
            (t("sidebar.wallpapers", "Wallpapers"), "wallpapers"),
            (t("sidebar.providers", "Providers"), "providers"),
            (t("sidebar.media_paths", "Media Paths"), "media_paths"),
            (t("sidebar.appearance", "Appearance"), "appearance"),
            (t("sidebar.bars", "Bars & Dock"), "bars"),
            (t("sidebar.system", "System"), "system"),
            (t("sidebar.developer", "Developer"), "developer"),
            (t("sidebar.plugins", "Plugins"), "plugins"),
            (t("sidebar.language", "Language"), "language"),
        ]

        self.rows = {}
        for title, key in sections:
            row = Gtk.ListBoxRow()
            row.key = key  # type: ignore[attr-defined]
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(12)
            box.set_margin_end(12)
            label = Gtk.Label(label=title, xalign=0)
            box.append(label)
            row.set_child(box)
            self.sidebar_list.append(row)
            self.rows[key] = row

        sidebar_scroller = Gtk.ScrolledWindow()
        sidebar_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroller.set_size_request(240, -1)
        sidebar_scroller.set_child(self.sidebar_list)
        sidebar_page.set_child(sidebar_scroller)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(220)
        self.stack.add_named(DashboardPage(), "dashboard")
        self.stack.add_named(WallpapersPage(on_navigate=self.navigate_to), "wallpapers")
        self.stack.add_named(ProvidersPage(), "providers")
        self.stack.add_named(MediaPathsPage(), "media_paths")
        self.stack.add_named(AppearancePage(), "appearance")
        self.stack.add_named(BarsPage(), "bars")
        self.stack.add_named(SystemPage(), "system")
        self.stack.add_named(self.make_placeholder(t("sidebar.developer", "Developer")), "developer")
        self.stack.add_named(self.make_placeholder(t("sidebar.plugins", "Plugins")), "plugins")
        self.stack.add_named(LanguagePage(on_language_changed=self.on_language_changed), "language")
        content_page.set_child(self.stack)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=t("app.title", "Arch Hyprland Settings Center")))
        toolbar.add_top_bar(header)
        toolbar.set_content(split)
        self.set_content(toolbar)

        key = active_key if active_key in self.rows else "dashboard"
        self.sidebar_list.select_row(self.rows[key])

    def make_placeholder(self, title: str) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(32)
        box.set_margin_bottom(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        heading = Gtk.Label(xalign=0)
        heading.set_label(title)
        heading.add_css_class("title-1")

        sub = Gtk.Label(
            label="This section will be connected in the next step.",
            xalign=0,
        )
        sub.add_css_class("dim-label")

        box.append(heading)
        box.append(sub)
        return box

    def on_row_selected(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if row is None:
            return
        self.stack.set_visible_child_name(row.key)  # type: ignore[attr-defined]

    def navigate_to(self, key: str) -> None:
        row = self.rows.get(key)
        if row is None:
            return
        self.sidebar_list.select_row(row)
        self.stack.set_visible_child_name(key)

    def on_language_changed(self) -> None:
        active = self.stack.get_visible_child_name() if hasattr(self, "stack") else "language"
        self.rebuild_ui(active or "language")


class SettingsCenterApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)

    def do_activate(self) -> None:
        window = self.props.active_window
        if not window:
            window = SettingsCenterWindow(self)
        window.present()


def main() -> None:
    app = SettingsCenterApp()
    app.run(None)


if __name__ == "__main__":
    main()
