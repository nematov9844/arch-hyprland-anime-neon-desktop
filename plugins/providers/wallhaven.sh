#!/usr/bin/env bash

set -e

ACTION="${1:-}"
QUERY="${2:-}"
URL="${2:-}"
DEST="${3:-}"

case "$ACTION" in
  search)
    curl -fsSL --get "https://wallhaven.cc/api/v1/search" --data-urlencode "q=$QUERY"
    ;;
  download)
    [ -n "$URL" ] && [ -n "$DEST" ] || exit 1
    curl -fsSL "$URL" -o "$DEST"
    ;;
  *)
    echo "Usage: $0 {search <query>|download <url> <dest>}"
    exit 1
    ;;
esac
