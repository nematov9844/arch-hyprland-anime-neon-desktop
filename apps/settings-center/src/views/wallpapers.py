import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GLib, Gtk
from services.config_service import load_config
from services.job_controller import JobController
from services.locale_service import t
from services.wallpaper_service import (
    download_image_to_library,
    download_video_to_live,
    fetch_thumbnail,
    get_pexels_api_key,
    get_pixabay_api_key,
    get_unsplash_api_key,
    list_local_videos,
    list_local_wallpapers,
    search_pexels,
    search_pexels_videos,
    search_pixabay,
    search_unsplash,
    search_wallhaven,
)


class WallpapersPage(Gtk.Box):
    def __init__(self, on_navigate=None) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_navigate = on_navigate
        self.set_vexpand(True)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='xx-large' weight='bold'>{t('wallpapers.title', 'Wallpapers')}</span>")
        subtitle = Gtk.Label(label=t("wallpapers.subtitle", "Browse, preview and apply wallpapers."), xalign=0)
        subtitle.add_css_class("dim-label")
        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status = Gtk.Label(label="", xalign=0)
        self.status.set_hexpand(True)
        self.status.add_css_class("dim-label")
        self.cancel_button = Gtk.Button(label=t("common.cancel", "Cancel"))
        self.cancel_button.set_sensitive(False)
        self.cancel_button.set_visible(False)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        status_row.append(self.status)
        status_row.append(self.cancel_button)
        header.append(title)
        header.append(subtitle)
        header.append(status_row)

        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text(t("wallpapers.search_placeholder", "Search wallpapers..."))
        self.search.set_hexpand(True)
        self.search.connect("activate", self.on_search_clicked)

        self.search_button = Gtk.Button()
        self.search_button.set_icon_name("system-search-symbolic")
        self.search_button.add_css_class("suggested-action")
        self.search_button.connect("clicked", self.on_search_clicked)

        self.media_options = [("photo", "Photo"), ("video", "Video")]
        self.media = Gtk.DropDown.new_from_strings([x[1] for x in self.media_options])
        self.media.connect("notify::selected", self.on_media_changed)

        self.photo_category_options = [
            "General",
            "Anime",
            "People",
            "Nature",
            "Sci-Fi",
            "Minimal",
            "Abstract",
            "City",
            "Dark",
            "Aesthetic",
        ]
        self.video_category_options = [
            "General",
            "Anime",
            "Nature",
            "City",
            "Sci-Fi",
            "Dark",
            "Aesthetic",
            "Loop",
        ]
        self.category_options = list(self.photo_category_options)
        self.category = Gtk.DropDown.new_from_strings(self.category_options)
        self.category.connect("notify::selected", self.on_category_changed)

        self.per_page_options = ["12", "24", "48"]
        self.per_page = Gtk.DropDown.new_from_strings(self.per_page_options)
        self.per_page.connect("notify::selected", self.on_per_page_changed)

        self.providers_hint = Gtk.Label(label=t("wallpapers.providers_hint", "Enable more providers from Providers page."), xalign=0)
        self.providers_hint.add_css_class("dim-label")

        search_row.append(self.search)
        search_row.append(self.search_button)

        filter_scroller = Gtk.ScrolledWindow()
        filter_scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        filter_scroller.set_hexpand(True)
        filter_scroller.set_min_content_height(48)
        filter_scroller.set_child(self.filter_row)

        controls.append(search_row)
        controls.append(filter_scroller)
        controls.append(self.providers_hint)

        pager = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.prev_button = Gtk.Button(label=t("common.prev", "Prev"))
        self.prev_button.connect("clicked", self.on_prev_page_clicked)
        self.page_label = Gtk.Label(label="Page 1/1")
        self.next_button = Gtk.Button(label=t("common.next", "Next"))
        self.next_button.connect("clicked", self.on_next_page_clicked)
        pager.append(self.prev_button)
        pager.append(self.page_label)
        pager.append(self.next_button)

        self.grid = Gtk.FlowBox()
        self.grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.grid.set_min_children_per_line(4)
        self.grid.set_max_children_per_line(4)
        self.grid.set_row_spacing(12)
        self.grid.set_column_spacing(12)
        self.grid.set_valign(Gtk.Align.START)
        self.grid.set_homogeneous(True)

        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_vexpand(True)
        self.scroller.set_hexpand(True)
        self.scroller.set_child(self.grid)

        self.append(header)
        self.append(controls)
        self.append(pager)
        self.append(self.scroller)
        self.pager = pager

        self.loading = False
        self._suppress_events = True
        self.job_controller = JobController()
        self.thumb_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="thumb")
        self.apply_buttons: list[Gtk.Button] = []
        self.wallhaven_page = 1
        self.wallhaven_end_page = 1
        self.wallhaven_last_page = 1
        self.local_page = 1
        self.local_last_page = 1
        self.local_items: list[dict[str, str]] = []
        self._current_columns = 0
        GLib.timeout_add(700, self.poll_grid_columns)

        self.provider_options: list[tuple[str, str]] = []
        self.provider = Gtk.DropDown.new_from_strings(["Local"])
        self.provider.connect("notify::selected", self.on_provider_changed)
        self.rebuild_filter_row()
        self.media.set_selected(0)
        self.category.set_selected(0)
        self.per_page.set_selected(0)
        self.rebuild_provider_dropdown()
        self._suppress_events = False
        self.update_provider_dependent_controls()
        self.load_local_results()

    # -------- Config/provider helpers --------
    def read_config(self) -> dict:
        try:
            raw = load_config()
            return raw if isinstance(raw, dict) else {}
        except Exception:
            return {}

    def has_api_key(self, provider: str) -> bool:
        cfg = self.read_config()
        section = cfg.get(provider, {})
        if not isinstance(section, dict):
            return False
        return bool(str(section.get("api_key", "")).strip())

    def provider_enabled(self, provider: str) -> bool:
        cfg = self.read_config()
        section = cfg.get(provider, {})
        if not isinstance(section, dict):
            return False
        return bool(section.get("enabled", False))

    def get_available_providers(self, media_type: str) -> list[tuple[str, str]]:
        # UX talabi bo'yicha provider nomlari doim ko'rinadi.
        # API key yoki enabled bo'lmasa search paytida foydali xabar beriladi.
        if media_type == "video":
            return [
                ("local-video", "Local"),
                ("pexels-video", "Pexels"),
            ]
        return [
            ("local", "Local"),
            ("wallhaven", "Wallhaven"),
            ("pexels", "Pexels"),
            ("unsplash", "Unsplash"),
            ("pixabay", "Pixabay"),
        ]

    def rebuild_provider_dropdown(self) -> None:
        media_type = self.current_media_type()
        self.provider_options = self.get_available_providers(media_type)
        if not self.provider_options:
            # safety fallback
            fallback = ("local-video", "Local") if media_type == "video" else ("local", "Local")
            self.provider_options = [fallback]

        labels = [label for _pid, label in self.provider_options]
        self.provider = Gtk.DropDown.new_from_strings(labels)
        self.provider.set_selected(0)
        self.provider.connect("notify::selected", self.on_provider_changed)
        self.rebuild_filter_row()

        if len(self.provider_options) == 1 and self.provider_options[0][1] == "Local":
            self.providers_hint.set_label(t("wallpapers.only_local", "Only Local is available. Enable more providers from Providers page."))
        else:
            self.providers_hint.set_label(t("wallpapers.providers_hint", "Enable more providers from Providers page."))

    # -------- UI helpers --------
    def rebuild_filter_row(self) -> None:
        while True:
            child = self.filter_row.get_first_child()
            if child is None:
                break
            self.filter_row.remove(child)
        self.filter_row.append(self.media)
        self.filter_row.append(self.provider)
        self.filter_row.append(self.category)
        self.filter_row.append(self.per_page)

    def rebuild_category_dropdown(self) -> None:
        media_type = self.current_media_type()
        self.category_options = list(self.video_category_options if media_type == "video" else self.photo_category_options)
        selected = self.category.get_selected()
        self.category = Gtk.DropDown.new_from_strings(self.category_options)
        if 0 <= selected < len(self.category_options):
            self.category.set_selected(selected)
        else:
            self.category.set_selected(0)
        self.category.connect("notify::selected", self.on_category_changed)
        self.rebuild_filter_row()

    def refresh_grid_columns(self, width: int) -> None:
        columns = 4
        if width >= 1700:
            columns = 5
        elif width >= 1300:
            columns = 4
        elif width >= 980:
            columns = 3
        elif width >= 700:
            columns = 2
        else:
            columns = 1
        if columns != self._current_columns:
            self._current_columns = columns
            self.grid.set_min_children_per_line(columns)
            self.grid.set_max_children_per_line(columns)

    def poll_grid_columns(self) -> bool:
        self.refresh_grid_columns(self.scroller.get_allocated_width())
        return True

    def clear_grid(self) -> None:
        child = self.grid.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.grid.remove(child)
            child = nxt

    def show_empty_state(self, message: str) -> None:
        self.show_message_state(t("common.empty", "Empty"), message)

    def set_status(self, message: str, level: str = "info") -> None:
        self.status.set_label(message)
        for css in ("success", "warning", "error", "dim-label"):
            self.status.remove_css_class(css)
        if level == "success":
            self.status.add_css_class("success")
        elif level == "warning":
            self.status.add_css_class("warning")
        elif level == "error":
            self.status.add_css_class("error")
        else:
            self.status.add_css_class("dim-label")

    def show_message_state(
        self,
        title: str,
        subtitle: str,
        action_label: str | None = None,
        action_callback=None,
    ) -> None:
        self.clear_grid()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        box.set_size_request(-1, 220)
        title_lbl = Gtk.Label(label=title, xalign=0.5)
        title_lbl.add_css_class("heading")
        subtitle_lbl = Gtk.Label(label=subtitle, xalign=0.5)
        subtitle_lbl.add_css_class("dim-label")
        subtitle_lbl.set_wrap(True)
        box.append(title_lbl)
        box.append(subtitle_lbl)
        if action_label and action_callback:
            btn = Gtk.Button(label=action_label)
            btn.connect("clicked", lambda _b: action_callback())
            box.append(btn)
        self.grid.insert(box, -1)

    def show_loading(self, message: str) -> None:
        self.clear_grid()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        box.set_size_request(-1, 180)
        spinner = Gtk.Spinner()
        spinner.start()
        lbl = Gtk.Label(label=message, xalign=0.5)
        lbl.add_css_class("dim-label")
        box.append(spinner)
        box.append(lbl)
        self.grid.insert(box, -1)

    def make_result_card(self, item: dict[str, str]) -> tuple[Gtk.Widget, Gtk.Picture]:
        frame = Gtk.Frame()
        frame.set_size_request(210, 230)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        thumbnail = item.get("thumbnail_path", "")
        preview = Gtk.Picture()
        preview.set_size_request(186, 124)
        preview.set_content_fit(Gtk.ContentFit.COVER)
        preview.add_css_class("card")
        if thumbnail and Path(thumbnail).is_file():
            preview.set_filename(thumbnail)
        preview_overlay = Gtk.Overlay()
        preview_overlay.set_child(preview)

        loading_revealer = Gtk.Revealer()
        loading_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        loading_revealer.set_reveal_child(False)
        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        loading_box.set_halign(Gtk.Align.CENTER)
        loading_box.set_valign(Gtk.Align.CENTER)
        loading_label = Gtk.Label(label="", xalign=0.5)
        loading_bar = Gtk.ProgressBar()
        loading_bar.set_size_request(128, -1)
        loading_box.append(loading_label)
        loading_box.append(loading_bar)
        loading_revealer.set_child(loading_box)
        preview_overlay.add_overlay(loading_revealer)

        title = Gtk.Label(label=item.get("title", "Untitled"), xalign=0)
        title.set_wrap(True)
        title.set_max_width_chars(28)
        title.set_size_request(-1, 40)

        apply_btn = Gtk.Button(label=t("wallpapers.apply", "Apply"))
        apply_btn.connect("clicked", self.on_apply_clicked, item, apply_btn, loading_revealer, loading_label, loading_bar)
        self.apply_buttons.append(apply_btn)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        box.append(preview_overlay)
        box.append(title)
        box.append(spacer)
        box.append(apply_btn)
        frame.set_child(box)
        return frame, preview

    def resolve_apply_script(self) -> str:
        local_bin = Path.home() / ".local/bin/wallpaper-apply.sh"
        if local_bin.exists():
            return str(local_bin)
        return str(Path(__file__).resolve().parents[4] / "scripts/wallpaper/wallpaper-apply.sh")

    def resolve_video_apply_script(self) -> str:
        local_bin = Path.home() / ".local/bin/wallpaper-video-apply.sh"
        if local_bin.exists():
            return str(local_bin)
        return str(Path(__file__).resolve().parents[4] / "scripts/wallpaper/wallpaper-video-apply.sh")

    # -------- state getters --------
    def current_media_type(self) -> str:
        idx = self.media.get_selected()
        if idx < 0 or idx >= len(self.media_options):
            return "photo"
        return self.media_options[idx][0]

    def current_provider_id(self) -> str:
        idx = self.provider.get_selected()
        if idx < 0 or idx >= len(self.provider_options):
            return "local-video" if self.current_media_type() == "video" else "local"
        return self.provider_options[idx][0]

    def current_provider_label(self) -> str:
        idx = self.provider.get_selected()
        if idx < 0 or idx >= len(self.provider_options):
            return "Local"
        return self.provider_options[idx][1]

    def get_results_limit(self) -> int:
        idx = self.per_page.get_selected()
        if idx < 0 or idx >= len(self.per_page_options):
            return 12
        try:
            return max(12, int(self.per_page_options[idx]))
        except ValueError:
            return 12

    def get_page_step(self) -> int:
        if self.current_provider_id() == "wallhaven":
            return max(1, self.get_results_limit() // 24)
        return 1

    # -------- actions --------
    def on_cancel_clicked(self, _button: Gtk.Button) -> None:
        self.job_controller.request_cancel()
        self.set_status(t("wallpapers.cancel_requested", "Cancellation requested..."), "warning")

    def _set_cancel_ui(self, active: bool) -> None:
        self.cancel_button.set_visible(active)
        self.cancel_button.set_sensitive(active)

    def _open_providers(self) -> None:
        if callable(self.on_navigate):
            self.on_navigate("providers")

    def _open_media_paths(self) -> None:
        if callable(self.on_navigate):
            self.on_navigate("media_paths")

    def on_apply_clicked(
        self,
        _button: Gtk.Button,
        item: dict[str, str],
        apply_btn: Gtk.Button,
        loading_revealer: Gtk.Revealer,
        loading_label: Gtk.Label,
        loading_bar: Gtk.ProgressBar,
    ) -> None:
        job_id = self.job_controller.start_job()
        if job_id is None:
            self.set_status(t("wallpapers.busy_wait", "A job is already running. Please wait."), "warning")
            return
        self.loading = True
        self._set_cancel_ui(True)
        for btn in self.apply_buttons:
            btn.set_sensitive(False)

        provider = item.get("provider", "manual").lower()
        media_type = item.get("media_type", "photo")
        file_path = item.get("file_path", "")
        media_name = item.get("display_name", item.get("title", "media")).strip() or "media"
        is_remote_download = not file_path and provider in {"wallhaven", "pexels", "unsplash", "pixabay"}

        loading_label.set_label("0%" if is_remote_download else t("wallpapers.applying", "Applying"))
        loading_revealer.set_reveal_child(True)
        loading_bar.set_fraction(0.05 if is_remote_download else 0.45)
        self.set_status(
            f"{t('wallpapers.downloading', 'Downloading')}: {media_name}" if is_remote_download else f"{t('wallpapers.applying', 'Applying')}: {media_name}",
            "info",
        )
        apply_btn.set_sensitive(False)

        def worker() -> None:
            try:
                resolved_file_path = file_path
                if not resolved_file_path and is_remote_download:
                    def on_progress(downloaded: int, total: int) -> None:
                        if self.job_controller.should_cancel(job_id):
                            raise RuntimeError("Cancelled")
                        if total > 0:
                            percent = int((downloaded / total) * 100)
                            fraction = min(0.9, max(0.08, percent / 100))
                            GLib.idle_add(loading_bar.set_fraction, fraction)
                            GLib.idle_add(loading_label.set_label, f"{percent}%")
                        else:
                            mb = downloaded / (1024 * 1024)
                            GLib.idle_add(loading_bar.pulse)
                            GLib.idle_add(loading_label.set_label, f"{mb:.1f} MB")

                    if media_type == "video":
                        resolved_file_path = str(
                            download_video_to_live(
                                item.get("image_url", ""),
                                progress_cb=on_progress,
                                should_cancel=lambda: self.job_controller.should_cancel(job_id),
                            )
                        )
                    else:
                        resolved_file_path = str(
                            download_image_to_library(
                                item.get("image_url", ""),
                                progress_cb=on_progress,
                                should_cancel=lambda: self.job_controller.should_cancel(job_id),
                            )
                        )

                if not resolved_file_path:
                    raise RuntimeError("No file path to apply")
                if self.job_controller.should_cancel(job_id):
                    raise RuntimeError("Cancelled")

                GLib.idle_add(loading_label.set_label, t("wallpapers.applying", "Applying"))
                GLib.idle_add(loading_bar.set_fraction, 0.8)
                if media_type == "video":
                    subprocess.run([self.resolve_video_apply_script(), resolved_file_path], check=True)
                else:
                    subprocess.run([self.resolve_apply_script(), resolved_file_path, provider, "image"], check=True)
                GLib.idle_add(self.set_status, f"{t('wallpapers.applied', 'Applied')}: {Path(resolved_file_path).name}", "success")
            except Exception as exc:
                if str(exc).lower() == "cancelled":
                    GLib.idle_add(self.set_status, t("common.cancelled", "Cancelled"), "warning")
                else:
                    GLib.idle_add(self.set_status, f"{t('wallpapers.apply_failed', 'Apply failed')}: {exc}", "error")
            finally:
                self.job_controller.finish_job(job_id)
                GLib.idle_add(loading_bar.set_fraction, 1.0)
                GLib.idle_add(loading_revealer.set_reveal_child, False)
                GLib.idle_add(self.set_loading_done)

        threading.Thread(target=worker, daemon=True).start()

    def on_search_clicked(self, _widget: Gtk.Widget) -> None:
        if self.current_provider_id() in {"local", "local-video"}:
            self.local_page = 1
        else:
            self.wallhaven_page = 1
        self.load_results_async()

    def on_media_changed(self, _dropdown: Gtk.DropDown, _pspec: object) -> None:
        if self._suppress_events:
            return
        self._suppress_events = True
        self.wallhaven_page = 1
        self.local_page = 1
        self.clear_grid()
        self.rebuild_category_dropdown()
        self.rebuild_provider_dropdown()
        self._suppress_events = False
        self.update_provider_dependent_controls()
        self.show_empty_state(t("wallpapers.media_changed", "Media mode changed. Pick provider and search."))

    def on_provider_changed(self, _dropdown: Gtk.DropDown, _pspec: object) -> None:
        if self._suppress_events:
            return
        self.update_provider_dependent_controls()
        self.load_results_async()

    def update_provider_dependent_controls(self) -> None:
        pid = self.current_provider_id()
        is_local = pid in {"local", "local-video"}
        self.category.set_visible(not is_local)
        self.per_page.set_visible(True)
        self.pager.set_visible(True)
        if is_local:
            self.local_page = 1
        self.update_pager_ui()

    def on_category_changed(self, _dropdown: Gtk.DropDown, _pspec: object) -> None:
        if self.current_provider_id() not in {"local", "local-video"}:
            self.wallhaven_page = 1
            self.load_results_async()

    def on_per_page_changed(self, _dropdown: Gtk.DropDown, _pspec: object) -> None:
        if self._suppress_events:
            return
        if self.current_provider_id() in {"local", "local-video"}:
            self.local_page = 1
            self.load_local_results()
        else:
            self.wallhaven_page = 1
            self.load_results_async()

    def on_prev_page_clicked(self, _button: Gtk.Button) -> None:
        if self.loading:
            return
        if self.current_provider_id() in {"local", "local-video"}:
            if self.local_page <= 1:
                return
            self.local_page = max(1, self.local_page - 1)
            self.load_local_results()
            return
        if self.wallhaven_page <= 1:
            return
        self.wallhaven_page = max(1, self.wallhaven_page - self.get_page_step())
        self.load_results_async()

    def on_next_page_clicked(self, _button: Gtk.Button) -> None:
        if self.loading:
            return
        if self.current_provider_id() in {"local", "local-video"}:
            if self.local_page >= self.local_last_page:
                return
            self.local_page += 1
            self.load_local_results()
            return
        if self.wallhaven_end_page >= self.wallhaven_last_page:
            return
        self.wallhaven_page = self.wallhaven_end_page + 1
        self.load_results_async()

    def set_loading_done(self) -> bool:
        self.loading = False
        self._set_cancel_ui(False)
        for btn in self.apply_buttons:
            btn.set_sensitive(True)
        self.update_pager_ui()
        return False

    def update_pager_ui(self) -> None:
        pid = self.current_provider_id()
        is_online = pid not in {"local", "local-video"}
        if is_online:
            self.prev_button.set_sensitive(not self.loading and self.wallhaven_page > 1)
            self.next_button.set_sensitive(not self.loading and self.wallhaven_end_page < self.wallhaven_last_page)
        else:
            self.prev_button.set_sensitive(not self.loading and self.local_page > 1)
            self.next_button.set_sensitive(not self.loading and self.local_page < self.local_last_page)
        if is_online:
            if self.wallhaven_page == self.wallhaven_end_page:
                self.page_label.set_label(f"{t('common.page', 'Page')} {self.wallhaven_page}/{self.wallhaven_last_page}")
            else:
                self.page_label.set_label(
                    f"{t('common.pages', 'Pages')} {self.wallhaven_page}-{self.wallhaven_end_page}/{self.wallhaven_last_page}"
                )
        else:
            self.page_label.set_label(f"{t('wallpapers.local_page', 'Local page')} {self.local_page}/{self.local_last_page}")

    def load_local_results(self) -> None:
        pid = self.current_provider_id()
        query = self.search.get_text().strip()
        all_items = list_local_videos(query=query, limit=5000) if pid == "local-video" else list_local_wallpapers(query=query, limit=5000)
        self.local_items = all_items
        page_size = self.get_results_limit()
        total = len(all_items)
        self.local_last_page = max(1, (total + page_size - 1) // page_size)
        if self.local_page > self.local_last_page:
            self.local_page = self.local_last_page
        start = (self.local_page - 1) * page_size
        end = start + page_size
        items = all_items[start:end]
        self.clear_grid()
        if total == 0:
            title = (
                t("wallpapers.no_video_files", "No video files found")
                if pid == "local-video"
                else t("wallpapers.no_local_media", "No local media found")
            )
            self.show_message_state(
                title,
                t("wallpapers.local_empty_desc", "Local folder is empty. Add media or change paths."),
                t("wallpapers.open_media_paths", "Open Media Paths"),
                self._open_media_paths,
            )
            self.set_status(title, "warning")
            self.update_pager_ui()
            return
        self.set_status(f"Local results: {total} (showing {start + 1}-{min(end, total)})", "info")
        for item in items:
            card, _preview = self.make_result_card(item)
            self.grid.insert(card, -1)
        self.update_pager_ui()

    def _thumbnail_prefetch(self, items: list[dict[str, str]], previews: list[Gtk.Picture]) -> None:
        if not items or not previews:
            return

        def worker(idx: int, thumb_url: str) -> None:
            cached = fetch_thumbnail(thumb_url)
            if not cached or idx >= len(previews):
                return
            GLib.idle_add(previews[idx].set_filename, cached)

        for idx, item in enumerate(items):
            if idx >= len(previews):
                break
            thumb_url = item.get("thumbnail_url", "")
            if not thumb_url:
                continue
            self.thumb_executor.submit(worker, idx, thumb_url)

    def load_results_async(self) -> None:
        if self.loading:
            return

        provider_id = self.current_provider_id()
        provider_label = self.current_provider_label()
        media_type = self.current_media_type()
        query = self.search.get_text().strip()
        category_idx = self.category.get_selected()
        category = self.category_options[category_idx] if 0 <= category_idx < len(self.category_options) else "General"

        if provider_id in {"local", "local-video"}:
            self.load_local_results()
            return

        if provider_id == "pexels" and not get_pexels_api_key():
            self.show_message_state(
                t("providers.api_required", "API key required"),
                t("wallpapers.pexels_key_missing", "Pexels is enabled but API key is missing."),
                t("wallpapers.open_providers", "Open Providers"),
                self._open_providers,
            )
            self.set_status("Pexels API key missing", "warning")
            return
        if provider_id == "unsplash" and not get_unsplash_api_key():
            self.show_message_state(
                t("providers.api_required", "API key required"),
                t("wallpapers.unsplash_key_missing", "Unsplash is enabled but API key is missing."),
                t("wallpapers.open_providers", "Open Providers"),
                self._open_providers,
            )
            self.set_status("Unsplash API key missing", "warning")
            return
        if provider_id == "pixabay" and not get_pixabay_api_key():
            self.show_message_state(
                t("providers.api_required", "API key required"),
                t("wallpapers.pixabay_key_missing", "Pixabay is enabled but API key is missing."),
                t("wallpapers.open_providers", "Open Providers"),
                self._open_providers,
            )
            self.set_status("Pixabay API key missing", "warning")
            return

        self.loading = True
        self.set_status(f"Loading {provider_label}/{category}...", "info")
        self.show_loading(f"{t('wallpapers.loading', 'Loading...')} {provider_label}/{category}...")
        self.update_pager_ui()

        def worker() -> None:
            try:
                if provider_id == "wallhaven":
                    payload = search_wallhaven(query=query, category=category, page=self.wallhaven_page, limit=self.get_results_limit())
                elif provider_id == "pexels":
                    payload = search_pexels(query=query, category=category, page=self.wallhaven_page, limit=self.get_results_limit())
                elif provider_id == "unsplash":
                    payload = search_unsplash(query=query, category=category, page=self.wallhaven_page, limit=self.get_results_limit())
                elif provider_id == "pixabay":
                    payload = search_pixabay(query=query, category=category, page=self.wallhaven_page, limit=self.get_results_limit())
                elif provider_id == "pexels-video":
                    payload = search_pexels_videos(query=query, category=category, page=self.wallhaven_page, limit=self.get_results_limit())
                else:
                    payload = {"items": [], "current_page": 1, "end_page": 1, "last_page": 1}

                items = payload.get("items", [])
                page = int(payload.get("current_page", self.wallhaven_page))
                end_page = int(payload.get("end_page", page))
                last_page = int(payload.get("last_page", self.wallhaven_page))

                GLib.idle_add(self.render_results, provider_label, items, page, end_page, last_page)
            except Exception as exc:
                GLib.idle_add(self.render_error, provider_label, query, str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def render_error(self, provider_name: str, query: str, error: str) -> bool:
        self.clear_grid()
        self.set_status(f"{t('wallpapers.search_error', 'Search error')} ({provider_name}): {error}", "error")
        self.loading = False
        self.show_message_state(
            t("wallpapers.network_or_provider_error", "Network or provider error"),
            t("wallpapers.search_failed_desc", "Search failed. Check internet connection and provider configuration."),
            t("wallpapers.open_providers", "Open Providers"),
            self._open_providers,
        )
        self.update_pager_ui()
        print(f"[Wallpapers] Search error | provider={provider_name} | query={query} | error={error}")
        return False

    def render_results(
        self,
        provider_name: str,
        items: list[dict[str, str]],
        page: int = 1,
        end_page: int = 1,
        last_page: int = 1,
    ) -> bool:
        self.clear_grid()
        self.wallhaven_page = max(1, page)
        self.wallhaven_end_page = max(self.wallhaven_page, end_page)
        self.wallhaven_last_page = max(1, last_page)

        if not items:
            self.set_status(f"{t('wallpapers.no_results', 'No results found')} ({provider_name})", "warning")
            self.loading = False
            self.show_message_state(
                t("wallpapers.no_results_short", "No results"),
                t("wallpapers.no_results_filter", "No results for current provider/filter."),
            )
            self.update_pager_ui()
            return False

        self.set_status(
            f"Results: {len(items)} ({provider_name}) - pages {self.wallhaven_page}-{self.wallhaven_end_page}/{self.wallhaven_last_page}"
            ,
            "info",
        )
        previews: list[Gtk.Picture] = []
        for item in items:
            card, preview = self.make_result_card(item)
            previews.append(preview)
            self.grid.insert(card, -1)
        self._thumbnail_prefetch(items, previews)
        self.loading = False
        self.update_pager_ui()
        return False
