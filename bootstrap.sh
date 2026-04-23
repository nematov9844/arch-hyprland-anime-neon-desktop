#!/usr/bin/env bash

set -euo pipefail

REPO="${REPO:-https://github.com/nematov9844/arch-hyprland-anime-neon-desktop.git}"
DIR="${DIR:-$HOME/.cache/arch-hyprland}"

echo "==> Downloading project..."
rm -rf "$DIR"
git clone "$REPO" "$DIR"

cd "$DIR"

echo "==> Running installer..."
bash install.sh "$@"
