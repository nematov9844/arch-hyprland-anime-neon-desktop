#!/usr/bin/env bash

set -e

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

pkill waybar || true
waybar &
notify-send "Settings" "Theme switched to $THEME"
