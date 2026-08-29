# 🚀 Hyprland Modular Lua Configuration

A modular, performant, and feature-rich **Hyprland** setup powered by **Lua configuration** (`hyprland.lua`), Python automation utilities, custom OSD notifications, Catppuccin-themed clipboard management, and interactive dmenu controls.

---

## 📁 Repository Structure

```
~/.config/hypr/
├── hyprland.lua                 # Main entrypoint; loads all modular components
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
    ├── fuzzel_launcher.sh       # Fuzzel wrapper with outside-click dismissal
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

### 2. Status Bar, Notifications & Launchers
- **waybar** — Highly customizable top status bar.
- **mako** — Lightweight notification daemon (with click-to-focus window activation).
- **hyprpaper** — Fast wallpaper utility.
- **fuzzel** — High-performance Wayland application launcher and dmenu.
- **wofi** — Alternative launcher with menu support.

### 3. Applications & File Management
- **kitty** — GPU-accelerated terminal emulator (`SUPER + Q`).
- **yazi** — Lightning fast terminal file manager (`SUPER + SHIFT + E`).
- **dolphin** — GUI file manager (`SUPER + E`).
- **firefox** — Web browser (`SUPER + B`).
- **btop** — Floating system monitor.

### 4. Audio & Media Controls
- **pipewire**, **pipewire-pulse**, **wireplumber** — Audio server and subsystem.
- **libpulse** (`pactl`) — Device switching and volume control.
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
- **swappy** / **satty** (Optional AUR) — Screenshot annotation tools.

### 8. Python Runtime & Libraries
- **python3**
- **python-gobject** (`python-gi`), **gtk3**, **gtk-layer-shell** — Required for the transparent click-dismiss backdrop.
- **libnotify** (`notify-send`) — On-Screen Display (OSD) notifications.

### 9. Fonts & Icons
- **ttf-jetbrains-mono-nerd** or **ttf-nerd-fonts-symbols** — Required for icons and glyphs.
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

### Option B: Manual Installation via `pacman` and AUR

#### 1. Install Official Arch Packages
```bash
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
```

#### 2. Install AUR Packages (Annotation Tools)
Using `paru` or `yay`:
```bash
paru -S --needed swappy satty
# or: yay -S --needed swappy satty
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
  ~/.config/waybar/scripts/launch_waybar.sh --toggle
  ```

---

## ⌨️ Keybindings Cheat Sheet

### 🖥️ Applications & Navigation
| Shortcut | Action |
| :--- | :--- |
| `SUPER + Q` | Open Kitty Terminal |
| `SUPER + E` | Open Dolphin File Manager |
| `SUPER + SHIFT + E` | Open Yazi Terminal File Manager |
| `SUPER + B` | Open Firefox Browser |
| `SUPER + R` | Open Fuzzel Application Launcher (with outside click-dismiss) |
| `SUPER + L` / `ALT + L` | Lock Screen immediately (`hyprlock`) |
| `SUPER + C` | Close Active Window |
| `SUPER + V` | Toggle Window Floating Mode |
| `SUPER + P` | Toggle Pseudo Tiling |
| `SUPER + J` | Toggle Split (Dwindle layout) |
| `SUPER + M` | Hyprland Exit / Power Menu |
| `SUPER + SHIFT + W` | Toggle Waybar (Show / Hide) |
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
| `SUPER + SHIFT + V` | Open Clipboard History Menu (with image previews & search) |
| `SUPER + ALT + V` | Open Clipboard History Menu |
| `SUPER + ALT + D` | Open Delete Item / Wipe History Menu |

---

### 📐 Window Resizing & Screen Scaling
| Shortcut | Action |
| :--- | :--- |
| `SUPER + CTRL + =` / `+` | Scale Window Up (+40px) with live dimension OSD |
| `SUPER + CTRL + -` | Scale Window Down (-40px) with live dimension OSD |
| `SUPER + CTRL + Arrow / HJKL` | Directional Window Resize (Left / Right / Up / Down) |
| `SUPER + CTRL + I` or `0` | Display active window dimensions & screen % |
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
| `SUPER + SHIFT + A` / `ALT + A` | Open Audio Control & Device Switcher Menu |
| `XF86MonBrightnessUp / Down` | Adjust Laptop Screen Brightness |
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
