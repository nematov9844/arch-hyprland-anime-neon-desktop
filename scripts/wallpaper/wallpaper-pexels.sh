#!/usr/bin/env bash

set -e

CONFIG_FILE="$HOME/.config/arch-hyprland/wallpaper/config.json"
QUERY="${1:-}"

if [ -z "$QUERY" ]; then
  QUERY=$(wofi --dmenu --prompt "Search Pexels")
fi
[ -z "$QUERY" ] && exit 0

API_KEY=$(jq -r '.pexels.api_key // ""' "$CONFIG_FILE")
if [ -z "$API_KEY" ]; then
  notify-send "Wallpaper" "Pexels API key yo'q (Wallpaper Settings -> Pexels API Key)"
  exit 1
fi

CATEGORY=$(printf "General\nAnime\nPeople\nNature\nSci-Fi\nMinimal\nAbstract\nCity\nDark\nAesthetic" | \
  wofi --dmenu --prompt "Pexels Category")
[ -z "$CATEGORY" ] && exit 0

EXTRA_QUERY=""
case "$CATEGORY" in
  Anime) EXTRA_QUERY="anime art illustration wallpaper" ;;
  People) EXTRA_QUERY="portrait person" ;;
  Nature) EXTRA_QUERY="nature landscape forest mountain" ;;
  Sci-Fi) EXTRA_QUERY="sci-fi cyberpunk futuristic" ;;
  Minimal) EXTRA_QUERY="minimal clean background" ;;
  Abstract) EXTRA_QUERY="abstract art geometry" ;;
  City) EXTRA_QUERY="city urban skyline" ;;
  Dark) EXTRA_QUERY="dark moody" ;;
  Aesthetic) EXTRA_QUERY="aesthetic neon vaporwave" ;;
esac

FINAL_QUERY="$QUERY"
[ -n "$EXTRA_QUERY" ] && FINAL_QUERY="$QUERY $EXTRA_QUERY"

TMP_JSON="/tmp/pexels_search.json"
LIBRARY_DIR="$HOME/.local/share/arch-hyprland/wallpapers/library"
mkdir -p "$LIBRARY_DIR"

curl -fsSL \
  --get "https://api.pexels.com/v1/search" \
  --header "Authorization: $API_KEY" \
  --data-urlencode "query=$FINAL_QUERY" \
  --data "per_page=30" \
  --data "orientation=landscape" \
  -o "$TMP_JSON"

CHOICE=$(jq -r '.photos[] | "\(.id) | \(.photographer) | \(.src.original)"' "$TMP_JSON" | \
  wofi --dmenu --prompt "Select Pexels Wallpaper")
[ -z "$CHOICE" ] && exit 0

IMAGE_URL=$(printf '%s\n' "$CHOICE" | awk -F' \\| ' '{print $3}')
FILE_NAME=$(basename "${IMAGE_URL%%\?*}")
DEST="$LIBRARY_DIR/$FILE_NAME"

curl -fsSL "$IMAGE_URL" -o "$DEST"
"$HOME/.local/bin/wallpaper-apply.sh" "$DEST" "pexels" "image"
