#!/usr/bin/env bash

set -euo pipefail

REPO_OWNER="${REPO_OWNER:-nematov9844}"
REPO_NAME="${REPO_NAME:-arch-hyprland-anime-neon-desktop}"
REPO_BRANCH="${REPO_BRANCH:-main}"
TMP_DIR="${TMPDIR:-/tmp}/${REPO_NAME}-setup"

echo "==> Downloading project tarball..."
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

curl -fsSL "https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${REPO_BRANCH}.tar.gz" \
  | tar -xz -C "$TMP_DIR" --strip-components=1

cd "$TMP_DIR"

echo "==> Running installer..."
bash install.sh "$@"
