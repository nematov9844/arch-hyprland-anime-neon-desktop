#!/usr/bin/env bash

set -euo pipefail

TOP_CONFIG_DEFAULT="$HOME/.config/waybar/config.jsonc"
TOP_CONFIG_GENERATED="$HOME/.config/waybar/config.generated.jsonc"
TOP_STYLE="$HOME/.config/waybar/style.css"

if [ -f "$TOP_CONFIG_GENERATED" ]; then
  TOP_CONFIG="$TOP_CONFIG_GENERATED"
else
  TOP_CONFIG="$TOP_CONFIG_DEFAULT"
fi

# Stop only top waybar instances (leave dock intact).
pkill -f "waybar -c $TOP_CONFIG_DEFAULT" 2>/dev/null || true
pkill -f "waybar -c $TOP_CONFIG_GENERATED" 2>/dev/null || true
pkill -f "waybar -c ~/.config/waybar/config.jsonc" 2>/dev/null || true
pkill -f "waybar -c ~/.config/waybar/config.generated.jsonc" 2>/dev/null || true

sleep 0.35
waybar -c "$TOP_CONFIG" -s "$TOP_STYLE" >/dev/null 2>&1 &
