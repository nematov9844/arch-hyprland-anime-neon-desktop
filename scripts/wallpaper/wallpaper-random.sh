#!/usr/bin/env bash

set -e

DIR="$HOME/.local/share/arch-hyprland/wallpapers/static"

FILE=$(find "$DIR" -maxdepth 1 -type f \( \
  -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) \
  | shuf -n 1)

[ -z "$FILE" ] && exit 1

"$HOME/.local/bin/wallpaper-apply.sh" "$FILE" "local-random" "image"