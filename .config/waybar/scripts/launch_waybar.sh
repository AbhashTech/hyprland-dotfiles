#!/usr/bin/env bash
# =============================================================================
# Waybar Launch & Toggle Controller
# Supports toggling, starting, or restarting Waybar and its Hyprland proxy
# =============================================================================

ACTION="start"
PASSTHROUGH_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --toggle|-t)
            ACTION="toggle"
            ;;
        --start|-s)
            ACTION="start"
            ;;
        --restart|-r)
            ACTION="restart"
            ;;
        *)
            PASSTHROUGH_ARGS+=("$arg")
            ;;
    esac
done

is_waybar_running() {
    pgrep -x waybar >/dev/null
}

stop_waybar() {
    pkill -x waybar 2>/dev/null
    pkill -f launch_waybar.py 2>/dev/null
    sleep 0.15
}

start_waybar() {
    # Clean any stale proxy processes first
    pkill -f launch_waybar.py 2>/dev/null
    python3 "$HOME/.config/waybar/scripts/launch_waybar.py" --daemon "${PASSTHROUGH_ARGS[@]}"
}

case "$ACTION" in
    toggle)
        if is_waybar_running; then
            stop_waybar
        else
            start_waybar
        fi
        ;;
    start)
        if ! is_waybar_running; then
            start_waybar
        fi
        ;;
    restart)
        stop_waybar
        sleep 0.2
        start_waybar
        ;;
esac
