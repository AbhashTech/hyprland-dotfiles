#!/usr/bin/env bash
# =============================================================================
# Unified Hyprland Desktop Dotfiles - Automated Installer & Symlinker
# (Hyprland, Waybar, Fuzzel, Mako, Wofi, Btop, Audio, Clipboard, OSDs)
# =============================================================================

set -e

COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"
COLOR_GREEN="\033[1;32m"
COLOR_BLUE="\033[1;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_TARGET="${HOME}/.config"

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
echo -e "${COLOR_BOLD}   Unified Dotfiles Setup: Hyprland & Waybar Desktop  ${COLOR_RESET}"
echo -e "${COLOR_BOLD}======================================================${COLOR_RESET}"

# 1. Install System Dependencies (Arch Linux / Pacman)
if command -v pacman >/dev/null 2>&1; then
    log_info "Arch Linux detected. Installing official repository packages..."

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
        sddm
        qt6-declarative
        qt6-svg
        qt6-5compat
    )

    sudo pacman -S --needed --noconfirm "${PACKAGES[@]}" || {
        log_warn "Some pacman packages failed to install automatically. Please check your package manager."
    }

    # AUR helper detection for extras (swappy, satty)
    AUR_HELPER=""
    if command -v paru >/dev/null 2>&1; then
        AUR_HELPER="paru"
    elif command -v yay >/dev/null 2>&1; then
        AUR_HELPER="yay"
    fi

    if [ -n "$AUR_HELPER" ]; then
        log_info "Installing optional AUR packages (swappy, satty) with $AUR_HELPER..."
        $AUR_HELPER -S --needed --noconfirm swappy satty || log_warn "Optional AUR packages skipped."
    else
        log_warn "No AUR helper (paru/yay) found. Install swappy or satty manually if you want screenshot annotation."
    fi

else
    log_warn "Non-Arch Linux distribution detected."
    log_info "Ensure Hyprland, Waybar, Mako, Fuzzel, Cliphist, Grim, Slurp, Pipewire, SDDM, and Python dependencies are installed."
fi

# 2. Symlink Configs to ~/.config
log_info "Deploying symlinks from ${DOTFILES_DIR}/.config to ${CONFIG_TARGET}..."
mkdir -p "${CONFIG_TARGET}"

DOT_CONFIG_DIRS=("hypr" "waybar" "fuzzel" "mako" "wofi" "btop")

for pkg in "${DOT_CONFIG_DIRS[@]}"; do
    SRC="${DOTFILES_DIR}/.config/${pkg}"
    DEST="${CONFIG_TARGET}/${pkg}"

    if [ -d "$SRC" ]; then
        if [ -L "$DEST" ]; then
            # Already a symlink
            rm "$DEST"
        elif [ -d "$DEST" ]; then
            # Directory exists, create a backup
            BACKUP="${DEST}.backup_$(date +%Y%m%d_%H%M%S)"
            log_warn "Existing directory at ${DEST} backed up to ${BACKUP}"
            mv "$DEST" "$BACKUP"
        fi
        ln -s "$SRC" "$DEST"
        log_success "Symlinked ~/.config/${pkg} -> ${SRC}"
    fi
done

# 3. Ensure Permissions
log_info "Configuring executable permissions for all custom scripts..."
find "${DOTFILES_DIR}/.config" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
find "${DOTFILES_DIR}/sddm" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
chmod +x "${DOTFILES_DIR}/install.sh" 2>/dev/null || true
log_success "Script permissions configured."

# 4. Create Cache & User Directories
log_info "Ensuring user media and cache directories exist..."
mkdir -p "${HOME}/.cache/cliphist_thumbs"
mkdir -p "${HOME}/Pictures/Screenshots"
mkdir -p "${HOME}/Videos/Recordings"
log_success "Media directories initialized."

# 5. Kernel DDC Permissions
if ! lsmod | grep -q "i2c_dev"; then
    log_info "Loading i2c-dev kernel module for external monitor DDC brightness control..."
    sudo modprobe i2c-dev 2>/dev/null || log_warn "Could not load i2c-dev automatically."
fi

# 6. SDDM Theme Installation & Activation
if [ -d "${DOTFILES_DIR}/sddm/themes/catppuccin-mocha" ]; then
    log_info "Deploying Catppuccin Mocha SDDM Theme..."
    if command -v sudo >/dev/null 2>&1; then
        sudo mkdir -p /usr/share/sddm/themes
        sudo rm -rf /usr/share/sddm/themes/catppuccin-mocha
        sudo cp -r "${DOTFILES_DIR}/sddm/themes/catppuccin-mocha" /usr/share/sddm/themes/catppuccin-mocha
        sudo mkdir -p /etc/sddm.conf.d
        sudo tee /etc/sddm.conf.d/theme.conf >/dev/null << 'EOF'
[Theme]
Current=catppuccin-mocha
EOF
        log_success "Catppuccin Mocha SDDM theme installed and activated (/etc/sddm.conf.d/theme.conf)."
    else
        log_warn "Sudo not available. Run 'sddm/scripts/install-theme.sh' with root privileges to activate the SDDM theme."
    fi
fi

echo ""
log_success "Unified dotfiles deployed successfully!"
echo -e "To apply or reload:"
echo -e "  • Hyprland Reload:   ${COLOR_BOLD}hyprctl reload${COLOR_RESET}"
echo -e "  • Waybar Restart:    ${COLOR_BOLD}SUPER + SHIFT + W${COLOR_RESET} (or ${COLOR_BOLD}killall waybar && waybar &${COLOR_RESET})"
echo -e "  • Notification Mako: ${COLOR_BOLD}makoctl reload${COLOR_RESET}"
echo -e "  • Test SDDM Theme:   ${COLOR_BOLD}~/.dotfiles/sddm/test-theme.sh${COLOR_RESET}"
