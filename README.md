# 🌌 Unified Hyprland & Wayland Dotfiles

A modular, unified, and fully version-controlled dotfiles suite for **Hyprland** on Arch Linux. Features **Waybar**, **Fuzzel**, **Mako**, **Wofi**, **Btop**, **Kitty**, **Starship**, **Lazygit**, **Zellij**, **Swappy**, custom OSD overlays, Catppuccin Mocha themed SDDM greeter, clipboard management, media/audio switchers, dynamic shortcut viewer, and a comprehensive modern CLI productivity suite (100% official Pacman packages).

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
    │   └── scripts/             # Python & Shell utilities (keybinds viewer, brightness, audio, capture, scaling)
    ├── waybar/                  # Waybar Status Bar
    │   ├── config.jsonc         # Bar layout, modules, click actions & tooltips
    │   ├── style.css            # Styling, gradients, glassmorphism & padding
    │   └── scripts/             # Connectivity, notifications, bluetooth & power scripts
    ├── kitty/                   # Kitty Terminal Emulator
    │   └── kitty.conf           # Catppuccin Mocha theme, font, padding & shortcuts
    ├── starship.toml            # Starship Cross-Shell Prompt (Catppuccin Mocha)
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
| **Session & Lock Screen** | `hyprlock`, `hypridle` | Catppuccin Mocha lockscreen and smart idle management |
| **Status Bar** | `waybar` | Status bar with system trays, volume, network, and workspaces |
| **Notifications** | `mako`, `libnotify` | Notification daemon & `notify-send` for OSDs (with click-to-focus) |
| **Wallpaper** | `hyprpaper` | Fast Wayland wallpaper daemon |
| **App Launchers & Theming** | `fuzzel`, `wofi`, `nwg-look` | Fast Wayland launcher, GTK dmenu, and GTK3/4 theme switcher |
| **Terminal & Apps** | `kitty`, `yazi`, `dolphin`, `firefox`, `btop` | Terminal, CLI file manager, KDE file manager, browser, and monitor |
| **Modern CLI Power Suite** | `eza`, `bat`, `ripgrep`, `fd`, `git-delta`, `duf`, `dust`, `tealdeer`, `trash-cli`, `xh`, `glow` | Daily replacements for ls, cat, grep, find, diff, du, df, man, rm, curl |
| **TUIs & Multiplexing** | `lazygit`, `lazydocker`, `zellij` | Interactive terminal UIs for Git, Docker, and terminal multiplexing |
| **Shell & Environment** | `starship`, `atuin`, `direnv`, `mise`, `zoxide`, `fzf`, `wtype` | Fast prompt, SQLite history search, per-directory env/venv, tool version manager |
| **Audio Subsystem** | `pipewire`, `pipewire-pulse`, `wireplumber`, `libpulse`, `playerctl` | PipeWire audio, `wpctl`/`pactl` controls, and media playback keys |
| **Brightness & Night Light**| `brightnessctl`, `ddcutil`, `hyprsunset` / `wlsunset` | Backlight, external DDC brightness, and warm blue-light filter |
| **Clipboard** | `wl-clipboard`, `cliphist` | Wayland clipboard manager with binary image and thumbnail support |
| **Screen Capture & OCR** | `grim`, `slurp`, `swappy`, `wf-recorder`, `hyprpicker`, `tesseract`, `tesseract-data-eng` | Screenshots, annotation, video recording, color picker, OCR |
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
- Deploy the Catppuccin Mocha SDDM theme.

### Shell Integration

Add the following lines to your `~/.bashrc` or `~/.zshrc`:
```bash
source ~/.config/shell/env.sh
source ~/.config/shell/aliases.sh
```

---

## ⚡ Dynamic Keybindings Viewer & Cheat Sheet

The repository includes an intelligent dynamic shortcut viewer ([`keybinds_viewer.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/keybinds_viewer.py)) that parses doc-comments directly from [`keybinds.lua`](file:///home/kunal/.dotfiles/.config/hypr/modules/keybinds.lua):

- **Desktop GUI**: Press **`SUPER + /`** or **`SUPER + F1`** to open an interactive, fuzzy-searchable Fuzzel overlay. Selecting any shortcut automatically copies the key combination to your clipboard.
- **Terminal CLI**: Run `python3 ~/.config/hypr/scripts/keybinds_viewer.py --cli` for categorized, ANSI-colored tables.
- **Export Formats**: Supports `--json` and `--markdown` for automated documentation generation.

---

## ⌨️ Complete Keyboard Shortcuts Reference

### 🖥️ Applications, Navigation & System Control
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + Q` | **Open Kitty Terminal** | Launch main terminal emulator |
| `SUPER + grave (~)` | **Dropdown Terminal** | Fast floating scratchpad terminal (`dropdown-terminal`) |
| `SUPER + G` | **Lazygit Overlay** | Open floating full-featured Git TUI |
| `SUPER + D` | **Lazydocker Overlay** | Open floating Docker/Podman container manager TUI |
| `SUPER + SHIFT + Z` | **Zellij Workspace** | Open floating terminal multiplexer session |
| `SUPER + E` | **Dolphin File Manager** | Launch KDE GUI file manager |
| `SUPER + SHIFT + E` | **Yazi File Manager** | Launch terminal file manager in Kitty |
| `SUPER + B` | **Firefox Web Browser** | Launch default web browser |
| `SUPER + R` | **Fuzzel App Launcher** | Open application search menu (with outside-click dismissal) |
| `SUPER + ESCAPE` | **Power & Session Menu** | Open power menu (Lock, Logout, Suspend, Reboot, Shutdown) |
| `SUPER + M` | **Power & Session Menu** | Alternate shortcut for session & power menu |
| `SUPER + L` / `ALT + L` | **Lock Screen** | Immediately trigger `hyprlock` lockscreen |
| `SUPER + C` | **Close Window** | Close active focused window |
| `SUPER + V` | **Toggle Floating** | Switch active window between tiled and floating mode |
| `SUPER + P` | **Toggle Pseudo Tiling** | Toggle pseudo-tile on active window |
| `SUPER + J` | **Toggle Layout Split** | Toggle horizontal/vertical split orientation (dwindle) |
| `SUPER + SHIFT + W` | **Restart Waybar** | Reload and restart Waybar status bar |

---

### 🗂️ Workspaces & Scratchpad Navigation
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + [1-9, 0]` | **Switch Workspace** | Jump directly to workspace 1 through 10 |
| `SUPER + SHIFT + [1-9, 0]` | **Move Window to Workspace** | Move focused window to workspace 1 through 10 |
| `SUPER + S` | **Toggle Special Workspace** | Toggle magic scratchpad workspace |
| `SUPER + SHIFT + S` | **Move to Special Workspace** | Send focused window into magic scratchpad |
| `SUPER + Left / Right / Up / Down` | **Focus Window** | Move focus directionally between windows |
| `SUPER + Mouse Scroll Down` | **Next Workspace** | Switch to next workspace |
| `SUPER + Mouse Scroll Up` | **Previous Workspace** | Switch to previous workspace |
| `SUPER + Left Mouse Drag` | **Move Window** | Drag and move floating or tiled window |
| `SUPER + Right Mouse Drag` | **Resize Window** | Drag to resize window bounds |

---

### ⚡ Productivity & Workflow Utilities
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + /` / `F1` / `?` | **Shortcut Cheat Sheet** | Open interactive **Fuzzel/Wofi** dynamic keybindings viewer |
| `SUPER + SHIFT + P` | **Hyprpicker** | Pick color from screen, copy hex code to clipboard & trigger notification |
| `SUPER + SHIFT + T` / `ALT + T` | **Screen OCR** | Select region with mouse, extract text via Tesseract & copy to clipboard |
| `SUPER + ALT + N` | **Night Light** | Toggle warm blue-light filter (3800K night / 6500K day) |
| `SUPER + =` / `ALT + C` | **Quick Calculator** | Interactive math expression evaluator via Fuzzel prompt |
| `SUPER + .` (period) | **Emoji Picker** | Searchable emoji catalog with automatic clipboard copy & keystroke paste |

---

### 📋 Clipboard Manager (`clipboard_manager.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + SHIFT + V` | **Clipboard Browser** | Open searchable clipboard history with images, snippets, and thumbnails |
| `SUPER + ALT + V` | **Clipboard Browser** | Alternate shortcut for clipboard history |
| `SUPER + SHIFT + C` | **Clipboard Browser** | Alternate shortcut for clipboard history |
| `SUPER + ALT + D` | **Clipboard Cleaner** | Open menu to delete individual entries or wipe complete clipboard cache |

---

### 📸 Screenshots & Screen Recording (`screen_capture.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Print` | **Area Screenshot** | Select screen region with mouse, copy image to clipboard & save file |
| `SHIFT + Print` | **Full Screen Screenshot** | Capture all displays immediately to clipboard and file |
| `ALT + Print` | **Active Window Screenshot**| Capture only the currently focused window |
| `CTRL + Print` | **Annotate Screenshot** | Select region and open in **Swappy** editor to draw arrows, crop, or blur |
| `SUPER + Print` | **Capture Menu** | Open interactive capture dashboard with timer and area options |
| `SUPER + ALT + R` | **Toggle Screen Recording** | Start / stop video recording with `wf-recorder` for selected region |
| `SUPER + SHIFT + R` | **Stop Screen Recording** | Stop active video recording cleanly and save MP4/MKV container |

---

### 🔊 Audio & Media Controls (`volume_control.py` & `playerctl`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `XF86AudioRaiseVolume` | **Volume Up (+5%)** | Increase output volume with visual OSD |
| `XF86AudioLowerVolume` | **Volume Down (-5%)** | Decrease output volume with visual OSD |
| `XF86AudioMute` | **Toggle Mute** | Mute / unmute speaker audio output |
| `XF86AudioMicMute` | **Toggle Mic Mute** | Mute / unmute microphone input |
| `SHIFT + XF86AudioRaiseVolume` | **Mic Volume Up** | Increase microphone input gain |
| `SHIFT + XF86AudioLowerVolume` | **Mic Volume Down** | Decrease microphone input gain |
| `SUPER + SHIFT + A` / `ALT + A` | **Audio Device Switcher** | Interactive menu to switch sinks (headphones, speakers, Bluetooth) |
| `XF86AudioPlay` / `XF86AudioPause` | **Play / Pause** | Toggle media playback (Spotify, browser, playerctl) |
| `XF86AudioNext` | **Next Track** | Skip to next track in active media player |
| `XF86AudioPrev` | **Previous Track** | Skip to previous track in active media player |

---

### ☀️ Brightness Controls (`brightness_control.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `XF86MonBrightnessUp` | **Brightness Up (+5%)** | Increase laptop panel backlight with visual OSD |
| `XF86MonBrightnessDown` | **Brightness Down (-5%)** | Decrease laptop panel backlight with visual OSD |
| `SHIFT + XF86MonBrightnessUp` | **External DDC Up** | Increase external monitor brightness via DDC/CI (`ddcutil`) |
| `SHIFT + XF86MonBrightnessDown` | **External DDC Down** | Decrease external monitor brightness via DDC/CI (`ddcutil`) |
| `SUPER + XF86MonBrightnessUp` | **External DDC Up** | Alternate shortcut for external monitor brightness up |
| `SUPER + XF86MonBrightnessDown` | **External DDC Down** | Alternate shortcut for external monitor brightness down |
| `SUPER + SHIFT + B` / `ALT + B` | **Brightness Presets Menu**| Select brightness presets (20%, 40%, 60%, 80%, 100%) |

---

### 📐 Window Resizing & Screen Scaling (`scale_window.py` & `resolution_menu.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + CTRL + =` / `+` | **Scale Window Up** | Increase active window size by +40px with live dimension OSD |
| `SUPER + CTRL + -` | **Scale Window Down** | Decrease active window size by -40px with live dimension OSD |
| `SUPER + CTRL + Right / L` | **Resize Width Right** | Grow window horizontally to the right |
| `SUPER + CTRL + Left / H` | **Resize Width Left** | Shrink window horizontally from the left |
| `SUPER + CTRL + Up / K` | **Resize Height Up** | Shrink window vertically from the top |
| `SUPER + CTRL + Down / J` | **Resize Height Down** | Grow window vertically to the bottom |
| `SUPER + CTRL + I` / `0` | **Show Window Size** | Display active window dimensions & screen coverage percentage |
| `SUPER + SHIFT + R` / `SHIFT + D` | **Resolution & Scaling Menu**| Interactive menu to set monitor resolution and DPI scaling |
| `SUPER + ALT + 1` to `5` | **Direct Scale Presets** | Set display scale: `1`=1.0x, `2`=1.25x, `3`=1.5x, `4`=1.75x, `5`=2.0x |
| `SUPER + ALT + BackSpace` | **Reset Display Scale** | Instantly reset display scale to default 1.0x (100%) |

---

### ⌨️ Modern CLI Shell Aliases (`~/.config/shell/aliases.sh`)
| Alias | Real Command | Description |
| :--- | :--- | :--- |
| `ls` | `eza --icons --group-directories-first` | Modern file list with icons |
| `ll` | `eza -la --icons --group-directories-first --git` | Long format list with Git status |
| `lt` | `eza --tree --level=2 --icons` | 2-level directory tree view |
| `cat` | `bat --style=plain --paging=never` | Syntax-highlighted output |
| `catp` | `bat --style=full` | Paged syntax output with Git gutters and line numbers |
| `grep` | `rg` | Ripgrep fast regex search |
| `find` | `fd` | Fast, intuitive file/folder search |
| `df` | `duf` | Colorful, clean disk space summary |
| `du` | `dust` | Descending graphical tree visualization of folder size |
| `rm` | `trash-put` | Safe deletion into FreeDesktop Trash (`~/.local/share/Trash`) |
| `tldr` | `tealdeer` | Concise 5-line practical command examples |
| `http` | `xh` | Clean, colored HTTP client with formatted JSON output |
| `md` | `glow -p` | Terminal Markdown pager |
| `lg` | `lazygit` | Launch Git TUI |
| `ld` | `lazydocker` | Launch Docker/Podman container TUI |
| `zj` | `zellij` | Launch Zellij terminal multiplexer |
| `ff` | `fastfetch` | Display hardware and OS info |

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

### ⚙️ Theme Customization (`sddm/themes/catppuccin-mocha/theme.conf`)
Modify `~/.dotfiles/sddm/themes/catppuccin-mocha/theme.conf` to customize:
- `Background`: Path to custom wallpaper (SVG/PNG/JPG)
- `FontFamily`: Preferred system font (defaults to `JetBrainsMono Nerd Font`)
- `ClockFormat` / `DateFormat`: Time and date layout formats
- `AccentColor`: Primary accent hex color (`#cba6f7`)
- `ShowSessions` / `ShowPowerButtons` / `ShowGreeting`: Toggle UI component visibility
