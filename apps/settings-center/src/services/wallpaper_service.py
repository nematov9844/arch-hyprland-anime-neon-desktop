from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
from math import ceil
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

from services.config_service import DEFAULT_PATHS, load_config


SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_VIDEO_EXT = {".mp4", ".webm", ".mkv"}


def _clean_title(value: str, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    text = re.sub(r"\s+", " ", text)
    return text[:88]


def get_wallpaper_dir() -> Path:
    return Path.home() / ".local/share/arch-hyprland/wallpapers"


def get_local_static_dir() -> Path:
    return _configured_path("images", get_wallpaper_dir() / "static")


def get_local_library_dir() -> Path:
    return get_wallpaper_dir() / "library"


def get_cache_dir() -> Path:
    return _configured_path("cache", get_wallpaper_dir() / "cache")


def get_thumbnail_cache_dir() -> Path:
    return _configured_path("thumbnails", get_wallpaper_dir() / "previews")


def get_wallpaper_config_path() -> Path:
    return Path.home() / ".config/arch-hyprland/wallpaper/config.json"


def load_wallpaper_config() -> dict[str, object]:
    return load_config()


def _configured_path(key: str, fallback: Path) -> Path:
    cfg = load_wallpaper_config()
    paths = cfg.get("paths", {})
    if isinstance(paths, dict):
        raw = str(paths.get(key, "")).strip()
        if raw:
            return Path(raw).expanduser()
    return fallback


def get_pexels_api_key() -> str:
    # Env is handy during quick testing without editing config files.
    env_key = os.environ.get("PEXELS_API_KEY", "").strip()
    if env_key:
        return env_key
    cfg = load_wallpaper_config()
    pexels_cfg = cfg.get("pexels", {})
    if isinstance(pexels_cfg, dict):
        return str(pexels_cfg.get("api_key", "")).strip()
    return ""


def get_unsplash_api_key() -> str:
    env_key = os.environ.get("UNSPLASH_API_KEY", "").strip()
    if env_key:
        return env_key
    cfg = load_wallpaper_config()
    section = cfg.get("unsplash", {})
    if isinstance(section, dict):
        return str(section.get("api_key", "")).strip()
    return ""


def get_pixabay_api_key() -> str:
    env_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if env_key:
        return env_key
    cfg = load_wallpaper_config()
    section = cfg.get("pixabay", {})
    if isinstance(section, dict):
        return str(section.get("api_key", "")).strip()
    return ""


def _iter_local_dirs() -> list[Path]:
    return [get_local_static_dir()]


def _iter_local_video_dirs() -> list[Path]:
    return [_configured_path("videos", get_wallpaper_dir() / "live")]


def _video_thumbnail_path(video_path: Path) -> Path:
    previews_dir = get_thumbnail_cache_dir()
    previews_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(str(video_path).encode("utf-8")).hexdigest()[:16]
    return previews_dir / f"video-{key}.jpg"


def get_local_video_thumbnail(video_path: Path) -> str:
    thumb = _video_thumbnail_path(video_path)
    if thumb.exists():
        return str(thumb)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        "00:00:01",
        "-i",
        str(video_path),
        "-vframes",
        "1",
        "-vf",
        "scale=360:-1",
        str(thumb),
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    return str(thumb) if thumb.exists() else ""


def list_local_wallpapers(query: str = "", limit: int = 24) -> list[dict[str, str]]:
    query_l = query.lower().strip()
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for folder in _iter_local_dirs():
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXT:
                continue
            key = path.name.lower()
            if key in seen:
                continue
            seen.add(key)
            name = path.name
            if query_l and query_l not in name.lower():
                continue
            thumb_cache = get_thumbnail_cache_path(str(path))
            items.append(
                {
                    "title": name,
                    "provider": "Local",
                    "file_path": str(path),
                    "thumbnail_path": str(thumb_cache) if thumb_cache.exists() else str(path),
                    "media_type": "photo",
                }
            )
            if len(items) >= limit:
                return items
    return items


def list_local_videos(query: str = "", limit: int = 24) -> list[dict[str, str]]:
    query_l = query.lower().strip()
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for folder in _iter_local_video_dirs():
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_VIDEO_EXT:
                continue
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            name = path.name
            if query_l and query_l not in name.lower():
                continue
            items.append(
                {
                    "title": f"{name} ({folder.name})",
                    "provider": "Local",
                    "file_path": str(path),
                    "thumbnail_path": get_local_video_thumbnail(path),
                    "media_type": "video",
                }
            )
            if len(items) >= limit:
                return items
    return items


def search_wallhaven(
    query: str,
    category: str = "General",
    limit: int = 24,
    page: int = 1,
) -> dict[str, object]:
    category_terms = {
        "General": "",
        "Anime": "anime",
        "People": "portrait character person",
        "Nature": "nature landscape forest mountain",
        "Sci-Fi": "sci-fi cyberpunk futuristic",
        "Minimal": "minimal clean",
        "Abstract": "abstract geometry",
        "City": "city urban night",
        "Dark": "dark moody noir",
        "Aesthetic": "aesthetic vaporwave neon",
    }
    final_query = query.strip() or "anime"
    extra = category_terms.get(category, "")
    if extra and extra.lower() not in final_query.lower():
        final_query = f"{final_query} {extra}"

    start_page = max(1, page)
    # Wallhaven API returns up to 24 results per request, so we aggregate pages.
    pages_to_fetch = max(1, min(3, (limit + 23) // 24))
    items: list[dict[str, str]] = []
    current_page = start_page
    last_page = start_page
    end_page = start_page
    total = 0

    for offset in range(pages_to_fetch):
        request_page = start_page + offset
        params = {
            "q": final_query,
            "sorting": "relevance",
            "purity": "100",
            "categories": "111",
            "page": request_page,
        }
        url = "https://wallhaven.cc/api/v1/search?" + urlencode(params)
        req = Request(url, headers={"User-Agent": "arch-hypr-settings-center/1.0"})

        try:
            with urlopen(req, timeout=12) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except URLError as exc:
            raise RuntimeError(f"Wallhaven request failed: {exc}") from exc

        meta = payload.get("meta", {})
        current_page = int(meta.get("current_page", request_page))
        last_page = int(meta.get("last_page", current_page))
        total = int(meta.get("total", total))
        end_page = current_page

        for row in payload.get("data", []):
            wid = row.get("id", "unknown")
            resolution = row.get("resolution", "")
            image_url = row.get("path", "")
            wall_title = _clean_title(str(row.get("id", "")), f"Wallhaven {wid}")
            items.append(
                {
                    "title": f"{wall_title} ({resolution})",
                    "provider": "Wallhaven",
                    "image_url": image_url,
                    "thumbnail_url": (row.get("thumbs") or {}).get("small", ""),
                    "media_type": "photo",
                }
            )
            if len(items) >= limit:
                break

        if len(items) >= limit or current_page >= last_page:
            break

    return {
        "items": items,
        "current_page": start_page,
        "end_page": end_page,
        "last_page": last_page,
        "total": total,
    }


def search_pexels(
    query: str,
    category: str = "General",
    limit: int = 24,
    page: int = 1,
) -> dict[str, object]:
    api_key = get_pexels_api_key()
    if not api_key:
        raise RuntimeError("Pexels API key topilmadi. Wallpaper Settings -> Pexels API Key")

    category_terms = {
        "General": "",
        "Anime": "anime art illustration",
        "People": "portrait person",
        "Nature": "nature forest mountain landscape",
        "Sci-Fi": "cyberpunk futuristic sci-fi",
        "Minimal": "minimal clean background",
        "Abstract": "abstract art",
        "City": "city urban skyline",
        "Dark": "dark moody",
        "Aesthetic": "aesthetic neon vaporwave",
    }
    final_query = query.strip() or "wallpaper"
    extra = category_terms.get(category, "")
    if extra and extra.lower() not in final_query.lower():
        final_query = f"{final_query} {extra}"

    per_page = max(1, min(80, limit))
    params = {
        "query": final_query,
        "page": max(1, page),
        "per_page": per_page,
        "orientation": "landscape",
    }
    req = Request(
        "https://api.pexels.com/v1/search?" + urlencode(params),
        headers={
            "Authorization": api_key,
            "User-Agent": "arch-hypr-settings-center/1.0",
        },
    )
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"Pexels request failed: {exc}") from exc

    photos = payload.get("photos", [])
    items: list[dict[str, str]] = []
    for row in photos[:limit]:
        src = row.get("src", {}) if isinstance(row.get("src"), dict) else {}
        image_url = str(src.get("original") or src.get("large2x") or "")
        thumb_url = str(src.get("medium") or src.get("small") or "")
        pid = str(row.get("id", "unknown"))
        alt = _clean_title(str(row.get("alt", "")), "")
        author = _clean_title(str(row.get("photographer", "")), "Pexels")
        title = alt or f"Pexels photo by {author}"
        items.append(
            {
                "title": title,
                "provider": "Pexels",
                "image_url": image_url,
                "thumbnail_url": thumb_url,
                "media_type": "photo",
                "display_name": title,
            }
        )

    current_page = int(payload.get("page", max(1, page)))
    total = int(payload.get("total_results", 0))
    last_page = max(1, ceil(total / per_page)) if per_page else 1
    return {
        "items": items,
        "current_page": current_page,
        "end_page": current_page,
        "last_page": last_page,
        "total": total,
    }


def search_pexels_videos(
    query: str,
    category: str = "General",
    limit: int = 24,
    page: int = 1,
) -> dict[str, object]:
    api_key = get_pexels_api_key()
    if not api_key:
        raise RuntimeError("Pexels API key topilmadi. Wallpaper Settings -> Pexels API Key")

    category_terms = {
        "General": "",
        "Anime": "anime",
        "People": "people portrait",
        "Nature": "nature landscape",
        "Sci-Fi": "cyberpunk futuristic",
        "Minimal": "minimal",
        "Abstract": "abstract",
        "City": "city night",
        "Dark": "dark moody",
        "Aesthetic": "aesthetic neon",
    }
    final_query = query.strip() or "live wallpaper"
    extra = category_terms.get(category, "")
    if extra and extra.lower() not in final_query.lower():
        final_query = f"{final_query} {extra}"

    per_page = max(1, min(80, limit))
    params = {
        "query": final_query,
        "page": max(1, page),
        "per_page": per_page,
        "orientation": "landscape",
    }
    req = Request(
        "https://api.pexels.com/videos/search?" + urlencode(params),
        headers={
            "Authorization": api_key,
            "User-Agent": "arch-hypr-settings-center/1.0",
        },
    )
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"Pexels video request failed: {exc}") from exc

    items: list[dict[str, str]] = []
    for row in payload.get("videos", [])[:limit]:
        video_files = row.get("video_files", [])
        best_link = ""
        best_width = 0
        for vf in video_files:
            link = str(vf.get("link", ""))
            width = int(vf.get("width", 0) or 0)
            if link and width >= best_width:
                best_link = link
                best_width = width
        if not best_link:
            continue
        duration = str(row.get("duration", ""))
        image = str(row.get("image", ""))
        pexels_url = str(row.get("url", ""))
        slug = ""
        if "/video/" in pexels_url:
            slug = pexels_url.split("/video/", 1)[1].strip("/")
            slug = slug.rsplit("-", 1)[0].replace("-", " ")
        user = row.get("user", {}) if isinstance(row.get("user"), dict) else {}
        uploader = _clean_title(str(user.get("name", "")), "Pexels")
        video_title = _clean_title(slug, f"Pexels video by {uploader}")
        items.append(
            {
                "title": f"{video_title} ({duration}s)",
                "provider": "Pexels",
                "image_url": best_link,
                "thumbnail_url": image,
                "media_type": "video",
                "display_name": video_title,
            }
        )

    current_page = int(payload.get("page", max(1, page)))
    total = int(payload.get("total_results", 0))
    last_page = max(1, ceil(total / per_page)) if per_page else 1
    return {
        "items": items,
        "current_page": current_page,
        "end_page": current_page,
        "last_page": last_page,
        "total": total,
    }


def search_unsplash(
    query: str,
    category: str = "General",
    limit: int = 24,
    page: int = 1,
) -> dict[str, object]:
    api_key = get_unsplash_api_key()
    if not api_key:
        raise RuntimeError("Unsplash API key topilmadi. Wallpaper Settings -> Unsplash API Key")

    final_query = (query.strip() or "wallpaper").strip()
    if category and category.lower() != "general":
        final_query = f"{final_query} {category}"

    per_page = max(1, min(30, limit))
    params = {
        "query": final_query,
        "page": max(1, page),
        "per_page": per_page,
        "orientation": "landscape",
        "content_filter": "high",
        "client_id": api_key,
    }
    req = Request(
        "https://api.unsplash.com/search/photos?" + urlencode(params),
        headers={"User-Agent": "arch-hypr-settings-center/1.0"},
    )
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"Unsplash request failed: {exc}") from exc

    results = payload.get("results", [])
    items: list[dict[str, str]] = []
    for row in results[:limit]:
        urls = row.get("urls", {}) if isinstance(row.get("urls"), dict) else {}
        user = row.get("user", {}) if isinstance(row.get("user"), dict) else {}
        desc = _clean_title(str(row.get("description", "") or row.get("alt_description", "")), "")
        author = _clean_title(str(user.get("name", "")), "Unsplash")
        title = desc or f"Unsplash photo by {author}"
        items.append(
            {
                "title": title,
                "provider": "Unsplash",
                "image_url": str(urls.get("full") or urls.get("regular") or ""),
                "thumbnail_url": str(urls.get("small") or urls.get("thumb") or ""),
                "media_type": "photo",
                "display_name": title,
            }
        )

    total = int(payload.get("total", 0))
    total_pages = int(payload.get("total_pages", 1))
    return {
        "items": items,
        "current_page": max(1, page),
        "end_page": max(1, page),
        "last_page": max(1, total_pages),
        "total": total,
    }


def search_pixabay(
    query: str,
    category: str = "General",
    limit: int = 24,
    page: int = 1,
) -> dict[str, object]:
    api_key = get_pixabay_api_key()
    if not api_key:
        raise RuntimeError("Pixabay API key topilmadi. Wallpaper Settings -> Pixabay API Key")

    final_query = (query.strip() or "wallpaper").strip()
    if category and category.lower() != "general":
        final_query = f"{final_query} {category}"

    per_page = max(3, min(200, limit))
    params = {
        "key": api_key,
        "q": final_query,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "page": max(1, page),
        "per_page": per_page,
    }
    req = Request(
        "https://pixabay.com/api/?" + urlencode(params),
        headers={"User-Agent": "arch-hypr-settings-center/1.0"},
    )
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"Pixabay request failed: {exc}") from exc

    items: list[dict[str, str]] = []
    for row in payload.get("hits", [])[:limit]:
        tag_text = _clean_title(str(row.get("tags", "")), "")
        title = tag_text or f"Pixabay {row.get('id', 'photo')}"
        items.append(
            {
                "title": title,
                "provider": "Pixabay",
                "image_url": str(row.get("largeImageURL") or row.get("webformatURL") or ""),
                "thumbnail_url": str(row.get("webformatURL") or row.get("previewURL") or ""),
                "media_type": "photo",
                "display_name": title,
            }
        )

    total = int(payload.get("totalHits", 0))
    last_page = max(1, ceil(total / per_page))
    return {
        "items": items,
        "current_page": max(1, page),
        "end_page": max(1, page),
        "last_page": last_page,
        "total": total,
    }


def download_image_to_library(
    image_url: str,
    progress_cb: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> Path:
    if not image_url:
        raise RuntimeError("Image URL yo'q")

    library_dir = get_cache_dir() / "images"
    library_dir.mkdir(parents=True, exist_ok=True)

    file_name = Path(image_url).name
    dest = library_dir / file_name
    if dest.exists():
        if progress_cb is not None:
            progress_cb(1, 1)
        return dest

    req = Request(image_url, headers={"User-Agent": "arch-hypr-settings-center/1.0"})
    try:
        with urlopen(req, timeout=20) as resp:
            total_raw = resp.headers.get("Content-Length")
            total = int(total_raw) if total_raw and total_raw.isdigit() else 0
            downloaded = 0
            with dest.open("wb") as out:
                while True:
                    if should_cancel is not None and should_cancel():
                        raise RuntimeError("Cancelled")
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb is not None:
                        progress_cb(downloaded, total)
            if progress_cb is not None:
                if total > 0:
                    progress_cb(total, total)
                else:
                    progress_cb(downloaded, downloaded if downloaded > 0 else 1)
    except URLError as exc:
        raise RuntimeError(f"Image download failed: {exc}") from exc

    return dest


def download_video_to_live(
    video_url: str,
    progress_cb: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> Path:
    if not video_url:
        raise RuntimeError("Video URL yo'q")

    live_dir = _configured_path("videos", get_wallpaper_dir() / "live")
    live_dir.mkdir(parents=True, exist_ok=True)

    file_name = Path(video_url.split("?", 1)[0]).name or "video.mp4"
    dest = live_dir / file_name
    if dest.exists():
        if progress_cb is not None:
            progress_cb(1, 1)
        return dest

    req = Request(video_url, headers={"User-Agent": "arch-hypr-settings-center/1.0"})
    try:
        with urlopen(req, timeout=60) as resp:
            total_raw = resp.headers.get("Content-Length")
            total = int(total_raw) if total_raw and total_raw.isdigit() else 0
            downloaded = 0
            with dest.open("wb") as out:
                while True:
                    if should_cancel is not None and should_cancel():
                        raise RuntimeError("Cancelled")
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb is not None:
                        progress_cb(downloaded, total)
            if progress_cb is not None:
                if total > 0:
                    progress_cb(total, total)
                else:
                    progress_cb(downloaded, downloaded if downloaded > 0 else 1)
    except URLError as exc:
        raise RuntimeError(f"Video download failed: {exc}") from exc

    return dest


def download_wallhaven_image(image_url: str) -> Path:
    # Backward-compatible wrapper used by old call sites.
    return download_image_to_library(image_url)


def fetch_thumbnail(thumbnail_url: str) -> str:
    if not thumbnail_url:
        return ""
    dest = get_thumbnail_cache_path(thumbnail_url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return str(dest)

    tmp = dest.with_suffix(dest.suffix + ".tmp")
    req = Request(thumbnail_url, headers={"User-Agent": "arch-hypr-settings-center/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            with tmp.open("wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
        tmp.replace(dest)
        return str(dest)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return ""


def get_thumbnail_cache_path(url_or_file: str) -> Path:
    base_dir = _configured_path("thumbnails", Path(DEFAULT_PATHS["thumbnails"]).expanduser())
    suffix = Path(url_or_file.split("?", 1)[0]).suffix.lower() if url_or_file else ""
    if not suffix or len(suffix) > 8:
        suffix = ".jpg"
    digest = hashlib.sha256(url_or_file.encode("utf-8")).hexdigest()
    return base_dir / f"{digest}{suffix}"
