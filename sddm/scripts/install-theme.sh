#!/usr/bin/env bash
# =============================================================================
# SDDM Catppuccin Mocha Theme - System Installer & Activator
# =============================================================================

set -e

COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"
COLOR_GREEN="\033[1;32m"
COLOR_BLUE="\033[1;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME_SOURCE="${SCRIPT_DIR}/../themes/catppuccin-mocha"
THEME_DEST="/usr/share/sddm/themes/catppuccin-mocha"
CONF_DIR="/etc/sddm.conf.d"
CONF_FILE="${CONF_DIR}/theme.conf"

log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

echo -e "${COLOR_BOLD}======================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}   Catppuccin Mocha SDDM Theme Installer             ${COLOR_RESET}"
echo -e "${COLOR_BOLD}======================================================${COLOR_RESET}"

if [ ! -d "$THEME_SOURCE" ]; then
    log_error "Theme source directory not found at $THEME_SOURCE"
    exit 1
fi

# 1. Ensure Qt6 Greeter is used by SDDM daemon
log_info "Configuring SDDM to use Qt6 greeter..."
if [ -f "/usr/bin/sddm-greeter-qt6" ]; then
    if [ ! -L "/usr/bin/sddm-greeter" ] || [ "$(readlink /usr/bin/sddm-greeter 2>/dev/null)" != "/usr/bin/sddm-greeter-qt6" ]; then
        sudo mv /usr/bin/sddm-greeter /usr/bin/sddm-greeter.qt5 2>/dev/null || true
        sudo ln -sf /usr/bin/sddm-greeter-qt6 /usr/bin/sddm-greeter
        log_success "Linked /usr/bin/sddm-greeter -> /usr/bin/sddm-greeter-qt6"
    fi
fi

# 2. Install Theme to /usr/share/sddm/themes
log_info "Installing theme to ${THEME_DEST}..."
sudo mkdir -p "/usr/share/sddm/themes"
sudo rm -rf "$THEME_DEST"
sudo cp -r "$THEME_SOURCE" "$THEME_DEST"
sudo chmod -R 755 "$THEME_DEST"
log_success "Theme installed to ${THEME_DEST}"

# 3. Configure SDDM to use the theme
log_info "Configuring SDDM default theme in ${CONF_FILE}..."
sudo mkdir -p "$CONF_DIR"

sudo tee "$CONF_FILE" >/dev/null << 'EOF'
[Theme]
Current=catppuccin-mocha
EOF

log_success "SDDM configuration updated (${CONF_FILE})."

# 3. Verify
echo ""
log_success "Catppuccin Mocha SDDM theme is now fully installed and activated!"
echo -e "You can test the installed theme anytime by running:"
echo -e "  ${COLOR_BOLD}sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/catppuccin-mocha${COLOR_RESET}"
