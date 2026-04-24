#!/usr/bin/env bash

APP_DIR="$HOME/.local/share/arch-hyprland/apps/settings-center/src"

if [ ! -d "$APP_DIR" ]; then
  notify-send "Settings Center" "Ilova o‘rnatilmagan. Repoda: bash install.sh yoki arch-hypr-update"
  exit 1
fi

cd "$APP_DIR" || exit 1
PYTHONPATH=. exec python3 app.py
