#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="default"
MANIFEST="$HOME/.config/arch-hyprland/manifest.json"
SKIP_PACKAGES=0
NO_AUR=0

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-packages)
      SKIP_PACKAGES=1
      shift
      ;;
    --no-aur)
      NO_AUR=1
      shift
      ;;
    --profile)
      PROFILE="${2:-default}"
      shift 2
      ;;
    default|frontend|backend|full)
      PROFILE="$1"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: bash install.sh [default|frontend|backend|full] [--profile <name>] [--skip-packages] [--no-aur]"
      exit 1
      ;;
  esac
done

echo "==> Selected profile: $PROFILE"

init_manifest() {
  mkdir -p "$(dirname "$MANIFEST")"
  [ -f "$MANIFEST" ] || echo '{"installed_files":[],"installed_dirs":[]}' > "$MANIFEST"
}

safe_write_json_file() {
  local temp_file="$1"
  local target_file="$2"
  if mv "$temp_file" "$target_file" 2>/dev/null; then
    return 0
  fi
  if cp "$temp_file" "$target_file" 2>/dev/null; then
    rm -f "$temp_file"
    return 0
  fi
  rm -f "$temp_file"
  return 1
}

add_file() {
  local path="$1"
  local tmp
  tmp="$(mktemp "$(dirname "$MANIFEST")/.manifest.XXXXXX")"
  if jq --arg p "$path" '.installed_files += [$p] | .installed_files |= unique' "$MANIFEST" > "$tmp"; then
    if ! safe_write_json_file "$tmp" "$MANIFEST"; then
      echo "==> [WARN] Failed to write manifest file entry: $path"
    fi
  else
    rm -f "$tmp"
    echo "==> [WARN] jq failed while updating manifest file entry: $path"
  fi
}

add_dir() {
  local path="$1"
  local tmp
  tmp="$(mktemp "$(dirname "$MANIFEST")/.manifest.XXXXXX")"
  if jq --arg p "$path" '.installed_dirs += [$p] | .installed_dirs |= unique' "$MANIFEST" > "$tmp"; then
    if ! safe_write_json_file "$tmp" "$MANIFEST"; then
      echo "==> [WARN] Failed to write manifest directory entry: $path"
    fi
  else
    rm -f "$tmp"
    echo "==> [WARN] jq failed while updating manifest directory entry: $path"
  fi
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
  if [ ! -d "$src_dir" ]; then
    echo "==> [WARN] Missing config directory, skipping: $src_dir"
    return 0
  fi
  find "$src_dir" -type f | while read -r src_file; do
    rel="${src_file#"$src_dir"/}"
    mkdir -p "$dst_dir/$(dirname "$rel")"
    cp "$src_file" "$dst_dir/$rel"
    add_file "$dst_dir/$rel"
  done
}

install_packages() {
  local file="$1"
  local aur_helper="$2"
  while read -r pkg; do
    [ -z "$pkg" ] && continue
    case "$pkg" in
      \#*) continue ;;
    esac
    try_install_package "$pkg" "$aur_helper"
  done < "$file"
}

try_install_package() {
  local pkg="$1"
  local helper="$2"
  if sudo pacman -S --needed --noconfirm "$pkg" >/dev/null 2>&1; then
    echo "==> [OK] Installed package: $pkg"
    return 0
  fi

  echo "==> [WARN] Official package install failed: $pkg"

  if [ "$NO_AUR" -eq 0 ] && [ -n "$helper" ]; then
    if "$helper" -S --needed --noconfirm "$pkg" >/dev/null 2>&1; then
      echo "==> [OK] Installed from AUR ($helper): $pkg"
      return 0
    fi
    echo "==> [WARN] AUR install failed: $pkg"
  fi
  return 0
}

detect_aur_helper() {
  if [ "$NO_AUR" -eq 1 ]; then
    echo ""
    return
  fi
  if command -v yay >/dev/null 2>&1; then
    echo "yay"
    return
  fi
  if command -v paru >/dev/null 2>&1; then
    echo "paru"
    return
  fi
  echo ""
}

check_cmd_present() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1
}

verify_command_group() {
  local label="$1"
  local required="$2"
  shift 2
  local missing=0
  local cmd
  for cmd in "$@"; do
    if check_cmd_present "$cmd"; then
      echo "==> [OK] $label command: $cmd"
    else
      if [ "$required" = "1" ]; then
        echo "==> [ERR] Missing required command: $cmd"
      else
        echo "==> [WARN] Missing $label command: $cmd"
      fi
      missing=$((missing + 1))
    fi
  done
  return "$missing"
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

AUR_HELPER="$(detect_aur_helper)"

if [ "$SKIP_PACKAGES" -eq 1 ]; then
  echo "==> Skipping package installation (--skip-packages)"
else
  echo "==> Installing base packages..."
  install_packages "$PROJECT_DIR/packages/base.txt" "$AUR_HELPER"

  read -r -p "Install UI packages? (Y/n): " ui_ans
  if [[ ! "$ui_ans" =~ ^[Nn]$ ]]; then
    echo "==> Installing UI packages..."
    install_packages "$PROJECT_DIR/packages/ui.txt" "$AUR_HELPER"
  else
    echo "==> Skipping UI packages"
  fi

  echo "$PROFILE_MESSAGE"
  case "$PROFILE" in
    frontend)
      read -r -p "Install frontend dev packages? (Y/n): " fe_ans
      if [[ ! "$fe_ans" =~ ^[Nn]$ ]]; then
        install_packages "$PROJECT_DIR/packages/dev-frontend.txt" "$AUR_HELPER"
      fi
      ;;
    backend)
      read -r -p "Install backend dev packages? (Y/n): " be_ans
      if [[ ! "$be_ans" =~ ^[Nn]$ ]]; then
        install_packages "$PROJECT_DIR/packages/dev-backend.txt" "$AUR_HELPER"
      fi
      ;;
    full)
      read -r -p "Install frontend dev packages? (Y/n): " fe_ans
      if [[ ! "$fe_ans" =~ ^[Nn]$ ]]; then
        install_packages "$PROJECT_DIR/packages/dev-frontend.txt" "$AUR_HELPER"
      fi
      read -r -p "Install backend dev packages? (Y/n): " be_ans
      if [[ ! "$be_ans" =~ ^[Nn]$ ]]; then
        install_packages "$PROJECT_DIR/packages/dev-backend.txt" "$AUR_HELPER"
      fi
      ;;
  esac

  read -r -p "Install optional packages? (y/N): " opt
  if [[ "$opt" =~ ^[Yy]$ ]]; then
    echo "==> Installing optional packages..."
    install_packages "$PROJECT_DIR/packages/optional.txt" "$AUR_HELPER"
  fi
fi

init_manifest

echo "==> Creating config directories..."
mkdir_track "$HOME/.config/hypr"
mkdir_track "$HOME/.config/waybar"
mkdir_track "$HOME/.config/wofi"
mkdir_track "$HOME/.config/kitty"
mkdir_track "$HOME/.config/settings"
mkdir_track "$HOME/.local/bin"
mkdir_track "$HOME/.config/arch-hyprland"
mkdir_track "$HOME/.config/arch-hyprland/wallpaper"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/static"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/library"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/cache"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/live"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/previews"
mkdir_track "$HOME/.local/share/arch-hyprland/wallpapers/favorites"
mkdir_track "$HOME/.local/share/arch-hyprland/apps"
mkdir_track "$HOME/.local/share/arch-hyprland/localization"



echo "==> Backing up old configs..."
[ -d "$HOME/.config/hypr" ] && cp -rn "$HOME/.config/hypr" "$HOME/.config/hypr.backup.$(date +%s)" || true
[ -d "$HOME/.config/waybar" ] && cp -rn "$HOME/.config/waybar" "$HOME/.config/waybar.backup.$(date +%s)" || true
[ -d "$HOME/.config/wofi" ] && cp -rn "$HOME/.config/wofi" "$HOME/.config/wofi.backup.$(date +%s)" || true
[ -d "$HOME/.config/kitty" ] && cp -rn "$HOME/.config/kitty" "$HOME/.config/kitty.backup.$(date +%s)" || true

echo "==> Copying configs..."
WALL_CFG_TARGET="$HOME/.config/arch-hyprland/wallpaper/config.json"
OLD_PEXELS_KEY=""
OLD_UNSPLASH_KEY=""
OLD_PIXABAY_KEY=""
if [ -f "$WALL_CFG_TARGET" ]; then
  OLD_PEXELS_KEY="$(jq -r '.pexels.api_key // ""' "$WALL_CFG_TARGET" 2>/dev/null || echo "")"
  OLD_UNSPLASH_KEY="$(jq -r '.unsplash.api_key // ""' "$WALL_CFG_TARGET" 2>/dev/null || echo "")"
  OLD_PIXABAY_KEY="$(jq -r '.pixabay.api_key // ""' "$WALL_CFG_TARGET" 2>/dev/null || echo "")"
fi
copy_dir_contents_track "$PROJECT_DIR/config/hypr" "$HOME/.config/hypr"
copy_dir_contents_track "$PROJECT_DIR/config/waybar" "$HOME/.config/waybar"
copy_dir_contents_track "$PROJECT_DIR/config/wofi" "$HOME/.config/wofi"
copy_dir_contents_track "$PROJECT_DIR/config/kitty" "$HOME/.config/kitty"
copy_dir_contents_track "$PROJECT_DIR/config/wallpaper" "$HOME/.config/arch-hyprland/wallpaper"
if [ -f "$WALL_CFG_TARGET" ]; then
  TMP_WALL_CFG="$(mktemp)"
  jq --arg p "$OLD_PEXELS_KEY" \
     --arg u "$OLD_UNSPLASH_KEY" \
     --arg x "$OLD_PIXABAY_KEY" \
     '.pexels.api_key = (if $p != "" then $p else .pexels.api_key end)
      | .unsplash.api_key = (if $u != "" then $u else .unsplash.api_key end)
      | .pixabay.api_key = (if $x != "" then $x else .pixabay.api_key end)' \
     "$WALL_CFG_TARGET" > "$TMP_WALL_CFG" && mv "$TMP_WALL_CFG" "$WALL_CFG_TARGET"
fi
copy_dir_contents_track "$PROJECT_DIR/config/settings" "$HOME/.config/settings"
if [ -f "$PROJECT_DIR/config/hyprlock/hyprlock.conf" ]; then
  copy_file_track "$PROJECT_DIR/config/hyprlock/hyprlock.conf" "$HOME/.config/hypr/hyprlock.conf"
fi
if [ -f "$PROJECT_DIR/config/hypridle/hypridle.conf" ]; then
  copy_file_track "$PROJECT_DIR/config/hypridle/hypridle.conf" "$HOME/.config/hypr/hypridle.conf"
fi
if [ -f "$PROJECT_DIR/config/hypr/hyprpaper.conf" ]; then
  copy_file_track "$PROJECT_DIR/config/hypr/hyprpaper.conf" "$HOME/.config/hypr/hyprpaper.conf"
fi
if [ -d "$PROJECT_DIR/assets/wallpapers/static" ]; then
  cp -rn "$PROJECT_DIR/assets/wallpapers/static/"* "$HOME/.local/share/arch-hyprland/wallpapers/static/" 2>/dev/null || true
fi
if [ -d "$HOME/.local/share/arch-hyprland/wallpapers/static" ]; then
  cp -rn "$HOME/.local/share/arch-hyprland/wallpapers/static/"* "$HOME/.local/share/arch-hyprland/wallpapers/library/" 2>/dev/null || true
fi

if [ -d "$PROJECT_DIR/apps/settings-center" ]; then
  echo "==> Installing Settings Center app..."
  rm -rf "$HOME/.local/share/arch-hyprland/apps/settings-center"
  copy_dir_contents_track "$PROJECT_DIR/apps/settings-center" "$HOME/.local/share/arch-hyprland/apps/settings-center"
fi

if [ -d "$PROJECT_DIR/localization" ]; then
  echo "==> Installing localization files..."
  copy_dir_contents_track "$PROJECT_DIR/localization" "$HOME/.local/share/arch-hyprland/localization"
fi

if [ -f "$PROJECT_DIR/VERSION" ]; then
  copy_file_track "$PROJECT_DIR/VERSION" "$HOME/.local/share/arch-hyprland/VERSION"
fi


echo "==> Installing scripts..."
copy_file_track "$PROJECT_DIR/scripts/ui/power-menu.sh" "$HOME/.local/bin/power-menu.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/screenshot.sh" "$HOME/.local/bin/screenshot.sh"
copy_file_track "$PROJECT_DIR/scripts/system/volume.sh" "$HOME/.local/bin/volume.sh"
copy_file_track "$PROJECT_DIR/scripts/system/brightness.sh" "$HOME/.local/bin/brightness.sh"
# Compatibility layer: keep legacy Wofi menus while migrating to app-first Settings Center.
copy_file_track "$PROJECT_DIR/scripts/ui/settings-menu.sh" "$HOME/.local/bin/settings-menu.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-theme.sh" "$HOME/.local/bin/settings-theme.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-waybar.sh" "$HOME/.local/bin/settings-waybar.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/waybar-restart.sh" "$HOME/.local/bin/waybar-restart.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/start-waybar.sh" "$HOME/.local/bin/start-waybar.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-system.sh" "$HOME/.local/bin/settings-system.sh"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-center.sh" "$HOME/.local/bin/settings-center"
copy_file_track "$PROJECT_DIR/scripts/ui/settings-dev.sh" "$HOME/.local/bin/settings-dev.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-apply.sh" "$HOME/.local/bin/wallpaper-apply.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-local.sh" "$HOME/.local/bin/wallpaper-local.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-search.sh" "$HOME/.local/bin/wallpaper-search.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-fetch.sh" "$HOME/.local/bin/wallpaper-fetch.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-pexels.sh" "$HOME/.local/bin/wallpaper-pexels.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-random.sh" "$HOME/.local/bin/wallpaper-random.sh"
# Compatibility layer: legacy wallpaper menu redirects to settings-center.
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-menu.sh" "$HOME/.local/bin/wallpaper-menu.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-history.sh" "$HOME/.local/bin/wallpaper-history.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-favorites.sh" "$HOME/.local/bin/wallpaper-favorites.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-favorite-add.sh" "$HOME/.local/bin/wallpaper-favorite-add.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-settings.sh" "$HOME/.local/bin/wallpaper-settings.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-preview.sh" "$HOME/.local/bin/wallpaper-preview.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-video.sh" "$HOME/.local/bin/wallpaper-video.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-video-apply.sh" "$HOME/.local/bin/wallpaper-video-apply.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-video-local.sh" "$HOME/.local/bin/wallpaper-video-local.sh"
copy_file_track "$PROJECT_DIR/scripts/wallpaper/wallpaper-stop-video.sh" "$HOME/.local/bin/wallpaper-stop-video.sh"
copy_file_track "$PROJECT_DIR/doctor.sh" "$HOME/.local/bin/arch-hypr-doctor"
copy_file_track "$PROJECT_DIR/backup.sh" "$HOME/.local/bin/arch-hypr-backup"
copy_file_track "$PROJECT_DIR/restore.sh" "$HOME/.local/bin/arch-hypr-restore"
copy_file_track "$PROJECT_DIR/update.sh" "$HOME/.local/bin/arch-hypr-update"

if [ -f "$PROJECT_DIR/scripts/ui/theme-switch.sh" ]; then
  copy_file_track "$PROJECT_DIR/scripts/ui/theme-switch.sh" "$HOME/.local/bin/theme-switch.sh"
fi

chmod +x "$HOME/.local/bin/"*.sh
chmod +x "$HOME/.local/bin/arch-hypr-doctor" "$HOME/.local/bin/arch-hypr-backup" "$HOME/.local/bin/arch-hypr-restore" "$HOME/.local/bin/arch-hypr-update"
chmod +x "$HOME/.local/bin/settings-center"
chmod +x "$PROJECT_DIR/install.sh" "$PROJECT_DIR/update.sh" "$PROJECT_DIR/doctor.sh" "$PROJECT_DIR/backup.sh" "$PROJECT_DIR/restore.sh" "$PROJECT_DIR/uninstall.sh"

echo "==> Ensuring local.conf exists..."
touch "$HOME/.config/hypr/local.conf"
add_file "$HOME/.config/hypr/local.conf"

if [ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ] && [ -x "$HOME/.local/bin/start-waybar.sh" ]; then
  echo "==> Waybar: takrorlanishlarsiz qayta ishga tushirish..."
  "$HOME/.local/bin/start-waybar.sh" || true
fi

echo "==> Verifying runtime commands..."
required_missing=0
recommended_missing=0
optional_missing=0

verify_command_group "required" 1 \
  hyprctl waybar wofi kitty jq curl || required_missing=$?
verify_command_group "recommended" 0 \
  hyprlock hyprpaper hypridle grim slurp wl-copy pamixer brightnessctl notify-send || recommended_missing=$?
verify_command_group "optional" 0 \
  mpvpaper ffmpeg blueman-manager nm-applet || optional_missing=$?

echo
echo "== Package/command summary =="
echo "Installed attempts: done"
echo "WARN missing recommended: $recommended_missing"
echo "WARN missing optional: $optional_missing"
echo "ERR missing required: $required_missing"

echo "==> Done."
echo "Reload Hyprland with: hyprctl reload"

if [ "$required_missing" -gt 0 ]; then
  echo "==> [ERR] Install completed with missing required commands."
  exit 1
fi