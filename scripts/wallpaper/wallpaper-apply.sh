#!/usr/bin/env bash

set -e

FILE="${1:-}"
PROVIDER="${2:-manual}"
TYPE="${3:-image}"

CONFIG_DIR="$HOME/.config/arch-hyprland/wallpaper"
STATE_FILE="$CONFIG_DIR/state.json"
HISTORY_FILE="$CONFIG_DIR/history.json"

if [ -z "$FILE" ]; then
  echo "Usage: $0 /path/to/file [provider] [type]"
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE"
  exit 1
fi

mkdir -p "$CONFIG_DIR"

# Ensure json files exist
[ -f "$STATE_FILE" ] || echo '{"current":"","provider":"","type":"","updated_at":""}' > "$STATE_FILE"
[ -f "$HISTORY_FILE" ] || echo '{"items":[]}' > "$HISTORY_FILE"

# Apply wallpaper
hyprctl hyprpaper unload all >/dev/null 2>&1 || true
hyprctl hyprpaper preload "$FILE"
hyprctl hyprpaper wallpaper ",$FILE"

NOW="$(date --iso-8601=seconds)"

# Update current state
cat > "$STATE_FILE" <<EOF
{
  "current": "$FILE",
  "provider": "$PROVIDER",
  "type": "$TYPE",
  "updated_at": "$NOW"
}
EOF

# Append to history
TMP_FILE="$(mktemp)"
jq --arg file "$FILE" \
   --arg provider "$PROVIDER" \
   --arg type "$TYPE" \
   --arg applied_at "$NOW" \
   '
   .items |= [{
     file: $file,
     provider: $provider,
     type: $type,
     applied_at: $applied_at
   }] + .
   | .items |= unique_by(.file)
   | .items |= .[:50]
   ' "$HISTORY_FILE" > "$TMP_FILE"

mv "$TMP_FILE" "$HISTORY_FILE"

notify-send "Wallpaper" "Applied: $(basename "$FILE")"