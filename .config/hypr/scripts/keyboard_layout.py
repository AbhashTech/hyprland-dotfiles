#!/usr/bin/env python3
"""
=============================================================================
Hyprland Keyboard Layout & Variant Manager Utility (Desktop GUI & CLI)
=============================================================================
A modern, native graphical (GTK3) and CLI/Fuzzel utility to:
- Dynamically adapt the active system theme palette (Catppuccin, Tokyo Night, etc.)
- Switch and cycle active keyboard layouts & variants live across all keyboards
- Search, browse, and add regional layouts & ergonomic variants (Indian languages,
  Dvorak, Colemak, French Bépo, European, Asian, etc.)
- Test active layouts immediately in an integrated interactive typing test area
- Configure XKB layout switching options (Alt+Shift, Super+Space, CapsLock mods)
- Synchronize kb_layout, kb_variant, and kb_options in input.lua safely & persistently
- Integrate with App Menus, Quickshell, Waybar, and Hyprland keybindings
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
DOTFILES_CONFIG_DIR = HOME / ".dotfiles" / ".config"
INPUT_CONFIG_PATH = CONFIG_DIR / "hypr" / "modules" / "input.lua"
DOTFILES_INPUT_PATH = DOTFILES_CONFIG_DIR / "hypr" / "modules" / "input.lua"
XKB_BASE_LST = Path("/usr/share/X11/xkb/rules/base.lst")
XKB_EVDEV_LST = Path("/usr/share/X11/xkb/rules/evdev.lst")

# Curated Popular, Regional, and Ergonomic Layouts for fast discovery
CURATED_POPULAR = [
    # US & Ergonomic Variants
    {"lay": "us", "var": "", "desc": "English (US)", "group": "Popular", "flag": "🇺🇸"},
    {"lay": "gb", "var": "", "desc": "English (UK)", "group": "Popular", "flag": "🇬🇧"},
    {"lay": "us", "var": "intl", "desc": "English (US, intl with AltGr dead keys)", "group": "Popular", "flag": "🇺🇸"},
    {"lay": "us", "var": "altgr-intl", "desc": "English (US, intl AltGr dead keys)", "group": "Popular", "flag": "🇺🇸"},
    {"lay": "us", "var": "dvorak", "desc": "English (Dvorak ergonomic)", "group": "Ergonomic", "flag": "⌨️"},
    {"lay": "us", "var": "dvorak-programmer", "desc": "English (Programmer Dvorak)", "group": "Ergonomic", "flag": "⌨️"},
    {"lay": "us", "var": "colemak", "desc": "English (Colemak ergonomic)", "group": "Ergonomic", "flag": "⌨️"},
    {"lay": "us", "var": "colemak_dh", "desc": "English (Colemak DH ergonomic)", "group": "Ergonomic", "flag": "⌨️"},
    {"lay": "us", "var": "workman", "desc": "English (Workman ergonomic)", "group": "Ergonomic", "flag": "⌨️"},

    # Indian Languages & Regional Variants
    {"lay": "in", "var": "eng", "desc": "English (India, with Rupee ₹)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "bolnagri", "desc": "Hindi (Bolnagri phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "hin-kagapa", "desc": "Hindi (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "deva", "desc": "Hindi (Devanagari InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "mar-kagapa", "desc": "Marathi (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "marathi", "desc": "Marathi (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "tam", "desc": "Tamil (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "tamilnet", "desc": "Tamil (TamilNet '99)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "tel", "desc": "Telugu (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "tel-kagapa", "desc": "Telugu (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "kan", "desc": "Kannada (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "kan-kagapa", "desc": "Kannada (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "mal", "desc": "Malayalam (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "mal_lalitha", "desc": "Malayalam (Lalitha)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "guj", "desc": "Gujarati (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "guj-kagapa", "desc": "Gujarati (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "ben", "desc": "Bangla / Bengali (India)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "ben_probhat", "desc": "Bangla / Bengali (Probhat)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "guru", "desc": "Punjabi (Gurmukhi)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "san-kagapa", "desc": "Sanskrit (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "ori", "desc": "Odia / Oriya (InScript)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "asm-kagapa", "desc": "Assamese (KaGaPa, phonetic)", "group": "Indic", "flag": "🇮🇳"},
    {"lay": "in", "var": "urd-phonetic", "desc": "Urdu (Phonetic)", "group": "Indic", "flag": "🇮🇳"},

    # European Languages
    {"lay": "de", "var": "", "desc": "German (Germany)", "group": "European", "flag": "🇩🇪"},
    {"lay": "de", "var": "nodeadkeys", "desc": "German (no dead keys)", "group": "European", "flag": "🇩🇪"},
    {"lay": "fr", "var": "", "desc": "French (France, AZERTY)", "group": "European", "flag": "🇫🇷"},
    {"lay": "fr", "var": "bepo", "desc": "French (Bépo ergonomic)", "group": "Ergonomic", "flag": "🇫🇷"},
    {"lay": "fr", "var": "oss", "desc": "French (AltGr dead keys)", "group": "European", "flag": "🇫🇷"},
    {"lay": "es", "var": "", "desc": "Spanish (Spain)", "group": "European", "flag": "🇪🇸"},
    {"lay": "latam", "var": "", "desc": "Spanish (Latin American)", "group": "Popular", "flag": "🇲🇽"},
    {"lay": "it", "var": "", "desc": "Italian (Italy)", "group": "European", "flag": "🇮🇹"},
    {"lay": "pt", "var": "", "desc": "Portuguese (Portugal)", "group": "European", "flag": "🇵🇹"},
    {"lay": "br", "var": "", "desc": "Portuguese (Brazil, ABNT2)", "group": "Popular", "flag": "🇧🇷"},
    {"lay": "ru", "var": "", "desc": "Russian (Standard)", "group": "European", "flag": "🇷🇺"},
    {"lay": "ru", "var": "phonetic", "desc": "Russian (Phonetic)", "group": "European", "flag": "🇷🇺"},
    {"lay": "ua", "var": "", "desc": "Ukrainian (Standard)", "group": "European", "flag": "🇺🇦"},
    {"lay": "pl", "var": "", "desc": "Polish (Programmers)", "group": "European", "flag": "🇵🇱"},
    {"lay": "cz", "var": "", "desc": "Czech (QWERTZ)", "group": "European", "flag": "🇨🇿"},
    {"lay": "cz", "var": "qwerty", "desc": "Czech (QWERTY)", "group": "European", "flag": "🇨🇿"},
    {"lay": "gr", "var": "", "desc": "Greek", "group": "European", "flag": "🇬🇷"},
    {"lay": "tr", "var": "", "desc": "Turkish (Q)", "group": "European", "flag": "🇹🇷"},
    {"lay": "tr", "var": "f", "desc": "Turkish (F ergonomic)", "group": "Ergonomic", "flag": "🇹🇷"},
    {"lay": "se", "var": "", "desc": "Swedish", "group": "European", "flag": "🇸🇪"},
    {"lay": "no", "var": "", "desc": "Norwegian", "group": "European", "flag": "🇳🇴"},
    {"lay": "dk", "var": "", "desc": "Danish", "group": "European", "flag": "🇩🇰"},
    {"lay": "fi", "var": "", "desc": "Finnish", "group": "European", "flag": "🇫🇮"},
    {"lay": "nl", "var": "", "desc": "Dutch", "group": "European", "flag": "🇳🇱"},
    {"lay": "hu", "var": "", "desc": "Hungarian", "group": "European", "flag": "🇭🇺"},
    {"lay": "ro", "var": "", "desc": "Romanian", "group": "European", "flag": "🇷🇴"},

    # Asian & Middle Eastern
    {"lay": "ara", "var": "", "desc": "Arabic (Standard)", "group": "Asian & Middle East", "flag": "🇸🇦"},
    {"lay": "ara", "var": "digits", "desc": "Arabic (with Eastern Arabic numerals)", "group": "Asian & Middle East", "flag": "🇸🇦"},
    {"lay": "ir", "var": "", "desc": "Persian / Farsi (Iran)", "group": "Asian & Middle East", "flag": "🇮🇷"},
    {"lay": "il", "var": "", "desc": "Hebrew (Israel)", "group": "Asian & Middle East", "flag": "🇮🇱"},
    {"lay": "jp", "var": "", "desc": "Japanese", "group": "Asian & Middle East", "flag": "🇯🇵"},
    {"lay": "cn", "var": "", "desc": "Chinese", "group": "Asian & Middle East", "flag": "🇨🇳"},
    {"lay": "kr", "var": "", "desc": "Korean", "group": "Asian & Middle East", "flag": "🇰🇷"},
    {"lay": "th", "var": "", "desc": "Thai", "group": "Asian & Middle East", "flag": "🇹🇭"},
    {"lay": "vn", "var": "", "desc": "Vietnamese", "group": "Asian & Middle East", "flag": "🇻🇳"},
]

POPULAR_OPTIONS = [
    ("grp:alt_shift_toggle", "Alt + Shift Toggle", "Toggle layout using Left Alt + Left Shift"),
    ("grp:win_space_toggle", "Super + Space Toggle", "Toggle layout using Super (Windows key) + Space"),
    ("grp:ctrl_shift_toggle", "Ctrl + Shift Toggle", "Toggle layout using Ctrl + Shift"),
    ("grp:caps_toggle", "CapsLock Toggle", "Toggle layout using CapsLock key"),
    ("caps:swapescape", "Swap CapsLock & Escape", "Swap Escape and CapsLock positions (popular for Vim)"),
    ("caps:escape", "CapsLock as Escape", "Make CapsLock act as an additional Escape key"),
    ("caps:ctrl_modifier", "CapsLock as Ctrl", "Make CapsLock act as an additional Ctrl key"),
    ("compose:ralt", "Compose Key on Right Alt", "Right Alt acts as Compose key for special accents & symbols"),
    ("terminate:ctrl_alt_bksp", "Kill X/Wayland on Ctrl+Alt+Bksp", "Emergency restart of graphical session"),
]


# =============================================================================
# 🎨 Dynamic Theme Palette Engine
# =============================================================================

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


def run_cmd(cmd, check=False):
    """Run shell command safely and return stdout string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""


def show_notification(title, body, icon="input-keyboard", urgency="low"):
    """Display a desktop notification."""
    run_cmd([
        "notify-send",
        "-r", "9130",
        "-t", "2500",
        "-u", urgency,
        "-a", "Keyboard Layout Manager",
        "-i", icon,
        "-h", "string:x-canonical-private-synchronous:keyboard_layout",
        title,
        body
    ])


# =============================================================================
# 📖 XKB Database Parser & Layout Info
# =============================================================================

def parse_all_xkb_catalog():
    """
    Parse base layouts and all layout variants from XKB rules.
    Returns:
      layouts: dict of code -> description
      variants: dict of (lay_code, var_code) -> description
    """
    lst_path = XKB_BASE_LST if XKB_BASE_LST.exists() else XKB_EVDEV_LST
    layouts = {}
    variants = {}

    if lst_path.exists():
        try:
            with open(lst_path, "r", encoding="utf-8", errors="ignore") as f:
                section = None
                for line in f:
                    l = line.strip()
                    if l.startswith("! "):
                        section = l[2:].strip()
                        continue
                    if not l or not section:
                        continue
                    parts = line.split(maxsplit=1)
                    if len(parts) < 2:
                        continue
                    code = parts[0].strip()
                    desc = parts[1].strip()
                    if section == "layout":
                        layouts[code] = desc
                    elif section == "variant":
                        if ":" in desc:
                            lay_part, var_desc = desc.split(":", 1)
                            lay_code = lay_part.strip()
                            variants[(lay_code, code)] = var_desc.strip()
        except Exception:
            pass

    return layouts, variants


def get_entry_description(lay, var, layouts_map=None, variants_map=None):
    """Get readable description for a layout/variant combo."""
    if var:
        for c in CURATED_POPULAR:
            if c["lay"] == lay and c["var"] == var:
                return c["desc"]
        if variants_map and (lay, var) in variants_map:
            return variants_map[(lay, var)]
        return f"{lay.upper()} ({var})"
    else:
        for c in CURATED_POPULAR:
            if c["lay"] == lay and not c["var"]:
                return c["desc"]
        if layouts_map and lay in layouts_map:
            return layouts_map[lay]
        return lay.upper()


def get_entry_flag(lay, var):
    """Get country flag or symbol for entry."""
    for c in CURATED_POPULAR:
        if c["lay"] == lay and c["var"] == var:
            return c.get("flag", "⌨️")
    for c in CURATED_POPULAR:
        if c["lay"] == lay:
            return c.get("flag", "⌨️")
    return "⌨️"


def format_entry_tag(lay, var):
    """Return compact representation e.g. 'us' or 'in(bolnagri)'."""
    return f"{lay}({var})" if var else lay


def parse_layout_arg(arg):
    """Parse user argument e.g. 'in(bolnagri)', 'in:bolnagri', or 'in'."""
    arg = arg.strip()
    match = re.match(r'^([a-zA-Z0-9_-]+)[(:]([a-zA-Z0-9_-]+)\)?$', arg)
    if match:
        return match.group(1).lower(), match.group(2).lower()
    return arg.lower(), ""


def get_hypr_keyboards():
    """Get all keyboard devices from hyprctl."""
    raw = run_cmd(["hyprctl", "devices", "-j"])
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data.get("keyboards", [])
    except Exception:
        return []


def get_main_keyboard():
    """Find the primary active keyboard device."""
    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        if kb.get("main"):
            return kb
    for kb in keyboards:
        name = kb.get("name", "").lower()
        if "receiver" in name or "keyboard" in name:
            return kb
    return keyboards[0] if keyboards else None


def get_configured_from_file():
    """Read currently configured layouts and options from input.lua."""
    target_files = [
        INPUT_CONFIG_PATH.resolve() if INPUT_CONFIG_PATH.exists() else None,
        DOTFILES_INPUT_PATH.resolve() if DOTFILES_INPUT_PATH.exists() else None,
        INPUT_CONFIG_PATH,
        DOTFILES_INPUT_PATH
    ]
    config_file = None
    for f in target_files:
        if f and f.exists():
            config_file = f
            break

    if not config_file:
        return {"layouts": ["us"], "variants": [""], "options": ""}

    try:
        content = config_file.read_text(encoding="utf-8")

        layout_match = re.search(r'kb_layout\s*=\s*["\']([^"\']*)["\']', content)
        variant_match = re.search(r'kb_variant\s*=\s*["\']([^"\']*)["\']', content)
        options_match = re.search(r'kb_options\s*=\s*["\']([^"\']*)["\']', content)

        kb_layout_str = layout_match.group(1).strip() if layout_match else "us"
        kb_variant_str = variant_match.group(1).strip() if variant_match else ""
        kb_options_str = options_match.group(1).strip() if options_match else ""

        layouts = [l.strip() for l in kb_layout_str.split(",") if l.strip()]
        if not layouts:
            layouts = ["us"]

        raw_variants = [v.strip() for v in kb_variant_str.split(",")] if kb_variant_str else []
        variants = []
        for i in range(len(layouts)):
            variants.append(raw_variants[i] if i < len(raw_variants) else "")

        return {
            "layouts": layouts,
            "variants": variants,
            "options": kb_options_str
        }
    except Exception:
        return {"layouts": ["us"], "variants": [""], "options": ""}


def get_active_layout_info():
    """Return active layout state including pairs of (layout, variant)."""
    conf = get_configured_from_file()
    layouts = conf["layouts"]
    variants = conf["variants"]

    main_kb = get_main_keyboard()
    active_idx = 0
    active_keymap = "English (US)"

    if main_kb:
        active_idx = main_kb.get("active_layout_index", 0)
        active_keymap = main_kb.get("active_keymap", "English (US)")

    if active_idx >= len(layouts):
        active_idx = 0

    curr_lay = layouts[active_idx] if layouts else "us"
    curr_var = variants[active_idx] if active_idx < len(variants) else ""
    curr_tag = format_entry_tag(curr_lay, curr_var)

    pairs = list(zip(layouts, variants))

    return {
        "active_index": active_idx,
        "active_keymap": active_keymap,
        "current_lay": curr_lay,
        "current_var": curr_var,
        "current_tag": curr_tag,
        "pairs": pairs,
        "layouts": layouts,
        "variants": variants,
        "options": conf["options"]
    }


def save_and_apply_config(layouts, variants, options=None):
    """Update input.lua and apply live via Hyprland IPC."""
    if not layouts:
        layouts = ["us"]
        variants = [""]

    while len(variants) < len(layouts):
        variants.append("")

    kb_layout_str = ",".join(layouts)
    kb_variant_str = ",".join(variants)

    # Save to disk across potential paths
    target_files = set()
    for p in [INPUT_CONFIG_PATH, DOTFILES_INPUT_PATH]:
        if p.exists():
            target_files.add(p.resolve())
            target_files.add(p)

    for config_file in target_files:
        try:
            content = config_file.read_text(encoding="utf-8")

            # Replace kb_layout
            if re.search(r'kb_layout\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_layout\s*=\s*["\'][^"\']*["\']',
                    f'kb_layout  = "{kb_layout_str}"',
                    content
                )

            # Replace kb_variant
            if re.search(r'kb_variant\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_variant\s*=\s*["\'][^"\']*["\']',
                    f'kb_variant = "{kb_variant_str}"',
                    content
                )

            # Replace kb_options if given
            if options is not None and re.search(r'kb_options\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_options\s*=\s*["\'][^"\']*["\']',
                    f'kb_options = "{options}"',
                    content
                )

            config_file.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: writing {config_file} failed: {e}", file=sys.stderr)

    # Apply live to Hyprland
    lua_code = f'hl.config({{ input = {{ kb_layout = "{kb_layout_str}", kb_variant = "{kb_variant_str}" }} }})'
    run_cmd(["hyprctl", "eval", lua_code])
    run_cmd(["hyprctl", "reload"])


def switch_next_layout():
    """Cycle to next configured keyboard layout/variant across keyboards."""
    info = get_active_layout_info()
    if len(info["pairs"]) <= 1:
        show_notification(
            "󰌌  Single Layout Configured",
            f"Current: <b>{info['active_keymap']}</b>\nOpen <b>Keyboard Layout Manager</b> to add more layouts!"
        )
        print("Only 1 layout is configured.")
        return

    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        kb_name = kb.get("name")
        if kb_name:
            run_cmd(["hyprctl", "switchxkblayout", kb_name, "next"])

    new_info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()
    curr_desc = get_entry_description(new_info["current_lay"], new_info["current_var"], l_map, v_map)

    layouts_display = " • ".join([
        f"<b><u>{format_entry_tag(l, v).upper()}</u></b>" if i == new_info["active_index"] else format_entry_tag(l, v).upper()
        for i, (l, v) in enumerate(new_info["pairs"])
    ])

    show_notification(
        "󰌌  Keyboard Layout Switched",
        f"Active: <b>{curr_desc}</b>\nLayouts: {layouts_display}"
    )
    print(f"Switched to: {curr_desc} [{format_entry_tag(new_info['current_lay'], new_info['current_var'])}]")


def switch_prev_layout():
    """Cycle to previous configured keyboard layout/variant."""
    info = get_active_layout_info()
    if len(info["pairs"]) <= 1:
        return

    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        kb_name = kb.get("name")
        if kb_name:
            run_cmd(["hyprctl", "switchxkblayout", kb_name, "prev"])

    new_info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()
    curr_desc = get_entry_description(new_info["current_lay"], new_info["current_var"], l_map, v_map)

    show_notification(
        "󰌌  Keyboard Layout Switched",
        f"Active: <b>{curr_desc}</b>"
    )
    print(f"Switched to: {curr_desc} [{format_entry_tag(new_info['current_lay'], new_info['current_var'])}]")


def set_layout_by_index_or_tag(target):
    """Switch directly to a layout by index or tag (e.g. '0', 'in(bolnagri)', 'us')."""
    info = get_active_layout_info()
    pairs = info["pairs"]
    target_idx = -1

    if str(target).isdigit():
        idx = int(target)
        if 0 <= idx < len(pairs):
            target_idx = idx
    else:
        req_lay, req_var = parse_layout_arg(target)
        for i, (l, v) in enumerate(pairs):
            if l.lower() == req_lay and v.lower() == req_var:
                target_idx = i
                break
        if target_idx == -1:
            for i, (l, v) in enumerate(pairs):
                if l.lower() == req_lay:
                    target_idx = i
                    break

    if target_idx != -1:
        keyboards = get_hypr_keyboards()
        for kb in keyboards:
            kb_name = kb.get("name")
            if kb_name:
                run_cmd(["hyprctl", "switchxkblayout", kb_name, str(target_idx)])
        new_info = get_active_layout_info()
        l_map, v_map = parse_all_xkb_catalog()
        desc = get_entry_description(new_info["current_lay"], new_info["current_var"], l_map, v_map)
        show_notification(
            "󰌌  Keyboard Layout Changed",
            f"Active: <b>{desc}</b>"
        )
        print(f"Switched to layout {target_idx}: {desc}")
    else:
        print(f"Layout '{target}' not found in active layouts: {[format_entry_tag(l, v) for l, v in pairs]}", file=sys.stderr)


def add_layout(layout_arg, variant_arg=""):
    """Add a layout or layout(variant) to configured list."""
    if variant_arg:
        lay, var = layout_arg.strip().lower(), variant_arg.strip().lower()
    else:
        lay, var = parse_layout_arg(layout_arg)

    if not lay:
        return False

    conf = get_configured_from_file()
    layouts = list(conf["layouts"])
    variants = list(conf["variants"])

    for i, (l, v) in enumerate(zip(layouts, variants)):
        if l == lay and v == var:
            tag = format_entry_tag(lay, var)
            show_notification(
                "󰌌  Keyboard Layout Info",
                f"Layout <b>{tag.upper()}</b> is already configured."
            )
            print(f"Layout '{tag}' is already configured.")
            set_layout_by_index_or_tag(str(i))
            return True

    layouts.append(lay)
    variants.append(var)

    save_and_apply_config(layouts, variants)
    set_layout_by_index_or_tag(str(len(layouts) - 1))

    l_map, v_map = parse_all_xkb_catalog()
    desc = get_entry_description(lay, var, l_map, v_map)
    all_tags = ", ".join([format_entry_tag(l, v).upper() for l, v in zip(layouts, variants)])

    show_notification(
        "󰐕  Keyboard Layout Added",
        f"Added: <b>{desc}</b>\nActive layouts: <b>{all_tags}</b>"
    )
    print(f"Successfully added layout '{format_entry_tag(lay, var)}' ({desc}). Active: {all_tags}")
    return True


def remove_layout(layout_arg, variant_arg=""):
    """Remove a layout/variant from configured list."""
    if variant_arg:
        lay, var = layout_arg.strip().lower(), variant_arg.strip().lower()
    else:
        lay, var = parse_layout_arg(layout_arg)

    conf = get_configured_from_file()
    layouts = list(conf["layouts"])
    variants = list(conf["variants"])

    target_idx = -1
    for i, (l, v) in enumerate(zip(layouts, variants)):
        if l == lay and v == var:
            target_idx = i
            break
    if target_idx == -1:
        for i, (l, v) in enumerate(zip(layouts, variants)):
            if l == lay:
                target_idx = i
                break

    if target_idx == -1:
        print(f"Layout '{format_entry_tag(lay, var)}' is not in configured layouts.", file=sys.stderr)
        return False

    if len(layouts) <= 1:
        show_notification(
            "⚠️  Cannot Remove Layout",
            "At least one keyboard layout must remain configured!",
            urgency="normal"
        )
        print("Cannot remove the only remaining keyboard layout.", file=sys.stderr)
        return False

    removed_tag = format_entry_tag(layouts[target_idx], variants[target_idx])
    del layouts[target_idx]
    del variants[target_idx]

    save_and_apply_config(layouts, variants)
    set_layout_by_index_or_tag("0")

    all_tags = ", ".join([format_entry_tag(l, v).upper() for l, v in zip(layouts, variants)])
    show_notification(
        "󰍵  Keyboard Layout Removed",
        f"Removed: <b>{removed_tag.upper()}</b>\nRemaining: <b>{all_tags}</b>"
    )
    print(f"Successfully removed layout '{removed_tag}'. Active: {all_tags}")
    return True


def reorder_layout(from_idx, to_idx):
    """Reorder a layout in the configured list."""
    conf = get_configured_from_file()
    layouts = list(conf["layouts"])
    variants = list(conf["variants"])

    if 0 <= from_idx < len(layouts) and 0 <= to_idx < len(layouts):
        lay = layouts.pop(from_idx)
        var = variants.pop(from_idx)
        layouts.insert(to_idx, lay)
        variants.insert(to_idx, var)
        save_and_apply_config(layouts, variants)
        set_layout_by_index_or_tag(str(to_idx))
        return True
    return False


# =============================================================================
# 🚀 Interactive Fuzzel / Dmenu Menu Mode
# =============================================================================

def run_fuzzel_menu(prompt, lines_list):
    """Display interactive Fuzzel fuzzy-search dmenu or fallback."""
    menu_input = "\n".join(lines_list)
    if shutil.which("fuzzel"):
        try:
            res = subprocess.run(
                [
                    "fuzzel",
                    "--dmenu",
                    "--prompt", prompt,
                    "--lines", str(min(max(len(lines_list), 4), 16)),
                    "--width", "56",
                ],
                input=menu_input,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
            return None
        except Exception:
            return None
    elif shutil.which("wofi"):
        try:
            res = subprocess.run(
                [
                    "wofi",
                    "--dmenu",
                    "--prompt", prompt,
                    "--lines", str(min(max(len(lines_list), 4), 16)),
                    "--width", "560",
                ],
                input=menu_input,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
            return None
        except Exception:
            return None
    return None


def gui_add_layout_menu():
    """Interactive Fuzzel search menu to add any layout or variant."""
    l_map, v_map = parse_all_xkb_catalog()
    conf = get_configured_from_file()
    configured_pairs = set(zip(conf["layouts"], conf["variants"]))

    menu_lines = []
    item_map = {}
    seen = set()

    for item in CURATED_POPULAR:
        lay, var, desc, flag = item["lay"], item["var"], item["desc"], item.get("flag", "⌨️")
        is_conf = (lay, var) in configured_pairs
        tag = format_entry_tag(lay, var)
        status = " (Configured)" if is_conf else ""
        line = f"{flag} {tag:<16} │ {desc}{status}"
        menu_lines.append(line)
        item_map[line] = (lay, var)
        seen.add((lay, var))

    for (lay, var), desc in sorted(v_map.items(), key=lambda x: (x[0][0], x[1])):
        if (lay, var) not in seen:
            is_conf = (lay, var) in configured_pairs
            tag = format_entry_tag(lay, var)
            status = " (Configured)" if is_conf else ""
            line = f"  {tag:<16} │ {desc}{status}"
            menu_lines.append(line)
            item_map[line] = (lay, var)
            seen.add((lay, var))

    for lay, desc in sorted(l_map.items()):
        if (lay, "") not in seen:
            is_conf = (lay, "") in configured_pairs
            tag = lay
            status = " (Configured)" if is_conf else ""
            line = f"  {tag:<16} │ {desc}{status}"
            menu_lines.append(line)
            item_map[line] = (lay, "")
            seen.add((lay, ""))

    selected = run_fuzzel_menu("󰐕 Add Layout/Variant > ", menu_lines)
    if selected and selected in item_map:
        lay, var = item_map[selected]
        add_layout(lay, var)


def gui_remove_layout_menu():
    """Interactive Fuzzel menu to remove a configured layout."""
    conf = get_configured_from_file()
    pairs = list(zip(conf["layouts"], conf["variants"]))
    l_map, v_map = parse_all_xkb_catalog()

    if len(pairs) <= 1:
        show_notification(
            "⚠️  Cannot Remove Layout",
            f"Only 1 layout ({format_entry_tag(pairs[0][0], pairs[0][1]).upper()}) is configured. You cannot remove it.",
            urgency="normal"
        )
        return

    menu_lines = []
    item_map = {}

    for lay, var in pairs:
        desc = get_entry_description(lay, var, l_map, v_map)
        tag = format_entry_tag(lay, var)
        flag = get_entry_flag(lay, var)
        line = f"󰍵 {flag} Remove {tag.upper():<14} │ {desc}"
        menu_lines.append(line)
        item_map[line] = (lay, var)

    selected = run_fuzzel_menu("󰍵 Remove Layout > ", menu_lines)
    if selected and selected in item_map:
        lay, var = item_map[selected]
        remove_layout(lay, var)


def gui_fuzzel_main_menu():
    """Main interactive Fuzzel layout manager menu."""
    info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()

    menu_lines = []
    action_map = {}

    for idx, (lay, var) in enumerate(info["pairs"]):
        is_active = (idx == info["active_index"])
        desc = get_entry_description(lay, var, l_map, v_map)
        tag = format_entry_tag(lay, var).upper()
        flag = get_entry_flag(lay, var)
        indicator = "●" if is_active else "○"
        status_text = " [Active]" if is_active else ""
        line = f"{indicator} {flag} {tag:<12} ➜  {desc}{status_text}"
        menu_lines.append(line)
        action_map[line] = ("switch", str(idx))

    menu_lines.append("─────────────────────────────────────────────")
    action_map[menu_lines[-1]] = ("noop", None)

    line_cycle = "󰑐  Cycle Next Layout (Super+Ctrl+Space)"
    menu_lines.append(line_cycle)
    action_map[line_cycle] = ("cycle_next", None)

    line_add = "󰐕  Add New Regional Layout / Variant..."
    menu_lines.append(line_add)
    action_map[line_add] = ("gui_add", None)

    line_remove = "󰍵  Remove a Configured Layout..."
    menu_lines.append(line_remove)
    action_map[line_remove] = ("gui_remove", None)

    line_app = "🖥️  Open Full Desktop GUI App..."
    menu_lines.append(line_app)
    action_map[line_app] = ("gui_app", None)

    selected = run_fuzzel_menu("󰌌 Layout Manager > ", menu_lines)
    if not selected or selected not in action_map:
        return

    action, data = action_map[selected]
    if action == "switch":
        set_layout_by_index_or_tag(data)
    elif action == "cycle_next":
        switch_next_layout()
    elif action == "gui_add":
        gui_add_layout_menu()
    elif action == "gui_remove":
        gui_remove_layout_menu()
    elif action == "gui_app":
        launch_gtk_gui()


# =============================================================================
# 🖥️ Full Graphical GTK3 Desktop Application (Dynamic Theme Adaptation)
# =============================================================================

def launch_gtk_gui():
    """Launch full GTK3 desktop interface with theme styling."""
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gtk, Gdk, GLib
    except Exception as e:
        print(f"GTK3 initialization error: {e}", file=sys.stderr)
        return

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
    c_peach = colors.get("peach", "#fab387")

    accent_fg = get_contrast_color(c_accent)
    sapphire_fg = get_contrast_color(c_sapphire)
    blue_fg = get_contrast_color(c_blue)
    red_fg = get_contrast_color(c_red)
    green_fg = get_contrast_color(c_green)

    css_provider = Gtk.CssProvider()
    css_data = f"""
    * {{
        font-family: system-ui, -apple-system, 'Inter', 'Roboto', 'Noto Sans', 'JetBrainsMono Nerd Font', sans-serif;
    }}

    window, viewport, scrolledwindow, box, notebook, notebook > stack, notebook > stack > * {{
        background-color: {c_base};
        color: {c_text};
    }}

    .header-box {{
        background-color: {c_mantle};
        border-bottom: 2px solid {c_surface0};
        padding: 16px 24px;
    }}

    .title-label {{
        font-size: 20px;
        font-weight: 800;
        color: {c_accent};
    }}

    .subtitle-label {{
        font-size: 12px;
        color: {c_subtext1};
    }}

    /* Global button overrides */
    button {{
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 12px;
        transition: all 120ms ease-in-out;
    }}

    button.btn-primary {{
        background-color: {c_accent};
        background-image: none;
        border: 1px solid {c_accent};
        color: {accent_fg};
        font-weight: 800;
        padding: 8px 18px;
    }}
    button.btn-primary label {{
        color: {accent_fg};
        font-weight: 800;
    }}
    button.btn-primary:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}
    button.btn-primary:hover label {{
        color: {c_text};
    }}

    button.btn-secondary {{
        background-color: {c_surface0};
        background-image: none;
        border: 1px solid {c_surface2};
        color: {c_text};
        padding: 6px 14px;
    }}
    button.btn-secondary label {{
        color: {c_text};
        font-weight: bold;
    }}
    button.btn-secondary:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}

    button.btn-active-switch {{
        background-color: {c_sapphire};
        background-image: none;
        border: 1px solid {c_sapphire};
        color: {sapphire_fg};
        padding: 6px 14px;
    }}
    button.btn-active-switch label {{
        color: {c_crust};
        font-weight: 800;
    }}
    button.btn-active-switch:hover {{
        background-color: {c_blue};
        color: #000000;
    }}
    button.btn-active-switch:hover label {{
        color: #000000;
    }}

    button.btn-danger {{
        background-color: rgba(243, 139, 168, 0.12);
        background-image: none;
        border: 1px solid {c_red};
        color: {c_red};
        padding: 6px 12px;
    }}
    button.btn-danger label {{
        color: {c_red};
        font-weight: bold;
    }}
    button.btn-danger:hover {{
        background-color: {c_red};
        color: {red_fg};
    }}
    button.btn-danger:hover label {{
        color: {red_fg};
    }}

    /* Card Styling */
    .card-item {{
        background-color: {c_mantle};
        border: 1px solid {c_surface0};
        border-radius: 12px;
        padding: 14px 18px;
        margin: 6px 16px;
    }}
    .card-item:hover {{
        background-color: {c_surface0};
        border-color: {c_surface1};
    }}
    .card-active {{
        background-color: {c_surface0};
        border: 2px solid {c_accent};
    }}

    .tag-badge {{
        background-color: {c_surface1};
        border: 1px solid {c_surface2};
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
        color: {c_accent};
    }}

    .active-badge {{
        background-color: {c_accent};
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 800;
        color: {accent_fg};
    }}

    /* Live Testing Area */
    .typing-box {{
        background-color: {c_mantle};
        border: 1px solid {c_surface1};
        border-radius: 12px;
        padding: 14px 18px;
        margin: 12px 16px;
    }}

    entry.typing-entry {{
        background-color: {c_base};
        color: {c_text};
        border: 1px solid {c_surface2};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
    }}
    entry.typing-entry:focus {{
        border-color: {c_accent};
        background-color: {c_crust};
    }}

    /* Search Bar */
    entry.search-entry {{
        background-color: {c_mantle};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 10px;
        padding: 9px 14px;
        font-size: 13px;
    }}
    entry.search-entry:focus {{
        border-color: {c_accent};
        background-color: {c_crust};
    }}

    /* Filter Pills */
    .filter-pill {{
        background-color: {c_mantle};
        color: {c_subtext1};
        border: 1px solid {c_surface0};
        border-radius: 14px;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: bold;
    }}
    .filter-pill:checked {{
        background-color: {c_accent};
        color: {accent_fg};
        border-color: {c_accent};
    }}
    .filter-pill label {{
        color: {c_subtext1};
        font-weight: bold;
    }}
    .filter-pill:checked label {{
        color: {accent_fg};
        font-weight: 800;
    }}

    /* Notebook Tabs */
    notebook header {{
        background-color: {c_mantle};
        border-bottom: 1px solid {c_surface0};
        padding: 4px 12px;
    }}
    notebook tab {{
        background-color: transparent;
        color: {c_subtext1};
        padding: 10px 20px;
        font-size: 13px;
        font-weight: bold;
        border: none;
        border-bottom: 3px solid transparent;
    }}
    notebook tab label {{
        color: {c_subtext1};
        font-weight: bold;
    }}
    notebook tab:checked {{
        background-color: {c_base};
        border-bottom: 3px solid {c_accent};
    }}
    notebook tab:checked label {{
        color: {c_accent};
        font-weight: 800;
    }}

    /* Checkbuttons */
    checkbutton check {{
        min-width: 18px;
        min-height: 18px;
        border-radius: 5px;
        border: 2px solid {c_surface2};
        background-color: {c_surface0};
    }}
    checkbutton check:checked {{
        background-color: {c_accent};
        border-color: {c_accent};
        color: {c_crust};
    }}
    """

    css_provider.load_from_data(css_data.encode("utf-8"))
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    class KeyboardLayoutWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Keyboard Layout Manager")
            self.set_default_size(780, 680)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.l_map, self.v_map = parse_all_xkb_catalog()

            # Root vertical container
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_box)

            # 1. Header Bar
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header.get_style_context().add_class("header-box")

            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_title = Gtk.Label(label="⌨️  Keyboard Layout & Variant Manager", xalign=0)
            lbl_title.get_style_context().add_class("title-label")
            lbl_sub = Gtk.Label(
                label=f"Theme: {theme_name.replace('-', ' ').title()} • Live Hyprland XKB Switcher & Regional Installer",
                xalign=0
            )
            lbl_sub.get_style_context().add_class("subtitle-label")
            title_box.pack_start(lbl_title, False, False, 0)
            title_box.pack_start(lbl_sub, False, False, 0)
            header.pack_start(title_box, True, True, 0)

            # Cycle Next Quick Button
            btn_cycle = Gtk.Button(label="󰑐  Cycle Layout")
            btn_cycle.get_style_context().add_class("btn-primary")
            btn_cycle.connect("clicked", self.on_cycle_clicked)
            header.pack_start(btn_cycle, False, False, 4)

            # Refresh Button
            btn_refresh = Gtk.Button(label="🔄 Refresh")
            btn_refresh.get_style_context().add_class("btn-secondary")
            btn_refresh.connect("clicked", lambda b: self.refresh_all())
            header.pack_start(btn_refresh, False, False, 0)

            main_box.pack_start(header, False, False, 0)

            # 2. Notebook Navigation
            self.notebook = Gtk.Notebook()
            main_box.pack_start(self.notebook, True, True, 0)

            # Tab 1: Configured Layouts
            self.tab_configured = self.build_configured_tab()
            self.notebook.append_page(self.tab_configured, Gtk.Label(label="󰌌  Active Layouts"))

            # Tab 2: Layout Catalog
            self.tab_catalog = self.build_catalog_tab()
            self.notebook.append_page(self.tab_catalog, Gtk.Label(label="󰐕  Browse & Add Catalog"))

            # Tab 3: Options & Hardware
            self.tab_options = self.build_options_tab()
            self.notebook.append_page(self.tab_options, Gtk.Label(label="⚙️  Options & Devices"))

            self.refresh_all()

        def on_cycle_clicked(self, btn):
            switch_next_layout()
            self.refresh_all()

        def refresh_all(self):
            self.refresh_configured_list()
            self.refresh_catalog_list()
            self.refresh_devices_list()
            self.refresh_options_list()

        # =========================================================================
        # TAB 1: Configured Layouts & Active Switcher
        # =========================================================================
        def build_configured_tab(self):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            box.set_margin_top(12)
            box.set_margin_bottom(12)
            box.set_margin_start(8)
            box.set_margin_end(8)

            # Scrolled list of configured layout cards
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.configured_listbox = Gtk.ListBox()
            self.configured_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroller.add(self.configured_listbox)
            box.pack_start(scroller, True, True, 0)

            # Live Typing Test Box
            test_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            test_card.get_style_context().add_class("typing-box")

            t_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            self.lbl_test_title = Gtk.Label(label="⌨️  Interactive Typing Test Area", xalign=0)
            self.lbl_test_title.get_style_context().add_class("subtitle-label")
            t_head.pack_start(self.lbl_test_title, True, True, 0)

            btn_clear = Gtk.Button(label="Clear")
            btn_clear.get_style_context().add_class("btn-secondary")
            t_head.pack_start(btn_clear, False, False, 0)
            test_card.pack_start(t_head, False, False, 0)

            self.typing_entry = Gtk.Entry()
            self.typing_entry.get_style_context().add_class("typing-entry")
            self.typing_entry.set_placeholder_text("Click here and type to immediately test active layout characters & dead keys...")
            btn_clear.connect("clicked", lambda b: self.typing_entry.set_text(""))
            test_card.pack_start(self.typing_entry, False, False, 0)

            box.pack_start(test_card, False, False, 0)
            return box

        def refresh_configured_list(self):
            for child in self.configured_listbox.get_children():
                self.configured_listbox.remove(child)

            info = get_active_layout_info()
            pairs = info["pairs"]
            active_idx = info["active_index"]

            # Update typing test label
            curr_desc = get_entry_description(info["current_lay"], info["current_var"], self.l_map, self.v_map)
            self.lbl_test_title.set_markup(
                f"<b>⌨️ Interactive Typing Test Area</b> — Active: <span foreground='{c_accent}'><b>{curr_desc} ({info['current_tag'].upper()})</b></span>"
            )

            for idx, (lay, var) in enumerate(pairs):
                is_active = (idx == active_idx)
                desc = get_entry_description(lay, var, self.l_map, self.v_map)
                tag = format_entry_tag(lay, var).upper()
                flag = get_entry_flag(lay, var)

                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                card.get_style_context().add_class("card-item")
                if is_active:
                    card.get_style_context().add_class("card-active")

                # Flag & Info
                flag_lbl = Gtk.Label()
                flag_lbl.set_markup(f"<span size='16000'>{flag}</span>")
                card.pack_start(flag_lbl, False, False, 4)

                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                row_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                
                name_lbl = Gtk.Label(label=desc, xalign=0)
                name_lbl.get_style_context().add_class("subtitle-label")
                name_lbl.set_markup(f"<span size='12000' weight='bold'>{desc}</span>")
                row_top.pack_start(name_lbl, False, False, 0)

                tag_lbl = Gtk.Label(label=tag)
                tag_lbl.get_style_context().add_class("tag-badge")
                row_top.pack_start(tag_lbl, False, False, 0)

                if is_active:
                    act_badge = Gtk.Label(label="● Active")
                    act_badge.get_style_context().add_class("active-badge")
                    row_top.pack_start(act_badge, False, False, 0)

                info_box.pack_start(row_top, False, False, 0)

                variant_text = f"Layout Code: <code>{lay}</code>" + (f" • Variant: <code>{var}</code>" if var else "")
                sub_lbl = Gtk.Label(xalign=0)
                sub_lbl.set_markup(f"<span size='10000' foreground='{c_subtext0}'>{variant_text}</span>")
                info_box.pack_start(sub_lbl, False, False, 0)

                card.pack_start(info_box, True, True, 0)

                # Action Buttons
                actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

                if not is_active:
                    btn_switch = Gtk.Button(label="Switch to this")
                    btn_switch.get_style_context().add_class("btn-active-switch")
                    btn_switch.connect("clicked", lambda b, i=idx: self.on_switch_layout(i))
                    actions_box.pack_start(btn_switch, False, False, 0)

                # Reorder buttons
                if idx > 0:
                    btn_up = Gtk.Button(label="▲")
                    btn_up.get_style_context().add_class("btn-secondary")
                    btn_up.set_tooltip_text("Move layout up in switching order")
                    btn_up.connect("clicked", lambda b, i=idx: self.on_reorder(i, i - 1))
                    actions_box.pack_start(btn_up, False, False, 0)

                if idx < len(pairs) - 1:
                    btn_down = Gtk.Button(label="▼")
                    btn_down.get_style_context().add_class("btn-secondary")
                    btn_down.set_tooltip_text("Move layout down in switching order")
                    btn_down.connect("clicked", lambda b, i=idx: self.on_reorder(i, i + 1))
                    actions_box.pack_start(btn_down, False, False, 0)

                # Delete button (disabled if only 1 layout)
                if len(pairs) > 1:
                    btn_del = Gtk.Button(label="✕")
                    btn_del.get_style_context().add_class("btn-danger")
                    btn_del.set_tooltip_text("Remove this layout")
                    btn_del.connect("clicked", lambda b, l=lay, v=var: self.on_remove_layout(l, v))
                    actions_box.pack_start(btn_del, False, False, 0)

                card.pack_start(actions_box, False, False, 0)
                self.configured_listbox.add(card)

            self.configured_listbox.show_all()

        def on_switch_layout(self, index):
            set_layout_by_index_or_tag(str(index))
            self.refresh_all()

        def on_reorder(self, from_idx, to_idx):
            reorder_layout(from_idx, to_idx)
            self.refresh_all()

        def on_remove_layout(self, lay, var):
            remove_layout(lay, var)
            self.refresh_all()

        # =========================================================================
        # TAB 2: Browse & Add Catalog
        # =========================================================================
        def build_catalog_tab(self):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            box.set_margin_top(12)
            box.set_margin_bottom(12)
            box.set_margin_start(12)
            box.set_margin_end(12)

            # Search Bar
            self.search_entry = Gtk.Entry()
            self.search_entry.get_style_context().add_class("search-entry")
            self.search_entry.set_placeholder_text("🔍 Search by language, country, variant (e.g. Hindi, Bolnagri, Tamil, Dvorak, German)...")
            self.search_entry.connect("changed", lambda e: self.filter_catalog())
            box.pack_start(self.search_entry, False, False, 0)

            # Category filter pills
            pills_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.current_category = "All"
            self.cat_buttons = {}

            categories = [
                ("All", "All"),
                ("Popular", "⭐ Popular"),
                ("Indic", "🇮🇳 Indic & Regional"),
                ("European", "🌍 European"),
                ("Asian & Middle East", "🌏 Asian & Middle East"),
                ("Ergonomic", "⌨️ Ergonomic"),
            ]

            for cat_id, cat_title in categories:
                btn = Gtk.ToggleButton(label=cat_title)
                btn.get_style_context().add_class("filter-pill")
                if cat_id == "All":
                    btn.set_active(True)
                btn.connect("toggled", lambda b, c=cat_id: self.on_category_toggled(b, c))
                pills_box.pack_start(btn, False, False, 0)
                self.cat_buttons[cat_id] = btn

            box.pack_start(pills_box, False, False, 2)

            # Scrolled list of catalog items
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.catalog_listbox = Gtk.ListBox()
            self.catalog_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroller.add(self.catalog_listbox)
            box.pack_start(scroller, True, True, 0)

            return box

        def on_category_toggled(self, button, cat_id):
            if button.get_active():
                self.current_category = cat_id
                for cid, btn in self.cat_buttons.items():
                    if cid != cat_id and btn.get_active():
                        btn.set_active(False)
                self.filter_catalog()
            else:
                if self.current_category == cat_id:
                    button.set_active(True)

        def refresh_catalog_list(self):
            for child in self.catalog_listbox.get_children():
                self.catalog_listbox.remove(child)

            conf = get_configured_from_file()
            configured_set = set(zip(conf["layouts"], conf["variants"]))
            seen = set()

            self.catalog_items = []

            # 1. Curated list
            for item in CURATED_POPULAR:
                lay, var, desc, group, flag = item["lay"], item["var"], item["desc"], item["group"], item.get("flag", "⌨️")
                self.catalog_items.append({
                    "lay": lay, "var": var, "desc": desc, "group": group, "flag": flag,
                    "is_configured": (lay, var) in configured_set
                })
                seen.add((lay, var))

            # 2. XKB Variants
            for (lay, var), desc in sorted(self.v_map.items(), key=lambda x: (x[0][0], x[1])):
                if (lay, var) not in seen:
                    self.catalog_items.append({
                        "lay": lay, "var": var, "desc": desc, "group": "Other", "flag": "⌨️",
                        "is_configured": (lay, var) in configured_set
                    })
                    seen.add((lay, var))

            # 3. Base Layouts
            for lay, desc in sorted(self.l_map.items()):
                if (lay, "") not in seen:
                    self.catalog_items.append({
                        "lay": lay, "var": "", "desc": desc, "group": "Other", "flag": "⌨️",
                        "is_configured": (lay, "") in configured_set
                    })
                    seen.add((lay, ""))

            self.filter_catalog()

        def filter_catalog(self):
            for child in self.catalog_listbox.get_children():
                self.catalog_listbox.remove(child)

            query = self.search_entry.get_text().strip().lower()
            count = 0

            for item in self.catalog_items:
                # Category match
                if self.current_category != "All":
                    if item["group"] != self.current_category:
                        continue

                # Query match
                if query:
                    tag = format_entry_tag(item["lay"], item["var"]).lower()
                    desc = item["desc"].lower()
                    if query not in tag and query not in desc:
                        continue

                count += 1
                if count > 80:  # Prevent UI overload
                    break

                card = self.create_catalog_card(item)
                self.catalog_listbox.add(card)

            self.catalog_listbox.show_all()

        def create_catalog_card(self, item):
            lay, var, desc, flag = item["lay"], item["var"], item["desc"], item["flag"]
            is_conf = item["is_configured"]
            tag = format_entry_tag(lay, var).upper()

            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            card.get_style_context().add_class("card-item")

            flag_lbl = Gtk.Label()
            flag_lbl.set_markup(f"<span size='15000'>{flag}</span>")
            card.pack_start(flag_lbl, False, False, 2)

            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            row_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            name_lbl = Gtk.Label(xalign=0)
            name_lbl.set_markup(f"<span size='11500' weight='bold'>{desc}</span>")
            row_top.pack_start(name_lbl, False, False, 0)

            tag_lbl = Gtk.Label(label=tag)
            tag_lbl.get_style_context().add_class("tag-badge")
            row_top.pack_start(tag_lbl, False, False, 0)

            info_box.pack_start(row_top, False, False, 0)

            detail_text = f"Code: <code>{lay}</code>" + (f" • Variant: <code>{var}</code>" if var else "")
            sub_lbl = Gtk.Label(xalign=0)
            sub_lbl.set_markup(f"<span size='9500' foreground='{c_subtext0}'>{detail_text}</span>")
            info_box.pack_start(sub_lbl, False, False, 0)

            card.pack_start(info_box, True, True, 0)

            if is_conf:
                badge = Gtk.Label(label="✓ Configured")
                badge.get_style_context().add_class("tag-badge")
                card.pack_start(badge, False, False, 0)
            else:
                btn_add = Gtk.Button(label="󰐕  Add Layout")
                btn_add.get_style_context().add_class("btn-primary")
                btn_add.connect("clicked", lambda b, l=lay, v=var: self.on_add_layout_from_catalog(l, v))
                card.pack_start(btn_add, False, False, 0)

            return card

        def on_add_layout_from_catalog(self, lay, var):
            add_layout(lay, var)
            self.refresh_all()
            self.notebook.set_current_page(0)

        # =========================================================================
        # TAB 3: Options, Keybinds & Hardware
        # =========================================================================
        def build_options_tab(self):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(14)
            box.set_margin_end(14)

            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            scroller.add(content_box)
            box.pack_start(scroller, True, True, 0)

            # Section 1: Connected Hardware Keyboards
            sec1_title = Gtk.Label(xalign=0)
            sec1_title.set_markup(f"<span size='13000' weight='bold' foreground='{c_accent}'>⌨️ Detected Keyboard Hardware Devices</span>")
            content_box.pack_start(sec1_title, False, False, 0)

            self.devices_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            content_box.pack_start(self.devices_box, False, False, 0)

            # Section 2: Layout Switching & XKB Options
            sec2_title = Gtk.Label(xalign=0)
            sec2_title.set_markup(f"<span size='13000' weight='bold' foreground='{c_accent}'>⚙️ XKB Input Switching & Modifier Options</span>")
            content_box.pack_start(sec2_title, False, False, 4)

            self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            content_box.pack_start(self.options_box, False, False, 0)

            # Section 3: Keybinding Shortcuts Reference
            sec3_title = Gtk.Label(xalign=0)
            sec3_title.set_markup(f"<span size='13000' weight='bold' foreground='{c_accent}'>⚡ Configured Desktop Keybindings</span>")
            content_box.pack_start(sec3_title, False, False, 4)

            keybinds_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            keybinds_card.get_style_context().add_class("card-item")

            shortcuts = [
                ("SUPER + CTRL + Space", "Cycle Next Keyboard Layout"),
                ("SUPER + CTRL + K", "Open Layout Switcher Menu"),
                ("SUPER + CTRL + SHIFT + K", "Search & Add Regional Layout Catalog"),
                ("Waybar / Quickshell Language Module", "Click to cycle layout, right-click for manager menu"),
            ]
            for key, act in shortcuts:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                lbl_k = Gtk.Label(xalign=0)
                lbl_k.set_markup(f"<span weight='bold' foreground='{c_yellow}'><code>{key}</code></span>")
                row.pack_start(lbl_k, False, False, 0)

                lbl_a = Gtk.Label(xalign=0)
                lbl_a.set_markup(f"<span foreground='{c_text}'>➜  {act}</span>")
                row.pack_start(lbl_a, True, True, 0)
                keybinds_card.pack_start(row, False, False, 2)

            content_box.pack_start(keybinds_card, False, False, 0)

            return box

        def refresh_devices_list(self):
            for child in self.devices_box.get_children():
                self.devices_box.remove(child)

            keyboards = get_hypr_keyboards()
            if not keyboards:
                empty_lbl = Gtk.Label(label="No keyboard devices detected.", xalign=0)
                self.devices_box.pack_start(empty_lbl, False, False, 0)
                return

            for kb in keyboards:
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                card.get_style_context().add_class("card-item")

                icon_lbl = Gtk.Label()
                icon_lbl.set_markup("<span size='14000'>⌨️</span>")
                card.pack_start(icon_lbl, False, False, 0)

                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                name_lbl = Gtk.Label(xalign=0)
                name_lbl.set_markup(f"<span weight='bold'>{kb.get('name', 'Unknown Keyboard')}</span>")
                info_box.pack_start(name_lbl, False, False, 0)

                sub_text = f"Keymap: <b>{kb.get('active_keymap', 'Default')}</b>"
                if kb.get("main"):
                    sub_text += f" • <span foreground='{c_green}'><b>[Main Primary Keyboard]</b></span>"
                sub_lbl = Gtk.Label(xalign=0)
                sub_lbl.set_markup(f"<span size='10000' foreground='{c_subtext0}'>{sub_text}</span>")
                info_box.pack_start(sub_lbl, False, False, 0)

                card.pack_start(info_box, True, True, 0)
                self.devices_box.pack_start(card, False, False, 0)

            self.devices_box.show_all()

        def refresh_options_list(self):
            for child in self.options_box.get_children():
                self.options_box.remove(child)

            conf = get_configured_from_file()
            current_options = set([o.strip() for o in conf.get("options", "").split(",") if o.strip()])

            for opt_code, opt_title, opt_desc in POPULAR_OPTIONS:
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                card.get_style_context().add_class("card-item")

                chk = Gtk.CheckButton()
                chk.set_active(opt_code in current_options)
                chk.connect("toggled", lambda b, c=opt_code: self.on_option_toggled(c, b.get_active()))
                card.pack_start(chk, False, False, 0)

                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                title_lbl = Gtk.Label(xalign=0)
                title_lbl.set_markup(f"<span weight='bold'>{opt_title}</span> <code>({opt_code})</code>")
                info_box.pack_start(title_lbl, False, False, 0)

                desc_lbl = Gtk.Label(xalign=0)
                desc_lbl.set_markup(f"<span size='10000' foreground='{c_subtext0}'>{opt_desc}</span>")
                info_box.pack_start(desc_lbl, False, False, 0)

                card.pack_start(info_box, True, True, 0)
                self.options_box.pack_start(card, False, False, 0)

            self.options_box.show_all()

        def on_option_toggled(self, opt_code, is_active):
            conf = get_configured_from_file()
            current_options = set([o.strip() for o in conf.get("options", "").split(",") if o.strip()])

            if is_active:
                current_options.add(opt_code)
            else:
                current_options.discard(opt_code)

            new_options_str = ",".join(sorted(current_options))
            save_and_apply_config(conf["layouts"], conf["variants"], options=new_options_str)
            show_notification(
                "⚙️  XKB Options Updated",
                f"Configured options: <b>{new_options_str or 'None'}</b>"
            )

    win = KeyboardLayoutWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


# =============================================================================
# 📊 Status JSON (Waybar / Quickshell Support)
# =============================================================================

def print_status_json():
    """Output JSON formatted status for Waybar or scripting."""
    info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()
    curr_desc = get_entry_description(info["current_lay"], info["current_var"], l_map, v_map)
    tag = info["current_tag"].upper()

    configured_list = ", ".join([
        f"{get_entry_description(l, v, l_map, v_map)} ({format_entry_tag(l, v).upper()})"
        for l, v in info["pairs"]
    ])

    data = {
        "text": tag,
        "alt": curr_desc,
        "tooltip": f"<b>Active Keyboard Layout:</b>\n{curr_desc} ({tag})\n\n<b>Configured Layouts:</b>\n{configured_list}\n\n• Left Click: Cycle Next Layout\n• Right Click: Layout & Variant Menu\n• Middle Click: Add New Layout",
        "class": f"layout-{info['current_lay']}",
        "percentage": (info["active_index"] + 1) / max(len(info["pairs"]), 1) * 100
    }
    print(json.dumps(data))


# =============================================================================
# 🏁 Main CLI Dispatcher
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Hyprland Keyboard Layout & Variant Manager Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  keyboard_layout.py --gui                   Launch graphical desktop manager
  keyboard_layout.py --next                  Switch to next configured layout
  keyboard_layout.py --add "in(bolnagri)"    Add Hindi Bolnagri phonetic layout
  keyboard_layout.py --add "in(tam)"         Add Tamil layout
  keyboard_layout.py --add "in(tel)"         Add Telugu layout
  keyboard_layout.py --add "in(eng)"         Add Indian English with ₹ layout
  keyboard_layout.py --add "us(dvorak)"      Add US Dvorak layout
  keyboard_layout.py --remove "in(bolnagri)" Remove Hindi Bolnagri layout
  keyboard_layout.py --menu                  Open interactive Fuzzel menu
  keyboard_layout.py --add-menu              Open interactive layout/variant catalog
  keyboard_layout.py --list                  List configured layouts & active variant
"""
    )

    parser.add_argument("-g", "--gui", action="store_true", help="Launch full graphical GTK3 desktop interface")
    parser.add_argument("-n", "--next", action="store_true", help="Switch to next keyboard layout")
    parser.add_argument("-p", "--prev", action="store_true", help="Switch to previous keyboard layout")
    parser.add_argument("-s", "--set", metavar="LAYOUT", help="Switch to layout by index or tag (e.g. 'in(bolnagri)')")
    parser.add_argument("-a", "--add", metavar="LAYOUT", help="Add layout/variant (e.g. 'in(bolnagri)', 'tam', 'de')")
    parser.add_argument("-r", "--remove", metavar="LAYOUT", help="Remove layout/variant")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel layout manager menu")
    parser.add_argument("--add-menu", action="store_true", help="Open interactive Fuzzel add layout/variant menu")
    parser.add_argument("--remove-menu", action="store_true", help="Open interactive Fuzzel remove layout menu")
    parser.add_argument("-l", "--list", action="store_true", help="Print active and configured layouts with variants")
    parser.add_argument("--status", action="store_true", help="Output JSON status for Waybar")

    args = parser.parse_args()

    if args.gui:
        launch_gtk_gui()
    elif args.next:
        switch_next_layout()
    elif args.prev:
        switch_prev_layout()
    elif args.set:
        set_layout_by_index_or_tag(args.set)
    elif args.add:
        add_layout(args.add)
    elif args.remove:
        remove_layout(args.remove)
    elif args.add_menu:
        gui_add_layout_menu()
    elif args.remove_menu:
        gui_remove_layout_menu()
    elif args.menu:
        gui_fuzzel_main_menu()
    elif args.status:
        print_status_json()
    elif args.list:
        info = get_active_layout_info()
        l_map, v_map = parse_all_xkb_catalog()
        curr_desc = get_entry_description(info["current_lay"], info["current_var"], l_map, v_map)
        print(f"Active Keymap : {curr_desc} [{info['current_tag'].upper()}]")
        print(f"Active Index  : {info['active_index']}")
        print(f"Configured    : {', '.join([format_entry_tag(l, v).upper() for l, v in info['pairs']])}")
        for i, (l, v) in enumerate(info["pairs"]):
            d = get_entry_description(l, v, l_map, v_map)
            act = " [ACTIVE]" if i == info["active_index"] else ""
            print(f"  [{i}] {format_entry_tag(l, v):<16} : {d}{act}")
    else:
        # Default when launched directly from App Menu without arguments: open GUI
        launch_gtk_gui()


if __name__ == "__main__":
    main()
