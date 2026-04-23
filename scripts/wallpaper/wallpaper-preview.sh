#!/usr/bin/env bash

set -e

FILE="${1:-}"
[ -n "$FILE" ] || {
  echo "Usage: $0 /path/to/image"
  exit 1
}
[ -f "$FILE" ] || {
  echo "File not found: $FILE"
  exit 1
}

if command -v imv >/dev/null 2>&1; then
  imv "$FILE"
else
  notify-send "Wallpaper Preview" "Install imv for image preview"
fi
