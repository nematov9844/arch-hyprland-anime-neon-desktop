#!/usr/bin/env bash

set -e

CONFIG_FILE="$HOME/.config/arch-hyprland/wallpaper/config.json"
QUERY="${1:-}"
if [ -z "$QUERY" ]; then
  QUERY=$(wofi --dmenu --prompt "Search Wallpaper")
fi
[ -z "$QUERY" ] && exit 0

CATEGORY=$(printf "Local\nGeneral\nAnime\nPeople\nNature\nSci-Fi\nMinimal\nAbstract\nCity\nDark\nAesthetic" | \
  wofi --dmenu --prompt "Category")
[ -z "$CATEGORY" ] && exit 0
if [ "$CATEGORY" = "Local" ]; then
  "$HOME/.local/bin/wallpaper-local.sh"
  exit 0
fi

API_URL=$(jq -r '.wallhaven.api_base' "$CONFIG_FILE")
PURITY=$(jq -r '.wallhaven.purity' "$CONFIG_FILE")
CATEGORIES=$(jq -r '.wallhaven.categories' "$CONFIG_FILE")
SORTING=$(jq -r '.wallhaven.sorting' "$CONFIG_FILE")
TMP_JSON="/tmp/wallhaven_search.json"
LIBRARY_DIR="$HOME/.local/share/arch-hyprland/wallpapers/library"
mkdir -p "$LIBRARY_DIR"

EXTRA_QUERY=""
case "$CATEGORY" in
  Anime) EXTRA_QUERY="anime" ;;
  People) EXTRA_QUERY="portrait character person" ;;
  Nature) EXTRA_QUERY="nature landscape forest mountain" ;;
  Sci-Fi) EXTRA_QUERY="sci-fi cyberpunk futuristic" ;;
  Minimal) EXTRA_QUERY="minimal clean" ;;
  Abstract) EXTRA_QUERY="abstract geometry" ;;
  City) EXTRA_QUERY="city urban night" ;;
  Dark) EXTRA_QUERY="dark moody noir" ;;
  Aesthetic) EXTRA_QUERY="aesthetic vaporwave neon" ;;
esac
FINAL_QUERY="$QUERY"
[ -n "$EXTRA_QUERY" ] && FINAL_QUERY="$QUERY $EXTRA_QUERY"

curl -fsSL \
  --get "$API_URL" \
  --data-urlencode "q=$FINAL_QUERY" \
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
DEST="$LIBRARY_DIR/$FILE_NAME"

curl -fsSL "$IMAGE_URL" -o "$DEST"

"$HOME/.local/bin/wallpaper-apply.sh" "$DEST" "wallhaven" "image"