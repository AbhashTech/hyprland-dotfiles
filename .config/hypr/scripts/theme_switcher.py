#!/usr/bin/env python3
"""
=============================================================================
Universal Desktop Theme Switcher & Palette Manager
=============================================================================
Dynamically discovers and applies color themes stored in:
    ~/.config/theme/*.json (or ~/.dotfiles/.config/theme/*.json)

Applies palettes across:
- Hyprland (Borders, shadows, blur, Lua variables)
- Waybar (CSS color definitions & live reload)
- Fuzzel (RGBA launcher palette)
- Kitty (Terminal 16 colors, cursor, borders, tabs)
- Mako (Notification daemon colors & live reload)
- Wofi & Wlogout (CSS glassmorphic styles)
- Hyprlock (Lockscreen color variables)
- Starship Prompt (Dynamic palette selection)
- Zellij Multiplexer (Themes & layouts)
- Btop++ System Monitor (Theme files & config)
- Lazygit (TUI git theme)
- Swappy (Annotation accent color)
- Dolphin (KDE File Manager color palette & UI)
- Kate & KWrite (Editor themes, syntax highlighting & UI)

Provides CLI management and an interactive Fuzzel / Wofi GUI menu (SUPER + T).
"""


import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
DOTFILES_DIR = HOME / ".dotfiles" / ".config"
THEME_DIR = CONFIG_DIR / "theme"
FALLBACK_THEME_DIR = DOTFILES_DIR / "theme"
CACHE_DIR = HOME / ".cache"
STATE_FILE = CACHE_DIR / "hypr_theme_state.json"
CURRENT_THEME_TXT = CACHE_DIR / "current_theme"

# ANSI Colors for CLI
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[38;2;166;227;161m"
C_BLUE = "\033[38;2;137;180;250m"
C_YELLOW = "\033[38;2;249;226;175m"
C_RED = "\033[38;2;243;139;168m"
C_MAUVE = "\033[38;2;203;166;247m"
C_CYAN = "\033[38;2;148;226;213m"
C_GRAY = "\033[38;2;108;112;134m"

DEFAULT_THEME = "catppuccin-mocha"

# =============================================================================
# 📂 Dynamic Theme Loader from ~/.config/theme/*.json
# =============================================================================
def load_themes():
    """
    Scan ~/.config/theme and ~/.dotfiles/.config/theme for .json theme files.
    Returns a dictionary of {theme_id: theme_dict}.
    """
    themes = {}
    search_dirs = [THEME_DIR]
    if FALLBACK_THEME_DIR.exists() and FALLBACK_THEME_DIR not in search_dirs:
        search_dirs.append(FALLBACK_THEME_DIR)

    for directory in search_dirs:
        if not directory.exists():
            continue
        for json_file in sorted(directory.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    theme_id = data.get("id") or json_file.stem
                    data["id"] = theme_id
                    data["file_path"] = str(json_file)
                    if theme_id not in themes:
                        themes[theme_id] = data
            except Exception as e:
                print(f"Error loading theme {json_file}: {e}", file=sys.stderr)

    if not themes:
        # Fallback minimal default
        themes[DEFAULT_THEME] = {
            "id": DEFAULT_THEME,
            "name": "Catppuccin Mocha",
            "icon": "󰄯",
            "type": "dark",
            "desc": "Warm, soothing dark pastel aesthetic",
            "colors": {
                "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
                "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
                "overlay0": "#6c7086", "overlay1": "#7f849c", "overlay2": "#9399b2",
                "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
                "blue": "#89b4fa", "lavender": "#b4befe", "sapphire": "#74c7ec",
                "sky": "#89dceb", "teal": "#94e2d5", "green": "#a6e3a1",
                "yellow": "#f9e2af", "peach": "#fab387", "maroon": "#eba0ac",
                "red": "#f38ba8", "mauve": "#cba6f7", "pink": "#f5c2e7",
                "flamingo": "#f2cdcd", "rosewater": "#f5e0dc",
                "accent": "#cba6f7",
                "active_border_1": "rgba(cba6f7ee)", "active_border_2": "rgba(89b4faee)",
                "inactive_border": "rgba(313244aa)", "shadow_hex": "0xee11111b",
                "shadow_css": "rgba(17, 17, 27, 0.6)",
            },
            "terminal": {
                "color0": "#45475a", "color8": "#585b70",
                "color1": "#f38ba8", "color9": "#f38ba8",
                "color2": "#a6e3a1", "color10": "#a6e3a1",
                "color3": "#f9e2af", "color11": "#f9e2af",
                "color4": "#89b4fa", "color12": "#89b4fa",
                "color5": "#cba6f7", "color13": "#cba6f7",
                "color6": "#94e2d5", "color14": "#94e2d5",
                "color7": "#bac2de", "color15": "#a6adc8",
            },
            "starship_palette": "catppuccin_mocha",
        }

    return themes

# =============================================================================
# Helper Utilities
# =============================================================================
def hex_to_rgb_tuple(hex_str):
    """Convert hex string (e.g. #cba6f7) to tuple of ints (r, g, b)."""
    hex_str = str(hex_str).lstrip("#")
    if len(hex_str) == 6:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (200, 200, 200)

def hex_to_rgba_str(hex_str, alpha="ff"):
    """Convert hex (#1e1e2e) to rgba hex string (1e1e2eff)."""
    clean = str(hex_str).lstrip("#")
    return f"{clean}{alpha}"

def ensure_dirs():
    """Ensure config and cache directories exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    THEME_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "hypr").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "waybar").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "kitty").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "fuzzel").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "wofi").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "wlogout").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "btop" / "themes").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "zellij").mkdir(parents=True, exist_ok=True)
    (HOME / ".local" / "share" / "color-schemes").mkdir(parents=True, exist_ok=True)
    (HOME / ".local" / "share" / "org.kde.syntax-highlighting" / "themes").mkdir(parents=True, exist_ok=True)


def get_current_theme(themes):
    """Get ID of currently active theme."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                theme_id = data.get("current_theme")
                if theme_id in themes:
                    return theme_id
        except Exception:
            pass
    if CURRENT_THEME_TXT.exists():
        try:
            tid = CURRENT_THEME_TXT.read_text().strip()
            if tid in themes:
                return tid
        except Exception:
            pass
    return DEFAULT_THEME if DEFAULT_THEME in themes else list(themes.keys())[0]

def save_state(theme_id):
    """Save active theme ID to cache files."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"current_theme": theme_id}, f, indent=2)
        CURRENT_THEME_TXT.write_text(theme_id)
    except Exception as e:
        print(f"Error saving state: {e}", file=sys.stderr)

# =============================================================================
# Generator Functions for Components
# =============================================================================
def generate_hypr_lua_vars(theme):
    """Generate ~/.config/hypr/theme_vars.lua for Hyprland."""
    c = theme["colors"]
    content = f"""-- Auto-generated by theme_switcher.py for Hyprland
return {{
    name            = "{theme.get('name', theme['id'])}",
    id              = "{theme['id']}",
    base            = "rgba({c['base'].lstrip('#')}ff)",
    mantle          = "rgba({c['mantle'].lstrip('#')}ff)",
    crust           = "rgba({c['crust'].lstrip('#')}ff)",
    surface0        = "rgba({c['surface0'].lstrip('#')}ff)",
    surface1        = "rgba({c['surface1'].lstrip('#')}ff)",
    surface2        = "rgba({c['surface2'].lstrip('#')}ff)",
    text            = "rgba({c['text'].lstrip('#')}ff)",
    subtext0        = "rgba({c['subtext0'].lstrip('#')}ff)",
    subtext1        = "rgba({c['subtext1'].lstrip('#')}ff)",
    active_border_1 = "{c['active_border_1']}",
    active_border_2 = "{c['active_border_2']}",
    inactive_border = "{c['inactive_border']}",
    shadow          = {c['shadow_hex']},
    accent          = "rgba({c['accent'].lstrip('#')}ff)",
}}
"""
    target = CONFIG_DIR / "hypr" / "theme_vars.lua"
    target.write_text(content)
    df_target = DOTFILES_DIR / "hypr" / "theme_vars.lua"
    if df_target.parent.exists():
        df_target.write_text(content)

def generate_hypr_conf(theme):
    """Generate ~/.config/hypr/theme.conf for Hyprland / Hyprlock."""
    c = theme["colors"]
    lines = [f"# Hyprland & Hyprlock Theme: {theme.get('name', theme['id'])}"]
    for k, hex_val in c.items():
        if isinstance(hex_val, str) and hex_val.startswith("#"):
            r, g, b = hex_to_rgb_tuple(hex_val)
            lines.append(f"${k} = rgb({r}, {g}, {b})")
    content = "\n".join(lines) + "\n"
    (CONFIG_DIR / "hypr" / "theme.conf").write_text(content)
    if (DOTFILES_DIR / "hypr").exists():
        (DOTFILES_DIR / "hypr" / "theme.conf").write_text(content)

def generate_waybar_colors(theme):
    """Generate ~/.config/waybar/colors.css for Waybar with dynamic transparency."""
    c = theme["colors"]
    is_light = theme.get("type") == "light"
    lines = [f"/* Waybar Colors: {theme.get('name', theme['id'])} */"]
    for k, hex_val in c.items():
        if isinstance(hex_val, str) and hex_val.startswith("#"):
            lines.append(f"@define-color {k} {hex_val};")

    cr_r, cr_g, cr_b = hex_to_rgb_tuple(c.get("crust", "#11111b"))
    ma_r, ma_g, ma_b = hex_to_rgb_tuple(c.get("mantle", "#181825"))
    ba_r, ba_g, ba_b = hex_to_rgb_tuple(c.get("base", "#1e1e2e"))
    s0_r, s0_g, s0_b = hex_to_rgb_tuple(c.get("surface0", "#313244"))
    s1_r, s1_g, s1_b = hex_to_rgb_tuple(c.get("surface1", "#45475a"))
    ac_r, ac_g, ac_b = hex_to_rgb_tuple(c.get("accent", "#cba6f7"))

    if is_light:
        border_rgba = "rgba(0, 0, 0, 0.12)"
        border_subtle = "rgba(0, 0, 0, 0.06)"
        shadow_rgba = "rgba(0, 0, 0, 0.12)"
        bg_alpha = "0.72"
        mod_alpha = "0.85"
    else:
        border_rgba = "rgba(255, 255, 255, 0.12)"
        border_subtle = "rgba(255, 255, 255, 0.06)"
        shadow_rgba = "rgba(0, 0, 0, 0.40)"
        bg_alpha = "0.60"
        mod_alpha = "0.88"

    lines.append("")
    lines.append("/* Dynamic Glassmorphic Waybar Backgrounds & Borders */")
    lines.append(f"@define-color waybar_bg rgba({cr_r}, {cr_g}, {cr_b}, {bg_alpha});")
    lines.append(f"@define-color waybar_border {border_rgba};")
    lines.append(f"@define-color waybar_shadow {shadow_rgba};")
    lines.append(f"@define-color tooltip_bg rgba({ma_r}, {ma_g}, {ma_b}, 0.95);")
    lines.append(f"@define-color tooltip_border rgba({ac_r}, {ac_g}, {ac_b}, 0.45);")
    lines.append(f"@define-color module_bg rgba({ba_r}, {ba_g}, {ba_b}, {mod_alpha});")
    lines.append(f"@define-color module_border {border_rgba};")
    lines.append(f"@define-color module_hover_bg rgba({s0_r}, {s0_g}, {s0_b}, 0.95);")
    lines.append(f"@define-color module_hover_border rgba({ac_r}, {ac_g}, {ac_b}, 0.50);")
    lines.append(f"@define-color module_subtle_bg rgba({s0_r}, {s0_g}, {s0_b}, 0.45);")
    lines.append(f"@define-color module_subtle_border {border_subtle};")
    lines.append(f"@define-color module_active_bg rgba({s1_r}, {s1_g}, {s1_b}, 0.80);")
    lines.append(f"@define-color accent_glow rgba({ac_r}, {ac_g}, {ac_b}, 0.40);")

    content = "\n".join(lines) + "\n"
    (CONFIG_DIR / "waybar" / "colors.css").write_text(content)
    if (DOTFILES_DIR / "waybar").exists():
        (DOTFILES_DIR / "waybar" / "colors.css").write_text(content)


def generate_wofi_colors(theme):
    """Generate ~/.config/wofi/colors.css for Wofi."""
    c = theme["colors"]
    lines = [f"/* Wofi Colors: {theme.get('name', theme['id'])} */"]
    for k, hex_val in c.items():
        if isinstance(hex_val, str) and hex_val.startswith("#"):
            lines.append(f"@define-color {k} {hex_val};")
    content = "\n".join(lines) + "\n"
    (CONFIG_DIR / "wofi" / "colors.css").write_text(content)
    if (DOTFILES_DIR / "wofi").exists():
        (DOTFILES_DIR / "wofi" / "colors.css").write_text(content)

def generate_wlogout_colors(theme):
    """Generate ~/.config/wlogout/colors.css for Wlogout."""
    c = theme["colors"]
    r, g, b = hex_to_rgb_tuple(c["crust"])
    content = f"""/* Wlogout Colors: {theme.get('name', theme['id'])} */
@define-color base            {c['base']};
@define-color mantle          {c['mantle']};
@define-color crust           {c['crust']};
@define-color text            {c['text']};
@define-color surface0        {c['surface0']};
@define-color surface1        {c['surface1']};
@define-color accent          {c['accent']};
@define-color bg_overlay      rgba({r}, {g}, {b}, 0.75);
"""
    (CONFIG_DIR / "wlogout" / "colors.css").write_text(content)
    if (DOTFILES_DIR / "wlogout").exists():
        (DOTFILES_DIR / "wlogout" / "colors.css").write_text(content)

def generate_kitty_theme(theme):
    """Generate ~/.config/kitty/theme.conf for Kitty."""
    c = theme["colors"]
    t = theme["terminal"]
    content = f"""# =============================================================================
# Kitty Theme Colors - {theme.get('name', theme['id'])}
# =============================================================================

# Window borders
active_border_color {c['accent']}
inactive_border_color {c['surface0']}
bell_border_color {c['red']}

# Cursor
cursor {c['rosewater']}
cursor_text_color {c['crust']}

# URL
url_color {c['blue']}

# Tabs
active_tab_foreground   {c['crust']}
active_tab_background   {c['accent']}
inactive_tab_foreground {c['text']}
inactive_tab_background {c['mantle']}
tab_bar_background      {c['crust']}

# Color Scheme
background {c['base']}
foreground {c['text']}
selection_background {c['surface2']}
selection_foreground {c['text']}

# Black
color0 {t['color0']}
color8 {t['color8']}

# Red
color1 {t['color1']}
color9 {t['color9']}

# Green
color2  {t['color2']}
color10 {t['color10']}

# Yellow
color3  {t['color3']}
color11 {t['color11']}

# Blue
color4  {t['color4']}
color12 {t['color12']}

# Magenta / Mauve
color5  {t['color5']}
color13 {t['color13']}

# Cyan / Teal
color6  {t['color6']}
color14 {t['color14']}

# White
color7  {t['color7']}
color15 {t['color15']}
"""
    (CONFIG_DIR / "kitty" / "theme.conf").write_text(content)
    if (DOTFILES_DIR / "kitty").exists():
        (DOTFILES_DIR / "kitty" / "theme.conf").write_text(content)

def update_fuzzel_colors(theme):
    """Update ~/.config/fuzzel/fuzzel.ini colors section."""
    c = theme["colors"]
    fuzzel_file = CONFIG_DIR / "fuzzel" / "fuzzel.ini"
    df_fuzzel = DOTFILES_DIR / "fuzzel" / "fuzzel.ini"
    
    target_files = [fuzzel_file]
    if df_fuzzel.exists() and df_fuzzel not in target_files:
        target_files.append(df_fuzzel)

    bg_rgba = hex_to_rgba_str(c["mantle"], "ea")
    text_rgba = hex_to_rgba_str(c["text"], "ff")
    prompt_rgba = hex_to_rgba_str(c["accent"], "ff")
    placeholder_rgba = hex_to_rgba_str(c["overlay0"], "ff")
    input_rgba = hex_to_rgba_str(c["text"], "ff")
    match_rgba = hex_to_rgba_str(c["accent"], "ff")
    selection_rgba = hex_to_rgba_str(c["surface0"], "ff")
    sel_text_rgba = "ffffffef"
    sel_match_rgba = hex_to_rgba_str(c["pink"], "ff")
    border_rgba = hex_to_rgba_str(c["accent"], "88")

    colors_section = f"""[colors]
# {theme.get('name', theme['id'])} RGBA
background={bg_rgba}
text={text_rgba}
prompt={prompt_rgba}
placeholder={placeholder_rgba}
input={input_rgba}
match={match_rgba}
selection={selection_rgba}
selection-text={sel_text_rgba}
selection-match={sel_match_rgba}
border={border_rgba}

"""

    for fpath in target_files:
        if fpath.exists():
            try:
                content = fpath.read_text()
                if "[colors]" in content:
                    import re
                    content = re.sub(r"\[colors\][\s\S]*?(?=\n\[|\Z)", colors_section.rstrip() + "\n", content)
                    fpath.write_text(content)
            except Exception as e:
                print(f"Error updating fuzzel {fpath}: {e}", file=sys.stderr)

def update_mako_colors(theme):
    """Update ~/.config/mako/config with theme colors."""
    c = theme["colors"]
    mako_file = CONFIG_DIR / "mako" / "config"
    df_mako = DOTFILES_DIR / "mako" / "config"
    
    targets = [mako_file]
    if df_mako.exists() and df_mako not in targets:
        targets.append(df_mako)

    bg_color = f"{c['base']}e6"
    text_color = c["text"]
    border_color = c["accent"]
    progress_color = f"over {c['surface0']}"
    low_border = c["blue"]
    normal_border = c["accent"]
    crit_border = c["red"]
    crit_text = c["red"]

    for fpath in targets:
        if fpath.exists():
            try:
                lines = fpath.read_text().splitlines()
                new_lines = []
                current_section = "main"
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("[") and stripped.endswith("]"):
                        current_section = stripped[1:-1]
                        new_lines.append(line)
                        continue
                    
                    if current_section == "main":
                        if stripped.startswith("background-color="):
                            new_lines.append(f"background-color={bg_color}")
                        elif stripped.startswith("text-color="):
                            new_lines.append(f"text-color={text_color}")
                        elif stripped.startswith("border-color="):
                            new_lines.append(f"border-color={border_color}")
                        elif stripped.startswith("progress-color="):
                            new_lines.append(f"progress-color={progress_color}")
                        else:
                            new_lines.append(line)
                    elif current_section == "urgency=low":
                        if stripped.startswith("border-color="):
                            new_lines.append(f"border-color={low_border}")
                        else:
                            new_lines.append(line)
                    elif current_section == "urgency=normal":
                        if stripped.startswith("border-color="):
                            new_lines.append(f"border-color={normal_border}")
                        else:
                            new_lines.append(line)
                    elif current_section == "urgency=critical":
                        if stripped.startswith("border-color="):
                            new_lines.append(f"border-color={crit_border}")
                        elif stripped.startswith("text-color="):
                            new_lines.append(f"text-color={crit_text}")
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                fpath.write_text("\n".join(new_lines) + "\n")
            except Exception as e:
                print(f"Error updating mako {fpath}: {e}", file=sys.stderr)

def generate_btop_theme(theme):
    """Generate theme file for btop and update btop.conf."""
    c = theme["colors"]
    theme_id = theme["id"]
    
    theme_content = f"""# Btop theme: {theme.get('name', theme_id)}
theme[main_bg]="{c['base']}"
theme[main_fg]="{c['text']}"
theme[title]="{c['accent']}"
theme[hi_fg]="{c['blue']}"
theme[selected_bg]="{c['surface0']}"
theme[selected_fg]="{c['accent']}"
theme[inactive_fg]="{c['overlay0']}"
theme[graph_text]="{c['subtext0']}"
theme[proc_misc]="{c['mauve']}"
theme[cpu_box]="{c['accent']}"
theme[mem_box]="{c['green']}"
theme[net_box]="{c['blue']}"
theme[proc_box]="{c['peach']}"
theme[div_line]="{c['surface0']}"
theme[temp_start]="{c['green']}"
theme[temp_mid]="{c['yellow']}"
theme[temp_end]="{c['red']}"
theme[cpu_start]="{c['teal']}"
theme[cpu_mid]="{c['blue']}"
theme[cpu_end]="{c['mauve']}"
theme[free_start]="{c['teal']}"
theme[free_mid]="{c['green']}"
theme[free_end]="{c['yellow']}"
theme[cached_start]="{c['blue']}"
theme[cached_mid]="{c['lavender']}"
theme[cached_end]="{c['mauve']}"
theme[available_start]="{c['peach']}"
theme[available_mid]="{c['yellow']}"
theme[available_end]="{c['green']}"
theme[used_start]="{c['green']}"
theme[used_mid]="{c['yellow']}"
theme[used_end]="{c['red']}"
theme[download_start]="{c['teal']}"
theme[download_mid]="{c['blue']}"
theme[download_end]="{c['mauve']}"
theme[upload_start]="{c['pink']}"
theme[upload_mid]="{c['peach']}"
theme[upload_end]="{c['red']}"
theme[process_start]="{c['teal']}"
theme[process_mid]="{c['blue']}"
theme[process_end]="{c['mauve']}"
"""
    btop_theme_dir = CONFIG_DIR / "btop" / "themes"
    btop_theme_dir.mkdir(parents=True, exist_ok=True)
    theme_file = btop_theme_dir / f"{theme_id}.theme"
    theme_file.write_text(theme_content)
    
    df_btop_dir = DOTFILES_DIR / "btop" / "themes"
    if df_btop_dir.exists():
        (df_btop_dir / f"{theme_id}.theme").write_text(theme_content)

    btop_conf = CONFIG_DIR / "btop" / "btop.conf"
    df_btop_conf = DOTFILES_DIR / "btop" / "btop.conf"
    for bconf in [btop_conf, df_btop_conf]:
        if bconf.exists():
            try:
                lines = bconf.read_text().splitlines()
                new_lines = []
                for l in lines:
                    if l.strip().startswith("color_theme ="):
                        new_lines.append(f'color_theme = "{theme_id}"')
                    else:
                        new_lines.append(l)
                bconf.write_text("\n".join(new_lines) + "\n")
            except Exception:
                pass

def update_starship_palette(theme):
    """Update starship.toml active palette."""
    starship_file = CONFIG_DIR / "starship.toml"
    df_starship = DOTFILES_DIR / "starship.toml"
    palette_name = theme.get("starship_palette") or theme["id"].replace("-", "_")
    c = theme["colors"]

    palette_block = f"""[palettes.{palette_name}]
rosewater = "{c['rosewater']}"
flamingo = "{c['flamingo']}"
pink = "{c['pink']}"
mauve = "{c['mauve']}"
red = "{c['red']}"
maroon = "{c['maroon']}"
peach = "{c['peach']}"
yellow = "{c['yellow']}"
green = "{c['green']}"
teal = "{c['teal']}"
sky = "{c['sky']}"
sapphire = "{c['sapphire']}"
blue = "{c['blue']}"
lavender = "{c['lavender']}"
text = "{c['text']}"
subtext1 = "{c['subtext1']}"
subtext0 = "{c['subtext0']}"
overlay2 = "{c['overlay2']}"
overlay1 = "{c['overlay1']}"
overlay0 = "{c['overlay0']}"
surface2 = "{c['surface2']}"
surface1 = "{c['surface1']}"
surface0 = "{c['surface0']}"
base = "{c['base']}"
mantle = "{c['mantle']}"
crust = "{c['crust']}"
"""

    for sfile in [starship_file, df_starship]:
        if sfile.exists():
            try:
                content = sfile.read_text()
                import re
                content = re.sub(r'palette = ".*?"', f'palette = "{palette_name}"', content)
                if f"[palettes.{palette_name}]" not in content:
                    content = content + "\n" + palette_block
                sfile.write_text(content)
            except Exception as e:
                print(f"Error updating starship {sfile}: {e}", file=sys.stderr)

def update_zellij_theme(theme):
    """Update zellij config with theme."""
    theme_id = theme["id"]
    c = theme["colors"]
    zfile = CONFIG_DIR / "zellij" / "config.kdl"
    df_zfile = DOTFILES_DIR / "zellij" / "config.kdl"
    
    theme_def = f"""    {theme_id} {{
        bg "{c['surface2']}"
        fg "{c['text']}"
        red "{c['red']}"
        green "{c['green']}"
        blue "{c['blue']}"
        yellow "{c['yellow']}"
        magenta "{c['mauve']}"
        orange "{c['peach']}"
        cyan "{c['teal']}"
        black "{c['mantle']}"
        white "{c['text']}"
    }}"""

    for zf in [zfile, df_zfile]:
        if zf.exists():
            try:
                content = zf.read_text()
                import re
                content = re.sub(r'theme ".*?"', f'theme "{theme_id}"', content)
                if f"{theme_id} {{" not in content and "themes {" in content:
                    content = content.replace("themes {", f"themes {{\n{theme_def}")
                zf.write_text(content)
            except Exception as e:
                print(f"Error updating zellij {zf}: {e}", file=sys.stderr)

def update_lazygit_theme(theme):
    """Update lazygit config.yml colors."""
    c = theme["colors"]
    lg_file = CONFIG_DIR / "lazygit" / "config.yml"
    df_lg = DOTFILES_DIR / "lazygit" / "config.yml"
    
    lg_content = f"""# =============================================================================
# Lazygit Configuration - {theme.get('name', theme['id'])}
# =============================================================================

gui:
  theme:
    activeBorderColor:
      - '{c['accent']}'
      - bold
    inactiveBorderColor:
      - '{c['surface2']}'
    optionsTextColor:
      - '{c['blue']}'
    selectedLineBgColor:
      - '{c['surface0']}'
    cherryPickedCommitBgColor:
      - '{c['surface1']}'
    cherryPickedCommitFgColor:
      - '{c['accent']}'
    unstagedChangesColor:
      - '{c['red']}'
    defaultFgColor:
      - '{c['text']}'
    searchingActiveBorderColor:
      - '{c['yellow']}'

git:
  paging:
    colorArg: always
    pager: delta --dark --paging=never --line-numbers --hyperlinks --side-by-side
"""
    for lf in [lg_file, df_lg]:
        try:
            lf.parent.mkdir(parents=True, exist_ok=True)
            lf.write_text(lg_content)
        except Exception:
            pass

def update_swappy_color(theme):
    """Update swappy/config accent color."""
    c = theme["colors"]
    accent_clean = c["accent"].lstrip("#")
    sfile = CONFIG_DIR / "swappy" / "config"
    df_s = DOTFILES_DIR / "swappy" / "config"
    for sf in [sfile, df_s]:
        if sf.exists():
            try:
                lines = sf.read_text().splitlines()
                new_lines = []
                for l in lines:
                    if l.strip().startswith("custom_color="):
                        new_lines.append(f"custom_color={accent_clean}")
                    else:
                        new_lines.append(l)
                sf.write_text("\n".join(new_lines) + "\n")
            except Exception:
                pass

def generate_kde_theme(theme):
    """
    Generate ~/.config/kdeglobals and ~/.local/share/color-schemes/<Theme>.colors
    Applies colors for Dolphin, Kate, KWrite, and all KDE/Qt applications.
    """
    c = theme["colors"]
    name = theme.get("name", theme["id"])
    theme_id = theme["id"]
    is_light = theme.get("type") == "light"

    def to_rgb_str(hex_val, default="200,200,200"):
        if not hex_val:
            return default
        r, g, b = hex_to_rgb_tuple(hex_val)
        return f"{r},{g},{b}"

    base_rgb = to_rgb_str(c.get("base"))
    mantle_rgb = to_rgb_str(c.get("mantle"))
    crust_rgb = to_rgb_str(c.get("crust"))
    surf0_rgb = to_rgb_str(c.get("surface0"))
    surf1_rgb = to_rgb_str(c.get("surface1"))
    surf2_rgb = to_rgb_str(c.get("surface2"))
    text_rgb = to_rgb_str(c.get("text"))
    subtext0_rgb = to_rgb_str(c.get("subtext0"))
    subtext1_rgb = to_rgb_str(c.get("subtext1"))
    accent_rgb = to_rgb_str(c.get("accent"))
    blue_rgb = to_rgb_str(c.get("blue"))
    lavender_rgb = to_rgb_str(c.get("lavender"))
    red_rgb = to_rgb_str(c.get("red"))
    yellow_rgb = to_rgb_str(c.get("yellow"))
    green_rgb = to_rgb_str(c.get("green"))

    # Selection foreground color
    sel_fg_rgb = crust_rgb if not is_light else "255,255,255"

    kdeglobals_content = f"""[General]
ColorScheme={name}
Name={name}
TerminalApplication=kitty
TerminalService=kitty

[KDE]
ColorScheme={name}
contrast=4

[Colors:Window]
BackgroundNormal={base_rgb}
BackgroundAlternate={mantle_rgb}
ForegroundNormal={text_rgb}
ForegroundInactive={subtext0_rgb}
ForegroundActive={accent_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}

[Colors:View]
BackgroundNormal={base_rgb}
BackgroundAlternate={mantle_rgb}
ForegroundNormal={text_rgb}
ForegroundInactive={subtext0_rgb}
ForegroundActive={accent_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}

[Colors:Button]
BackgroundNormal={surf0_rgb}
BackgroundAlternate={surf1_rgb}
ForegroundNormal={text_rgb}
ForegroundInactive={subtext0_rgb}
ForegroundActive={accent_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}

[Colors:Selection]
BackgroundNormal={accent_rgb}
BackgroundAlternate={surf2_rgb}
ForegroundNormal={sel_fg_rgb}
ForegroundInactive={text_rgb}
ForegroundActive={sel_fg_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}

[Colors:Tooltip]
BackgroundNormal={mantle_rgb}
BackgroundAlternate={crust_rgb}
ForegroundNormal={text_rgb}
ForegroundInactive={subtext0_rgb}
ForegroundActive={accent_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}

[Colors:Header]
BackgroundNormal={mantle_rgb}
BackgroundAlternate={crust_rgb}
ForegroundNormal={text_rgb}
ForegroundInactive={subtext0_rgb}
ForegroundActive={accent_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}

[Colors:Complementary]
BackgroundNormal={mantle_rgb}
BackgroundAlternate={crust_rgb}
ForegroundNormal={text_rgb}
ForegroundInactive={subtext0_rgb}
ForegroundActive={accent_rgb}
ForegroundLink={blue_rgb}
ForegroundVisited={lavender_rgb}
ForegroundNegative={red_rgb}
ForegroundNeutral={yellow_rgb}
ForegroundPositive={green_rgb}
DecorationFocus={accent_rgb}
DecorationHover={blue_rgb}
"""

    kde_config = CONFIG_DIR / "kdeglobals"
    kde_config.write_text(kdeglobals_content)
    df_kde = DOTFILES_DIR / "kdeglobals"
    if df_kde.parent.exists():
        df_kde.write_text(kdeglobals_content)

    color_schemes_dir = HOME / ".local" / "share" / "color-schemes"
    color_schemes_dir.mkdir(parents=True, exist_ok=True)
    scheme_file = color_schemes_dir / f"{theme_id}.colors"
    scheme_file.write_text(kdeglobals_content)

def generate_kate_theme(theme):
    """
    Generate Kate / KWrite syntax highlighting theme in:
    ~/.local/share/org.kde.syntax-highlighting/themes/<theme_id>.theme
    and update ~/.config/katerc and ~/.config/kwriterc.
    """
    c = theme["colors"]
    name = theme.get("name", theme["id"])
    theme_id = theme["id"]
    is_light = theme.get("type") == "light"

    syntax_dir = HOME / ".local" / "share" / "org.kde.syntax-highlighting" / "themes"
    syntax_dir.mkdir(parents=True, exist_ok=True)
    theme_json_file = syntax_dir / f"{theme_id}.theme"

    theme_def = {
        "_comments": f"Theme generated by theme_switcher.py for {name}",
        "metadata": {
            "name": name,
            "revision": 1
        },
        "editor-colors": {
            "BackgroundColor": c.get("base", "#1e1e2e"),
            "CodeFolding": c.get("surface2", "#585b70"),
            "CurrentLine": c.get("surface0", "#313244"),
            "CurrentLineNumber": c.get("accent", "#cba6f7"),
            "IconBorder": c.get("mantle", "#181825"),
            "IndentationLine": c.get("surface1", "#45475a"),
            "LineNumbers": c.get("overlay0", "#6c7086"),
            "MarkBookmark": c.get("blue", "#89b4fa"),
            "MarkBreakpointActive": c.get("red", "#f38ba8"),
            "MarkBreakpointDisabled": c.get("overlay0", "#6c7086"),
            "MarkBreakpointReached": c.get("yellow", "#f9e2af"),
            "MarkError": c.get("red", "#f38ba8"),
            "MarkExecution": c.get("teal", "#94e2d5"),
            "MarkWarning": c.get("peach", "#fab387"),
            "ModifiedLines": c.get("yellow", "#f9e2af"),
            "ReplaceHighlight": c.get("green", "#a6e3a1"),
            "SavedLines": c.get("green", "#a6e3a1"),
            "SearchHighlight": c.get("yellow", "#f9e2af"),
            "Separator": c.get("surface0", "#313244"),
            "SpellChecking": c.get("red", "#f38ba8"),
            "TabMarker": c.get("surface1", "#45475a"),
            "TemplateBackground": c.get("surface0", "#313244"),
            "TemplateFocusedEditablePlaceholder": c.get("surface1", "#45475a"),
            "TemplateReadOnlyPlaceholder": c.get("mantle", "#181825"),
            "TextSelection": c.get("surface2", "#585b70"),
            "WordWrapMarker": c.get("surface1", "#45475a")
        },
        "text-styles": {
            "Normal": { "text-color": c.get("text", "#cdd6f4"), "selected-text-color": "#ffffff" if not is_light else "#000000" },
            "Keyword": { "text-color": c.get("mauve", c.get("accent", "#cba6f7")), "bold": True },
            "Function": { "text-color": c.get("blue", "#89b4fa") },
            "Variable": { "text-color": c.get("text", "#cdd6f4") },
            "ControlFlow": { "text-color": c.get("mauve", c.get("accent", "#cba6f7")), "bold": True },
            "String": { "text-color": c.get("green", "#a6e3a1") },
            "Char": { "text-color": c.get("teal", "#94e2d5") },
            "SpecialChar": { "text-color": c.get("pink", "#f5c2e7") },
            "DecVal": { "text-color": c.get("peach", "#fab387") },
            "BaseN": { "text-color": c.get("peach", "#fab387") },
            "Float": { "text-color": c.get("peach", "#fab387") },
            "Constant": { "text-color": c.get("peach", "#fab387") },
            "Comment": { "text-color": c.get("overlay0", "#6c7086"), "italic": True },
            "Documentation": { "text-color": c.get("overlay2", "#9399b2") },
            "DataType": { "text-color": c.get("yellow", "#f9e2af") },
            "Preprocessor": { "text-color": c.get("red", "#f38ba8") },
            "Attribute": { "text-color": c.get("sky", "#89dceb") },
            "RegionMarker": { "text-color": c.get("sapphire", "#74c7ec"), "background-color": c.get("surface0", "#313244") },
            "Information": { "text-color": c.get("blue", "#89b4fa") },
            "Warning": { "text-color": c.get("peach", "#fab387") },
            "Alert": { "text-color": c.get("red", "#f38ba8"), "bold": True },
            "Error": { "text-color": c.get("red", "#f38ba8"), "underline": True },
            "Others": { "text-color": c.get("rosewater", "#f5e0dc") }
        }
    }

    try:
        with open(theme_json_file, "w", encoding="utf-8") as f:
            json.dump(theme_def, f, indent=4)
    except Exception as e:
        print(f"Error saving syntax theme {theme_json_file}: {e}", file=sys.stderr)

    # Update katerc & kwriterc
    for app_rc in [CONFIG_DIR / "katerc", CONFIG_DIR / "kwriterc"]:
        try:
            content = app_rc.read_text() if app_rc.exists() else ""
            if "[KTextEditor Renderer]" in content:
                import re
                content = re.sub(r"Color Theme=.*", f"Color Theme={name}", content)
                content = re.sub(r"Auto Color Theme Selection=.*", "Auto Color Theme Selection=false", content)
            else:
                content += f"\n[KTextEditor Renderer]\nAuto Color Theme Selection=false\nColor Theme={name}\n"
            app_rc.write_text(content.strip() + "\n")
        except Exception as e:
            print(f"Error updating {app_rc}: {e}", file=sys.stderr)

def update_dolphin_theme(theme):
    """Ensure dolphinrc exists and is synchronized with KDE global theme."""
    dolphin_rc = CONFIG_DIR / "dolphinrc"
    df_dolphin = DOTFILES_DIR / "dolphinrc"
    try:
        if not dolphin_rc.exists():
            dolphin_rc.write_text("[General]\nVersion=202\n")
        if df_dolphin.parent.exists() and not df_dolphin.exists():
            df_dolphin.write_text(dolphin_rc.read_text())
    except Exception:
        pass

# =============================================================================
# Core Application & Live Reload
# =============================================================================
def reload_desktop():
    """Reload all active running Wayland apps/daemons."""
    # 1. Reload Hyprland
    try:
        subprocess.run(["hyprctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 2. Reload Waybar
    try:
        subprocess.run(["pkill", "-SIGUSR2", "waybar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 3. Reload Mako
    try:
        subprocess.run(["makoctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 4. Reload Kitty terminals
    try:
        subprocess.run(["killall", "-SIGUSR1", "kitty"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 5. Reload KDE/Qt services if running
    for bus in ["org.kde.kded6", "org.kde.kded5"]:
        try:
            subprocess.run(["qdbus", bus, "/kded", f"{bus}.reconfigure"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def send_theme_notification(theme):
    """Send visual desktop notification with theme information."""
    if not shutil.which("notify-send"):
        return
    c = theme["colors"]
    icon = "preferences-desktop-theme"
    title = f"🎨 Theme Applied: {theme.get('name', theme['id'])}"
    body = f"<b>Accent:</b> <span foreground=\"{c['accent']}\">████ {c['accent']}</span>  |  <b>Type:</b> {theme.get('type', 'dark').capitalize()}\n{theme.get('desc', '')}"
    try:
        subprocess.run(
            ["notify-send", "-a", "Theme Switcher", "-i", icon, "-r", "9944", title, body],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def apply_theme(theme_id, themes=None, notify=True):
    """Apply theme by ID across all desktop configs and trigger live reloads."""
    if themes is None:
        themes = load_themes()

    if theme_id not in themes:
        print(f"{C_RED}Error: Unknown theme '{theme_id}'{C_RESET}", file=sys.stderr)
        print(f"Available themes: {', '.join(sorted(themes.keys()))}", file=sys.stderr)
        return False

    theme = themes[theme_id]
    theme["id"] = theme_id
    ensure_dirs()

    # Generate all configuration components
    generate_hypr_lua_vars(theme)
    generate_hypr_conf(theme)
    generate_waybar_colors(theme)
    generate_wofi_colors(theme)
    generate_wlogout_colors(theme)
    generate_kitty_theme(theme)
    update_fuzzel_colors(theme)
    update_mako_colors(theme)
    generate_btop_theme(theme)
    update_starship_palette(theme)
    update_zellij_theme(theme)
    update_lazygit_theme(theme)
    update_swappy_color(theme)
    generate_kde_theme(theme)
    generate_kate_theme(theme)
    update_dolphin_theme(theme)

    # Save state
    save_state(theme_id)

    # Live reload desktop
    reload_desktop()

    if notify:
        send_theme_notification(theme)

    print(f"{C_GREEN}✓ Successfully applied theme:{C_RESET} {C_BOLD}{theme.get('name', theme_id)}{C_RESET} ({theme_id})")
    return True


# =============================================================================
# Interactive GUI Menu (Fuzzel / Wofi)
# =============================================================================
def run_interactive_menu(themes):
    """Display an interactive Fuzzel or Wofi graphical menu to select a theme."""
    current = get_current_theme(themes)
    menu_items = []
    
    for tid, tdata in sorted(themes.items(), key=lambda x: x[1].get("name", x[0])):
        is_active = (tid == current)
        active_mark = "✔ " if is_active else "  "
        icon = tdata.get("icon", "🎨")
        name = tdata.get("name", tid)
        ttype = tdata.get("type", "dark").capitalize()
        desc = tdata.get("desc", "")
        display_line = f"{active_mark}{icon} {name:<22} │ {ttype:<5} │ {desc}"
        menu_items.append((display_line, tid))

    menu_input = "\n".join(item[0] for item in menu_items)
    selected_tid = None

    if shutil.which("fuzzel"):
        cmd = [
            "fuzzel",
            "--dmenu",
            "--prompt", "🎨 Select Theme: ",
            "--width", "52",
            "--lines", str(len(themes) + 1),
        ]
        try:
            res = subprocess.run(cmd, input=menu_input, text=True, capture_output=True)
            chosen_line = res.stdout.strip()
            if chosen_line:
                for dline, tid in menu_items:
                    if dline.strip() == chosen_line:
                        selected_tid = tid
                        break
        except Exception as e:
            print(f"Error launching fuzzel: {e}", file=sys.stderr)
            
    elif shutil.which("wofi"):
        cmd = [
            "wofi",
            "--dmenu",
            "--prompt", "🎨 Select Theme",
            "--width", "550",
            "--lines", str(len(themes) + 1),
        ]
        try:
            res = subprocess.run(cmd, input=menu_input, text=True, capture_output=True)
            chosen_line = res.stdout.strip()
            if chosen_line:
                for dline, tid in menu_items:
                    if dline.strip() == chosen_line:
                        selected_tid = tid
                        break
        except Exception as e:
            print(f"Error launching wofi: {e}", file=sys.stderr)

    if selected_tid:
        apply_theme(selected_tid, themes=themes, notify=True)

# =============================================================================
# CLI Commands & Entry Point
# =============================================================================
def list_themes(themes):
    """Print all available themes in formatted CLI output."""
    current = get_current_theme(themes)
    print(f"\n{C_BOLD}{C_MAUVE}═════════════════════════════════════════════════════════════════════════{C_RESET}")
    print(f"{C_BOLD} 🎨 Available Themes & Color Palettes ({len(themes)} total){C_RESET}")
    print(f"{C_BOLD}{C_MAUVE}═════════════════════════════════════════════════════════════════════════{C_RESET}\n")

    for tid, tdata in sorted(themes.items(), key=lambda x: x[1].get("name", x[0])):
        is_active = (tid == current)
        indicator = f"{C_GREEN}● ACTIVE{C_RESET}" if is_active else f"{C_GRAY}○{C_RESET}"
        c = tdata["colors"]
        name = tdata.get("name", tid)
        desc = tdata.get("desc", "")
        swatches = f"\033[38;2;{hex_to_rgb_tuple(c['base'])[0]};{hex_to_rgb_tuple(c['base'])[1]};{hex_to_rgb_tuple(c['base'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['surface0'])[0]};{hex_to_rgb_tuple(c['surface0'])[1]};{hex_to_rgb_tuple(c['surface0'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['accent'])[0]};{hex_to_rgb_tuple(c['accent'])[1]};{hex_to_rgb_tuple(c['accent'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['blue'])[0]};{hex_to_rgb_tuple(c['blue'])[1]};{hex_to_rgb_tuple(c['blue'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['green'])[0]};{hex_to_rgb_tuple(c['green'])[1]};{hex_to_rgb_tuple(c['green'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['red'])[0]};{hex_to_rgb_tuple(c['red'])[1]};{hex_to_rgb_tuple(c['red'])[2]}m██\033[0m"

        print(f"  {indicator:<18} {C_BOLD}{name:<22}{C_RESET} [{C_CYAN}{tid:<20}{C_RESET}] {swatches}  {C_GRAY}{desc}{C_RESET}")

    print(f"\n{C_BOLD}Tip:{C_RESET} Drop new theme JSON files in {C_YELLOW}~/.config/theme/<name>.json{C_RESET}")
    print(f"     Press {C_YELLOW}SUPER + T{C_RESET} to open the interactive theme menu.\n")

def cycle_theme(themes, forward=True):
    """Cycle to next or previous theme in registry."""
    theme_keys = sorted(themes.keys())
    current = get_current_theme(themes)
    try:
        idx = theme_keys.index(current)
        new_idx = (idx + 1) % len(theme_keys) if forward else (idx - 1) % len(theme_keys)
    except ValueError:
        new_idx = 0
    apply_theme(theme_keys[new_idx], themes=themes, notify=True)

def random_theme(themes):
    """Apply a random theme from registry."""
    import random
    theme_keys = list(themes.keys())
    current = get_current_theme(themes)
    candidates = [k for k in theme_keys if k != current]
    choice = random.choice(candidates if candidates else theme_keys)
    apply_theme(choice, themes=themes, notify=True)

def main():
    parser = argparse.ArgumentParser(
        description="Universal Desktop Theme Switcher & Palette Manager (SUPER + T)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-l", "--list", action="store_true", help="List all available themes and their status")
    parser.add_argument("-s", "--set", metavar="THEME_ID", help="Apply a specific theme by ID")
    parser.add_argument("-c", "--current", action="store_true", help="Display the active theme ID")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel / Wofi GUI theme selector")
    parser.add_argument("-n", "--next", action="store_true", help="Cycle to the next theme")
    parser.add_argument("-p", "--prev", action="store_true", help="Cycle to the previous theme")
    parser.add_argument("-r", "--random", action="store_true", help="Apply a random theme")
    parser.add_argument("--silent", action="store_true", help="Suppress desktop notifications")

    args = parser.parse_args()
    themes = load_themes()

    if args.list:
        list_themes(themes)
    elif args.set:
        apply_theme(args.set, themes=themes, notify=not args.silent)
    elif args.current:
        cur = get_current_theme(themes)
        name = themes.get(cur, {}).get("name", cur)
        print(f"Current theme: {name} ({cur})")
    elif args.menu:
        run_interactive_menu(themes)
    elif args.next:
        cycle_theme(themes, forward=True)
    elif args.prev:
        cycle_theme(themes, forward=False)
    elif args.random:
        random_theme(themes)
    else:
        run_interactive_menu(themes)

if __name__ == "__main__":
    main()
