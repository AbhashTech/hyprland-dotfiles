# 🌌 Unified Hyprland & Wayland Dotfiles

A unified, modular, and fully version-controlled dotfiles suite for **Hyprland** on Linux. Includes **Waybar**, **Fuzzel**, **Mako**, **Wofi**, **Btop**, custom OSD overlays, Catppuccin-themed clipboard management, media/audio switchers, and outside-click application launchers.

---

## 📁 Repository Structure

```
~/.dotfiles/
├── install.sh                   # All-in-one dependency installer & symlink deployer
├── .gitignore                   # Exclusions for temporary files & Python cache
├── README.md                    # Full documentation and shortcut cheat sheet
├── sddm/                        # SDDM Catppuccin Mocha Theme Suite
│   ├── test-theme.sh            # Live test-mode theme previewer (Qt6)
│   ├── scripts/
│   │   └── install-theme.sh     # System deployment & /etc/sddm.conf.d activator
│   └── themes/catppuccin-mocha/ # Full Qt6 QML Theme
│       ├── Main.qml             # Main greeter entrypoint & SDDM bindings
│       ├── metadata.desktop     # Theme metadata definition
│       ├── theme.conf           # User-customizable settings (colors, background, fonts)
│       ├── components/          # Modular QML components (GlassCard, Clock, Avatar, Password, Session, Power)
│       └── assets/              # Vector SVG icons & Catppuccin Mocha background wallpaper
└── .config/
    ├── hypr/                    # Hyprland Compositor Config & Scripts
    │   ├── hyprland.lua         # Main modular entrypoint
    │   ├── modules/             # Config modules (animations, keybinds, rules, monitors, etc.)
    │   └── scripts/             # Python & Shell utilities (brightness, audio, screen capture, scaling)
    ├── waybar/                  # Waybar Status Bar
    │   ├── config.jsonc         # Bar layout, modules, click actions & tooltips
    │   ├── style.css            # Styling, gradients, glassmorphism & padding
    │   └── scripts/             # Connectivity, notifications, bluetooth & power scripts
    ├── fuzzel/                  # Application Launcher & Dmenu
    │   └── fuzzel.ini           # Font, border radius, prompt & colors
    ├── mako/                    # Notification Daemon
    │   └── config               # Formatting, timeouts, icons, border & colors
    ├── wofi/                    # Alternative Application Launcher
    │   ├── config               # Dimensions, prompt & search mode
    │   └── style.css            # GTK stylesheet for Wofi
    └── btop/                    # System & Resource Monitor
        └── btop.conf            # Layout, update intervals, process sorting & graphs
```

---

## 📦 What All Needs to be Installed

| Component | Packages / Tools | Description |
| :--- | :--- | :--- |
| **Display Manager (SDDM)**| `sddm`, `qt6-declarative`, `qt6-svg`, `qt6-5compat` | Qt6 display manager & Catppuccin Mocha glassmorphic greeter |
| **Compositor & Portals** | `hyprland`, `xdg-desktop-portal-hyprland`, `xdg-desktop-portal-gtk` | Wayland compositor and portals for screen sharing / file dialogues |
| **Session & Lock Screen** | `hyprlock`, `hypridle` | Catppuccin Mocha lockscreen and smart idle management |
| **Status Bar** | `waybar` | Status bar with system trays, volume, network, and workspaces |
| **Notifications** | `mako`, `libnotify` | Notification daemon & `notify-send` for OSDs (with click-to-focus) |
| **Wallpaper** | `hyprpaper` | Fast Wayland wallpaper daemon |
| **App Launchers** | `fuzzel`, `wofi` | Fast Wayland app launcher and GTK dmenu launcher |
| **Terminal & Apps** | `kitty`, `yazi`, `dolphin`, `firefox`, `btop` | Terminal, CLI file manager, KDE file manager, browser, and monitor |
| **CLI Ergonomics** | `zoxide`, `fzf`, `wtype` | Smart cd, fuzzy searching, and Wayland keystroke simulation |
| **Audio Subsystem** | `pipewire`, `pipewire-pulse`, `wireplumber`, `libpulse`, `playerctl` | PipeWire audio, `wpctl`/`pactl` controls, and media playback keys |
| **Brightness & Night Light**| `brightnessctl`, `ddcutil`, `hyprsunset` / `wlsunset` | Backlight, external DDC brightness, and warm blue-light filter |
| **Clipboard** | `wl-clipboard`, `cliphist` | Wayland clipboard manager with binary image and thumbnail support |
| **Screen Capture & OCR** | `grim`, `slurp`, `tesseract`, `tesseract-data-eng`, `wf-recorder`, `hyprpicker`, `swappy`/`satty` (AUR) | Screenshots, OCR text extraction, video recorder, color picker, annotations |
| **Python Runtime & UI** | `python`, `python-gobject`, `gtk3`, `gtk-layer-shell` | Python 3, PyGObject, and Wayland layer-shell for launchers |
| **Fonts & Icons** | `ttf-jetbrains-mono-nerd`, `papirus-icon-theme` | Nerd font glyphs and system icon theme |

---

## 🛠️ How to Install

### Automated Setup (Recommended)

1. Clone the repository to `~/.dotfiles`:
   ```bash
   git clone <your-repo-url> ~/.dotfiles
   ```
2. Run the installer:
   ```bash
   chmod +x ~/.dotfiles/install.sh
   ~/.dotfiles/install.sh
   ```

The installer will:
- Install all required Arch/AUR packages.
- Symlink `~/.dotfiles/.config/*` into `~/.config/` (safely backing up any existing folders).
- Set executable permissions on all Python and Shell scripts.
- Create user media directories (`~/Pictures/Screenshots`, `~/Videos/Recordings`, `~/.cache/cliphist_thumbs`).
- Load the `i2c-dev` kernel module for external monitor DDC brightness.

---

### Manual Installation (Arch Linux)

```bash
# 1. Install Official Packages
sudo pacman -S --needed \
    hyprland hypridle hyprlock hyprpicker hyprsunset wlsunset \
    xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
    waybar mako hyprpaper fuzzel wofi kitty yazi zoxide fzf wtype \
    dolphin firefox btop \
    pipewire pipewire-pulse wireplumber libpulse playerctl \
    brightnessctl ddcutil wl-clipboard cliphist \
    grim slurp tesseract tesseract-data-eng wf-recorder \
    libnotify python python-gobject gtk3 gtk-layer-shell \
    ttf-jetbrains-mono-nerd papirus-icon-theme

# 2. Install Optional AUR Annotation Tools
paru -S --needed swappy satty # or: yay -S --needed swappy satty

# 3. Create Symlinks
mkdir -p ~/.config
for pkg in hypr waybar fuzzel mako wofi btop; do
    ln -s ~/.dotfiles/.config/$pkg ~/.config/$pkg
done

# 4. Make Scripts Executable
find ~/.dotfiles/.config -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} +
```

---

## 🚀 How to Apply & Reload Configs

- **Start Hyprland**: Run `Hyprland` from TTY or login manager.
- **Reload Hyprland**: Run `hyprctl reload`.
- **Lock Screen**: Press `SUPER + L` or `SUPER + ALT + L`.
- **Restart Waybar**: Press `SUPER + SHIFT + W` or run `killall waybar && waybar &`.
- **Reload Mako Notifications**: Run `makoctl reload`.
- **Test SDDM Theme**: Run `~/.dotfiles/sddm/test-theme.sh`.

---

## 🎨 Catppuccin Mocha SDDM Theme

A sleek, responsive, and glassmorphic login theme built with Qt6 QML that seamlessly integrates with the desktop aesthetic.

### ✨ Highlights
- **Frosted Glassmorphism**: Translucent floating card (`#181825`) with glowing Mauve (`#cba6f7`) focus borders and dark backdrop vignette.
- **Dynamic Clock & Greeting**: Real-time 24h/12h digital clock, full date formatting, and contextual greeting based on the time of day.
- **User Avatar & Profile Switcher**: Circular user avatar with glowing border ring and multi-user dropdown selector.
- **Password Input**: Modern pill input with reveal/hide password toggle (eye icon), auto-focus, Caps Lock active warning banner, and error shake animation with feedback on failed authentication.
- **Session Selector**: Wayland / X11 desktop session switcher (Hyprland, etc.) with styled popup list.
- **Power Menu & Confirmation**: Fast access to Power Off, Restart, Suspend, and Hibernate with safety confirmation modals to prevent accidental shutdowns.
- **Host & Status Indicator**: System hostname badge and battery monitor.

### 🧪 Live Preview / Test Mode
You can test and preview the SDDM theme in a standalone window without root permissions:

```bash
# Preview using the built-in runner script:
~/.dotfiles/sddm/test-theme.sh

# Or directly with sddm-greeter-qt6:
sddm-greeter-qt6 --test-mode --theme ~/.dotfiles/sddm/themes/catppuccin-mocha
```

### 📦 Manual SDDM Installation & Activation

```bash
# 1. Install dependencies
sudo pacman -S --needed sddm qt6-declarative qt6-svg qt6-5compat

# 2. Deploy theme to system directory
sudo mkdir -p /usr/share/sddm/themes
sudo cp -r ~/.dotfiles/sddm/themes/catppuccin-mocha /usr/share/sddm/themes/catppuccin-mocha

# 3. Activate theme in SDDM configuration
sudo mkdir -p /etc/sddm.conf.d
sudo tee /etc/sddm.conf.d/theme.conf << 'EOF'
[Theme]
Current=catppuccin-mocha
EOF

# 4. Enable and start SDDM (if not already enabled)
sudo systemctl enable sddm.service
```

### ⚙️ Theme Customization (`sddm/themes/catppuccin-mocha/theme.conf`)
Modify `~/.dotfiles/sddm/themes/catppuccin-mocha/theme.conf` to customize:
- `Background`: Path to custom wallpaper (SVG/PNG/JPG)
- `FontFamily`: Preferred system font (defaults to `JetBrainsMono Nerd Font`)
- `ClockFormat` / `DateFormat`: Time and date layout formats
- `AccentColor`: Primary accent hex color (`#cba6f7`)
- `ShowSessions` / `ShowPowerButtons` / `ShowGreeting`: Toggle UI component visibility

---

## ⌨️ Keybindings Reference

### 🖥️ Applications & Navigation
| Shortcut | Action |
| :--- | :--- |
| `SUPER + Q` | Open Kitty Terminal |
| `SUPER + E` | Open Dolphin File Manager |
| `SUPER + SHIFT + E` | Open Yazi Terminal File Manager |
| `SUPER + B` | Open Firefox Web Browser |
| `SUPER + R` | Open Fuzzel Launcher (with outside-click dismissal) |
| `SUPER + L` / `ALT + L` | Lock Screen immediately (`hyprlock`) |
| `SUPER + C` | Close Active Window |
| `SUPER + V` | Toggle Window Floating Mode |
| `SUPER + P` | Toggle Pseudo Tiling |
| `SUPER + J` | Toggle Split (Dwindle layout) |
| `SUPER + M` | Hyprland Exit / Power Menu |
| `SUPER + SHIFT + W` | Restart / Reload Waybar |
| `SUPER + [1-9, 0]` | Switch to Workspace 1–10 |
| `SUPER + SHIFT + [1-9, 0]` | Move Active Window to Workspace 1–10 |
| `SUPER + S` / `grave (~)` | Toggle Special Scratchpad Workspace |
| `SUPER + SHIFT + S` | Move Active Window to Special Scratchpad |

---

### ⚡ Productivity & Workflow Utilities
| Shortcut | Action |
| :--- | :--- |
| `SUPER + SHIFT + P` | **Hyprpicker**: Pick color from screen, copy hex code & notify |
| `SUPER + SHIFT + T` / `ALT + T` | **Screen OCR**: Grab and extract text from any screen region to clipboard |
| `SUPER + ALT + N` | **Night Light**: Toggle warm blue light filter (3800K / 6500K) |
| `SUPER + =` / `ALT + C` | **Quick Calculator**: Interactive math evaluator via Fuzzel |
| `SUPER + .` (period) | **Emoji Picker**: Searchable emoji menu with instant copy & auto-typing |

---

### 📋 Clipboard Manager (`clipboard_manager.py`)
| Shortcut | Action |
| :--- | :--- |
| `SUPER + SHIFT + V` | Open Clipboard History Browser (with images, code snippets, search) |
| `SUPER + ALT + V` | Open Clipboard History Browser |
| `SUPER + ALT + D` | Open Delete Single Item / Wipe History Menu |

---

### 📐 Window Resizing & Screen Scaling
| Shortcut | Action |
| :--- | :--- |
| `SUPER + CTRL + =` / `+` | Scale Window Up (+40px) with live dimension OSD |
| `SUPER + CTRL + -` | Scale Window Down (-40px) with live dimension OSD |
| `SUPER + CTRL + Arrow / HJKL` | Directional Window Resize (Left / Right / Up / Down) |
| `SUPER + CTRL + I` or `0` | Display active window dimensions & screen % overlay |
| `SUPER + SHIFT + R` / `SHIFT + D` | Open Interactive Screen Resolution & Display Scaling Menu |
| `SUPER + ALT + 1` to `5` | Switch display scaling (1.0x, 1.25x, 1.5x, 1.75x, 2.0x) |
| `SUPER + ALT + BackSpace` | Reset display scale to 1.0x (100%) |

---

### 🔊 Audio & Brightness Controls
| Shortcut | Action |
| :--- | :--- |
| `XF86AudioRaiseVolume` | Increase Speaker Volume (+5%) with OSD |
| `XF86AudioLowerVolume` | Decrease Speaker Volume (-5%) with OSD |
| `XF86AudioMute` | Toggle Speaker Mute |
| `XF86AudioMicMute` | Toggle Microphone Mute |
| `SHIFT + Audio Raise/Lower` | Adjust Microphone Volume |
| `SUPER + SHIFT + A` / `ALT + A` | Open Audio Output & Input Device Switcher Menu |
| `XF86MonBrightnessUp / Down` | Adjust Laptop Screen Brightness with OSD |
| `SUPER / SHIFT + Brightness` | Adjust External Monitor Brightness (DDC/CI) |
| `SUPER + SHIFT + B` / `ALT + B` | Open Interactive Brightness Presets Menu |

---

### 📸 Screenshots & Screen Recording (`screen_capture.py`)
| Shortcut | Action |
| :--- | :--- |
| `Print` | Capture Area / Selection to clipboard & file |
| `SHIFT + Print` | Capture Full Screen |
| `ALT + Print` | Capture Active Window |
| `CTRL + Print` | Capture Area & Open in Annotation Tool (Swappy/Satty) |
| `SUPER + Print` | Open Interactive Capture Menu |
| `SUPER + ALT + R` | Toggle Area Video Screen Recording |
| `SUPER + SHIFT + R` | Stop Active Video Screen Recording |
