import getpass
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
from services.locale_service import t


STATE_PATH = Path.home() / ".config/arch-hyprland/wallpaper/state.json"
PREVIEW_DIR = Path.home() / ".local/share/arch-hyprland/wallpapers/previews"


def run_shell(command: str) -> None:
    try:
        subprocess.Popen(["bash", "-lc", command])
    except Exception as exc:
        print(f"[Dashboard] run_shell failed: {command} | error={exc}")


def read_json(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"[Dashboard] read_json failed: {path} | error={exc}")
        return {}


def read_mem_info() -> dict[str, int]:
    info: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, raw = line.split(":", 1)
            num = raw.strip().split()[0]
            if num.isdigit():
                info[key] = int(num)  # kB
    except Exception as exc:
        print(f"[Dashboard] read_mem_info failed: {exc}")
    return info


def get_cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception as exc:
        print(f"[Dashboard] get_cpu_model failed: {exc}")
    return "Unknown CPU"


def _cpu_times() -> tuple[int, int]:
    line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0]
    parts = [int(x) for x in line.split()[1:]]
    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
    total = sum(parts)
    return idle, total


def get_cpu_usage() -> float:
    try:
        idle1, total1 = _cpu_times()
        time.sleep(0.08)
        idle2, total2 = _cpu_times()
        idle_delta = idle2 - idle1
        total_delta = total2 - total1
        if total_delta <= 0:
            return 0.0
        usage = (1.0 - (idle_delta / total_delta)) * 100.0
        return max(0.0, min(100.0, usage))
    except Exception as exc:
        print(f"[Dashboard] get_cpu_usage failed: {exc}")
        return 0.0


def get_ram_usage() -> dict[str, float]:
    mem = read_mem_info()
    total_kb = float(mem.get("MemTotal", 0))
    avail_kb = float(mem.get("MemAvailable", 0))
    used_kb = max(0.0, total_kb - avail_kb)
    percent = (used_kb / total_kb * 100.0) if total_kb > 0 else 0.0
    return {
        "percent": percent,
        "used_gb": used_kb / (1024 * 1024),
        "total_gb": total_kb / (1024 * 1024),
    }


def get_disk_usage() -> dict[str, float]:
    try:
        total, used, _free = shutil.disk_usage("/")
        percent = (used / total * 100.0) if total > 0 else 0.0
        return {
            "percent": percent,
            "used_gb": used / (1024**3),
            "total_gb": total / (1024**3),
        }
    except Exception as exc:
        print(f"[Dashboard] get_disk_usage failed: {exc}")
        return {"percent": 0.0, "used_gb": 0.0, "total_gb": 0.0}


def get_battery() -> dict[str, object]:
    power = Path("/sys/class/power_supply")
    if not power.is_dir():
        return {"available": False}
    try:
        for bat_dir in power.glob("BAT*"):
            cap_file = bat_dir / "capacity"
            if cap_file.is_file():
                cap_raw = cap_file.read_text(encoding="utf-8").strip()
                if cap_raw.isdigit():
                    return {"available": True, "percent": float(cap_raw)}
    except Exception as exc:
        print(f"[Dashboard] get_battery failed: {exc}")
    return {"available": False}


def get_uptime() -> str:
    try:
        raw = Path("/proc/uptime").read_text(encoding="utf-8").split()[0]
        sec = int(float(raw))
        days, sec = divmod(sec, 86400)
        hours, sec = divmod(sec, 3600)
        mins, _sec = divmod(sec, 60)
        if days > 0:
            return f"{days}d {hours}h {mins}m"
        return f"{hours}h {mins}m"
    except Exception as exc:
        print(f"[Dashboard] get_uptime failed: {exc}")
        return "-"


def get_video_preview(video_path: Path) -> str:
    if not video_path.is_file():
        return ""
    try:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(str(video_path).encode("utf-8")).hexdigest()[:16]
        thumb = PREVIEW_DIR / f"dash-video-{key}.jpg"
        if thumb.exists():
            return str(thumb)

        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-vf",
            "scale=520:-1",
            str(thumb),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return str(thumb) if thumb.exists() else ""
    except Exception as exc:
        print(f"[Dashboard] get_video_preview failed: {video_path} | error={exc}")
        return ""


def _cmd_ok(command: str) -> bool:
    try:
        res = subprocess.run(["bash", "-lc", command], capture_output=True, timeout=1.2)
        return res.returncode == 0
    except Exception:
        return False


def get_service_status() -> dict[str, str]:
    statuses: dict[str, str] = {}
    statuses["Hyprland"] = "Running" if _cmd_ok("pgrep -x Hyprland >/dev/null 2>&1") else "Stopped"
    statuses["Waybar"] = "Running" if _cmd_ok("pgrep -x waybar >/dev/null 2>&1") else "Stopped"
    statuses["Hyprpaper"] = "Running" if _cmd_ok("pgrep -x hyprpaper >/dev/null 2>&1") else "Stopped"
    statuses["NetworkManager"] = "Running" if _cmd_ok("systemctl is-active --quiet NetworkManager") else "Stopped"
    statuses["Bluetooth"] = "Running" if _cmd_ok("systemctl is-active --quiet bluetooth") else "Stopped"
    statuses["PipeWire"] = "Running" if _cmd_ok("systemctl --user is-active --quiet pipewire") else "Stopped"
    return statuses


class DashboardPage(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)

        self.hero_card = self.make_card("")
        self.overview_card = self.make_card(f"󰍛 {t('dashboard.system_overview', 'System Overview')}")
        self.services_card = self.make_card(f"󰒋 {t('dashboard.services', 'Services')}")
        self.wallpaper_card = self.make_card(f"󰸉 {t('dashboard.current_wallpaper', 'Current Wallpaper')}")
        self.actions_card = self.make_card(f"󰐕 {t('dashboard.quick_actions', 'Quick Actions')}")

        content = Gtk.Grid()
        content.set_row_spacing(12)
        content.set_column_spacing(12)
        content.set_hexpand(True)
        content.set_vexpand(True)

        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_col.append(self.overview_card)
        left_col.append(self.services_card)

        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_col.append(self.wallpaper_card)
        right_col.append(self.actions_card)

        content.attach(left_col, 0, 0, 1, 1)
        content.attach(right_col, 1, 0, 1, 1)

        self.append(self.hero_card)
        self.append(content)

        self.refresh_dashboard()

    def make_card(self, heading: str) -> Gtk.Frame:
        frame = Gtk.Frame()
        frame.set_hexpand(True)
        frame.set_vexpand(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(14)
        box.set_margin_bottom(14)
        box.set_margin_start(14)
        box.set_margin_end(14)
        frame.set_child(box)

        if heading:
            h = Gtk.Label(label=heading, xalign=0)
            h.add_css_class("title-4")
            box.append(h)

        frame.content = box  # type: ignore[attr-defined]
        return frame

    def make_metric_card(self, name: str, value_text: str, percent: float | None = None) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        n = Gtk.Label(label=name, xalign=0)
        n.set_hexpand(True)
        v = Gtk.Label(label=value_text, xalign=1)
        v.add_css_class("dim-label")
        top.append(n)
        top.append(v)
        row.append(top)

        if percent is not None:
            bar = Gtk.LevelBar()
            bar.set_min_value(0.0)
            bar.set_max_value(100.0)
            bar.set_value(max(0.0, min(100.0, percent)))
            row.append(bar)
        return row

    def make_action_button(self, label: str, command: str | None = None, callback=None) -> Gtk.Button:
        btn = Gtk.Button(label=label)
        if callback is not None:
            btn.connect("clicked", callback)
        elif command is not None:
            btn.connect("clicked", lambda _b: run_shell(command))
        return btn

    def open_wallpapers_page(self, _button: Gtk.Button) -> None:
        # Navigate inside Settings Center instead of opening external wofi menu.
        try:
            widget: Gtk.Widget | None = self
            while widget is not None:
                if isinstance(widget, Gtk.Stack):
                    widget.set_visible_child_name("wallpapers")
                    return
                widget = widget.get_parent()
        except Exception as exc:
            print(f"[Dashboard] open_wallpapers_page failed: {exc}")
        print("[Dashboard] Could not find stack parent to open wallpapers page.")

    def _clear_content(self, card: Gtk.Frame) -> Gtk.Box:
        box = card.content  # type: ignore[attr-defined]
        child = box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt
        return box

    def refresh_hero(self) -> None:
        box = self._clear_content(self.hero_card)
        now = datetime.now()
        user = getpass.getuser()
        host = socket.gethostname()

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('dashboard.welcome', 'Welcome to Arch Hyprland')}</span>")

        sub = Gtk.Label(label=t("dashboard.subtitle", "Overview and quick controls"), xalign=0)
        sub.add_css_class("dim-label")

        meta = Gtk.Label(
            label=f"󰃭 {now:%a, %d %b %Y}   󰥔 {now:%H:%M:%S}   󰀄 {user}@{host}",
            xalign=0,
        )
        meta.add_css_class("dim-label")

        box.append(title)
        box.append(sub)
        box.append(meta)

    def refresh_overview(self) -> None:
        box = self._clear_content(self.overview_card)

        uname = platform.uname()
        cpu_model = get_cpu_model()
        cpu_usage = get_cpu_usage()
        ram = get_ram_usage()
        disk = get_disk_usage()
        battery = get_battery()
        session = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")
        uptime = get_uptime()

        box.append(self.make_metric_card("CPU Model", cpu_model))
        box.append(self.make_metric_card("CPU Usage", f"{cpu_usage:.1f}%", cpu_usage))
        box.append(self.make_metric_card("RAM Usage", f"{ram['used_gb']:.1f}/{ram['total_gb']:.1f} GB", ram["percent"]))
        box.append(self.make_metric_card("Disk /", f"{disk['used_gb']:.1f}/{disk['total_gb']:.1f} GB", disk["percent"]))
        if battery.get("available"):
            b = float(battery.get("percent", 0.0))
            box.append(self.make_metric_card("Battery", f"{b:.0f}%", b))
        else:
            miss = Gtk.Label(label="Battery: N/A", xalign=0)
            miss.add_css_class("dim-label")
            box.append(miss)

        box.append(self.make_metric_card("Session", session))
        box.append(self.make_metric_card("Kernel", uname.release))
        box.append(self.make_metric_card("Uptime", uptime))

    def refresh_services(self) -> None:
        box = self._clear_content(self.services_card)
        statuses = get_service_status()

        pill_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pill_row.set_homogeneous(False)

        for name, status in statuses.items():
            pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            pill.add_css_class("card")
            pill.set_margin_top(2)
            pill.set_margin_bottom(2)
            pill.set_margin_start(2)
            pill.set_margin_end(2)

            dot = "●"
            if status == "Running":
                color = "#7bd88f"
            elif status == "Warning":
                color = "#ffd166"
            else:
                color = "#ff6b6b"

            label = Gtk.Label(xalign=0)
            label.set_markup(f"<span foreground='{color}'>{dot}</span> {name}: {status}")
            pill.append(label)
            pill_row.append(pill)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroll.set_child(pill_row)
        box.append(scroll)

    def refresh_wallpaper(self) -> None:
        box = self._clear_content(self.wallpaper_card)
        state = read_json(str(STATE_PATH))

        if not state:
            lbl = Gtk.Label(label=t("dashboard.no_wallpaper_selected", "No wallpaper selected"), xalign=0)
            lbl.add_css_class("dim-label")
            box.append(lbl)
        else:
            current = str(state.get("current", ""))
            provider = str(state.get("provider", "unknown"))
            media_type = str(state.get("type", "unknown"))
            updated = str(state.get("updated_at", "-"))
            file_name = Path(current).name if current else "Unknown"

            box.append(Gtk.Label(label=f"File: {file_name}", xalign=0))
            box.append(Gtk.Label(label=f"Provider: {provider}", xalign=0))
            box.append(Gtk.Label(label=f"Type: {media_type}", xalign=0))
            upd = Gtk.Label(label=f"Updated: {updated}", xalign=0)
            upd.add_css_class("dim-label")
            box.append(upd)

            if media_type == "video":
                preview = get_video_preview(Path(current))
                if preview and Path(preview).is_file():
                    pic = Gtk.Picture.new_for_filename(preview)
                    pic.set_size_request(280, 160)
                    pic.set_content_fit(Gtk.ContentFit.COVER)
                    box.append(pic)
                else:
                    holder = Gtk.Box()
                    holder.set_size_request(280, 140)
                    holder.add_css_class("card")
                    holder.append(Gtk.Label(label=f"󰕧 {t('dashboard.video_wallpaper_active', 'Video wallpaper active')}", xalign=0.5))
                    box.append(holder)
            elif current and Path(current).is_file():
                pic = Gtk.Picture.new_for_filename(current)
                pic.set_size_request(280, 160)
                pic.set_content_fit(Gtk.ContentFit.COVER)
                box.append(pic)
            else:
                miss = Gtk.Label(label=f"Preview unavailable (path missing): {current}", xalign=0)
                miss.add_css_class("dim-label")
                box.append(miss)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.append(self.make_action_button(f"󰸉 {t('dashboard.open_wallpapers_page', 'Open Wallpapers Page')}", callback=self.open_wallpapers_page))
        actions.append(self.make_action_button(f" {t('dashboard.random_wallpaper', 'Random Wallpaper')}", "$HOME/.local/bin/wallpaper-random.sh"))
        box.append(actions)

    def refresh_actions(self) -> None:
        box = self._clear_content(self.actions_card)
        box.append(self.make_action_button(f"󰑓 {t('dashboard.reload_hyprland', 'Reload Hyprland')}", "hyprctl reload"))
        box.append(
            self.make_action_button(
                f"󰑓 {t('dashboard.reload_waybar', 'Reload Waybar')}",
                "pkill waybar || true; sleep 0.5; waybar -c \"$HOME/.config/waybar/config.jsonc\" -s \"$HOME/.config/waybar/style.css\" >/dev/null 2>&1 &",
            )
        )
        box.append(self.make_action_button(f"󰸉 {t('dashboard.open_wallpapers_page', 'Open Wallpapers Page')}", callback=self.open_wallpapers_page))
        box.append(self.make_action_button(f"󰒲 {t('system.run_doctor', 'Run Doctor')}", "kitty --hold -e arch-hypr-doctor"))
        box.append(self.make_action_button(f"󰆓 {t('dashboard.backup', 'Backup')}", "kitty --hold -e arch-hypr-backup"))
        box.append(self.make_action_button(f" {t('dashboard.open_terminal', 'Open Terminal')}", "kitty"))

    def refresh_dashboard(self) -> None:
        self.refresh_hero()
        self.refresh_overview()
        self.refresh_services()
        self.refresh_wallpaper()
        self.refresh_actions()
