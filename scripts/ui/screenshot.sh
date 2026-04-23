#!/usr/bin/env bash

set -e

DIR="$HOME/Pictures/Screenshots"
FILE="$DIR/$(date +'%Y-%m-%d_%H-%M-%S').png"

mkdir -p "$DIR"

case "$1" in
  area)
    grim -g "$(slurp)" "$FILE"
    wl-copy < "$FILE"
    notify-send "Screenshot" "Area screenshot saved and copied"
    ;;
  full)
    grim "$FILE"
    wl-copy < "$FILE"
    notify-send "Screenshot" "Full screenshot saved and copied"
    ;;
  *)
    echo "Usage: $0 {area|full}"
    exit 1
    ;;
esac