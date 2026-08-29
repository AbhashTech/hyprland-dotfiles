#!/usr/bin/env bash

# Network launcher script for Waybar
# Launches modern NETCTL-TUI in Kitty floating window

if command -v kitty >/dev/null 2>&1; then
    kitty --class="netctl-floating" -e /home/kunal/.config/waybar/scripts/netctl-tui.py &
elif command -v iwctl >/dev/null 2>&1; then
    kitty --class="netctl-floating" -e iwctl &
fi
