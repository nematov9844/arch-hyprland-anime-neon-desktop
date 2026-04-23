#!/usr/bin/env bash

set -e

CONFIG_DIR="$HOME/.config/arch-hyprland/wallpaper"
HISTORY_FILE="$CONFIG_DIR/history.json"

[ -f "$HISTORY_FILE" ] || {
  notify-send "Wallpaper" "History is empty"
  exit 0
}

CHOICE=$(jq -r '.items[]? | "\(.applied_at) | \(.provider) | \(.file)"' "$HISTORY_FILE" \
  | head -n 100 \
  | wofi --dmenu --prompt "Wallpaper History")

[ -z "$CHOICE" ] && exit 0

FILE=$(printf '%s\n' "$CHOICE" | awk -F' \\| ' '{print $3}')
[ -f "$FILE" ] || {
  notify-send "Wallpaper" "History file missing"
  exit 1
}

"$HOME/.local/bin/wallpaper-apply.sh" "$FILE" "history" "image"
