#!/usr/bin/env bash

set -e

DIR="$HOME/.local/share/arch-hyprland/wallpapers/static"

if [ ! -d "$DIR" ]; then
  notify-send "Wallpaper" "Local wallpaper directory not found"
  exit 1
fi

CHOICE=$(find "$DIR" -maxdepth 1 -type f \( \
  -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) \
  | sort \
  | sed "s|$DIR/||" \
  | wofi --dmenu --prompt "Local Wallpaper")

[ -z "$CHOICE" ] && exit 0

FULL_PATH="$DIR/$CHOICE"
"$HOME/.local/bin/wallpaper-apply.sh" "$FULL_PATH" "local" "image"