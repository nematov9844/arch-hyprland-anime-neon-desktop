#!/usr/bin/env bash

set -e

CONFIG_DIR="$HOME/.config/arch-hyprland/wallpaper"
FAVORITES_FILE="$CONFIG_DIR/favorites.json"

[ -f "$FAVORITES_FILE" ] || {
  notify-send "Wallpaper" "No favorites yet"
  exit 0
}

CHOICE=$(jq -r '.items[]? | "\(.added_at) | \(.file)"' "$FAVORITES_FILE" \
  | head -n 100 \
  | wofi --dmenu --prompt "Wallpaper Favorites")

[ -z "$CHOICE" ] && exit 0

FILE=$(printf '%s\n' "$CHOICE" | awk -F' \\| ' '{print $2}')
[ -f "$FILE" ] || {
  notify-send "Wallpaper" "Favorite file missing"
  exit 1
}

"$HOME/.local/bin/wallpaper-apply.sh" "$FILE" "favorites" "image"
