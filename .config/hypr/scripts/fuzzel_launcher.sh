#!/bin/bash
# =============================================================================
# Fuzzel Application Launcher Wrapper
# Handles toggle (open/close) functionality cleanly on Hyprland/Wayland
# =============================================================================

# If fuzzel is already running, toggle (kill) and exit
if pgrep -x "fuzzel" > /dev/null 2>&1; then
    killall fuzzel 2>/dev/null
    exit 0
fi

# Launch fuzzel directly
exec fuzzel "$@"

