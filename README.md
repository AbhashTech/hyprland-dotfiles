# 🌌 Unified Hyprland & Wayland Dotfiles

A modular, unified, and fully version-controlled dotfiles suite for **Hyprland** on Arch Linux. Features **Quickshell** (modular status bar and native plugins suite for App Menu, Power Session, Clipboard, Calculator, Emojis, Keybindings, Audio Mixer, Display Brightness, and System Resources), **Mako**, **Btop**, **Foot**, **Starship**, **Lazygit**, **Zellij**, **Swappy**, custom OSD overlays, Catppuccin Mocha themed SDDM greeter, dynamic power profiles, keyboard layout management, media/audio switchers, and a comprehensive modern CLI productivity suite (100% official Pacman packages).

---

## 📁 Repository Structure

```
~/.dotfiles/
├── install.sh                   # All-in-one dependency installer & symlink deployer (Pacman native)
├── .zshrc                      # Modern Zsh shell configuration (history, plugins, prompt)
├── .gitignore                   # Exclusions for temporary files & Python cache
├── README.md                    # Full documentation and shortcut cheat sheet
├── sddm/                        # SDDM Theme Suite (Left-Sidebar Frosted Glass Layout)
│   ├── test-theme.sh            # Live test-mode theme previewer (Qt6)
│   ├── scripts/
│   │   ├── hide-unwanted-apps.sh# App launcher cleaner
│   │   └── install-theme.sh     # System deployment & /etc/sddm.conf.d activator
│   └── themes/catppuccin-mocha/ # Full Qt6 QML Theme
│       ├── Main.qml             # Main greeter entrypoint & SDDM bindings
│       ├── metadata.desktop     # Theme metadata definition
│       ├── theme.conf           # User-customizable settings (colors, background, fonts)
│       ├── components/          # Modular QML components (UsernameField, PasswordField, Clock, PowerMenu, Session)
│       └── assets/              # Vector SVG icons & custom wallpaper artwork
└── .config/
    ├── hypr/                    # Hyprland Compositor Config & Scripts
    │   ├── hyprland.lua         # Main modular entrypoint
    │   ├── hyprlock.conf        # Unified left-sidebar lockscreen configuration
    │   ├── assets/              # Lockscreen background artwork (lock_bg.jpg)
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
    │       ├── bluetooth_agent.py    # Background Bluetooth auto-pairing DBus agent
    │       ├── brightness_control.py # Panel & external DDC brightness with OSD & presets
    │       ├── clipboard_manager.py  # Image/text clipboard manager daemon & thumbnailer
    │       ├── hyprsunset-hypridle.desktop # Application menu entry for Night Light & Idle Manager
    │       ├── keyboard-layout-manager.desktop # Application menu entry for Keyboard Layout & Variant Manager
    │       ├── keyboard_layout.py    # Dynamic keyboard layout switcher, regional installer & GTK3 Manager
    │       ├── monitor_workspace_manager.py # Automatic workspace allocator for external monitors
    │       ├── ocr-language-manager.desktop # Application menu entry for OCR Language Manager
    │       ├── ocr_grab.py           # Optical character recognition text grabber
    │       ├── ocr_language_manager.py # Tesseract OCR language model downloader, manager & selector (GTK3/CLI)
    │       ├── plugin-manager.desktop # Application menu entry for Quickshell Plugin Manager
    │       ├── qr_reader.py          # Screen QR / 2D barcode scanner & decoder
    │       ├── resolution_menu.py    # Display resolution & UI scaling switcher
    │       ├── scale_window.py       # Window resizing with on-screen dimensions overlay
    │       ├── screen_capture.py     # Screenshot & video recorder with Swappy annotation
    │       ├── sunset_idle_manager.py # Unified Hyprsunset & Hypridle display power & idle control center (GTK3/Menu/CLI)
    │       ├── theme-manager.desktop # Application menu entry for graphical Theme Manager
    │       ├── theme_switcher.py     # Universal desktop theme switcher & palette manager (GTK3/CLI)
    │       ├── volume_control.py     # Speaker/mic volume control, OSD & sink switcher
    │       └── wallpaper_switcher.py # Wallpaper randomizer & selector (~/Wallpaper)
    ├── quickshell/              # Quickshell Status Bar & Desktop Shell Suite
    │   ├── shell.qml            # Main entrypoint, screen variants, status bar & plugin windows
    │   ├── Theme.qml            # Dynamic palette provider connected to colors.json
    │   ├── PluginManager.qml    # Singleton managing plugin visibility & IPC state
    │   ├── components/          # Modular bar capsules (Launcher, Workspaces, Window, MPRIS, Clock, Status, Tray)
    │   ├── plugins/             # Built-in Quickshell Plugins (Folderwise)
    │   │   ├── appmenu/         # Searchable Application Launcher with categories & desktop scanning
    │   │   ├── powermenu/       # Glassmorphic session menu (Lock, Suspend, Logout, Reboot, Shutdown)
    │   │   ├── clipboard/       # Live searchable clipboard history drawer (cliphist & wl-copy)
    │   │   ├── calc/            # Quick math evaluator & instant copy
    │   │   ├── emoji/           # Categorized emoji picker with wtype auto-paste
    │   │   ├── keybinds/        # Interactive shortcut reference cheat sheet
    │   │   ├── volume/          # Audio mixer & speaker/mic slider popup
    │   │   ├── brightness/      # Display backlight & warm night light popup
    │   │   ├── connectivity/    # Native Wi-Fi & Bluetooth network management
    │   │   ├── battery/         # Battery metrics & dynamic power profile selector
    │   │   ├── notifications/   # Notification center & history viewer
    │   │   ├── sysinfo/         # System hardware dashboard (CPU, RAM, Disk) with fast 800ms updates
    │   │   ├── filepicker/      # Floating File Uploader & Selector Modal with XDG Portal, preview & thumbnail grid
    │   │   ├── workspace_viewer/# Interactive multi-workspace layout viewer & hover snapshot previews
    │   │   └── plugin-manager/  # Comprehensive Quickshell Plugin Manager, store catalog, template scaffolder & git sync
    │   ├── custom_plugins/      # User Custom Plugins (untracked by git, see README inside)
    │   └── scripts/             # Supervisor scripts (launch_quickshell.sh, toggle_plugin.sh, plugin_loader.sh)
    ├── wireplumber/             # WirePlumber Audio Session Rules
    │   └── wireplumber.conf.d/  # Software DSP mixing (51-alsa-soft-mixer.conf) & profile priority routing (52-alsa-routes.conf)
    ├── foot/                    # Foot Terminal Emulator
    │   ├── foot.ini             # Font, geometry, latency, ergonomics & keybinds
    │   └── theme.ini            # Dynamic theme colors (Catppuccin Mocha & multi-theme)
    ├── starship.toml            # Starship Cross-Shell Prompt (Catppuccin Mocha, multi-theme, continuation prompt & Claude Code statusline)
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
    ├── mako/                    # Notification Daemon
    │   └── config               # Formatting, timeouts, icons, border & colors
    └── btop/                    # System & Resource Monitor
        └── btop.conf            # Layout, update intervals, process sorting & graphs
```

---

## 📦 What All Needs to be Installed (100% Official Pacman Repos)

| Component | Packages / Tools | Description |
| :--- | :--- | :--- |
| **Display Manager (SDDM)**| `sddm`, `qt6-declarative`, `qt6-svg`, `qt6-5compat` | Qt6 display manager & Catppuccin Mocha glassmorphic greeter |
| **Compositor & Portals** | `hyprland`, `xdg-desktop-portal-hyprland`, `xdg-desktop-portal-gtk`, `xdg-utils`, `xdg-user-dirs`, `hyprpolkitagent` | Wayland compositor, XDG portals for screen sharing & file dialogs, and Polkit agent |
| **Session, Lock & Logout** | `hyprlock`, `hypridle`, `quickshell` | Catppuccin Mocha lockscreen, idle management, and Quickshell Power Menu plugin |
| **Status Bar & Desktop Suite** | `quickshell`, `power-profiles-daemon`, `upower` | Modern Quickshell status bar, modular capsules, hardware stats, power profile selector & battery metrics |
| **Notifications** | `mako`, `libnotify` | Notification daemon & `notify-send` for OSDs (with click-to-focus) |
| **Wallpaper** | `hyprpaper` | Fast Wayland wallpaper daemon |
| **App Launchers & Theming** | `quickshell`, `nwg-look`, `gsettings-desktop-schemas`, `dconf`, `xsettingsd` | Fast Quickshell Application Menu plugin and GTK3/4 & DConf settings sync |
| **Qt/GTK Unified Integration** | `qt5-wayland`, `qt6-wayland`, `qt5ct`, `qt6ct`, `kvantum`, `kvantum-qt5` | Native Wayland runtime and uniform theme/font/icon syncing across Qt5/Qt6 & GTK apps |
| **File Pickers, Mounts & Thumbs** | `dolphin`, `yazi`, `gvfs`, `gvfs-mtp`, `gvfs-smb`, `tumbler`, `ffmpegthumbnailer`, `poppler-glib`, `webp-pixbuf-loader`, `trash-cli` | File managers, external drive mounting, trash bin support, and PDF/video/image thumbnail previews |
| **Default Media & App Viewers** | `loupe`, `mpv`, `zathura`, `zathura-pdf-mupdf`, `file-roller` | Fast image viewer, media player, minimalist PDF reader, and archive manager |
| **Modern CLI Power Suite** | `eza`, `bat`, `ripgrep`, `fd`, `git-delta`, `duf`, `dust`, `tealdeer`, `xh`, `glow`, `fzf`, `zoxide`, `wtype` | Daily replacements for ls, cat, grep, find, diff, du, df, man, curl |
| **TUIs & Multiplexing** | `lazygit`, `lazydocker`, `zellij`, `btop`, `fastfetch` | Interactive terminal UIs for Git, Docker, terminal multiplexing, and system monitoring |
| **Performance, Gaming & Thermals** | `gamemode`, `thermald`, `power-profiles-daemon`, `upower` | Process CPU/GPU optimizer, Intel thermal daemon, and hardware power profile metrics |
| **Shell & Environment** | `starship`, `zsh`, `zsh-autosuggestions`, `zsh-syntax-highlighting`, `atuin`, `direnv`, `mise` | Fast prompt, Zsh shell with autosuggestions & syntax highlighting, SQLite history search, per-directory env/venv, tool version manager |
| **Audio & Media Codecs** | `pipewire`, `pipewire-pulse`, `pipewire-alsa`, `pipewire-jack`, `wireplumber`, `libldac`, `libfreeaptx`, `gst-plugins-good`, `gst-plugins-bad`, `gst-plugins-ugly`, `gst-libav`, `playerctl`, `libva-utils` | PipeWire audio suite, LDAC/aptX Bluetooth HD codecs, GStreamer codecs, VA-API utils, and MPRIS playback keys |
| **System Tuning & Cleanup** | `zram-generator`, `pacman-contrib` | Compressed in-memory ZRAM swap and automated pacman cache maintenance |
| **Brightness & Night Light**| `brightnessctl`, `ddcutil`, `hyprsunset` / `wlsunset` | Backlight, external DDC brightness, and warm blue-light filter |
| **Authentication & Hardware 2FA**| `gnome-keyring`, `libsecret`, `polkit-gnome`, `libfido2`, `ccid`, `pcsc-tools`, `yubikey-manager` | Secrets/password storage, Polkit agent, and YubiKey / FIDO2 security key support |
| **Clipboard** | `wl-clipboard`, `cliphist` | Wayland clipboard manager with binary image and thumbnail support |
| **Screen Capture & OCR** | `grim`, `slurp`, `swappy`, `wf-recorder`, `hyprpicker`, `tesseract`, `tesseract-data-eng`, `zbar` | Screenshots, annotation, video recording, color picker, OCR & QR scanner |
| **Python Runtime & UI** | `python`, `python-gobject`, `gtk3`, `gtk4`, `gtk-layer-shell` | Python 3, PyGObject, and Wayland layer-shell for popups |
| **Fonts & Icons** | `ttf-jetbrains-mono-nerd`, `ttf-liberation`, `noto-fonts`, `noto-fonts-cjk`, `noto-fonts-emoji`, `papirus-icon-theme`, `adwaita-icon-theme` | Nerd font glyphs, CJK characters, emojis, and complete icon themes |

---

## 🛠️ How to Install

### All-in-One Pacman Command

```bash
sudo pacman -S --needed \
    qt5-wayland qt6-wayland qt5ct qt6ct kvantum kvantum-qt5 \
    nwg-look gsettings-desktop-schemas dconf \
    papirus-icon-theme adwaita-icon-theme \
    xdg-desktop-portal-hyprland xdg-desktop-portal-gtk xdg-utils xdg-user-dirs \
    gvfs gvfs-mtp gvfs-smb tumbler ffmpegthumbnailer poppler-glib webp-pixbuf-loader trash-cli \
    loupe mpv zathura zathura-pdf-mupdf file-roller gamemode thermald \
    pipewire pipewire-pulse pipewire-alsa pipewire-jack wireplumber \
    libldac libfreeaptx gst-plugins-good gst-plugins-bad gst-plugins-ugly gst-libav playerctl libva-utils \
    gnome-keyring libsecret polkit-gnome libfido2 ccid pcsc-tools yubikey-manager \
    noto-fonts noto-fonts-cjk noto-fonts-emoji ttf-liberation ttf-jetbrains-mono-nerd \
    wl-clipboard cliphist brightnessctl zram-generator pacman-contrib zbar
```

### Automated Setup (Recommended)

```bash
chmod +x ~/.dotfiles/install.sh
~/.dotfiles/install.sh
```

The installer will:
- Install all official Arch Linux packages via `pacman`.
- Symlink all `~/.dotfiles/.config/*` into `~/.config/` (safely backing up existing folders).
- Deploy unified default MIME associations (`mimeapps.list`).
- Hide internal, technical, and background helper apps from application launchers.
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

## 📊 Status Bar Architecture & Interactive Features (Quickshell)

The top status bar is built with **Quickshell** (`~/.config/quickshell/shell.qml`) featuring a glassmorphic island design across three functional zones and modular native plugins:

### 1. Left Zone
- **󰣇 Application Launcher (`LauncherButton.qml`)**: Left-click opens the native **Quickshell App Launcher** popup with live desktop application search, categories, and icons; right-click opens the **Quickshell Power Menu**.
- **Workspaces (`Workspaces.qml`)**: Persistent workspaces 1–4 with live active badges and automatic available workspace allocation when connecting external monitors; mouse scroll cycles through workspaces.
- **Active Window (`ActiveWindow.qml`)**: Shows current focused window title with contextual application icons (Firefox, Foot, Dolphin, VS Code).

### 2. Center Zone
- **MPRIS Media Controller (`MprisModule.qml`)**: Shows currently playing media (Spotify, Firefox, mpv) with play/pause click and scroll track skipping.
- **󰌌 Keyboard Layout (`LanguageModule.qml`)**: Live keyboard layout indicator (e.g. US). Left-click cycles layout; right-click opens layout menu; middle-click opens layout installer.

### 3. Right Zone
- **Live Screen Recording Indicator (`RecordingModule.qml`)**:
  - Automatically appears when video screen recording (`wf-recorder`) is active with a pulsating red capsule and live duration counter (`󰻃 REC 00:15`).
  - **Left-Click**: Instantly stops recording, finalizes the video container, and triggers desktop save notification.
  - **Right-Click**: Toggles recording indicator visibility on/off.
  - **Middle-Click**: Opens the full Screen Capture & Recording menu.
- **Group Tray & Notifications (`TrayNotifGroup.qml`)**:
  - System tray for background application indicators.
  - Clipboard indicator: Left-click opens the searchable **Clipboard History** drawer (`quickshell/plugins/clipboard/`); right-click wipes history.
  - Notification center badge: Shows unread count badge. Left-click opens the **Notification Center** popup (`quickshell/plugins/notifications/`); right-click toggles Do-Not-Disturb (DND); middle-click clears notifications.
- **Group Status (`StatusGroup.qml` & Modular Modules `VolumeModule`, `BrightnessModule`, `WifiModule`, `BluetoothModule`, `BatteryModule`)**:
  - **PipeWire Audio**: Volume level and mute state. Hover tooltip displays output sink device name, volume/mute state, microphone input device name & volume, and PipeWire server. Left-click toggles mute; right-click opens the **Quickshell Audio Mixer** popup (`quickshell/plugins/volume/`) with device switching and per-app sliders; scroll adjusts volume.
  - **Screen Brightness**: Live display brightness percentage and adaptive icon (`󰃞`, `󰃟`, `󰃠`). Hover tooltip displays exact brightness percentage, hardware DDC/backlight control mode, and night light filter status. Left-click opens the **Quickshell Brightness & Night Light** popup (`quickshell/plugins/brightness/`); right-click toggles Night Light; scroll adjusts brightness (±5%).
  - **Wi-Fi**: Signal strength icon. Hover tooltip displays SSID, signal strength with RSSI dBm, assigned IPv4 address, security protocol, frequency band (5 GHz / 2.4 GHz), and network interface (`wlan0`). Left-click opens the native **Wi-Fi & Network Manager** popup (`quickshell/plugins/connectivity/`) with network scanning, connection, password prompts, and forget network options; right-click toggles Wi-Fi radio.
  - **Bluetooth**: Connection status. Hover tooltip displays connected device list with icons, names, and peripheral battery percentages, controller radio power status, and paired device count. Left-click opens the native **Bluetooth Manager** popup (`quickshell/plugins/connectivity/`) for pairing, connecting, and disconnecting devices; right-click toggles Bluetooth radio.
  - **Battery & Power Profiles**: Dynamic battery percentage and power profile color indicator. Hover tooltip displays state & charge percentage, active power profile, real-time power draw in Watts (`W`), battery health percentage, and estimated remaining runtime. Left-click opens the **Battery & Power Profile** popup (`quickshell/plugins/battery/`) to switch between Power Saver, Balanced, and Performance modes; right-click opens Btop task manager.
- **󰍛 System Hardware & Stats Chip (`StatsModule.qml`)**:
  - Displays a clean chip icon in the status bar.
  - **Left-Click**: Opens the glassmorphic **System Resources Dashboard** (`quickshell/plugins/sysinfo/`) with fast 800ms real-time metric updates, smooth progress bar animations, CPU %, RAM GB/%, Disk GB/%, and outside-click dismissal.
  - **Right-Click**: Directly opens **Btop** task monitor (`foot --app-id=btop -e btop`).
- **󰐥 Power Menu (`PowerModule.qml`)**: Left-click launches the glassmorphic **Quickshell Power & Session Menu** (Lock, Suspend, Logout, Reboot, Shutdown).
- ** Clock & Calendar (`ClockModule.qml`)**: 12h/24h digital clock with a rich interactive Catppuccin calendar tooltip. Right-click toggles format; scroll navigates months.

---

## 🔊 Sound & Audio Management Control Center (Quickshell Plugin)

The dotfiles include a dedicated **Audio Mixer & Sound Hub** (`~/.config/quickshell/plugins/volume/`):

- **Status Bar Trigger**: Right-clicking the sound icon on the top bar or pressing **`SUPER + SHIFT + A`** opens a glassmorphic popup anchored directly beneath the bar.
- **Device Selection Dropdowns**:
  - **Output Sinks Dropdown**: Instant switching between connected output devices (HDMI/DisplayPort, Headphones, Built-in Speakers, Bluetooth headsets).
  - **Input Sources Dropdown**: Instant switching between microphones (Internal Laptop Mic, Headset Mic, USB Microphones).
- **Smooth Range Sliders**:
  - **Master Output Volume**: Range slider supporting `0%` to `150%` (volume amplification boost beyond standard 100%) with live percentage feedback.
  - **Master Microphone Volume**: Range slider (`0% - 100%`) with gain indicator.
  - **Quick Volume Presets**: One-click preset pills: `[20%]`, `[50%]`, `[80%]`, `[100%]`, `[150% 🚀]`.
  - **Mute Controls**: Independent mute toggle buttons for output and microphone with active color badges.
- **Per-Application Audio Stream Mixers**:
  - Automatically discovers all running apps playing audio (e.g. Chromium, Spotify, Telegram, MPV, Discord).
  - Dedicated individual volume range sliders (`0% - 150%`) and per-app mute toggles.
- **Audio Tools & Server Recovery**:
  - **󰋋 Test Audio**: Plays stereo left/right audio channel test tones.
  - **🔄 Restart PipeWire**: Single-click restart and recovery of `pipewire`, `pipewire-pulse`, and `wireplumber` user services.
  - **🎛️ Terminal TUI**: Launches the interactive curses mixer in a floating Foot terminal.
- **Enhanced PipeWire & WirePlumber Audio Architecture**:
  - **Hardware Jack & Cable Presence Sense**: Audio utilities actively verify physical port connection availability via `pactl list cards`, hiding phantom/unplugged HDMI audio pipes and disconnected mic/headphone jacks.
  - **Clean Profile Routing (`52-alsa-routes.conf`)**: Enforces stable default priority for internal Speaker and microphone routing without duplicate node ghosting.
  - **Software DSP Mixing (`api.alsa.soft-mixer = true`)**: Configured in `~/.config/wireplumber/wireplumber.conf.d/51-alsa-soft-mixer.conf` to force software-level digital PCM attenuation for HDMI / DisplayPort monitors and external speakers lacking physical ALSA hardware mixer registers.

---

## ☀️ Display Brightness & External Monitor Manager (Quickshell Plugin)

The dotfiles include a dedicated **Display & Brightness Control Center** (`~/.config/quickshell/plugins/brightness/`):

- **Status Bar Trigger**: Left-clicking the brightness indicator or pressing **`SUPER + SHIFT + B`** opens the glassmorphic Display Control Center.
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

---

## 🌅 Hyprsunset & Hypridle Display Management Suite

The dotfiles include a dedicated **Display Power, Monitor Turn-Off & Night Light Control Suite** ([`sunset_idle_manager.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/sunset_idle_manager.py)):

- **Application Menu Integration**: Available directly in the app launcher as **Night Light & Idle Manager** (`hyprsunset-hypridle.desktop`).
- **Hyprsunset / Blue Light Engine**:
  - Continuous color temperature slider (1000K – 6500K) with instant preview.
  - Quick temperature preset buttons:
    - ☀️ **Daylight** (`6500K` - Normal display colors)
    - 🍵 **Soft Warm** (`5000K` - Gentle eye relaxation)
    - 🌙 **Night Light** (`3800K` - Evening eye comfort)
    - 🕯️ **Candlelight** (`2500K` - Late-night amber tint)
    - 🔴 **Deep Ember** (`1800K` - Pitch-dark bedtime mode)
  - Automatic state persistence across desktop reboots.
- **Night Light Scheduling & Solar Location Engine**:
  - **⏰ Custom Time Schedule**: Set fixed daily turn-on and turn-off hours (e.g. `20:00` to `06:30`).
  - **📍 Solar Sunset-to-Sunrise (Location)**: Automatically turns Night Light on at sunset and off at sunrise based on real geographic coordinates.
  - **🛰️ 1-Click IP Geolocation**: Auto-detects your city coordinates with a single click in the GUI or via `--auto-location`.
  - **🔄 Background Daemon**: Evaluates scheduling rules every minute and transitions color temperatures smoothly without user intervention.
- **Hypridle & Display Power Engine**:
  - **Configurable Monitor Turn-Off Timeout (DPMS)**: Configure idle monitor power-off timeout directly from the GUI or quick menu (`1m`, `2m`, `2.5m`, `5m`, `10m`, `15m`, `30m`, `1h`, `Never / Disabled`, or custom seconds).
  - **Idle Lock, Dimming & Suspend Synchronization**: Configure and sync screen dimming (`brightnessctl`), screen lock (`hyprlock`), and system sleep timeouts directly into `~/.config/hypr/hypridle.conf` with automatic daemon reloading.
  - **Instant Display Turn-Off**: Power down display panels immediately (`hyprctl dispatch dpms off`) — wake up instantly on mouse movement or keyboard key press.
  - **☕ Caffeine / Idle Inhibit Mode**: 1-click toggle to prevent monitors from turning off, dimming, or sleeping during movies, presentations, or long compiles.
- **Access Modes**:
  - **GTK3 Control Center GUI**: Press **`SUPER + ALT + I`** or launch from application menu.
  - **Fuzzel / Wofi Interactive Menu**: Press **`SUPER + CTRL + I`** (Idle & Power) or **`SUPER + CTRL + N`** (Night Light).
  - **Quick Toggle**: Press **`SUPER + ALT + N`** to instantly toggle Night Light on/off.
  - **CLI Commands**:
    ```bash
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --gui                      # Launch GTK3 Control Center
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --menu                     # Launch Fuzzel/Wofi interactive menu
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --sunset-toggle            # Toggle Night Light On/Off
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --set-temp 3800            # Set Night Light temperature to 3800K
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --schedule-mode location   # Enable Solar Sunset/Sunrise auto-schedule
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --auto-location            # Auto-detect coordinates via IP
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --schedule-mode custom --schedule-on 21:00 --schedule-off 06:30
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --daemon                   # Run background scheduler daemon
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --dpms-off                 # Turn off displays immediately
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --set-dpms-timeout 300     # Set monitor turn-off to 5 minutes
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --caffeine-toggle          # Toggle Caffeine mode
    python3 ~/.config/hypr/scripts/sunset_idle_manager.py --status                   # Print status JSON
    ```

---

## 🖥️ System Hardware & Stats Dashboard (Quickshell Plugin)

The dotfiles include a dedicated **System Hardware & Resources** dashboard (`~/.config/quickshell/plugins/sysinfo/`):

- **Status Bar Chip (`󰍛`)**: A minimal and responsive chip indicator on the right side of the status bar.
- **Left-Click Dashboard Popup**: Opens a glassmorphic popup styled with Catppuccin Mocha colors:
  - **Ultra-Fast 800ms Update Interval**: Polling and metric sampling occurs every 800ms for smooth, real-time live performance tracking.
  - **Accurate Instant CPU Metric**: Direct kernel `/proc/stat` delta sampling providing real-time CPU usage percentage without external library latency or 0.0% initialization lag.
  - **Memory & Storage Metrics**: Real-time RAM usage in GiB and percentage alongside root filesystem (`/`) capacity and utilization.
  - **Smooth Fluid Progress Bars**: Hardware bars feature animated width interpolation (`NumberAnimation`) and dynamic color transitions based on load thresholds.
  - **Btop Terminal Launcher**: 1-click button (and status bar right-click trigger) to immediately open **Btop** in Foot terminal.
  - **Outside-Click & Escape Dismissal**: Easy keyboard and mouse dismissal.
- **Right-Click Action**: Instantly launches the **Btop** interactive terminal monitor (`foot --app-id=btop -e btop`).

---

## 🔋 Power Management & Battery Profiles (Quickshell Plugin)

The dotfiles include a dedicated **Power Profile & Battery Management** system (`~/.config/quickshell/plugins/battery/`):

- **Dynamic Icon Coloring**: The battery icon dynamically changes color based on the active power profile:
  - **🌱 Power Saver**: **Green** (`#a6e3a1`) — Reduces CPU clocks and limits background power draw.
  - **⚖ Balanced**: **Blue** (`#89b4fa`) — Standard dynamic balance between speed and battery life.
  - **🚀 Performance**: **Peach / Red** (`#fab387` / `#f38ba8`) — Maximum CPU clock speeds and responsiveness for heavy workloads.
- **Interactive Selector Popup**: **Clicking** the battery indicator opens a glassmorphic popup:
  - High-contrast power profile cards for instant 1-click switching over DBus (`powerprofilesctl`).
  - Live power consumption in Watts (`power_now`), battery health percentage, and charging state.
  - Instant outside-click backdrop dismissal and `Escape` key handling.

---

## 🔔 Notification Center & Mako Daemon (Quickshell Plugin)

The dotfiles include a full-featured, glassmorphic **Notification Center & History Drawer** (`~/.config/quickshell/plugins/notifications/`) backed by **Mako**:

- **Status Bar Integration (`TrayNotifGroup.qml`)**:
  - **Dynamic Unread Badge**: Live unread count badge displaying active and historical notifications.
  - **Left-Click / `SUPER + N`**: Opens the glassmorphic Notification Center drawer.
  - **Middle-Click**: Toggles **Do-Not-Disturb (DND)** mode on/off systemwide.
- **Extended 500-Entry History Buffer**:
  - Configured with `max-history=500` in [`~/.config/mako/config`](file:///home/kunal/.config/mako/config) to preserve up to **500** notifications across your entire desktop session.
  - Automatically sanitizes large message payloads and command bodies for high-performance rendering.
- **Interactive Controls & Actions**:
  - **Live Search & Filter**: Real-time fuzzy filtering of notifications by application name, title summary, or body text.
  - **1-Click Invoke Action**: Clicking any notification card invokes its primary action (e.g. opens link, views file, focuses application).
  - **Individual Dismissal**: Per-card close (`󰅖`) button with instant optimistic UI removal and persistent state caching.
  - **Protected Clear All**: Dedicated "Clear All" trash icon with a glassmorphic confirmation dialog to prevent accidental deletion.
  - **Do-Not-Disturb (DND) Switch**: In-drawer toggle button to silence notifications during presentations or focus sessions.
- **Keyboard Shortcuts & CLI Commands**:
  - **`SUPER + N`**: Open / toggle the Notification Center drawer.
  - **`Escape`**: Close notification drawer or dismiss the Clear All confirmation dialog.
  - **`Up / Down` & `Enter`**: Keyboard navigation through notification cards.
  - **CLI Controls**:
    ```bash
    makoctl list -j                          # List active visible notifications
    makoctl history -j                       # List historical notifications
    makoctl dismiss -a                       # Dismiss all visible notifications
    makoctl mode -t dnd                      # Toggle Do-Not-Disturb (DND) mode
    makoctl reload                           # Reload Mako daemon configuration
    python3 ~/.config/quickshell/plugins/notifications/notification_helper.py list
    ```

---

## 🗂️ Quickshell Workspace Viewer & Live Window Snapshot Previews

The dotfiles include a dedicated **Workspace Viewer HUD & Workspace Hover Preview** plugin (`~/.config/quickshell/plugins/workspace_viewer/`):

- **Interactive Fullscreen Overlay (`SUPER + Tab`)**:
  - Displays all active workspaces across connected monitors in a visual grid layout.
  - Multi-monitor coordinate normalization ensures preview blocks align accurately without overflow.
  - Interactive window cards show running application icons, window titles, and live snapshot previews.
  - Click any window card or workspace block to instantly switch focus and jump to that workspace.
- **Top Bar Workspace Hover Previews (`WorkspacePreviewPopup.qml`)**:
  - Hovering over any workspace pill on the top bar displays a floating glassmorphic preview popup showing all windows open on that workspace with their positions and thumbnails.
- **Live Snapshot Capture Daemon (`window_preview_capture.py`)**:
  - Asynchronously captures window snapshots via `grim` into `~/.cache/quickshell/window_previews/`.
  - Automatically updates thumbnails when active windows change or focus shifts without freezing the UI.

---

## 🧩 User Custom Plugins Discovery Engine

The dotfiles include an **automated plugin discovery engine** for Quickshell at [`~/.config/quickshell/custom_plugins/`](file:///home/kunal/.dotfiles/.config/quickshell/custom_plugins):

- **Zero Code Modification Required**: Users can drop any custom plugin directory with a `manifest.json` into `custom_plugins/` without modifying any repository files or QML code.
- **Untracked by Git**: The `custom_plugins/` directory is ignored by Git, ensuring user plugins remain intact across dotfile updates.
- **Dynamic Bar Placement & Window Loading**: Declaring `"position": "left" | "center" | "right"` in `manifest.json` automatically injects the widget into that topbar zone, while popup windows and background services are loaded on startup.
- **Built-in Guide**: Complete specification and boilerplate templates are provided in [`custom_plugins/README.md`](file:///home/kunal/.dotfiles/.config/quickshell/custom_plugins/README.md).

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

- **Dynamic Color Variables & Quickshell Theming Architecture**:
  - **Quickshell Dynamic Theme Singleton (`Theme.qml`)**: The status bar and native plugins consume dynamic colors synchronized directly with the active palette. User-customized palette overrides are loaded from `~/.config/quickshell/colors.json` (untracked in git, preserving your personal desktop aesthetics).
  - **Hyprland**: Border colors and shadows consume variables from [`modules/theme.lua`](file:///home/kunal/.dotfiles/.config/hypr/modules/theme.lua).
  - **Dolphin, Kate & KWrite**: KDE color schemes ([`kdeglobals`](file:///home/kunal/.dotfiles/.config/kdeglobals)), editor syntax highlighting themes ([`org.kde.syntax-highlighting`](file:///home/kunal/.local/share/org.kde.syntax-highlighting/themes)), and UI configs ([`katerc`](file:///home/kunal/.config/katerc), [`kwriterc`](file:///home/kunal/.config/kwriterc)) synchronized live across all 19 themes.
  - **Starship, Zellij, Btop, Lazygit & Swappy**: Palettes and accents dynamically synchronized.
  - **Systemwide Light / Dark Mode & Portal Integration**: Sets `org.gnome.desktop.interface color-scheme` ('prefer-dark' / 'prefer-light') via GSettings and DConf, configures GTK 3.0 & GTK 4.0 `settings.ini`, and triggers XDG Desktop Portal updates so Web Browsers (Firefox, Chrome), Electron apps (VS Code, Discord, Obsidian), Libadwaita/GTK4 apps, Flatpaks, and Qt apps instantly switch between light and dark modes.
  - **Extensibility**: Add new themes at any time by dropping a single `.json` file into `~/.config/theme/<name>.json`.



- **Usage**:
  - **Graphical Menu**: Press **`SUPER + T`** to open the interactive Fuzzel/Wofi theme picker with active indicator.
  - **Theme Manager GUI**: Press **`SUPER + ALT + T`** to open the GTK3 Theme Manager & Studio.
  - **Cycle Themes**: Press **`SUPER + CTRL + T`** to instantly cycle forward through all available themes.
  - **Terminal CLI**:
    ```bash
    python3 ~/.config/hypr/scripts/theme_switcher.py --list
    python3 ~/.config/hypr/scripts/theme_switcher.py --set tokyo-night
    python3 ~/.config/hypr/scripts/theme_switcher.py --dark         # Switch to dark mode systemwide
    python3 ~/.config/hypr/scripts/theme_switcher.py --light        # Switch to light mode systemwide
    python3 ~/.config/hypr/scripts/theme_switcher.py --toggle-mode  # Toggle between dark & light systemwide
    python3 ~/.config/hypr/scripts/theme_switcher.py --next
    ```

---

## 🌐 Screen OCR Text Grabber, Multi-Language Hub & QR Scanner

The dotfiles include a comprehensive, native Wayland suite for extracting text and reading 2D codes from any region of the screen:

### 1. Tesseract OCR Multi-Language Hub ([`ocr_language_manager.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/ocr_language_manager.py))
- **Simultaneous Multi-Language Recognition**: Select and combine multiple OCR recognition languages at once (e.g. `English (eng) + Marathi (mar) + Hindi (hin)` or `English + Japanese`).
- **Sudo-Free Model Downloads**: Browse and install from a catalog of 80+ worldwide languages (Indic, East Asian, European, Cyrillic, Middle Eastern, math equations). Downloads `.traineddata` files directly into `~/.local/share/tessdata` without requiring root/sudo privileges.
- **Interactive Multi-Select GUI (GTK3)**: High-contrast Catppuccin themed manager with multi-select checkboxes, category filter pills, real-time search across scripts (*मराठी*, *हिन्दी*, *日本語*), instant solo selection, and model removal.
- **Fast Fuzzel Dmenu Switcher**: Press **`SUPER + CTRL + O`** for quick keyboard-driven language toggling on the fly.
- **Usage & Shortcuts**:
  - **`SUPER + SHIFT + T`**: Drag cursor with mouse to grab text from screen area (auto-copies to clipboard).
  - **`SUPER + ALT + O`**: Open OCR Language Hub GUI.
  - **`SUPER + CTRL + O`**: Open interactive Fuzzel/Wofi OCR language toggle menu.
  - **CLI Commands**:
    ```bash
    python3 ~/.config/hypr/scripts/ocr_language_manager.py --list          # View installed models & active combo
    python3 ~/.config/hypr/scripts/ocr_language_manager.py --set "eng+mar" # Set simultaneous recognition languages
    python3 ~/.config/hypr/scripts/ocr_language_manager.py --install hin   # Download and activate Hindi model
    python3 ~/.config/hypr/scripts/ocr_grab.py --lang "eng+mar"           # Trigger OCR with specific language combo
    ```

### 2. Screen QR Code & 2D Barcode Scanner ([`qr_reader.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/qr_reader.py))
- **Screen Area & Window Capture**: Select any screen region with `slurp` + `grim` to decode QR codes, DataMatrix, and 2D barcodes via `zbar` / Python fallbacks.
- **Clipboard & Actionable Notifications**: Decoded content is automatically copied to the Wayland clipboard (`wl-copy`), with interactive desktop notifications featuring a 1-click **"Open Link"** button for URLs.
- **Usage & Shortcuts**:
  - **`SUPER + ALT + Q`**: Drag cursor to scan any QR code on screen.
  - **`SUPER + Print`**: Screen Capture Dashboard -> select **"📱 Read QR Code from Screen"**.
### 3. Screen Recording & Live Quickshell Indicator Hub ([`screen_capture.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/screen_capture.py))
- **Live Quickshell Recording Indicator**: When screen recording begins, a glowing red capsule (`󰻃 REC 00:12`) appears in the top status bar showing the real-time recording timer.
- **1-Click Stop**: Left-clicking the recording capsule immediately stops the recording, finalizes the MP4/MKV video container, and sends a notification with instant Play / Folder actions.
- **Configurable Visibility**: Toggle the recording indicator on or off at any time:
  - **Fuzzel/Wofi GUI**: Press **`SUPER + Print`** and select **`⚙️  Recording Indicator Icon: [Enabled/Disabled]`**.
  - **Right-Click**: Right-clicking the recording capsule toggles its visibility.
  - **CLI Command**: `python3 ~/.config/hypr/scripts/screen_capture.py --toggle-indicator` or `screen_capture.py --indicator on|off`.
- **Usage & Shortcuts**:
  - **`SUPER + ALT + R`**: Toggle video screen recording for selected region.
  - **`SUPER + CTRL + R`**: Stop active video screen recording cleanly.
  - **`SUPER + Print`**: Open interactive capture & recording hub.
  - **CLI Commands**:
    ```bash
    python3 ~/.config/hypr/scripts/screen_capture.py record --area            # Record region (default)
    python3 ~/.config/hypr/scripts/screen_capture.py record --full --mic      # Full screen + microphone
    python3 ~/.config/hypr/scripts/screen_capture.py record --desktop         # Region + desktop audio
    python3 ~/.config/hypr/scripts/screen_capture.py stop                     # Stop recording
    python3 ~/.config/hypr/scripts/screen_capture.py --toggle-indicator       # Toggle recording icon
    ```

---

## ⚡ Dynamic Keybindings Viewer & Cheat Sheet

The repository includes an intelligent dynamic shortcut viewer ([`keybinds_viewer.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/keybinds_viewer.py)) that parses doc-comments directly from [`keybinds.lua`](file:///home/kunal/.dotfiles/.config/hypr/modules/keybinds.lua):

- **Desktop GUI**: Press **`SUPER + /`**, **`SUPER + ?`**, or **`SUPER + F1`** to open the interactive **Quickshell** dynamic keybindings viewer with category filters and search. Selecting any shortcut automatically copies the key combination to your clipboard.
- **Terminal CLI**: Run `python3 ~/.config/hypr/scripts/keybinds_viewer.py --cli` for categorized, ANSI-colored tables.
- **Export Formats**: Supports `--json` and `--markdown` for automated documentation generation.

---

## 🚀 Application Shortcut & Desktop Entry Creator

The dotfiles include a dedicated GUI and CLI utility ([`app_shortcut_creator.py`](file:///home/kunal/.dotfiles/.config/hypr/scripts/app_shortcut_creator.py)) to easily create, edit, test, and manage standard `.desktop` application launchers in `~/.local/share/applications/`:

- **Interactive GTK GUI (`SUPER + ALT + S`)**:
  - Full-featured form to configure Application Name, Executable / Command, Arguments, Working Directory, Categories, and Terminal requirements.
  - Native file and directory browsing with `Gtk.FileChooserNative` (preventing modal hangs or portal crashes).
  - Built-in system icon picker and custom image loader.
  - Live `.desktop` file syntax preview and instant launch test button.
  - Manage and edit existing custom application shortcuts with one click.
- **Terminal CLI Support**:
  ```bash
  python3 ~/.config/hypr/scripts/app_shortcut_creator.py --gui                     # Launch GTK3 shortcut creator GUI
  python3 ~/.config/hypr/scripts/app_shortcut_creator.py --list                    # List all custom .desktop entries
  python3 ~/.config/hypr/scripts/app_shortcut_creator.py --create "My App" -e "/usr/bin/myapp" -i "terminal"
  python3 ~/.config/hypr/scripts/app_shortcut_creator.py --delete "custom-app.desktop"
  ```

---

## ⌨️ Complete Keyboard Shortcuts Reference

### 🖥️ Core Applications & Essential Controls
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + Return` | **Open Terminal** | Launch Foot Wayland-native terminal emulator |
| `SUPER + grave (~)` | **Dropdown Terminal** | Fast floating scratchpad terminal (`dropdown-terminal`) |
| `SUPER + R` / `SUPER + Space` | **App Launcher** | Open **Quickshell** application menu (with category tabs & search) |
| `SUPER + B` | **Web Browser** | Launch default web browser (Firefox) |
| `SUPER + E` | **Dolphin File Manager** | Launch KDE GUI file manager |
| `SUPER + SHIFT + E` | **Yazi File Manager** | Launch terminal file manager in Foot |
| `SUPER + C` / `SUPER + SHIFT + Q` / `ALT + F4` | **Close Window** | Close active focused window |
| `SUPER + F` | **Toggle Fullscreen** | Toggle active window between normal and true fullscreen mode |
| `SUPER + V` | **Toggle Floating** | Switch active window between tiled and floating mode |
| `SUPER + P` | **Toggle Pseudo Tiling** | Toggle pseudo-tile mode on active window |
| `SUPER + J` | **Toggle Layout Split** | Toggle horizontal/vertical split orientation (Dwindle layout) |
| `SUPER + L` / `SUPER + ALT + L` | **Lock Screen** | Immediately trigger `hyprlock` lockscreen |
| `SUPER + Escape` / `SUPER + M` | **Power & Session Menu** | Open **Quickshell** session modal (Lock, Logout, Suspend, Reboot, Shutdown) |
| `SUPER + SHIFT + W` | **Toggle Status Bar** | Toggle Quickshell status bar on/off with state persistence |
| `SUPER + /` / `SUPER + ?` / `SUPER + F1` | **Shortcut Cheat Sheet** | Open interactive **Quickshell** dynamic keybindings viewer |

---

### 🗂️ Workspaces & Window Navigation
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + Left / Right / Up / Down` | **Focus Window** | Move focus directionally between windows |
| `ALT + Tab` | **Cycle Focus** | Cycle focus forward to next window |
| `SUPER + Tab` | **Workspace Overview** | Open interactive **Quickshell** multi-workspace app viewer & layout HUD |
| `SUPER + [1-9, 0]` | **Switch Workspace** | Jump directly to workspace 1 through 10 |
| `SUPER + SHIFT + [1-9, 0]` | **Move Window to Workspace** | Move focused window to workspace 1 through 10 |
| `SUPER + S` | **Toggle Special Workspace** | Toggle magic scratchpad workspace |
| `SUPER + SHIFT + S` | **Move to Special Workspace** | Send focused window into magic scratchpad |
| `SUPER + Mouse Scroll Down` | **Next Workspace** | Switch to next workspace |
| `SUPER + Mouse Scroll Up` | **Previous Workspace** | Switch to previous workspace |
| `SUPER + Left Mouse Drag` | **Move Window** | Drag and move floating or tiled window |
| `SUPER + Right Mouse Drag` | **Resize Window** | Drag to resize window bounds |

---

### 📐 Window Resizing & Screen Scaling (`scale_window.py` & `resolution_menu.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + CTRL + =` / `+` / `KP_Add` | **Scale Window Up** | Increase active window size by +40px with live dimension OSD |
| `SUPER + CTRL + -` / `KP_Subtract` | **Scale Window Down** | Decrease active window size by -40px with live dimension OSD |
| `SUPER + CTRL + Right / L` | **Resize Width Right** | Grow window horizontally to the right (+40px) |
| `SUPER + CTRL + Left / H` | **Resize Width Left** | Shrink window horizontally from the left (-40px) |
| `SUPER + CTRL + Up / K` | **Resize Height Up** | Shrink window vertically from the top (-40px) |
| `SUPER + CTRL + Down / J` | **Resize Height Down** | Grow window vertically to the bottom (+40px) |
| `SUPER + CTRL + 0` | **Show Window Size** | Display active window dimensions & screen coverage percentage OSD |
| `SUPER + SHIFT + R` / `SUPER + SHIFT + D` | **Resolution & Scaling Menu** | Interactive menu to set monitor resolution and DPI scaling |
| `SUPER + ALT + =` / `+` | **Display Scale Up** | Increment display scaling (+0.1) |
| `SUPER + ALT + -` | **Display Scale Down** | Decrement display scaling (-0.1) |
| `SUPER + ALT + 0` | **Show Display Scale** | Display active monitor resolution & scale factor OSD |
| `SUPER + ALT + 1` to `5` | **Direct Scale Presets** | Set display scale: `1`=1.0x, `2`=1.25x, `3`=1.5x, `4`=1.75x, `5`=2.0x |
| `SUPER + ALT + BackSpace` | **Reset Display Scale** | Instantly reset display scale to default 1.0x (100%) |

---

### ⚡ Productivity, Development & System Utilities
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + G` | **Lazygit Overlay** | Open floating full-featured Git TUI |
| `SUPER + D` | **Lazydocker Overlay** | Open floating Docker/Podman container manager TUI |
| `SUPER + SHIFT + Z` | **Zellij Workspace** | Open floating terminal multiplexer session |
| `SUPER + SHIFT + P` | **Hyprpicker** | Pick color from screen, copy hex code to clipboard & trigger notification |
| `SUPER + ALT + P` | **Quickshell Plugin Manager** | Open native Plugin Manager GUI & Store catalog modal |
| `SUPER + T` | **Theme Switcher Menu** | Open interactive **Fuzzel/Wofi** theme selector (19 curated themes, live reload) |
| `SUPER + ALT + T` | **Theme Manager & Studio GUI** | Launch graphical **GTK3** theme & palette manager with live card previews |
| `SUPER + CTRL + T` | **Cycle Theme** | Instantly cycle to the next color palette in the theme registry |
| `SUPER + SHIFT + T` | **Screen OCR** | Select region with mouse, extract text via Tesseract & copy to clipboard |
| `SUPER + ALT + O` | **OCR Language Manager GUI** | Launch graphical GTK3 language downloader & multi-language manager |
| `SUPER + CTRL + O` | **OCR Language Selector Menu** | Fast interactive Fuzzel/Wofi OCR language switcher |
| `SUPER + ALT + Q` | **Screen QR Reader** | Select region with mouse, decode QR/2D barcodes to clipboard & open URLs |
| `SUPER + ALT + N` | **Toggle Night Light** | Toggle warm blue-light eye comfort filter (Hyprsunset) |
| `SUPER + CTRL + N` | **Night Light Menu** | Interactive color temperature selector (6500K, 5000K, 3800K, 2500K, 1800K) |
| `SUPER + ALT + I` | **Idle & Display Power GUI** | Launch GTK3 Night Light & Display Idle Power Manager |
| `SUPER + CTRL + I` | **Idle & Power Menu** | Quick menu for monitor turn-off timeouts, DPMS off, and Caffeine mode |
| `SUPER + =` / `SUPER + ALT + C` | **Quick Calculator** | Interactive math expression evaluator via **Quickshell** Calc plugin |
| `SUPER + .` (period) | **Emoji Picker** | Searchable emoji catalog with clipboard copy via **Quickshell** Emoji plugin |
| `SUPER + ALT + S` | **App Shortcut Creator** | Launch interactive desktop shortcut (.desktop) creator & manager GUI |
| `SUPER + W` | **Random Wallpaper** | Cycle to a random wallpaper from `~/Wallpaper` |
| `SUPER + ALT + W` | **Wallpaper Selector Menu** | Interactive graphical wallpaper selector with live preview |
| `SUPER + ALT + Space` | **Next Keyboard Layout** | Cycle to next active keyboard layout |
| `SUPER + SHIFT + K` | **Keyboard Layout Menu** | Open interactive selector for active keyboard layouts |
| `SUPER + ALT + K` | **Add Keyboard Layout** | Search and add regional layout variants (including Indian languages) |

---

### 🔔 Notifications & Clipboard History
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + N` | **Notifications Center** | Open notification history and management center (**Quickshell**) |
| `SUPER + SHIFT + N` | **Toggle DND** | Toggle Do-Not-Disturb notification silencing mode (`󰂛`) |
| `SUPER + SHIFT + V` / `ALT + V` / `SHIFT + C` | **Clipboard Browser** | Open searchable clipboard history with images and snippets (**Quickshell**) |
| `SUPER + ALT + X` / `SUPER + SHIFT + X` | **Toggle Private Mode** | Toggle clipboard Private Mode / pause recording (`󰈉`) |
| `SUPER + ALT + D` | **Clipboard Cleaner** | Open clipboard history with confirmation dialog to clear cache |

---

### 📂 Floating File Picker & Uploader Modal (**Quickshell Plugin & XDG Portal**)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `SUPER + SHIFT + F` | **File Picker Modal** | Open floating file selector/uploader modal (**Quickshell Plugin**) |
| `SUPER + ALT + F` | **Image Grid Mode** | Open file selector directly in thumbnail grid preview mode |
| `Ctrl + H` *(inside modal)* | **Toggle Hidden Files** | Show or hide dotfiles and hidden folders |
| `Ctrl + P` *(inside modal)* | **Toggle Preview Panel** | Expand or collapse right-side live image/code/metadata preview |
| `Ctrl + D` *(inside modal)* | **Bookmark Folder** | Add current directory to sidebar Bookmarks |
| `Ctrl + L` *(inside modal)* | **Edit Path Bar** | Focus editable breadcrumb bar for direct path input |

---

### 🔊 Audio & Media Controls (`volume_control.py` & `playerctl`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `XF86AudioRaiseVolume` | **Volume Up (+5%)** | Increase output volume with visual OSD |
| `XF86AudioLowerVolume` | **Volume Down (-5%)** | Decrease output volume with visual OSD |
| `XF86AudioMute` | **Toggle Mute** | Mute / unmute speaker audio output |
| `XF86AudioMicMute` | **Toggle Mic Mute** | Mute / unmute microphone input |
| `SHIFT + XF86AudioRaiseVolume` | **Mic Volume Up** | Increase microphone input gain (+5%) |
| `SHIFT + XF86AudioLowerVolume` | **Mic Volume Down** | Decrease microphone input gain (-5%) |
| `SUPER + SHIFT + A` / `SUPER + ALT + A` | **Audio Control Center** | Open **Quickshell** Sound Control Center & audio sink/source device switcher |
| `XF86AudioPlay` / `XF86AudioPause` | **Play / Pause** | Toggle media playback (Spotify, browser, playerctl) |
| `XF86AudioNext` | **Next Track** | Skip to next track in active media player |
| `XF86AudioPrev` | **Previous Track** | Skip to previous track in active media player |

---

### ☀️ Brightness, Network & Connectivity Controls
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `XF86MonBrightnessUp` | **Brightness Up (+5%)** | Increase laptop panel backlight with visual OSD |
| `XF86MonBrightnessDown` | **Brightness Down (-5%)** | Decrease laptop panel backlight with visual OSD |
| `SHIFT + XF86MonBrightnessUp` / `SUPER + Up` | **External DDC Up** | Increase external monitor brightness via DDC/CI (`ddcutil`) |
| `SHIFT + XF86MonBrightnessDown` / `SUPER + Down` | **External DDC Down** | Decrease external monitor brightness via DDC/CI (`ddcutil`) |
| `SUPER + SHIFT + B` / `SUPER + ALT + B` | **Display Control Center** | Open **Quickshell** Display Brightness & Contrast Control Center |
| `SUPER + CTRL + W` | **Wi-Fi Network Manager** | Open native **Quickshell** Wi-Fi network scanner and connection manager |
| `SUPER + CTRL + B` | **Bluetooth Manager** | Open native **Quickshell** Bluetooth device manager |

---

### 📸 Screenshots & Screen Recording (`screen_capture.py`)
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Print` | **Area Screenshot** | Select screen region with mouse, copy image to clipboard & save file |
| `SHIFT + Print` | **Full Screen Screenshot** | Capture all displays immediately to clipboard and file |
| `ALT + Print` | **Active Window Screenshot** | Capture only the currently focused window |
| `CTRL + Print` | **Annotate Screenshot** | Select region and open in **Swappy** editor to draw arrows, crop, or blur |
| `SUPER + Print` | **Capture Hub** | Open interactive capture dashboard with timer and area options |
| `SUPER + ALT + R` | **Toggle Screen Recording** | Start / stop video recording with `wf-recorder` for selected region |
| `SUPER + CTRL + R` | **Stop Screen Recording** | Stop active video recording cleanly and save MP4/MKV container |

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

### 🚀 Starship Prompt & Shell Integration (`~/.config/starship.toml`)

- **Cross-Shell Prompting**: High-performance prompt supporting Bash, Zsh, and Fish with Git branch/status, execution time (`cmd_duration`), language versions (Rust, Go, Python, Node), and OS iconography.
- **Dynamic Theme Palette Sync**: Synced across 19 desktop themes via `theme_switcher.py`.
- **Advanced Features**:
  - **Continuation Prompt (`continuation_prompt`)**: Displays `▶▶ ` on multi-line and unclosed statements.
  - **Dynamic Terminal Window Title**: `set_win_title` hook via `starship_precmd_user_func` dynamically updates terminal tabs with your current working directory.
  - **Claude Code Statusline**: Pre-configured statusline profile (`starship statusline claude-code`) featuring active model display, visual context window gauge (`▰▰▰▱▱▱`), and token cost tracking.

---

## 🎨 Modern Left-Sidebar SDDM Theme & Hyprlock

A sleek, modern split-screen design layout unifying both the **SDDM Display Manager** login screen and the **Hyprlock (`hyprlock.conf`)** lock screen with a full-height left frosted-glass sidebar and un-obscured right background artwork.

### ✨ SDDM Theme Highlights
- **Left Frosted Sidebar**: Full-height translucent dark sidebar (`rgba(20, 22, 33, 0.82)`) on the left side (~36% width) with a subtle vertical dividing border.
- **Top Greeting & Live Clock**: Bold `"Welcome!"` greeting, large digital clock (`HH:mm`), and formatted date (`Monday, d of MMMM`).
- **Username Input**: Pill-outlined input container with a dark user silhouette badge on the left, auto-filled with the current user and supporting multi-user dropdown switching.
- **Password Input**: Matching pill-outlined container with dot masking, Caps Lock warning banner, and error shake animation on failed authentication.
- **Show Password Checkbox & Toggle**: Interactive checkbox and eye icon toggle to reveal or hide password characters with interactive hover tooltips.
- **Log In Button**: Prominent solid pill button (`#ffffff` / `#e0def4`) with interactive hover and click feedback.
- **Session Selector**: Clean `"Session: <SessionName>"` dropdown to easily select between Wayland and X11 sessions (e.g. Hyprland).
- **Power Menu & Confirmation**: Pinned at the bottom with **Suspend**, **Reboot**, and **Shutdown** actions featuring icons, text labels, interactive hover tooltips ("Suspend System", "Restart System", "Shut Down System"), and safety confirmation modals.

### 🧪 Live Preview & SDDM Deployment
```bash
# Preview SDDM theme in test mode without logging out:
~/.dotfiles/sddm/test-theme.sh

# Or directly with sddm-greeter-qt6 / qml6:
sddm-greeter-qt6 --test-mode --theme ~/.dotfiles/sddm/themes/catppuccin-mocha
qml6 ~/.dotfiles/sddm/themes/catppuccin-mocha/Main.qml

# Install and activate theme systemwide in /usr/share/sddm/themes/:
~/.dotfiles/sddm/scripts/install-theme.sh
```

### ⚙️ Theme Customization (`sddm/themes/catppuccin-mocha/theme.conf`)
Modify `~/.dotfiles/sddm/themes/catppuccin-mocha/theme.conf` to customize:
- `Background`: Path to custom wallpaper (defaults to `assets/background.jpg`)
- `FontFamily`: Preferred system font (defaults to `JetBrainsMono Nerd Font`)
- `ClockFormat` / `DateFormat`: Time and date layout formats
- `AccentColor`: Primary accent hex color (`#cba6f7`)
- `ShowSessions` / `ShowPowerButtons` / `ShowGreeting`: Toggle UI component visibility

---

## 🔒 Hyprlock Screen (`~/.config/hypr/hyprlock.conf`)

Hyprland's screen locker is styled with the exact same left-sidebar aesthetic:
- **Left Frosted Sidebar**: Semi-transparent rectangular panel (`rgba(20, 22, 33, 0.82)`) extending full height on the left.
- **Welcome & Clock Widgets**: Top `"Welcome!"` greeting with large digital clock (`60px`) and full date.
- **User & Password Field**: User icon label with a sleek pill-outlined password input field.
- **Power Status Hints**: Bottom action hints for Suspend, Reboot, and Shutdown.
- **Lockscreen Shortcut**: Press **`SUPER + L`** or **`SUPER + ALT + L`** to lock the session.

---

## 🔄 Dotfiles Sync & User Config Isolation (`scripts/dotfiles-push.sh`)

When developing on or tweaking your dotfiles, local personal preferences (such as dynamic active desktop theme colors, custom idle timeouts, active wallpaper assignments, or keyboard layouts) are automatically protected using Git's **`skip-worktree`** mechanism. This ensures that personal machine runtime state never dirties `git status` or conflicts with git pulls.

### 🚀 Using `scripts/dotfiles-push.sh`

A dedicated helper script is provided at `~/.dotfiles/scripts/dotfiles-push.sh`:

```bash
# Push dotfiles changes to remote (automatically syncs theme and enforces skip-worktree)
~/.dotfiles/scripts/dotfiles-push.sh

# Check the skip-worktree protection status of all user configuration files
~/.dotfiles/scripts/dotfiles-push.sh --status

# Explicitly isolate all user configuration files (clean working tree)
~/.dotfiles/scripts/dotfiles-push.sh --skip

# Temporarily un-skip files if you intend to commit a core template change
~/.dotfiles/scripts/dotfiles-push.sh --unskip
```

### 🛡️ Protected User Configuration Files
- **Desktop Themes**: `.config/hypr/theme.conf`, `theme_vars.lua`, `.config/foot/theme.ini`, `.config/mako/config`, `.config/btop/btop.conf`, `.config/starship.toml`, `.config/zellij/config.kdl`, `.config/lazygit/config.yml`, `.config/swappy/config`, `.config/kdeglobals`, `.config/dolphinrc`, GTK & XSettings configs.
- **Runtime User State**: `.config/hypr/hypridle.conf` (idle & suspend timeouts), `.config/hypr/hyprpaper.conf` (wallpaper selection), `.config/hypr/modules/input.lua` (keyboard layout & variant), `.config/mimeapps.list`.

---

## 🧩 Personal Configurations & Modular Extensions (`scripts/dotfiles-personal.sh`)

To customize your system with personal plugins, programming languages, multi-monitor setups, and shell tokens without dirtying the Git repository or causing merge conflicts during `git pull`, this dotfiles suite provides **granular, self-descriptive personal extension points** across all packages.

All personal files in these directories are automatically ignored by Git.

### 📂 Self-Descriptive Personal File Structure

#### 1. 🖥️ Hyprland (`~/.dotfiles/.config/hypr/user/`)
Split into dedicated files for each component:
- `monitors.lua`: Custom multi-display resolutions, refresh rates, and positioning (e.g. `hyprland.monitor(...)`). Automatically written by the Screen Resolution & Display Scaling Manager (`Super+Shift+D` / `resolution_menu.py`).
- `input.lua`: Keyboard layouts, variants, options, mouse sensitivity, and touchpad natural scroll. Automatically written by the Keyboard Layout & Variant Manager (`Super+Shift+K` / `keyboard_layout.py`).
- `keybinds.lua`: Personal hotkeys and custom application shortcuts (automatically parsed and displayed by the Keybinds Viewer `Super+K` / `keybinds_viewer.py`).
- `rules.lua`: Custom window rules, floating rules, and workspace assignments.
- `autostart.lua`: Background applications to launch on login (e.g. Discord, Spotify).
- `env.lua`: Personal compositor environment variables.
- `workspaces.lua`: Custom workspace monitors and behavior.

#### 2. 🐚 Shell (`~/.dotfiles/.config/shell/user/` & `~/.zshenv`)
- `~/.zshenv`: Machine-wide environment variables loaded by all Zsh shells and tools (outside git).
- `~/.config/shell/user/env.sh` / `paths.sh`: Personal PATH additions (e.g. `$GOPATH/bin`, Cargo).
- `~/.config/shell/user/aliases.sh`: Custom command aliases.
- `~/.config/shell/user/functions.sh`: Custom shell helper functions.
- `~/.config/shell/user/tokens.sh`: Private API tokens and credentials.

#### 3. 📝 Neovim (`~/.dotfiles/.config/nvim/lua/plugins/`)
- `personal_go.lua`: Golang development suite (`go.nvim`, `nvim-dap-go`, Delve debugger).
- `personal_web.lua`: React, Next.js, and TypeScript JSX/TSX helpers (`nvim-ts-autotag`).
- `personal_terminal.lua`: ToggleTerm suite (`<leader>tt` floating terminal, splits, and floating Lazygit).
- `personal_lsp.lua`: Personal LSP servers (`gopls`, `ts_ls`, `tailwindcss`, `eslint`), formatters (`prettierd`), and inlay hints.
- `personal_<name>.lua`: Any additional custom plugin or language configuration.

---

### 🛠️ Personal Settings Management Utility (`scripts/dotfiles-personal.sh`)

A dedicated CLI utility is provided at `~/.dotfiles/scripts/dotfiles-personal.sh` (or alias `dotpersonal`):

```bash
# 1. Inspect all active personal files and version control status
dotpersonal status

# 2. Export all personal settings to an archive (for backup or transferring to a new machine)
dotpersonal export ~/my-personal-dotfiles.tar.gz

# 3. Import and restore personal settings from an archive or folder
dotpersonal import ~/my-personal-dotfiles.tar.gz

# 4. Initialize a standalone, private Git repository for your personal settings
dotpersonal init-repo

# 5. Commit personal configuration updates to your private personal repo
dotpersonal save "feat: add python setup and custom keybinds"

# 6. View diffs between active files and your private personal repo
dotpersonal diff

# 7. Push / pull personal configs to your private GitHub or GitLab repository
dotpersonal push
dotpersonal pull
```



