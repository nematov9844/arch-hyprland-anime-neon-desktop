#!/usr/bin/env bash

set -e

CHOICE=$(printf "Local\nSearch Wallhaven\nRandom\nRecent\nFavorites\nAdd Current to Favorites\nSettings\nVideo (Local)" | \
  wofi --dmenu --prompt "Wallpaper Menu")

case "$CHOICE" in
  Local)
    "$HOME/.local/bin/wallpaper-local.sh"
    ;;
  "Search Wallhaven")
    "$HOME/.local/bin/wallpaper-fetch.sh"
    ;;
  Random)
    "$HOME/.local/bin/wallpaper-random.sh"
    ;;
  Recent)
    "$HOME/.local/bin/wallpaper-history.sh"
    ;;
  Favorites)
    "$HOME/.local/bin/wallpaper-favorites.sh"
    ;;
  "Add Current to Favorites")
    "$HOME/.local/bin/wallpaper-favorite-add.sh"
    ;;
  Settings)
    "$HOME/.local/bin/wallpaper-settings.sh"
    ;;
  "Video (Local)")
    "$HOME/.local/bin/wallpaper-video.sh"
    ;;
  *)
    exit 0
    ;;
esac