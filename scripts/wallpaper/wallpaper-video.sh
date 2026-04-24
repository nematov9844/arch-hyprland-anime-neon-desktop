#!/usr/bin/env bash

set -e

CONFIG_FILE="$HOME/.config/arch-hyprland/wallpaper/config.json"
STATE_FILE="$HOME/.config/arch-hyprland/wallpaper/state.json"
LIVE_DIR="$HOME/.local/share/arch-hyprland/wallpapers/live"
VIDEOS_DIR="$HOME/Videos"
DOWNLOADS_DIR="$HOME/Downloads"
ENGINE=$(jq -r '.engine' "$CONFIG_FILE")

if ! command -v mpvpaper >/dev/null 2>&1; then
  notify-send "Wallpaper" "mpvpaper o'rnatilmagan (install optional packages)"
  exit 1
fi

if [ "$ENGINE" != "mpvpaper" ]; then
  TMP="$(mktemp)"
  jq '.engine = "mpvpaper"' "$CONFIG_FILE" > "$TMP" && mv "$TMP" "$CONFIG_FILE"
  notify-send "Wallpaper" "Engine avtomatik mpvpaper ga o'tdi"
fi

mkdir -p "$LIVE_DIR"

SRC=$(printf "Live Library\nVideos\nDownloads" | wofi --dmenu --prompt "Video source")
[ -z "$SRC" ] && exit 0

SEARCH_DIR="$LIVE_DIR"
case "$SRC" in
  "Videos") SEARCH_DIR="$VIDEOS_DIR" ;;
  "Downloads") SEARCH_DIR="$DOWNLOADS_DIR" ;;
esac

if [ ! -d "$SEARCH_DIR" ]; then
  notify-send "Wallpaper" "Papka topilmadi: $SEARCH_DIR"
  exit 1
fi

CHOICE=$(find "$SEARCH_DIR" -maxdepth 1 -type f \( \
  -iname "*.mp4" -o -iname "*.webm" -o -iname "*.mkv" \) \
  | sort \
  | sed "s|$SEARCH_DIR/||" \
  | wofi --dmenu --prompt "Video Wallpaper")

[ -z "$CHOICE" ] && exit 0

FILE="$SEARCH_DIR/$CHOICE"
if [ "$SEARCH_DIR" != "$LIVE_DIR" ]; then
  SAFE_NAME="$(basename "$FILE")"
  TARGET="$LIVE_DIR/$SAFE_NAME"
  cp -f "$FILE" "$TARGET"
  FILE="$TARGET"
fi

pkill mpvpaper >/dev/null 2>&1 || true
MONITOR=$(hyprctl monitors -j | jq -r '.[0].name')
pkill hyprpaper >/dev/null 2>&1 || true
mpvpaper -o "no-audio loop" "$MONITOR" "$FILE" &

NOW="$(date --iso-8601=seconds)"
cat > "$STATE_FILE" <<EOF
{
  "current": "$FILE",
  "provider": "local-video",
  "type": "video",
  "updated_at": "$NOW"
}
EOF

notify-send "Wallpaper" "Video wallpaper applied"
