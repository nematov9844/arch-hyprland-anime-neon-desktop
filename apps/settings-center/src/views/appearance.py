import json
import shutil
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from services.appearance_apply_service import (
    apply_hypr_effects,
    apply_waybar_modules,
    reload_waybar as reload_waybar_runtime,
)
from services.locale_service import t

THEMES_DIR = Path.home() / ".config/waybar/themes"
SETTINGS_CONFIG_PATH = Path.home() / ".config/settings/config.json"
REPO_THEMES_DIR = Path(__file__).resolve().parents[4] / "config/waybar/themes"
THEME_REPO_FILES = {"neon-purple.css", "crimson-night.css", "mono-dark.css"}
PANEL_MODE_CSS_PATH = THEMES_DIR / "panel-mode.css"
HYPRLOCK_HOME_PATH = Path.home() / ".config/hypr/hyprlock.conf"
HYPRLOCK_REPO_PATH = Path(__file__).resolve().parents[4] / "config/hypr/hyprlock.conf"

THEMES = [
    {"id": "neon-purple", "title": "Neon Purple", "description": "Cyber neon purple accent.", "file": "neon-purple.css", "accent": "#A855F7"},
    {"id": "crimson-night", "title": "Crimson Night", "description": "Dark crimson contrast.", "file": "crimson-night.css", "accent": "#DC2626"},
    {"id": "mono-dark", "title": "Mono Dark", "description": "Minimal monochrome dark.", "file": "mono-dark.css", "accent": "#9CA3AF"},
    {"id": "ocean-cyber", "title": "Ocean Cyber", "description": "Blue cyber ocean tone.", "file": "ocean-cyber.css", "accent": "#0EA5E9"},
    {"id": "sakura-night", "title": "Sakura Night", "description": "Soft pink night style.", "file": "sakura-night.css", "accent": "#F472B6"},
    {"id": "matrix-green", "title": "Matrix Green", "description": "Classic green terminal vibe.", "file": "matrix-green.css", "accent": "#22C55E"},
    {"id": "amber-glow", "title": "Amber Glow", "description": "Warm amber accent.", "file": "amber-glow.css", "accent": "#F59E0B"},
    {"id": "ice-blue", "title": "Ice Blue", "description": "Cool icy blue palette.", "file": "ice-blue.css", "accent": "#60A5FA"},
    {"id": "rose-pine", "title": "Rose Pine", "description": "Muted rose-pine style.", "file": "rose-pine.css", "accent": "#C084FC"},
    {"id": "cyber-yellow", "title": "Cyber Yellow", "description": "Bright yellow cyber look.", "file": "cyber-yellow.css", "accent": "#EAB308"},
]

THEME_PALETTES = {
    "neon-purple": {"accent": "#8b5cf6", "bg": "rgba(11, 15, 23, 0.88)", "fg": "#e5e7eb", "cyan": "#22d3ee", "red": "#ef4444", "yellow": "#facc15", "blue": "#60a5fa", "green": "#4ade80", "violet": "#c084fc"},
    "crimson-night": {"accent": "#dc2626", "bg": "rgba(20, 10, 12, 0.90)", "fg": "#f5e7e7", "cyan": "#fda4af", "red": "#f43f5e", "yellow": "#f59e0b", "blue": "#fb7185", "green": "#86efac", "violet": "#f472b6"},
    "mono-dark": {"accent": "#9ca3af", "bg": "rgba(17, 17, 17, 0.90)", "fg": "#e5e7eb", "cyan": "#d1d5db", "red": "#f87171", "yellow": "#facc15", "blue": "#93c5fd", "green": "#86efac", "violet": "#c4b5fd"},
    "ocean-cyber": {"accent": "#0ea5e9", "bg": "rgba(8, 20, 30, 0.90)", "fg": "#e0f2fe", "cyan": "#22d3ee", "red": "#fb7185", "yellow": "#fde047", "blue": "#38bdf8", "green": "#34d399", "violet": "#818cf8"},
    "sakura-night": {"accent": "#f472b6", "bg": "rgba(28, 15, 24, 0.90)", "fg": "#fce7f3", "cyan": "#f9a8d4", "red": "#fb7185", "yellow": "#facc15", "blue": "#93c5fd", "green": "#86efac", "violet": "#e879f9"},
    "matrix-green": {"accent": "#22c55e", "bg": "rgba(8, 18, 10, 0.90)", "fg": "#dcfce7", "cyan": "#4ade80", "red": "#fb7185", "yellow": "#a3e635", "blue": "#34d399", "green": "#22c55e", "violet": "#86efac"},
    "amber-glow": {"accent": "#f59e0b", "bg": "rgba(24, 18, 8, 0.90)", "fg": "#fef3c7", "cyan": "#fbbf24", "red": "#fb7185", "yellow": "#facc15", "blue": "#f59e0b", "green": "#86efac", "violet": "#fcd34d"},
    "ice-blue": {"accent": "#60a5fa", "bg": "rgba(10, 18, 28, 0.90)", "fg": "#e0f2fe", "cyan": "#7dd3fc", "red": "#f87171", "yellow": "#fde047", "blue": "#60a5fa", "green": "#6ee7b7", "violet": "#93c5fd"},
    "rose-pine": {"accent": "#c084fc", "bg": "rgba(18, 14, 28, 0.90)", "fg": "#f5f3ff", "cyan": "#a78bfa", "red": "#fb7185", "yellow": "#facc15", "blue": "#93c5fd", "green": "#86efac", "violet": "#c084fc"},
    "cyber-yellow": {"accent": "#eab308", "bg": "rgba(20, 20, 8, 0.90)", "fg": "#fef9c3", "cyan": "#fde047", "red": "#f87171", "yellow": "#eab308", "blue": "#facc15", "green": "#a3e635", "violet": "#fde68a"},
}

FONT_PRESETS = [
    "JetBrainsMono Nerd Font",
    "FiraCode Nerd Font",
    "Hack Nerd Font",
    "Iosevka Nerd Font",
    "MesloLGS Nerd Font",
    "CascadiaCode Nerd Font",
    "UbuntuMono Nerd Font",
    "Mononoki Nerd Font",
    "SourceCodePro Nerd Font",
    "Noto Sans",
]

MODULES = [
    ("bluetooth", "appearance.modules.bluetooth", "Bluetooth"),
    ("network", "appearance.modules.network", "Network"),
    ("battery", "appearance.modules.battery", "Battery"),
    ("clock", "appearance.modules.clock", "Clock"),
    ("tray", "appearance.modules.tray", "Tray"),
    ("backlight", "appearance.modules.backlight", "Backlight"),
    ("volume", "appearance.modules.volume", "Volume"),
    ("settings", "appearance.modules.settings", "Settings"),
    ("power", "appearance.modules.power", "Power"),
]

WAYBAR_MODULE_MAP = {
    "bluetooth": "bluetooth",
    "network": "network",
    "battery": "battery",
    "clock": "clock",
    "tray": "tray",
    "backlight": "backlight",
    "volume": "pulseaudio",
    "settings": "custom/settings",
    "power": "custom/power",
}

WAYBAR_RIGHT_ORDER = [
    "custom/wallpaper",
    "custom/settings",
    "custom/media",
    "pulseaudio",
    "network",
    "battery",
    "tray",
    "custom/power",
    "backlight",
    "bluetooth",
]

PANEL_BACKGROUND_MODES = ["solid", "transparent", "blur"]
LOCKSCREEN_LAYOUTS = ["center", "top"]


class AppearancePage(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_vexpand(True)

        self.theme_status_labels: dict[str, Gtk.Label] = {}
        self.theme_apply_buttons: dict[str, Gtk.Button] = {}
        self.module_switches: dict[str, Gtk.Switch] = {}
        self._suppress_events = False

        self.opacity_active_values = ["1.0", "0.95", "0.9", "0.85"]
        self.opacity_inactive_values = ["0.95", "0.85", "0.75", "0.65"]
        self.blur_size_values = ["2", "4", "6", "8"]
        self.blur_passes_values = ["1", "2", "3"]
        self.panel_mode_labels = [
            t("appearance.panel_mode.solid", "Solid"),
            t("appearance.panel_mode.transparent", "Transparent"),
            t("appearance.panel_mode.blur", "Blur"),
        ]
        self.lockscreen_layout_labels = [
            t("appearance.lockscreen.layout.center", "Center"),
            t("appearance.lockscreen.layout.top", "Top"),
        ]

        self.current_theme_value = Gtk.Label(label=t("common.unknown", "Unknown"), xalign=0)
        self.current_theme_value.add_css_class("dim-label")

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('appearance.title', 'Appearance')}</span>")
        subtitle = Gtk.Label(label=t("appearance.subtitle", "Themes, fonts, and visual style"), xalign=0)
        subtitle.add_css_class("dim-label")

        self.status_label = Gtk.Label(label="", xalign=0)
        self.status_label.add_css_class("dim-label")

        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.cards_box.append(self._build_current_theme_card())
        self.cards_box.append(self._build_theme_presets_card())
        self.cards_box.append(self._build_font_presets_card())
        self.cards_box.append(self._build_top_panel_modules_card())
        self.cards_box.append(self._build_blur_effects_card())
        self.cards_box.append(self._build_lockscreen_card())
        self.cards_box.append(self._build_advanced_card())

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_hexpand(True)
        scroller.set_child(self.cards_box)

        self.append(title)
        self.append(subtitle)
        self.append(self.status_label)
        self.append(scroller)

        self.ensure_theme_files_installed()
        self._init_form_values()
        self.refresh_theme_state()
        self.refresh_theme_install_state()

    def read_settings_config(self) -> dict:
        if not SETTINGS_CONFIG_PATH.exists():
            return {}
        try:
            raw = json.loads(SETTINGS_CONFIG_PATH.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception:
            self.set_status(t("appearance.settings_parse_failed", "Settings config parse failed, using defaults."), "warning")
            return {}

    def save_settings_config(self, config: dict) -> bool:
        try:
            SETTINGS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
            return True
        except Exception as exc:
            self.set_status(f"{t('appearance.settings_save_failed', 'Settings config save failed')}: {exc}", "error")
            return False

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

    def _build_current_theme_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        heading = Gtk.Label(label=t("appearance.current_theme", "Current Theme"), xalign=0)
        heading.add_css_class("heading")
        box.append(heading)
        box.append(self.current_theme_value)
        frame.set_child(box)
        return frame

    def _build_theme_presets_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)
        heading = Gtk.Label(label=t("appearance.theme_presets", "Theme Presets"), xalign=0)
        heading.add_css_class("heading")
        desc = Gtk.Label(label=t("appearance.theme_presets_desc", "Pick a preset and apply instantly."), xalign=0)
        desc.add_css_class("dim-label")
        outer.append(heading)
        outer.append(desc)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_valign(Gtk.Align.START)
        flow.set_max_children_per_line(4)
        flow.set_min_children_per_line(1)
        flow.set_column_spacing(8)
        flow.set_row_spacing(8)

        for theme in THEMES:
            card = Gtk.Frame()
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            row.set_margin_top(8)
            row.set_margin_bottom(8)
            row.set_margin_start(8)
            row.set_margin_end(8)

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            title = Gtk.Label(label=str(theme["title"]), xalign=0)
            title.add_css_class("title-4")
            title.set_hexpand(True)
            accent = Gtk.Label(xalign=1)
            accent.set_use_markup(True)
            accent.set_markup(f"<span foreground='{theme['accent']}'>●</span>")
            top.append(title)
            top.append(accent)
            description = Gtk.Label(label=str(theme["description"]), xalign=0)
            description.add_css_class("dim-label")
            description.set_wrap(True)

            actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            apply_btn = Gtk.Button(label=t("wallpapers.apply", "Apply"))
            apply_btn.connect("clicked", self.on_apply_theme_clicked, str(theme["id"]))
            status = Gtk.Label(label="", xalign=0)
            status.add_css_class("dim-label")
            self.theme_status_labels[str(theme["id"])] = status
            self.theme_apply_buttons[str(theme["id"])] = apply_btn
            actions.append(apply_btn)
            actions.append(status)

            row.append(top)
            row.append(description)
            row.append(actions)
            card.set_child(row)
            card.set_size_request(240, -1)
            flow.insert(card, -1)
        outer.append(flow)
        frame.set_child(outer)
        return frame

    def _build_font_presets_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        heading = Gtk.Label(label=t("appearance.font_presets", "Font Presets"), xalign=0)
        heading.add_css_class("heading")
        desc = Gtk.Label(label=t("appearance.font_presets_desc", "Choose fonts and save settings for terminal/UI/Waybar."), xalign=0)
        desc.add_css_class("dim-label")

        self.font_terminal = Gtk.DropDown.new_from_strings(FONT_PRESETS)
        self.font_ui = Gtk.DropDown.new_from_strings(FONT_PRESETS)
        self.font_waybar = Gtk.DropDown.new_from_strings(FONT_PRESETS)
        save_btn = Gtk.Button(label=t("appearance.save_font_settings", "Save Font Settings"))
        save_btn.connect("clicked", self.on_save_fonts_clicked)

        for dd in [self.font_terminal, self.font_ui, self.font_waybar]:
            dd.set_hexpand(True)

        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(10)
        lbl_terminal = Gtk.Label(label=t("appearance.font_terminal_label", "Terminal font"), xalign=0)
        lbl_terminal.set_size_request(130, -1)
        lbl_ui = Gtk.Label(label=t("appearance.font_ui_label", "UI font"), xalign=0)
        lbl_ui.set_size_request(130, -1)
        lbl_waybar = Gtk.Label(label=t("appearance.font_waybar_label", "Waybar font"), xalign=0)
        lbl_waybar.set_size_request(130, -1)
        grid.attach(lbl_terminal, 0, 0, 1, 1)
        grid.attach(self.font_terminal, 1, 0, 1, 1)
        grid.attach(lbl_ui, 0, 1, 1, 1)
        grid.attach(self.font_ui, 1, 1, 1, 1)
        grid.attach(lbl_waybar, 0, 2, 1, 1)
        grid.attach(self.font_waybar, 1, 2, 1, 1)

        box.append(heading)
        box.append(desc)
        box.append(grid)
        save_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        save_row.append(save_btn)
        save_row.set_halign(Gtk.Align.END)
        box.append(save_row)
        frame.set_child(box)
        return frame

    def _build_top_panel_modules_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        heading = Gtk.Label(label=t("appearance.top_panel_modules", "Top Panel Modules"), xalign=0)
        heading.add_css_class("heading")
        note = Gtk.Label(label=t("appearance.modules_note", "Module toggles will be applied to Waybar config in the next step."), xalign=0)
        note.add_css_class("dim-label")
        box.append(heading)
        box.append(note)

        panel_mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        panel_mode_label = Gtk.Label(label=t("appearance.panel_mode", "Panel background mode"), xalign=0)
        panel_mode_label.set_hexpand(True)
        self.panel_mode_dropdown = Gtk.DropDown.new_from_strings(self.panel_mode_labels)
        self.panel_mode_dropdown.connect("notify::selected", self.on_panel_mode_changed)
        panel_mode_row.append(panel_mode_label)
        panel_mode_row.append(self.panel_mode_dropdown)
        box.append(panel_mode_row)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(4)
        flow.set_min_children_per_line(1)
        flow.set_column_spacing(8)
        flow.set_row_spacing(8)

        for key, tr_key, fallback in MODULES:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_margin_top(6)
            row.set_margin_bottom(6)
            row.set_margin_start(8)
            row.set_margin_end(8)
            lbl = Gtk.Label(label=t(tr_key, fallback), xalign=0)
            lbl.set_hexpand(True)
            sw = Gtk.Switch()
            sw.connect("notify::active", self.on_module_toggled, key)
            self.module_switches[key] = sw
            row.append(lbl)
            row.append(sw)
            card = Gtk.Frame()
            card.set_child(row)
            card.set_size_request(190, -1)
            flow.insert(card, -1)
        box.append(flow)
        frame.set_child(box)
        return frame

    def _build_blur_effects_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        heading = Gtk.Label(label=t("appearance.blur_effects", "Blur & Effects"), xalign=0)
        heading.add_css_class("heading")
        box.append(heading)

        self.blur_enabled = Gtk.Switch()
        self.lockscreen_blur = Gtk.Switch()
        self.blur_enabled.connect("notify::active", self.on_effect_setting_changed)
        self.lockscreen_blur.connect("notify::active", self.on_effect_setting_changed)
        self.opacity_active = Gtk.DropDown.new_from_strings(self.opacity_active_values)
        self.opacity_inactive = Gtk.DropDown.new_from_strings(self.opacity_inactive_values)
        self.blur_size = Gtk.DropDown.new_from_strings(self.blur_size_values)
        self.blur_passes = Gtk.DropDown.new_from_strings(self.blur_passes_values)
        for dd in [self.opacity_active, self.opacity_inactive, self.blur_size, self.blur_passes]:
            dd.connect("notify::selected", self.on_effect_setting_changed)
            dd.set_hexpand(True)

        switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        switch_box.append(self._switch_row(t("appearance.blur_enabled", "Blur enabled"), self.blur_enabled))
        switch_box.append(self._switch_row(t("appearance.lockscreen_blur", "Lockscreen blur"), self.lockscreen_blur))
        box.append(switch_box)

        selects_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        for title, dropdown in [
            (t("appearance.opacity_active", "Active opacity"), self.opacity_active),
            (t("appearance.opacity_inactive", "Inactive opacity"), self.opacity_inactive),
            (t("appearance.blur_size", "Blur size"), self.blur_size),
            (t("appearance.blur_passes", "Blur passes"), self.blur_passes),
        ]:
            item = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            item.set_hexpand(True)
            lbl = Gtk.Label(label=title, xalign=0)
            lbl.add_css_class("dim-label")
            item.append(lbl)
            item.append(dropdown)
            selects_row.append(item)
        box.append(selects_row)
        frame.set_child(box)
        return frame

    def _build_lockscreen_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("appearance.lockscreen.title", "Lockscreen Design"), xalign=0)
        heading.add_css_class("heading")
        desc = Gtk.Label(
            label=t("appearance.lockscreen.desc", "Control lockscreen layout and visible elements."),
            xalign=0,
        )
        desc.add_css_class("dim-label")
        box.append(heading)
        box.append(desc)

        self.lockscreen_layout = Gtk.DropDown.new_from_strings(self.lockscreen_layout_labels)
        self.lockscreen_show_greeting = Gtk.Switch()
        self.lockscreen_show_clock = Gtk.Switch()
        self.lockscreen_show_power_hint = Gtk.Switch()
        self.lockscreen_show_date = Gtk.Switch()
        self.lockscreen_layout.connect("notify::selected", self.on_lockscreen_setting_changed)
        self.lockscreen_show_greeting.connect("notify::active", self.on_lockscreen_setting_changed)
        self.lockscreen_show_clock.connect("notify::active", self.on_lockscreen_setting_changed)
        self.lockscreen_show_power_hint.connect("notify::active", self.on_lockscreen_setting_changed)
        self.lockscreen_show_date.connect("notify::active", self.on_lockscreen_setting_changed)

        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        layout_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        layout_col.set_hexpand(True)
        layout_lbl = Gtk.Label(label=t("appearance.lockscreen.layout", "Layout"), xalign=0)
        layout_lbl.add_css_class("dim-label")
        layout_col.append(layout_lbl)
        layout_col.append(self.lockscreen_layout)
        grid.attach(layout_col, 0, 0, 2, 1)

        for idx, (title, sw) in enumerate(
            [
                (t("appearance.lockscreen.greeting", "Show greeting"), self.lockscreen_show_greeting),
                (t("appearance.lockscreen.clock", "Show clock"), self.lockscreen_show_clock),
                (t("appearance.lockscreen.date", "Show date"), self.lockscreen_show_date),
                (t("appearance.lockscreen.power_hint", "Show power hint"), self.lockscreen_show_power_hint),
            ]
        ):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_hexpand(True)
            lbl = Gtk.Label(label=title, xalign=0)
            lbl.set_hexpand(True)
            row.append(lbl)
            row.append(sw)
            grid.attach(row, idx % 2, 1 + (idx // 2), 1, 1)
        box.append(grid)
        frame.set_child(box)
        return frame

    def _build_advanced_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        heading = Gtk.Label(label=t("appearance.advanced_config", "Advanced Config"), xalign=0)
        heading.add_css_class("heading")
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(4)
        flow.set_min_children_per_line(1)
        flow.set_column_spacing(8)
        flow.set_row_spacing(8)

        b1 = Gtk.Button(label=t("appearance.open_waybar_config", "Open Waybar Config"))
        b1.connect("clicked", lambda _b: self.open_path(Path.home() / ".config/waybar"))
        b2 = Gtk.Button(label=t("appearance.open_hyprland_config", "Open Hyprland Config"))
        b2.connect("clicked", lambda _b: self.open_path(Path.home() / ".config/hypr"))
        b3 = Gtk.Button(label=t("appearance.open_kitty_config", "Open Kitty Config"))
        b3.connect("clicked", lambda _b: self.open_kitty_config())
        b4 = Gtk.Button(label=t("appearance.open_theme_folder", "Open Theme Folder"))
        b4.connect("clicked", lambda _b: self.open_path(THEMES_DIR))
        b5 = Gtk.Button(label=t("appearance.reset_settings", "Reset Appearance Settings"))
        b5.connect("clicked", self.on_reset_appearance_clicked)

        for btn in [b1, b2, b3, b4, b5]:
            flow.insert(btn, -1)
        box.append(heading)
        box.append(flow)
        frame.set_child(box)
        return frame

    def _switch_row(self, label: str, switch: Gtk.Switch) -> Gtk.Widget:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.set_hexpand(True)
        row.append(lbl)
        row.append(switch)
        return row

    def _dropdown_row(self, label: str, dropdown: Gtk.DropDown) -> Gtk.Widget:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.set_hexpand(True)
        row.append(lbl)
        row.append(dropdown)
        return row

    def _ensure_sections(self, cfg: dict) -> dict:
        appearance = cfg.get("appearance", {})
        if not isinstance(appearance, dict):
            appearance = {}
        font = appearance.get("font", {})
        if not isinstance(font, dict):
            font = {}
        panel = appearance.get("panel", {})
        if not isinstance(panel, dict):
            panel = {}
        lockscreen = appearance.get("lockscreen", {})
        if not isinstance(lockscreen, dict):
            lockscreen = {}
        appearance["font"] = font
        appearance["panel"] = panel
        appearance["lockscreen"] = lockscreen
        cfg["appearance"] = appearance

        waybar = cfg.get("waybar", {})
        if not isinstance(waybar, dict):
            waybar = {}
        modules = waybar.get("modules", {})
        if not isinstance(modules, dict):
            modules = {}
        waybar["modules"] = modules
        cfg["waybar"] = waybar

        effects = cfg.get("effects", {})
        if not isinstance(effects, dict):
            effects = {}
        blur = effects.get("blur", {})
        if not isinstance(blur, dict):
            blur = {}
        opacity = effects.get("opacity", {})
        if not isinstance(opacity, dict):
            opacity = {}
        effects["blur"] = blur
        effects["opacity"] = opacity
        cfg["effects"] = effects
        return cfg

    def _init_form_values(self) -> None:
        self._suppress_events = True
        cfg = self._ensure_sections(self.read_settings_config())
        font = cfg["appearance"]["font"]
        panel = cfg["appearance"]["panel"]
        lockscreen = cfg["appearance"]["lockscreen"]
        modules = cfg["waybar"]["modules"]
        effects = cfg["effects"]

        def set_dropdown(dropdown: Gtk.DropDown, values: list[str], value: str) -> None:
            dropdown.set_selected(values.index(value) if value in values else 0)

        set_dropdown(self.font_terminal, FONT_PRESETS, str(font.get("terminal", FONT_PRESETS[0])))
        set_dropdown(self.font_ui, FONT_PRESETS, str(font.get("ui", FONT_PRESETS[0])))
        set_dropdown(self.font_waybar, FONT_PRESETS, str(font.get("waybar", FONT_PRESETS[0])))
        set_dropdown(self.panel_mode_dropdown, PANEL_BACKGROUND_MODES, str(panel.get("background_mode", "solid")))
        set_dropdown(self.lockscreen_layout, LOCKSCREEN_LAYOUTS, str(lockscreen.get("layout", "center")))
        self.lockscreen_show_greeting.set_active(bool(lockscreen.get("show_greeting", True)))
        self.lockscreen_show_clock.set_active(bool(lockscreen.get("show_clock", True)))
        self.lockscreen_show_date.set_active(bool(lockscreen.get("show_date", True)))
        self.lockscreen_show_power_hint.set_active(bool(lockscreen.get("show_power_hint", True)))

        for key, _tr, _fb in MODULES:
            self.module_switches[key].set_active(bool(modules.get(key, True)))

        blur = effects["blur"]
        opacity = effects["opacity"]
        self.blur_enabled.set_active(bool(blur.get("enabled", True)))
        self.lockscreen_blur.set_active(bool(effects.get("lockscreen_blur", True)))
        set_dropdown(self.opacity_active, self.opacity_active_values, str(opacity.get("active", "1.0")))
        set_dropdown(self.opacity_inactive, self.opacity_inactive_values, str(opacity.get("inactive", "0.85")))
        set_dropdown(self.blur_size, self.blur_size_values, str(blur.get("size", "4")))
        set_dropdown(self.blur_passes, self.blur_passes_values, str(blur.get("passes", "2")))
        self._suppress_events = False

    def get_current_theme_id(self) -> str:
        cfg = self.read_settings_config()
        theme_cfg = cfg.get("theme", {})
        if isinstance(theme_cfg, dict):
            return str(theme_cfg.get("current", "")).strip()
        return ""

    def refresh_theme_state(self) -> None:
        current = self.get_current_theme_id() or "neon-purple"
        self.current_theme_value.set_label(current)
        for theme in THEMES:
            tid = str(theme["id"])
            label = self.theme_status_labels.get(tid)
            if label is not None:
                label.set_label(t("common.active", "Active") if tid == current else "")

    def refresh_theme_install_state(self) -> None:
        for theme in THEMES:
            tid = str(theme["id"])
            status = self.theme_status_labels.get(tid)
            button = self.theme_apply_buttons.get(tid)
            if status is None or button is None:
                continue
            is_installed = (THEMES_DIR / str(theme["file"])).exists()
            button.set_sensitive(is_installed)
            if not is_installed and status.get_label() != t("common.active", "Active"):
                status.set_label(t("appearance.not_installed", "Not installed"))

    def apply_theme(self, theme_id: str) -> None:
        selected = next((item for item in THEMES if str(item["id"]) == theme_id), None)
        if selected is None:
            self.set_status(t("appearance.unknown_theme_id", "Unknown theme id."), "error")
            return
        source = THEMES_DIR / str(selected["file"])
        target = THEMES_DIR / "current.css"
        if not source.exists():
            self.set_status(t("appearance.theme_not_installed", "Theme is not installed."), "warning")
            self.refresh_theme_install_state()
            return
        try:
            THEMES_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        except Exception as exc:
            self.set_status(f"{t('appearance.theme_write_failed', 'Cannot write current.css')}: {exc}", "error")
            return

        cfg = self._ensure_sections(self.read_settings_config())
        theme_cfg = cfg.get("theme", {})
        if not isinstance(theme_cfg, dict):
            theme_cfg = {}
        theme_cfg["current"] = theme_id
        cfg["theme"] = theme_cfg
        if not self.save_settings_config(cfg):
            return
        panel_mode = str(cfg.get("appearance", {}).get("panel", {}).get("background_mode", "solid"))
        self.apply_panel_mode_to_waybar(panel_mode)
        self.apply_lockscreen_config(cfg)
        self.reload_waybar()
        self.trigger_global_theme_sync()
        self.refresh_theme_state()
        self.refresh_theme_install_state()
        self.set_status(t("appearance.theme_applied", "Theme applied"), "success")

    def on_apply_theme_clicked(self, _button: Gtk.Button, theme_id: str) -> None:
        self.apply_theme(theme_id)

    def on_save_fonts_clicked(self, _button: Gtk.Button) -> None:
        cfg = self._ensure_sections(self.read_settings_config())
        font = cfg["appearance"]["font"]
        font["terminal"] = FONT_PRESETS[self.font_terminal.get_selected()]
        font["ui"] = FONT_PRESETS[self.font_ui.get_selected()]
        font["waybar"] = FONT_PRESETS[self.font_waybar.get_selected()]
        if self.save_settings_config(cfg):
            self.set_status(t("appearance.fonts_saved", "Font settings saved."), "success")

    def on_panel_mode_changed(self, _widget, _pspec=None) -> None:
        if self._suppress_events:
            return
        cfg = self._ensure_sections(self.read_settings_config())
        selected_mode = PANEL_BACKGROUND_MODES[self.panel_mode_dropdown.get_selected()]
        cfg["appearance"]["panel"]["background_mode"] = selected_mode
        if not self.save_settings_config(cfg):
            return
        self.apply_panel_mode_to_waybar(selected_mode)
        self.trigger_global_theme_sync()
        self.reload_waybar()
        self.set_status(t("appearance.panel_mode_saved", "Panel mode updated."), "success")

    def on_lockscreen_setting_changed(self, _widget, _pspec=None) -> None:
        if self._suppress_events:
            return
        cfg = self._ensure_sections(self.read_settings_config())
        lock = cfg["appearance"]["lockscreen"]
        lock["layout"] = LOCKSCREEN_LAYOUTS[self.lockscreen_layout.get_selected()]
        lock["show_greeting"] = bool(self.lockscreen_show_greeting.get_active())
        lock["show_clock"] = bool(self.lockscreen_show_clock.get_active())
        lock["show_date"] = bool(self.lockscreen_show_date.get_active())
        lock["show_power_hint"] = bool(self.lockscreen_show_power_hint.get_active())
        if not self.save_settings_config(cfg):
            return
        self.apply_lockscreen_config(cfg)
        self.set_status(t("appearance.lockscreen.saved", "Lockscreen design updated."), "success")

    def on_module_toggled(self, _switch: Gtk.Switch, _pspec: object, module_key: str) -> None:
        if self._suppress_events:
            return
        cfg = self._ensure_sections(self.read_settings_config())
        cfg["waybar"]["modules"][module_key] = bool(self.module_switches[module_key].get_active())
        if not self.save_settings_config(cfg):
            return
        ok_apply, _msg, generated = apply_waybar_modules(cfg)
        if ok_apply:
            self.reload_waybar(generated)
            self.set_status(t("appearance.module_saved", "Module settings saved."), "success")
        else:
            self.set_status(t("appearance.module_apply_failed", "Module saved, but Waybar update failed."), "warning")

    def on_effect_setting_changed(self, _widget, _pspec=None) -> None:
        if self._suppress_events:
            return
        cfg = self._ensure_sections(self.read_settings_config())
        effects = cfg["effects"]
        blur = effects["blur"]
        opacity = effects["opacity"]
        blur["enabled"] = bool(self.blur_enabled.get_active())
        blur["size"] = int(self.blur_size_values[self.blur_size.get_selected()])
        blur["passes"] = int(self.blur_passes_values[self.blur_passes.get_selected()])
        opacity["active"] = float(self.opacity_active_values[self.opacity_active.get_selected()])
        opacity["inactive"] = float(self.opacity_inactive_values[self.opacity_inactive.get_selected()])
        effects["lockscreen_blur"] = bool(self.lockscreen_blur.get_active())
        if self.save_settings_config(cfg):
            ok, _msg = apply_hypr_effects(cfg)
            if ok:
                self.set_status(t("appearance.effects_saved", "Effects settings saved."), "info")
            else:
                self.set_status(t("appearance.effects_apply_failed", "Effects saved, but Hyprland apply failed."), "warning")

    def _build_theme_css(self, theme_id: str, accent: str) -> str:
        p = THEME_PALETTES.get(theme_id, THEME_PALETTES["neon-purple"])
        return f"""/* generated-theme:{theme_id} */
@define-color accent {p["accent"]};
@define-color bg {p["bg"]};
@define-color fg {p["fg"]};
@define-color fg_bright #ffffff;
@define-color fg_dim rgba(229, 231, 235, 0.72);
@define-color purple {p["violet"]};
@define-color cyan {p["cyan"]};
@define-color red {p["red"]};
@define-color yellow {p["yellow"]};
@define-color blue {p["blue"]};
@define-color green {p["green"]};
@define-color violet {p["violet"]};
@define-color tooltip_bg rgba(8, 10, 14, 0.96);
@define-color tooltip_border rgba(255, 255, 255, 0.20);
@define-color ws_hover rgba(255, 255, 255, 0.14);
@define-color ws_active_start {p["accent"]};
@define-color ws_active_end {p["cyan"]};
@define-color ws_urgent rgba(239, 68, 68, 0.30);
@define-color clock_border rgba(255, 255, 255, 0.24);
"""

    def ensure_theme_files_installed(self) -> None:
        THEMES_DIR.mkdir(parents=True, exist_ok=True)
        for theme in THEMES:
            filename = str(theme["file"])
            target = THEMES_DIR / filename
            repo_source = REPO_THEMES_DIR / filename
            try:
                if filename in THEME_REPO_FILES and repo_source.exists() and not target.exists():
                    shutil.copy2(repo_source, target)
                else:
                    target.write_text(self._build_theme_css(str(theme["id"]), str(theme["accent"])), encoding="utf-8")
            except Exception:
                continue
        self.ensure_panel_mode_import()
        cfg = self._ensure_sections(self.read_settings_config())
        mode = str(cfg.get("appearance", {}).get("panel", {}).get("background_mode", "solid"))
        self.apply_panel_mode_to_waybar(mode)
        self.apply_lockscreen_config(cfg)

    def ensure_panel_mode_import(self) -> None:
        style_path = Path.home() / ".config/waybar/style.css"
        if not style_path.exists():
            style_path = Path(__file__).resolve().parents[4] / "config/waybar/style.css"
        try:
            content = style_path.read_text(encoding="utf-8")
        except Exception:
            return
        marker = '@import "themes/panel-mode.css";'
        if marker in content:
            return
        try:
            style_path.write_text(marker + "\n" + content, encoding="utf-8")
        except Exception:
            return

    def apply_panel_mode_to_waybar(self, mode: str) -> None:
        normalized = mode if mode in PANEL_BACKGROUND_MODES else "solid"
        if normalized == "transparent":
            css = """/* generated panel mode */
window#waybar {
  background: transparent;
}
#custom-launcher, #workspaces, #window, #clock, #custom-media, #pulseaudio, #network, #battery, #tray, #custom-settings, #custom-power, #backlight, #bluetooth {
  background: transparent;
  border-color: transparent;
}
"""
        elif normalized == "blur":
            css = """/* generated panel mode */
window#waybar {
  background: rgba(0, 0, 0, 0.20);
}
#custom-launcher, #workspaces, #window, #clock, #custom-media, #pulseaudio, #network, #battery, #tray, #custom-settings, #custom-power, #backlight, #bluetooth {
  background: rgba(0, 0, 0, 0.28);
  border-color: @accent;
}
"""
        else:
            css = """/* generated panel mode */
window#waybar {
  background: transparent;
}
#custom-launcher, #workspaces, #window, #clock, #custom-media, #pulseaudio, #network, #battery, #tray, #custom-settings, #custom-power, #backlight, #bluetooth {
  background: @bg;
  border-color: @accent;
}
"""
        try:
            THEMES_DIR.mkdir(parents=True, exist_ok=True)
            PANEL_MODE_CSS_PATH.write_text(css, encoding="utf-8")
        except Exception:
            return

    def _hex_to_rgb_token(self, value: str) -> str:
        cleaned = value.strip().lstrip("#")
        if len(cleaned) == 6:
            return cleaned.lower()
        return "e5e7eb"

    def _palette_bg_token(self, value: str) -> str:
        raw = value.strip()
        if raw.startswith("#"):
            return self._hex_to_rgb_token(raw)
        if raw.startswith("rgba(") or raw.startswith("rgb("):
            inside = raw[raw.find("(") + 1 : raw.find(")")]
            first_three = [part.strip() for part in inside.split(",")[:3]]
            if len(first_three) == 3:
                try:
                    nums = [max(0, min(255, int(float(x)))) for x in first_three]
                    return "".join(f"{n:02x}" for n in nums)
                except Exception:
                    return "111827"
        return "111827"

    def apply_lockscreen_config(self, cfg: dict) -> None:
        # Hyprlock config qo'lda yozilgan neon-anime style bo'lsa,
        # settings app uni qayta buzib yozmasin.
        return

    def trigger_global_theme_sync(self) -> None:
        script_candidates = [
            Path.home() / ".local/bin/arch-hypr-apply-theme",
            Path(__file__).resolve().parents[4] / "scripts/ui/apply-global-theme.sh",
        ]
        for sync_script in script_candidates:
            if not sync_script.exists():
                continue
            try:
                subprocess.Popen(["sh", "-lc", str(sync_script)])
                return
            except Exception:
                continue
        return

    def _get_waybar_config_path(self) -> Path:
        home_cfg = Path.home() / ".config/waybar/config.jsonc"
        if home_cfg.exists():
            return home_cfg
        return Path(__file__).resolve().parents[4] / "config/waybar/config.jsonc"

    def apply_modules_to_waybar_config(self, module_state: dict) -> bool:
        cfg = self._ensure_sections(self.read_settings_config())
        cfg["waybar"]["modules"] = module_state if isinstance(module_state, dict) else {}
        ok, _msg, _generated = apply_waybar_modules(cfg)
        return ok

    def on_reset_appearance_clicked(self, _button: Gtk.Button) -> None:
        cfg = self._ensure_sections(self.read_settings_config())
        cfg["appearance"] = {
            "font": {"terminal": FONT_PRESETS[0], "ui": FONT_PRESETS[0], "waybar": FONT_PRESETS[0]},
            "panel": {"background_mode": "solid"},
            "lockscreen": {
                "layout": "center",
                "show_greeting": True,
                "show_clock": True,
                "show_date": True,
                "show_power_hint": True,
            },
        }
        cfg["effects"] = {"blur": {"enabled": True, "size": 4, "passes": 2}, "opacity": {"active": 1.0, "inactive": 0.85}, "lockscreen_blur": True}
        if self.save_settings_config(cfg):
            self.apply_panel_mode_to_waybar("solid")
            self.apply_lockscreen_config(cfg)
            self._init_form_values()
            self.set_status(t("appearance.reset_done", "Appearance settings reset."), "warning")

    def reload_waybar(self, config_path: Path | None = None) -> None:
        ok, _msg = reload_waybar_runtime(config_path)
        if ok:
            self.set_status(t("appearance.waybar_reload_sent", "Waybar reload command sent."), "info")
        else:
            self.set_status(t("appearance.waybar_reload_failed", "Waybar reload failed"), "error")

    def open_path(self, path: Path) -> None:
        try:
            subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            self.set_status(f"{t('appearance.open_failed', 'Open failed')}: {exc}", "error")

    def open_kitty_config(self) -> None:
        kitty_path = Path.home() / ".config/kitty/kitty.conf"
        try:
            subprocess.Popen(["xdg-open", str(kitty_path)])
        except Exception:
            try:
                subprocess.Popen(["sh", "-lc", f"${{EDITOR:-nano}} \"{kitty_path}\""])
            except Exception as exc:
                self.set_status(f"{t('appearance.open_kitty_failed', 'Open kitty config failed')}: {exc}", "error")
