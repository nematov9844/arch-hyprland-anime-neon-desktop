#!/usr/bin/env bash

set -e

CONFIG_FILE="$HOME/.config/arch-hyprland/wallpaper/config.json"
STATE_FILE="$HOME/.config/arch-hyprland/wallpaper/state.json"
LIVE_DIR="$HOME/.local/share/arch-hyprland/wallpapers/live"
ENGINE=$(jq -r '.engine' "$CONFIG_FILE")

if [ "$ENGINE" != "mpvpaper" ]; then
  notify-send "Wallpaper" "Set engine to mpvpaper in Wallpaper Settings first"
  exit 1
fi

if [ ! -d "$LIVE_DIR" ]; then
  notify-send "Wallpaper" "Live wallpaper directory not found"
  exit 1
fi

CHOICE=$(find "$LIVE_DIR" -maxdepth 1 -type f \( \
  -iname "*.mp4" -o -iname "*.webm" -o -iname "*.mkv" \) \
  | sort \
  | sed "s|$LIVE_DIR/||" \
  | wofi --dmenu --prompt "Video Wallpaper")

[ -z "$CHOICE" ] && exit 0

FILE="$LIVE_DIR/$CHOICE"

if ! command -v mpvpaper >/dev/null 2>&1; then
  notify-send "Wallpaper" "mpvpaper not installed"
  exit 1
fi

pkill mpvpaper >/dev/null 2>&1 || true
MONITOR=$(hyprctl monitors -j | jq -r '.[0].name')
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
