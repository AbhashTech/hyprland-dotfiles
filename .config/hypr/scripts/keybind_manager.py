#!/usr/bin/env python3
"""
=============================================================================
Hyprland Keybindings Manager (Desktop GUI & CLI)
=============================================================================
A modern GTK3 utility that dynamically adapts to the active system theme to:
- Inspect and manage default Hyprland keybindings
- Override or disable/enable default keybindings non-destructively
- Add, edit, delete, and enable/disable custom user keybindings
- Manage Quickshell custom and built-in plugin keybindings
- Capture physical keypresses interactively to record shortcut chords
- Perform real-time conflict detection across defaults, custom binds, plugins, and live compositor
- Write all modifications exclusively to ~/.config/hypr/user/keybinds.lua
- Apply changes live instantly with hyprctl reload
"""

import os
import sys
import re
import json
import shutil
import subprocess
from pathlib import Path

# Paths
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
DOTFILES_DIR = HOME / ".dotfiles"
DOTFILES_CONFIG_DIR = DOTFILES_DIR / ".config"
MODULE_KEYBINDS_PATH = CONFIG_DIR / "hypr" / "modules" / "keybinds.lua"
DOTFILES_MODULE_KEYBINDS_PATH = DOTFILES_CONFIG_DIR / "hypr" / "modules" / "keybinds.lua"
USER_KEYBINDS_PATH = CONFIG_DIR / "hypr" / "user" / "keybinds.lua"
QUICKSHELL_CUSTOM_PLUGINS_DIR = CONFIG_DIR / "quickshell" / "custom_plugins"
QUICKSHELL_BUILTIN_PLUGINS_DIR = CONFIG_DIR / "quickshell" / "plugins"

KEY_ALIASES = {
    "ret": "Return", "enter": "Return", "return": "Return",
    "esc": "Escape", "escape": "Escape",
    "spc": "space", "space": "space",
    "backspace": "BackSpace", "bs": "BackSpace",
    "tab": "Tab", "iso_left_tab": "Tab",
    "del": "Delete", "delete": "Delete",
    "ins": "Insert", "insert": "Insert",
    "prior": "Page_Up", "page_up": "Page_Up", "pgup": "Page_Up",
    "next": "Page_Down", "page_down": "Page_Down", "pgdn": "Page_Down",
    "home": "Home", "end": "End",
    "left": "left", "right": "right", "up": "up", "down": "down",
    # Multimedia & Hardware keys (GDK keyval name -> XKB keysym)
    "mail": "XF86Mail",
    "calculator": "XF86Calculator",
    "calc": "XF86Calculator",
    "homepage": "XF86HomePage", "www": "XF86HomePage",
    "search": "XF86Search",
    "explorer": "XF86Explorer", "mycomputer": "XF86Explorer",
    "tools": "XF86Tools",
    "audioraisevolume": "XF86AudioRaiseVolume", "volumeup": "XF86AudioRaiseVolume",
    "audiolowervolume": "XF86AudioLowerVolume", "volumedown": "XF86AudioLowerVolume",
    "audiomute": "XF86AudioMute", "mute": "XF86AudioMute",
    "audiomicmute": "XF86AudioMicMute", "micmute": "XF86AudioMicMute",
    "audioplay": "XF86AudioPlay", "play": "XF86AudioPlay",
    "audiopause": "XF86AudioPause",
    "audiostop": "XF86AudioStop", "stop": "XF86AudioStop",
    "audioprev": "XF86AudioPrev", "prev": "XF86AudioPrev",
    "audionext": "XF86AudioNext",
    "audiorewind": "XF86AudioRewind",
    "audioforward": "XF86AudioForward",
    "audiorecord": "XF86AudioRecord",
    "monbrightnessup": "XF86MonBrightnessUp", "brightnessup": "XF86MonBrightnessUp",
    "monbrightnessdown": "XF86MonBrightnessDown", "brightnessdown": "XF86MonBrightnessDown",
    "kbdbrightnessup": "XF86KbdBrightnessUp",
    "kbdbrightnessdown": "XF86KbdBrightnessDown",
    "display": "XF86Display",
    "wlan": "XF86WLAN", "wifi": "XF86WLAN",
    "bluetooth": "XF86Bluetooth",
    "poweroff": "XF86PowerOff", "power": "XF86PowerOff",
    "sleep": "XF86Sleep",
    "standby": "XF86Standby",
    "screensaver": "XF86ScreenSaver",
    "touchpadtoggle": "XF86TouchpadToggle",
    "touchpadon": "XF86TouchpadOn",
    "touchpadoff": "XF86TouchpadOff",
    "favorites": "XF86Favorites",
    "webcam": "XF86WebCam",
    "messenger": "XF86Messenger",
    "launch0": "XF86Launch0", "launch1": "XF86Launch1", "launch2": "XF86Launch2",
    "launch3": "XF86Launch3", "launch4": "XF86Launch4", "launch5": "XF86Launch5",
    "launch6": "XF86Launch6", "launch7": "XF86Launch7", "launch8": "XF86Launch8",
    "launch9": "XF86Launch9",
}


def get_active_theme_colors():
    """Load colors from active theme JSON file with fallback."""
    cache_state = HOME / ".cache" / "hypr_theme_state.json"
    current_txt = HOME / ".cache" / "current_theme"
    theme_id = "gruvbox-light"

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
    """Calculate WCAG high-contrast foreground color based on background luminance."""
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


def run_cmd(cmd):
    """Execute command safely and return output."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.stdout.strip()
    except Exception:
        return ""


def clean_comment(text):
    """Strip comment markers and whitespace."""
    text = re.sub(r"^[-\s#]+", "", text).strip()
    text = re.sub(r"[-=]{3,}", "", text).strip()
    return text


def normalize_key(k):
    """Normalize single key string (e.g. Return, space, F12, uppercase letters)."""
    k_strip = k.strip()
    k_low = k_strip.lower()
    if k_low in KEY_ALIASES:
        return KEY_ALIASES[k_low]
    if len(k_strip) == 1:
        return k_strip.upper()
    if k_low.startswith("f") and k_low[1:].isdigit():
        return f"F{k_low[1:]}"
    return k_strip


def normalize_keybind(raw_key):
    """
    Canonicalize key combination string into strict Hyprland chord syntax:
    SUPER + CTRL + ALT + SHIFT + KEY
    """
    if not raw_key:
        return ""
    s = raw_key.replace('mainMod .. "', 'SUPER').replace("mainMod .. '", 'SUPER')
    s = s.replace('"', '').replace("'", "").replace(' .. ', ' ')
    s = s.replace("mainMod", "SUPER").strip()

    parts = re.split(r'[\s+]+', s)
    mods = []
    keys = []
    for p in parts:
        pu = p.upper()
        if pu in ["SUPER", "MOD4", "WIN", "LOGO", "META"]:
            if "SUPER" not in mods:
                mods.append("SUPER")
        elif pu in ["CTRL", "CONTROL"]:
            if "CTRL" not in mods:
                mods.append("CTRL")
        elif pu in ["ALT", "MOD1"]:
            if "ALT" not in mods:
                mods.append("ALT")
        elif pu in ["SHIFT"]:
            if "SHIFT" not in mods:
                mods.append("SHIFT")
        elif p:
            keys.append(normalize_key(p))

    ordered_mods = [m for m in ["SUPER", "CTRL", "ALT", "SHIFT"] if m in mods]
    return " + ".join(ordered_mods + keys)


def normalize_key_str(raw_key):
    """Alias for backward compatibility."""
    return normalize_keybind(raw_key)


def split_lua_args(arg_str):
    """Split comma-separated arguments respecting nested parentheses, brackets, and quotes."""
    args = []
    current = []
    depth = 0
    in_quote = None
    for ch in arg_str:
        if in_quote:
            if ch == in_quote:
                in_quote = None
            current.append(ch)
        elif ch in ('"', "'"):
            in_quote = ch
            current.append(ch)
        elif ch in ('(', '{', '['):
            depth += 1
            current.append(ch)
        elif ch in (')', '}', ']'):
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            args.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        args.append(''.join(current).strip())
    return args


def parse_default_keybinds():
    """Extract default keybinds from modules/keybinds.lua."""
    target = MODULE_KEYBINDS_PATH if MODULE_KEYBINDS_PATH.is_file() else DOTFILES_MODULE_KEYBINDS_PATH
    if not target.is_file():
        return []

    lines = target.read_text(encoding="utf-8").splitlines()
    entries = []
    current_category = "🖥️ Core Applications & Essential Controls"
    pending_comments = []
    last_description = ""

    for line in lines:
        sline = line.strip()
        if not sline:
            pending_comments = []
            continue

        if sline.startswith("--"):
            comment = clean_comment(sline)
            if any(emoji in comment for emoji in ["🖥️", "🔔", "⚡", "🗂️", "📐", "🔊", "☀️", "📸", "🎨", "📁"]) or "@category" in comment.lower():
                current_category = comment
                pending_comments = []
                last_description = ""
            elif comment and not comment.startswith("hl."):
                pending_comments.append(comment)
            continue

        if sline.startswith("hl.bind("):
            m = re.match(r"^hl\.bind\((.+)\)(?:.*)$", sline)
            if m:
                inner = m.group(1).strip()
                args = split_lua_args(inner)
                if len(args) >= 2:
                    raw_key = args[0]
                    action = args[1]
                    flags = args[2] if len(args) > 2 else ""

                    norm_key = normalize_keybind(raw_key)
                    desc = " ".join(pending_comments) if pending_comments else last_description or "Execute Action"
                    last_description = desc
                    pending_comments = []

                    entries.append({
                        "id": f"def:{norm_key}",
                        "raw_key": raw_key,
                        "key": norm_key,
                        "action": action,
                        "flags": flags,
                        "desc": desc,
                        "category": current_category,
                        "type": "default"
                    })

    return entries


def discover_all_plugins():
    """Discover custom and built-in Quickshell plugins with manifests and keybinding states."""
    plugins = []
    seen_ids = set()

    # 1. Custom plugins
    if QUICKSHELL_CUSTOM_PLUGINS_DIR.is_dir():
        for p in sorted(QUICKSHELL_CUSTOM_PLUGINS_DIR.iterdir()):
            if p.is_dir() and not p.name.startswith("."):
                manifest_file = p / "manifest.json"
                keybind_file = p / "keybinding.json"
                mdata = {}
                if manifest_file.is_file():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            mdata = json.load(f)
                    except Exception:
                        pass
                kdata = {}
                if keybind_file.is_file():
                    try:
                        with open(keybind_file, "r", encoding="utf-8") as f:
                            kdata = json.load(f)
                    except Exception:
                        pass

                p_id = mdata.get("id") or p.name
                seen_ids.add(p_id)
                k_str = normalize_keybind(kdata.get("keybind", ""))
                plugins.append({
                    "id": p_id,
                    "name": mdata.get("name") or p.name.replace("-", " ").title(),
                    "desc": mdata.get("description") or "Custom Quickshell plugin widget/modal",
                    "dir": str(p),
                    "is_custom": True,
                    "key": k_str,
                    "action": f'hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh {p_id}")',
                    "enabled": kdata.get("enabled", True) if k_str else False
                })

    # 2. Builtin plugins
    if QUICKSHELL_BUILTIN_PLUGINS_DIR.is_dir():
        for p in sorted(QUICKSHELL_BUILTIN_PLUGINS_DIR.iterdir()):
            if p.is_dir() and not p.name.startswith("."):
                manifest_file = p / "manifest.json"
                keybind_file = p / "keybinding.json"
                mdata = {}
                if manifest_file.is_file():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            mdata = json.load(f)
                    except Exception:
                        pass
                kdata = {}
                if keybind_file.is_file():
                    try:
                        with open(keybind_file, "r", encoding="utf-8") as f:
                            kdata = json.load(f)
                    except Exception:
                        pass

                p_id = mdata.get("id") or p.name.replace("-", "_")
                if p_id in seen_ids:
                    continue
                seen_ids.add(p_id)

                k_str = normalize_keybind(kdata.get("keybind", ""))
                if p_id == "plugin_manager" and not k_str:
                    k_str = "SUPER + ALT + P"

                plugins.append({
                    "id": p_id,
                    "name": mdata.get("name") or p.name.replace("-", " ").title(),
                    "desc": mdata.get("description") or f"Quickshell built-in {p.name} service",
                    "dir": str(p),
                    "is_custom": False,
                    "key": k_str,
                    "action": f'hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh {p_id}")',
                    "enabled": True if k_str else False
                })

    return plugins


def get_live_hyprctl_binds():
    """Extract active keybindings from the live Hyprland compositor (hyprctl binds -j)."""
    binds = {}
    try:
        res = subprocess.run(["hyprctl", "binds", "-j"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            for b in json.loads(res.stdout):
                modmask = b.get("modmask", 0)
                mods = []
                if modmask & 64: mods.append("SUPER")
                if modmask & 4:  mods.append("CTRL")
                if modmask & 8:  mods.append("ALT")
                if modmask & 1:  mods.append("SHIFT")
                kname = normalize_key(b.get("key", ""))
                if kname:
                    norm = normalize_keybind(" + ".join(mods + [kname]))
                    disp = b.get("dispatcher", "")
                    arg = b.get("arg", "")
                    desc = b.get("description", "") or (f"{disp} {arg}".strip() if disp else "Hyprland Action")
                    binds[norm] = desc
    except Exception:
        pass
    return binds


def find_keybind_conflict(candidate, exclude_id=None, default_binds=None, disabled_defaults=None,
                           overrides=None, custom_binds=None, plugin_binds=None, live_binds=None):
    """
    Check if candidate key combination is already claimed by any:
    - Default keybind (unless disabled or overridden)
    - Overridden default keybind
    - Custom user keybind
    - Custom/built-in plugin keybind
    - Live Hyprland compositor binding
    Returns a dict with conflict details or None if available.
    """
    norm = normalize_keybind(candidate)
    if not norm:
        return None

    # 1. Check Custom Keybinds
    for cb in (custom_binds or []):
        if not cb.get("enabled", True):
            continue
        if exclude_id and cb.get("id") == exclude_id:
            continue
        if normalize_keybind(cb.get("key", "")) == norm:
            return {
                "type": "custom",
                "name": cb.get("desc", "Custom Keybind"),
                "detail": f"Custom Keybind '{cb.get('desc', 'Custom')}'",
                "key": norm
            }

    # 2. Check Plugin Keybinds
    for pid, pb in (plugin_binds or {}).items():
        if not pb.get("enabled", True):
            continue
        if exclude_id and (exclude_id == pid or exclude_id == f"plugin:{pid}"):
            continue
        if normalize_keybind(pb.get("key", "")) == norm:
            pname = pb.get("name") or pb.get("desc") or pid
            return {
                "type": "plugin",
                "name": pname,
                "detail": f"Plugin '{pname}'",
                "key": norm
            }

    # 3. Check Overridden Defaults
    for orig_k, ov in (overrides or {}).items():
        if exclude_id and (exclude_id == orig_k or exclude_id == f"def:{orig_k}"):
            continue
        if normalize_keybind(ov.get("new_key", "")) == norm:
            return {
                "type": "override",
                "name": ov.get("desc", orig_k),
                "detail": f"Overridden Default '{ov.get('desc', orig_k)}' (replacing {orig_k})",
                "key": norm
            }

    # 4. Check Default Keybinds
    for db in (default_binds or []):
        orig_k = db.get("key", "")
        if exclude_id and (exclude_id == orig_k or exclude_id == f"def:{orig_k}"):
            continue
        if disabled_defaults and orig_k in disabled_defaults:
            continue
        if overrides and orig_k in overrides:
            continue
        if normalize_keybind(orig_k) == norm:
            return {
                "type": "default",
                "name": db.get("desc", "Default Shortcut"),
                "detail": f"Default Keybind '{db.get('desc', 'Default')}'",
                "key": norm
            }

    # 5. Check Live Compositor Bindings
    if live_binds and norm in live_binds:
        desc = live_binds[norm]
        if not (desc.startswith("__lua") or "toggle_plugin" in desc):
            return {
                "type": "system",
                "name": desc,
                "detail": f"System Binding '{desc}'",
                "key": norm
            }

    return None


def load_user_keybinds_state():
    """
    Parse ~/.config/hypr/user/keybinds.lua and discover Quickshell plugins.
    Returns:
      disabled_defaults: set of normalized keys that are disabled (hl.unbind)
      overrides: dict mapping normalized default key -> custom key & action
      custom_binds: list of custom keybind dicts
      plugin_binds: dict mapping plugin_id -> plugin info dict
    """
    disabled_defaults = set()
    overrides = {}
    custom_binds = []
    plugin_binds = {}

    if USER_KEYBINDS_PATH.is_file():
        lines = USER_KEYBINDS_PATH.read_text(encoding="utf-8").splitlines()
        for line in lines:
            sline = line.strip()
            if not sline:
                continue

            # 1. Unbinds for disabled defaults or overrides
            if sline.startswith("hl.unbind("):
                m = re.search(r'hl\.unbind\(\s*["\']([^"\']+)["\']\s*\)', sline)
                if m:
                    unbound_key = normalize_keybind(m.group(1))
                    if "@disabled" in sline:
                        disabled_defaults.add(unbound_key)

            # 2. Overrides, Custom binds, or Plugin binds
            is_disabled = sline.startswith("-- [DISABLED]")
            code_part = sline.replace("-- [DISABLED]", "").strip()

            if code_part.startswith("hl.bind("):
                parts = code_part.split("--", 1)
                bind_code = parts[0].strip()
                trailing = parts[1].strip() if len(parts) > 1 else ""

                bm = re.match(r"^hl\.bind\((.+)\)$", bind_code)
                if bm:
                    args = split_lua_args(bm.group(1).strip())
                    if len(args) >= 2:
                        raw_k = args[0]
                        act = args[1]
                        flg = args[2] if len(args) > 2 else ""
                        norm_k = normalize_keybind(raw_k)

                        plugin_match = re.search(r'@plugin:([^|]+)', trailing)
                        ov_match = re.search(r'@override:([^|]+)', trailing)
                        desc_match = re.search(r'@desc:([^|]+)', trailing)
                        cat_match = re.search(r'@category:([^|]+)', trailing)

                        desc = desc_match.group(1).strip() if desc_match else ""
                        cat = cat_match.group(1).strip() if cat_match else "Personal Shortcuts"

                        if plugin_match:
                            p_id = plugin_match.group(1).strip()
                            plugin_binds[p_id] = {
                                "id": p_id,
                                "name": desc or p_id.replace("_", " ").replace("-", " ").title(),
                                "key": norm_k,
                                "action": act,
                                "desc": desc,
                                "enabled": not is_disabled,
                                "is_custom": True,
                            }
                        elif ov_match:
                            orig_key = normalize_keybind(ov_match.group(1).strip())
                            overrides[orig_key] = {
                                "orig_key": orig_key,
                                "new_key": norm_k,
                                "action": act,
                                "flags": flg,
                                "desc": desc,
                            }
                        elif "@custom" in trailing:
                            custom_binds.append({
                                "id": f"custom:{norm_k}:{desc}",
                                "key": norm_k,
                                "action": act,
                                "flags": flg,
                                "desc": desc or "Custom User Shortcut",
                                "category": cat,
                                "enabled": not is_disabled,
                                "type": "custom"
                            })

    # Merge with plugins discovered on disk
    disk_plugins = discover_all_plugins()
    for pl in disk_plugins:
        p_id = pl["id"]
        if p_id not in plugin_binds:
            plugin_binds[p_id] = pl
        else:
            plugin_binds[p_id]["dir"] = pl.get("dir", "")
            plugin_binds[p_id]["is_custom"] = pl.get("is_custom", True)
            if not plugin_binds[p_id].get("desc"):
                plugin_binds[p_id]["desc"] = pl.get("desc", "")
            if not plugin_binds[p_id].get("name") or plugin_binds[p_id]["name"] == p_id:
                plugin_binds[p_id]["name"] = pl.get("name", p_id)

    return disabled_defaults, overrides, custom_binds, plugin_binds


def save_user_keybinds_state(disabled_defaults, overrides, custom_binds, plugin_binds=None):
    """
    Serialize all user keybinding configurations cleanly to:
    ~/.config/hypr/user/keybinds.lua
    and sync individual plugin keybinding.json files.
    """
    USER_KEYBINDS_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "--------------------------------------------------------------------------------",
        "-- User Personal Keybindings Configuration (Untracked)",
        "--------------------------------------------------------------------------------",
        "-- Managed by Hyprland Keybindings Manager GUI",
        "",
        'local programs = require("modules.programs")',
        'local mainMod = "SUPER"',
        "",
    ]

    # 1. Disabled defaults
    if disabled_defaults:
        lines.append("-- =============================================================================")
        lines.append("-- 🚫 Disabled Default Keybindings")
        lines.append("-- =============================================================================")
        for k in sorted(disabled_defaults):
            lines.append(f'hl.unbind("{k}") -- @disabled:true')
        lines.append("")

    # 2. Overridden defaults
    if overrides:
        lines.append("-- =============================================================================")
        lines.append("-- 🔄 Overridden Default Keybindings")
        lines.append("-- =============================================================================")
        for orig_k, ov in sorted(overrides.items()):
            new_k = normalize_keybind(ov["new_key"])
            act = ov["action"]
            flg = f", {ov['flags']}" if ov.get("flags") else ""
            desc = ov.get("desc", "")
            lines.append(f'hl.unbind("{orig_k}")')
            lines.append(f'hl.bind("{new_k}", {act}{flg}) -- @override:{orig_k} | @desc:{desc}')
        lines.append("")

    # 3. Custom keybindings
    if custom_binds:
        lines.append("-- =============================================================================")
        lines.append("-- ⚡ Custom User Keybindings")
        lines.append("-- =============================================================================")
        for cb in custom_binds:
            k = normalize_keybind(cb["key"])
            act = cb["action"]
            flg = f", {cb['flags']}" if cb.get("flags") else ""
            desc = cb.get("desc", "Custom Action")
            cat = cb.get("category", "Personal Shortcuts")
            prefix = "" if cb.get("enabled", True) else "-- [DISABLED] "
            lines.append(f'{prefix}hl.bind("{k}", {act}{flg}) -- @custom | @desc:{desc} | @category:{cat}')
        lines.append("")

    # 4. Quickshell Plugin keybindings
    if plugin_binds:
        lines.append("-- =============================================================================")
        lines.append("-- 🧩 Quickshell Plugin Keybindings")
        lines.append("-- =============================================================================")
        for p_id, pb in sorted(plugin_binds.items()):
            k = normalize_keybind(pb.get("key", ""))
            if k:
                act = pb.get("action") or f'hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh {p_id}")'
                desc = pb.get("name") or pb.get("desc") or p_id
                prefix = "" if pb.get("enabled", True) else "-- [DISABLED] "
                lines.append(f'{prefix}hl.bind("{k}", {act}) -- @plugin:{p_id} | @desc:{desc}')

                # Sync keybinding.json in plugin directory
                p_dir = pb.get("dir")
                if p_dir and Path(p_dir).is_dir():
                    kb_file = Path(p_dir) / "keybinding.json"
                    cmd = f"bash ~/.config/quickshell/scripts/toggle_plugin.sh {p_id}"
                    lua_snip = f'hl.bind("{k}", hl.dsp.exec_cmd("{cmd}"))'
                    try:
                        with open(kb_file, "w", encoding="utf-8") as kf:
                            json.dump({
                                "keybind": k,
                                "ipcCommand": cmd,
                                "luaSnippet": lua_snip,
                                "enabled": pb.get("enabled", True)
                            }, kf, indent=2)
                    except Exception:
                        pass
            else:
                p_dir = pb.get("dir")
                if p_dir and Path(p_dir).is_dir():
                    kb_file = Path(p_dir) / "keybinding.json"
                    if kb_file.is_file():
                        try:
                            with open(kb_file, "w", encoding="utf-8") as kf:
                                json.dump({
                                    "keybind": "",
                                    "ipcCommand": f"bash ~/.config/quickshell/scripts/toggle_plugin.sh {p_id}",
                                    "luaSnippet": "",
                                    "enabled": False
                                }, kf, indent=2)
                        except Exception:
                            pass
        lines.append("")

    content = "\n".join(lines) + "\n"
    USER_KEYBINDS_PATH.write_text(content, encoding="utf-8")

    # Apply live to Hyprland
    run_cmd(["hyprctl", "reload"])


def launch_keybind_manager_gui(start_tab: int = 0):
    """Launch the GTK3 Keybindings Manager application."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, Pango

    colors, theme_type, theme_name = get_active_theme_colors()

    c_base = colors.get("base", "#1e1e2e")
    c_mantle = colors.get("mantle", "#181825")
    c_crust = colors.get("crust", "#11111b")
    c_surface0 = colors.get("surface0", "#313244")
    c_surface1 = colors.get("surface1", "#45475a")
    c_surface2 = colors.get("surface2", "#585b70")
    c_text = colors.get("text", "#cdd6f4")
    c_subtext0 = colors.get("subtext0", "#a6adc8")
    c_subtext1 = colors.get("subtext1", "#bac2de")
    c_accent = colors.get("accent", "#cba6f7")
    c_green = colors.get("green", "#a6e3a1")
    c_red = colors.get("red", "#f38ba8")
    c_blue = colors.get("blue", "#89b4fa")
    c_sapphire = colors.get("sapphire", "#74c7ec")
    c_yellow = colors.get("yellow", "#f9e2af")

    accent_fg = get_contrast_color(c_accent)
    green_fg = get_contrast_color(c_green)
    red_fg = get_contrast_color(c_red)
    yellow_fg = get_contrast_color(c_yellow)
    sapphire_fg = get_contrast_color(c_sapphire)

    settings = Gtk.Settings.get_default()
    if settings:
        settings.set_property("gtk-application-prefer-dark-theme", theme_type == "dark")

    css_provider = Gtk.CssProvider()
    css_data = f"""
    * {{
        font-family: system-ui, -apple-system, 'Inter', 'Roboto', 'Noto Sans', 'JetBrainsMono Nerd Font', sans-serif;
    }}

    /* Full Window & Container Surface Styling */
    window, dialog, messagedialog,
    viewport, scrolledwindow,
    box, grid,
    notebook, notebook > stack, notebook > stack > *,
    list, listbox, row, listboxrow {{
        background-color: {c_base};
        color: {c_text};
    }}

    scrolledwindow, viewport {{
        background-color: {c_base};
        border: none;
    }}

    list, listbox, row, listboxrow {{
        background-color: transparent;
        color: {c_text};
    }}

    label {{
        color: {c_text};
    }}

    .top-header {{
        background-color: {c_mantle};
        border-bottom: 1px solid {c_surface0};
        padding: 14px 20px;
    }}

    .window-title {{
        font-size: 16px;
        font-weight: 700;
        color: {c_text};
    }}

    .window-subtitle {{
        font-size: 11px;
        color: {c_subtext0};
    }}

    notebook > header {{
        background-color: {c_mantle};
        border-bottom: 1px solid {c_surface0};
        padding: 0 12px;
    }}

    notebook tab {{
        padding: 8px 16px;
        font-weight: 600;
        font-size: 12px;
        color: {c_subtext0};
        border-bottom: 2px solid transparent;
        background: transparent;
    }}

    notebook tab label {{
        color: {c_subtext0};
        font-weight: 600;
    }}

    notebook tab:checked {{
        color: {c_accent};
        border-bottom: 2px solid {c_accent};
        background-color: {c_base};
    }}

    notebook tab:checked label {{
        color: {c_accent};
        font-weight: 700;
    }}

    notebook stack {{
        background-color: {c_base};
    }}

    /* Base Buttons */
    button {{
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 6px 14px;
        border: 1px solid {c_surface2};
        background-color: {c_surface0};
        color: {c_text};
        transition: all 120ms ease-in-out;
    }}

    button label {{
        color: {c_text};
        font-weight: 600;
        font-size: 12px;
    }}

    button:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}

    button:hover label {{
        color: {c_text};
    }}

    button:active {{
        background-color: {c_surface2};
    }}

    /* Accent / Primary Button */
    button.accent {{
        background-color: {c_accent};
        background-image: none;
        border: 1px solid {c_accent};
        color: {accent_fg};
    }}

    button.accent label {{
        color: {accent_fg};
        font-weight: 700;
    }}

    button.accent:hover {{
        background-color: {c_accent};
        border-color: {c_accent};
        opacity: 0.88;
    }}

    button.accent:hover label {{
        color: {accent_fg};
        font-weight: 700;
    }}

    /* Success Button (Enable, Save) */
    button.success {{
        background-color: {c_green};
        background-image: none;
        border: 1px solid {c_green};
        color: {green_fg};
    }}

    button.success label {{
        color: {green_fg};
        font-weight: 700;
    }}

    button.success:hover {{
        background-color: {c_green};
        border-color: {c_green};
        opacity: 0.88;
    }}

    button.success:hover label {{
        color: {green_fg};
        font-weight: 700;
    }}

    /* Danger Button (Delete, Reset) */
    button.danger {{
        background-color: {c_red};
        background-image: none;
        border: 1px solid {c_red};
        color: {red_fg};
    }}

    button.danger label {{
        color: {red_fg};
        font-weight: 700;
    }}

    button.danger:hover {{
        background-color: {c_red};
        border-color: {c_red};
        opacity: 0.88;
    }}

    button.danger:hover label {{
        color: {red_fg};
        font-weight: 700;
    }}

    /* Dialog and Action Area Buttons */
    dialog, messagedialog {{
        background-color: {c_base};
        color: {c_text};
    }}

    dialog button,
    messagedialog button,
    .dialog-action-area button {{
        background-color: {c_surface0};
        background-image: none;
        box-shadow: none;
        border: 1px solid {c_surface2};
        border-radius: 6px;
        padding: 6px 16px;
        color: {c_text};
    }}

    dialog button label,
    messagedialog button label,
    .dialog-action-area button label {{
        color: {c_text};
        font-weight: 600;
    }}

    dialog button:hover,
    messagedialog button:hover,
    .dialog-action-area button:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}

    dialog button.accent,
    messagedialog button.accent,
    .dialog-action-area button.accent {{
        background-color: {c_accent};
        border: 1px solid {c_accent};
        color: {accent_fg};
    }}

    dialog button.accent label,
    messagedialog button.accent label,
    .dialog-action-area button.accent label {{
        color: {accent_fg};
        font-weight: 700;
    }}

    entry, entry.search-input {{
        background-color: {c_mantle};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 6px;
        padding: 6px 10px;
    }}

    entry:focus {{
        border-color: {c_accent};
        background-color: {c_surface0};
        color: {c_text};
    }}

    textview, textview text, textview.view {{
        background-color: {c_mantle};
        color: {c_text};
        font-family: 'JetBrainsMono Nerd Font', monospace;
        font-size: 12px;
    }}

    scrolledwindow textview,
    scrolledwindow textview text {{
        background-color: {c_mantle};
        color: {c_text};
    }}

    combobox, combobox button, combobox textview, combobox cellview {{
        background-color: {c_surface0};
        color: {c_text};
        border: 1px solid {c_surface2};
        border-radius: 6px;
    }}

    combobox button:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
    }}

    combobox window, combobox menu, combobox .menu, menu, .menu {{
        background-color: {c_mantle};
        color: {c_text};
        border: 1px solid {c_surface1};
    }}

    menuitem, .menuitem {{
        color: {c_text};
    }}

    menuitem:hover, .menuitem:hover {{
        background-color: {c_surface1};
        color: {c_text};
    }}

    label.key-badge, .key-badge {{
        background-color: {c_surface0};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 6px;
        font-family: 'JetBrainsMono Nerd Font', monospace;
        font-size: 12px;
        font-weight: 700;
        padding: 3px 8px;
    }}

    label.key-badge-overridden, .key-badge-overridden {{
        background-color: {c_yellow};
        color: {yellow_fg};
        border: 1px solid {c_yellow};
        font-weight: 700;
    }}

    label.key-badge-disabled, .key-badge-disabled {{
        background-color: {c_surface0};
        color: {c_subtext0};
        text-decoration: line-through;
        opacity: 0.6;
    }}

    label.key-badge-unassigned, .key-badge-unassigned {{
        background-color: {c_surface0};
        color: {c_subtext0};
        font-style: italic;
        border: 1px dashed {c_surface2};
    }}

    .card {{
        background-color: {c_mantle};
        border: 1px solid {c_surface0};
        border-radius: 8px;
        padding: 8px 14px;
        margin-bottom: 5px;
    }}

    .card:hover {{
        border-color: {c_surface1};
        background-color: {c_surface0};
    }}

    .card label {{
        color: {c_text};
    }}

    .card label.stat-label {{
        color: {c_subtext0};
    }}

    .empty-card {{
        background-color: {c_mantle};
        border: 1px dashed {c_surface2};
        border-radius: 10px;
        padding: 36px 20px;
        margin: 16px 4px;
    }}

    label.empty-title {{
        color: {c_text};
        font-size: 14px;
        font-weight: 700;
    }}

    label.empty-sub {{
        color: {c_subtext0};
        font-size: 12px;
    }}

    label.status-tag, .status-tag {{
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
    }}

    label.status-default, .status-default {{ background-color: {c_surface1}; color: {c_text}; }}
    label.status-active, .status-active {{ background-color: {c_green}; color: {green_fg}; }}
    label.status-override, .status-override {{ background-color: {c_yellow}; color: {yellow_fg}; }}
    label.status-disabled, .status-disabled {{ background-color: {c_red}; color: {red_fg}; }}
    label.status-unbound, .status-unbound {{ background-color: {c_surface0}; color: {c_subtext0}; }}

    .badge-plugin, label.badge-plugin {{
        background-color: {c_sapphire};
        color: {sapphire_fg};
        font-size: 10px;
        font-weight: 700;
        border-radius: 4px;
        padding: 2px 6px;
    }}

    /* Keypress Recorder & Live Conflict Badge Styling */
    .btn-record {{
        background-color: {c_surface0};
        color: {c_text};
        font-weight: 600;
        border: 1px solid {c_surface2};
    }}

    .btn-record:hover {{
        border-color: {c_accent};
        background-color: {c_surface1};
    }}

    .recorder-recording, button.recorder-recording {{
        background-color: {c_red};
        color: {red_fg};
        border: 1px solid {c_red};
        font-weight: 700;
    }}

    .recorder-recording label, button.recorder-recording label {{
        color: {red_fg};
        font-weight: 700;
    }}

    label.conflict-badge, .conflict-badge {{
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 11px;
    }}

    label.conflict-hint, .conflict-hint {{
        background-color: {c_surface0};
        color: {c_subtext0};
        border: 1px solid {c_surface1};
    }}

    label.conflict-available, .conflict-available {{
        background-color: {c_green};
        color: {green_fg};
        border: 1px solid {c_green};
        font-weight: 600;
    }}

    label.conflict-warning, .conflict-warning {{
        background-color: {c_red};
        color: {red_fg};
        border: 1px solid {c_red};
        font-weight: 600;
    }}

    label.conflict-current, .conflict-current {{
        background-color: {c_sapphire};
        color: {sapphire_fg};
        border: 1px solid {c_sapphire};
        font-weight: 600;
    }}

    label.conflict-recording, .conflict-recording {{
        background-color: {c_yellow};
        color: {yellow_fg};
        border: 1px solid {c_yellow};
        font-weight: 700;
    }}

    .section-title, label.section-title {{
        font-size: 13px;
        font-weight: 700;
        color: {c_accent};
        margin-bottom: 6px;
    }}

    .stat-label, label.stat-label {{
        font-size: 11px;
        color: {c_subtext0};
    }}

    .stat-value, label.stat-value {{
        font-size: 12px;
        font-weight: 600;
        color: {c_text};
    }}

    scrollbar trough {{
        background-color: {c_base};
    }}
    scrollbar slider {{
        background-color: {c_surface1};
        border-radius: 4px;
    }}
    """
    css_provider.load_from_data(css_data.encode("utf-8"))
    screen = Gdk.Screen.get_default()
    if screen:
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    # -------------------------------------------------------------------------
    # Keypress Recorder & Conflict Badge Widget
    # -------------------------------------------------------------------------
    class KeybindRecorderBox(Gtk.Box):
        """
        Interactive widget providing:
        - Manual text entry for shortcut combination
        - 'Record' button that captures physical keypresses directly into chords
        - Dynamic conflict badge validating shortcut availability in real time
        """
        def __init__(self, parent_dialog, initial_key="", current_id=None, conflict_checker=None):
            super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.parent_dialog = parent_dialog
            self.initial_key = normalize_keybind(initial_key)
            self.current_id = current_id
            self.conflict_checker = conflict_checker

            self.is_recording = False
            self.held_modifiers = set()
            self.key_press_handler_id = None
            self.key_release_handler_id = None

            # Shortcut Input Row
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            self.entry = Gtk.Entry()
            self.entry.set_text(self.initial_key)
            self.entry.set_placeholder_text("e.g. SUPER + SHIFT + K")
            row.pack_start(self.entry, True, True, 0)

            self.btn_record = Gtk.Button(label="⏺ Record Keypress")
            self.btn_record.get_style_context().add_class("btn-record")
            self.btn_record.connect("clicked", self.toggle_recording)
            row.pack_start(self.btn_record, False, False, 0)

            self.btn_clear = Gtk.Button(label="Clear")
            self.btn_clear.connect("clicked", self.clear_key)
            row.pack_start(self.btn_clear, False, False, 0)

            self.pack_start(row, False, False, 0)

            # Live Conflict / Status Label
            self.lbl_status = Gtk.Label(xalign=0)
            self.lbl_status.set_line_wrap(True)
            self.lbl_status.get_style_context().add_class("conflict-badge")
            self.pack_start(self.lbl_status, False, False, 0)

            # Listen for entry changes
            self.entry.connect("changed", self._on_entry_changed)
            self.update_conflict_status(self.entry.get_text())

            # Cleanup on dialog destroy
            self.parent_dialog.connect("destroy", lambda w: self.stop_recording())

        def get_key(self):
            return normalize_keybind(self.entry.get_text().strip())

        def start_recording(self):
            if self.is_recording:
                return
            self.is_recording = True
            self.held_modifiers = set()
            self.btn_record.set_label("⏹ Press Key Combo... (Esc cancels)")
            self.btn_record.get_style_context().add_class("recorder-recording")

            self._reset_status_styles()
            self.lbl_status.get_style_context().add_class("conflict-recording")
            self.lbl_status.set_markup("<b>⏺ Listening:</b> Press physical keys on your keyboard... (Esc cancels)")

            self.key_press_handler_id = self.parent_dialog.connect("key-press-event", self._on_dialog_key_press)
            self.key_release_handler_id = self.parent_dialog.connect("key-release-event", self._on_dialog_key_release)

        def stop_recording(self):
            if not self.is_recording:
                return
            self.is_recording = False
            self.held_modifiers.clear()
            self.btn_record.set_label("⏺ Record Keypress")
            self.btn_record.get_style_context().remove_class("recorder-recording")

            if self.key_press_handler_id:
                try:
                    self.parent_dialog.disconnect(self.key_press_handler_id)
                except Exception:
                    pass
                self.key_press_handler_id = None

            if self.key_release_handler_id:
                try:
                    self.parent_dialog.disconnect(self.key_release_handler_id)
                except Exception:
                    pass
                self.key_release_handler_id = None

            self.update_conflict_status(self.entry.get_text())

        def toggle_recording(self, widget):
            if self.is_recording:
                self.stop_recording()
            else:
                self.start_recording()

        def clear_key(self, widget):
            if self.is_recording:
                self.stop_recording()
            self.entry.set_text("")
            self.update_conflict_status("")

        def _on_dialog_key_press(self, widget, event):
            if not self.is_recording:
                return False

            key_name = Gdk.keyval_name(event.keyval)
            if not key_name:
                return True

            # Escape alone cancels recording
            if key_name == "Escape" and not self.held_modifiers:
                self.stop_recording()
                return True

            mod_map = {
                "Super_L": "SUPER", "Super_R": "SUPER",
                "Control_L": "CTRL", "Control_R": "CTRL",
                "Alt_L": "ALT", "Alt_R": "ALT",
                "Shift_L": "SHIFT", "Shift_R": "SHIFT",
                "Meta_L": "SUPER", "Meta_R": "SUPER",
                "ISO_Level3_Shift": "ALT"
            }

            # Modifier key pressed: track and update listening status
            if key_name in mod_map:
                self.held_modifiers.add(mod_map[key_name])
                ordered = [m for m in ["SUPER", "CTRL", "ALT", "SHIFT"] if m in self.held_modifiers]
                self._reset_status_styles()
                self.lbl_status.get_style_context().add_class("conflict-recording")
                self.lbl_status.set_markup(f"<b>⏺ Listening:</b> {' + '.join(ordered)} + [Press Primary Key]")
                return True

            # Primary non-modifier key pressed: assemble chord
            active_mods = set(self.held_modifiers)
            if event.state & Gdk.ModifierType.MOD4_MASK:
                active_mods.add("SUPER")
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                active_mods.add("CTRL")
            if event.state & Gdk.ModifierType.MOD1_MASK:
                active_mods.add("ALT")
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                active_mods.add("SHIFT")

            norm_key = normalize_key(key_name)
            ordered_mods = [m for m in ["SUPER", "CTRL", "ALT", "SHIFT"] if m in active_mods]
            combo_str = " + ".join(ordered_mods + [norm_key])

            self.entry.set_text(combo_str)
            self.stop_recording()
            return True

        def _on_dialog_key_release(self, widget, event):
            if not self.is_recording:
                return False
            key_name = Gdk.keyval_name(event.keyval)
            mod_map = {
                "Super_L": "SUPER", "Super_R": "SUPER",
                "Control_L": "CTRL", "Control_R": "CTRL",
                "Alt_L": "ALT", "Alt_R": "ALT",
                "Shift_L": "SHIFT", "Shift_R": "SHIFT",
                "Meta_L": "SUPER", "Meta_R": "SUPER",
                "ISO_Level3_Shift": "ALT"
            }
            if key_name in mod_map:
                self.held_modifiers.discard(mod_map[key_name])
                if self.held_modifiers:
                    ordered = [m for m in ["SUPER", "CTRL", "ALT", "SHIFT"] if m in self.held_modifiers]
                    self.lbl_status.set_markup(f"<b>⏺ Listening:</b> {' + '.join(ordered)} + [Press Primary Key]")
                else:
                    self.lbl_status.set_markup("<b>⏺ Listening:</b> Press physical keys on your keyboard... (Esc cancels)")
            return True

        def _reset_status_styles(self):
            ctx = self.lbl_status.get_style_context()
            for cls in ["conflict-hint", "conflict-available", "conflict-warning", "conflict-current", "conflict-recording"]:
                ctx.remove_class(cls)

        def _on_entry_changed(self, widget):
            self.update_conflict_status(self.entry.get_text())

        def update_conflict_status(self, raw_text):
            self._reset_status_styles()
            raw_clean = raw_text.strip()
            if not raw_clean:
                self.lbl_status.get_style_context().add_class("conflict-hint")
                self.lbl_status.set_markup("<span size='small'>Press <b>⏺ Record Keypress</b> or enter a shortcut (e.g. SUPER + SHIFT + K)</span>")
                return

            candidate = normalize_keybind(raw_clean)

            # Check if identical to initial key
            if self.initial_key and candidate == self.initial_key:
                self.lbl_status.get_style_context().add_class("conflict-current")
                self.lbl_status.set_markup(f"<b>ℹ️ Current:</b> '{candidate}' is currently assigned to this action.")
                return

            # Live Conflict Detection
            if self.conflict_checker:
                conflict = self.conflict_checker(candidate, self.current_id)
                if conflict:
                    self.lbl_status.get_style_context().add_class("conflict-warning")
                    self.lbl_status.set_markup(f"<b>⚠️ Conflict Detected:</b> '{candidate}' is already in use by {conflict['detail']}.")
                    return

            # Shortcut is completely free
            self.lbl_status.get_style_context().add_class("conflict-available")
            self.lbl_status.set_markup(f"<b>✓ Available:</b> '{candidate}' has no conflicts and is free to use!")

    # -------------------------------------------------------------------------
    # Main Keybindings Manager Window
    # -------------------------------------------------------------------------
    class KeybindsManagerWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Hyprland Keybindings Manager")
            self.set_default_size(960, 660)
            self.set_position(Gtk.WindowPosition.CENTER)

            self.default_binds = parse_default_keybinds()
            self.disabled_defaults, self.overrides, self.custom_binds, self.plugin_binds = load_user_keybinds_state()
            self.live_binds = get_live_hyprctl_binds()

            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_box)

            # Top Header
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header.get_style_context().add_class("top-header")

            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_title = Gtk.Label(label="⌨️ Hyprland Keybindings Manager", xalign=0)
            lbl_title.get_style_context().add_class("window-title")
            self.lbl_sub = Gtk.Label(
                label=f"Active System Theme: {theme_name.title()}  •  {len(self.default_binds)} Defaults  •  {len(self.custom_binds)} Custom  •  {len(self.plugin_binds)} Plugins",
                xalign=0
            )
            self.lbl_sub.get_style_context().add_class("window-subtitle")
            title_box.pack_start(lbl_title, False, False, 0)
            title_box.pack_start(self.lbl_sub, False, False, 0)
            header.pack_start(title_box, True, True, 0)

            btn_reload = Gtk.Button(label="󰑐  Reload Hyprland")
            btn_reload.connect("clicked", lambda b: self.reload_hyprland())
            header.pack_end(btn_reload, False, False, 0)

            btn_add = Gtk.Button(label="󰐕  Add Custom Keybind")
            btn_add.get_style_context().add_class("accent")
            btn_add.connect("clicked", lambda b: self.show_add_custom_dialog())
            header.pack_end(btn_add, False, False, 0)

            main_box.pack_start(header, False, False, 0)

            # Notebook Tabs
            self.notebook = Gtk.Notebook()
            main_box.pack_start(self.notebook, True, True, 0)

            # Tab 0: Default Keybinds
            self.tab_defaults = self.build_defaults_tab()
            self.notebook.append_page(self.tab_defaults, Gtk.Label(label="󰌌  Default Keybinds"))

            # Tab 1: Custom Keybinds
            self.tab_custom = self.build_custom_tab()
            self.notebook.append_page(self.tab_custom, Gtk.Label(label="⚡  Custom Keybinds"))

            # Tab 2: Plugin Keybinds
            self.tab_plugins = self.build_plugins_tab()
            self.notebook.append_page(self.tab_plugins, Gtk.Label(label="🧩  Plugin Keybinds"))

            # Tab 3: Generated Lua Config
            self.tab_lua = self.build_lua_tab()
            self.notebook.append_page(self.tab_lua, Gtk.Label(label="📄  user/keybinds.lua"))

            self.refresh_all()

        def check_conflict(self, candidate, exclude_id=None):
            """Evaluate candidate shortcut conflict across all system bindings."""
            return find_keybind_conflict(
                candidate,
                exclude_id=exclude_id,
                default_binds=self.default_binds,
                disabled_defaults=self.disabled_defaults,
                overrides=self.overrides,
                custom_binds=self.custom_binds,
                plugin_binds=self.plugin_binds,
                live_binds=self.live_binds
            )

        # ---------------------------------------------------------------------
        # Tab 1: Default Keybinds
        # ---------------------------------------------------------------------
        def build_defaults_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            container.set_margin_top(12)
            container.set_margin_bottom(12)
            container.set_margin_start(16)
            container.set_margin_end(16)

            # Filter Row
            filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            self.def_search_entry = Gtk.Entry()
            self.def_search_entry.set_placeholder_text("🔍 Search default keybinds or actions...")
            self.def_search_entry.connect("changed", lambda e: self.populate_defaults_list())
            filter_row.pack_start(self.def_search_entry, True, True, 0)

            self.status_filter = Gtk.ComboBoxText()
            self.status_filter.append("all", "All Statuses")
            self.status_filter.append("enabled", "Active / Enabled")
            self.status_filter.append("overridden", "Overridden")
            self.status_filter.append("disabled", "Disabled")
            self.status_filter.set_active(0)
            self.status_filter.connect("changed", lambda c: self.populate_defaults_list())
            filter_row.pack_start(self.status_filter, False, False, 0)

            container.pack_start(filter_row, False, False, 0)

            # Scroller Listbox
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.defaults_listbox = Gtk.ListBox()
            self.defaults_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroller.add(self.defaults_listbox)
            container.pack_start(scroller, True, True, 0)

            self.lbl_def_summary = Gtk.Label(label="", xalign=0)
            self.lbl_def_summary.get_style_context().add_class("stat-label")
            container.pack_start(self.lbl_def_summary, False, False, 0)

            return container

        def populate_defaults_list(self):
            for child in self.defaults_listbox.get_children():
                self.defaults_listbox.remove(child)

            query = self.def_search_entry.get_text().strip().lower()
            status_filter = self.status_filter.get_active_id()

            visible_count = 0
            for item in self.default_binds:
                k = item["key"]
                is_disabled = k in self.disabled_defaults
                is_overridden = k in self.overrides

                # Status filtering
                if status_filter == "enabled" and (is_disabled or is_overridden):
                    continue
                elif status_filter == "overridden" and not is_overridden:
                    continue
                elif status_filter == "disabled" and not is_disabled:
                    continue

                # Query filtering
                match_text = f"{k} {item['desc']} {item['category']} {item['action']}".lower()
                if is_overridden:
                    match_text += f" {self.overrides[k]['new_key']}"
                if query and query not in match_text:
                    continue

                visible_count += 1
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                card.get_style_context().add_class("card")

                # Key Badge
                display_key = self.overrides[k]["new_key"] if is_overridden else k
                lbl_key = Gtk.Label(label=display_key)
                lbl_key.get_style_context().add_class("key-badge")
                if is_overridden:
                    lbl_key.get_style_context().add_class("key-badge-overridden")
                elif is_disabled:
                    lbl_key.get_style_context().add_class("key-badge-disabled")
                card.pack_start(lbl_key, False, False, 0)

                # Description & Category
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                lbl_desc = Gtk.Label(label=item["desc"], xalign=0)
                lbl_desc.get_style_context().add_class("stat-value")

                sub_text = item["category"]
                if is_overridden:
                    sub_text += f"  •  Replaced default [{k}]"
                lbl_cat = Gtk.Label(label=sub_text, xalign=0)
                lbl_cat.get_style_context().add_class("stat-label")

                info_box.pack_start(lbl_desc, False, False, 0)
                info_box.pack_start(lbl_cat, False, False, 0)
                card.pack_start(info_box, True, True, 0)

                # Status Tag
                if is_disabled:
                    tag = Gtk.Label(label="Disabled")
                    tag.get_style_context().add_class("status-tag")
                    tag.get_style_context().add_class("status-disabled")
                elif is_overridden:
                    tag = Gtk.Label(label="Overridden")
                    tag.get_style_context().add_class("status-tag")
                    tag.get_style_context().add_class("status-override")
                else:
                    tag = Gtk.Label(label="Default")
                    tag.get_style_context().add_class("status-tag")
                    tag.get_style_context().add_class("status-default")
                card.pack_end(tag, False, False, 0)

                # Actions
                if is_disabled:
                    btn_toggle = Gtk.Button(label="Enable")
                    btn_toggle.get_style_context().add_class("success")
                    btn_toggle.connect("clicked", lambda b, key=k: self.toggle_default_disabled(key, False))
                    card.pack_end(btn_toggle, False, False, 0)
                else:
                    btn_toggle = Gtk.Button(label="Disable")
                    btn_toggle.connect("clicked", lambda b, key=k: self.toggle_default_disabled(key, True))
                    card.pack_end(btn_toggle, False, False, 0)

                btn_edit = Gtk.Button(label="✏️ Override")
                btn_edit.connect("clicked", lambda b, entry=item: self.show_override_dialog(entry))
                card.pack_end(btn_edit, False, False, 0)

                if is_overridden or is_disabled:
                    btn_reset = Gtk.Button(label="↺ Reset")
                    btn_reset.connect("clicked", lambda b, key=k: self.reset_default(key))
                    card.pack_end(btn_reset, False, False, 0)

                self.defaults_listbox.add(card)

            if visible_count == 0:
                empty_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
                empty_card.get_style_context().add_class("empty-card")
                lbl_title = Gtk.Label(label="No default keybindings match your filter.", xalign=0.5)
                lbl_title.get_style_context().add_class("empty-title")
                lbl_sub = Gtk.Label(label="Try clearing the search query or changing category/status filters.", xalign=0.5)
                lbl_sub.get_style_context().add_class("empty-sub")
                empty_card.pack_start(lbl_title, False, False, 0)
                empty_card.pack_start(lbl_sub, False, False, 0)
                self.defaults_listbox.add(empty_card)

            self.defaults_listbox.show_all()
            self.lbl_def_summary.set_text(
                f"Showing {visible_count} of {len(self.default_binds)} default keybinds  •  "
                f"{len(self.disabled_defaults)} disabled  •  {len(self.overrides)} overridden"
            )

        # ---------------------------------------------------------------------
        # Tab 2: Custom Keybinds
        # ---------------------------------------------------------------------
        def build_custom_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            container.set_margin_top(12)
            container.set_margin_bottom(12)
            container.set_margin_start(16)
            container.set_margin_end(16)

            # Top action
            top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl_desc = Gtk.Label(
                label="Custom keybindings are stored in ~/.config/hypr/user/keybinds.lua (untracked in Git).",
                xalign=0
            )
            lbl_desc.get_style_context().add_class("stat-label")
            top_bar.pack_start(lbl_desc, True, True, 0)

            btn_add = Gtk.Button(label="󰐕  Add Keybind")
            btn_add.get_style_context().add_class("accent")
            btn_add.connect("clicked", lambda b: self.show_add_custom_dialog())
            top_bar.pack_end(btn_add, False, False, 0)
            container.pack_start(top_bar, False, False, 0)

            # Scroller Listbox
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.custom_listbox = Gtk.ListBox()
            self.custom_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroller.add(self.custom_listbox)
            container.pack_start(scroller, True, True, 0)

            self.lbl_custom_summary = Gtk.Label(label="", xalign=0)
            self.lbl_custom_summary.get_style_context().add_class("stat-label")
            container.pack_start(self.lbl_custom_summary, False, False, 0)

            return container

        def populate_custom_list(self):
            for child in self.custom_listbox.get_children():
                self.custom_listbox.remove(child)

            if not self.custom_binds:
                empty_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
                empty_card.get_style_context().add_class("empty-card")
                lbl_title = Gtk.Label(label="No custom keybindings configured yet.", xalign=0.5)
                lbl_title.get_style_context().add_class("empty-title")
                lbl_sub = Gtk.Label(
                    label="Click '+ Add Custom Keybind' above to create personal shortcuts with keypress recording!",
                    xalign=0.5
                )
                lbl_sub.get_style_context().add_class("empty-sub")
                empty_card.pack_start(lbl_title, False, False, 0)
                empty_card.pack_start(lbl_sub, False, False, 0)
                self.custom_listbox.add(empty_card)
                self.custom_listbox.show_all()
                self.lbl_custom_summary.set_text("0 custom keybindings configured.")
                return

            for i, cb in enumerate(self.custom_binds):
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                card.get_style_context().add_class("card")

                # Key Badge
                lbl_key = Gtk.Label(label=cb["key"])
                lbl_key.get_style_context().add_class("key-badge")
                if not cb.get("enabled", True):
                    lbl_key.get_style_context().add_class("key-badge-disabled")
                card.pack_start(lbl_key, False, False, 0)

                # Description
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                lbl_desc = Gtk.Label(label=cb["desc"], xalign=0)
                lbl_desc.get_style_context().add_class("stat-value")

                lbl_sub = Gtk.Label(label=f"{cb['category']}  •  {cb['action']}", xalign=0)
                lbl_sub.get_style_context().add_class("stat-label")
                lbl_sub.set_ellipsize(Pango.EllipsizeMode.END)

                info_box.pack_start(lbl_desc, False, False, 0)
                info_box.pack_start(lbl_sub, False, False, 0)
                card.pack_start(info_box, True, True, 0)

                # Status tag
                tag = Gtk.Label(label="Active" if cb.get("enabled", True) else "Disabled")
                tag.get_style_context().add_class("status-tag")
                tag.get_style_context().add_class("status-active" if cb.get("enabled", True) else "status-disabled")
                card.pack_end(tag, False, False, 0)

                # Action buttons
                btn_del = Gtk.Button(label="🗑️")
                btn_del.get_style_context().add_class("danger")
                btn_del.connect("clicked", lambda b, idx=i: self.delete_custom_bind(idx))
                card.pack_end(btn_del, False, False, 0)

                btn_edit = Gtk.Button(label="✏️ Edit")
                btn_edit.connect("clicked", lambda b, idx=i: self.show_edit_custom_dialog(idx))
                card.pack_end(btn_edit, False, False, 0)

                btn_toggle = Gtk.Button(label="Disable" if cb.get("enabled", True) else "Enable")
                if not cb.get("enabled", True):
                    btn_toggle.get_style_context().add_class("success")
                btn_toggle.connect("clicked", lambda b, idx=i: self.toggle_custom_enabled(idx))
                card.pack_end(btn_toggle, False, False, 0)

                self.custom_listbox.add(card)

            self.custom_listbox.show_all()
            enabled_count = sum(1 for c in self.custom_binds if c.get("enabled", True))
            self.lbl_custom_summary.set_text(
                f"{len(self.custom_binds)} custom keybindings ({enabled_count} active, {len(self.custom_binds)-enabled_count} disabled)"
            )

        # ---------------------------------------------------------------------
        # Tab 3: Plugin Keybinds (Quickshell Custom & Built-in Plugins)
        # ---------------------------------------------------------------------
        def build_plugins_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            container.set_margin_top(12)
            container.set_margin_bottom(12)
            container.set_margin_start(16)
            container.set_margin_end(16)

            # Filter Row
            filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            self.plugin_search_entry = Gtk.Entry()
            self.plugin_search_entry.set_placeholder_text("🔍 Search plugins by name or shortcut...")
            self.plugin_search_entry.connect("changed", lambda e: self.populate_plugins_list())
            filter_row.pack_start(self.plugin_search_entry, True, True, 0)

            self.plugin_status_filter = Gtk.ComboBoxText()
            self.plugin_status_filter.append("all", "All Statuses")
            self.plugin_status_filter.append("assigned", "With Shortcut")
            self.plugin_status_filter.append("active", "Active / Enabled")
            self.plugin_status_filter.append("disabled", "Disabled")
            self.plugin_status_filter.append("unassigned", "No Shortcut")
            self.plugin_status_filter.set_active(0)
            self.plugin_status_filter.connect("changed", lambda c: self.populate_plugins_list())
            filter_row.pack_start(self.plugin_status_filter, False, False, 0)

            self.plugin_type_filter = Gtk.ComboBoxText()
            self.plugin_type_filter.append("all", "All Plugins")
            self.plugin_type_filter.append("custom", "Custom Plugins Only")
            self.plugin_type_filter.append("builtin", "Built-in Plugins Only")
            self.plugin_type_filter.set_active(0)
            self.plugin_type_filter.connect("changed", lambda c: self.populate_plugins_list())
            filter_row.pack_start(self.plugin_type_filter, False, False, 0)

            container.pack_start(filter_row, False, False, 0)

            # Scroller Listbox
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.plugins_listbox = Gtk.ListBox()
            self.plugins_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroller.add(self.plugins_listbox)
            container.pack_start(scroller, True, True, 0)

            self.lbl_plugin_summary = Gtk.Label(label="", xalign=0)
            self.lbl_plugin_summary.get_style_context().add_class("stat-label")
            container.pack_start(self.lbl_plugin_summary, False, False, 0)

            return container

        def populate_plugins_list(self):
            for child in self.plugins_listbox.get_children():
                self.plugins_listbox.remove(child)

            query = self.plugin_search_entry.get_text().strip().lower()
            status_filter = self.plugin_status_filter.get_active_id()
            type_filter = self.plugin_type_filter.get_active_id()

            # Sort: custom plugins first, then alphabetically
            sorted_plugins = sorted(
                self.plugin_binds.items(),
                key=lambda item: (not item[1].get("is_custom", True), item[1].get("name", "").lower())
            )

            visible_count = 0
            for pid, pl in sorted_plugins:
                k = normalize_keybind(pl.get("key", ""))
                is_custom = pl.get("is_custom", True)
                is_enabled = pl.get("enabled", True) if k else False
                has_key = bool(k)

                # Type filtering
                if type_filter == "custom" and not is_custom:
                    continue
                elif type_filter == "builtin" and is_custom:
                    continue

                # Status filtering
                if status_filter == "assigned" and not has_key:
                    continue
                elif status_filter == "active" and (not has_key or not is_enabled):
                    continue
                elif status_filter == "disabled" and (not has_key or is_enabled):
                    continue
                elif status_filter == "unassigned" and has_key:
                    continue

                # Query filtering
                match_text = f"{pid} {pl.get('name', '')} {pl.get('desc', '')} {k}".lower()
                if query and query not in match_text:
                    continue

                visible_count += 1
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                card.get_style_context().add_class("card")

                # Key Badge
                if has_key:
                    lbl_key = Gtk.Label(label=k)
                    lbl_key.get_style_context().add_class("key-badge")
                    if not is_enabled:
                        lbl_key.get_style_context().add_class("key-badge-disabled")
                else:
                    lbl_key = Gtk.Label(label="No Shortcut")
                    lbl_key.get_style_context().add_class("key-badge")
                    lbl_key.get_style_context().add_class("key-badge-unassigned")
                card.pack_start(lbl_key, False, False, 0)

                # Description & Meta
                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

                lbl_name = Gtk.Label(label=f"🧩 {pl['name']}", xalign=0)
                lbl_name.get_style_context().add_class("stat-value")
                title_row.pack_start(lbl_name, False, False, 0)

                tag_type = Gtk.Label(label="Custom Plugin" if is_custom else "Built-in")
                tag_type.get_style_context().add_class("badge-plugin" if is_custom else "status-default")
                title_row.pack_start(tag_type, False, False, 0)

                info_box.pack_start(title_row, False, False, 0)

                lbl_desc = Gtk.Label(label=pl.get("desc", ""), xalign=0)
                lbl_desc.get_style_context().add_class("stat-label")
                lbl_desc.set_ellipsize(Pango.EllipsizeMode.END)
                info_box.pack_start(lbl_desc, False, False, 0)

                card.pack_start(info_box, True, True, 0)

                # Status Tag
                if not has_key:
                    tag = Gtk.Label(label="Unbound")
                    tag.get_style_context().add_class("status-tag")
                    tag.get_style_context().add_class("status-unbound")
                elif is_enabled:
                    tag = Gtk.Label(label="Active")
                    tag.get_style_context().add_class("status-tag")
                    tag.get_style_context().add_class("status-active")
                else:
                    tag = Gtk.Label(label="Disabled")
                    tag.get_style_context().add_class("status-tag")
                    tag.get_style_context().add_class("status-disabled")
                card.pack_end(tag, False, False, 0)

                # Actions
                if has_key:
                    btn_unbind = Gtk.Button(label="🗑️")
                    btn_unbind.get_style_context().add_class("danger")
                    btn_unbind.set_tooltip_text("Unbind shortcut")
                    btn_unbind.connect("clicked", lambda b, p_id=pid: self.unbind_plugin(p_id))
                    card.pack_end(btn_unbind, False, False, 0)

                    btn_edit = Gtk.Button(label="✏️ Edit")
                    btn_edit.connect("clicked", lambda b, p_id=pid: self.show_edit_plugin_dialog(p_id))
                    card.pack_end(btn_edit, False, False, 0)

                    btn_toggle = Gtk.Button(label="Disable" if is_enabled else "Enable")
                    if not is_enabled:
                        btn_toggle.get_style_context().add_class("success")
                    btn_toggle.connect("clicked", lambda b, p_id=pid: self.toggle_plugin_enabled(p_id))
                    card.pack_end(btn_toggle, False, False, 0)
                else:
                    btn_assign = Gtk.Button(label="󰐕 Set Shortcut")
                    btn_assign.get_style_context().add_class("accent")
                    btn_assign.connect("clicked", lambda b, p_id=pid: self.show_edit_plugin_dialog(p_id))
                    card.pack_end(btn_assign, False, False, 0)

                self.plugins_listbox.add(card)

            if visible_count == 0:
                empty_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
                empty_card.get_style_context().add_class("empty-card")
                lbl_title = Gtk.Label(label="No plugins match your current filter.", xalign=0.5)
                lbl_title.get_style_context().add_class("empty-title")
                lbl_sub = Gtk.Label(label="Try changing or clearing your search criteria.", xalign=0.5)
                lbl_sub.get_style_context().add_class("empty-sub")
                empty_card.pack_start(lbl_title, False, False, 0)
                empty_card.pack_start(lbl_sub, False, False, 0)
                self.plugins_listbox.add(empty_card)

            self.plugins_listbox.show_all()
            assigned_count = sum(1 for pl in self.plugin_binds.values() if pl.get("key"))
            self.lbl_plugin_summary.set_text(
                f"Showing {visible_count} plugins  •  {assigned_count} assigned shortcuts  •  "
                f"{len(self.plugin_binds) - assigned_count} unassigned"
            )

        # ---------------------------------------------------------------------
        # Tab 4: Generated Lua Config
        # ---------------------------------------------------------------------
        def build_lua_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            container.set_margin_top(12)
            container.set_margin_bottom(12)
            container.set_margin_start(16)
            container.set_margin_end(16)

            top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl_desc = Gtk.Label(label="Live contents of ~/.config/hypr/user/keybinds.lua:", xalign=0)
            lbl_desc.get_style_context().add_class("stat-label")
            top_bar.pack_start(lbl_desc, True, True, 0)

            btn_open = Gtk.Button(label="✏️ Open in Editor")
            btn_open.connect("clicked", lambda b: self.open_in_editor())
            top_bar.pack_end(btn_open, False, False, 0)
            container.pack_start(top_bar, False, False, 0)

            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.lua_textview = Gtk.TextView()
            self.lua_textview.set_editable(False)
            self.lua_textview.set_monospace(True)
            scroller.add(self.lua_textview)
            container.pack_start(scroller, True, True, 0)

            return container

        def refresh_lua_view(self):
            buf = self.lua_textview.get_buffer()
            if USER_KEYBINDS_PATH.is_file():
                buf.set_text(USER_KEYBINDS_PATH.read_text(encoding="utf-8"))
            else:
                buf.set_text("-- No personal keybind overrides present yet.")

        # ---------------------------------------------------------------------
        # Actions & Dialog Handlers
        # ---------------------------------------------------------------------
        def toggle_default_disabled(self, key, disable):
            if disable:
                self.disabled_defaults.add(key)
                if key in self.overrides:
                    del self.overrides[key]
            else:
                self.disabled_defaults.discard(key)
            self.save_and_sync()

        def reset_default(self, key):
            self.disabled_defaults.discard(key)
            if key in self.overrides:
                del self.overrides[key]
            self.save_and_sync()

        def toggle_custom_enabled(self, idx):
            if 0 <= idx < len(self.custom_binds):
                curr = self.custom_binds[idx].get("enabled", True)
                self.custom_binds[idx]["enabled"] = not curr
                self.save_and_sync()

        def delete_custom_bind(self, idx):
            if 0 <= idx < len(self.custom_binds):
                del self.custom_binds[idx]
                self.save_and_sync()

        def toggle_plugin_enabled(self, plugin_id):
            if plugin_id in self.plugin_binds:
                curr = self.plugin_binds[plugin_id].get("enabled", True)
                self.plugin_binds[plugin_id]["enabled"] = not curr
                self.save_and_sync()

        def unbind_plugin(self, plugin_id):
            if plugin_id in self.plugin_binds:
                self.plugin_binds[plugin_id]["key"] = ""
                self.plugin_binds[plugin_id]["enabled"] = False
                self.save_and_sync()

        def show_override_dialog(self, default_item):
            orig_key = default_item["key"]
            curr_override = self.overrides.get(orig_key, {})

            dialog = Gtk.Dialog(title=f"Override Default: {default_item['desc']}", flags=0)
            dialog.set_default_size(560, 340)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(10)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_orig = Gtk.Label(label=f"Original Shortcut: <b>{orig_key}</b>", xalign=0, use_markup=True)
            box.pack_start(lbl_orig, False, False, 0)

            lbl_key = Gtk.Label(label="New Keyboard Shortcut (Record or type):", xalign=0)
            box.pack_start(lbl_key, False, False, 0)

            # Keypress Recorder & Conflict detector widget
            initial_k = curr_override.get("new_key") or orig_key
            recorder = KeybindRecorderBox(
                parent_dialog=dialog,
                initial_key=initial_k,
                current_id=f"def:{orig_key}",
                conflict_checker=self.check_conflict
            )
            box.pack_start(recorder, False, False, 0)

            lbl_act = Gtk.Label(label="Lua Action Dispatcher:", xalign=0)
            box.pack_start(lbl_act, False, False, 0)
            entry_act = Gtk.Entry()
            entry_act.set_text(curr_override.get("action") or default_item["action"])
            box.pack_start(entry_act, False, False, 0)

            lbl_desc = Gtk.Label(label="Description:", xalign=0)
            box.pack_start(lbl_desc, False, False, 0)
            entry_desc = Gtk.Entry()
            entry_desc.set_text(curr_override.get("desc") or default_item["desc"])
            box.pack_start(entry_desc, False, False, 0)

            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            btn_save = dialog.add_button("Save Override", Gtk.ResponseType.OK)
            btn_save.get_style_context().add_class("accent")

            dialog.show_all()
            res = dialog.run()
            new_key = recorder.get_key()
            new_act = entry_act.get_text().strip()
            new_desc = entry_desc.get_text().strip()
            recorder.stop_recording()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and new_key and new_act:
                self.disabled_defaults.discard(orig_key)
                self.overrides[orig_key] = {
                    "orig_key": orig_key,
                    "new_key": new_key,
                    "action": new_act,
                    "desc": new_desc or default_item["desc"],
                    "flags": default_item.get("flags", "")
                }
                self.save_and_sync()

        def show_add_custom_dialog(self):
            dialog = Gtk.Dialog(title="Add Custom Keybinding", flags=0)
            dialog.set_default_size(560, 380)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(8)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_k = Gtk.Label(label="Keyboard Shortcut (Record or type):", xalign=0)
            box.pack_start(lbl_k, False, False, 0)

            recorder = KeybindRecorderBox(
                parent_dialog=dialog,
                initial_key="SUPER + ",
                current_id=None,
                conflict_checker=self.check_conflict
            )
            box.pack_start(recorder, False, False, 0)

            lbl_type = Gtk.Label(label="Action Preset or Command:", xalign=0)
            box.pack_start(lbl_type, False, False, 0)

            combo_preset = Gtk.ComboBoxText()
            combo_preset.append("exec", "Execute Terminal Command / Application")
            combo_preset.append("close", "Close Window (hl.dsp.window.close())")
            combo_preset.append("float", "Toggle Floating Window (hl.dsp.window.float())")
            combo_preset.append("fullscreen", "Toggle Fullscreen (hl.dsp.window.fullscreen())")
            combo_preset.append("custom", "Custom Lua Dispatcher Code")
            combo_preset.set_active(0)
            box.pack_start(combo_preset, False, False, 0)

            lbl_act = Gtk.Label(label="Command / Executable to launch:", xalign=0)
            box.pack_start(lbl_act, False, False, 0)
            entry_act = Gtk.Entry()
            entry_act.set_placeholder_text("foot -e btop")
            box.pack_start(entry_act, False, False, 0)

            lbl_desc = Gtk.Label(label="Short Description:", xalign=0)
            box.pack_start(lbl_desc, False, False, 0)
            entry_desc = Gtk.Entry()
            entry_desc.set_placeholder_text("Open Btop System Monitor")
            box.pack_start(entry_desc, False, False, 0)

            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            btn_ok = dialog.add_button("Add Shortcut", Gtk.ResponseType.OK)
            btn_ok.get_style_context().add_class("accent")

            dialog.show_all()
            res = dialog.run()
            k = recorder.get_key()
            cmd = entry_act.get_text().strip()
            desc = entry_desc.get_text().strip() or "Custom Shortcut"
            preset = combo_preset.get_active_id()
            recorder.stop_recording()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and k:
                if preset == "exec":
                    action_lua = f'hl.dsp.exec_cmd("{cmd}")'
                elif preset == "close":
                    action_lua = "hl.dsp.window.close()"
                elif preset == "float":
                    action_lua = 'hl.dsp.window.float({ action = "toggle" })'
                elif preset == "fullscreen":
                    action_lua = "hl.dsp.window.fullscreen()"
                else:
                    action_lua = cmd

                self.custom_binds.append({
                    "id": f"custom:{k}:{desc}",
                    "key": k,
                    "action": action_lua,
                    "desc": desc,
                    "category": "Personal Shortcuts",
                    "enabled": True,
                    "type": "custom"
                })
                self.save_and_sync()

        def show_edit_custom_dialog(self, idx):
            if not (0 <= idx < len(self.custom_binds)):
                return
            cb = self.custom_binds[idx]

            dialog = Gtk.Dialog(title="Edit Custom Keybinding", flags=0)
            dialog.set_default_size(560, 320)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(8)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_k = Gtk.Label(label="Keyboard Shortcut (Record or type):", xalign=0)
            box.pack_start(lbl_k, False, False, 0)

            recorder = KeybindRecorderBox(
                parent_dialog=dialog,
                initial_key=cb["key"],
                current_id=cb["id"],
                conflict_checker=self.check_conflict
            )
            box.pack_start(recorder, False, False, 0)

            lbl_act = Gtk.Label(label="Action Dispatcher (Lua):", xalign=0)
            box.pack_start(lbl_act, False, False, 0)
            entry_act = Gtk.Entry()
            entry_act.set_text(cb["action"])
            box.pack_start(entry_act, False, False, 0)

            lbl_desc = Gtk.Label(label="Description:", xalign=0)
            box.pack_start(lbl_desc, False, False, 0)
            entry_desc = Gtk.Entry()
            entry_desc.set_text(cb["desc"])
            box.pack_start(entry_desc, False, False, 0)

            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            btn_ok = dialog.add_button("Save Changes", Gtk.ResponseType.OK)
            btn_ok.get_style_context().add_class("accent")

            dialog.show_all()
            res = dialog.run()
            k = recorder.get_key()
            act = entry_act.get_text().strip()
            desc = entry_desc.get_text().strip()
            recorder.stop_recording()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and k and act:
                self.custom_binds[idx]["key"] = k
                self.custom_binds[idx]["action"] = act
                self.custom_binds[idx]["desc"] = desc or "Custom Shortcut"
                self.save_and_sync()

        def show_edit_plugin_dialog(self, plugin_id):
            if plugin_id not in self.plugin_binds:
                return
            pl = self.plugin_binds[plugin_id]

            dialog = Gtk.Dialog(title=f"Set Shortcut: {pl['name']}", flags=0)
            dialog.set_default_size(560, 290)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(10)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_info = Gtk.Label(
                label=f"<b>Plugin:</b> {pl['name']} ({'Custom' if pl.get('is_custom', True) else 'Built-in'})\n<span size='small'>{pl.get('desc', '')}</span>",
                xalign=0,
                use_markup=True
            )
            box.pack_start(lbl_info, False, False, 0)

            lbl_k = Gtk.Label(label="Keyboard Shortcut (Record or type):", xalign=0)
            box.pack_start(lbl_k, False, False, 0)

            recorder = KeybindRecorderBox(
                parent_dialog=dialog,
                initial_key=pl.get("key", ""),
                current_id=f"plugin:{plugin_id}",
                conflict_checker=self.check_conflict
            )
            box.pack_start(recorder, False, False, 0)

            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            btn_ok = dialog.add_button("Save Shortcut", Gtk.ResponseType.OK)
            btn_ok.get_style_context().add_class("accent")

            dialog.show_all()
            res = dialog.run()
            new_key = recorder.get_key()
            recorder.stop_recording()
            dialog.destroy()

            if res == Gtk.ResponseType.OK:
                self.plugin_binds[plugin_id]["key"] = new_key
                self.plugin_binds[plugin_id]["enabled"] = bool(new_key)
                self.save_and_sync()

        def save_and_sync(self):
            save_user_keybinds_state(
                self.disabled_defaults,
                self.overrides,
                self.custom_binds,
                self.plugin_binds
            )
            self.live_binds = get_live_hyprctl_binds()
            self.refresh_all()

        def open_in_editor(self):
            editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nvim"
            if shutil.which("foot") and editor in ["nvim", "vim", "nano"]:
                subprocess.Popen(["foot", editor, str(USER_KEYBINDS_PATH)])
            else:
                subprocess.Popen([editor, str(USER_KEYBINDS_PATH)])

        def reload_hyprland(self):
            run_cmd(["hyprctl", "reload"])
            self.live_binds = get_live_hyprctl_binds()
            run_cmd([
                "notify-send",
                "-a", "Hyprland Keybindings",
                "-i", "preferences-desktop-keyboard",
                "⌨️ Keybindings Reloaded",
                "Hyprland configuration reloaded successfully."
            ])

        def refresh_all(self):
            self.populate_defaults_list()
            self.populate_custom_list()
            self.populate_plugins_list()
            self.refresh_lua_view()
            self.lbl_sub.set_text(
                f"Active System Theme: {theme_name.title()}  •  {len(self.default_binds)} Defaults  •  "
                f"{len(self.custom_binds)} Custom  •  {len(self.plugin_binds)} Plugins"
            )

    win = KeybindsManagerWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    if start_tab and 0 <= start_tab < 4:
        win.notebook.set_current_page(start_tab)
    Gtk.main()


if __name__ == "__main__":
    tab = 0
    for arg in sys.argv[1:]:
        if arg.startswith("--tab="):
            try:
                tab = int(arg.split("=")[1])
            except ValueError:
                pass
    launch_keybind_manager_gui(start_tab=tab)
