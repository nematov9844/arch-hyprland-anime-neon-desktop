import json
from pathlib import Path
from typing import Any


SUPPORTED_LANGS = {"en", "uz", "ru"}
_TRANSLATION_CACHE: dict[str, dict[str, str]] = {}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def get_locale_config_path() -> Path:
    return Path.home() / ".config/settings/config.json"


def load_language() -> str:
    cfg_path = get_locale_config_path()
    if not cfg_path.exists():
        return "en"
    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return "en"
    if not isinstance(raw, dict):
        return "en"
    language = raw.get("language", {})
    if not isinstance(language, dict):
        return "en"
    current = str(language.get("current", "en")).strip().lower()
    return current if current in SUPPORTED_LANGS else "en"


def save_language(lang: str) -> None:
    selected = str(lang).strip().lower()
    if selected not in SUPPORTED_LANGS:
        selected = "en"
    cfg_path = get_locale_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            raw = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
        except Exception:
            data = {}

    language = data.get("language", {})
    if not isinstance(language, dict):
        language = {}
    language["current"] = selected
    data["language"] = language
    cfg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _translation_path_candidates(lang: str) -> list[Path]:
    safe_lang = lang if lang in SUPPORTED_LANGS else "en"
    installed = Path.home() / f".local/share/arch-hyprland/localization/{safe_lang}/settings_center.json"
    repo = _repo_root() / f"localization/{safe_lang}/settings_center.json"
    return [installed, repo]


def load_translations(lang: str) -> dict[str, str]:
    safe_lang = lang if lang in SUPPORTED_LANGS else "en"
    if safe_lang in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[safe_lang]

    result: dict[str, str] = {}
    for path in _translation_path_candidates(safe_lang):
        if not path.exists():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                result = {str(k): str(v) for k, v in raw.items()}
                break
        except Exception:
            continue

    if safe_lang != "en" and not result:
        return load_translations("en")

    _TRANSLATION_CACHE[safe_lang] = result
    return result


def t(key: str, fallback: str = "") -> str:
    lang = load_language()
    translations = load_translations(lang)
    if key in translations and translations[key]:
        return translations[key]
    if fallback:
        return fallback
    return key


def tt(key: str) -> str:
    return t(key, key)
