#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="${1:-default}"
MANIFEST="$HOME/.config/arch-hyprland/manifest.json"

echo "==> Selected profile: $PROFILE"

init_manifest() {
  mkdir -p "$(dirname "$MANIFEST")"
  [ -f "$MANIFEST" ] || echo '{"installed_files":[],"installed_dirs":[]}' > "$MANIFEST"
}

add_file() {
  local path="$1"
  local tmp
  tmp="$(mktemp)"
  jq --arg p "$path" '.installed_files += [$p] | .installed_files |= unique' "$MANIFEST" > "$tmp"
  mv "$tmp" "$MANIFEST"
}

add_dir() {
  local path="$1"
  local tmp
  tmp="$(mktemp)"
  jq --arg p "$path" '.installed_dirs += [$p] | .installed_dirs |= unique' "$MANIFEST" > "$tmp"
  mv "$tmp" "$MANIFEST"
}

mkdir_track() {
  local path="$1"
  mkdir -p "$path"
  add_dir "$path"
}

copy_file_track() {
  local src="$1"
  local dst="$2"
  cp "$src" "$dst"
  add_file "$dst"
}

copy_dir_contents_track() {
  local src_dir="$1"
  local dst_dir="$2"
  local rel
  find "$src_dir" -type f | while read -r src_file; do
    rel="${src_file#"$src_dir"/}"
    mkdir -p "$dst_dir/$(dirname "$rel")"
    cp "$src_file" "$dst_dir/$rel"
    add_file "$dst_dir/$rel"
  done
}

install_packages() {
  local file="$1"
  while read -r pkg; do
    [ -z "$pkg" ] && continue
    sudo pacman -S --needed --noconfirm "$pkg"
  done < "$file"
}

case "$PROFILE" in
  default)
    PROFILE_MESSAGE="==> Installing default profile (no dev tools)"
    ;;
  frontend)
    PROFILE_MESSAGE="==> Installing frontend dev tools..."
    ;;
  backend)
    PROFILE_MESSAGE="==> Installing backend dev tools..."
    ;;
  full)
    PROFILE_MESSAGE="==> Installing full dev environment..."
    ;;
  *)
    echo "Unknown profile: $PROFILE"
    echo "Available: default | frontend | backend | full"
    exit 1
    ;;
esac

echo "==> Installing base packages..."
install_packages "$PROJECT_DIR/packages/base.txt"

echo "==> Installing UI packages..."
install_packages "$PROJECT_DIR/packages/ui.txt"

echo "$PROFILE_MESSAGE"
case "$PROFILE" in
  frontend)
    install_packages "$PROJECT_DIR/packages/dev-frontend.txt"
    ;;
  backend)
    install_packages "$PROJECT_DIR/packages/dev-backend.txt"
    ;;
  full)
    install_packages "$PROJECT_DIR/packages/dev-frontend.txt"
    install_packages "$PROJECT_DIR/packages/dev-backend.txt"
    ;;
esac

read -r -p "Install optional packages? (y/N): " opt
if [[ "$opt" =~ ^[Yy]$ ]]; then
  echo "==> Installing optional packages..."
  install_packages "$PROJECT_DIR/packages/optional.txt"
fi

init_manifest

echo "==> Creating config directories..."
mkdir_track "$HOME/.config/hypr"
mkdir_track "$HOME/.config/waybar"
mkdir_track "$HOME/.config/wofi"
mkdir_track "$HOME/.config/kitty"
mkdir_track "$HOME/.config/hyprlock"
mkdir_track "$HOME/.config/hypridle"
mkdir_track "$HOME/.config/settings"
mkdir_track "$HOME/.local/bin"
mkdir_track "$HOME/.config/arch-hyprland/wallpaper"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/static"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/cache"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/live"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/previews"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/favorites"



echo "==> Backing up old configs..."
[ -d "$HOME/.config/hypr" ] && cp -rn "$HOME/.config/hypr" "$HOME/.config/hypr.backup.$(date +%s)" || true
[ -d "$HOME/.config/waybar" ] && cp -rn "$HOME/.config/waybar" "$HOME/.config/waybar.backup.$(date +%s)" || true
[ -d "$HOME/.config/wofi" ] && cp -rn "$HOME/.config/wofi" "$HOME/.config/wofi.backup.$(date +%s)" || true
[ -d "$HOME/.config/kitty" ] && cp -rn "$HOME/.config/kitty" "$HOME/.config/kitty.backup.$(date +%s)" || true

echo "==> Copying configs..."
copy_dir_contents_track "$PROJECT_DIR/config/hypr" "$HOME/.config/hypr"
copy_dir_contents_track "$PROJECT_DIR/config/waybar" "$HOME/.config/waybar"
copy_dir_contents_track "$PROJECT_DIR/config/wofi" "$HOME/.config/wofi"
copy_dir_contents_track "$PROJECT_DIR/config/kitty" "$HOME/.config/kitty"
copy_dir_contents_track "$PROJECT_DIR/config/hyprlock" "$HOME/.config/hypr"
copy_dir_contents_track "$PROJECT_DIR/config/hypridle" "$HOME/.config/hypr"
copy_dir_contents_track "$PROJECT_DIR/config/wallpaper" "$HOME/.config/arch-hyprland/wallpaper"
copy_dir_contents_track "$PROJECT_DIR/config/settings" "$HOME/.config/settings"
if [ -d "$PROJECT_DIR/assets/wallpapers/static" ]; then
  cp -rn "$PROJECT_DIR/assets/wallpapers/static/"* "$HOME/.local/share/arch-hyprland/wallpapers/static/" 2>/dev/null || true
fi


echo "==> Installing scripts..."
copy_file_track "$PROJECT_DIR/scripts/ui/power-menu.sh" "$HOME/.local/bin/power-menu.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/screenshot.sh" "$HOME/.local/bin/screenshot.sh"
copy_file_track "$PROJECT_DIR/scripts/system/volume.sh" "$HOME/.local/bin/volume.sh"
copy_file_track "$PROJECT_DIR/scripts/system/brightness.sh" "$HOME/.local/bin/brightness.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-menu.sh" "$HOME/.local/bin/settings-menu.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-theme.sh" "$HOME/.local/bin/settings-theme.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-waybar.sh" "$HOME/.local/bin/settings-waybar.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-system.sh" "$HOME/.local/bin/settings-system.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-dev.sh" "$HOME/.local/bin/settings-dev.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-apply.sh" "$HOME/.local/bin/wallpaper-apply.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-local.sh" "$HOME/.local/bin/wallpaper-local.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-search.sh" "$HOME/.local/bin/wallpaper-search.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-fetch.sh" "$HOME/.local/bin/wallpaper-fetch.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-random.sh" "$HOME/.local/bin/wallpaper-random.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-menu.sh" "$HOME/.local/bin/wallpaper-menu.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-history.sh" "$HOME/.local/bin/wallpaper-history.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-favorites.sh" "$HOME/.local/bin/wallpaper-favorites.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-favorite-add.sh" "$HOME/.local/bin/wallpaper-favorite-add.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-settings.sh" "$HOME/.local/bin/wallpaper-settings.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-preview.sh" "$HOME/.local/bin/wallpaper-preview.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-video.sh" "$HOME/.local/bin/wallpaper-video.sh"
copy_file_track "$PROJECT_DIR/doctor.sh" "$HOME/.local/bin/arch-hypr-doctor"
copy_file_track "$PROJECT_DIR/backup.sh" "$HOME/.local/bin/arch-hypr-backup"
copy_file_track "$PROJECT_DIR/restore.sh" "$HOME/.local/bin/arch-hypr-restore"
copy_file_track "$PROJECT_DIR/update.sh" "$HOME/.local/bin/arch-hypr-update"

if [ -f "$PROJECT_DIR/scripts/ui/theme-switch.sh" ]; then
  copy_file_track "$PROJECT_DIR/scripts/ui/theme-switch.sh" "$HOME/.local/bin/theme-switch.sh"
fi

chmod +x "$HOME/.local/bin/"*.sh
chmod +x "$HOME/.local/bin/arch-hypr-doctor" "$HOME/.local/bin/arch-hypr-backup" "$HOME/.local/bin/arch-hypr-restore" "$HOME/.local/bin/arch-hypr-update"

echo "==> Ensuring local.conf exists..."
touch "$HOME/.config/hypr/local.conf"
add_file "$HOME/.config/hypr/local.conf"

echo "==> Done."
echo "Reload Hyprland with: hyprctl reload"