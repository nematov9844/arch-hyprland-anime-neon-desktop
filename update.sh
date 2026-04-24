#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Updating installed configs..."

bash "$PROJECT_DIR/install.sh" "${1:-default}"

echo "==> Reloading Hyprland..."
hyprctl reload

echo "==> Restarting Waybar..."
"$HOME/.local/bin/waybar-restart.sh" || true

echo "==> Done"