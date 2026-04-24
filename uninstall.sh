#!/usr/bin/env bash

set -e

MANIFEST="$HOME/.config/arch-hyprland/manifest.json"

if [ ! -f "$MANIFEST" ]; then
  echo "No manifest found. Nothing to uninstall."
  exit 1
fi

echo "==> Safe uninstall"
read -rp "Continue? (y/N): " confirm

[[ "$confirm" =~ ^[Yy]$ ]] || exit 0

jq -r '.installed_files[]' "$MANIFEST" | while read -r file; do
  [ -e "$file" ] && rm -f "$file"
done

jq -r '.installed_dirs[]' "$MANIFEST" | tac | while read -r dir; do
  [ -d "$dir" ] && rmdir "$dir" 2>/dev/null || true
done

rm -f "$MANIFEST"

echo "==> Safe uninstall completed"