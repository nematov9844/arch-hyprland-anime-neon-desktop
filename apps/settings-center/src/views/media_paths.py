import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from services.config_service import (
    DEFAULT_PATHS,
    load_config_with_status,
    update_paths_config,
)
from services.locale_service import t

CARD_META = [
    ("images", "Image Wallpapers Folder", "Local image wallpapers are read from this folder."),
    ("videos", "Video Wallpapers Folder", "Local video wallpapers are read from this folder."),
    ("cache", "Cache Folder", "Downloaded media cache is stored here."),
    ("thumbnails", "Thumbnails Folder", "Generated previews and thumbnails are stored here."),
]


class MediaPathsPage(Gtk.Box):
    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_vexpand(True)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('media_paths.title', 'Media Paths')}</span>")
        subtitle = Gtk.Label(
            label=t("media_paths.subtitle", "Configure local folders for images, videos, cache and thumbnails."),
            xalign=0,
        )
        subtitle.add_css_class("dim-label")
        self.page_status = Gtk.Label(label="", xalign=0)
        self.page_status.add_css_class("dim-label")
        header.append(title)
        header.append(subtitle)
        header.append(self.page_status)
        self.append(header)

        self._cards: dict[str, dict[str, Gtk.Widget]] = {}

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_vexpand(True)
        scroller.set_child(content)
        self.append(scroller)

        for key, label, desc in CARD_META:
            card = self._build_path_card(key, label, desc)
            content.append(card["frame"])
            self._cards[key] = card

        self.reload_from_config()

    def _build_path_card(self, key: str, title: str, description: str) -> dict[str, Gtk.Widget]:
        frame = Gtk.Frame()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        heading = Gtk.Label(label=title, xalign=0)
        heading.add_css_class("heading")

        desc = Gtk.Label(label=description, xalign=0)
        desc.add_css_class("dim-label")
        desc.set_wrap(True)

        entry = Gtk.Entry()
        entry.set_hexpand(True)
        entry.connect("activate", self.on_entry_activate, key)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        browse_btn = Gtk.Button(label=t("media_paths.browse", "Browse"))
        browse_btn.connect("clicked", self.on_browse_clicked, key)
        open_btn = Gtk.Button(label=t("common.open", "Open"))
        open_btn.connect("clicked", self.on_open_clicked, key)
        reset_btn = Gtk.Button(label=t("media_paths.reset_default", "Reset default"))
        reset_btn.connect("clicked", self.on_reset_clicked, key)
        buttons.append(browse_btn)
        buttons.append(open_btn)
        buttons.append(reset_btn)

        status = Gtk.Label(label="", xalign=0)
        status.add_css_class("dim-label")

        box.append(heading)
        box.append(desc)
        box.append(entry)
        box.append(buttons)
        box.append(status)
        frame.set_child(box)

        return {
            "frame": frame,
            "entry": entry,
            "status": status,
        }

    def _expand_path(self, value: str) -> Path:
        return Path(value).expanduser()

    def _user_path(self, value: str | Path) -> str:
        raw = str(value)
        home = str(Path.home())
        if raw.startswith(home):
            return raw.replace(home, "~", 1)
        return raw

    def _load_config(self) -> dict:
        try:
            cfg, had_fallback = load_config_with_status()
            if had_fallback:
                self.page_status.set_label("Config recover qilindi: ba'zi qiymatlar defaultga qaytdi.")
            return cfg
        except Exception as exc:
            self.page_status.set_label(f"Config load failed: {exc}")
            return {}

    def _read_paths(self) -> dict[str, str]:
        cfg = self._load_config()
        paths = cfg.get("paths", {})
        out: dict[str, str] = {}
        for key, default_val in DEFAULT_PATHS.items():
            if isinstance(paths, dict) and key in paths and str(paths.get(key, "")).strip():
                out[key] = str(paths[key]).strip()
            else:
                out[key] = default_val
        return out

    def reload_from_config(self) -> None:
        paths = self._read_paths()
        for key, card in self._cards.items():
            entry = card["entry"]
            status = card["status"]
            value = paths.get(key, DEFAULT_PATHS[key])
            entry.set_text(value)
            resolved = self._expand_path(value)
            status.set_label(
                t("media_paths.folder_exists", "Folder exists")
                if resolved.is_dir()
                else t("media_paths.folder_missing", "Folder missing")
            )

    def _save_path(self, key: str, raw_path: str) -> None:
        path_text = raw_path.strip()
        if not path_text:
            self._cards[key]["status"].set_label(t("media_paths.path_empty", "Path is empty"))
            return

        target = self._expand_path(path_text)
        try:
            created = False
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
                created = True
        except Exception as exc:
            self._cards[key]["status"].set_label(f"Failed to create folder: {exc}")
            return

        try:
            update_paths_config(key, self._user_path(target))
        except Exception:
            self._cards[key]["status"].set_label(t("common.save_failed", "Failed to save config"))
            return

        self._cards[key]["entry"].set_text(self._user_path(target))
        self._cards[key]["status"].set_label(
            t("media_paths.folder_created", "Folder created")
            if created
            else t("media_paths.folder_exists", "Folder exists")
        )

    def on_entry_activate(self, entry: Gtk.Entry, key: str) -> None:
        self._save_path(key, entry.get_text())

    def on_open_clicked(self, _button: Gtk.Button, key: str) -> None:
        entry = self._cards[key]["entry"]
        status = self._cards[key]["status"]
        path = self._expand_path(entry.get_text())
        if not path.exists():
            status.set_label(t("media_paths.folder_not_exists", "Folder does not exist"))
            return
        try:
            subprocess.Popen(["xdg-open", str(path)])
            status.set_label(t("media_paths.opened_folder", "Opened folder"))
        except Exception as exc:
            status.set_label(f"Open failed: {exc}")

    def on_reset_clicked(self, _button: Gtk.Button, key: str) -> None:
        self._save_path(key, DEFAULT_PATHS[key])

    def on_browse_clicked(self, _button: Gtk.Button, key: str) -> None:
        file_dialog_cls = getattr(Gtk, "FileDialog", None)
        if file_dialog_cls is not None:
            try:
                dialog = file_dialog_cls()

                def on_done(dlg: Gtk.FileDialog, result: object) -> None:
                    try:
                        folder = dlg.select_folder_finish(result)
                    except Exception:
                        self._cards[key]["status"].set_label(t("media_paths.selection_cancelled", "Folder selection cancelled"))
                        return
                    if folder is None:
                        self._cards[key]["status"].set_label(t("media_paths.selection_cancelled", "Folder selection cancelled"))
                        return
                    path = folder.get_path()
                    if path:
                        self._save_path(key, path)

                dialog.select_folder(self.get_root(), None, on_done)
                return
            except Exception:
                # Fall back to FileChooserNative on older PyGObject builds.
                pass

        chooser = Gtk.FileChooserNative.new(
            t("media_paths.select_folder", "Select Folder"),
            self.get_root(),
            Gtk.FileChooserAction.SELECT_FOLDER,
            t("common.select", "Select"),
            t("common.cancel", "Cancel"),
        )

        def on_response(native: Gtk.FileChooserNative, response: int) -> None:
            if response != Gtk.ResponseType.ACCEPT:
                self._cards[key]["status"].set_label(t("media_paths.selection_cancelled", "Folder selection cancelled"))
                native.destroy()
                return
            selected = native.get_file()
            path = selected.get_path() if selected else None
            if path:
                self._save_path(key, path)
            else:
                self._cards[key]["status"].set_label(t("media_paths.invalid_selection", "Invalid folder selection"))
            native.destroy()

        chooser.connect("response", on_response)
        chooser.show()
