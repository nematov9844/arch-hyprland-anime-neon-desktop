from pathlib import Path


def settings_path() -> Path:
    return Path.home() / ".config/settings/config.json"
