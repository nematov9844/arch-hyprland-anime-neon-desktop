#!/usr/bin/env bash

set -e

pkill mpvpaper >/dev/null 2>&1 || true
hyprpaper >/dev/null 2>&1 &

notify-send "Video Wallpaper" "Stopped"
