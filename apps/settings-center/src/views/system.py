import platform
import shutil
import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GLib, Gtk

from services.locale_service import t

LOCAL_VERSION_PATH = Path.home() / ".local/share/arch-hyprland/VERSION"
REPO_VERSION_PATH = Path(__file__).resolve().parents[4] / "VERSION"


class SystemPage(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_vexpand(True)

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('system.title', 'System')}</span>")
        subtitle = Gtk.Label(label=t("system.subtitle", "Maintenance, diagnostics, and system actions."), xalign=0)
        subtitle.add_css_class("dim-label")

        self.status_label = Gtk.Label(label="", xalign=0)
        self.status_label.add_css_class("dim-label")

        self.doctor_buffer = Gtk.TextBuffer()
        self.service_labels: dict[str, Gtk.Label] = {}
        self.project_version_label = Gtk.Label(label=t("system.project_version_unknown", "Project version: Unknown"), xalign=0)
        self.hyprland_version_label = Gtk.Label(label=t("system.hyprland_unknown", "Hyprland: Unknown"), xalign=0)
        self.kernel_label = Gtk.Label(label=f"{t('system.kernel', 'Kernel')}: {platform.uname().release}", xalign=0)
        for lbl in [self.project_version_label, self.hyprland_version_label, self.kernel_label]:
            lbl.add_css_class("dim-label")

        cards = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        cards.append(self._build_health_card())
        cards.append(self._build_maintenance_card())
        cards.append(self._build_services_card())
        cards.append(self._build_logs_card())
        cards.append(self._build_version_card())

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_hexpand(True)
        scroller.set_child(cards)

        self.append(title)
        self.append(subtitle)
        self.append(self.status_label)
        self.append(scroller)

        self.refresh_service_status()
        self.refresh_versions()

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

    def _build_health_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("system.health_check", "Health Check"), xalign=0)
        heading.add_css_class("heading")
        desc = Gtk.Label(label="Run system diagnostics and inspect summary output.", xalign=0)
        desc.add_css_class("dim-label")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        run_btn = Gtk.Button(label=t("system.run_doctor", "Run Doctor"))
        run_btn.connect("clicked", lambda _b: self.run_doctor())
        terminal_btn = Gtk.Button(label=t("system.run_doctor_terminal", "Run Doctor in Terminal"))
        terminal_btn.connect("clicked", lambda _b: self.run_doctor_in_terminal())
        row.append(run_btn)
        row.append(terminal_btn)

        output_view = Gtk.TextView()
        output_view.set_buffer(self.doctor_buffer)
        output_view.set_editable(False)
        output_view.set_cursor_visible(False)
        output_view.set_monospace(True)
        output_scroller = Gtk.ScrolledWindow()
        output_scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        output_scroller.set_min_content_height(140)
        output_scroller.set_child(output_view)

        box.append(heading)
        box.append(desc)
        box.append(row)
        box.append(output_scroller)
        frame.set_child(box)
        return frame

    def _build_maintenance_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("system.maintenance", "Maintenance"), xalign=0)
        heading.add_css_class("heading")
        desc = Gtk.Label(label="Backup, restore, update, and reload core services.", xalign=0)
        desc.add_css_class("dim-label")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        backup_btn = Gtk.Button(label=t("system.create_backup", "Create Backup"))
        backup_btn.connect("clicked", lambda _b: self.run_terminal_command(["arch-hypr-backup"], "Backup started"))
        restore_btn = Gtk.Button(label=t("system.restore_backup", "Restore Latest Backup"))
        restore_btn.connect("clicked", lambda _b: self.run_terminal_command(["arch-hypr-restore"], "Restore started"))
        update_btn = Gtk.Button(label=t("system.update", "Update Setup"))
        update_btn.connect("clicked", lambda _b: self.run_terminal_command(["arch-hypr-update"], "Update started"))
        reload_btn = Gtk.Button(label=t("system.reload_hyprland", "Reload Hyprland"))
        reload_btn.connect("clicked", lambda _b: self.run_background_command(["hyprctl", "reload"], "Hyprland reload sent"))
        row.append(backup_btn)
        row.append(restore_btn)
        row.append(update_btn)
        row.append(reload_btn)

        box.append(heading)
        box.append(desc)
        box.append(row)
        frame.set_child(box)
        return frame

    def _build_services_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("system.services", "Services"), xalign=0)
        heading.add_css_class("heading")

        for key in ["NetworkManager", "bluetooth", "pipewire", "hyprpaper", "mpvpaper", "waybar"]:
            lbl = Gtk.Label(label=f"{key}: Unknown", xalign=0)
            lbl.add_css_class("dim-label")
            self.service_labels[key] = lbl
            box.append(lbl)

        refresh_btn = Gtk.Button(label=t("common.refresh", "Refresh"))
        refresh_btn.connect("clicked", lambda _b: self.refresh_service_status())

        box.append(refresh_btn)
        frame.set_child(box)
        return frame

    def _build_logs_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("system.logs", "Logs"), xalign=0)
        heading.add_css_class("heading")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hypr_logs = Gtk.Button(label=t("system.hyprland_logs", "Hyprland logs"))
        hypr_logs.connect("clicked", lambda _b: self.run_terminal_shell("hyprctl logs | tail -n 120", "Opened Hyprland logs"))
        waybar_logs = Gtk.Button(label=t("system.waybar_logs", "Waybar logs"))
        waybar_logs.connect("clicked", lambda _b: self.run_terminal_shell("pgrep -fa waybar", "Opened Waybar process logs"))
        open_cfg = Gtk.Button(label=t("system.open_config_folders", "Open config folders"))
        open_cfg.connect("clicked", lambda _b: self.open_path(Path.home() / ".config/hypr"))
        row.append(hypr_logs)
        row.append(waybar_logs)
        row.append(open_cfg)

        box.append(heading)
        box.append(row)
        frame.set_child(box)
        return frame

    def _build_version_card(self) -> Gtk.Widget:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=t("system.version", "Version"), xalign=0)
        heading.add_css_class("heading")
        refresh_btn = Gtk.Button(label=t("system.refresh_versions", "Refresh Versions"))
        refresh_btn.connect("clicked", lambda _b: self.refresh_versions())

        box.append(heading)
        box.append(self.project_version_label)
        box.append(self.hyprland_version_label)
        box.append(self.kernel_label)
        box.append(refresh_btn)
        frame.set_child(box)
        return frame

    def command_exists(self, name: str) -> bool:
        return shutil.which(name) is not None

    def run_background_command(self, command: list[str], ok_message: str) -> None:
        try:
            if not self.command_exists(command[0]):
                self.set_status(f"Missing command: {command[0]}", "error")
                return
            subprocess.Popen(command)
            self.set_status(ok_message, "success")
        except Exception as exc:
            self.set_status(f"Command failed: {exc}", "error")

    def run_terminal_command(self, command: list[str], ok_message: str) -> None:
        if not self.command_exists("kitty"):
            self.set_status("Missing command: kitty", "error")
            return
        try:
            subprocess.Popen(["kitty", "--hold", "-e", *command])
            self.set_status(ok_message, "info")
        except Exception as exc:
            self.set_status(f"Terminal launch failed: {exc}", "error")

    def run_terminal_shell(self, shell_cmd: str, ok_message: str) -> None:
        if not self.command_exists("kitty"):
            self.set_status("Missing command: kitty", "error")
            return
        try:
            subprocess.Popen(["kitty", "--hold", "-e", "sh", "-lc", shell_cmd])
            self.set_status(ok_message, "info")
        except Exception as exc:
            self.set_status(f"Terminal launch failed: {exc}", "error")

    def run_doctor(self) -> None:
        if not self.command_exists("arch-hypr-doctor"):
            self.set_status("Missing command: arch-hypr-doctor", "error")
            return
        self.set_status("Running doctor...", "info")
        self.doctor_buffer.set_text("Running arch-hypr-doctor...\n")

        def worker() -> None:
            try:
                proc = subprocess.Popen(
                    ["arch-hypr-doctor"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                out, _ = proc.communicate(timeout=120)
                output = out if out else "(no output)"
                GLib.idle_add(self.doctor_buffer.set_text, output)
                GLib.idle_add(
                    self.set_status,
                    "Doctor completed" if proc.returncode == 0 else f"Doctor finished with code {proc.returncode}",
                    "success" if proc.returncode == 0 else "warning",
                )
            except Exception as exc:
                GLib.idle_add(self.set_status, f"Doctor failed: {exc}", "error")

        threading.Thread(target=worker, daemon=True).start()

    def run_doctor_in_terminal(self) -> None:
        self.run_terminal_command(["arch-hypr-doctor"], "Opened doctor in terminal")

    def open_path(self, path: Path) -> None:
        try:
            subprocess.Popen(["xdg-open", str(path)])
            self.set_status(f"Opened: {path}", "info")
        except Exception as exc:
            self.set_status(f"Open failed: {exc}", "error")

    def _service_status(self, command: list[str], is_pgrep: bool = False) -> str:
        try:
            proc = subprocess.run(command, capture_output=True, text=True, check=False)
            if is_pgrep:
                return "Running" if proc.returncode == 0 else "Stopped"
            out = (proc.stdout or "").strip().lower()
            if out == "active":
                return "Running"
            if out:
                return "Stopped"
            return "Unknown"
        except Exception:
            return "Unknown"

    def refresh_service_status(self) -> None:
        nm = self._service_status(["systemctl", "is-active", "NetworkManager"])
        bt = self._service_status(["systemctl", "is-active", "bluetooth"])
        pw = self._service_status(["systemctl", "--user", "is-active", "pipewire"])
        hp = self._service_status(["pgrep", "hyprpaper"], is_pgrep=True)
        mpv = self._service_status(["pgrep", "mpvpaper"], is_pgrep=True)
        wb = self._service_status(["pgrep", "waybar"], is_pgrep=True)

        self.service_labels["NetworkManager"].set_label(f"NetworkManager: {nm}")
        self.service_labels["bluetooth"].set_label(f"bluetooth: {bt}")
        self.service_labels["pipewire"].set_label(f"pipewire (user): {pw}")
        self.service_labels["hyprpaper"].set_label(f"hyprpaper: {hp}")
        self.service_labels["mpvpaper"].set_label(f"mpvpaper: {mpv}")
        self.service_labels["waybar"].set_label(f"waybar: {wb}")
        self.set_status(t("system.service_refreshed", "Service status refreshed"), "info")

    def refresh_versions(self) -> None:
        version = "Unknown"
        if LOCAL_VERSION_PATH.exists():
            try:
                version = LOCAL_VERSION_PATH.read_text(encoding="utf-8").strip()
            except Exception:
                version = "Unknown"
        elif REPO_VERSION_PATH.exists():
            try:
                version = REPO_VERSION_PATH.read_text(encoding="utf-8").strip()
            except Exception:
                version = "Unknown"
        self.project_version_label.set_label(f"{t('system.project_version', 'Project version')}: {version}")

        try:
            if self.command_exists("hyprctl"):
                proc = subprocess.run(["hyprctl", "version"], capture_output=True, text=True, check=False)
                line = (proc.stdout or "").strip().splitlines()
                hypr_v = line[0] if line else "Unknown"
            else:
                hypr_v = "hyprctl not found"
        except Exception:
            hypr_v = "Unknown"
        self.hyprland_version_label.set_label(f"{t('system.hyprland', 'Hyprland')}: {hypr_v}")
        self.kernel_label.set_label(f"{t('system.kernel', 'Kernel')}: {platform.uname().release}")
