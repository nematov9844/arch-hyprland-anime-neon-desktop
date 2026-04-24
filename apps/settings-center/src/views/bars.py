import json
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from services.locale_service import t

WAYBAR_DIR = Path.home() / ".config/waybar"
TOP_CONFIG = WAYBAR_DIR / "config.jsonc"
TOP_STYLE = WAYBAR_DIR / "style.css"
DOCK_CONFIG = WAYBAR_DIR / "dock.jsonc"
DOCK_STYLE = WAYBAR_DIR / "dock.css"
SETTINGS_CONFIG = Path.home() / ".config/settings/config.json"


class BarsPage(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_vexpand(True)

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('bars.title', 'Bars & Dock')}</span>")
        subtitle = Gtk.Label(label=t("bars.subtitle", "Manage Waybar top panel and dock."), xalign=0)
        subtitle.add_css_class("dim-label")

        self.status_label = Gtk.Label(label="", xalign=0)
        self.status_label.add_css_class("dim-label")

        self.top_status = Gtk.Label(label=t("bars.top_unknown", "Top Bar: Unknown"), xalign=0)
        self.dock_status = Gtk.Label(label=t("bars.dock_unknown", "Dock: Unknown"), xalign=0)
        self.proc_count_status = Gtk.Label(label=t("bars.process_count", "Waybar processes: 0"), xalign=0)
        self.last_action_status = Gtk.Label(label=t("bars.last_action", "Last action: -"), xalign=0)
        for lbl in [self.top_status, self.dock_status, self.proc_count_status, self.last_action_status]:
            lbl.add_css_class("dim-label")

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.append(self._build_top_bar_card())
        content.append(self._build_dock_card())
        content.append(self._build_status_card())
        content.append(self._build_configs_card())

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_hexpand(True)
        scroller.set_child(content)

        self.append(title)
        self.append(subtitle)
        self.append(self.status_label)
        self.append(scroller)

        self.refresh_status()

    def set_status(self, message: str, level: str = "info") -> None:
        self.status_label.set_label(message)
        self.last_action_status.set_label(f"{t('bars.last_action_prefix', 'Last action')}: {message}")
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

    def _build_top_bar_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("bars.top_bar", "Top Bar"), xalign=0)
        heading.add_css_class("heading")
        cfg = Gtk.Label(label=f"Config: {TOP_CONFIG}", xalign=0)
        css = Gtk.Label(label=f"Style: {TOP_STYLE}", xalign=0)
        cfg.add_css_class("dim-label")
        css.add_css_class("dim-label")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        reload_btn = Gtk.Button(label=t("bars.reload_top", "Reload Top Bar"))
        reload_btn.connect("clicked", lambda _b: self.reload_top_bar())
        start_btn = Gtk.Button(label=t("bars.start_top", "Start Top Bar"))
        start_btn.connect("clicked", lambda _b: self.start_top_bar())
        stop_btn = Gtk.Button(label=t("bars.stop_top", "Stop Top Bar"))
        stop_btn.connect("clicked", lambda _b: self.stop_top_bar())
        open_btn = Gtk.Button(label=t("bars.open_config", "Open Config"))
        open_btn.connect("clicked", lambda _b: self.open_path(WAYBAR_DIR))
        row.append(reload_btn)
        row.append(start_btn)
        row.append(stop_btn)
        row.append(open_btn)

        box.append(heading)
        box.append(cfg)
        box.append(css)
        box.append(row)
        frame.set_child(box)
        return frame

    def _build_dock_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("bars.dock", "Dock"), xalign=0)
        heading.add_css_class("heading")
        cfg = Gtk.Label(label=f"Dock config: {DOCK_CONFIG}", xalign=0)
        css = Gtk.Label(label=f"Dock style: {DOCK_STYLE}", xalign=0)
        cfg.add_css_class("dim-label")
        css.add_css_class("dim-label")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        start_btn = Gtk.Button(label=t("bars.start_dock", "Start Dock"))
        start_btn.connect("clicked", lambda _b: self.start_dock())
        stop_btn = Gtk.Button(label=t("bars.stop_dock", "Stop Dock"))
        stop_btn.connect("clicked", lambda _b: self.stop_dock())
        reload_btn = Gtk.Button(label=t("bars.reload_dock", "Reload Dock"))
        reload_btn.connect("clicked", lambda _b: self.reload_dock())
        open_btn = Gtk.Button(label=t("bars.open_dock_config", "Open Dock Config"))
        open_btn.connect("clicked", lambda _b: self.open_path(WAYBAR_DIR))
        row.append(start_btn)
        row.append(stop_btn)
        row.append(reload_btn)
        row.append(open_btn)

        box.append(heading)
        box.append(cfg)
        box.append(css)
        box.append(row)
        frame.set_child(box)
        return frame

    def _build_status_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("bars.status", "Status"), xalign=0)
        heading.add_css_class("heading")
        refresh_btn = Gtk.Button(label=t("bars.refresh_status", "Refresh Status"))
        refresh_btn.connect("clicked", lambda _b: self.refresh_status())

        box.append(heading)
        box.append(self.top_status)
        box.append(self.dock_status)
        box.append(self.proc_count_status)
        box.append(self.last_action_status)
        box.append(refresh_btn)
        frame.set_child(box)
        return frame

    def _build_configs_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("bars.config_files", "Config Files"), xalign=0)
        heading.add_css_class("heading")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b1 = Gtk.Button(label=t("bars.open_waybar_folder", "Open Waybar folder"))
        b1.connect("clicked", lambda _b: self.open_path(WAYBAR_DIR))
        b2 = Gtk.Button(label=t("bars.open_top_config", "Open top config"))
        b2.connect("clicked", lambda _b: self.open_path(TOP_CONFIG))
        b3 = Gtk.Button(label=t("bars.open_style", "Open style.css"))
        b3.connect("clicked", lambda _b: self.open_path(TOP_STYLE))
        b4 = Gtk.Button(label=t("bars.open_dock_config_file", "Open dock config"))
        b4.connect("clicked", lambda _b: self.open_path(DOCK_CONFIG))
        b5 = Gtk.Button(label=t("bars.open_dock_style", "Open dock.css"))
        b5.connect("clicked", lambda _b: self.open_path(DOCK_STYLE))
        row.append(b1)
        row.append(b2)
        row.append(b3)
        row.append(b4)
        row.append(b5)

        box.append(heading)
        box.append(row)
        frame.set_child(box)
        return frame

    def read_settings_config(self) -> dict:
        if not SETTINGS_CONFIG.exists():
            return {}
        try:
            raw = json.loads(SETTINGS_CONFIG.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception:
            return {}

    def save_settings_config(self, cfg: dict) -> bool:
        try:
            SETTINGS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            return True
        except Exception as exc:
            self.set_status(f"Settings write failed: {exc}", "error")
            return False

    def update_waybar_enabled(self, key: str, value: bool) -> None:
        cfg = self.read_settings_config()
        wb = cfg.get("waybar", {})
        if not isinstance(wb, dict):
            wb = {}
        wb[key] = value
        cfg["waybar"] = wb
        self.save_settings_config(cfg)

    def _file_warnings(self) -> list[str]:
        warnings: list[str] = []
        if not TOP_CONFIG.exists():
            warnings.append("top config missing")
        if not TOP_STYLE.exists():
            warnings.append("top style missing")
        if not DOCK_CONFIG.exists():
            warnings.append("dock config missing")
        if not DOCK_STYLE.exists():
            warnings.append("dock style missing")
        return warnings

    def run_shell(self, command: str, ok_message: str, level: str = "success") -> None:
        try:
            subprocess.Popen(["sh", "-lc", command])
            self.set_status(ok_message, level)
        except Exception as exc:
            self.set_status(f"Command failed: {exc}", "error")
        self.refresh_status()

    def start_top_bar(self) -> None:
        self.run_shell(
            "waybar -c ~/.config/waybar/config.jsonc -s ~/.config/waybar/style.css",
            t("bars.top_start_sent", "Top bar start command sent"),
        )
        self.update_waybar_enabled("top_enabled", True)

    def stop_top_bar(self) -> None:
        self.run_shell(
            "pkill -f \"waybar -c .*config.jsonc\" || pkill waybar || true",
            t("bars.top_stop_sent", "Top bar stop command sent"),
            "warning",
        )
        self.update_waybar_enabled("top_enabled", False)

    def reload_top_bar(self) -> None:
        self.run_shell(
            "pkill waybar || true; sleep 0.5; waybar -c ~/.config/waybar/config.jsonc -s ~/.config/waybar/style.css",
            t("bars.top_reloaded", "Top bar reloaded"),
        )
        self.update_waybar_enabled("top_enabled", True)

    def start_dock(self) -> None:
        self.run_shell(
            "waybar -c ~/.config/waybar/dock.jsonc -s ~/.config/waybar/dock.css",
            t("bars.dock_start_sent", "Dock start command sent"),
        )
        self.update_waybar_enabled("dock_enabled", True)

    def stop_dock(self) -> None:
        self.run_shell("pkill -f \"dock.jsonc\" || true", t("bars.dock_stop_sent", "Dock stop command sent"), "warning")
        self.update_waybar_enabled("dock_enabled", False)

    def reload_dock(self) -> None:
        self.run_shell(
            "pkill -f \"dock.jsonc\" || true; sleep 0.5; waybar -c ~/.config/waybar/dock.jsonc -s ~/.config/waybar/dock.css",
            t("bars.dock_reloaded", "Dock reloaded"),
        )
        self.update_waybar_enabled("dock_enabled", True)

    def open_path(self, path: Path) -> None:
        try:
            subprocess.Popen(["xdg-open", str(path)])
            self.set_status(f"Opened: {path}", "info")
        except Exception as exc:
            self.set_status(f"Open failed: {exc}", "error")

    def refresh_status(self) -> None:
        try:
            proc = subprocess.run(
                ["pgrep", "-fa", "waybar"],
                capture_output=True,
                text=True,
                check=False,
            )
            lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        except Exception as exc:
            self.set_status(f"Status refresh failed: {exc}", "error")
            lines = []

        dock_running = any("dock.jsonc" in ln for ln in lines)
        top_running = any(("config.jsonc" in ln and "dock.jsonc" not in ln) or ("waybar" in ln and "dock.jsonc" not in ln) for ln in lines)

        self.top_status.set_label(
            f"{t('bars.top_bar', 'Top Bar')}: {t('common.running', 'Running') if top_running else t('common.stopped', 'Stopped')}"
        )
        self.dock_status.set_label(
            f"{t('bars.dock', 'Dock')}: {t('common.running', 'Running') if dock_running else t('common.stopped', 'Stopped')}"
        )
        self.proc_count_status.set_label(f"{t('bars.processes', 'Waybar processes')}: {len(lines)}")

        warnings = self._file_warnings()
        if warnings:
            self.set_status(f"Warning: {', '.join(warnings)}", "warning")
