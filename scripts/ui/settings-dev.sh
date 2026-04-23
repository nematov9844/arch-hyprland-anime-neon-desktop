#!/usr/bin/env bash

set -e

CHOICE=$(printf "Open Project\nGit Status\nRun Update Script" | \
  wofi --dmenu --prompt "Developer Settings")

[ -z "$CHOICE" ] && exit 0

case "$CHOICE" in
  "Open Project")
    kitty --hold -e bash -lc "cd $HOME/Projects/arch-hyprland-anime-neon-desktop && exec \$SHELL"
    ;;

  "Git Status")
    kitty --hold -e bash -lc "cd $HOME/Projects/arch-hyprland-anime-neon-desktop && git status && exec \$SHELL"
    ;;

  "Run Update Script")
    kitty --hold -e arch-hypr-update
    ;;
esac
