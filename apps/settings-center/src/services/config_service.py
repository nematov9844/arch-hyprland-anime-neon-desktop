import json
from pathlib import Path
from typing import Any


CONFIG_PATH = Path.home() / ".config/arch-hyprland/wallpaper/config.json"
DEFAULT_PATHS = {
    "images": "~/.local/share/arch-hyprland/wallpapers/static",
    "videos": "~/.local/share/arch-hyprland/wallpapers/live",
    "cache": "~/.local/share/arch-hyprland/wallpapers/cache",
    "thumbnails": "~/.local/share/arch-hyprland/wallpapers/previews",
}
PROVIDER_DEFAULTS = {
    "wallhaven": {"enabled": True, "api_key": ""},
    "pexels": {"enabled": True, "api_key": "", "default_query": "anime wallpaper"},
    "unsplash": {"enabled": False, "api_key": "", "default_query": "anime wallpaper"},
    "pixabay": {"enabled": False, "api_key": "", "default_query": "anime wallpaper"},
}


def load_config() -> dict[str, Any]:
    config, _had_fallback = load_config_with_status()
    return config


def load_config_with_status() -> tuple[dict[str, Any], bool]:
    had_fallback = False
    if not CONFIG_PATH.exists():
        return migrate_config({}), True
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
        had_fallback = True
    if not isinstance(raw, dict):
        raw = {}
        had_fallback = True
    return migrate_config(raw), had_fallback


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def ensure_config_schema(config: dict[str, Any]) -> dict[str, Any]:
    out = dict(config)
    out["schema_version"] = 1

    paths = out.get("paths", {})
    if not isinstance(paths, dict):
        paths = {}
    merged_paths = dict(paths)
    for key, value in DEFAULT_PATHS.items():
        if not str(merged_paths.get(key, "")).strip():
            merged_paths[key] = value
    out["paths"] = merged_paths

    for provider, defaults in PROVIDER_DEFAULTS.items():
        section = out.get(provider, {})
        if not isinstance(section, dict):
            section = {}
        merged = dict(section)
        for key, value in defaults.items():
            if key not in merged:
                merged[key] = value
        out[provider] = merged

    return out


def migrate_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    base = config if isinstance(config, dict) else {}
    migrated = ensure_config_schema(base)
    # Best effort auto-save so the file stays schema-aligned.
    try:
        save_config(migrated)
    except Exception:
        pass
    return migrated


def update_provider_config(provider: str, updates: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config()
    section = cfg.get(provider, {})
    if not isinstance(section, dict):
        section = {}
    merged = dict(section)
    for key, value in updates.items():
        merged[key] = value
    cfg[provider] = merged
    save_config(cfg)
    return cfg


def update_paths_config(key: str, value: str) -> dict[str, Any]:
    cfg = load_config()
    paths = cfg.get("paths", {})
    if not isinstance(paths, dict):
        paths = {}
    merged_paths = dict(paths)
    merged_paths[key] = value
    cfg["paths"] = merged_paths
    save_config(cfg)
    return cfg
