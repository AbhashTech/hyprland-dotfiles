#!/usr/bin/env bash
# =============================================================================
# Quickshell Launch & Toggle Controller
# Supports toggling, starting, stopping, or restarting Quickshell
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
        --stop|-k)
            ACTION="stop"
            ;;
        --restart|-r)
            ACTION="restart"
            ;;
        *)
            PASSTHROUGH_ARGS+=("$arg")
            ;;
    esac
done

is_quickshell_running() {
    pgrep -x quickshell >/dev/null 2>&1
}

stop_quickshell() {
    pkill -x quickshell 2>/dev/null
    for i in {1..10}; do
        if ! is_quickshell_running; then
            break
        fi
        sleep 0.05
    done
}

start_quickshell() {
    # If waybar is running, stop it to prevent overlapping top bars
    pkill -x waybar 2>/dev/null
    pkill -f launch_waybar.py 2>/dev/null
    rm -f "${HOME}/.cache/quickshell_plugin_trigger" 2>/dev/null

    # Auto-discover and generate QML loader manifests for custom plugins
    if [ -f "${HOME}/.config/quickshell/scripts/plugin_loader.sh" ]; then
        bash "${HOME}/.config/quickshell/scripts/plugin_loader.sh" >/dev/null 2>&1 || true
    fi

    QS_BIN="$(command -v quickshell || echo /usr/bin/quickshell)"
    "$QS_BIN" -d -p "$HOME/.config/quickshell" "${PASSTHROUGH_ARGS[@]}" >/dev/null 2>&1
}

case "$ACTION" in
    toggle)
        if is_quickshell_running; then
            stop_quickshell
        else
            start_quickshell
        fi
        ;;
    start)
        if ! is_quickshell_running; then
            start_quickshell
        fi
        ;;
    stop)
        stop_quickshell
        ;;
    restart)
        stop_quickshell
        sleep 0.1
        start_quickshell
        ;;
esac
