import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


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

WAYBAR_HOME_CONFIG = Path.home() / ".config/waybar/config.jsonc"
WAYBAR_HOME_GENERATED = Path.home() / ".config/waybar/config.generated.jsonc"
WAYBAR_HOME_STYLE = Path.home() / ".config/waybar/style.css"
REPO_ROOT = Path(__file__).resolve().parents[4]
WAYBAR_REPO_CONFIG = REPO_ROOT / "config/waybar/config.jsonc"
WAYBAR_REPO_STYLE = REPO_ROOT / "config/waybar/style.css"


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _base_waybar_config_path() -> Path:
    return WAYBAR_HOME_CONFIG if WAYBAR_HOME_CONFIG.exists() else WAYBAR_REPO_CONFIG


def _style_path() -> Path:
    return WAYBAR_HOME_STYLE if WAYBAR_HOME_STYLE.exists() else WAYBAR_REPO_STYLE


def apply_waybar_modules(config: dict[str, Any]) -> tuple[bool, str, Path | None]:
    module_state = config.get("waybar", {}).get("modules", {}) if isinstance(config.get("waybar", {}), dict) else {}
    if not isinstance(module_state, dict):
        module_state = {}

    source_path = _base_waybar_config_path()
    try:
        raw = _load_json(source_path)
    except Exception as exc:
        return False, f"waybar config parse failed: {exc}", None

    left = raw.get("modules-left", [])
    center = raw.get("modules-center", [])
    right = raw.get("modules-right", [])
    if not isinstance(left, list):
        left = []
    if not isinstance(center, list):
        center = []
    if not isinstance(right, list):
        right = []

    center_base = [item for item in center if isinstance(item, str) and item != "clock"]
    if bool(module_state.get("clock", True)):
        center_base.append("clock")

    right_base = [item for item in right if isinstance(item, str) and item not in WAYBAR_RIGHT_ORDER]
    enabled_right: list[str] = []
    for name in WAYBAR_RIGHT_ORDER:
        matched_key = next((k for k, v in WAYBAR_MODULE_MAP.items() if v == name), None)
        if matched_key is None:
            if name not in enabled_right:
                enabled_right.append(name)
            continue
        if bool(module_state.get(matched_key, True)):
            enabled_right.append(name)

    raw["modules-left"] = [item for item in left if isinstance(item, str)]
    raw["modules-center"] = center_base
    raw["modules-right"] = right_base + enabled_right

    try:
        WAYBAR_HOME_GENERATED.parent.mkdir(parents=True, exist_ok=True)
        WAYBAR_HOME_GENERATED.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    except Exception as exc:
        return False, f"waybar generated write failed: {exc}", None

    return True, "ok", WAYBAR_HOME_GENERATED


def reload_waybar(config_path: Path | None = None) -> tuple[bool, str]:
    target_config = config_path if config_path is not None else _base_waybar_config_path()
    style = _style_path()
    cmd = f'pkill waybar || true; sleep 0.4; waybar -c "{target_config}" -s "{style}"'
    try:
        subprocess.Popen(["sh", "-lc", cmd])
        return True, "waybar reload sent"
    except Exception as exc:
        return False, f"waybar reload failed: {exc}"


def apply_hypr_effects(config: dict[str, Any]) -> tuple[bool, str]:
    if shutil.which("hyprctl") is None:
        return False, "hyprctl not found"

    effects = config.get("effects", {}) if isinstance(config.get("effects", {}), dict) else {}
    blur = effects.get("blur", {}) if isinstance(effects.get("blur", {}), dict) else {}
    opacity = effects.get("opacity", {}) if isinstance(effects.get("opacity", {}), dict) else {}

    blur_enabled = "1" if bool(blur.get("enabled", True)) else "0"
    blur_size = str(int(blur.get("size", 4)))
    blur_passes = str(int(blur.get("passes", 2)))
    active_opacity = str(float(opacity.get("active", 1.0)))
    inactive_opacity = str(float(opacity.get("inactive", 0.85)))

    commands = [
        ("decoration:blur:enabled", blur_enabled),
        ("decoration:blur:size", blur_size),
        ("decoration:blur:passes", blur_passes),
        ("decoration:active_opacity", active_opacity),
        ("decoration:inactive_opacity", inactive_opacity),
    ]

    try:
        for key, value in commands:
            subprocess.Popen(["hyprctl", "keyword", key, value])
        return True, "hypr effects apply sent"
    except Exception as exc:
        return False, f"hypr effects apply failed: {exc}"
