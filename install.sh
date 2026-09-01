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
        neovim
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

        # Unified Theming, Portals & Runtimes (Qt + GTK)
        qt5-wayland
        qt6-wayland
        qt5ct
        qt6ct
        kvantum
        kvantum-qt5
        nwg-look
        dconf
        gsettings-desktop-schemas
        xsettingsd
        papirus-icon-theme
        adwaita-icon-theme
        xdg-desktop-portal
        xdg-desktop-portal-gtk
        xdg-desktop-portal-hyprland
        xdg-utils
        xdg-user-dirs

        # File Choosers, Thumbnails & Storage Integration
        gvfs
        gvfs-mtp
        gvfs-smb
        tumbler
        ffmpegthumbnailer
        poppler-glib
        webp-pixbuf-loader

        # Audio, Media Codecs & Bluetooth High-Res
        pipewire
        pipewire-pulse
        pipewire-alsa
        pipewire-jack
        wireplumber
        libpulse
        libcanberra
        vorbis-tools
        libldac
        libfreeaptx
        gst-plugins-good
        gst-plugins-bad
        gst-plugins-ugly
        gst-libav
        playerctl
        brightnessctl
        ddcutil
        libva-utils

        # System Optimization & Maintenance
        zram-generator
        pacman-contrib

        # Clipboard & Screen Capture (Official Repos)
        wl-clipboard
        cliphist
        grim
        slurp
        swappy
        wf-recorder
        tesseract
        tesseract-data-eng
        zbar

        # Authentication, Keyring & Security
        gnome-keyring
        libsecret
        polkit-gnome
        libfido2
        ccid
        pcsc-tools
        yubikey-manager

        # Fonts, Emojis & CJK Characters
        ttf-jetbrains-mono-nerd
        ttf-liberation
        noto-fonts
        noto-fonts-cjk
        noto-fonts-emoji

        # Desktop Apps, Viewers & Performance
        dolphin
        firefox
        loupe
        mpv
        zathura
        zathura-pdf-mupdf
        file-roller
        gamemode
        thermald
        libnotify
        python
        python-gobject
        gtk3
        gtk4
        gtk-layer-shell

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
    "nvim"
    "wlogout"
    "zellij"
    "fastfetch"
    "lazygit"
    "swappy"
    "shell"
    "theme"
    "gtk-3.0"
    "gtk-4.0"
    "xdg-desktop-portal"
    "xsettingsd"
    "environment.d"
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
for cfg_file in "starship.toml" "mimeapps.list"; do
    if [ -f "${DOTFILES_DIR}/.config/${cfg_file}" ]; then
        FILE_DEST="${CONFIG_TARGET}/${cfg_file}"
        if [ -L "$FILE_DEST" ]; then
            rm "$FILE_DEST"
        elif [ -f "$FILE_DEST" ]; then
            mv "$FILE_DEST" "${FILE_DEST}.backup_$(date +%Y%m%d_%H%M%S)"
        fi
        ln -s "${DOTFILES_DIR}/.config/${cfg_file}" "$FILE_DEST"
        log_success "Symlinked ~/.config/${cfg_file} -> ${DOTFILES_DIR}/.config/${cfg_file}"
    fi
done

# 3. Ensure Permissions
log_info "Configuring executable permissions for all custom scripts..."
find "${DOTFILES_DIR}/.config" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
find "${DOTFILES_DIR}/sddm" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
chmod +x "${DOTFILES_DIR}/install.sh" 2>/dev/null || true
log_success "Script permissions configured."

# 4. Create Cache & User Directories
log_info "Ensuring user media, cache, and tessdata directories exist..."
mkdir -p "${HOME}/.cache/cliphist_thumbs"
mkdir -p "${HOME}/Pictures/Screenshots"
mkdir -p "${HOME}/Videos/Recordings"
mkdir -p "${HOME}/.local/share/tessdata"
log_success "Media, cache, and OCR model directories initialized."

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

# 8. User Desktop Shortcuts (App Menu)
log_info "Deploying custom desktop application shortcuts..."
mkdir -p "${HOME}/.local/share/applications"
for desktop_file in app-shortcut-creator.desktop theme-manager.desktop ocr-language-manager.desktop; do
    if [ -f "${DOTFILES_DIR}/.config/hypr/scripts/${desktop_file}" ]; then
        cp "${DOTFILES_DIR}/.config/hypr/scripts/${desktop_file}" "${HOME}/.local/share/applications/"
        chmod +x "${HOME}/.local/share/applications/${desktop_file}"
    fi
done

# Hide technical / developer / internal background helper desktop entries
if [ -f "${DOTFILES_DIR}/sddm/scripts/hide-unwanted-apps.sh" ]; then
    bash "${DOTFILES_DIR}/sddm/scripts/hide-unwanted-apps.sh" >/dev/null 2>&1 || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true
fi
log_success "Application menus cleaned and customized."

# 9. Initialize Theme & Color Variables
log_info "Initializing desktop theme and dynamic color variables..."
if [ -f "${DOTFILES_DIR}/.config/hypr/scripts/theme_switcher.py" ]; then
    python3 "${DOTFILES_DIR}/.config/hypr/scripts/theme_switcher.py" --set catppuccin-mocha --silent 2>/dev/null || true
    log_success "Catppuccin Mocha theme variables initialized."
fi

# 10. System Enhancements: Fontconfig, ZRAM, Pacman Cache & Bluetooth
log_info "Configuring system enhancements (Subpixel Fonts, ZRAM, Pacman cache, Bluetooth)..."
if command -v sudo >/dev/null 2>&1; then
    # Subpixel LCD font rendering
    sudo mkdir -p /etc/fonts/conf.d
    sudo ln -sf /usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf /etc/fonts/conf.d/ 2>/dev/null || true
    sudo ln -sf /usr/share/fontconfig/conf.avail/11-lcdfilter-default.conf /etc/fonts/conf.d/ 2>/dev/null || true
    sudo ln -sf /usr/share/fontconfig/conf.avail/70-no-bitmaps.conf /etc/fonts/conf.d/ 2>/dev/null || true
    fc-cache -f 2>/dev/null || true

    # ZRAM compressed swap
    if [ ! -f /etc/systemd/zram-generator.conf ]; then
        sudo bash -c 'cat << "EOF" > /etc/systemd/zram-generator.conf
[zram0]
zram-size = ram / 2
compression-algorithm = zstd
EOF' 2>/dev/null || true
        sudo systemctl daemon-reload 2>/dev/null || true
        sudo systemctl start /dev/zram0 2>/dev/null || true
    fi

    # Automated Pacman cache cleaning timer
    sudo systemctl enable --now paccache.timer 2>/dev/null || true

    # Bluetooth battery level reporting & fast connectable
    if [ -f /etc/bluetooth/main.conf ] && ! grep -q "Experimental = true" /etc/bluetooth/main.conf; then
        sudo sed -i '/^\[General\]/a Experimental = true\nFastConnectable = true' /etc/bluetooth/main.conf 2>/dev/null || true
    fi
    log_success "System enhancements configured."
fi

echo ""
log_success "Unified dotfiles deployed successfully!"
echo -e "To load the productivity shell suite in your terminal, add this to your ~/.bashrc or ~/.zshrc:"
echo -e "  ${COLOR_BOLD}source ~/.config/shell/env.sh${COLOR_RESET}"
echo -e "  ${COLOR_BOLD}source ~/.config/shell/aliases.sh${COLOR_RESET}"
echo ""
echo -e "To apply or reload desktop components:"
echo -e "  • Shortcuts Cheat:   ${COLOR_BOLD}SUPER + /${COLOR_RESET} or ${COLOR_BOLD}SUPER + F1${COLOR_RESET} (interactive search)"
echo -e "  • Theme Menu:        ${COLOR_BOLD}SUPER + T${COLOR_RESET} (or ${COLOR_BOLD}~/.config/hypr/scripts/theme_switcher.py --menu${COLOR_RESET})"
echo -e "  • Theme Manager GUI: ${COLOR_BOLD}SUPER + ALT + T${COLOR_RESET} (or ${COLOR_BOLD}~/.config/hypr/scripts/theme_switcher.py --gui${COLOR_RESET})"
echo -e "  • Hyprland Reload:   ${COLOR_BOLD}hyprctl reload${COLOR_RESET}"
echo -e "  • Waybar Toggle:     ${COLOR_BOLD}SUPER + SHIFT + W${COLOR_RESET} (or ${COLOR_BOLD}~/.config/waybar/scripts/launch_waybar.sh${COLOR_RESET})"
echo -e "  • Power Menu:        ${COLOR_BOLD}SUPER + ESCAPE${COLOR_RESET} / ${COLOR_BOLD}SUPER + M${COLOR_RESET} (wlogout)"
echo -e "  • Git TUI Overlay:   ${COLOR_BOLD}SUPER + G${COLOR_RESET} (lazygit)"
echo -e "  • Notification Mako: ${COLOR_BOLD}makoctl reload${COLOR_RESET}"
echo -e "  • Test SDDM Theme:   ${COLOR_BOLD}~/.dotfiles/sddm/test-theme.sh${COLOR_RESET}"

