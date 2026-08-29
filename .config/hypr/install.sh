#!/usr/bin/env bash
# =============================================================================
# Hyprland Lua Configuration - Automated Installer & Setup Script
# =============================================================================

set -e

COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"
COLOR_GREEN="\033[1;32m"
COLOR_BLUE="\033[1;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"

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

echo -e "${COLOR_BOLD}====================================================${COLOR_RESET}"
echo -e "${COLOR_BOLD}   Hyprland Modular Lua Config - Setup & Installer  ${COLOR_RESET}"
echo -e "${COLOR_BOLD}====================================================${COLOR_RESET}"

CONFIG_DIR="${HOME}/.config/hypr"
SCRIPTS_DIR="${CONFIG_DIR}/scripts"

# 1. Check Distro & Package Manager
if command -v pacman >/dev/null 2>&1; then
    log_info "Arch Linux / Pacman detected."
    
    PACKAGES=(
        hyprland
        hypridle
        hyprlock
        hyprpicker
        hyprsunset
        wlsunset
        xdg-desktop-portal-hyprland
        xdg-desktop-portal-gtk
        waybar
        mako
        hyprpaper
        fuzzel
        wofi
        kitty
        yazi
        zoxide
        fzf
        wtype
        dolphin
        firefox
        btop
        pipewire
        pipewire-pulse
        wireplumber
        libpulse
        playerctl
        brightnessctl
        ddcutil
        wl-clipboard
        cliphist
        grim
        slurp
        tesseract
        tesseract-data-eng
        wf-recorder
        libnotify
        python
        python-gobject
        gtk3
        gtk-layer-shell
        ttf-jetbrains-mono-nerd
        papirus-icon-theme
    )

    log_info "Installing official repository packages via pacman..."
    sudo pacman -S --needed --noconfirm "${PACKAGES[@]}" || {
        log_warn "Some pacman packages failed to install automatically. Please check your network or package list."
    }

    # AUR helper detection for extras (swappy, satty)
    AUR_HELPER=""
    if command -v paru >/dev/null 2>&1; then
        AUR_HELPER="paru"
    elif command -v yay >/dev/null 2>&1; then
        AUR_HELPER="yay"
    fi

    if [ -n "$AUR_HELPER" ]; then
        log_info "Installing optional AUR utilities (swappy, satty) using $AUR_HELPER..."
        $AUR_HELPER -S --needed --noconfirm swappy satty || log_warn "Optional AUR packages skipped."
    else
        log_warn "No AUR helper (paru/yay) found. You can manually install swappy or satty for screenshot annotation."
    fi

else
    log_warn "Non-Arch Linux distribution detected."
    log_info "Please ensure the required packages (Hyprland, Waybar, Mako, Fuzzel, Cliphist, Grim, Slurp, Pipewire, Brightnessctl) are installed with your package manager."
fi

# 2. Make scripts executable
log_info "Making helper scripts executable..."
if [ -d "$SCRIPTS_DIR" ]; then
    chmod +x "$SCRIPTS_DIR"/*.sh "$SCRIPTS_DIR"/*.py 2>/dev/null || true
    log_success "Script permissions configured."
fi

# 3. Create required user directories and caches
log_info "Ensuring cache and user directories exist..."
mkdir -p "${HOME}/.cache/cliphist_thumbs"
mkdir -p "${HOME}/Pictures/Screenshots"
mkdir -p "${HOME}/Videos/Recordings"
log_success "Directories created: Screenshots, Recordings, and Cliphist thumbnail cache."

# 4. Kernel i2c-dev module for DDC external monitor brightness
if ! lsmod | grep -q "i2c_dev"; then
    log_info "Loading i2c-dev kernel module for external monitor DDC brightness control..."
    sudo modprobe i2c-dev 2>/dev/null || log_warn "Could not load i2c-dev automatically."
fi

# 5. Initialize Theme & Color Variables
log_info "Initializing desktop theme and dynamic color variables..."
if [ -f "${SCRIPTS_DIR}/theme_switcher.py" ]; then
    python3 "${SCRIPTS_DIR}/theme_switcher.py" --set catppuccin-mocha --silent 2>/dev/null || true
    log_success "Catppuccin Mocha theme variables initialized."
fi

# 6. Finished
echo ""
log_success "Installation and environment setup completed!"
echo -e "To launch or apply the configuration:"
echo -e "  • Start Hyprland:    ${COLOR_BOLD}Hyprland${COLOR_RESET}"
echo -e "  • Theme Switcher:    ${COLOR_BOLD}SUPER + T${COLOR_RESET} (or ${COLOR_BOLD}~/.config/hypr/scripts/theme_switcher.py --menu${COLOR_RESET})"
echo -e "  • If already in Hyprland, reload with: ${COLOR_BOLD}hyprctl reload${COLOR_RESET}"
echo -e "  • Toggle Waybar with: ${COLOR_BOLD}SUPER + SHIFT + W${COLOR_RESET} (or ${COLOR_BOLD}~/.config/waybar/scripts/launch_waybar.sh${COLOR_RESET})"

