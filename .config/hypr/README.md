# 🚀 Hyprland Modular Lua Configuration

A modular, performant, and feature-rich **Hyprland** setup powered by **Lua configuration** (`hyprland.lua`), Python automation utilities, custom OSD notifications, Catppuccin-themed clipboard management, and interactive dmenu controls.

---

## 📁 Repository Structure

```
~/.config/hypr/
├── hyprland.lua                 # Main entrypoint; loads all modular components
├── hyprlock.conf                # Catppuccin Mocha lockscreen configuration
├── hypridle.conf                # Screen timeout & idle power management
├── install.sh                   # Automated dependency installer & setup script
├── .gitignore                   # Version control exclusions
├── modules/                     # Modular configuration files
│   ├── animations.lua           # Smooth window, workspace, layer animations & spring curves
│   ├── appearance.lua           # Gaps, active/inactive borders, shadows & blur settings
│   ├── autostart.lua            # Daemons & background services (Hyprpaper, Mako, Waybar, Clipboard)
│   ├── env.lua                  # Environment variables & cursor sizes
│   ├── input.lua                # Keyboard layout, mouse sensitivity, trackpad gestures
│   ├── keybinds.lua             # Comprehensive keybindings & shortcuts
│   ├── layouts.lua              # Dwindle, Master, and Scrolling layout configurations
│   ├── misc.lua                 # Wallpapers, logo, and general misc settings
│   ├── monitors.lua             # Monitor resolution, position, and scaling definitions
│   ├── permissions.lua          # Security and ecosystem permissions
│   ├── programs.lua             # Default apps (terminal, browser, file manager, app launcher)
│   └── rules.lua                # Window rules, layer rules, and workspace persistence
└── scripts/                     # Custom Python & Shell utilities
    ├── brightness_control.py    # Backlight & external DDC monitor brightness with OSD & GUI menu
    ├── clipboard_manager.py     # Image/text clipboard manager with thumbnails, pause & delete
    ├── emoji_picker.py          # Searchable emoji catalog with instant copy & auto-typing
    ├── fuzzel_launcher.sh       # Fuzzel wrapper with outside-click dismissal
    ├── keybinds_viewer.py       # Dynamic keybindings parser & interactive cheat sheet
    ├── keyboard_layout.py       # Dynamic keyboard layout switcher & installer
    ├── nightlight.py            # Warm blue-light filter (3800K night / 6500K day)
    ├── ocr_grab.py              # Screen OCR text extraction via Tesseract
    ├── quick_calc.py            # Interactive math expression evaluator
    ├── resolution_menu.py       # Interactive display resolution & UI scale switcher
    ├── scale_window.py          # Window resizing with on-screen dimensions overlay
    ├── screen_capture.py        # Screenshot & video screen recording with audio & editor support
    ├── volume_control.py        # Speaker & mic volume control, OSD, and device switcher
    └── wofi_launcher.py         # Wofi wrapper with transparent backdrop layer
```

---

## 📦 Required Dependencies & Software

### 1. Core Window Manager, Session & Desktop Portals
- **Hyprland** — Dynamic tiling Wayland compositor.
- **Hyprland Lua integration** — Enables modular Lua configuration.
- **hyprlock** & **hypridle** — Modern Catppuccin Mocha lock screen and idle management.
- **xdg-desktop-portal-hyprland** & **xdg-desktop-portal-gtk** — Screen sharing, file picker, and portals.
- **hyprpolkitagent** — Polkit authentication agent for privilege escalation.

### 2. Status Bar, Notifications, Session & Launchers
- **waybar** — Highly customizable top status bar with hardware stats & dynamic power profiles.
- **mako** — Lightweight notification daemon (with click-to-focus window activation).
- **hyprpaper** — Fast wallpaper utility.
- **fuzzel** — High-performance Wayland application launcher and dmenu.
- **wofi** — Alternative launcher with menu support.
- **wlogout** — Wayland logout and power management modal.

### 3. Applications & File Management
- **kitty** — GPU-accelerated terminal emulator (`SUPER + Q`).
- **yazi** — Lightning fast terminal file manager (`SUPER + SHIFT + E`).
- **dolphin** — GUI file manager (`SUPER + E`).
- **firefox** — Web browser (`SUPER + B`).
- **btop** — Floating system monitor.

### 4. Audio & Media Controls
- **pipewire**, **pipewire-pulse**, **wireplumber** — Audio server and subsystem.
- **libpulse** (`pactl`) & `wpctl` — Device switching and volume control.
- **playerctl** — Media control (Play/Pause, Next, Prev).

### 5. Brightness & Night Light
- **brightnessctl** — Internal laptop display backlight control.
- **ddcutil** — External monitor DDC/CI brightness adjustment.
- **hyprsunset** / **wlsunset** — Blue light filter & night light temperature manager.

### 6. Clipboard & Productivity Tools
- **wl-clipboard** (`wl-copy`, `wl-paste`) — Wayland clipboard utilities.
- **cliphist** — Clipboard history daemon for text and binary images.
- **hyprpicker** — Wayland pixel color picker (`SUPER + SHIFT + P`).
- **tesseract** & **tesseract-data-eng** — Optical character recognition text grabber (`SUPER + SHIFT + T`).
- **wtype** — Wayland keystroke simulation for emoji typing.

### 7. Screenshots & Screen Recording
- **grim** — Wayland screenshot capture.
- **slurp** — Interactive region/area selector.
- **wf-recorder** — Wayland video screen recorder with audio.
- **swappy** / **satty** — Screenshot annotation tools.

### 8. Python Runtime & Libraries
- **python3**
- **python-gobject** (`python-gi`), **gtk3**, **gtk-layer-shell** — Required for interactive popups & transparent click-dismiss backdrop.
- **libnotify** (`notify-send`) — On-Screen Display (OSD) notifications.

### 9. Fonts & Icons
- **ttf-jetbrains-mono-nerd** — Required for icons and glyphs.
- **papirus-icon-theme** — System icons for notifications and menus.

---

## 🛠️ How to Install

### Option A: Automated Installation (Recommended for Arch Linux)

Run the included `install.sh` script:

```bash
chmod +x ~/.config/hypr/install.sh
~/.config/hypr/install.sh
```

---

### Option B: Manual Installation via `pacman`

```bash
sudo pacman -S --needed \
    hyprland hypridle hyprlock hyprpaper hyprpicker hyprsunset wlsunset hyprpolkitagent \
    xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
    waybar mako fuzzel wofi wlogout kitty yazi zoxide fzf wtype \
    dolphin firefox btop \
    pipewire pipewire-pulse wireplumber libpulse playerctl \
    brightnessctl ddcutil wl-clipboard cliphist \
    grim slurp swappy wf-recorder tesseract tesseract-data-eng \
    libnotify python python-gobject gtk3 gtk-layer-shell \
    ttf-jetbrains-mono-nerd papirus-icon-theme
```

---

## 🚀 How to Apply This Configuration

### 1. Clone / Copy to Config Location
Ensure the files reside at `~/.config/hypr`:

```bash
git clone <your-repo-url> ~/.config/hypr
```

### 2. Make All Helper Scripts Executable
```bash
chmod +x ~/.config/hypr/scripts/* ~/.config/hypr/install.sh
```

### 3. Ensure Required Directories Exist
```bash
mkdir -p ~/.cache/cliphist_thumbs ~/Pictures/Screenshots ~/Videos/Recordings
```

### 4. External Monitor DDC Permissions (Optional)
If using `ddcutil` for external monitor brightness without root:
```bash
sudo modprobe i2c-dev
sudo usermod -aG i2c $USER
```

### 5. Launch or Reload Hyprland
- **Starting from TTY / Login Manager**: Execute `Hyprland`.
- **Reloading inside an active session**:
  ```bash
  hyprctl reload
  ```
- **Lock Screen**: Press `SUPER + L` or `SUPER + ALT + L`.
- **Toggle Waybar**:
  Press `SUPER + SHIFT + W` or run:
  ```bash
  ~/.config/waybar/scripts/launch_waybar.sh
  ```

---

## ⌨️ Keybindings Cheat Sheet

### 🖥️ Applications & Navigation
| Shortcut | Action |
| :--- | :--- |
| `SUPER + Q` | Open Kitty Terminal |
| `SUPER + grave (~)` | Toggle Dropdown Scratchpad Terminal (`dropdown-terminal`) |
| `SUPER + G` | Open Floating Lazygit TUI |
| `SUPER + D` | Open Floating Lazydocker TUI |
| `SUPER + SHIFT + Z` | Open Floating Zellij Session |
| `SUPER + E` | Open Dolphin File Manager |
| `SUPER + SHIFT + E` | Open Yazi Terminal File Manager |
| `SUPER + B` | Open Firefox Browser |
| `SUPER + R` | Open Fuzzel Application Launcher (with outside click-dismiss) |
| `SUPER + ESCAPE` / `SUPER + M` | Open Power & Session Menu (`wlogout`) |
| `SUPER + L` / `SUPER + ALT + L` | Lock Screen immediately (`hyprlock`) |
| `SUPER + C` | Close Active Window |
| `SUPER + V` | Toggle Window Floating Mode |
| `SUPER + P` | Toggle Pseudo Tiling |
| `SUPER + J` | Toggle Split (Dwindle layout) |
| `SUPER + SHIFT + W` | Toggle Waybar (Show / Hide) |
| `SUPER + [1-9, 0]` | Switch to Workspace 1–10 |
| `SUPER + SHIFT + [1-9, 0]` | Move Active Window to Workspace 1–10 |
| `SUPER + S` | Toggle Magic Scratchpad Workspace |
| `SUPER + SHIFT + S` | Move Active Window to Special Scratchpad |

---

### 🌐 Keyboard Layout & Input Switching
| Shortcut | Action |
| :--- | :--- |
| `SUPER + Space` | Cycle to next active keyboard layout |
| `SUPER + SHIFT + K` | Open interactive active layout menu |
| `SUPER + ALT + K` | Open add new keyboard layout menu |

---

### 🔔 Notifications & Quick Settings
| Shortcut | Action |
| :--- | :--- |
| `SUPER + N` | Open Notification History Center |
| `SUPER + SHIFT + N` | Toggle Do-Not-Disturb (DND) Mode |
| `SUPER + SHIFT + V` / `SUPER + ALT + V` / `SUPER + SHIFT + C` | Open Clipboard History Browser |
| `SUPER + ALT + D` | Open Delete Item / Wipe Clipboard History Menu |

---

### ⚡ Productivity & Workflow Utilities
| Shortcut | Action |
| :--- | :--- |
| `SUPER + /` / `SUPER + ?` / `SUPER + F1` | **Dynamic Keybindings Viewer**: Searchable shortcut cheat sheet |
| `SUPER + SHIFT + P` | **Hyprpicker**: Pick color from screen, copy hex code & notify |
| `SUPER + SHIFT + T` / `SUPER + ALT + T` | **Screen OCR**: Grab and extract text from any screen region to clipboard |
| `SUPER + ALT + N` | **Night Light**: Toggle warm blue light filter (3800K / 6500K) |
| `SUPER + =` / `SUPER + ALT + C` | **Quick Calculator**: Interactive math evaluator via Fuzzel |
| `SUPER + .` (period) | **Emoji Picker**: Searchable emoji menu with instant copy & auto-typing |

---

### 📐 Window Resizing & Screen Scaling
| Shortcut | Action |
| :--- | :--- |
| `SUPER + CTRL + =` / `+` / `KP_Add` | Scale Window Up (+40px) with live dimension OSD |
| `SUPER + CTRL + -` / `KP_Subtract` | Scale Window Down (-40px) with live dimension OSD |
| `SUPER + CTRL + Arrow / HJKL` | Directional Window Resize (Left / Right / Up / Down) |
| `SUPER + CTRL + I` / `0` | Display active window dimensions & screen % |
| `SUPER + SHIFT + R` / `SUPER + SHIFT + D` | Open Interactive Screen Resolution & Display Scaling Menu |
| `SUPER + ALT + =` / `+` | Increment Display Scale (+0.1) |
| `SUPER + ALT + -` | Decrement Display Scale (-0.1) |
| `SUPER + ALT + 0` | Display Active Screen Scale Factor |
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
| `SHIFT + XF86AudioRaiseVolume` / `LowerVolume` | Adjust Microphone Volume |
| `SUPER + SHIFT + A` / `SUPER + ALT + A` | Open Audio Control & Device Switcher Menu |
| `XF86AudioPlay` / `Pause` / `Next` / `Prev` | Media playback controls via `playerctl` |
| `XF86MonBrightnessUp` / `Down` | Adjust Laptop Screen Brightness with OSD |
| `SUPER / SHIFT + XF86MonBrightnessUp` / `Down` | Adjust External Monitor Brightness (DDC/CI) |
| `SUPER + SHIFT + B` / `SUPER + ALT + B` | Open Interactive Brightness Presets Menu |

---

### 📸 Screenshots & Screen Recording (`screen_capture.py`)
| Shortcut | Action |
| :--- | :--- |
| `Print` | Capture Area / Selection to clipboard & file |
| `SHIFT + Print` | Capture Full Screen |
| `ALT + Print` | Capture Active Window |
| `CTRL + Print` | Capture Area & Open in Annotation Tool (Swappy) |
| `SUPER + Print` | Open Interactive Capture Menu (5s delay, full/area) |
| `SUPER + ALT + R` | Toggle Area Video Screen Recording |
| `SUPER + SHIFT + R` | Stop Active Video Screen Recording |

---

## 💡 Customization & Tweaks

- **Change Default Programs**: Edit [modules/programs.lua](file:///home/kunal/.config/hypr/modules/programs.lua).
- **Adjust Appearance & Gaps**: Edit [modules/appearance.lua](file:///home/kunal/.config/hypr/modules/appearance.lua).
- **Tweak Animations**: Edit [modules/animations.lua](file:///home/kunal/.config/hypr/modules/animations.lua).
- **Add / Modify Keybindings**: Edit [modules/keybinds.lua](file:///home/kunal/.config/hypr/modules/keybinds.lua).
- **Configure Window Rules**: Edit [modules/rules.lua](file:///home/kunal/.config/hypr/modules/rules.lua).
- **Autostarted Apps**: Edit [modules/autostart.lua](file:///home/kunal/.config/hypr/modules/autostart.lua).
- **Monitors & Scaling**: Edit [modules/monitors.lua](file:///home/kunal/.config/hypr/modules/monitors.lua).

