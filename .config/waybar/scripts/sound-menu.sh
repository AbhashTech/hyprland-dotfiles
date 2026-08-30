#!/usr/bin/env bash
# Sound launcher script for Waybar
# Launches Sound Manager Menu or TUI Mixer

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" == "--tui" ] || [ "$1" == "-t" ]; then
    kitty --class="soundctl-floating" -e python3 "${SCRIPT_DIR}/sound-manager.py" --tui
else
    python3 "${SCRIPT_DIR}/sound-manager.py" "$@"
fi
