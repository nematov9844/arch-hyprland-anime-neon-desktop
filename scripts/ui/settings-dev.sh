#!/usr/bin/env bash

set -e

CHOICE=$(printf "Open Project\nGit Status\nRun Update Script" | \
  wofi --dmenu --prompt "Developer Settings")

[ -z "$CHOICE" ] && exit 0

PROJECT_DIR="${ARCH_HYPR_REPO_DIR:-$PWD}"
if [ ! -d "$PROJECT_DIR/.git" ]; then
  PROJECT_DIR="$HOME"
fi

case "$CHOICE" in
  "Open Project")
    kitty --hold -e bash -lc "cd \"$PROJECT_DIR\" && exec \$SHELL"
    ;;

  "Git Status")
    kitty --hold -e bash -lc "cd \"$PROJECT_DIR\" && git status && exec \$SHELL"
    ;;

  "Run Update Script")
    kitty --hold -e arch-hypr-update
    ;;
esac
