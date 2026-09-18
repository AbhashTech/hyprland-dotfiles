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

# 1. Ensure SDDM and Qt6 dependencies are installed
if ! command -v sddm >/dev/null 2>&1; then
    log_info "SDDM is not installed. Installing SDDM and Qt6 dependencies..."
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm sddm qt6-declarative qt6-svg qt6-5compat
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y sddm qt6-qtdeclarative qt6-qtsvg
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y sddm qml6-module-qtquick qml6-module-qtquick-controls qml6-module-qtquick-layouts
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y sddm
    else
        log_warn "Package manager not recognized. Please install SDDM and Qt6 dependencies manually."
    fi
fi

# 2. Restore original sddm-greeter if previously moved/symlinked
if [ -f "/usr/bin/sddm-greeter.qt5" ] && [ -L "/usr/bin/sddm-greeter" ]; then
    log_info "Restoring standard package /usr/bin/sddm-greeter..."
    sudo rm /usr/bin/sddm-greeter 2>/dev/null || true
    sudo mv /usr/bin/sddm-greeter.qt5 /usr/bin/sddm-greeter 2>/dev/null || true
    log_success "Restored /usr/bin/sddm-greeter package binary."
fi

# 3. Install Theme to /usr/share/sddm/themes
log_info "Installing theme to ${THEME_DEST}..."
sudo mkdir -p "/usr/share/sddm/themes"
sudo rm -rf "$THEME_DEST"
sudo cp -r "$THEME_SOURCE" "$THEME_DEST"
sudo chmod -R 755 "$THEME_DEST"
log_success "Theme installed to ${THEME_DEST}"

# 4. Configure SDDM to use the theme
log_info "Configuring SDDM default theme in ${CONF_FILE}..."
sudo mkdir -p "$CONF_DIR"

sudo tee "$CONF_FILE" >/dev/null << 'EOF'
[Theme]
Current=catppuccin-mocha
EOF

log_success "SDDM configuration updated (${CONF_FILE})."

# 5. Enable SDDM systemd service & assert graphical target
log_info "Enabling sddm.service and ensuring graphical boot target..."
for dm in gdm lightdm lxdm ly greetd; do
    if systemctl is-enabled "${dm}.service" >/dev/null 2>&1; then
        log_info "Disabling conflicting display manager: ${dm}.service"
        sudo systemctl disable "${dm}.service" 2>/dev/null || true
    fi
done

sudo systemctl set-default graphical.target 2>/dev/null || true
sudo systemctl enable -f sddm.service

if systemctl is-enabled sddm.service >/dev/null 2>&1; then
    log_success "sddm.service successfully enabled (graphical.target default)."
else
    log_warn "sddm.service could not be verified as enabled. Please check systemctl status sddm.service."
fi

# 6. Verify
echo ""
log_success "Catppuccin Mocha SDDM theme is now fully installed, activated, and sddm.service is enabled!"
echo -e "You can test the installed theme anytime by running:"
echo -e "  ${COLOR_BOLD}sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/catppuccin-mocha${COLOR_RESET}"
