#!/usr/bin/env bash

# Power menu script for Waybar / Hyprland

options="󰌾  Lock\n󰍃  Logout\n󰒲  Suspend\n󰑐  Reboot\n󰐥  Shutdown"

if command -v fuzzel >/dev/null 2>&1; then
    chosen=$(echo -e "$options" | fuzzel --dmenu --prompt " 󰐥 Session: " --width 24 --lines 5)
else
    chosen=$(echo -e "$options" | wofi --dmenu \
        --prompt "Session" \
        --width 280 \
        --height 230 \
        --cache-file /dev/null \
        --hide-scroll \
        --allow-markup \
        --lines 5 \
        --insensitive)
fi

case "$chosen" in
    *"Lock"*)
        if command -v hyprlock >/dev/null 2>&1; then
            hyprlock
        elif command -v swaylock >/dev/null 2>&1; then
            swaylock -f -c 1e1e2e
        fi
        ;;
    *"Logout"*)
        if command -v uwsm >/dev/null 2>&1 && [ -n "$UWSM_APP_ID" ]; then
            uwsm stop
        else
            hyprctl dispatch 'hl.dsp.exit()' 2>/dev/null || hyprctl dispatch exit 2>/dev/null || loginctl terminate-session "${XDG_SESSION_ID}" 2>/dev/null || loginctl terminate-user "$USER" 2>/dev/null || pkill -u "$USER" -x Hyprland
        fi
        ;;
    *"Suspend"*)
        systemctl suspend
        ;;
    *"Reboot"*)
        systemctl reboot
        ;;
    *"Shutdown"*)
        systemctl poweroff
        ;;
esac
