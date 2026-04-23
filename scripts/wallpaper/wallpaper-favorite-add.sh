#!/usr/bin/env bash

set -e

CONFIG_DIR="$HOME/.config/arch-hyprland/wallpaper"
STATE_FILE="$CONFIG_DIR/state.json"
FAVORITES_FILE="$CONFIG_DIR/favorites.json"
FAVORITES_DIR="$HOME/.local/share/arch-hyprland/wallpapers/favorites"

[ -f "$STATE_FILE" ] || {
  notify-send "Wallpaper" "No current wallpaper state"
  exit 1
}

CURRENT=$(jq -r '.current // empty' "$STATE_FILE")
[ -n "$CURRENT" ] || {
  notify-send "Wallpaper" "Nothing to favorite"
  exit 1
}
[ -f "$CURRENT" ] || {
  notify-send "Wallpaper" "Current wallpaper file not found"
  exit 1
}

mkdir -p "$CONFIG_DIR" "$FAVORITES_DIR"
[ -f "$FAVORITES_FILE" ] || printf '{\n  "items": []\n}\n' > "$FAVORITES_FILE"

cp -n "$CURRENT" "$FAVORITES_DIR/" 2>/dev/null || true

jq --arg file "$CURRENT" \
   --arg ts "$(date --iso-8601=seconds)" \
   '.items = ([{"file":$file,"added_at":$ts}] + .items)
    | .items |= unique_by(.file)' \
   "$FAVORITES_FILE" > "$FAVORITES_FILE.tmp" && mv "$FAVORITES_FILE.tmp" "$FAVORITES_FILE"

notify-send "Wallpaper" "Added to favorites"
