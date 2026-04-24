#!/usr/bin/env bash

set -e

THEME=$(printf "neon-purple\ncrimson-night\nmono-dark" | \
  wofi --dmenu --prompt "Waybar Theme")

[ -z "$THEME" ] && exit 0

cp "$HOME/.config/waybar/themes/$THEME.css" \
  "$HOME/.config/waybar/themes/current.css"

"$HOME/.local/bin/waybar-restart.sh"