#!/usr/bin/env bash
# =============================================================================
# Waybar Brightness & Display Manager Wrapper
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    --up|up)
        STEP="${2:-5}"
        python3 "${SCRIPT_DIR}/brightness-manager.py" up "$STEP"
        ;;
    --down|down)
        STEP="${2:-5}"
        python3 "${SCRIPT_DIR}/brightness-manager.py" down "$STEP"
        ;;
    --set|set)
        python3 "${SCRIPT_DIR}/brightness-manager.py" set "$2"
        ;;
    --nightlight|-n|nightlight)
        python3 "${SCRIPT_DIR}/brightness-manager.py" nightlight
        ;;
    --tui|-t)
        kitty --class="brightness-floating" -e python3 "${SCRIPT_DIR}/brightness-manager.py" --tui
        ;;
    --menu|-m)
        python3 "${SCRIPT_DIR}/brightness-manager.py" --menu
        ;;
    --gui|-g|*)
        python3 "${SCRIPT_DIR}/brightness-manager.py" --gui
        ;;
esac
