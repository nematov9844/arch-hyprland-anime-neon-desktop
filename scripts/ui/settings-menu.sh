#!/usr/bin/env bash

set -e

CHOICE=$(printf "Theme\nWallpaper\nWaybar\nSystem\nDeveloper\nLock\nPower Menu" | \
  wofi --dmenu --prompt "Settings")

case "$CHOICE" in
  Theme)
    "$HOME/.local/bin/settings-theme.sh"
    ;;
  Wallpaper)
    "$HOME/.local/bin/wallpaper-menu.sh"
    ;;
  Waybar)
    "$HOME/.local/bin/settings-waybar.sh"
    ;;
  System)
    "$HOME/.local/bin/settings-system.sh"
    ;;
  Developer)
    "$HOME/.local/bin/settings-dev.sh"
    ;;
  Lock)
    hyprlock
    ;;
  "Power Menu")
    "$HOME/.local/bin/power-menu.sh"
    ;;
  *)
    exit 0
    ;;
esac
