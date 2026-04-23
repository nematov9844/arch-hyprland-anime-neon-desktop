#!/usr/bin/env bash

THEME=$(printf "neon-purple\ncrimson-night\nmono-dark" | \
  wofi --dmenu --prompt "Waybar Theme")

[ -z "$THEME" ] && exit 0

cp "$HOME/Projects/arch-hyprland-anime-neon-desktop/config/waybar/themes/$THEME.css" \
   "$HOME/.config/waybar/themes/current.css"

pkill waybar
waybar &