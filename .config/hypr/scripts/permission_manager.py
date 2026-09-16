#!/usr/bin/env python3
"""
=============================================================================
Hyprland Security & Permissions Manager (Desktop GUI & CLI)
=============================================================================
A modern GTK3 utility that dynamically adapts to the active system theme to:
- Inspect and manage persistent Hyprland security permissions (screencopy, plugin)
- Toggle Hyprland ecosystem permission enforcement (enforce_permissions)
- Detect installed and active Hyprland compositor plugins
- Manage plugin loaders (hyprpm, hyprctl) and individual plugin security rules
- Add, edit, remove, and switch permission rules (allow, ask, deny)
- Provide quick presets for common Hyprland & Wayland applications
- Write modifications to ~/.config/hypr/modules/permissions.lua
- Notify user about compositor restart requirement for security rules
"""

import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
DOTFILES_DIR = HOME / ".dotfiles"
DOTFILES_CONFIG_DIR = DOTFILES_DIR / ".config"
PERMISSIONS_LUA = CONFIG_DIR / "hypr" / "modules" / "permissions.lua"
ASSETS_DIR = CONFIG_DIR / "hypr" / "assets"
DOTFILES_ASSETS_DIR = DOTFILES_CONFIG_DIR / "hypr" / "assets"

# Common applications known to need Hyprland permissions
KNOWN_APPS = [
    {
        "id": "hyprlock",
        "name": "Hyprlock (Screen Locker)",
        "binary": "/usr/(bin|local/bin)/hyprlock",
        "type": "screencopy",
        "mode": "allow",
        "icon": "system-lock-screen",
        "desc": "Required for screen locking, background blur, and capture"
    },
    {
        "id": "hyprpicker",
        "name": "Hyprpicker (Color Picker)",
        "binary": "/usr/(bin|local/bin)/hyprpicker",
        "type": "screencopy",
        "mode": "allow",
        "icon": "color-picker",
        "desc": "Required to sample pixel colors from active monitors"
    },
    {
        "id": "grim",
        "name": "Grim (Screenshot Utility)",
        "binary": "/usr/(bin|local/bin)/grim",
        "type": "screencopy",
        "mode": "allow",
        "icon": "applets-screenshooter",
        "desc": "Required for screen capture, region snapshot, and OCR"
    },
    {
        "id": "xdg-desktop-portal-hyprland",
        "name": "Desktop Portal (Screen Sharing)",
        "binary": "/usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland",
        "type": "screencopy",
        "mode": "allow",
        "icon": "video-display",
        "desc": "Required for PipeWire screen sharing in browsers & Discord"
    },
    {
        "id": "wf-recorder",
        "name": "WF-Recorder (Screen Recorder)",
        "binary": "/usr/(bin|local/bin)/wf-recorder",
        "type": "screencopy",
        "mode": "allow",
        "icon": "camera-video",
        "desc": "Required for video recording and GIF captures"
    },
    {
        "id": "hyprsunset",
        "name": "Hyprsunset (Blue Light / Gamma)",
        "binary": "/usr/(bin|local/bin)/hyprsunset",
        "type": "screencopy",
        "mode": "allow",
        "icon": "weather-clear-night",
        "desc": "Required for blue-light temperature and display gamma filter"
    },
    {
        "id": "hyprpm",
        "name": "Hyprpm (Plugin Manager)",
        "binary": "/usr/(bin|local/bin)/hyprpm",
        "type": "plugin",
        "mode": "allow",
        "icon": "system-software-install",
        "desc": "Required to build and load Hyprland compositor plugins"
    },
    {
        "id": "wl-screenrec",
        "name": "wl-screenrec (Hardware Recorder)",
        "binary": "/usr/(bin|local/bin)/wl-screenrec",
        "type": "screencopy",
        "mode": "allow",
        "icon": "camera-video",
        "desc": "Hardware-accelerated screen recorder for Wayland"
    },
    {
        "id": "swappy",
        "name": "Swappy (Snapshot Editor)",
        "binary": "/usr/(bin|local/bin)/swappy",
        "type": "screencopy",
        "mode": "allow",
        "icon": "accessories-image-viewer",
        "desc": "Interactive snapshot editing and annotation"
    },
    {
        "id": "obs",
        "name": "OBS Studio",
        "binary": "/usr/(bin|local/bin)/obs",
        "type": "screencopy",
        "mode": "allow",
        "icon": "obs",
        "desc": "Open Broadcaster Software live streaming & recording"
    }
]

# Hyprland Plugin Loaders that control plugin loading
PLUGIN_LOADERS = [
    {
        "id": "hyprpm",
        "name": "Hyprpm (Hyprland Plugin Manager)",
        "binary": "/usr/(bin|local/bin)/hyprpm",
        "type": "plugin",
        "default_mode": "allow",
        "icon": "system-software-install",
        "desc": "Compiles, updates, and auto-reloads plugins via hyprpm reload",
        "recommended": "allow (Recommended: avoids repeated permission prompts on reload)"
    },
    {
        "id": "hyprctl",
        "name": "Hyprctl (Compositor IPC Client)",
        "binary": "/usr/(bin|local/bin)/hyprctl",
        "type": "plugin",
        "default_mode": "deny",
        "icon": "utilities-terminal",
        "desc": "General CLI that can execute 'hyprctl plugin load <path>'",
        "recommended": "deny or ask (Recommended: prevents unvetted scripts from loading .so files)"
    }
]

# Popular official and community Hyprland plugins
POPULAR_PLUGINS = [
    {
        "id": "hyprbars",
        "name": "Hyprbars",
        "binary": "/usr/(lib|local/lib)/hyprland/hyprbars.so",
        "repo": "hyprwm/hyprland-plugins",
        "desc": "Adds window titlebars with customizable action buttons"
    },
    {
        "id": "hyprexpo",
        "name": "Hyprexpo",
        "binary": "/usr/(lib|local/lib)/hyprland/hyprexpo.so",
        "repo": "hyprwm/hyprland-plugins",
        "desc": "Interactive overview grid of all active workspaces"
    },
    {
        "id": "hyprtrails",
        "name": "Hyprtrails",
        "binary": "/usr/(lib|local/lib)/hyprland/hyprtrails.so",
        "repo": "hyprwm/hyprland-plugins",
        "desc": "Smooth graphical motion trails for moving windows"
    },
    {
        "id": "hyprwinwrap",
        "name": "Hyprwinwrap",
        "binary": "/usr/(lib|local/lib)/hyprland/hyprwinwrap.so",
        "repo": "hyprwm/hyprland-plugins",
        "desc": "Embeds background apps (video/visualizers) directly into wallpaper canvas"
    },
    {
        "id": "hycov",
        "name": "Hycov",
        "binary": "/usr/(lib|local/lib)/hyprland/hycov.so",
        "repo": "DreamMaoMao/hycov",
        "desc": "Expose-style overview and fast window switcher"
    },
    {
        "id": "hyprsplit",
        "name": "Hyprsplit",
        "binary": "/usr/(lib|local/lib)/hyprland/hyprsplit.so",
        "repo": "shezdy/hyprsplit",
        "desc": "Independent workspace numbering per connected display"
    },
    {
        "id": "hypr-dynamic-cursors",
        "name": "Dynamic Cursors",
        "binary": "/usr/(lib|local/lib)/hyprland/hypr-dynamic-cursors.so",
        "repo": "VirtCode/hypr-dynamic-cursors",
        "desc": "Physics-based cursor tilting, stretching, and motion dynamics"
    }
]


def get_active_theme_colors():
    """Load colors from active theme JSON file with fallback."""
    cache_state = HOME / ".cache" / "hypr_theme_state.json"
    current_txt = HOME / ".cache" / "current_theme"
    theme_id = "catppuccin-mocha"

    if cache_state.exists():
        try:
            with open(cache_state, "r", encoding="utf-8") as f:
                theme_id = json.load(f).get("current_theme", theme_id)
        except Exception:
            pass
    elif current_txt.exists():
        try:
            theme_id = current_txt.read_text(encoding="utf-8").strip() or theme_id
        except Exception:
            pass

    for d in [CONFIG_DIR / "theme", DOTFILES_CONFIG_DIR / "theme"]:
        tfile = d / f"{theme_id}.json"
        if tfile.exists():
            try:
                with open(tfile, "r", encoding="utf-8") as f:
                    tdata = json.load(f)
                    return tdata.get("colors", {}), tdata.get("type", "dark"), theme_id
            except Exception:
                pass

    return {
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
        "accent": "#cba6f7", "blue": "#89b4fa", "green": "#a6e3a1",
        "yellow": "#f9e2af", "peach": "#fab387", "red": "#f38ba8",
        "mauve": "#cba6f7", "teal": "#94e2d5", "pink": "#f5c2e7",
        "sapphire": "#74c7ec", "lavender": "#b4befe"
    }, "dark", theme_id


def get_contrast_color(hex_color, dark_fg="#11111b", light_fg="#ffffff"):
    """Calculate high-contrast foreground color based on background luminance."""
    if not hex_color or not isinstance(hex_color, str) or not hex_color.startswith("#"):
        return light_fg
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c + c for c in hex_clean)
    if len(hex_clean) < 6:
        return light_fg
    try:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return dark_fg if lum > 140 else light_fg
    except Exception:
        return light_fg


def hex_to_rgba(hex_color, alpha=1.0):
    """Convert hex color code to rgba(...) CSS string."""
    if not hex_color or not isinstance(hex_color, str) or not hex_color.startswith("#"):
        return hex_color
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c + c for c in h)
    if len(h) >= 6:
        try:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        except Exception:
            return hex_color
    return hex_color


def detect_hyprland_plugins():
    """Detect all installed, active, or configured Hyprland plugins."""
    plugins = []
    seen_names = set()

    # 1. Live plugins reported by running compositor (hyprctl -j plugin list)
    try:
        res = subprocess.run(["hyprctl", "-j", "plugin", "list"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, list):
                for p in data:
                    name = p.get("name", "") or "Unnamed Plugin"
                    handle = p.get("handle", "") or p.get("path", "")
                    author = p.get("author", "")
                    desc = p.get("description", "")
                    seen_names.add(name.lower())
                    plugins.append({
                        "name": name,
                        "author": author or "Author Unknown",
                        "description": desc or "Currently loaded and running in Hyprland",
                        "path": handle or f"hyprland-plugin:{name}",
                        "status": "loaded",
                        "source": "Active Compositor",
                        "icon": "system-run"
                    })
    except Exception:
        pass

    # 2. Check hyprpm data directory (~/.local/share/hyprpm)
    hyprpm_dir = Path.home() / ".local" / "share" / "hyprpm"
    if hyprpm_dir.exists():
        for so_file in hyprpm_dir.rglob("*.so"):
            p_name = so_file.stem.replace("lib", "")
            if p_name.lower() not in seen_names:
                seen_names.add(p_name.lower())
                plugins.append({
                    "name": p_name.title(),
                    "author": "hyprpm",
                    "description": f"Compiled and managed by hyprpm ({so_file.name})",
                    "path": str(so_file),
                    "status": "installed",
                    "source": "hyprpm",
                    "icon": "application-x-sharedlib"
                })

    # 3. Check Hyprland configuration files for plugin declarations
    config_dir = Path.home() / ".config" / "hypr"
    if config_dir.exists():
        for cfg_file in config_dir.glob("**/*"):
            if cfg_file.is_file() and cfg_file.suffix in [".lua", ".conf"] and "permissions" not in cfg_file.name:
                try:
                    for line in cfg_file.read_text(encoding="utf-8").splitlines():
                        sline = line.strip()
                        if sline.startswith("#") or sline.startswith("--"):
                            continue
                        if "plugin" in sline and (".so" in sline or "load" in sline):
                            match = re.search(r'["\']?([^"\'\s]+\.so)["\']?', sline)
                            if match:
                                so_path = match.group(1)
                                p_name = Path(so_path).stem.replace("lib", "")
                                if p_name.lower() not in seen_names:
                                    seen_names.add(p_name.lower())
                                    plugins.append({
                                        "name": p_name.title(),
                                        "author": "config",
                                        "description": f"Configured in {cfg_file.name}",
                                        "path": so_path,
                                        "status": "configured",
                                        "source": f"{cfg_file.name}",
                                        "icon": "preferences-system"
                                    })
                except Exception:
                    pass

    return plugins


class PermissionConfig:
    """Handles reading and writing ~/.config/hypr/modules/permissions.lua."""

    def __init__(self, file_path=PERMISSIONS_LUA):
        self.file_path = Path(file_path)
        self.enforce_permissions = True
        self.rules = []  # list of dicts: {"binary": str, "type": str, "mode": str}
        self.load()

    def load(self):
        self.rules = []
        self.enforce_permissions = True

        if not self.file_path.exists():
            return

        try:
            content = self.file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {self.file_path}: {e}", file=sys.stderr)
            return

        # Check enforce_permissions
        enforce_match = re.search(r"enforce_permissions\s*=\s*(true|false)", content, re.IGNORECASE)
        if enforce_match:
            self.enforce_permissions = (enforce_match.group(1).lower() == "true")

        # Match positional: hl.permission("binary", "type", "mode")
        pos_matches = re.finditer(
            r'hl\.permission\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
            content
        )
        for m in pos_matches:
            self.rules.append({
                "binary": m.group(1).strip(),
                "type": m.group(2).strip(),
                "mode": m.group(3).strip()
            })

        # Match table syntax: hl.permission({ binary = "...", type = "...", mode = "..." })
        table_matches = re.finditer(
            r'hl\.permission\s*\(\s*\{([^}]+)\}\s*\)',
            content
        )
        for tm in table_matches:
            body = tm.group(1)
            b_match = re.search(r'binary\s*=\s*["\']([^"\']+)["\']', body)
            t_match = re.search(r'type\s*=\s*["\']([^"\']+)["\']', body)
            m_match = re.search(r'mode\s*=\s*["\']([^"\']+)["\']', body)
            if b_match and t_match and m_match:
                entry = {
                    "binary": b_match.group(1).strip(),
                    "type": t_match.group(1).strip(),
                    "mode": m_match.group(1).strip()
                }
                if not any(r["binary"] == entry["binary"] and r["type"] == entry["type"] for r in self.rules):
                    self.rules.append(entry)

    def save(self):
        """Write current permissions back to lua file cleanly."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "-----------------------",
            "----- PERMISSIONS -----",
            "-----------------------",
            "",
            "-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Permissions/",
            "-- Please note permission changes here require a Hyprland restart and are not applied on-the-fly",
            "-- for security reasons",
            "",
            "hl.config({",
            "  ecosystem = {",
            f"    enforce_permissions = {'true' if self.enforce_permissions else 'false'},",
            "  },",
            "})",
            ""
        ]

        for rule in self.rules:
            binary = rule.get("binary", "").strip()
            ptype = rule.get("type", "screencopy").strip()
            mode = rule.get("mode", "allow").strip()
            if binary:
                lines.append(f'hl.permission("{binary}", "{ptype}", "{mode}")')

        lines.append("")
        self.file_path.write_text("\n".join(lines), encoding="utf-8")

    def add_or_update_rule(self, binary, ptype, mode):
        binary = binary.strip()
        ptype = ptype.strip()
        mode = mode.strip()
        for rule in self.rules:
            if rule["binary"] == binary and rule["type"] == ptype:
                rule["mode"] = mode
                return False  # updated
        self.rules.append({"binary": binary, "type": ptype, "mode": mode})
        return True  # added new

    def get_rule_mode(self, binary, ptype):
        """Return mode if rule exists, else None."""
        for rule in self.rules:
            if rule["type"] == ptype:
                if rule["binary"] == binary or (binary in rule["binary"]) or (rule["binary"] in binary):
                    return rule["mode"]
        return None

    def remove_rule(self, index):
        if 0 <= index < len(self.rules):
            del self.rules[index]
            return True
        return False


def get_gui_css():
    c, ttype, _ = get_active_theme_colors()
    accent = c.get("accent", "#cba6f7")
    accent_fg = get_contrast_color(accent)
    green = c.get("green", "#a6e3a1")
    green_fg = get_contrast_color(green)
    red = c.get("red", "#f38ba8")
    red_fg = get_contrast_color(red)
    yellow = c.get("yellow", "#f9e2af")
    yellow_fg = get_contrast_color(yellow)
    blue = c.get("blue", "#89b4fa")
    blue_fg = get_contrast_color(blue)
    text_color = c.get("text", "#cdd6f4")
    surface0 = c.get("surface0", "#313244")
    surface1 = c.get("surface1", "#45475a")
    surface2 = c.get("surface2", "#585b70")
    base = c.get("base", "#1e1e2e")
    mantle = c.get("mantle", "#181825")
    subtext0 = c.get("subtext0", "#a6adc8")

    return f"""
    * {{
        font-family: system-ui, -apple-system, 'Inter', 'Roboto', 'Noto Sans', sans-serif;
    }}

    window {{
        background-color: {base};
        color: {text_color};
        font-size: 13px;
    }}

    .header-box {{
        background-color: {mantle};
        border-bottom: 1px solid {surface0};
        padding: 14px 20px;
    }}

    .window-title {{
        font-size: 16px;
        font-weight: bold;
        color: {accent};
    }}

    .window-subtitle {{
        font-size: 11px;
        color: {subtext0};
    }}

    /* Tab Switcher Segmented Bar */
    .tab-bar {{
        background-color: {mantle};
        border-bottom: 1px solid {surface0};
        padding: 0px 16px;
    }}

    button.tab-btn {{
        background-color: transparent;
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0px;
        padding: 10px 18px;
        font-weight: 600;
        font-size: 13px;
        color: {subtext0};
    }}

    button.tab-btn label {{
        color: {subtext0};
        font-weight: 600;
    }}

    button.tab-btn.active {{
        border-bottom: 2px solid {accent};
    }}

    button.tab-btn.active label {{
        color: {accent};
        font-weight: bold;
    }}

    button.tab-btn:hover label {{
        color: {text_color};
    }}

    .card {{
        background-color: {mantle};
        border: 1px solid {surface0};
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 10px;
    }}

    .banner-warning {{
        background-color: {hex_to_rgba(yellow, 0.16)};
        border: 1px solid {hex_to_rgba(yellow, 0.45)};
        border-radius: 8px;
        padding: 10px 14px;
    }}

    .banner-info {{
        background-color: {hex_to_rgba(blue, 0.14)};
        border: 1px solid {hex_to_rgba(blue, 0.35)};
        border-radius: 8px;
        padding: 10px 14px;
    }}

    .banner-text {{
        color: {text_color};
        font-size: 11.5px;
    }}

    .rule-row {{
        background-color: {surface0};
        border: 1px solid {surface1};
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        transition: all 150ms ease-in-out;
    }}

    .rule-row:hover {{
        background-color: {surface1};
        border-color: {surface2};
    }}

    .rule-name {{
        font-weight: bold;
        font-size: 13px;
        color: {text_color};
    }}

    .rule-binary {{
        font-family: monospace;
        font-size: 11px;
        color: {subtext0};
    }}

    .badge-allow {{
        background-color: {green};
        color: {green_fg};
        font-weight: bold;
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 6px;
    }}

    .badge-ask {{
        background-color: {yellow};
        color: {yellow_fg};
        font-weight: bold;
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 6px;
    }}

    .badge-deny {{
        background-color: {red};
        color: {red_fg};
        font-weight: bold;
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 6px;
    }}

    .badge-type {{
        background-color: {surface2};
        color: {text_color};
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 6px;
    }}

    .badge-loaded {{
        background-color: {green};
        color: {green_fg};
        font-weight: bold;
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 6px;
    }}

    .badge-installed {{
        background-color: {blue};
        color: {blue_fg};
        font-weight: bold;
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 6px;
    }}

    /* Universal Button Reset */
    button {{
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        border-radius: 8px;
        transition: all 120ms ease-in-out;
    }}

    /* Primary Buttons (+ Add Common Preset, Save & Apply) */
    button.btn-primary {{
        background-color: {accent};
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        border: 1px solid {accent};
        color: {accent_fg};
        border-radius: 8px;
        padding: 6px 14px;
        font-weight: bold;
    }}

    button.btn-primary label {{
        color: {accent_fg};
        font-weight: bold;
    }}

    button.btn-primary:hover {{
        background-color: {hex_to_rgba(accent, 0.88)};
        background-image: none;
        box-shadow: none;
        border-color: {hex_to_rgba(accent, 0.88)};
        color: {accent_fg};
    }}

    button.btn-primary:hover label {{
        color: {accent_fg};
        font-weight: bold;
    }}

    button.btn-primary:active {{
        background-color: {hex_to_rgba(accent, 0.75)};
        background-image: none;
    }}

    /* Secondary Buttons (+ Add Custom Rule, Reload Config) */
    button.btn-secondary {{
        background-color: {surface0};
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        color: {text_color};
        border-radius: 8px;
        padding: 6px 12px;
        border: 1px solid {surface1};
        font-weight: 600;
    }}

    button.btn-secondary label {{
        color: {text_color};
        font-weight: 600;
    }}

    button.btn-secondary:hover {{
        background-color: {surface1};
        background-image: none;
        box-shadow: none;
        border-color: {accent};
        color: {text_color};
    }}

    button.btn-secondary:hover label {{
        color: {text_color};
    }}

    button.btn-secondary:active {{
        background-color: {surface2};
        background-image: none;
    }}

    /* Danger Button (Delete) */
    button.btn-danger {{
        background-color: {hex_to_rgba(red, 0.15)};
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        color: {red};
        border-radius: 8px;
        padding: 4px 10px;
        border: 1px solid {hex_to_rgba(red, 0.45)};
        font-weight: bold;
    }}

    button.btn-danger label {{
        color: {red};
        font-weight: bold;
    }}

    button.btn-danger:hover {{
        background-color: {red};
        background-image: none;
        box-shadow: none;
        border-color: {red};
        color: {red_fg};
    }}

    button.btn-danger:hover label {{
        color: {red_fg};
        font-weight: bold;
    }}

    /* ComboBoxes & Selectors */
    combobox button,
    combobox button.combo {{
        background-color: {surface0};
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        color: {text_color};
        border: 1px solid {surface1};
        border-radius: 6px;
        padding: 4px 8px;
    }}

    combobox button label,
    combobox button cellview {{
        color: {text_color};
    }}

    combobox button:hover {{
        background-color: {surface1};
        border-color: {accent};
    }}

    /* Dialog Buttons */
    dialog button {{
        background-color: {surface0};
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        color: {text_color};
        border: 1px solid {surface1};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
    }}

    dialog button label {{
        color: {text_color};
        font-weight: 600;
    }}

    dialog button:hover {{
        background-color: {surface1};
        border-color: {accent};
    }}

    entry {{
        background-color: {surface0};
        color: {text_color};
        border: 1px solid {surface1};
        border-radius: 6px;
        padding: 5px 8px;
    }}

    entry:focus {{
        border-color: {accent};
    }}
    """


def launch_gui():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

    _, ttype, _ = get_active_theme_colors()
    settings = Gtk.Settings.get_default()
    if settings:
        settings.set_property("gtk-application-prefer-dark-theme", ttype == "dark")

    cfg = PermissionConfig()

    win = Gtk.Window(title="Hyprland Security & Permissions")
    win.set_default_size(740, 720)
    win.set_position(Gtk.WindowPosition.CENTER)

    # Set custom application icon
    icon_file = ASSETS_DIR / "permission-manager.png"
    if not icon_file.exists():
        icon_file = DOTFILES_ASSETS_DIR / "permission-manager.png"

    if icon_file.exists():
        try:
            win.set_icon_from_file(str(icon_file))
        except Exception:
            win.set_icon_name("permission-manager")
    else:
        win.set_icon_name("preferences-security")

    # Apply CSS
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(get_gui_css().encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    win.add(main_vbox)

    # 1. Header Box
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
    header_box.get_style_context().add_class("header-box")

    # App icon in header
    if icon_file.exists():
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon_file), 38, 38, True)
            icon_img = Gtk.Image.new_from_pixbuf(pb)
        except Exception:
            icon_img = Gtk.Image.new_from_icon_name("permission-manager", Gtk.IconSize.DND)
    else:
        icon_img = Gtk.Image.new_from_icon_name("preferences-security", Gtk.IconSize.DND)

    header_box.pack_start(icon_img, False, False, 0)

    title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    title_lbl = Gtk.Label(label="Hyprland Security & Permissions")
    title_lbl.set_xalign(0)
    title_lbl.get_style_context().add_class("window-title")

    sub_lbl = Gtk.Label(label="Manage persistent screen capture rules and compositor plugin permissions")
    sub_lbl.set_xalign(0)
    sub_lbl.get_style_context().add_class("window-subtitle")

    title_vbox.pack_start(title_lbl, False, False, 0)
    title_vbox.pack_start(sub_lbl, False, False, 0)
    header_box.pack_start(title_vbox, True, True, 0)

    btn_reload = Gtk.Button(label="Reload Config")
    btn_reload.get_style_context().add_class("btn-secondary")
    btn_reload.set_tooltip_text("Reload permissions from disk")
    header_box.pack_end(btn_reload, False, False, 0)

    main_vbox.pack_start(header_box, False, False, 0)

    # 2. Segmented Tab Bar (Rules vs Plugins)
    tab_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    tab_bar.get_style_context().add_class("tab-bar")

    btn_tab_rules = Gtk.Button(label="🛡️  Permissions & Rules")
    btn_tab_rules.get_style_context().add_class("tab-btn")
    btn_tab_rules.get_style_context().add_class("active")

    btn_tab_plugins = Gtk.Button(label="🔌  Hyprland Plugins")
    btn_tab_plugins.get_style_context().add_class("tab-btn")

    tab_bar.pack_start(btn_tab_rules, False, False, 0)
    tab_bar.pack_start(btn_tab_plugins, False, False, 0)
    main_vbox.pack_start(tab_bar, False, False, 0)

    # Stack container for view switching
    stack = Gtk.Stack()
    stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
    stack.set_transition_duration(180)
    main_vbox.pack_start(stack, True, True, 0)

    # =========================================================================
    # TAB 1: RULES & SCREENCOPY PERMISSIONS
    # =========================================================================
    rules_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    rules_view.set_margin_top(14)
    rules_view.set_margin_bottom(8)
    rules_view.set_margin_start(16)
    rules_view.set_margin_end(16)

    # Enforcement Switch Card
    enforce_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
    enforce_card.get_style_context().add_class("card")

    enforce_txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    enforce_title = Gtk.Label(label="Ecosystem Permission Enforcement")
    enforce_title.set_xalign(0)
    enforce_title.get_style_context().add_class("rule-name")

    enforce_desc = Gtk.Label(label="When enabled, applications must have permission to capture the screen or load plugins.")
    enforce_desc.set_xalign(0)
    enforce_desc.get_style_context().add_class("window-subtitle")
    enforce_desc.set_line_wrap(True)

    enforce_txt_box.pack_start(enforce_title, False, False, 0)
    enforce_txt_box.pack_start(enforce_desc, False, False, 0)
    enforce_card.pack_start(enforce_txt_box, True, True, 0)

    enforce_switch = Gtk.Switch()
    enforce_switch.set_active(cfg.enforce_permissions)
    enforce_switch.set_valign(Gtk.Align.CENTER)
    enforce_card.pack_end(enforce_switch, False, False, 0)
    rules_view.pack_start(enforce_card, False, False, 0)

    # Security Restart Banner
    banner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    banner_box.get_style_context().add_class("banner-warning")

    info_icon = Gtk.Image.new_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
    banner_box.pack_start(info_icon, False, False, 0)

    banner_lbl = Gtk.Label(
        label="<b>Note:</b> Hyprland permission rules are enforced at startup and <i>cannot</i> be updated on-the-fly for security reasons. A Hyprland restart or re-login is required for new rules to take effect."
    )
    banner_lbl.set_use_markup(True)
    banner_lbl.set_line_wrap(True)
    banner_lbl.set_xalign(0)
    banner_lbl.get_style_context().add_class("banner-text")
    banner_box.pack_start(banner_lbl, True, True, 0)
    rules_view.pack_start(banner_box, False, False, 0)

    # Rules List Card
    rules_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    rules_card.get_style_context().add_class("card")

    rules_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    rules_title = Gtk.Label(label="Configured Persistent Rules")
    rules_title.get_style_context().add_class("rule-name")
    rules_title.set_xalign(0)
    rules_header.pack_start(rules_title, True, True, 0)

    btn_add_rule = Gtk.Button(label="+ Add Custom Rule")
    btn_add_rule.get_style_context().add_class("btn-secondary")
    rules_header.pack_end(btn_add_rule, False, False, 0)

    btn_add_preset = Gtk.Button(label="+ Add Common Preset")
    btn_add_preset.get_style_context().add_class("btn-primary")
    rules_header.pack_end(btn_add_preset, False, False, 0)
    rules_card.pack_start(rules_header, False, False, 0)

    # Scrolled Window for Rules
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_min_content_height(240)

    rules_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    rules_list_box.set_margin_top(6)
    rules_list_box.set_margin_bottom(6)
    scrolled.add(rules_list_box)
    rules_card.pack_start(scrolled, True, True, 0)
    rules_view.pack_start(rules_card, True, True, 0)

    stack.add_named(rules_view, "rules")

    # =========================================================================
    # TAB 2: HYPRLAND PLUGINS & SECURITY
    # =========================================================================
    plugins_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    plugins_view.set_margin_top(14)
    plugins_view.set_margin_bottom(8)
    plugins_view.set_margin_start(16)
    plugins_view.set_margin_end(16)

    # Plugin security explainer card
    plugin_info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    plugin_info_box.get_style_context().add_class("banner-info")

    pl_info_icon = Gtk.Image.new_from_icon_name("system-software-install", Gtk.IconSize.BUTTON)
    plugin_info_box.pack_start(pl_info_icon, False, False, 0)

    pl_info_lbl = Gtk.Label(
        label="<b>Compositor Plugin Security:</b> Hyprland 0.55+ uses the <tt>plugin</tt> permission type to control which tools are allowed to load shared object (<tt>.so</tt>) extensions into the compositor process."
    )
    pl_info_lbl.set_use_markup(True)
    pl_info_lbl.set_line_wrap(True)
    pl_info_lbl.set_xalign(0)
    pl_info_lbl.get_style_context().add_class("banner-text")
    plugin_info_box.pack_start(pl_info_lbl, True, True, 0)
    plugins_view.pack_start(plugin_info_box, False, False, 0)

    # Scrolled container for plugins tab
    plugins_scrolled = Gtk.ScrolledWindow()
    plugins_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    plugins_scrolled.set_min_content_height(340)

    plugins_inner_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    plugins_scrolled.add(plugins_inner_vbox)

    # Section 1: Plugin Loaders (hyprpm, hyprctl)
    loaders_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    loaders_card.get_style_context().add_class("card")

    loaders_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    loaders_title = Gtk.Label(label="Plugin Loaders & Managers")
    loaders_title.get_style_context().add_class("rule-name")
    loaders_title.set_xalign(0)
    loaders_header.pack_start(loaders_title, True, True, 0)
    loaders_card.pack_start(loaders_header, False, False, 0)

    loaders_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    loaders_card.pack_start(loaders_list_box, False, False, 0)
    plugins_inner_vbox.pack_start(loaders_card, False, False, 0)

    # Section 2: Detected Installed Plugins
    detected_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    detected_card.get_style_context().add_class("card")

    detected_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    detected_title = Gtk.Label(label="Detected Hyprland Plugins")
    detected_title.get_style_context().add_class("rule-name")
    detected_title.set_xalign(0)
    detected_header.pack_start(detected_title, True, True, 0)

    btn_scan_plugins = Gtk.Button(label="🔄 Scan & Refresh")
    btn_scan_plugins.get_style_context().add_class("btn-secondary")
    detected_header.pack_end(btn_scan_plugins, False, False, 0)
    detected_card.pack_start(detected_header, False, False, 0)

    detected_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    detected_card.pack_start(detected_list_box, False, False, 0)
    plugins_inner_vbox.pack_start(detected_card, False, False, 0)

    # Section 3: Popular Plugins Quick-Add
    popular_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    popular_card.get_style_context().add_class("card")

    pop_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    pop_title = Gtk.Label(label="Official & Popular Plugins Catalog")
    pop_title.get_style_context().add_class("rule-name")
    pop_title.set_xalign(0)
    pop_header.pack_start(pop_title, True, True, 0)
    popular_card.pack_start(pop_header, False, False, 0)

    popular_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    popular_card.pack_start(popular_list_box, False, False, 0)
    plugins_inner_vbox.pack_start(popular_card, False, False, 0)

    plugins_view.pack_start(plugins_scrolled, True, True, 0)
    stack.add_named(plugins_view, "plugins")

    # =========================================================================
    # BOTTOM ACTION & STATUS BAR
    # =========================================================================
    status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    status_bar.set_margin_start(16)
    status_bar.set_margin_end(16)
    status_bar.set_margin_bottom(14)

    status_lbl = Gtk.Label(label="")
    status_lbl.set_xalign(0)
    status_lbl.get_style_context().add_class("window-subtitle")
    status_bar.pack_start(status_lbl, True, True, 0)

    btn_save = Gtk.Button(label="Save & Apply to Config")
    btn_save.get_style_context().add_class("btn-primary")
    status_bar.pack_end(btn_save, False, False, 0)

    main_vbox.pack_start(status_bar, False, False, 0)

    # Switch Tabs Function
    def switch_tab(tab_name):
        stack.set_visible_child_name(tab_name)
        if tab_name == "rules":
            btn_tab_rules.get_style_context().add_class("active")
            btn_tab_plugins.get_style_context().remove_class("active")
        else:
            btn_tab_plugins.get_style_context().add_class("active")
            btn_tab_rules.get_style_context().remove_class("active")

    btn_tab_rules.connect("clicked", lambda b: switch_tab("rules"))
    btn_tab_plugins.connect("clicked", lambda b: switch_tab("plugins"))

    def find_known_app(binary_str):
        for app in KNOWN_APPS:
            if app["id"] in binary_str or app["binary"] == binary_str:
                return app
        return None

    def refresh_rules_ui():
        for child in rules_list_box.get_children():
            rules_list_box.remove(child)

        if not cfg.rules:
            empty_lbl = Gtk.Label(label="No persistent permission rules configured.")
            empty_lbl.get_style_context().add_class("window-subtitle")
            empty_lbl.set_margin_top(30)
            empty_lbl.set_margin_bottom(30)
            rules_list_box.pack_start(empty_lbl, True, True, 0)
            rules_list_box.show_all()
            return

        for idx, rule in enumerate(cfg.rules):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.get_style_context().add_class("rule-row")

            app_meta = find_known_app(rule["binary"])
            icon_name = app_meta["icon"] if app_meta else ("system-software-install" if rule["type"] == "plugin" else "application-x-executable")
            app_label = app_meta["name"] if app_meta else Path(rule["binary"].split("/")[-1].replace(")", "").replace("(", "")).name

            row_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            row_box.pack_start(row_icon, False, False, 0)

            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label(label=app_label)
            name_lbl.set_xalign(0)
            name_lbl.get_style_context().add_class("rule-name")

            bin_lbl = Gtk.Label(label=rule["binary"])
            bin_lbl.set_xalign(0)
            bin_lbl.get_style_context().add_class("rule-binary")

            text_vbox.pack_start(name_lbl, False, False, 0)
            text_vbox.pack_start(bin_lbl, False, False, 0)
            row_box.pack_start(text_vbox, True, True, 0)

            # Type badge
            type_lbl = Gtk.Label(label=rule["type"])
            type_lbl.get_style_context().add_class("badge-type")
            row_box.pack_start(type_lbl, False, False, 0)

            # Mode Combobox
            mode_combo = Gtk.ComboBoxText()
            mode_combo.append("allow", "Allow")
            mode_combo.append("ask", "Ask")
            mode_combo.append("deny", "Deny")
            mode_combo.set_active_id(rule["mode"])

            def on_mode_changed(combo, r_idx=idx):
                cfg.rules[r_idx]["mode"] = combo.get_active_id()
                refresh_plugins_ui()

            mode_combo.connect("changed", on_mode_changed)
            row_box.pack_start(mode_combo, False, False, 0)

            # Delete button
            btn_del = Gtk.Button(label="✕")
            btn_del.get_style_context().add_class("btn-danger")
            btn_del.set_tooltip_text("Delete rule")

            def on_delete_clicked(btn, r_idx=idx):
                cfg.remove_rule(r_idx)
                refresh_rules_ui()
                refresh_plugins_ui()

            btn_del.connect("clicked", on_delete_clicked)
            row_box.pack_start(btn_del, False, False, 0)

            rules_list_box.pack_start(row_box, False, False, 0)

        rules_list_box.show_all()

    def refresh_plugins_ui():
        # 1. Refresh Loaders
        for child in loaders_list_box.get_children():
            loaders_list_box.remove(child)

        for loader in PLUGIN_LOADERS:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.get_style_context().add_class("rule-row")

            row_icon = Gtk.Image.new_from_icon_name(loader["icon"], Gtk.IconSize.LARGE_TOOLBAR)
            row_box.pack_start(row_icon, False, False, 0)

            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label(label=loader["name"])
            name_lbl.set_xalign(0)
            name_lbl.get_style_context().add_class("rule-name")

            desc_lbl = Gtk.Label(label=f"{loader['desc']} • {loader['recommended']}")
            desc_lbl.set_xalign(0)
            desc_lbl.get_style_context().add_class("rule-binary")

            text_vbox.pack_start(name_lbl, False, False, 0)
            text_vbox.pack_start(desc_lbl, False, False, 0)
            row_box.pack_start(text_vbox, True, True, 0)

            current_mode = cfg.get_rule_mode(loader["binary"], "plugin")
            mode_combo = Gtk.ComboBoxText()
            mode_combo.append("none", "Not Configured (Ask)")
            mode_combo.append("allow", "Allow")
            mode_combo.append("ask", "Ask")
            mode_combo.append("deny", "Deny")
            mode_combo.set_active_id(current_mode or "none")

            def on_loader_mode_changed(combo, l_bin=loader["binary"]):
                val = combo.get_active_id()
                if val == "none":
                    # Remove rule
                    for i in range(len(cfg.rules) - 1, -1, -1):
                        if cfg.rules[i]["type"] == "plugin" and l_bin in cfg.rules[i]["binary"]:
                            del cfg.rules[i]
                else:
                    cfg.add_or_update_rule(l_bin, "plugin", val)
                refresh_rules_ui()
                status_lbl.set_text(f"Updated rule for {l_bin}. Click Save to apply.")

            mode_combo.connect("changed", on_loader_mode_changed)
            row_box.pack_start(mode_combo, False, False, 0)
            loaders_list_box.pack_start(row_box, False, False, 0)

        # 2. Refresh Detected Plugins
        for child in detected_list_box.get_children():
            detected_list_box.remove(child)

        detected_plugins = detect_hyprland_plugins()
        if not detected_plugins:
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            empty_box.set_margin_top(12)
            empty_box.set_margin_bottom(12)

            no_pl_lbl = Gtk.Label(label="No third-party Hyprland plugins currently loaded or compiled in ~/.local/share/hyprpm.")
            no_pl_lbl.get_style_context().add_class("window-subtitle")
            empty_box.pack_start(no_pl_lbl, False, False, 0)

            hint_lbl = Gtk.Label(label="When plugins are loaded or built, they will automatically be detected and listed here.")
            hint_lbl.get_style_context().add_class("banner-text")
            empty_box.pack_start(hint_lbl, False, False, 0)
            detected_list_box.pack_start(empty_box, False, False, 0)
        else:
            for pl in detected_plugins:
                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                row_box.get_style_context().add_class("rule-row")

                row_icon = Gtk.Image.new_from_icon_name(pl["icon"], Gtk.IconSize.LARGE_TOOLBAR)
                row_box.pack_start(row_icon, False, False, 0)

                text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                title_line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                name_lbl = Gtk.Label(label=pl["name"])
                name_lbl.get_style_context().add_class("rule-name")
                title_line.pack_start(name_lbl, False, False, 0)

                # Status tag
                st_badge = Gtk.Label(label="Active" if pl["status"] == "loaded" else "Installed")
                st_badge.get_style_context().add_class("badge-loaded" if pl["status"] == "loaded" else "badge-installed")
                title_line.pack_start(st_badge, False, False, 0)
                text_vbox.pack_start(title_line, False, False, 0)

                path_lbl = Gtk.Label(label=f"{pl['path']} ({pl['description']})")
                path_lbl.set_xalign(0)
                path_lbl.get_style_context().add_class("rule-binary")
                text_vbox.pack_start(path_lbl, False, False, 0)
                row_box.pack_start(text_vbox, True, True, 0)

                # Permission Selector
                curr_mode = cfg.get_rule_mode(pl["path"], "plugin")
                mode_combo = Gtk.ComboBoxText()
                mode_combo.append("none", "Default (Ask)")
                mode_combo.append("allow", "Allow")
                mode_combo.append("ask", "Ask")
                mode_combo.append("deny", "Deny")
                mode_combo.set_active_id(curr_mode or "none")

                def on_plugin_mode_changed(combo, pl_path=pl["path"]):
                    val = combo.get_active_id()
                    if val == "none":
                        for i in range(len(cfg.rules) - 1, -1, -1):
                            if cfg.rules[i]["type"] == "plugin" and pl_path in cfg.rules[i]["binary"]:
                                del cfg.rules[i]
                    else:
                        cfg.add_or_update_rule(pl_path, "plugin", val)
                    refresh_rules_ui()
                    status_lbl.set_text(f"Updated rule for {pl_path}. Click Save to apply.")

                mode_combo.connect("changed", on_plugin_mode_changed)
                row_box.pack_start(mode_combo, False, False, 0)
                detected_list_box.pack_start(row_box, False, False, 0)

        # 3. Refresh Catalog of Popular Plugins
        for child in popular_list_box.get_children():
            popular_list_box.remove(child)

        for pop in POPULAR_PLUGINS:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.get_style_context().add_class("rule-row")

            row_icon = Gtk.Image.new_from_icon_name("system-software-install", Gtk.IconSize.LARGE_TOOLBAR)
            row_box.pack_start(row_icon, False, False, 0)

            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label(label=f"{pop['name']} ({pop['repo']})")
            name_lbl.set_xalign(0)
            name_lbl.get_style_context().add_class("rule-name")

            desc_lbl = Gtk.Label(label=pop["desc"])
            desc_lbl.set_xalign(0)
            desc_lbl.get_style_context().add_class("rule-binary")

            text_vbox.pack_start(name_lbl, False, False, 0)
            text_vbox.pack_start(desc_lbl, False, False, 0)
            row_box.pack_start(text_vbox, True, True, 0)

            curr_mode = cfg.get_rule_mode(pop["binary"], "plugin")
            if curr_mode:
                badge = Gtk.Label(label=curr_mode.upper())
                badge.get_style_context().add_class(f"badge-{curr_mode}")
                row_box.pack_start(badge, False, False, 0)
            else:
                btn_preauth = Gtk.Button(label="+ Pre-Authorize")
                btn_preauth.get_style_context().add_class("btn-secondary")
                def on_preauth_clicked(btn, p_bin=pop["binary"], p_name=pop["name"]):
                    cfg.add_or_update_rule(p_bin, "plugin", "allow")
                    refresh_rules_ui()
                    refresh_plugins_ui()
                    status_lbl.set_text(f"Pre-authorized '{p_name}'. Click Save to apply.")
                btn_preauth.connect("clicked", on_preauth_clicked)
                row_box.pack_start(btn_preauth, False, False, 0)

            popular_list_box.pack_start(row_box, False, False, 0)

        loaders_list_box.show_all()
        detected_list_box.show_all()
        popular_list_box.show_all()

    btn_scan_plugins.connect("clicked", lambda b: refresh_plugins_ui())

    def show_add_custom_dialog():
        dialog = Gtk.Dialog(
            title="Add Custom Permission Rule",
            transient_for=win,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 240)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        bin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bin_entry = Gtk.Entry()
        bin_entry.set_placeholder_text("e.g. /usr/(bin|local/bin)/hyprlock or /usr/bin/grim")
        bin_box.pack_start(bin_entry, True, True, 0)

        btn_browse = Gtk.Button(label="Browse...")
        def on_browse_clicked(btn):
            chooser = Gtk.FileChooserNative.new(
                "Select Binary or Plugin", win, Gtk.FileChooserAction.OPEN, "_Select", "_Cancel"
            )
            chooser.set_current_folder("/usr/bin")
            res = chooser.run()
            if res == Gtk.ResponseType.ACCEPT:
                fpath = chooser.get_filename()
                if fpath:
                    if fpath.startswith("/usr/bin/"):
                        app = fpath[len("/usr/bin/"):]
                        bin_entry.set_text(f"/usr/(bin|local/bin)/{app}")
                    else:
                        bin_entry.set_text(fpath)
            chooser.destroy()

        btn_browse.connect("clicked", on_browse_clicked)
        bin_box.pack_start(btn_browse, False, False, 0)

        box.pack_start(Gtk.Label(label="Binary Executable Path or Regex:", xalign=0), False, False, 0)
        box.pack_start(bin_box, False, False, 0)

        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        type_combo = Gtk.ComboBoxText()
        type_combo.append("screencopy", "screencopy (Screen Capture & Recording)")
        type_combo.append("plugin", "plugin (Hyprland Plugins)")
        type_combo.set_active(0)
        type_box.pack_start(type_combo, True, True, 0)

        box.pack_start(Gtk.Label(label="Permission Type:", xalign=0), False, False, 0)
        box.pack_start(type_box, False, False, 0)

        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        mode_combo = Gtk.ComboBoxText()
        mode_combo.append("allow", "allow (Permit always without prompt)")
        mode_combo.append("ask", "ask (Always prompt before permitting)")
        mode_combo.append("deny", "deny (Always reject)")
        mode_combo.set_active(0)
        mode_box.pack_start(mode_combo, True, True, 0)

        box.pack_start(Gtk.Label(label="Permission Mode:", xalign=0), False, False, 0)
        box.pack_start(mode_box, False, False, 0)

        dialog.show_all()
        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            b_val = bin_entry.get_text().strip()
            t_val = type_combo.get_active_id() or "screencopy"
            m_val = mode_combo.get_active_id() or "allow"
            if b_val:
                cfg.add_or_update_rule(b_val, t_val, m_val)
                refresh_rules_ui()
                refresh_plugins_ui()
                status_lbl.set_text(f"Added rule for '{b_val}'. Remember to Save!")
        dialog.destroy()

    def show_add_preset_dialog():
        dialog = Gtk.Dialog(
            title="Add Common Application Preset",
            transient_for=win,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Add Selected", Gtk.ResponseType.OK
        )
        dialog.set_default_size(520, 360)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        info_lbl = Gtk.Label(label="Select a standard application preset to automatically configure its permission rule:")
        info_lbl.set_line_wrap(True)
        info_lbl.set_xalign(0)
        box.pack_start(info_lbl, False, False, 0)

        store = Gtk.ListStore(str, str, str, str, str, str)
        for app in KNOWN_APPS:
            store.append([app["id"], app["name"], app["binary"], app["type"], app["desc"], app["icon"]])

        tree = Gtk.TreeView(model=store)
        tree.set_headers_visible(False)

        col = Gtk.TreeViewColumn("App")
        icon_cell = Gtk.CellRendererPixbuf()
        col.pack_start(icon_cell, False)
        col.add_attribute(icon_cell, "icon-name", 5)

        text_cell = Gtk.CellRendererText()
        col.pack_start(text_cell, True)

        def text_data_func(column, cell, model, it, data):
            name = model.get_value(it, 1)
            desc = model.get_value(it, 4)
            cell.set_property("markup", f"<b>{name}</b>\n<small>{desc}</small>")

        col.set_cell_data_func(text_cell, text_data_func)
        tree.append_column(col)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(tree)
        box.pack_start(scroll, True, True, 0)

        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        mode_box.pack_start(Gtk.Label(label="Mode:"), False, False, 0)
        mode_combo = Gtk.ComboBoxText()
        mode_combo.append("allow", "allow")
        mode_combo.append("ask", "ask")
        mode_combo.append("deny", "deny")
        mode_combo.set_active(0)
        mode_box.pack_start(mode_combo, False, False, 0)
        box.pack_start(mode_box, False, False, 0)

        dialog.show_all()
        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            selection = tree.get_selection()
            model, it = selection.get_selected()
            if it:
                binary = model.get_value(it, 2)
                ptype = model.get_value(it, 3)
                mode = mode_combo.get_active_id() or "allow"
                cfg.add_or_update_rule(binary, ptype, mode)
                refresh_rules_ui()
                refresh_plugins_ui()
                status_lbl.set_text(f"Added preset for {model.get_value(it, 1)}. Click Save to apply.")
        dialog.destroy()

    def on_save_clicked(btn):
        cfg.enforce_permissions = enforce_switch.get_active()
        try:
            cfg.save()
            status_lbl.set_text(f"Saved {len(cfg.rules)} rules to {PERMISSIONS_LUA.name} successfully!")
            subprocess.run([
                "notify-send",
                "-a", "Hyprland Permissions",
                "-i", "permission-manager",
                "Permissions Saved",
                f"Successfully saved rules to {PERMISSIONS_LUA.name}. Hyprland restart required to apply."
            ], check=False)
        except Exception as e:
            status_lbl.set_text(f"Error saving: {e}")

    def on_reload_clicked(btn):
        cfg.load()
        enforce_switch.set_active(cfg.enforce_permissions)
        refresh_rules_ui()
        refresh_plugins_ui()
        status_lbl.set_text("Reloaded configuration from disk.")

    btn_add_rule.connect("clicked", lambda b: show_add_custom_dialog())
    btn_add_preset.connect("clicked", lambda b: show_add_preset_dialog())
    btn_save.connect("clicked", on_save_clicked)
    btn_reload.connect("clicked", on_reload_clicked)

    win.connect("destroy", Gtk.main_quit)
    refresh_rules_ui()
    refresh_plugins_ui()
    win.show_all()
    Gtk.main()


def cli_main():
    parser = argparse.ArgumentParser(description="Hyprland Permissions & Plugins Manager CLI & GUI")
    parser.add_argument("--gui", action="store_true", help="Launch Graphical GTK3 Manager")
    parser.add_argument("--list", action="store_true", help="List all persistent permission rules")
    parser.add_argument("--plugins", action="store_true", help="Detect and list Hyprland plugins")
    parser.add_argument("--add", nargs=3, metavar=("BINARY", "TYPE", "MODE"),
                        help="Add or update rule: e.g. --add '/usr/bin/hyprlock' screencopy allow")
    parser.add_argument("--remove", metavar="BINARY", help="Remove rule matching binary")
    parser.add_argument("--enforce", choices=["true", "false", "toggle"], help="Set or toggle enforce_permissions")

    args = parser.parse_args()

    if len(sys.argv) == 1 or args.gui:
        launch_gui()
        return

    cfg = PermissionConfig()

    if args.plugins:
        plugins = detect_hyprland_plugins()
        print(f"Detected Hyprland Plugins: {len(plugins)}")
        print("-" * 75)
        for idx, p in enumerate(plugins, 1):
            rule_mode = cfg.get_rule_mode(p["path"], "plugin") or "UNSET"
            print(f"[{idx}] {p['name']} ({p['status']}) - Source: {p['source']}")
            print(f"    Path: {p['path']}")
            print(f"    Permission Rule: {rule_mode}")
        print("-" * 75)
        print("Configured Plugin Loaders:")
        for ldr in PLUGIN_LOADERS:
            mode = cfg.get_rule_mode(ldr["binary"], "plugin") or "UNSET"
            print(f"    {ldr['name']} ({ldr['binary']}): {mode}")
        return

    if args.list:
        print(f"Ecosystem Enforcement: {'ENABLED' if cfg.enforce_permissions else 'DISABLED'}")
        print(f"File: {cfg.file_path}")
        print("-" * 75)
        print(f"{'#':<3} {'MODE':<8} {'TYPE':<12} {'BINARY PATTERN'}")
        print("-" * 75)
        for idx, rule in enumerate(cfg.rules, 1):
            print(f"{idx:<3} {rule['mode'].upper():<8} {rule['type']:<12} {rule['binary']}")
        print("-" * 75)
        return

    modified = False

    if args.enforce:
        if args.enforce == "toggle":
            cfg.enforce_permissions = not cfg.enforce_permissions
        else:
            cfg.enforce_permissions = (args.enforce == "true")
        print(f"Enforce permissions set to: {cfg.enforce_permissions}")
        modified = True

    if args.add:
        binary, ptype, mode = args.add
        cfg.add_or_update_rule(binary, ptype, mode)
        print(f"Added rule: {binary} [{ptype}] -> {mode}")
        modified = True

    if args.remove:
        found = False
        for idx in range(len(cfg.rules) - 1, -1, -1):
            if cfg.rules[idx]["binary"] == args.remove:
                del cfg.rules[idx]
                found = True
        if found:
            print(f"Removed rule(s) matching: {args.remove}")
            modified = True
        else:
            print(f"No rule found matching: {args.remove}", file=sys.stderr)

    if modified:
        cfg.save()
        print("Permissions saved successfully. Please restart Hyprland to apply.")


if __name__ == "__main__":
    cli_main()
