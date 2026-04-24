#!/usr/bin/env bash

set -e

BASE_DIR="$HOME/.local/share/arch-hyprland-anime-neon-desktop/backups"

if [ ! -d "$BASE_DIR" ]; then
  echo "No backup directory found: $BASE_DIR"
  exit 1
fi

LATEST_BACKUP="${1:-$(ls -1 "$BASE_DIR" | sort | tail -n 1)}"

if [ -z "$LATEST_BACKUP" ]; then
  echo "No backups found."
  exit 1
fi

BACKUP_DIR="$BASE_DIR/$LATEST_BACKUP"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup not found: $BACKUP_DIR"
  exit 1
fi

echo "==> Restoring from: $BACKUP_DIR"

mkdir -p "$HOME/.config"
mkdir -p "$HOME/.local/bin"

restore_if_exists() {
  local src="$1"
  local dst="$2"

  if [ -e "$src" ]; then
    echo "==> Restoring: $src -> $dst"
    cp -r "$src" "$dst"
  else
    echo "==> Skipping missing: $src"
  fi
}

restore_if_exists "$BACKUP_DIR/config/hypr" "$HOME/.config/"
restore_if_exists "$BACKUP_DIR/config/waybar" "$HOME/.config/"
restore_if_exists "$BACKUP_DIR/config/wofi" "$HOME/.config/"
restore_if_exists "$BACKUP_DIR/config/kitty" "$HOME/.config/"
restore_if_exists "$BACKUP_DIR/config/hyprlock" "$HOME/.config/"
restore_if_exists "$BACKUP_DIR/config/hypridle" "$HOME/.config/"

restore_if_exists "$BACKUP_DIR/bin/power-menu.sh" "$HOME/.local/bin/"
restore_if_exists "$BACKUP_DIR/bin/screenshot.sh" "$HOME/.local/bin/"
restore_if_exists "$BACKUP_DIR/bin/volume.sh" "$HOME/.local/bin/"
restore_if_exists "$BACKUP_DIR/bin/brightness.sh" "$HOME/.local/bin/"
restore_if_exists "$BACKUP_DIR/bin/theme-switch.sh" "$HOME/.local/bin/"

chmod +x "$HOME/.local/bin/"*.sh 2>/dev/null || true

echo
echo "==> Restore completed"
echo "==> Reload Hyprland with: hyprctl reload"