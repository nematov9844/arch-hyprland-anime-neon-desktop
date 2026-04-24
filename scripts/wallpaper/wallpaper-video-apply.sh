#!/usr/bin/env bash

set -e

FILE="${1:-}"

CONFIG_DIR="$HOME/.config/arch-hyprland/wallpaper"
STATE_FILE="$CONFIG_DIR/state.json"

if [ -z "$FILE" ]; then
  echo "Usage: $0 /path/to/video"
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "Video file not found: $FILE"
  exit 1
fi

if ! command -v mpvpaper >/dev/null 2>&1; then
  notify-send "Video Wallpaper" "mpvpaper o'rnatilmagan"
  exit 1
fi

MONITOR="$(hyprctl monitors -j | jq -r '.[0].name // empty')"
[ -z "$MONITOR" ] && MONITOR="ALL"

mkdir -p "$CONFIG_DIR"

pkill hyprpaper >/dev/null 2>&1 || true
pkill mpvpaper >/dev/null 2>&1 || true

mpvpaper -o "no-audio loop hwdec=auto" "$MONITOR" "$FILE" >/dev/null 2>&1 &

cat > "$STATE_FILE" <<EOF
{
  "current": "$FILE",
  "provider": "local-video",
  "type": "video",
  "engine": "mpvpaper",
  "updated_at": "$(date --iso-8601=seconds)"
}
EOF

notify-send "Video Wallpaper" "Applied: $(basename "$FILE")"
