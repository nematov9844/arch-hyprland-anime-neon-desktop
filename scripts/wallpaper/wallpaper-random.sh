#!/usr/bin/env bash

set -e

PRIMARY_DIR="$HOME/.local/share/arch-hyprland/wallpapers/library"
LEGACY_DIR="$HOME/.local/share/arch-hyprland/wallpapers/static"
DIR="$PRIMARY_DIR"

if [ ! -d "$DIR" ]; then
  DIR="$LEGACY_DIR"
fi

FILE=$(find "$DIR" -maxdepth 1 -type f \( \
  -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) \
  | shuf -n 1)

[ -z "$FILE" ] && exit 1

"$HOME/.local/bin/wallpaper-apply.sh" "$FILE" "local-random" "image"