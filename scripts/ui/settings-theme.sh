#!/usr/bin/env bash

set -e

kill_by_name() {
  local name="$1"
  local pid
  for pid in $(pgrep -x "$name" 2>/dev/null || true); do
    kill "$pid" 2>/dev/null || true
  done
}

THEME=$(printf "neon-purple\ncrimson-night\nmono-dark" | \
  wofi --dmenu --prompt "Theme")

[ -z "$THEME" ] && exit 0

mkdir -p "$HOME/.config/waybar/themes"

cp "$HOME/.config/waybar/themes/$THEME.css" \
   "$HOME/.config/waybar/themes/current.css"

TMP="$(mktemp)"
jq '.theme.current = $value' \
  --arg value "$THEME" \
  "$HOME/.config/settings/config.json" > "$TMP"

mv "$TMP" "$HOME/.config/settings/config.json"

kill_by_name waybar
sleep 0.5
waybar -c "$HOME/.config/waybar/config.jsonc" -s "$HOME/.config/waybar/style.css" >/dev/null 2>&1 &
notify-send "Settings" "Theme switched to $THEME"
