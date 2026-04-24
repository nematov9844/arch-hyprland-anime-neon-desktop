#!/usr/bin/env bash
# Restarts top bar with generated-config fallback, and keeps dock controlled separately.

set -euo pipefail

"$HOME/.local/bin/start-waybar.sh"

if command -v jq >/dev/null 2>&1 && [ -f "$HOME/.config/settings/config.json" ]; then
  if [ "$(jq -r '.waybar.dock_enabled // false' "$HOME/.config/settings/config.json")" = "true" ]; then
    # Restart dock only when enabled.
    pkill -f "waybar -c $HOME/.config/waybar/dock.jsonc" 2>/dev/null || true
    sleep 0.2
    waybar -c "$HOME/.config/waybar/dock.jsonc" -s "$HOME/.config/waybar/dock.css" >/dev/null 2>&1 &
  fi
fi
