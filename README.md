# 🌌 Unified Hyprland & Wayland Dotfiles

A unified, modular, and fully version-controlled dotfiles suite for **Hyprland** on Linux. Includes **Waybar**, **Fuzzel**, **Mako**, **Wofi**, **Btop**, **Kitty**, **Wlogout**, **Zellij**, **Lazygit**, **Starship**, custom OSD overlays, Catppuccin-themed clipboard management, media/audio switchers, and a comprehensive modern CLI productivity suite (100% official Pacman packages).

---

## 📁 Repository Structure

```
~/.dotfiles/
├── install.sh                   # All-in-one dependency installer & symlink deployer (Pacman native)
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
    ├── kitty/                   # Kitty Terminal Emulator
    │   └── kitty.conf           # Catppuccin Mocha theme, font, padding & shortcuts
    ├── starship.toml            # Starship Cross-Shell Prompt (Catppuccin Mocha)
    ├── wlogout/                 # Wayland Logout & Power Overlay
    │   ├── layout               # Button layouts & systemctl actions
    │   └── style.css            # Catppuccin Mocha stylesheet & icons
    ├── zellij/                  # Terminal Multiplexer
    │   └── config.kdl           # Themes, compact status bar & ergonomics
    ├── lazygit/                 # Git Terminal UI
    │   └── config.yml           # Theme & delta side-by-side pager integration
    ├── fastfetch/               # System Information Display
    │   └── config.jsonc         # Minimal, clean hardware/OS summary
    ├── swappy/                  # Screenshot Annotator
    │   └── config               # Paint tools, fonts & instant save rules
    ├── shell/                   # Modular Shell Setup
    │   ├── aliases.sh           # Modern aliases (ls->eza, cat->bat, grep->rg, rm->trash-put)
    │   └── env.sh               # Prompt hooks (Starship, Atuin, Zoxide, Direnv, Mise)
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

## 📦 What All Needs to be Installed (100% Official Pacman Repos)

| Component | Packages / Tools | Description |
| :--- | :--- | :--- |
| **Display Manager (SDDM)**| `sddm`, `qt6-declarative`, `qt6-svg`, `qt6-5compat` | Qt6 display manager & Catppuccin Mocha glassmorphic greeter |
| **Compositor & Portals** | `hyprland`, `xdg-desktop-portal-hyprland`, `xdg-desktop-portal-gtk`, `hyprpolkitagent` | Wayland compositor, screen sharing portals, and Polkit authentication agent |
| **Session, Lock & Power** | `hyprlock`, `hypridle`, `wlogout` | Catppuccin Mocha lockscreen, idle daemon, and graphical power menu |
| **Status Bar** | `waybar` | Status bar with system trays, volume, network, and workspaces |
| **Notifications** | `mako`, `libnotify` | Notification daemon & `notify-send` for OSDs (with click-to-focus) |
| **Wallpaper** | `hyprpaper` | Fast Wayland wallpaper daemon |
| **App Launchers & Theming** | `fuzzel`, `wofi`, `nwg-look` | Fast Wayland launcher, GTK dmenu, and GTK3/4 theme switcher |
| **Terminal & Apps** | `kitty`, `yazi`, `dolphin`, `firefox`, `btop` | Terminal, CLI file manager, KDE file manager, browser, and monitor |
| **Modern CLI Power Suite** | `eza`, `bat`, `ripgrep`, `fd`, `git-delta`, `duf`, `dust`, `tealdeer`, `trash-cli`, `xh`, `glow` | Rust/Go daily replacements for ls, cat, grep, find, diff, du, df, man, rm, curl |
| **TUIs & Multiplexing** | `lazygit`, `lazydocker`, `zellij` | Interactive terminal UIs for Git, Docker, and terminal multiplexing |
| **Shell & Environment** | `starship`, `atuin`, `direnv`, `mise`, `zoxide`, `fzf`, `wtype` | Fast prompt, SQLite history search, per-directory env/venv, tool version manager |
| **Audio Subsystem** | `pipewire`, `pipewire-pulse`, `wireplumber`, `libpulse`, `playerctl` | PipeWire audio, `wpctl`/`pactl` controls, and media playback keys |
| **Brightness & Night Light**| `brightnessctl`, `ddcutil`, `hyprsunset` / `wlsunset` | Backlight, external DDC brightness, and warm blue-light filter |
| **Clipboard** | `wl-clipboard`, `cliphist` | Wayland clipboard manager with binary image and thumbnail support |
| **Screen Capture & OCR** | `grim`, `slurp`, `swappy`, `wl-screenrec`, `wf-recorder`, `hyprpicker`, `tesseract`, `tesseract-data-eng` | Screenshots, annotation, GPU-accelerated video recording, color picker, OCR |
| **Python Runtime & UI** | `python`, `python-gobject`, `gtk3`, `gtk-layer-shell` | Python 3, PyGObject, and Wayland layer-shell for launchers |
| **Fonts & Icons** | `ttf-jetbrains-mono-nerd`, `papirus-icon-theme` | Nerd font glyphs and system icon theme |

---

## 🛠️ How to Install

### Automated Setup (Recommended)

```bash
chmod +x ~/.dotfiles/install.sh
~/.dotfiles/install.sh
```

The installer will:
- Install all official Arch Linux packages via `pacman`.
- Symlink all `~/.dotfiles/.config/*` into `~/.config/` (safely backing up existing folders).
- Set executable permissions on all Python and Shell scripts.
- Initialize tealdeer cheatsheets, directories (`~/Pictures/Screenshots`, `~/Videos/Recordings`), and `i2c-dev`.
- Deploy the SDDM theme.

### Shell Integration

Add the following lines to your `~/.bashrc` or `~/.zshrc`:
```bash
source ~/.config/shell/env.sh
source ~/.config/shell/aliases.sh
```

---

## ⌨️ Keybindings Reference

### 🖥️ Applications & Navigation
| Shortcut | Action |
| :--- | :--- |
| `SUPER + Q` | Open Kitty Terminal |
| `SUPER + grave (~)` | Toggle Dropdown Scratchpad Terminal |
| `SUPER + G` | Open Floating **Lazygit** TUI |
| `SUPER + D` | Open Floating **Lazydocker** TUI |
| `SUPER + SHIFT + Z` | Open Floating **Zellij** Multiplexer Session |
| `SUPER + E` | Open Dolphin File Manager |
| `SUPER + SHIFT + E` | Open Yazi Terminal File Manager |
| `SUPER + B` | Open Firefox Web Browser |
| `SUPER + R` | Open Fuzzel Launcher (with outside-click dismissal) |
| `SUPER + ESCAPE` / `SUPER + M` | Open **Wlogout** Power & Session Overlay |
| `SUPER + L` / `ALT + L` | Lock Screen immediately (`hyprlock`) |
| `SUPER + C` | Close Active Window |
| `SUPER + V` | Toggle Window Floating Mode |
| `SUPER + P` | Toggle Pseudo Tiling |
| `SUPER + J` | Toggle Split (Dwindle layout) |
| `SUPER + SHIFT + W` | Restart / Reload Waybar |
| `SUPER + [1-9, 0]` | Switch to Workspace 1–10 |
| `SUPER + SHIFT + [1-9, 0]` | Move Active Window to Workspace 1–10 |
| `SUPER + S` | Toggle Special Scratchpad Workspace |
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

### 📸 Screenshots & Screen Recording (`screen_capture.py`)
| Shortcut | Action |
| :--- | :--- |
| `Print` | Capture Area / Selection to clipboard & file |
| `SHIFT + Print` | Capture Full Screen |
| `ALT + Print` | Capture Active Window |
| `CTRL + Print` | Capture Area & Open in **Swappy** Annotation Tool |
| `SUPER + Print` | Open Interactive Capture Menu |
| `SUPER + ALT + R` | Toggle Area Video Screen Recording |
| `SUPER + SHIFT + R` | Stop Active Video Screen Recording |

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
