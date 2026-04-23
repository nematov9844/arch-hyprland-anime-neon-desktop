#!/usr/bin/env bash

STEP=5

case "$1" in
  up)
    pamixer -i $STEP
    ;;
  down)
    pamixer -d $STEP
    ;;
  mute)
    pamixer -t
    ;;
  *)
    echo "Usage: $0 {up|down|mute}"
    exit 1
    ;;
esac

VOLUME=$(pamixer --get-volume)
MUTE=$(pamixer --get-mute)

if [ "$MUTE" = "true" ]; then
  notify-send "Volume" "Muted"
else
  notify-send "Volume" "$VOLUME%"
fi