#!/usr/bin/env bash

set -e

CONFIG_FILE="$HOME/.config/arch-hyprland/wallpaper/config.json"
QUERY="${1:-}"
if [ -z "$QUERY" ]; then
  QUERY=$(wofi --dmenu --prompt "Search Wallpaper")
fi
[ -z "$QUERY" ] && exit 0

API_URL=$(jq -r '.wallhaven.api_base' "$CONFIG_FILE")
PURITY=$(jq -r '.wallhaven.purity' "$CONFIG_FILE")
CATEGORIES=$(jq -r '.wallhaven.categories' "$CONFIG_FILE")
SORTING=$(jq -r '.wallhaven.sorting' "$CONFIG_FILE")
TMP_JSON="/tmp/wallhaven_search.json"
CACHE_DIR="$HOME/.local/share/arch-hyprland/wallpapers/cache"
mkdir -p "$CACHE_DIR"

curl -fsSL \
  --get "$API_URL" \
  --data-urlencode "q=$QUERY" \
  --data "sorting=$SORTING" \
  --data "purity=$PURITY" \
  --data "categories=$CATEGORIES" \
  -o "$TMP_JSON"

CHOICE=$(jq -r '.data[] | "\(.id) | \(.resolution) | \(.path)"' "$TMP_JSON" \
  | head -n 30 \
  | wofi --dmenu --prompt "Select Wallpaper")

[ -z "$CHOICE" ] && exit 0

IMAGE_URL=$(printf '%s\n' "$CHOICE" | awk -F' \\| ' '{print $3}')
FILE_NAME=$(basename "$IMAGE_URL")
DEST="$CACHE_DIR/$FILE_NAME"

curl -fsSL "$IMAGE_URL" -o "$DEST"

"$HOME/.local/bin/wallpaper-apply.sh" "$DEST" "wallhaven" "image"