#!/usr/bin/env bash

chosen=$(printf "Lock\nLogout\nReboot\nShutdown\nSleep" | \
  wofi --dmenu \
       --prompt "Power Menu" \
       --conf ~/.config/wofi/config \
       --style ~/.config/wofi/style.css)

case "$chosen" in
  Lock)
    hyprlock
    ;;
  Logout)
    hyprctl dispatch exit
    ;;
  Reboot)
    systemctl reboot
    ;;
  Shutdown)
    systemctl poweroff
    ;;
  Sleep)
    systemctl suspend
    ;;
esac