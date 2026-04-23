#!/usr/bin/env bash

set -e

MANIFEST="$HOME/.config/arch-hyprland/manifest.json"

if [ ! -f "$MANIFEST" ]; then
  echo "No manifest found. Nothing to uninstall."
  exit 1
fi

echo "==> Safe uninstall (manifest-based)"
read -rp "Continue? (y/N): " confirm

[[ "$confirm" =~ ^[Yy]$ ]] || exit 0

# Remove files
jq -r '.installed_files[]' "$MANIFEST" | while read -r file; do
  if [ -e "$file" ]; then
    echo "Removing file: $file"
    rm -f "$file"
  fi
done

# Remove dirs (only if empty)
jq -r '.installed_dirs[]' "$MANIFEST" | while read -r dir; do
  if [ -d "$dir" ]; then
    rmdir "$dir" 2>/dev/null || true
  fi
done

rm -f "$MANIFEST"

echo "==> Uninstall completed safely"