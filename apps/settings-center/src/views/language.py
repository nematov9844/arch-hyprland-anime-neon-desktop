import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from services.locale_service import load_language, save_language, t


LANG_OPTIONS = [
    ("en", "English", "English"),
    ("uz", "Uzbek", "O'zbek"),
    ("ru", "Russian", "Русский"),
]


class LanguagePage(Gtk.Box):
    def __init__(self, on_language_changed=None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.on_language_changed = on_language_changed
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_vexpand(True)

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('sidebar.language', 'Language')}</span>")
        subtitle = Gtk.Label(label=t("language.subtitle", "Choose interface language."), xalign=0)
        subtitle.add_css_class("dim-label")

        self.status_label = Gtk.Label(label="", xalign=0)
        self.status_label.add_css_class("dim-label")
        self.active_labels: dict[str, Gtk.Label] = {}

        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for lang_code, display_name, native_name in LANG_OPTIONS:
            self.cards_box.append(self._build_language_card(lang_code, display_name, native_name))

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_hexpand(True)
        scroller.set_child(self.cards_box)

        self.append(title)
        self.append(subtitle)
        self.append(self.status_label)
        self.append(scroller)

        self.refresh_active_labels()

    def _build_language_card(self, lang: str, display_name: str, native_name: str) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label=display_name, xalign=0)
        title.add_css_class("title-4")
        title.set_hexpand(True)
        active = Gtk.Label(label="", xalign=1)
        active.add_css_class("dim-label")
        self.active_labels[lang] = active
        top.append(title)
        top.append(active)

        native = Gtk.Label(label=native_name, xalign=0)
        native.add_css_class("dim-label")

        apply_btn = Gtk.Button(label=t("wallpapers.apply", "Apply"))
        apply_btn.connect("clicked", self.on_apply_language, lang)

        box.append(top)
        box.append(native)
        box.append(apply_btn)
        frame.set_child(box)
        return frame

    def set_status(self, message: str, level: str = "info") -> None:
        self.status_label.set_label(message)
        for css in ("success", "warning", "error", "dim-label"):
            self.status_label.remove_css_class(css)
        if level == "success":
            self.status_label.add_css_class("success")
        elif level == "warning":
            self.status_label.add_css_class("warning")
        elif level == "error":
            self.status_label.add_css_class("error")
        else:
            self.status_label.add_css_class("dim-label")

    def refresh_active_labels(self) -> None:
        current = load_language()
        for lang, lbl in self.active_labels.items():
            lbl.set_label(t("common.active", "Active") if lang == current else "")

    def on_apply_language(self, _button: Gtk.Button, lang: str) -> None:
        try:
            save_language(lang)
            self.refresh_active_labels()
            self.set_status(t("language.saved_realtime", "Language saved and applied."), "success")
            if callable(self.on_language_changed):
                self.on_language_changed()
        except Exception as exc:
            self.set_status(f"{t('language.save_failed', 'Failed to save language')}: {exc}", "error")
