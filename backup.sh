#!/usr/bin/env bash

set -e

STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$HOME/.local/share/arch-hyprland-anime-neon-desktop/backups/$STAMP"

echo "==> Creating backup directory..."
mkdir -p "$BACKUP_DIR/config"
mkdir -p "$BACKUP_DIR/bin"

backup_if_exists() {
  local src="$1"
  local dst="$2"

  if [ -e "$src" ]; then
    echo "==> Backing up: $src"
    cp -r "$src" "$dst"
  else
    echo "==> Skipping missing: $src"
  fi
}

backup_if_exists "$HOME/.config/hypr" "$BACKUP_DIR/config/"
backup_if_exists "$HOME/.config/waybar" "$BACKUP_DIR/config/"
backup_if_exists "$HOME/.config/wofi" "$BACKUP_DIR/config/"
backup_if_exists "$HOME/.config/kitty" "$BACKUP_DIR/config/"
backup_if_exists "$HOME/.config/hyprlock" "$BACKUP_DIR/config/"
backup_if_exists "$HOME/.config/hypridle" "$BACKUP_DIR/config/"

backup_if_exists "$HOME/.local/bin/power-menu.sh" "$BACKUP_DIR/bin/"
backup_if_exists "$HOME/.local/bin/screenshot.sh" "$BACKUP_DIR/bin/"
backup_if_exists "$HOME/.local/bin/volume.sh" "$BACKUP_DIR/bin/"
backup_if_exists "$HOME/.local/bin/brightness.sh" "$BACKUP_DIR/bin/"
backup_if_exists "$HOME/.local/bin/theme-switch.sh" "$BACKUP_DIR/bin/"

echo
echo "==> Backup completed"
echo "==> Saved to: $BACKUP_DIR"