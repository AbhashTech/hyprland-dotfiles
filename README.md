# 🌌 Unified Hyprland & Wayland Dotfiles

A modular, unified, and fully version-controlled dotfiles suite for **Hyprland** on Arch Linux. Features **Waybar**, **Fuzzel**, **Mako**, **Wofi**, **Wlogout**, **Btop**, **Kitty**, **Starship**, **Lazygit**, **Zellij**, **Swappy**, custom OSD overlays, Catppuccin Mocha themed SDDM greeter, dynamic power profiles, keyboard layout management, clipboard history, media/audio switchers, dynamic shortcut viewer, and a comprehensive modern CLI productivity suite (100% official Pacman packages).

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
    │   ├── hyprlock.conf        # Catppuccin Mocha lockscreen configuration
    │   ├── hypridle.conf        # Screen timeout & idle power management
    │   ├── install.sh           # Standalone Hyprland installer
    │   ├── modules/             # Config modules (animations, keybinds, rules, monitors, input, etc.)
    │   │   ├── animations.lua   # Fluid window & workspace animation curves
    │   │   ├── appearance.lua   # Gaps, active/inactive borders, shadows & blur
    │   │   ├── autostart.lua    # Services, background daemons & polkit agent
    │   │   ├── env.lua          # Wayland & cursor environment variables
    │   │   ├── input.lua        # Keyboard layout, mouse sensitivity & touchpad gestures
    │   │   ├── keybinds.lua     # Complete keybindings & application shortcuts
    │   │   ├── layouts.lua      # Dwindle, master, and scrolling tiling layouts
    │   │   ├── misc.lua         # Wallpaper, logo & miscellaneous compositor settings
    │   │   ├── monitors.lua     # Display resolution, position & scaling
    │   │   ├── permissions.lua  # Security & ecosystem permission settings
    │   │   ├── programs.lua     # Default apps (terminal, browser, file manager, launcher)
    │   │   └── rules.lua        # Window rules, layer blur & workspace persistence
    │   └── scripts/             # Python & Shell utilities
    │       ├── app_shortcut_creator.py # App menu shortcut (.desktop) creator & manager GUI/CLI
    │       ├── brightness_control.py # Panel & external DDC brightness with OSD & presets
    │       ├── clipboard_manager.py  # Image/text clipboard manager with previews & purge
    │       ├── emoji_picker.py       # Searchable emoji catalog with auto-typing
    │       ├── fuzzel_launcher.sh    # Fuzzel wrapper with outside-click dismissal
    │       ├── keybinds_viewer.py    # Dynamic keybinds parser & searchable overlay
    │       ├── keyboard_layout.py    # Dynamic keyboard layout switcher & installer
    │       ├── monitor_workspace_manager.py # Automatic workspace allocator for external monitors
    │       ├── nightlight.py         # Blue-light filter (3800K night / 6500K day)
    │       ├── ocr_grab.py           # Optical character recognition text grabber
    │       ├── quick_calc.py         # Interactive math expression evaluator
    │       ├── resolution_menu.py    # Display resolution & UI scaling switcher
    │       ├── scale_window.py       # Window resizing with on-screen dimensions overlay
    │       ├── screen_capture.py     # Screenshot & video recorder with Swappy annotation
    │       ├── theme_switcher.py     # Universal desktop theme switcher & palette manager
    │       ├── volume_control.py     # Speaker/mic volume control, OSD & sink switcher
    │       ├── wallpaper_switcher.py # Wallpaper randomizer & selector (~/Wallpaper)
    │       └── wofi_launcher.py      # Wofi wrapper with transparent backdrop layer
    ├── waybar/                  # Waybar Status Bar
    │   ├── config.jsonc         # Bar layout, modules, click actions & tooltips
    │   ├── style.css            # Styling, gradients, glassmorphism & dynamic colors
    │   └── scripts/             # Waybar helper scripts & TUI / popup menus
    │       ├── battery-status.py     # Battery health & power profile JSON provider
    │       ├── bluetooth-menu.sh     # Interactive Bluetooth device manager
    │       ├── brightness-manager.py # GTK LayerShell Display Brightness & Contrast Control Center
    │       ├── brightness-menu.sh    # Waybar brightness click/scroll launcher
    │       ├── clipboard.py          # Clipboard history Waybar status provider
    │       ├── connectivity.py       # Network & Internet connectivity tester
    │       ├── keyboard-layout.py    # Layout status & click switcher for Waybar
    │       ├── launch_waybar.sh      # Waybar launch & toggle script with persistence
    │       ├── launch_waybar.py      # Python Waybar process controller
    │       ├── netctl-tui.py         # Terminal UI network connection manager
    │       ├── network-menu.sh       # Wi-Fi / Ethernet interactive network menu
    │       ├── notifications.py      # Mako notification center & DND toggle
    │       ├── power-menu.sh         # Wlogout & session power launcher
    │       ├── power-profile.py      # Interactive GTK LayerShell power profile selector
    │       ├── quick-settings.py     # Quick settings & hardware shortcuts menu
    │       ├── sound-manager.py      # Interactive GTK LayerShell audio & volume hub
    │       ├── sound-menu.sh         # Sound launcher for Waybar
    │       ├── system-stats.py       # Interactive GTK LayerShell hardware & stats dashboard
    │       └── toggle-stats.py       # Hardware stats drawer toggler
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
    ├── wlogout/                 # Wayland Logout & Power Menu
    │   ├── layout               # Lock, logout, suspend, reboot, shutdown buttons
    │   └── style.css            # Catppuccin glassmorphism modal stylesheet
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
| **Session, Lock & Logout** | `hyprlock`, `hypridle`, `wlogout` | Catppuccin Mocha lockscreen, idle management, and Wayland power modal |
| **Status Bar & Power** | `waybar`, `power-profiles-daemon`, `upower` | Status bar with hardware stats, power profile selector & battery metrics |
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
| **Python Runtime & UI** | `python`, `python-gobject`, `gtk3`, `gtk-layer-shell` | Python 3, PyGObject, and Wayland layer-shell for popups |
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
- Deploy and activate the Catppuccin Mocha SDDM theme.

### Shell Integration

Add the following lines to your `~/.bashrc` or `~/.zshrc`:
```bash
source ~/.config/shell/env.sh
source ~/.config/shell/aliases.sh
```

---

## 📊 Waybar Architecture & Interactive Features

The top status bar is divided into three functional zones:

### 1. Left Zone
- **󰣇 Application Launcher (`custom/launcher`)**: Left-click launches **Fuzzel** with backdrop blur; right-click opens the **Wlogout** power menu.
- **Workspaces (`hyprland/workspaces`)**: Persistent workspaces 1–4 with live active badges and automatic available workspace allocation when connecting external monitors; mouse scroll cycles through workspaces.
- **Active Window (`hyprland/window`)**: Shows current focused window title with contextual application icons (Firefox, Kitty, Dolphin, VS Code).
- **MPRIS Media Controller (`mpris`)**: Shows currently playing media (Spotify, Firefox, mpv) with play/pause click and scroll track skipping.

### 2. Center Zone
- ** Clock & Calendar (`clock`)**: 12h/24h digital clock with a rich interactive Catppuccin calendar tooltip. Right-click toggles format; scroll navigates months.
- **󰌌 Keyboard Layout (`hyprland/language`)**: Live keyboard layout indicator (e.g. US). Left-click cycles layout; right-click opens layout menu; middle-click opens layout installer.

### 3. Right Zone
- **Group Tray & Notifications (`group/tray-notif`)**:
  - System tray (`tray`) for background application indicators.
  - Clipboard indicator (`custom/clipboard`): Left-click browses history; right-click opens deletion menu; middle-click pauses/resumes daemon.
  - Notification center (`custom/notification`): Left-click shows history; right-click toggles Do-Not-Disturb (DND); middle-click clears all.
- **Group Status (`group/status`)**:
  - PipeWire Audio (`pulseaudio`): Volume level and mute state. Left-click toggles mute; right-click opens sound manager menu; middle-click opens TUI mixer; scroll adjusts volume.
  - Screen Brightness (`backlight`): Live display brightness percentage and adaptive icon (`󰃞`, `󰃟`, `󰃠`). Left-click opens the Display & Brightness Control Center with range sliders; right-click toggles Night Light; middle-click launches floating TUI mixer; scroll adjusts brightness (±5%) with OSD.
  - Network (`network`): Wi-Fi signal strength and Ethernet link state. Left-click opens network manager menu.
  - Bluetooth (`bluetooth`): Connection status and battery percentage. Left-click opens device selector; right-click toggles RFKill.
  - Battery & Power Profiles (`custom/battery`): Dynamic battery percentage and power profile color indicator. Left/right click opens power profile selector.
- **󰍛 System Hardware & Stats Chip (`custom/stats`)**:
  - Displays a clean chip icon in Waybar.
  - **Left-Click**: Opens the **GTK LayerShell** System Hardware & Stats Dashboard with live metrics, gradient progress bars, and outside-click dismissal.
  - **Right-Click**: Directly opens **Btop** task monitor (`kitty --class btop -e btop`).
- **󰐥 Power Menu (`custom/power`)**: Left-click launches **Wlogout** session modal.

---

## ☀️ Display Brightness & External Monitor Manager

The dotfiles include a dedicated **Display & Brightness Control Center** ([`brightness-manager.py`](file:///home/kunal/.dotfiles/.config/waybar/scripts/brightness-manager.py)):

- **Instant Launch (<30ms)**: Pre-caches display metadata and runs non-blocking background DDC/CI hardware synchronization so the window renders immediately on click.
- **Built-in Laptop Display Controls**:
  - Continuous range slider (1% – 100%) with live value badge.
  - Quick preset buttons (`10%`, `25%`, `50%`, `75%`, `100%`).
- **External Monitor(s) Brightness & Contrast (DDC/CI)**:
  - Auto-detects connected external displays (e.g. HDMI, DisplayPort).
  - Dedicated **Brightness Range Slider** (0% – 100%) with presets (`20%`, `40%`, `60%`, `80%`, `100%`).
  - Dedicated **Contrast Range Slider** (0% – 100%) with presets (`30%`, `50%`, `70%`, `85%`, `100%`).
  - Asynchronous debounced hardware writes for smooth 60fps slider drag without UI freeze.
- **Night Light (Blue Light Filter)**:
  - One-click toggle button with active state badge.
  - Color temperature range slider (2500K – 6500K) and presets (`3000K Candle`, `3800K Warm`, `4500K Soft`, `6500K Daylight`).
- **Alternative Modes**:
  - **Terminal Curses TUI**: Launch via `~/.config/waybar/scripts/brightness-manager.py --tui` or middle-click Waybar brightness icon.
  - **Fuzzel / Wofi Menu**: Launch via `~/.config/waybar/scripts/brightness-manager.py --menu`.

---

## 🖥️ System Hardware & Stats Dashboard

The dotfiles include a dedicated **System Hardware & Stats** popup ([`system-stats.py`](file:///home/kunal/.dotfiles/.config/waybar/scripts/system-stats.py)):

- **Chip Icon in Waybar (`󰍛`)**: A minimal and responsive chip indicator on the right side of the status bar.
- **Left-Click Dashboard Popup**: Opens a glassmorphic **GTK LayerShell** modal styled with high-contrast Catppuccin Mocha colors:
  - **Dynamic Sizing & Scrolling**: Automatically calculates active monitor dimensions via `hyprctl` to utilize **~90% of screen height** with a smooth custom-styled scrolling container, preventing any overflow on compact or fractional scaled screens.
  - **Host & System Info**: Displays hostname, Linux kernel release, and formatted system uptime.
  - **CPU Utilization**: Live percentage, CPU model name, total core count, 1m/5m/15m load averages, and a Sky/Mauve gradient progress bar.
  - **Memory & Storage Metrics**: Dual cards showing GiB RAM and Swap usage metrics alongside root disk (`/`) capacity and utilization bars.
  - **All Hardware Temperatures**: Aggregates and displays all detected hardware temperature sensors (**CPU Package**, **Per-Core temperatures**, **NVMe SSD**, and **Motherboard/Ambient sensors**) with dynamic thermal health badges and color thresholds.
  - **Dedicated Top Active Processes**: A dedicated section displaying the top active tasks with process name, PID, `% CPU` badge, and `% RAM` badge.
  - **High-Contrast Btop Launcher**: High-visibility interactive action button (and right-click trigger) to launch **Btop** in Kitty terminal.
  - **Outside-Click & Escape Dismissal**: Transparent full-screen backdrop dismissal and Escape key handling.
- **Right-Click Action**: Instantly launches the **Btop** interactive terminal monitor.

---

## 🔋 Power Management & Waybar Profiles

The dotfiles include a dedicated **Power Profile & Battery Management** system:

- **Dynamic Icon Coloring**: The Waybar battery icon changes color in real-time based on the active power profile:
  - **🌱 Power Saver**: **Green** (`#a6e3a1`) — Reduces CPU clocks and limits background power draw.
  - **⚖ Balanced**: **Orange** (`#fab387`) — Standard dynamic balance between speed and battery life.
  - **🚀 Performance**: **Red** (`#f38ba8`) — Maximum CPU clock speeds and responsiveness for heavy workloads.
- **Rich Hover Tooltip**: Hovering over the battery icon displays the active power mode, charging state, estimated time remaining, and battery hardware health percentage.
- **Interactive Selector Popup**: **Clicking** the battery icon opens a glassmorphic **GTK LayerShell** popup styled with Catppuccin Mocha colors:
  - Features high-contrast cards, active state badges, outside-click backdrop dismissal, and `Escape` key handling.
  - Switches profiles instantly via `power-profiles-daemon` over DBus and notifies Waybar for zero-latency UI updates.

---

## 🎨 Universal Theming System & Dynamic Color Variables

The dotfiles include a centralized, modular **Theming System** ([`theme_switcher.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/theme_switcher.py)) that dynamically discovers JSON theme files from `~/.config/theme/*.json` and applies them live across the entire desktop:

- **19 Curated Palettes (11 Dark & 8 Light)**:
  - **Dark Palettes**:
    - **Catppuccin Mocha** (Default Warm Dark)
    - **Catppuccin Macchiato** (Medium Dark)
    - **Catppuccin Frappé** (Soft Slate Dark)
    - **Tokyo Night** (Iconic Cyberpunk Dark Blue)
    - **Nord Arctic** (Arctic Ice Blue & Frost)
    - **Gruvbox Dark** (Retro Earthy Golden Tones)
    - **Rosé Pine** (Soho Warm Pine & Rose Gold)
    - **Dracula** (Vibrant Gothic Purple & Neon Green)
    - **Everforest Dark** (Serene Forest Green & Moss)
    - **One Dark Pro** (Atom Balanced Dark Aesthetic)
    - **Cyberpunk Synthwave** (High-Octane Neon Magenta & Cyan)
  - **Light Palettes**:
    - **Catppuccin Latte** (Crisp Clean Light Theme)
    - **Tokyo Night Day** (Daylight Cyberpunk Sky Blue & Indigo)
    - **Gruvbox Light** (Warm Parchment Paper & Retro Tones)
    - **Rosé Pine Dawn** (Soft Morning Light, Blush & Gold)
    - **Everforest Light** (Warm Natural Paper & Sage Green)
    - **Nord Snow Storm** (Pure Arctic Snow & Frosted Slate)
    - **One Light Pro** (Atom Balanced Bright Development Theme)
    - **Solarized Light** (Warm Precision Calibrated Light Palette)

- **Dynamic Color Variables & Transparent Waybar Architecture**:
  - **Waybar Dynamic Backdrop**: Waybar's root glassmorphic background, shadow, module containers, borders, and tooltips automatically adjust their transparency, tint, and borders based on the active theme's palette and dark/light mode (`@waybar_bg`, `@waybar_border`, `@module_bg`, `@module_hover_bg`).
  - **Hyprland**: Border colors and shadows consume variables from [`modules/theme.lua`](file:///home/kunal/.dotfiles/.config/hypr/modules/theme.lua).
  - **Dolphin, Kate & KWrite**: KDE color schemes ([`kdeglobals`](file:///home/kunal/.dotfiles/.config/kdeglobals)), editor syntax highlighting themes ([`org.kde.syntax-highlighting`](file:///home/kunal/.local/share/org.kde.syntax-highlighting/themes)), and UI configs ([`katerc`](file:///home/kunal/.config/katerc), [`kwriterc`](file:///home/kunal/.config/kwriterc)) synchronized live across all 19 themes.
  - **Fuzzel, Mako, Wofi, Wlogout & Hyprlock**: Color variables updated seamlessly.
  - **Starship, Zellij, Btop, Lazygit & Swappy**: Palettes and accents dynamically synchronized.
  - **Extensibility**: Add new themes at any time by dropping a single `.json` file into `~/.config/theme/<name>.json`.



- **Usage**:
  - **Graphical Menu**: Press **`SUPER + T`** to open the interactive Fuzzel/Wofi theme picker with active indicator.
  - **Cycle Themes**: Press **`SUPER + CTRL + T`** to instantly cycle forward through all available themes.
  - **Terminal CLI**:
    ```bash
    python3 ~/.config/hypr/scripts/theme_switcher.py --list
    python3 ~/.config/hypr/scripts/theme_switcher.py --set tokyo-night
    python3 ~/.config/hypr/scripts/theme_switcher.py --next
    ```

---

## ⚡ Dynamic Keybindings Viewer & Cheat Sheet


The repository includes an intelligent dynamic shortcut viewer ([`keybinds_viewer.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/keybinds_viewer.py)) that parses doc-comments directly from [`keybinds.lua`](file:///home/kunal/.dotfiles/.config/hypr/modules/keybinds.lua):

- **Desktop GUI**: Press **`SUPER + /`**, **`SUPER + ?`**, or **`SUPER + F1`** to open an interactive, fuzzy-searchable Fuzzel overlay. Selecting any shortcut automatically copies the key combination to your clipboard.
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
| `SUPER + SHIFT + W` | **Toggle Waybar** | Toggle Waybar status bar on/off with state persistence |

---

### 🌐 Keyboard Layout & Input Switching
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + Space` | **Next Keyboard Layout** | Cycle to next active keyboard layout |
| `SUPER + SHIFT + K` | **Keyboard Layout Menu** | Open interactive selector for active layouts |
| `SUPER + ALT + K` | **Add Keyboard Layout** | Search and add regional layout variants (including Indian languages) |

---

### 🔔 Notifications & Quick Settings
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + N` | **Notifications Center** | Open notification history and management center |
| `SUPER + SHIFT + N` | **Toggle DND** | Toggle Do-Not-Disturb notification silencing mode |
| `SUPER + SHIFT + V` | **Clipboard Browser** | Open searchable clipboard history with images and snippets |
| `SUPER + ALT + V` / `SUPER + SHIFT + C` | **Clipboard Browser** | Alternate shortcuts for clipboard history |
| `SUPER + ALT + D` | **Clipboard Cleaner** | Open menu to delete individual entries or wipe clipboard cache |

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
| `SUPER + T` | **Theme Switcher** | Open interactive **Fuzzel/Wofi** theme selector (12 curated themes, live reload) |
| `SUPER + CTRL + T` | **Cycle Theme** | Instantly cycle to the next color palette in the theme registry |
| `SUPER + /` / `SUPER + ?` / `SUPER + F1` | **Shortcut Cheat Sheet** | Open interactive **Fuzzel/Wofi** dynamic keybindings viewer |
| `SUPER + SHIFT + P` | **Hyprpicker** | Pick color from screen, copy hex code to clipboard & trigger notification |
| `SUPER + SHIFT + T` / `SUPER + ALT + T` | **Screen OCR** | Select region with mouse, extract text via Tesseract & copy to clipboard |
| `SUPER + ALT + N` | **Night Light** | Toggle warm blue-light filter (3800K night / 6500K day) |
| `SUPER + =` / `SUPER + ALT + C` | **Quick Calculator** | Interactive math expression evaluator via Fuzzel prompt |
| `SUPER + .` (period) | **Emoji Picker** | Searchable emoji catalog with automatic clipboard copy & keystroke paste |
| `SUPER + ALT + S` | **App Shortcut Creator** | Launch interactive GTK/CLI desktop shortcut (.desktop) creator & manager |



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
| `SUPER + SHIFT + A` / `SUPER + ALT + A` | **Audio Device Switcher** | Interactive menu to switch sinks (headphones, speakers, Bluetooth) |
| `XF86AudioPlay` / `XF86AudioPause` | **Play / Pause** | Toggle media playback (Spotify, browser, playerctl) |
| `XF86AudioNext` | **Next Track** | Skip to next track in active media player |
| `XF86AudioPrev` | **Previous Track** | Skip to previous track in active media player |

---

### ☀️ Brightness Controls (`brightness_control.py` & `brightness-manager.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `XF86MonBrightnessUp` | **Brightness Up (+5%)** | Increase laptop panel backlight with visual OSD |
| `XF86MonBrightnessDown` | **Brightness Down (-5%)** | Decrease laptop panel backlight with visual OSD |
| `SHIFT + XF86MonBrightnessUp` | **External DDC Up** | Increase external monitor brightness via DDC/CI (`ddcutil`) |
| `SHIFT + XF86MonBrightnessDown` | **External DDC Down** | Decrease external monitor brightness via DDC/CI (`ddcutil`) |
| `SUPER + XF86MonBrightnessUp` | **External DDC Up** | Alternate shortcut for external monitor brightness up |
| `SUPER + XF86MonBrightnessDown` | **External DDC Down** | Alternate shortcut for external monitor brightness down |
| `SUPER + SHIFT + B` / `SUPER + ALT + B` | **Display Control Center**| Open GTK LayerShell Display Brightness & Contrast Control Center with range sliders |

---

### 📐 Window Resizing & Screen Scaling (`scale_window.py` & `resolution_menu.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + CTRL + =` / `+` / `KP_Add` | **Scale Window Up** | Increase active window size by +40px with live dimension OSD |
| `SUPER + CTRL + -` / `KP_Subtract` | **Scale Window Down** | Decrease active window size by -40px with live dimension OSD |
| `SUPER + CTRL + Right / L` | **Resize Width Right** | Grow window horizontally to the right |
| `SUPER + CTRL + Left / H` | **Resize Width Left** | Shrink window horizontally from the left |
| `SUPER + CTRL + Up / K` | **Resize Height Up** | Shrink window vertically from the top |
| `SUPER + CTRL + Down / J` | **Resize Height Down** | Grow window vertically to the bottom |
| `SUPER + CTRL + I` / `0` | **Show Window Size** | Display active window dimensions & screen coverage percentage |
| `SUPER + SHIFT + R` / `SUPER + SHIFT + D` | **Resolution & Scaling Menu**| Interactive menu to set monitor resolution and DPI scaling |
| `SUPER + ALT + =` / `+` | **Display Scale Up** | Increment display scaling (+0.1) |
| `SUPER + ALT + -` | **Display Scale Down** | Decrement display scaling (-0.1) |
| `SUPER + ALT + 0` | **Show Display Scale** | Display active monitor resolution & scale factor |
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
