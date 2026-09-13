#!/usr/bin/env bash
# =============================================================================
# Unified Hyprland Desktop Dotfiles - Automated Installer & Symlinker
# (Hyprland, Quickshell, Mako, Btop, Foot, Audio, Modern CLI Power Tools)
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
echo -e "${COLOR_BOLD} Unified Dotfiles Setup: Hyprland & Quickshell Desktop${COLOR_RESET}"
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
        quickshell
        mako
        nwg-look

        # Terminal & Modern CLI Power Suite
        foot
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
        zsh
        zsh-autosuggestions
        zsh-syntax-highlighting
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
        imagemagick

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
        python-dbus
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
    log_info "Ensure Hyprland, Quickshell, Mako, Cliphist, Grim, Slurp, Pipewire, SDDM, and Python dependencies are installed."
fi

# 2. Symlink Configs to ~/.config
log_info "Deploying symlinks from ${DOTFILES_DIR}/.config to ${CONFIG_TARGET}..."
mkdir -p "${CONFIG_TARGET}"

DOT_CONFIG_DIRS=(
    "hypr"
    "quickshell"
    "wireplumber"
    "mako"
    "btop"
    "foot"
    "nvim"
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
    "systemd"
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
for cfg_file in "starship.toml" "mimeapps.list" "dolphinrc" "kdeglobals" "kwinrc"; do
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

# Symlink .zshrc
if [ -f "${DOTFILES_DIR}/.zshrc" ]; then
    ZSH_DEST="${HOME}/.zshrc"
    if [ -L "$ZSH_DEST" ]; then
        rm "$ZSH_DEST"
    elif [ -f "$ZSH_DEST" ]; then
        mv "$ZSH_DEST" "${ZSH_DEST}.backup_$(date +%Y%m%d_%H%M%S)"
    fi
    ln -s "${DOTFILES_DIR}/.zshrc" "$ZSH_DEST"
    log_success "Symlinked ~/.zshrc -> ${DOTFILES_DIR}/.zshrc"
fi

# 3. Ensure Permissions
log_info "Configuring executable permissions for all custom scripts..."
find "${DOTFILES_DIR}/.config" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
find "${DOTFILES_DIR}/sddm" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
chmod +x "${DOTFILES_DIR}/install.sh" 2>/dev/null || true
log_success "Script permissions configured."

# 4. Create Cache & User Directories
log_info "Ensuring user media, cache, tessdata, and custom plugin directories exist..."
mkdir -p "${HOME}/.cache/cliphist_thumbs"
mkdir -p "${HOME}/.cache/qs_filepicker/thumbnails"
mkdir -p "${HOME}/.cache/quickshell/window_previews"
mkdir -p "${HOME}/Pictures/Screenshots"
mkdir -p "${HOME}/Videos/Recordings"
mkdir -p "${HOME}/.local/share/tessdata"
mkdir -p "${HOME}/.local/share/xdg-desktop-portal/portals"
mkdir -p "${HOME}/.local/share/dbus-1/services"
mkdir -p "${DOTFILES_DIR}/.config/quickshell/custom_plugins"

# Register Quickshell FileChooser portal backend and D-Bus auto-activation service
if [ -f "${DOTFILES_DIR}/.config/quickshell/plugins/filepicker/quickshell.portal" ]; then
    ln -sf "${DOTFILES_DIR}/.config/quickshell/plugins/filepicker/quickshell.portal" "${HOME}/.local/share/xdg-desktop-portal/portals/quickshell.portal"
fi
# Note: D-Bus activation files do NOT support systemd specifiers like %h - use literal $HOME
cat > "${HOME}/.local/share/dbus-1/services/org.freedesktop.impl.portal.desktop.quickshell.service" << EOF
[D-BUS Service]
Name=org.freedesktop.impl.portal.desktop.quickshell
Exec=/usr/bin/python3 ${HOME}/.config/quickshell/plugins/filepicker/portal_service.py
SystemdService=quickshell-filepicker-portal.service
EOF

# Install and enable the systemd user service for the portal backend
# (The ~/.config/systemd dir may be a real directory, not a symlink — so we copy explicitly)
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
mkdir -p "${SYSTEMD_USER_DIR}"
if [ -f "${DOTFILES_DIR}/.config/systemd/user/quickshell-filepicker-portal.service" ]; then
    cp "${DOTFILES_DIR}/.config/systemd/user/quickshell-filepicker-portal.service" \
       "${SYSTEMD_USER_DIR}/quickshell-filepicker-portal.service"
    systemctl --user daemon-reload
    systemctl --user enable --now quickshell-filepicker-portal.service 2>/dev/null || true
    log_success "Quickshell file picker portal backend service enabled and started."
fi

# Also symlink the portal config files explicitly (in case ~/.config/xdg-desktop-portal is a real dir)
XDP_CONF_DIR="${HOME}/.config/xdg-desktop-portal"
mkdir -p "${XDP_CONF_DIR}"
for conf in hyprland-portals.conf portals.conf; do
    if [ -f "${DOTFILES_DIR}/.config/xdg-desktop-portal/${conf}" ]; then
        ln -sf "${DOTFILES_DIR}/.config/xdg-desktop-portal/${conf}" "${XDP_CONF_DIR}/${conf}"
    fi
done

# Restart xdg-desktop-portal so it picks up the new FileChooser backend routing
systemctl --user restart xdg-desktop-portal 2>/dev/null || true

log_success "Media, cache, portal backend, and custom plugin directories initialized."

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
        # Restore original sddm-greeter if previously symlinked
        if [ -f "/usr/bin/sddm-greeter.qt5" ] && [ -L "/usr/bin/sddm-greeter" ]; then
            sudo rm /usr/bin/sddm-greeter 2>/dev/null || true
            sudo mv /usr/bin/sddm-greeter.qt5 /usr/bin/sddm-greeter 2>/dev/null || true
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

cat > "${HOME}/.local/share/applications/app-shortcut-creator.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=App Shortcut Creator
GenericName=Desktop Entry Creator
Comment=Create and manage application shortcuts for your App menu
Exec=python3 ${HOME}/.config/hypr/scripts/app_shortcut_creator.py
Icon=preferences-desktop-keyboard-shortcuts
Terminal=false
Categories=Utility;Settings;DesktopSettings;Development;
StartupWMClass=app-shortcut-creator
StartupNotify=true
EOF

cat > "${HOME}/.local/share/applications/theme-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Theme Manager
GenericName=Desktop Theme & Palette Switcher
Comment=Select and apply custom color palettes across Hyprland, Quickshell, and applications
Exec=python3 ${HOME}/.config/hypr/scripts/theme_switcher.py --gui
Icon=preferences-desktop-theme
Terminal=false
Categories=Utility;Settings;DesktopSettings;Appearance;
StartupWMClass=theme-manager
StartupNotify=true
Keywords=theme;palette;colorscheme;hyprland;catppuccin;dracula;nord;gruvbox;
EOF

cat > "${HOME}/.local/share/applications/ocr-language-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=OCR Language Manager
GenericName=Tesseract OCR Language Manager & Model Installer
Comment=Install language models, manage active OCR recognition languages, and test capture
Exec=python3 ${HOME}/.config/hypr/scripts/ocr_language_manager.py --gui
Icon=ocr-language-manager
Terminal=false
Categories=Utility;Settings;DesktopSettings;Office;
StartupWMClass=ocr-language-manager
StartupNotify=true
Keywords=ocr;tesseract;language;text;grab;scanner;translate;
EOF

cat > "${HOME}/.local/share/applications/hyprsunset-hypridle.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Night Light & Idle Manager
GenericName=Display Power & Night Light Control
Comment=Configure Hyprsunset color temperature, Hypridle timeouts, monitor turn-off, and Caffeine mode
Exec=python3 ${HOME}/.config/hypr/scripts/sunset_idle_manager.py --gui
Icon=preferences-desktop-display
Terminal=false
Categories=Utility;Settings;DesktopSettings;HardwareSettings;
StartupWMClass=sunset-idle-manager
StartupNotify=true
Keywords=hyprsunset;hypridle;nightlight;bluelight;display;screen;idle;dpms;sleep;caffeine;brightness;temperature;
Actions=ToggleNightLight;TurnOffMonitor;CaffeineMode;OpenMenu;

[Desktop Action ToggleNightLight]
Name=Toggle Night Light (On/Off)
Exec=python3 ${HOME}/.config/hypr/scripts/sunset_idle_manager.py --sunset-toggle

[Desktop Action TurnOffMonitor]
Name=Turn Off Displays Now (DPMS)
Exec=python3 ${HOME}/.config/hypr/scripts/sunset_idle_manager.py --dpms-off

[Desktop Action CaffeineMode]
Name=Toggle Caffeine Mode (Inhibit Sleep)
Exec=python3 ${HOME}/.config/hypr/scripts/sunset_idle_manager.py --caffeine-toggle

[Desktop Action OpenMenu]
Name=Open Interactive Idle & Power Menu
Exec=python3 ${HOME}/.config/hypr/scripts/sunset_idle_manager.py --menu
EOF

cat > "${HOME}/.local/share/applications/keyboard-layout-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Keyboard Layout Manager
GenericName=Input Layouts & Regional Variant Switcher
Comment=Switch and configure keyboard layouts, Indian regional variants, and XKB options
Exec=python3 ${HOME}/.config/hypr/scripts/keyboard_layout.py --gui
Icon=preferences-desktop-keyboard
Terminal=false
Categories=Utility;Settings;DesktopSettings;HardwareSettings;
StartupWMClass=keyboard_layout.py
StartupNotify=true
Keywords=keyboard;layout;variant;language;typing;input;xkb;hindi;tamil;telugu;dvorak;colemak;marathi;bengali;kannada;malayalam;gujarati;
EOF

cat > "${HOME}/.local/share/applications/plugin-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Plugin Manager
GenericName=Quickshell Plugin Manager
Comment=Manage, configure, enable/disable, install and scaffold Quickshell plugins
Exec=bash ${HOME}/.config/quickshell/scripts/toggle_plugin.sh plugin_manager
Icon=preferences-plugin
Terminal=false
Categories=Utility;Settings;DesktopSettings;System;
StartupWMClass=quickshell:plugin_manager
StartupNotify=true
Keywords=plugin;manager;quickshell;extensions;widgets;custom;store;
EOF

cat > "${HOME}/.local/share/applications/dotpersonal-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Personal Settings Manager
GenericName=Modular Dotfiles & Private Backup Manager
Comment=Manage untracked personal configurations, export backups, and sync private Git repository
Exec=python3 ${HOME}/.config/hypr/scripts/dotpersonal_gui.py
Icon=preferences-desktop-personal
Terminal=false
Categories=Utility;Settings;DesktopSettings;
StartupWMClass=dotpersonal_gui.py
StartupNotify=true
Keywords=dotfiles;personal;backup;git;export;import;private;modular;neovim;hyprland;shell;
EOF

cat > "${HOME}/.local/share/applications/keybind-manager.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Keybindings Manager
GenericName=Hyprland Shortcuts & Hotkeys Manager
Comment=Manage, override, disable, and create custom Hyprland keybindings
Exec=python3 ${HOME}/.config/hypr/scripts/keybind_manager.py
Icon=preferences-desktop-keyboard
Terminal=false
Categories=Utility;Settings;DesktopSettings;
StartupWMClass=keybind_manager.py
StartupNotify=true
Keywords=hyprland;keybind;keys;shortcuts;hotkeys;binds;keyboard;actions;override;custom;
EOF

chmod +x "${HOME}/.local/share/applications/"*.desktop 2>/dev/null || true

if [ -f "${DOTFILES_DIR}/.config/hypr/assets/ocr-language-manager.png" ]; then
    mkdir -p "${HOME}/.local/share/icons/hicolor/512x512/apps" "${HOME}/.local/share/icons"
    cp "${DOTFILES_DIR}/.config/hypr/assets/ocr-language-manager.png" "${HOME}/.local/share/icons/"
    for size in 16 24 32 48 64 128 256 512; do
        mkdir -p "${HOME}/.local/share/icons/hicolor/${size}x${size}/apps"
        if command -v magick >/dev/null 2>&1; then
            magick "${DOTFILES_DIR}/.config/hypr/assets/ocr-language-manager.png" -resize "${size}x${size}" "${HOME}/.local/share/icons/hicolor/${size}x${size}/apps/ocr-language-manager.png" 2>/dev/null || true
        else
            cp "${DOTFILES_DIR}/.config/hypr/assets/ocr-language-manager.png" "${HOME}/.local/share/icons/hicolor/${size}x${size}/apps/ocr-language-manager.png" 2>/dev/null || true
        fi
    done
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" >/dev/null 2>&1 || true
    fi
fi

# Hide technical / developer / internal background helper desktop entries
if [ -f "${DOTFILES_DIR}/sddm/scripts/hide-unwanted-apps.sh" ]; then
    bash "${DOTFILES_DIR}/sddm/scripts/hide-unwanted-apps.sh" >/dev/null 2>&1 || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true
fi
log_success "Application menus and icons deployed."

# 9. Initialize Theme & Color Variables
log_info "Initializing desktop theme and dynamic color variables..."
if [ -f "${DOTFILES_DIR}/.config/hypr/scripts/theme_switcher.py" ]; then
    python3 "${DOTFILES_DIR}/.config/hypr/scripts/theme_switcher.py" --set catppuccin-mocha --silent 2>/dev/null || true
    log_success "Catppuccin Mocha theme variables initialized."
fi
if [ -f "${DOTFILES_DIR}/scripts/dotfiles-push.sh" ]; then
    bash "${DOTFILES_DIR}/scripts/dotfiles-push.sh" --skip >/dev/null 2>&1 || true
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

    # Bluetooth battery level reporting (keep FastConnectable disabled for security)
    if [ -f /etc/bluetooth/main.conf ] && ! grep -q "Experimental = true" /etc/bluetooth/main.conf; then
        sudo sed -i '/^\[General\]/a Experimental = true' /etc/bluetooth/main.conf 2>/dev/null || true
    fi
    log_success "System enhancements configured."
fi

# 11. Personal Settings Verification
if [ -f "${DOTFILES_DIR}/scripts/dotfiles-personal.sh" ]; then
    echo ""
    log_info "Modular personal configuration environment initialized."
fi

echo ""
log_success "Unified dotfiles deployed successfully!"
echo -e "To load the productivity shell suite in your terminal, add this to your ~/.bashrc or ~/.zshrc:"
echo -e "  ${COLOR_BOLD}source ~/.config/shell/env.sh${COLOR_RESET}"
echo -e "  ${COLOR_BOLD}source ~/.config/shell/aliases.sh${COLOR_RESET}"
echo ""
echo -e "To apply or reload desktop components:"
echo -e "  • Shortcuts Cheat:   ${COLOR_BOLD}SUPER + /${COLOR_RESET} or ${COLOR_BOLD}SUPER + F1${COLOR_RESET} (interactive search)"
echo -e "  • Workspace Overview: ${COLOR_BOLD}SUPER + Tab${COLOR_RESET} (or hover on workspace bar)"
echo -e "  • Theme Menu:        ${COLOR_BOLD}SUPER + T${COLOR_RESET} (or ${COLOR_BOLD}~/.config/hypr/scripts/theme_switcher.py --menu${COLOR_RESET})"
echo -e "  • Theme Manager GUI: ${COLOR_BOLD}SUPER + ALT + T${COLOR_RESET} (or ${COLOR_BOLD}~/.config/hypr/scripts/theme_switcher.py --gui${COLOR_RESET})"
echo -e "  • Shortcut Creator:  ${COLOR_BOLD}SUPER + ALT + S${COLOR_RESET} (or ${COLOR_BOLD}~/.config/hypr/scripts/app_shortcut_creator.py${COLOR_RESET})"
echo -e "  • Hyprland Reload:   ${COLOR_BOLD}hyprctl reload${COLOR_RESET}"
echo -e "  • Status Bar Toggle: ${COLOR_BOLD}SUPER + SHIFT + W${COLOR_RESET} (or ${COLOR_BOLD}~/.config/quickshell/scripts/launch_quickshell.sh --toggle${COLOR_RESET})"
echo -e "  • Power Menu:        ${COLOR_BOLD}SUPER + ESCAPE${COLOR_RESET} / ${COLOR_BOLD}SUPER + M${COLOR_RESET} (Quickshell Power Menu)"
echo -e "  • Notification Center: ${COLOR_BOLD}SUPER + N${COLOR_RESET} (or top bar bell, history: 500 entries)"
echo -e "  • Git TUI Overlay:   ${COLOR_BOLD}SUPER + G${COLOR_RESET} (lazygit)"
echo -e "  • File Picker Modal: ${COLOR_BOLD}SUPER + SHIFT + F${COLOR_RESET} (or ${COLOR_BOLD}SUPER + ALT + F${COLOR_RESET} for Image Grid)"
echo -e "  • Notification Mako: ${COLOR_BOLD}makoctl reload${COLOR_RESET}"
echo -e "  • Test SDDM Theme:   ${COLOR_BOLD}~/.dotfiles/sddm/test-theme.sh${COLOR_RESET}"
echo -e "  • Push Dotfiles:     ${COLOR_BOLD}~/.dotfiles/scripts/dotfiles-push.sh${COLOR_RESET} (safely syncs & isolates local configs)"
echo -e "  • Personal Configs:  ${COLOR_BOLD}~/.dotfiles/scripts/dotfiles-personal.sh${COLOR_RESET} (export, import, version control)"

