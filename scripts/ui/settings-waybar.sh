#!/usr/bin/env bash

set -e

CHOICE=$(printf "Reload Waybar\nToggle Top Bar\nToggle Dock" | \
  wofi --dmenu --prompt "Waybar Settings")

[ -z "$CHOICE" ] && exit 0

CONFIG_FILE="$HOME/.config/settings/config.json"

case "$CHOICE" in
  "Reload Waybar")
    pkill waybar || true
    waybar &
    notify-send "Waybar" "Reloaded"
    ;;

  "Toggle Top Bar")
    CURRENT=$(jq -r '.waybar.top_enabled' "$CONFIG_FILE")
    if [ "$CURRENT" = "true" ]; then
      TMP="$(mktemp)"
      jq '.waybar.top_enabled = false' "$CONFIG_FILE" > "$TMP"
      mv "$TMP" "$CONFIG_FILE"
      pkill waybar || true
      notify-send "Waybar" "Top bar disabled"
    else
      TMP="$(mktemp)"
      jq '.waybar.top_enabled = true' "$CONFIG_FILE" > "$TMP"
      mv "$TMP" "$CONFIG_FILE"
      pkill waybar || true
      waybar &
      notify-send "Waybar" "Top bar enabled"
    fi
    ;;

  "Toggle Dock")
    CURRENT=$(jq -r '.waybar.dock_enabled' "$CONFIG_FILE")
    if [ "$CURRENT" = "true" ]; then
      TMP="$(mktemp)"
      jq '.waybar.dock_enabled = false' "$CONFIG_FILE" > "$TMP"
      mv "$TMP" "$CONFIG_FILE"
      pkill -f "waybar -c $HOME/.config/waybar/dock.jsonc" || true
      notify-send "Waybar" "Dock disabled"
    else
      TMP="$(mktemp)"
      jq '.waybar.dock_enabled = true' "$CONFIG_FILE" > "$TMP"
      mv "$TMP" "$CONFIG_FILE"
      waybar -c "$HOME/.config/waybar/dock.jsonc" -s "$HOME/.config/waybar/dock.css" &
      notify-send "Waybar" "Dock enabled"
    fi
    ;;
esac
