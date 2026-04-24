#!/usr/bin/env bash

set -euo pipefail

CFG="$HOME/.config/settings/config.json"
WAYBAR_THEMES="$HOME/.config/waybar/themes"
CURRENT_CSS="$WAYBAR_THEMES/current.css"

if [[ -f "$CFG" ]]; then
  THEME="$(python - <<'PY'
import json
from pathlib import Path
p = Path.home()/'.config/settings/config.json'
try:
    data = json.loads(p.read_text(encoding='utf-8'))
except Exception:
    data = {}
theme = data.get('theme', {}).get('current', 'neon-purple')
print(theme)
PY
)"
else
  THEME="neon-purple"
fi

mkdir -p "$WAYBAR_THEMES"
if [[ -f "$WAYBAR_THEMES/$THEME.css" ]]; then
  cp "$WAYBAR_THEMES/$THEME.css" "$CURRENT_CSS"
fi

if command -v pkill >/dev/null 2>&1; then
  pkill waybar || true
fi

if command -v waybar >/dev/null 2>&1; then
  nohup waybar -c "$HOME/.config/waybar/config.jsonc" -s "$HOME/.config/waybar/style.css" >/dev/null 2>&1 &
fi

if command -v hyprctl >/dev/null 2>&1; then
  hyprctl reload >/dev/null 2>&1 || true
fi

if command -v notify-send >/dev/null 2>&1; then
  notify-send "Theme Sync" "Global theme sync applied: $THEME"
fi
