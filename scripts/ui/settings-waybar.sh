#!/usr/bin/env bash

set -e

kill_by_name() {
  local name="$1"
  local pid
  for pid in $(pgrep -x "$name" 2>/dev/null || true); do
    kill "$pid" 2>/dev/null || true
  done
}

CHOICE=$(printf "Reload Waybar\nToggle Top Bar\nToggle Dock" | \
  wofi --dmenu --prompt "Waybar Settings")

[ -z "$CHOICE" ] && exit 0

CONFIG_FILE="$HOME/.config/settings/config.json"

case "$CHOICE" in
  "Reload Waybar")
    kill_by_name waybar
    waybar &
    notify-send "Waybar" "Reloaded"
    ;;

  "Toggle Top Bar")
    CURRENT=$(jq -r '.waybar.top_enabled' "$CONFIG_FILE")
    if [ "$CURRENT" = "true" ]; then
      TMP="$(mktemp)"
      jq '.waybar.top_enabled = false' "$CONFIG_FILE" > "$TMP"
      mv "$TMP" "$CONFIG_FILE"
      kill_by_name waybar
      notify-send "Waybar" "Top bar disabled"
    else
      TMP="$(mktemp)"
      jq '.waybar.top_enabled = true' "$CONFIG_FILE" > "$TMP"
      mv "$TMP" "$CONFIG_FILE"
      kill_by_name waybar
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
      for pid in $(pgrep -f "waybar -c $HOME/.config/waybar/dock.jsonc" 2>/dev/null || true); do
        kill "$pid" 2>/dev/null || true
      done
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
