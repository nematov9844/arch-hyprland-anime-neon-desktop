#!/usr/bin/env bash

set -e

for pid in $(pgrep -x waybar 2>/dev/null || true); do
  kill "$pid" 2>/dev/null || true
done

THEME=$(printf "neon-purple\ncrimson-night\nmono-dark" | \
  wofi --dmenu --prompt "Waybar Theme")

[ -z "$THEME" ] && exit 0

cp "$HOME/.config/waybar/themes/$THEME.css" \
  "$HOME/.config/waybar/themes/current.css"

waybar &