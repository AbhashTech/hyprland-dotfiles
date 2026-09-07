#!/usr/bin/env bash
# =============================================================================
# Quickshell Plugin Toggle Helper
# Writes plugin name to ~/.cache/quickshell_plugin_trigger for instant IPC toggle
# =============================================================================

PLUGIN="${1:-menu}"
CACHE_TRIGGER="${HOME}/.cache/quickshell_plugin_trigger"

mkdir -p "${HOME}/.cache"

# If quickshell is not running, launch it first
if ! pgrep -x quickshell >/dev/null 2>&1; then
    bash "${HOME}/.config/quickshell/scripts/launch_quickshell.sh" --start
    sleep 0.2
fi

# Atomic write with timestamp to ensure FileView triggers onLoaded
echo "${PLUGIN} $(date +%s%N)" > "${CACHE_TRIGGER}.tmp"
mv "${CACHE_TRIGGER}.tmp" "${CACHE_TRIGGER}"
