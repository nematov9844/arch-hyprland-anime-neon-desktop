#!/usr/bin/env bash

set -e

CHOICE=$(printf "Reload Hyprland\nRun Doctor\nCreate Backup\nRestore Latest Backup\nRun Update" | \
  wofi --dmenu --prompt "System Settings")

[ -z "$CHOICE" ] && exit 0

case "$CHOICE" in
  "Reload Hyprland")
    hyprctl reload
    notify-send "System" "Hyprland reloaded"
    ;;

  "Run Doctor")
    kitty --hold -e arch-hypr-doctor
    ;;

  "Create Backup")
    kitty --hold -e arch-hypr-backup
    ;;

  "Restore Latest Backup")
    kitty --hold -e arch-hypr-restore
    ;;

  "Run Update")
    kitty --hold -e arch-hypr-update
    ;;
esac
