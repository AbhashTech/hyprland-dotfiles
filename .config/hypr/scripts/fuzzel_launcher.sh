#!/bin/bash
# =============================================================================
# Fuzzel Click-to-Close Wrapper using Slurp
# Captures outside clicks and closes Fuzzel immediately on Wayland/Hyprland
# =============================================================================

# If fuzzel is already running, toggle (kill) and exit
if pgrep -x "fuzzel" > /dev/null 2>&1; then
    killall fuzzel 2>/dev/null
    pkill -x slurp 2>/dev/null
    exit 0
fi

# Clean up any leftover background slurp monitors
pkill -x slurp 2>/dev/null

# Launch fuzzel in background
fuzzel "$@" &
FUZZEL_PID=$!

# Launch slurp click monitor if slurp is available
if command -v slurp > /dev/null 2>&1; then
    (
        # Wait for click on invisible overlay (-p: single point click, transparent color)
        slurp -p -b 00000000 -c 00000000 -B 00000000 > /dev/null 2>&1
        # When clicked outside, kill fuzzel
        kill "$FUZZEL_PID" 2>/dev/null
        killall fuzzel 2>/dev/null
    ) &
    SLURP_PID=$!

    # Monitor fuzzel process: when it exits (app launched or Esc pressed), kill slurp
    while kill -0 "$FUZZEL_PID" 2>/dev/null; do
        sleep 0.05
    done

    # Clean up slurp overlay
    kill "$SLURP_PID" 2>/dev/null
    pkill -x slurp 2>/dev/null
else
    # Fallback if slurp is not installed yet
    wait "$FUZZEL_PID" 2>/dev/null
fi
