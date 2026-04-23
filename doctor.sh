#!/usr/bin/env bash

set -u

ok=0
warn=0
err=0

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] command found: $cmd"
    ok=$((ok + 1))
  else
    echo "[ERR] command missing: $cmd"
    err=$((err + 1))
  fi
}

check_file() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "[OK] file exists: $file"
    ok=$((ok + 1))
  else
    echo "[ERR] file missing: $file"
    err=$((err + 1))
  fi
}

check_dir() {
  local dir="$1"
  if [ -d "$dir" ]; then
    echo "[OK] directory exists: $dir"
    ok=$((ok + 1))
  else
    echo "[WARN] directory missing: $dir"
    warn=$((warn + 1))
  fi
}

check_service_enabled() {
  local service="$1"
  if systemctl is-enabled "$service" >/dev/null 2>&1; then
    echo "[OK] service enabled: $service"
    ok=$((ok + 1))
  else
    echo "[WARN] service not enabled: $service"
    warn=$((warn + 1))
  fi
}

check_service_active() {
  local service="$1"
  if systemctl is-active "$service" >/dev/null 2>&1; then
    echo "[OK] service active: $service"
    ok=$((ok + 1))
  else
    echo "[WARN] service not active: $service"
    warn=$((warn + 1))
  fi
}

echo "== Arch Hyprland Anime Neon Desktop Doctor =="
echo

echo "-- Checking commands --"
check_cmd hyprctl
check_cmd waybar
check_cmd wofi
check_cmd kitty
check_cmd hyprlock
check_cmd hypridle
check_cmd hyprpaper
check_cmd grim
check_cmd slurp
check_cmd wl-copy
check_cmd pamixer
check_cmd brightnessctl
check_cmd notify-send
check_cmd jq
check_cmd curl

echo
echo "-- Checking config files --"
check_file "$HOME/.config/hypr/hyprland.conf"
check_file "$HOME/.config/hypr/binds.conf"
check_file "$HOME/.config/hypr/autostart.conf"
check_file "$HOME/.config/waybar/config.jsonc"
check_file "$HOME/.config/waybar/style.css"
check_file "$HOME/.config/wofi/config"
check_file "$HOME/.config/wofi/style.css"
check_file "$HOME/.config/kitty/kitty.conf"
check_file "$HOME/.config/hypr/hyprlock.conf"
check_file "$HOME/.config/settings/config.json"
check_file "$HOME/.config/settings/labels.json"
check_file "$HOME/.config/arch-hyprland/wallpaper/config.json"
check_file "$HOME/.config/arch-hyprland/wallpaper/sources.json"
check_file "$HOME/.config/arch-hyprland/wallpaper/state.json"
check_file "$HOME/.config/arch-hyprland/wallpaper/labels.json"

echo
echo "-- Checking script files --"
check_file "$HOME/.local/bin/power-menu.sh"
check_file "$HOME/.local/bin/screenshot.sh"
check_file "$HOME/.local/bin/volume.sh"
check_file "$HOME/.local/bin/brightness.sh"
check_file "$HOME/.local/bin/wallpaper-apply.sh"
check_file "$HOME/.local/bin/wallpaper-local.sh"
check_file "$HOME/.local/bin/wallpaper-fetch.sh"
check_file "$HOME/.local/bin/wallpaper-random.sh"
check_file "$HOME/.local/bin/wallpaper-menu.sh"
check_file "$HOME/.local/bin/wallpaper-settings.sh"
check_file "$HOME/.local/bin/wallpaper-video.sh"
check_file "$HOME/.local/bin/settings-menu.sh"
check_file "$HOME/.local/bin/settings-theme.sh"
check_file "$HOME/.local/bin/settings-waybar.sh"
check_file "$HOME/.local/bin/settings-system.sh"
check_file "$HOME/.local/bin/settings-dev.sh"

echo
echo "-- Checking directories --"
check_dir "$HOME/Pictures/Screenshots"
check_dir "$HOME/.config/waybar/themes"
check_dir "$HOME/.local/share/arch-hyprland/wallpapers/static"
check_dir "$HOME/.local/share/arch-hyprland/wallpapers/cache"

echo
echo "-- Checking permissions --"
for script in \
  "$HOME/.local/bin/power-menu.sh" \
  "$HOME/.local/bin/screenshot.sh" \
  "$HOME/.local/bin/volume.sh" \
  "$HOME/.local/bin/brightness.sh" \
  "$HOME/.local/bin/wallpaper-apply.sh" \
  "$HOME/.local/bin/wallpaper-local.sh" \
  "$HOME/.local/bin/wallpaper-fetch.sh" \
  "$HOME/.local/bin/wallpaper-random.sh" \
  "$HOME/.local/bin/wallpaper-menu.sh" \
  "$HOME/.local/bin/wallpaper-settings.sh" \
  "$HOME/.local/bin/wallpaper-video.sh" \
  "$HOME/.local/bin/settings-menu.sh" \
  "$HOME/.local/bin/settings-theme.sh" \
  "$HOME/.local/bin/settings-waybar.sh" \
  "$HOME/.local/bin/settings-system.sh" \
  "$HOME/.local/bin/settings-dev.sh"
do
  if [ -x "$script" ]; then
    echo "[OK] executable: $script"
    ok=$((ok + 1))
  else
    echo "[WARN] not executable: $script"
    warn=$((warn + 1))
  fi
done

echo
echo "-- Checking services --"
check_service_enabled bluetooth
check_service_active bluetooth
check_service_enabled NetworkManager
check_service_active NetworkManager

echo
echo "-- Verifying Hyprland config --"
if Hyprland --verify-config -c "$HOME/.config/hypr/hyprland.conf" >/dev/null 2>&1; then
  echo "[OK] Hyprland config verified"
  ok=$((ok + 1))
else
  echo "[ERR] Hyprland config verification failed"
  err=$((err + 1))
fi

echo
echo "-- Verifying Waybar JSON --"
if jq . "$HOME/.config/waybar/config.jsonc" >/dev/null 2>&1; then
  echo "[OK] Waybar config JSON valid"
  ok=$((ok + 1))
else
  echo "[ERR] Waybar config JSON invalid"
  err=$((err + 1))
fi

echo
echo "-- Checking shell script syntax --"
for script in \
  "$HOME/.local/bin/power-menu.sh" \
  "$HOME/.local/bin/screenshot.sh" \
  "$HOME/.local/bin/volume.sh" \
  "$HOME/.local/bin/brightness.sh" \
  "$HOME/.local/bin/wallpaper-apply.sh" \
  "$HOME/.local/bin/wallpaper-local.sh" \
  "$HOME/.local/bin/wallpaper-fetch.sh" \
  "$HOME/.local/bin/wallpaper-random.sh" \
  "$HOME/.local/bin/wallpaper-menu.sh" \
  "$HOME/.local/bin/wallpaper-settings.sh" \
  "$HOME/.local/bin/wallpaper-video.sh" \
  "$HOME/.local/bin/settings-menu.sh" \
  "$HOME/.local/bin/settings-theme.sh" \
  "$HOME/.local/bin/settings-waybar.sh" \
  "$HOME/.local/bin/settings-system.sh" \
  "$HOME/.local/bin/settings-dev.sh"
do
  if bash -n "$script" >/dev/null 2>&1; then
    echo "[OK] shell syntax valid: $script"
    ok=$((ok + 1))
  else
    echo "[ERR] shell syntax invalid: $script"
    err=$((err + 1))
  fi
done

echo
echo "== Summary =="
echo "OK:   $ok"
echo "WARN: $warn"
echo "ERR:  $err"

if [ "$err" -gt 0 ]; then
  exit 1
else
  exit 0
fi