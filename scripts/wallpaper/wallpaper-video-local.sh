#!/usr/bin/env bash

set -e

DIR="$HOME/.local/share/arch-hyprland/wallpapers/live"

mkdir -p "$DIR"

CHOICE=$(find "$DIR" -maxdepth 1 -type f \( \
  -iname "*.mp4" -o -iname "*.webm" -o -iname "*.mkv" \) \
  | sort \
  | sed "s|$DIR/||" \
  | wofi --dmenu --prompt "Local Video Wallpaper")

[ -z "$CHOICE" ] && exit 0

"$HOME/.local/bin/wallpaper-video-apply.sh" "$DIR/$CHOICE"
