#!/usr/bin/env bash

set -e

CONFIG_FILE="$HOME/.config/arch-hyprland/wallpaper/config.json"
LABELS_FILE="$HOME/.config/arch-hyprland/wallpaper/labels.json"

[ -f "$CONFIG_FILE" ] || {
  notify-send "Wallpaper" "Config not found"
  exit 1
}

get_label() {
  local key="$1"
  jq -r --arg key "$key" '.[$key] // $key' "$LABELS_FILE" 2>/dev/null || echo "$key"
}

MENU=$(printf "%s\n%s\n%s\n%s\n%s" \
  "$(get_label menu.settings): $(get_label settings.engine)" \
  "$(get_label menu.settings): $(get_label settings.provider)" \
  "$(get_label menu.settings): $(get_label settings.purity)" \
  "$(get_label menu.settings): $(get_label settings.categories)" \
  "$(get_label menu.settings): $(get_label settings.sorting)" \
  | wofi --dmenu --prompt "Wallpaper Settings")

[ -z "$MENU" ] && exit 0

case "$MENU" in
  *"Engine")
    VALUE=$(printf "hyprpaper\nmpvpaper" | wofi --dmenu --prompt "Engine")
    [ -z "$VALUE" ] && exit 0
    TMP="$(mktemp)"
    jq '.engine = $value' --arg value "$VALUE" "$CONFIG_FILE" > "$TMP"
    mv "$TMP" "$CONFIG_FILE"
    notify-send "Wallpaper" "Engine set to $VALUE"
    ;;
  *"Default Provider")
    VALUE=$(printf "wallhaven\nlocal" | wofi --dmenu --prompt "Provider")
    [ -z "$VALUE" ] && exit 0
    TMP="$(mktemp)"
    jq '.default_provider = $value' --arg value "$VALUE" "$CONFIG_FILE" > "$TMP"
    mv "$TMP" "$CONFIG_FILE"
    notify-send "Wallpaper" "Provider set to $VALUE"
    ;;
  *"Purity")
    VALUE=$(printf "100\n110\n111\n" | wofi --dmenu --prompt "Purity")
    [ -z "$VALUE" ] && exit 0
    TMP="$(mktemp)"
    jq '.wallhaven.purity = $value' --arg value "$VALUE" "$CONFIG_FILE" > "$TMP"
    mv "$TMP" "$CONFIG_FILE"
    notify-send "Wallpaper" "Purity set to $VALUE"
    ;;
  *"Categories")
    VALUE=$(printf "111\n100\n010\n001" | wofi --dmenu --prompt "Categories")
    [ -z "$VALUE" ] && exit 0
    TMP="$(mktemp)"
    jq '.wallhaven.categories = $value' --arg value "$VALUE" "$CONFIG_FILE" > "$TMP"
    mv "$TMP" "$CONFIG_FILE"
    notify-send "Wallpaper" "Categories set to $VALUE"
    ;;
  *"Sorting")
    VALUE=$(printf "relevance\ndate_added\nviews\nfavorites\ntoplist" | wofi --dmenu --prompt "Sorting")
    [ -z "$VALUE" ] && exit 0
    TMP="$(mktemp)"
    jq '.wallhaven.sorting = $value' --arg value "$VALUE" "$CONFIG_FILE" > "$TMP"
    mv "$TMP" "$CONFIG_FILE"
    notify-send "Wallpaper" "Sorting set to $VALUE"
    ;;
  *)
    exit 0
    ;;
esac
