import threading
import webbrowser
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GLib, Gtk

from services.config_service import (
    load_config_with_status,
    update_provider_config,
)
from services.locale_service import t

PROVIDER_META: dict[str, dict[str, object]] = {
    "wallhaven": {
        "title": "Wallhaven",
        "description": "High-quality wallpapers. API key optional for advanced limits.",
        "requires_key": False,
        "website": "https://wallhaven.cc/help/api",
    },
    "pexels": {
        "title": "Pexels",
        "description": "Photos + videos API. Requires API key.",
        "requires_key": True,
        "website": "https://www.pexels.com/api/",
    },
    "unsplash": {
        "title": "Unsplash",
        "description": "Professional photo API. Requires access key.",
        "requires_key": True,
        "website": "https://unsplash.com/developers",
    },
    "pixabay": {
        "title": "Pixabay",
        "description": "Free stock images API. Requires API key.",
        "requires_key": True,
        "website": "https://pixabay.com/api/docs/",
    },
}
class ProvidersPage(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('providers.title', 'Providers')}</span>")
        subtitle = Gtk.Label(
            label=t("providers.subtitle", "Manage wallpaper providers, API keys, and connectivity tests."),
            xalign=0,
        )
        subtitle.add_css_class("dim-label")

        self.error_label = Gtk.Label(label="", xalign=0)
        self.error_label.add_css_class("dim-label")

        self.cards_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.widgets: dict[str, dict[str, Gtk.Widget]] = {}
        self.config = self._load_config()

        for provider in ["pexels", "unsplash", "pixabay", "wallhaven"]:
            card = self._build_provider_card(provider)
            self.cards_wrap.append(card)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_hexpand(True)
        scroller.set_child(self.cards_wrap)

        self.append(title)
        self.append(subtitle)
        self.append(self.error_label)
        self.append(scroller)

    def _load_config(self) -> dict:
        try:
            cfg, had_fallback = load_config_with_status()
            if had_fallback:
                self.error_label.set_label("Config recover qilindi: ba'zi qiymatlar defaultga qaytdi.")
            return cfg
        except Exception:
            self.error_label.set_label("Config load failed.")
            return {}

    def _status_set(self, provider: str, text: str) -> None:
        status = self.widgets[provider]["status"]
        assert isinstance(status, Gtk.Label)
        status.set_label(text)

    def _set_card_enabled_visual(self, provider: str, enabled: bool) -> None:
        body = self.widgets[provider]["body"]
        assert isinstance(body, Gtk.Box)
        body.set_opacity(1.0 if enabled else 0.72)

    def _build_provider_card(self, provider: str) -> Gtk.Widget:
        meta = PROVIDER_META[provider]
        section = self.config.get(provider, {})
        if not isinstance(section, dict):
            section = {}

        frame = Gtk.Frame()
        frame.set_hexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_hexpand(True)
        name = Gtk.Label(label=str(meta["title"]), xalign=0)
        name.add_css_class("title-4")
        name.set_hexpand(True)

        enabled_switch = Gtk.Switch()
        enabled_switch.set_active(bool(section.get("enabled", True)))
        enabled_switch.connect("notify::active", self._on_enabled_toggled, provider)
        header.append(name)
        header.append(enabled_switch)

        desc = Gtk.Label(label=str(meta["description"]), xalign=0, wrap=True)
        desc.add_css_class("dim-label")

        entry_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        key_entry = Gtk.Entry()
        key_entry.set_visibility(False)
        key_entry.set_hexpand(True)
        key_entry.set_placeholder_text(t("providers.api_key", "API key"))
        key_entry.set_text(str(section.get("api_key", "")))

        reveal_btn = Gtk.ToggleButton(label=t("common.show", "Show"))
        reveal_btn.connect("toggled", self._on_reveal_toggled, key_entry)
        entry_row.append(key_entry)
        entry_row.append(reveal_btn)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        save_btn = Gtk.Button(label=t("providers.save", "Save"))
        save_btn.connect("clicked", self._on_save_clicked, provider)
        test_btn = Gtk.Button(label=t("providers.test", "Test"))
        test_btn.connect("clicked", self._on_test_clicked, provider)
        web_btn = Gtk.Button(label=t("providers.website", "Website"))
        web_btn.connect("clicked", self._on_open_website, str(meta["website"]))

        action_row.append(save_btn)
        action_row.append(test_btn)
        action_row.append(web_btn)

        status = Gtk.Label(label="", xalign=0)
        status.add_css_class("dim-label")

        requires_key = bool(meta["requires_key"])
        key_val = str(section.get("api_key", "")).strip()
        if requires_key and not key_val:
            status.set_label(t("providers.not_configured", "Not configured"))
        else:
            status.set_label(t("providers.saved", "Saved"))

        box.append(header)
        box.append(desc)
        # Wallhaven key is optional but still editable.
        box.append(entry_row)
        box.append(action_row)
        box.append(status)

        frame.set_child(box)

        self.widgets[provider] = {
            "switch": enabled_switch,
            "entry": key_entry,
            "status": status,
            "body": box,
        }
        self._set_card_enabled_visual(provider, enabled_switch.get_active())
        return frame

    def _on_reveal_toggled(self, button: Gtk.ToggleButton, entry: Gtk.Entry) -> None:
        visible = button.get_active()
        entry.set_visibility(visible)
        button.set_label(t("common.hide", "Hide") if visible else t("common.show", "Show"))

    def _on_enabled_toggled(self, switch: Gtk.Switch, _pspec: object, provider: str) -> None:
        enabled = switch.get_active()
        self._set_card_enabled_visual(provider, enabled)
        self._status_set(
            provider,
            t("providers.saved", "Saved") if enabled else t("providers.saved_disabled", "Saved (disabled)"),
        )

    def _on_save_clicked(self, _button: Gtk.Button, provider: str) -> None:
        sw = self.widgets[provider]["switch"]
        entry = self.widgets[provider]["entry"]
        assert isinstance(sw, Gtk.Switch)
        assert isinstance(entry, Gtk.Entry)
        try:
            self.config = update_provider_config(
                provider,
                {
                    "enabled": bool(sw.get_active()),
                    "api_key": entry.get_text().strip(),
                },
            )
            self._status_set(provider, t("providers.saved", "Saved"))
        except Exception:
            self._status_set(provider, t("common.failed", "Failed"))

    def _on_open_website(self, _button: Gtk.Button, url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception as exc:
            print(f"[Providers] open website failed: {url} | error={exc}")

    def _on_test_clicked(self, _button: Gtk.Button, provider: str) -> None:
        # Save latest values before test for predictable behavior.
        self._on_save_clicked(_button, provider)
        self._status_set(provider, t("providers.testing", "Testing..."))

        def worker() -> None:
            try:
                ok = self._test_provider(provider)
                GLib.idle_add(
                    self._status_set,
                    provider,
                    t("providers.working", "Working") if ok else t("common.failed", "Failed"),
                )
            except Exception as exc:
                print(f"[Providers] test failed: {provider} | error={exc}")
                GLib.idle_add(self._status_set, provider, t("common.failed", "Failed"))

        threading.Thread(target=worker, daemon=True).start()

    def _test_provider(self, provider: str) -> bool:
        section = self.config.get(provider, {})
        if not isinstance(section, dict):
            return False
        api_key = str(section.get("api_key", "")).strip()

        if provider == "wallhaven":
            req = Request("https://wallhaven.cc/api/v1/search?q=nature&page=1")
            return self._request_ok(req)

        if provider == "pexels":
            if not api_key:
                return False
            req = Request(
                "https://api.pexels.com/v1/search?query=nature&per_page=1",
                headers={"Authorization": api_key},
            )
            return self._request_ok(req)

        if provider == "unsplash":
            if not api_key:
                return False
            req = Request(
                "https://api.unsplash.com/search/photos?query=nature&per_page=1",
                headers={"Authorization": f"Client-ID {api_key}"},
            )
            return self._request_ok(req)

        if provider == "pixabay":
            if not api_key:
                return False
            url = "https://pixabay.com/api/?" + urlencode(
                {"key": api_key, "q": "nature", "per_page": "3"}
            )
            req = Request(url)
            return self._request_ok(req)

        return False

    def _request_ok(self, req: Request) -> bool:
        try:
            with urlopen(req, timeout=8) as resp:
                code = getattr(resp, "status", 200)
                if code < 200 or code >= 300:
                    return False
                payload = resp.read(512)
                return bool(payload)
        except URLError:
            return False
        except Exception as exc:
            print(f"[Providers] request error: {exc}")
            return False
