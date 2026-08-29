#!/usr/bin/env bash
# =============================================================================
# SDDM Catppuccin Mocha Theme - Interactive Test / Preview Runner
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME_DIR="${SCRIPT_DIR}/themes/catppuccin-mocha"

if [ ! -d "$THEME_DIR" ]; then
    echo "[ERROR] Theme directory not found at: $THEME_DIR"
    exit 1
fi

echo "======================================================"
echo "  Previewing Catppuccin Mocha SDDM Theme (Test Mode)  "
echo "======================================================"
echo "Theme Path: $THEME_DIR"
echo "Close the test window or press Ctrl+C to exit."
echo ""

if command -v sddm-greeter-qt6 >/dev/null 2>&1; then
    sddm-greeter-qt6 --test-mode --theme "$THEME_DIR"
elif command -v sddm-greeter >/dev/null 2>&1; then
    sddm-greeter --test-mode --theme "$THEME_DIR"
elif command -v qml6 >/dev/null 2>&1; then
    qml6 "${THEME_DIR}/Main.qml"
else
    echo "[ERROR] No SDDM greeter (sddm-greeter-qt6 or sddm-greeter) found."
    exit 1
fi
