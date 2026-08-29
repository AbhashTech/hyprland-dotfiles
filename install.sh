#!/usr/bin/env bash
# =============================================================================
# Unified Hyprland Desktop Dotfiles - Automated Installer & Symlinker
# (Hyprland, Waybar, Fuzzel, Mako, Wofi, Btop, Kitty, Audio, Modern CLI Tools)
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

# 1. Install System Dependencies (Arch Linux / Pacman Only)
if command -v pacman >/dev/null 2>&1; then
    log_info "Arch Linux detected. Installing official repository packages..."

    PACKAGES=(
        # Core Compositor & Display
        hyprland
        hypridle
        hyprlock
        hyprpaper
        hyprpicker
        hyprsunset
        wlsunset
        hyprpolkitagent
        xdg-desktop-portal-hyprland
        xdg-desktop-portal-gtk

        # Bar, Launchers & Notifications
        waybar
        mako
        fuzzel
        wofi
        nwg-look

        # Terminal & Modern CLI Power Suite
        kitty
        yazi
        zoxide
        fzf
        wtype
        btop
        fastfetch
        eza
        bat
        ripgrep
        fd
        git-delta
        duf
        dust
        tealdeer
        trash-cli
        xh
        glow

        # TUIs & Terminal Multiplexing
        lazygit
        lazydocker
        zellij

        # Shell Prompt & Environment
        starship
        atuin
        direnv
        mise

        # Audio, Media & Brightness
        pipewire
        pipewire-pulse
        wireplumber
        libpulse
        playerctl
        brightnessctl
        ddcutil

        # Clipboard & Screen Capture (Official Repos)
        wl-clipboard
        cliphist
        grim
        slurp
        swappy
        wf-recorder
        tesseract
        tesseract-data-eng

        # Desktop Apps & Theming
        dolphin
        firefox
        libnotify
        python
        python-gobject
        gtk3
        gtk-layer-shell
        ttf-jetbrains-mono-nerd
        papirus-icon-theme

        # SDDM Display Manager
        sddm
        qt6-declarative
        qt6-svg
        qt6-5compat
    )

    sudo pacman -S --needed --noconfirm "${PACKAGES[@]}" || {
        log_warn "Some pacman packages failed to install automatically. Please check your package manager."
    }

else
    log_warn "Non-Arch Linux distribution detected."
    log_info "Ensure Hyprland, Waybar, Mako, Fuzzel, Cliphist, Grim, Slurp, Pipewire, SDDM, and Python dependencies are installed."
fi

# 2. Symlink Configs to ~/.config
log_info "Deploying symlinks from ${DOTFILES_DIR}/.config to ${CONFIG_TARGET}..."
mkdir -p "${CONFIG_TARGET}"

DOT_CONFIG_DIRS=(
    "hypr"
    "waybar"
    "fuzzel"
    "mako"
    "wofi"
    "btop"
    "kitty"
    "wlogout"
    "zellij"
    "fastfetch"
    "lazygit"
    "swappy"
    "shell"
)

for pkg in "${DOT_CONFIG_DIRS[@]}"; do
    SRC="${DOTFILES_DIR}/.config/${pkg}"
    DEST="${CONFIG_TARGET}/${pkg}"

    if [ -d "$SRC" ]; then
        if [ -L "$DEST" ]; then
            rm "$DEST"
        elif [ -d "$DEST" ]; then
            BACKUP="${DEST}.backup_$(date +%Y%m%d_%H%M%S)"
            log_warn "Existing directory at ${DEST} backed up to ${BACKUP}"
            mv "$DEST" "$BACKUP"
        fi
        ln -s "$SRC" "$DEST"
        log_success "Symlinked ~/.config/${pkg} -> ${SRC}"
    fi
done

# Symlink standalone config files
if [ -f "${DOTFILES_DIR}/.config/starship.toml" ]; then
    STARSHIP_DEST="${CONFIG_TARGET}/starship.toml"
    if [ -L "$STARSHIP_DEST" ]; then
        rm "$STARSHIP_DEST"
    elif [ -f "$STARSHIP_DEST" ]; then
        mv "$STARSHIP_DEST" "${STARSHIP_DEST}.backup_$(date +%Y%m%d_%H%M%S)"
    fi
    ln -s "${DOTFILES_DIR}/.config/starship.toml" "$STARSHIP_DEST"
    log_success "Symlinked ~/.config/starship.toml -> ${DOTFILES_DIR}/.config/starship.toml"
fi

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

# 6. Initialize Tealdeer cache if available
if command -v tldr >/dev/null 2>&1; then
    log_info "Updating tealdeer (tldr) cheatsheet cache..."
    tldr --update >/dev/null 2>&1 || true
fi

# 7. SDDM Theme Installation & Activation
if [ -d "${DOTFILES_DIR}/sddm/themes/catppuccin-mocha" ]; then
    log_info "Deploying Catppuccin Mocha SDDM Theme..."
    if command -v sudo >/dev/null 2>&1; then
        if [ -f "/usr/bin/sddm-greeter-qt6" ]; then
            if [ ! -L "/usr/bin/sddm-greeter" ] || [ "$(readlink /usr/bin/sddm-greeter 2>/dev/null)" != "/usr/bin/sddm-greeter-qt6" ]; then
                sudo mv /usr/bin/sddm-greeter /usr/bin/sddm-greeter.qt5 2>/dev/null || true
                sudo ln -sf /usr/bin/sddm-greeter-qt6 /usr/bin/sddm-greeter
            fi
        fi
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
echo -e "To load the productivity shell suite in your terminal, add this to your ~/.bashrc or ~/.zshrc:"
echo -e "  ${COLOR_BOLD}source ~/.config/shell/env.sh${COLOR_RESET}"
echo -e "  ${COLOR_BOLD}source ~/.config/shell/aliases.sh${COLOR_RESET}"
echo ""
echo -e "To apply or reload desktop components:"
echo -e "  • Hyprland Reload:   ${COLOR_BOLD}hyprctl reload${COLOR_RESET}"
echo -e "  • Waybar Restart:    ${COLOR_BOLD}SUPER + SHIFT + W${COLOR_RESET} (or ${COLOR_BOLD}killall waybar && waybar &${COLOR_RESET})"
echo -e "  • Power Menu:        ${COLOR_BOLD}SUPER + ESCAPE${COLOR_RESET} / ${COLOR_BOLD}SUPER + M${COLOR_RESET} (wlogout)"
echo -e "  • Git TUI Overlay:   ${COLOR_BOLD}SUPER + G${COLOR_RESET} (lazygit)"
echo -e "  • Notification Mako: ${COLOR_BOLD}makoctl reload${COLOR_RESET}"
echo -e "  • Test SDDM Theme:   ${COLOR_BOLD}~/.dotfiles/sddm/test-theme.sh${COLOR_RESET}"
