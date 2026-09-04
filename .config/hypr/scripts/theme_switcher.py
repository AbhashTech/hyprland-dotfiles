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
    (CONFIG_DIR / "gtk-3.0").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "gtk-4.0").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "xsettingsd").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "nvim" / "lua").mkdir(parents=True, exist_ok=True)
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
# Git Integration & Worktree Isolation for Theme Files
# =============================================================================
DOTFILES_ROOT = HOME / ".dotfiles"

THEME_TRACKED_REL_PATHS = [
    ".config/hypr/theme.conf",
    ".config/hypr/theme_vars.lua",
    ".config/waybar/colors.css",
    ".config/wofi/colors.css",
    ".config/wlogout/colors.css",
    ".config/kitty/theme.conf",
    ".config/fuzzel/fuzzel.ini",
    ".config/mako/config",
    ".config/btop/btop.conf",
    ".config/starship.toml",
    ".config/zellij/config.kdl",
    ".config/lazygit/config.yml",
    ".config/swappy/config",
    ".config/kdeglobals",
    ".config/dolphinrc",
    ".config/gtk-3.0/settings.ini",
    ".config/gtk-4.0/settings.ini",
    ".config/xsettingsd/xsettingsd.conf",
    ".config/nvim/lua/theme_colors.lua",
]

def get_theme_tracked_files():
    """Return list of existing tracked theme files relative to ~/.dotfiles root."""
    existing = []
    for rel_path in THEME_TRACKED_REL_PATHS:
        if (DOTFILES_ROOT / rel_path).exists():
            existing.append(rel_path)
    return existing

def set_git_skip_worktree(skip=True, quiet=False):
    """
    Set (--skip-worktree) or unset (--no-skip-worktree) on theme files in git repo.
    Prevents local theme changes from dirtying git status.
    """
    if not (DOTFILES_ROOT / ".git").exists():
        return False
    files = get_theme_tracked_files()
    if not files:
        return False
    flag = "--skip-worktree" if skip else "--no-skip-worktree"
    try:
        subprocess.run(
            ["git", "-C", str(DOTFILES_ROOT), "update-index", flag] + files,
            capture_output=True,
            check=True
        )
        if not quiet:
            action = "Ignored locally (skip-worktree)" if skip else "Tracking un-ignored"
            print(f"{C_GRAY}git: {action} {len(files)} theme files{C_RESET}")
        return True
    except Exception as e:
        if not quiet:
            print(f"{C_YELLOW}Warning: git update-index {flag} failed: {e}{C_RESET}", file=sys.stderr)
        return False

def check_pending_theme_changes():
    """Check if any theme files have modified content compared to git index."""
    if not (DOTFILES_ROOT / ".git").exists():
        return []
    files = get_theme_tracked_files()
    if not files:
        return []
    subprocess.run(
        ["git", "-C", str(DOTFILES_ROOT), "update-index", "--no-skip-worktree"] + files,
        capture_output=True,
        check=False
    )
    try:
        res = subprocess.run(
            ["git", "-C", str(DOTFILES_ROOT), "status", "--porcelain"] + files,
            capture_output=True,
            text=True,
            check=True
        )
        modified = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        return modified
    finally:
        subprocess.run(
            ["git", "-C", str(DOTFILES_ROOT), "update-index", "--skip-worktree"] + files,
            capture_output=True,
            check=False
        )

def sync_theme_git(commit_message=None):
    """
    Unskip theme files, stage them, commit changes if any, and re-apply skip-worktree.
    """
    if not (DOTFILES_ROOT / ".git").exists():
        print(f"{C_RED}Error: {DOTFILES_ROOT} is not a git repository.{C_RESET}", file=sys.stderr)
        return False

    files = get_theme_tracked_files()
    if not files:
        print(f"{C_YELLOW}No theme tracked files found.{C_RESET}")
        return False

    subprocess.run(
        ["git", "-C", str(DOTFILES_ROOT), "update-index", "--no-skip-worktree"] + files,
        capture_output=True,
        check=False
    )

    try:
        res = subprocess.run(
            ["git", "-C", str(DOTFILES_ROOT), "status", "--porcelain"] + files,
            capture_output=True,
            text=True,
            check=True
        )
        modified = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        if modified:
            theme_id = CURRENT_THEME_TXT.read_text().strip() if CURRENT_THEME_TXT.exists() else "theme"
            msg = commit_message or f"chore(theme): sync active theme ({theme_id})"
            subprocess.run(["git", "-C", str(DOTFILES_ROOT), "add"] + files, check=True)
            subprocess.run(["git", "-C", str(DOTFILES_ROOT), "commit", "-m", msg, "--"] + files, check=True)
            print(f"{C_GREEN}✓ Successfully committed active theme:{C_RESET} {msg}")
        else:
            print(f"{C_BLUE}ℹ No theme changes to sync in git (working tree clean).{C_RESET}")
        return True
    except Exception as e:
        print(f"{C_RED}Error syncing theme to git: {e}{C_RESET}", file=sys.stderr)
        return False
    finally:
        subprocess.run(
            ["git", "-C", str(DOTFILES_ROOT), "update-index", "--skip-worktree"] + files,
            capture_output=True,
            check=False
        )


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

    is_light = theme.get("type") == "light"
    bg_rgba = hex_to_rgba_str(c["mantle"], "f0")
    text_rgba = hex_to_rgba_str(c["text"], "ff")
    prompt_rgba = hex_to_rgba_str(c["accent"], "ff")
    placeholder_rgba = hex_to_rgba_str(c["overlay0"], "ff")
    input_rgba = hex_to_rgba_str(c["text"], "ff")
    match_rgba = hex_to_rgba_str(c["accent"], "ff")
    selection_rgba = hex_to_rgba_str(c["surface0"], "ff")
    sel_text_rgba = hex_to_rgba_str(c["crust" if is_light else "text"], "ff") if is_light else "ffffffef"
    sel_match_rgba = hex_to_rgba_str(c.get("accent", c.get("pink", "#cba6f7")), "ff")
    border_rgba = hex_to_rgba_str(c["accent"], "aa")

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

def generate_nvim_theme(theme):
    """
    Generate ~/.config/nvim/lua/theme_colors.lua and update Neovim dynamic theme.
    Maps system themes to native Neovim colorschemes & full palette hex variables.
    """
    c = theme["colors"]
    t = theme.get("terminal", {})
    theme_id = theme["id"]
    name = theme.get("name", theme_id)
    is_light = (theme.get("type") == "light")

    # Map desktop themes to Neovim colorschemes
    colorscheme_map = {
        "catppuccin-mocha": {"scheme": "catppuccin", "flavour": "mocha", "background": "dark"},
        "catppuccin-macchiato": {"scheme": "catppuccin", "flavour": "macchiato", "background": "dark"},
        "catppuccin-frappe": {"scheme": "catppuccin", "flavour": "frappe", "background": "dark"},
        "catppuccin-latte": {"scheme": "catppuccin", "flavour": "latte", "background": "light"},
        "tokyo-night": {"scheme": "tokyonight-night", "flavour": "night", "background": "dark"},
        "tokyo-night-day": {"scheme": "tokyonight-day", "flavour": "day", "background": "light"},
        "gruvbox-dark": {"scheme": "gruvbox", "flavour": "dark", "background": "dark"},
        "gruvbox-light": {"scheme": "gruvbox", "flavour": "light", "background": "light"},
        "nord": {"scheme": "nord", "flavour": "dark", "background": "dark"},
        "nord-light": {"scheme": "nord", "flavour": "light", "background": "light"},
        "rose-pine": {"scheme": "rose-pine", "flavour": "main", "background": "dark"},
        "rose-pine-dawn": {"scheme": "rose-pine-dawn", "flavour": "dawn", "background": "light"},
        "everforest": {"scheme": "everforest", "flavour": "dark", "background": "dark"},
        "everforest-light": {"scheme": "everforest", "flavour": "light", "background": "light"},
        "one-dark": {"scheme": "onedark", "flavour": "dark", "background": "dark"},
        "one-light": {"scheme": "onelight", "flavour": "light", "background": "light"},
        "dracula": {"scheme": "dracula", "flavour": "dark", "background": "dark"},
        "cyberpunk": {"scheme": "catppuccin", "flavour": "mocha", "background": "dark"},
        "solarized-light": {"scheme": "solarized", "flavour": "light", "background": "light"},
    }

    scheme_info = colorscheme_map.get(theme_id, {
        "scheme": "catppuccin" if not is_light else "catppuccin",
        "flavour": "mocha" if not is_light else "latte",
        "background": "light" if is_light else "dark",
    })

    lua_content = f"""-- Auto-generated by theme_switcher.py for Neovim
-- Active Desktop Theme: {name} ({theme_id})

return {{
    id = "{theme_id}",
    name = "{name}",
    type = "{"light" if is_light else "dark"}",
    colorscheme = "{scheme_info['scheme']}",
    flavour = "{scheme_info['flavour']}",
    background = "{scheme_info['background']}",
    colors = {{
        base = "{c.get('base', '#1e1e2e')}",
        mantle = "{c.get('mantle', '#181825')}",
        crust = "{c.get('crust', '#11111b')}",
        surface0 = "{c.get('surface0', '#313244')}",
        surface1 = "{c.get('surface1', '#45475a')}",
        surface2 = "{c.get('surface2', '#585b70')}",
        overlay0 = "{c.get('overlay0', '#6c7086')}",
        overlay1 = "{c.get('overlay1', '#7f849c')}",
        overlay2 = "{c.get('overlay2', '#9399b2')}",
        text = "{c.get('text', '#cdd6f4')}",
        subtext0 = "{c.get('subtext0', '#a6adc8')}",
        subtext1 = "{c.get('subtext1', '#bac2de')}",
        accent = "{c.get('accent', '#cba6f7')}",
        blue = "{c.get('blue', '#89b4fa')}",
        lavender = "{c.get('lavender', '#b4befe')}",
        sapphire = "{c.get('sapphire', '#74c7ec')}",
        sky = "{c.get('sky', '#89dceb')}",
        teal = "{c.get('teal', '#94e2d5')}",
        green = "{c.get('green', '#a6e3a1')}",
        yellow = "{c.get('yellow', '#f9e2af')}",
        peach = "{c.get('peach', '#fab387')}",
        maroon = "{c.get('maroon', '#eba0ac')}",
        red = "{c.get('red', '#f38ba8')}",
        mauve = "{c.get('mauve', '#cba6f7')}",
        pink = "{c.get('pink', '#f5c2e7')}",
        flamingo = "{c.get('flamingo', '#f2cdcd')}",
        rosewater = "{c.get('rosewater', '#f5e0dc')}",
    }},
    terminal = {{
        color0 = "{t.get('color0', '#45475a')}",
        color1 = "{t.get('color1', '#f38ba8')}",
        color2 = "{t.get('color2', '#a6e3a1')}",
        color3 = "{t.get('color3', '#f9e2af')}",
        color4 = "{t.get('color4', '#89b4fa')}",
        color5 = "{t.get('color5', '#cba6f7')}",
        color6 = "{t.get('color6', '#94e2d5')}",
        color7 = "{t.get('color7', '#bac2de')}",
        color8 = "{t.get('color8', '#585b70')}",
        color9 = "{t.get('color9', '#f38ba8')}",
        color10 = "{t.get('color10', '#a6e3a1')}",
        color11 = "{t.get('color11', '#f9e2af')}",
        color12 = "{t.get('color12', '#89b4fa')}",
        color13 = "{t.get('color13', '#cba6f7')}",
        color14 = "{t.get('color14', '#94e2d5')}",
        color15 = "{t.get('color15', '#a6adc8')}",
    }}
}}
"""
    targets = [
        CONFIG_DIR / "nvim" / "lua" / "theme_colors.lua",
        DOTFILES_DIR / "nvim" / "lua" / "theme_colors.lua",
    ]
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(lua_content, encoding="utf-8")
        except Exception as e:
            print(f"Error saving Neovim theme to {target}: {e}", file=sys.stderr)



def update_systemwide_theme(theme):
    """
    Set systemwide light/dark theme across desktop environments and applications.
    Synchronizes:
    - XDG Desktop Portal & GSettings (org.gnome.desktop.interface color-scheme)
    - Dconf keys (/org/gnome/desktop/interface/)
    - GTK 3.0 & GTK 4.0 configuration (~/.config/gtk-3.0/settings.ini & ~/.config/gtk-4.0/settings.ini)
    - XSettings daemon (~/.config/xsettingsd/xsettingsd.conf)
    Ensures Web Browsers (Firefox, Chrome), Electron apps (VS Code, Discord, Obsidian),
    Libadwaita/GTK4 apps, Flatpaks, and Qt/KDE apps switch between light and dark modes automatically.
    """
    is_dark = (theme.get("type", "dark").lower() != "light")
    color_scheme = "prefer-dark" if is_dark else "prefer-light"
    gtk_dark_val = "1" if is_dark else "0"
    gtk_theme_name = "Adwaita-dark" if is_dark else "Adwaita"
    icon_theme_name = "Papirus-Dark" if is_dark else "Papirus-Light"

    # 1. Update GSettings (org.gnome.desktop.interface) - primary source for XDG Desktop Portal
    if shutil.which("gsettings"):
        for schema_key, val in [
            ("color-scheme", color_scheme),
            ("gtk-theme", gtk_theme_name),
            ("icon-theme", icon_theme_name),
        ]:
            try:
                subprocess.run(
                    ["gsettings", "set", "org.gnome.desktop.interface", schema_key, val],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    # 2. Update DConf directly if available
    if shutil.which("dconf"):
        for key_path, val in [
            ("/org/gnome/desktop/interface/color-scheme", f"'{color_scheme}'"),
            ("/org/gnome/desktop/interface/gtk-theme", f"'{gtk_theme_name}'"),
        ]:
            try:
                subprocess.run(
                    ["dconf", "write", key_path, val],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    # 3. Update GTK 3.0 and GTK 4.0 settings.ini
    for gtk_ver in ["gtk-3.0", "gtk-4.0"]:
        gtk_dir = CONFIG_DIR / gtk_ver
        gtk_dir.mkdir(parents=True, exist_ok=True)
        ini_file = gtk_dir / "settings.ini"

        settings_dict = {}
        if ini_file.exists():
            try:
                content = ini_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line_str = line.strip()
                    if "=" in line_str and not line_str.startswith(("#", ";", "[")):
                        k, v = line_str.split("=", 1)
                        settings_dict[k.strip()] = v.strip()
            except Exception:
                pass

        settings_dict["gtk-application-prefer-dark-theme"] = gtk_dark_val
        settings_dict["gtk-color-scheme"] = f'"{color_scheme}"'
        if "gtk-theme-name" not in settings_dict or settings_dict["gtk-theme-name"] in ["Adwaita", "Adwaita-dark", "Breeze", "Breeze-Dark"]:
            settings_dict["gtk-theme-name"] = gtk_theme_name
        if "gtk-icon-theme-name" not in settings_dict or settings_dict["gtk-icon-theme-name"] in ["Papirus", "Papirus-Dark", "Papirus-Light"]:
            settings_dict["gtk-icon-theme-name"] = icon_theme_name

        new_lines = ["[Settings]"]
        for k, v in sorted(settings_dict.items()):
            new_lines.append(f"{k} = {v}")
        new_lines.append("")

        new_content = "\n".join(new_lines)
        try:
            ini_file.write_text(new_content, encoding="utf-8")
            df_gtk_file = DOTFILES_DIR / gtk_ver / "settings.ini"
            if df_gtk_file.parent.exists():
                df_gtk_file.write_text(new_content, encoding="utf-8")
        except Exception as e:
            print(f"Error writing {ini_file}: {e}", file=sys.stderr)

    # 4. Update XSettings daemon config (xsettingsd)
    xsettings_dir = CONFIG_DIR / "xsettingsd"
    xsettings_dir.mkdir(parents=True, exist_ok=True)
    xsettings_file = xsettings_dir / "xsettingsd.conf"
    xsettings_content = f"""Net/ThemeName "{gtk_theme_name}"
Net/IconThemeName "{icon_theme_name}"
Gtk/ApplicationPreferDarkTheme {gtk_dark_val}
Gtk/ColorScheme "{color_scheme}"
"""
    try:
        xsettings_file.write_text(xsettings_content, encoding="utf-8")
        df_xsettings = DOTFILES_DIR / "xsettingsd" / "xsettingsd.conf"
        if df_xsettings.parent.exists():
            df_xsettings.write_text(xsettings_content, encoding="utf-8")
    except Exception:
        pass

    # 5. Trigger portal refresh so running apps receive the updated setting immediately
    if shutil.which("gdbus"):
        try:
            subprocess.run(
                [
                    "gdbus", "call", "--session",
                    "--dest", "org.freedesktop.portal.Desktop",
                    "--object-path", "/org/freedesktop/portal/desktop",
                    "--method", "org.freedesktop.portal.Settings.Read",
                    "org.freedesktop.appearance", "color-scheme"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
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

    # 6. Reload or spawn xsettingsd daemon
    if shutil.which("xsettingsd"):
        try:
            res = subprocess.run(["killall", "-HUP", "xsettingsd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode != 0:
                subprocess.Popen(["xsettingsd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def send_theme_notification(theme):
    """Send visual desktop notification with theme information."""
    if not shutil.which("notify-send"):
        return
    c = theme["colors"]
    icon = "preferences-desktop-theme"
    theme_name = theme.get("name", theme["id"])
    theme_type = theme.get("type", "dark").capitalize()
    theme_desc = theme.get("desc", "")
    accent = c.get("accent", "")
    
    title = f"🎨 Theme Applied: {theme_name}"
    body = f"Mode: {theme_type}   •   Accent: {accent}\n{theme_desc}"
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
    generate_nvim_theme(theme)
    update_systemwide_theme(theme)

    # Save state
    save_state(theme_id)

    # Live reload desktop
    reload_desktop()

    # Enforce git skip-worktree so theme switching never taints git status
    set_git_skip_worktree(skip=True, quiet=True)

    if notify:
        send_theme_notification(theme)

    print(f"{C_GREEN}✓ Successfully applied theme:{C_RESET} {C_BOLD}{theme.get('name', theme_id)}{C_RESET} ({theme_id})")
    return True


# =============================================================================
# Interactive GUI Menu (Fuzzel / Wofi / GTK3)
# =============================================================================
def run_interactive_menu(themes):
    """Display an interactive, beautifully formatted Fuzzel or Wofi graphical menu to select a theme."""
    current = get_current_theme(themes)
    menu_items = []
    
    # Top action: Launch Full Graphical Theme Manager GUI
    gui_entry = "󰒓  Launch Visual Theme Manager (GUI)..."
    menu_items.append((gui_entry, "__LAUNCH_GUI__"))

    # Add all themes with razor-sharp column alignment
    sorted_themes = sorted(themes.items(), key=lambda x: x[1].get("name", x[0]))
    active_line_str = None

    for tid, tdata in sorted_themes:
        is_active = (tid == current)
        bullet = "●" if is_active else "○"
        ttype = "[Dark] " if tdata.get("type") == "dark" else "[Light]"
        name = tdata.get("name", tid)
        desc = tdata.get("desc", "")
        
        display_line = f"{bullet}  {name:<23}  {ttype}   {desc}"
        menu_items.append((display_line, tid))
        if is_active:
            active_line_str = display_line

    menu_input = "\n".join(item[0] for item in menu_items)
    selected_tid = None

    if shutil.which("fuzzel"):
        cmd = [
            "fuzzel",
            "--dmenu",
            "--prompt", " 󰏘 Theme ❯ ",
            "--placeholder", "Filter 19 color themes (dark, light, pastel, vibrant)...",
            "--width", "78",
            "--lines", "14",
            "--horizontal-pad", "26",
            "--vertical-pad", "16",
            "--inner-pad", "10",
            "--line-height", "32",
            "--border-radius", "16",
        ]
        if active_line_str:
            cmd.extend(["--select", active_line_str])

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
            "--prompt", " 󰏘 Select Theme: ",
            "--width", "720",
            "--lines", "14",
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

    if selected_tid == "__LAUNCH_GUI__":
        run_gui_theme_manager(themes)
    elif selected_tid:
        apply_theme(selected_tid, themes=themes, notify=True)


# =============================================================================
# Modern GTK3 Graphical Theme Manager Window
# =============================================================================
def run_gui_theme_manager(themes=None):
    """Launch the modern graphical GTK3 Theme Manager with cards, color palettes, and live preview."""
    if themes is None:
        themes = load_themes()

    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Gdk, GLib, Pango
    except Exception as e:
        print(f"GTK3 not available ({e}), falling back to interactive menu.", file=sys.stderr)
        run_interactive_menu(themes)
        return

    current_id = get_current_theme(themes)

    def get_theme_manager_gtk_css(c, theme_type="dark"):
        is_dark = (theme_type == "dark")
        base = c.get("base", "#1e1e2e")
        mantle = c.get("mantle", "#181825")
        crust = c.get("crust", "#11111b")
        s0 = c.get("surface0", "#313244")
        s1 = c.get("surface1", "#45475a")
        s2 = c.get("surface2", "#585b70")
        text = c.get("text", "#cdd6f4")
        sub1 = c.get("subtext1", "#bac2de")
        sub0 = c.get("subtext0", "#a6adc8")
        accent = c.get("accent", "#cba6f7")
        blue = c.get("blue", "#89b4fa")
        green = c.get("green", "#a6e3a1")
        yellow = c.get("yellow", "#f9e2af")
        peach = c.get("peach", "#fab387")
        red = c.get("red", "#f38ba8")
        teal = c.get("teal", "#94e2d5")

        return f"""
        * {{
            font-family: 'Inter', 'Noto Sans', 'Segoe UI', 'Ubuntu', system-ui, sans-serif;
        }}
        window, dialog, .dialog-vbox {{
            background-color: {base};
            color: {text};
        }}
        headerbar {{
            background-color: {mantle};
            background-image: none;
            border-bottom: 1.5px solid {s0};
            padding: 8px 14px;
            color: {text};
        }}
        headerbar .title, headerbar .subtitle {{
            color: {text};
        }}
        entry, entry.search-input, .entry {{
            background-color: {s0};
            background-image: none;
            color: {text};
            border: 1.5px solid {s1};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 500;
        }}
        entry:focus, entry.search-input:focus {{
            border-color: {accent};
            background-color: {mantle};
            color: {text};
            box-shadow: 0 0 0 2px {accent}44;
        }}
        combobox, combobox button, combobox textview, combobox cellview {{
            background-color: {s0};
            background-image: none;
            color: {text};
            border: 1.5px solid {s1};
            border-radius: 8px;
            padding: 4px 8px;
        }}
        combobox button:hover {{
            background-color: {s1};
            border-color: {accent};
        }}
        combobox window, combobox menu, combobox .menu, menu, .menu {{
            background-color: {mantle};
            color: {text};
            border: 1px solid {s1};
        }}
        menuitem:hover, .menuitem:hover {{
            background-color: {s1};
            color: {text};
        }}
        button {{
            background-color: {s0};
            background-image: none;
            color: {text};
            border: 1.5px solid {s1};
            border-radius: 8px;
            padding: 7px 14px;
            font-weight: 700;
            font-size: 13px;
            transition: all 120ms ease-in-out;
        }}
        button:hover {{
            background-color: {s1};
            border-color: {accent};
            color: {text};
        }}
        button.btn-new {{
            background-color: {accent};
            background-image: none;
            color: {crust};
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-weight: 800;
            font-size: 13px;
        }}
        button.btn-new:hover {{
            background-color: {blue};
            color: {crust};
        }}
        button.btn-random {{
            background-color: {s0};
            background-image: none;
            color: {text};
            border: 1.5px solid {s1};
            border-radius: 8px;
            padding: 6px 12px;
            font-weight: 700;
        }}
        button.btn-random:hover {{
            background-color: {s1};
            border-color: {yellow};
            color: {text};
        }}
        button.filter-btn {{
            background-color: {mantle};
            background-image: none;
            color: {sub1};
            border: 1.5px solid {s0};
            border-radius: 20px;
            padding: 5px 14px;
            font-size: 12px;
            font-weight: 700;
        }}
        button.filter-btn:hover {{
            background-color: {s0};
            border-color: {accent};
            color: {text};
        }}
        button.filter-btn.active-filter {{
            background-color: {accent};
            background-image: none;
            color: {crust};
            border-color: {accent};
            font-weight: 800;
        }}
        button.btn-action-small {{
            background-color: {s0};
            background-image: none;
            color: {text};
            border: 1.5px solid {s1};
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 700;
        }}
        button.btn-action-small:hover {{
            background-color: {s1};
            color: {text};
            border-color: {accent};
        }}
        button.btn-delete {{
            background-color: {s0};
            background-image: none;
            color: {red};
            border: 1.5px solid {s1};
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 700;
        }}
        button.btn-delete:hover {{
            background-color: {red};
            color: {crust};
            border-color: {red};
        }}
        button.apply-btn {{
            background-color: {green};
            background-image: none;
            color: {crust};
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 800;
            padding: 12px 20px;
        }}
        button.apply-btn:hover {{
            background-color: {teal};
            color: {crust};
        }}
        .card-box {{
            background-color: {mantle};
            border: 1.5px solid {s0};
            border-radius: 14px;
            padding: 12px 14px;
            transition: all 120ms ease;
        }}
        .card-box:hover {{
            border-color: {s2};
            background-color: {s0};
        }}
        .card-box-selected {{
            border: 2px solid {accent};
            background-color: {s0};
            box-shadow: 0 4px 16px {accent}33;
        }}
        .card-box-active {{
            border: 2px solid {green};
        }}
        .preview-pane {{
            background-color: {mantle};
            border-left: 1.5px solid {s0};
            padding: 20px;
        }}
        .matrix-box {{
            background-color: {base};
            border: 1.5px solid {s0};
            border-radius: 12px;
            padding: 12px;
        }}
        .editor-frame {{
            background-color: {mantle};
            border: 1.5px solid {s0};
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }}
        .badge-dark {{
            background-color: {s1};
            color: {text};
            border: 1px solid {s2};
            border-radius: 6px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 700;
        }}
        .badge-light {{
            background-color: {peach};
            color: {crust};
            border: 1px solid {yellow};
            border-radius: 6px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 800;
        }}
        .badge-active {{
            background-color: {green};
            color: {crust};
            border: 1px solid {green};
            border-radius: 6px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 800;
        }}
        scrollbar slider {{
            background-color: {s1};
            border-radius: 8px;
            min-width: 6px;
        }}
        scrollbar slider:hover {{
            background-color: {accent};
        }}
        """

    class ThemeManagerWindow(Gtk.Window):
        def __init__(self, theme_dict, cur_id):
            super().__init__(title="Desktop Theme & Palette Manager")
            self.themes = theme_dict
            self.current_theme_id = cur_id
            self.selected_theme_id = cur_id
            self.filter_mode = "all"
            self.search_query = ""

            self.set_default_size(1080, 720)
            self.set_position(Gtk.WindowPosition.CENTER)

            self.css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            self._setup_css()
            self._build_ui()

        def _setup_css(self):
            tdata = self.themes.get(self.current_theme_id) or self.themes.get(DEFAULT_THEME, {})
            colors = tdata.get("colors", {})
            ttype = tdata.get("type", "dark")
            css_str = get_theme_manager_gtk_css(colors, ttype)
            try:
                self.css_provider.load_from_data(css_str.encode('utf-8'))
            except Exception as e:
                print(f"Warning: Failed to load custom CSS: {e}", file=sys.stderr)

        def _build_ui(self):
            tdata = self.themes.get(self.current_theme_id) or self.themes.get(DEFAULT_THEME, {})
            c = tdata.get("colors", {})
            txt_color = c.get("text", "#ffffff")
            sub_color = c.get("subtext1", "#bac2de")

            # HeaderBar
            header = Gtk.HeaderBar()
            header.set_show_close_button(True)
            
            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            self.title_lbl = Gtk.Label()
            self.title_lbl.set_markup(f"<span size='12000' weight='bold'>🎨 Desktop Theme Switcher &amp; Palette Manager</span>")
            self.subtitle_lbl = Gtk.Label()
            self.subtitle_lbl.set_markup(f"<span size='9500'>{len(self.themes)} Handcrafted Palettes • Hyprland, Waybar &amp; Apps</span>")
            title_box.pack_start(self.title_lbl, False, False, 0)
            title_box.pack_start(self.subtitle_lbl, False, False, 0)
            header.set_custom_title(title_box)

            # Action Buttons in HeaderBar
            btn_new = Gtk.Button(label="󰐕  New Theme")
            btn_new.get_style_context().add_class("btn-new")
            btn_new.connect("clicked", lambda b: self._open_theme_editor(create_new=True))
            header.pack_start(btn_new)

            btn_random = Gtk.Button(label="🎲 Random")
            btn_random.get_style_context().add_class("btn-random")
            btn_random.connect("clicked", self._on_random_clicked)
            header.pack_start(btn_random)

            self.set_titlebar(header)

            # Main Layout
            main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
            main_paned.set_position(680)
            self.add(main_paned)

            # Left Column (Search + Filters + Theme Grid)
            left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            left_box.set_margin_top(14)
            left_box.set_margin_bottom(14)
            left_box.set_margin_start(16)
            left_box.set_margin_end(12)
            main_paned.pack1(left_box, resize=True, shrink=False)

            # Top Bar: Search Entry & Filter Buttons
            top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            self.search_entry = Gtk.SearchEntry()
            self.search_entry.set_placeholder_text("🔍 Filter themes by name, mode, color or style...")
            self.search_entry.get_style_context().add_class("search-input")
            self.search_entry.connect("search-changed", self._on_search_changed)
            top_bar.pack_start(self.search_entry, True, True, 0)

            # Filter buttons
            dark_count = sum(1 for t in self.themes.values() if t.get("type") == "dark")
            light_count = len(self.themes) - dark_count

            self.btn_filter_all = Gtk.Button(label=f"All ({len(self.themes)})")
            self.btn_filter_all.get_style_context().add_class("filter-btn")
            self.btn_filter_all.get_style_context().add_class("active-filter")
            self.btn_filter_all.connect("clicked", lambda b: self._set_filter("all"))
            top_bar.pack_start(self.btn_filter_all, False, False, 0)

            self.btn_filter_dark = Gtk.Button(label=f"🌙 Dark ({dark_count})")
            self.btn_filter_dark.get_style_context().add_class("filter-btn")
            self.btn_filter_dark.connect("clicked", lambda b: self._set_filter("dark"))
            top_bar.pack_start(self.btn_filter_dark, False, False, 0)

            self.btn_filter_light = Gtk.Button(label=f"☀️ Light ({light_count})")
            self.btn_filter_light.get_style_context().add_class("filter-btn")
            self.btn_filter_light.connect("clicked", lambda b: self._set_filter("light"))
            top_bar.pack_start(self.btn_filter_light, False, False, 0)

            left_box.pack_start(top_bar, False, False, 0)

            # Scrollable Theme Grid
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            left_box.pack_start(scrolled, True, True, 0)

            self.grid = Gtk.Grid()
            self.grid.set_column_spacing(12)
            self.grid.set_row_spacing(12)
            self.grid.set_column_homogeneous(True)
            scrolled.add(self.grid)

            # Right Column (Theme Preview & Details Inspector)
            self.preview_pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            self.preview_pane.get_style_context().add_class("preview-pane")
            self.preview_pane.set_size_request(360, -1)
            main_paned.pack2(self.preview_pane, resize=False, shrink=False)

            self.card_widgets = {}
            self._populate_grid()
            self._update_preview()

            # Keyboard navigation
            self.connect("key-press-event", self._on_key_press)

        def _create_color_chip(self, hex_val, tooltip=None, size=22):
            rf, gf, bf = [c / 255.0 for c in hex_to_rgb_tuple(hex_val)]
            area = Gtk.DrawingArea()
            area.set_size_request(size, size)
            if tooltip:
                area.set_tooltip_text(f"{tooltip}: {hex_val}")

            def on_draw(w, cr):
                radius = 5
                x, y, width, height = 0, 0, size, size
                deg = 3.14159265 / 180.0
                cr.new_sub_path()
                cr.arc(x + width - radius, y + radius, radius, -90 * deg, 0 * deg)
                cr.arc(x + width - radius, y + height - radius, radius, 0 * deg, 90 * deg)
                cr.arc(x + radius, y + height - radius, radius, 90 * deg, 180 * deg)
                cr.arc(x + radius, y + radius, radius, 180 * deg, 270 * deg)
                cr.close_path()

                cr.set_source_rgb(rf, gf, bf)
                cr.fill_preserve()
                cr.set_source_rgba(0, 0, 0, 0.3)
                cr.set_line_width(1)
                cr.stroke()
                return False

            area.connect("draw", on_draw)
            return area

        def _populate_grid(self):
            for child in self.grid.get_children():
                self.grid.remove(child)
            self.card_widgets.clear()

            row, col = 0, 0
            sorted_themes = sorted(self.themes.items(), key=lambda x: x[1].get("name", x[0]))

            for tid, tdata in sorted_themes:
                ttype = tdata.get("type", "dark")
                if self.filter_mode != "all" and ttype != self.filter_mode:
                    continue

                q = self.search_query.lower()
                name = tdata.get("name", tid)
                desc = tdata.get("desc", "")
                if q and (q not in name.lower() and q not in desc.lower() and q not in tid.lower() and q not in ttype.lower()):
                    continue

                is_active = (tid == self.current_theme_id)
                is_selected = (tid == self.selected_theme_id)

                card = Gtk.EventBox()
                card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
                card_box.get_style_context().add_class("card-box")
                if is_selected:
                    card_box.get_style_context().add_class("card-box-selected")
                if is_active:
                    card_box.get_style_context().add_class("card-box-active")

                card.add(card_box)

                # Header row: Title + Badges
                h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                icon = tdata.get("icon", "🎨")
                title_label = Gtk.Label()
                title_label.set_markup(f"<span size='10500' weight='bold'>{icon}  {name}</span>")
                title_label.set_xalign(0)
                title_label.set_ellipsize(Pango.EllipsizeMode.END)
                h_box.pack_start(title_label, True, True, 0)

                badge = Gtk.Label(label="🌙 Dark" if ttype == "dark" else "☀️ Light")
                badge.get_style_context().add_class("badge-dark" if ttype == "dark" else "badge-light")
                h_box.pack_start(badge, False, False, 0)

                if is_active:
                    act_badge = Gtk.Label(label="✓ ACTIVE")
                    act_badge.get_style_context().add_class("badge-active")
                    h_box.pack_start(act_badge, False, False, 0)

                card_box.pack_start(h_box, False, False, 0)

                # Description
                desc_lbl = Gtk.Label()
                desc_lbl.set_markup(f"<span size='9000'>{desc}</span>")
                desc_lbl.set_xalign(0)
                desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                desc_lbl.set_max_width_chars(32)
                card_box.pack_start(desc_lbl, False, False, 0)

                # Swatch Palette Strip
                c = tdata.get("colors", {})
                swatch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                for k in ["base", "surface0", "accent", "blue", "green", "yellow", "red", "mauve", "teal"]:
                    if k in c and isinstance(c[k], str) and c[k].startswith("#"):
                        chip = self._create_color_chip(c[k], tooltip=k, size=18)
                        swatch_box.pack_start(chip, False, False, 0)
                card_box.pack_start(swatch_box, False, False, 0)

                # Card click event handling
                card.connect("button-press-event", self._on_card_clicked, tid)
                self.card_widgets[tid] = (card, card_box)

                self.grid.attach(card, col, row, 1, 1)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1

            self.grid.show_all()

        def _on_card_clicked(self, widget, event, tid):
            self.selected_theme_id = tid
            self._update_card_styles()
            self._update_preview()
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self._apply_selected_theme()

        def _update_card_styles(self):
            for tid, (card, card_box) in self.card_widgets.items():
                ctx = card_box.get_style_context()
                if tid == self.selected_theme_id:
                    ctx.add_class("card-box-selected")
                else:
                    ctx.remove_class("card-box-selected")

        def _update_preview(self):
            for child in self.preview_pane.get_children():
                self.preview_pane.remove(child)

            tdata = self.themes.get(self.selected_theme_id)
            if not tdata:
                return

            c = tdata.get("colors", {})
            name = tdata.get("name", self.selected_theme_id)
            ttype = tdata.get("type", "dark").capitalize()
            desc = tdata.get("desc", "")
            accent = c.get("accent", "#cba6f7")

            p_title = Gtk.Label()
            p_title.set_markup(f"<span size='15000' weight='heavy'>{tdata.get('icon', '🎨')}  {name}</span>")
            p_title.set_xalign(0)
            self.preview_pane.pack_start(p_title, False, False, 0)

            p_meta = Gtk.Label()
            p_meta.set_markup(f"<span size='10000'>Mode: <b>{ttype}</b>   •   Accent: <span font_family='monospace' weight='bold'>{accent}</span></span>")
            p_meta.set_xalign(0)
            self.preview_pane.pack_start(p_meta, False, False, 0)

            p_desc = Gtk.Label()
            p_desc.set_markup(f"<span size='9500'>{desc}</span>")
            p_desc.set_xalign(0)
            p_desc.set_line_wrap(True)
            self.preview_pane.pack_start(p_desc, False, False, 0)

            # Theme Management Action Bar (Duplicate / Copy, Edit, Delete)
            action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            
            btn_copy = Gtk.Button(label="󰆏 Copy / Fork")
            btn_copy.get_style_context().add_class("btn-action-small")
            btn_copy.set_tooltip_text("Create a new theme based on this palette")
            btn_copy.connect("clicked", lambda b: self._open_theme_editor(theme_data=tdata, is_copy=True))
            action_bar.pack_start(btn_copy, True, True, 0)

            btn_edit = Gtk.Button(label="✏️ Edit")
            btn_edit.get_style_context().add_class("btn-action-small")
            btn_edit.set_tooltip_text("Edit this theme definition")
            btn_edit.connect("clicked", lambda b: self._open_theme_editor(theme_data=tdata, is_copy=False))
            action_bar.pack_start(btn_edit, True, True, 0)

            btn_del = Gtk.Button(label="🗑️ Delete")
            btn_del.get_style_context().add_class("btn-delete")
            btn_del.set_tooltip_text("Delete this custom theme")
            btn_del.connect("clicked", lambda b: self._confirm_delete_theme(tdata))
            action_bar.pack_start(btn_del, False, False, 0)

            self.preview_pane.pack_start(action_bar, False, False, 2)
            self.preview_pane.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 2)

            # Palette matrix box
            pal_label = Gtk.Label()
            pal_label.set_markup("<span size='10500' weight='bold'>🎨 Color Palette Matrix</span>")
            pal_label.set_xalign(0)
            self.preview_pane.pack_start(pal_label, False, False, 0)

            matrix_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            matrix_frame.get_style_context().add_class("matrix-box")

            pal_grid = Gtk.Grid()
            pal_grid.set_column_spacing(10)
            pal_grid.set_row_spacing(8)
            r, c_idx = 0, 0
            swatch_keys = ["base", "mantle", "surface0", "surface1", "accent", "blue", "green", "yellow", "peach", "red", "mauve", "teal"]
            for k in swatch_keys:
                if k in c and isinstance(c[k], str) and c[k].startswith("#"):
                    chip = self._create_color_chip(c[k], tooltip=f"{k}: {c[k]}", size=20)
                    lbl = Gtk.Label()
                    lbl.set_markup(f"<span size='9000'><b>{k}:</b> <span font_family='monospace'>{c[k]}</span></span>")
                    lbl.set_xalign(0)
                    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                    box.pack_start(chip, False, False, 0)
                    box.pack_start(lbl, False, False, 0)
                    pal_grid.attach(box, c_idx, r, 1, 1)
                    r += 1
                    if r >= 6:
                        r = 0
                        c_idx += 1

            matrix_frame.pack_start(pal_grid, True, True, 0)
            self.preview_pane.pack_start(matrix_frame, False, False, 0)

            self.preview_pane.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 2)

            # Apply Button
            btn_apply = Gtk.Button(label=f"✓  Apply Theme: {name}")
            btn_apply.get_style_context().add_class("apply-btn")
            btn_apply.set_size_request(-1, 42)
            btn_apply.connect("clicked", lambda b: self._apply_selected_theme())
            self.preview_pane.pack_start(btn_apply, False, False, 4)

            self.preview_pane.show_all()

        def _open_theme_editor(self, theme_data=None, is_copy=False, create_new=False):
            dialog = ThemeEditorDialog(self, theme_to_edit=theme_data, is_copy=is_copy, all_themes=self.themes)
            dialog.show_all()

        def _confirm_delete_theme(self, theme_data):
            tid = theme_data.get("id")
            if not tid:
                return

            if tid == DEFAULT_THEME:
                msg_dlg = Gtk.MessageDialog(
                    transient_for=self,
                    flags=Gtk.DialogFlags.MODAL,
                    type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    message_format=f"Cannot delete default fallback theme '{theme_data.get('name', tid)}'."
                )
                msg_dlg.run()
                msg_dlg.destroy()
                return

            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                message_format=f"Delete Theme '{theme_data.get('name', tid)}'?"
            )
            dialog.format_secondary_text(f"This will permanently delete the JSON theme file for '{tid}'. This action cannot be undone.")
            res = dialog.run()
            dialog.destroy()

            if res == Gtk.ResponseType.YES:
                deleted = False
                for d in [THEME_DIR, FALLBACK_THEME_DIR]:
                    tfile = d / f"{tid}.json"
                    if tfile.exists():
                        try:
                            tfile.unlink()
                            deleted = True
                        except Exception as e:
                            print(f"Error deleting {tfile}: {e}", file=sys.stderr)
                if deleted:
                    print(f"{C_GREEN}✓ Deleted theme:{C_RESET} {tid}")
                    self.themes = load_themes()
                    if self.selected_theme_id == tid:
                        self.selected_theme_id = DEFAULT_THEME
                    if self.current_theme_id == tid:
                        self.current_theme_id = DEFAULT_THEME
                        apply_theme(DEFAULT_THEME, themes=self.themes, notify=True)
                    self._update_filter_button_labels()
                    self._setup_css()
                    self._populate_grid()
                    self._update_preview()

        def _update_filter_button_labels(self):
            dark_count = sum(1 for t in self.themes.values() if t.get("type") == "dark")
            light_count = len(self.themes) - dark_count
            self.btn_filter_all.set_label(f"All ({len(self.themes)})")
            self.btn_filter_dark.set_label(f"🌙 Dark ({dark_count})")
            self.btn_filter_light.set_label(f"☀️ Light ({light_count})")

        def _reload_themes(self, select_id=None, apply_immediately=False):
            self.themes = load_themes()
            if select_id and select_id in self.themes:
                self.selected_theme_id = select_id
            self._update_filter_button_labels()
            self._populate_grid()
            self._update_preview()
            if apply_immediately and select_id:
                self._apply_selected_theme()

        def _apply_selected_theme(self):
            if self.selected_theme_id:
                self.current_theme_id = self.selected_theme_id
                apply_theme(self.selected_theme_id, themes=self.themes, notify=True)
                self._setup_css()
                self._populate_grid()
                self._update_preview()

        def _on_search_changed(self, entry):
            self.search_query = entry.get_text().strip()
            self._populate_grid()

        def _set_filter(self, mode):
            self.filter_mode = mode
            for btn, m in [(self.btn_filter_all, "all"), (self.btn_filter_dark, "dark"), (self.btn_filter_light, "light")]:
                ctx = btn.get_style_context()
                if m == mode:
                    ctx.add_class("active-filter")
                else:
                    ctx.remove_class("active-filter")
            self._populate_grid()

        def _on_random_clicked(self, btn):
            import random
            candidates = list(self.themes.keys())
            if candidates:
                self.selected_theme_id = random.choice(candidates)
                self._apply_selected_theme()

        def _on_key_press(self, widget, event):
            if event.keyval == Gdk.KEY_Escape:
                self.destroy()
                return True
            elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                self._apply_selected_theme()
                return True
            return False

    # =========================================================================
    # 🎨 Theme Editor & Creator Dialog Modal
    # =========================================================================
    class ThemeEditorDialog(Gtk.Dialog):
        def __init__(self, parent_win, theme_to_edit=None, is_copy=False, all_themes=None):
            title = "🎨 Create New Theme"
            if theme_to_edit:
                title = f"󰆏 Duplicate Theme: {theme_to_edit.get('name', '')}" if is_copy else f"✏️ Edit Theme: {theme_to_edit.get('name', '')}"

            super().__init__(title=title, transient_for=parent_win, flags=Gtk.DialogFlags.MODAL)
            self.set_default_size(820, 740)
            self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            self.parent_win = parent_win
            self.all_themes = all_themes or {}
            self.theme_to_edit = theme_to_edit
            self.is_copy = is_copy
            self.color_widgets = {}  # {k: (color_button, hex_entry)}

            self._build_editor_ui()

        def _build_editor_ui(self):
            # Header bar with Save & Cancel
            header = Gtk.HeaderBar()
            header.set_show_close_button(False)
            
            title_text = "Create New Theme"
            if self.theme_to_edit:
                title_text = "Duplicate Theme" if self.is_copy else "Edit Theme"

            header.set_title(title_text)
            header.set_subtitle("Customize color palette, metadata & live preview")

            btn_cancel = Gtk.Button(label="Cancel")
            btn_cancel.get_style_context().add_class("btn-action-small")
            btn_cancel.connect("clicked", lambda b: self.destroy())
            header.pack_start(btn_cancel)

            btn_save = Gtk.Button(label="💾  Save & Apply")
            btn_save.get_style_context().add_class("btn-new")
            btn_save.connect("clicked", lambda b: self._save_theme(apply_now=True))
            header.pack_end(btn_save)

            self.set_titlebar(header)

            content_area = self.get_content_area()
            content_area.set_spacing(10)
            content_area.set_margin_start(16)
            content_area.set_margin_end(16)
            content_area.set_margin_top(12)
            content_area.set_margin_bottom(12)

            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            content_area.pack_start(scrolled, True, True, 0)

            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            scrolled.add(main_box)

            # Determine initial values
            default_tdata = self.all_themes.get(DEFAULT_THEME, {})
            source_data = self.theme_to_edit if self.theme_to_edit else default_tdata
            initial_colors = source_data.get("colors", {})

            # -----------------------------------------------------------------
            # 1. Template Seed Chooser
            # -----------------------------------------------------------------
            seed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            seed_lbl = Gtk.Label()
            seed_lbl.set_markup("<span size='10500' weight='bold'>🌱 Seed from Template:</span>")
            seed_box.pack_start(seed_lbl, False, False, 0)

            self.seed_combo = Gtk.ComboBoxText()
            self.seed_combo.append_text("— Choose existing palette to seed colors —")
            theme_names = sorted(self.all_themes.keys())
            for tid in theme_names:
                tname = self.all_themes[tid].get("name", tid)
                self.seed_combo.append_text(f"{tname} ({tid})")
            self.seed_combo.set_active(0)
            self.seed_combo.connect("changed", self._on_seed_template_changed)
            seed_box.pack_start(self.seed_combo, True, True, 0)
            main_box.pack_start(seed_box, False, False, 0)

            # -----------------------------------------------------------------
            # 2. Metadata Section Frame
            # -----------------------------------------------------------------
            meta_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            meta_frame.get_style_context().add_class("editor-frame")
            
            meta_title = Gtk.Label()
            meta_title.set_markup("<span size='11500' weight='bold'>📋 Theme Identity &amp; Metadata</span>")
            meta_title.set_xalign(0)
            meta_frame.pack_start(meta_title, False, False, 0)

            meta_grid = Gtk.Grid()
            meta_grid.set_column_spacing(14)
            meta_grid.set_row_spacing(10)

            # Name
            lbl_name = Gtk.Label(label="Display Name:")
            lbl_name.set_xalign(0)
            self.entry_name = Gtk.Entry()
            self.entry_name.get_style_context().add_class("entry")
            init_name = source_data.get("name", "")
            if self.is_copy:
                init_name += " (Copy)"
            self.entry_name.set_text(init_name if self.theme_to_edit else "My Custom Theme")
            self.entry_name.connect("changed", self._on_meta_changed)
            meta_grid.attach(lbl_name, 0, 0, 1, 1)
            meta_grid.attach(self.entry_name, 1, 0, 1, 1)

            # Slug / ID
            lbl_id = Gtk.Label(label="Theme ID (Filename):")
            lbl_id.set_xalign(0)
            self.entry_id = Gtk.Entry()
            self.entry_id.get_style_context().add_class("entry")
            init_id = source_data.get("id", "")
            if self.is_copy:
                init_id += "-copy"
            elif not self.theme_to_edit:
                init_id = "my-custom-theme"
            self.entry_id.set_text(init_id)
            meta_grid.attach(lbl_id, 2, 0, 1, 1)
            meta_grid.attach(self.entry_id, 3, 0, 1, 1)

            # Icon
            lbl_icon = Gtk.Label(label="Icon / Symbol:")
            lbl_icon.set_xalign(0)
            self.entry_icon = Gtk.Entry()
            self.entry_icon.get_style_context().add_class("entry")
            self.entry_icon.set_text(source_data.get("icon", "🎨"))
            self.entry_icon.set_max_length(4)
            meta_grid.attach(lbl_icon, 0, 1, 1, 1)
            meta_grid.attach(self.entry_icon, 1, 1, 1, 1)

            # Mode (Dark / Light)
            lbl_type = Gtk.Label(label="Theme Mode:")
            lbl_type.set_xalign(0)
            self.combo_type = Gtk.ComboBoxText()
            self.combo_type.append_text("🌙 Dark")
            self.combo_type.append_text("☀️ Light")
            self.combo_type.set_active(1 if source_data.get("type") == "light" else 0)
            self.combo_type.connect("changed", self._on_meta_changed)
            meta_grid.attach(lbl_type, 2, 1, 1, 1)
            meta_grid.attach(self.combo_type, 3, 1, 1, 1)

            # Description
            lbl_desc = Gtk.Label(label="Description:")
            lbl_desc.set_xalign(0)
            self.entry_desc = Gtk.Entry()
            self.entry_desc.get_style_context().add_class("entry")
            self.entry_desc.set_text(source_data.get("desc", "A personalized desktop color theme"))
            self.entry_desc.connect("changed", self._on_meta_changed)
            meta_grid.attach(lbl_desc, 0, 2, 1, 1)
            meta_grid.attach(self.entry_desc, 1, 2, 3, 1)

            meta_frame.pack_start(meta_grid, False, False, 0)
            main_box.pack_start(meta_frame, False, False, 0)

            # -----------------------------------------------------------------
            # 3. Palette Studio Section
            # -----------------------------------------------------------------
            pal_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            pal_frame.get_style_context().add_class("editor-frame")

            pal_title = Gtk.Label()
            pal_title.set_markup("<span size='11500' weight='bold'>🎨 Color Palette Studio</span>")
            pal_title.set_xalign(0)
            pal_frame.pack_start(pal_title, False, False, 0)

            # Color Categories Definition
            categories = [
                ("1. Core Backgrounds", [
                    ("base", "Base Background", "Main app & window background", "#1e1e2e"),
                    ("mantle", "Mantle Surface", "Cards, sidebars, modals & drawers", "#181825"),
                    ("crust", "Crust Contrast", "Headerbars, dock & deep contrast", "#11111b"),
                ]),
                ("2. Surfaces & Borders", [
                    ("surface0", "Surface 0", "Card borders, inactive buttons", "#313244"),
                    ("surface1", "Surface 1", "Hover states, active button bg", "#45475a"),
                    ("surface2", "Surface 2", "Dividers, highlights & borders", "#585b70"),
                    ("overlay0", "Overlay 0", "Placeholder & subtle elements", "#6c7086"),
                ]),
                ("3. Typography & Text", [
                    ("text", "Primary Text", "Main titles, labels and icons", "#cdd6f4"),
                    ("subtext1", "Subtext 1", "Secondary labels & subtitles", "#bac2de"),
                    ("subtext0", "Subtext 0", "Muted comments & descriptions", "#a6adc8"),
                ]),
                ("4. Accent & Brand Colors", [
                    ("accent", "Brand Accent", "Primary focus, glow & border highlights", "#cba6f7"),
                    ("blue", "Blue", "Informational & primary status", "#89b4fa"),
                    ("green", "Green", "Success, active state & confirm", "#a6e3a1"),
                    ("yellow", "Yellow", "Warning, search highlight & tips", "#f9e2af"),
                    ("peach", "Peach / Orange", "Special notifications & battery", "#fab387"),
                    ("red", "Red / Danger", "Errors, critical warnings & destructive", "#f38ba8"),
                    ("mauve", "Mauve / Purple", "Launcher highlights & keybind tags", "#cba6f7"),
                    ("teal", "Teal / Cyan", "Terminal cyan, disk meter & metrics", "#94e2d5"),
                    ("pink", "Pink / Magenta", "Special badges & audio mixer streams", "#f5c2e7"),
                    ("lavender", "Lavender", "Clock, date labels & secondary glow", "#b4befe"),
                ]),
            ]

            for cat_title, color_list in categories:
                cat_lbl = Gtk.Label()
                cat_lbl.set_markup(f"<span size='10500' weight='bold'>{cat_title}</span>")
                cat_lbl.set_xalign(0)
                pal_frame.pack_start(cat_lbl, False, False, 2)

                c_grid = Gtk.Grid()
                c_grid.set_column_spacing(16)
                c_grid.set_row_spacing(8)

                col, row = 0, 0
                for c_key, c_label, c_desc, c_def in color_list:
                    init_hex = initial_colors.get(c_key, c_def)
                    
                    row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    
                    lbl = Gtk.Label()
                    lbl.set_markup(f"<span size='9500' weight='bold'>{c_label}:</span>")
                    lbl.set_xalign(0)
                    lbl.set_size_request(130, -1)
                    lbl.set_tooltip_text(c_desc)
                    row_box.pack_start(lbl, False, False, 0)

                    # Gtk.ColorButton
                    rgba = Gdk.RGBA()
                    rgba.parse(init_hex)
                    c_btn = Gtk.ColorButton.new_with_rgba(rgba)
                    c_btn.set_size_request(40, 26)
                    row_box.pack_start(c_btn, False, False, 0)

                    # Hex Entry
                    hex_entry = Gtk.Entry()
                    hex_entry.get_style_context().add_class("entry")
                    hex_entry.set_text(init_hex)
                    hex_entry.set_width_chars(9)
                    hex_entry.set_max_length(7)
                    row_box.pack_start(hex_entry, False, False, 0)

                    # Connect synchronization
                    c_btn.connect("color-set", self._on_color_button_set, c_key, hex_entry)
                    hex_entry.connect("changed", self._on_hex_entry_changed, c_key, c_btn)

                    self.color_widgets[c_key] = (c_btn, hex_entry)

                    c_grid.attach(row_box, col, row, 1, 1)
                    col += 1
                    if col >= 2:
                        col = 0
                        row += 1

                pal_frame.pack_start(c_grid, False, False, 4)

            main_box.pack_start(pal_frame, False, False, 0)

            # -----------------------------------------------------------------
            # 4. Live Mini-Card Preview
            # -----------------------------------------------------------------
            self.live_preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            self.live_preview_box.get_style_context().add_class("editor-frame")
            main_box.pack_start(self.live_preview_box, False, False, 0)
            self._update_live_preview()

        def _on_seed_template_changed(self, combo):
            idx = combo.get_active()
            if idx <= 0:
                return
            theme_names = sorted(self.all_themes.keys())
            if idx - 1 < len(theme_names):
                seed_tid = theme_names[idx - 1]
                seed_data = self.all_themes[seed_tid]
                seed_colors = seed_data.get("colors", {})
                for k, (c_btn, hex_entry) in self.color_widgets.items():
                    if k in seed_colors and isinstance(seed_colors[k], str) and seed_colors[k].startswith("#"):
                        val = seed_colors[k]
                        hex_entry.set_text(val)
                        rgba = Gdk.RGBA()
                        if rgba.parse(val):
                            c_btn.set_rgba(rgba)
                self._update_live_preview()

        def _on_color_button_set(self, btn, c_key, hex_entry):
            rgba = btn.get_rgba()
            r = int(rgba.red * 255)
            g = int(rgba.green * 255)
            b = int(rgba.blue * 255)
            hex_str = f"#{r:02x}{g:02x}{b:02x}"
            hex_entry.handler_block_by_func(self._on_hex_entry_changed)
            hex_entry.set_text(hex_str)
            hex_entry.handler_unblock_by_func(self._on_hex_entry_changed)
            self._update_live_preview()

        def _on_hex_entry_changed(self, hex_entry, c_key, c_btn):
            txt = hex_entry.get_text().strip()
            if len(txt) == 7 and txt.startswith("#"):
                rgba = Gdk.RGBA()
                if rgba.parse(txt):
                    c_btn.set_rgba(rgba)
                    self._update_live_preview()

        def _on_meta_changed(self, widget):
            self._update_live_preview()

        def _get_current_colors(self):
            res = {}
            for k, (c_btn, hex_entry) in self.color_widgets.items():
                val = hex_entry.get_text().strip()
                if not val.startswith("#") or len(val) != 7:
                    val = "#cba6f7"
                res[k] = val
            return res

        def _update_live_preview(self):
            for child in self.live_preview_box.get_children():
                self.live_preview_box.remove(child)

            c = self._get_current_colors()
            name = self.entry_name.get_text().strip() or "Custom Theme"
            icon = self.entry_icon.get_text().strip() or "🎨"
            desc = self.entry_desc.get_text().strip() or "Theme Description"
            is_dark = (self.combo_type.get_active() == 0)

            title_lbl = Gtk.Label()
            title_lbl.set_markup("<span size='11500' weight='bold'>👁️ Real-Time Live Preview</span>")
            title_lbl.set_xalign(0)
            self.live_preview_box.pack_start(title_lbl, False, False, 0)

            # Simulated Card
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.get_style_context().add_class("card-box")

            h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            t_lbl = Gtk.Label()
            t_lbl.set_markup(f"<span size='11000' weight='bold'>{icon}  {name}</span>")
            t_lbl.set_xalign(0)
            h_box.pack_start(t_lbl, True, True, 0)

            badge = Gtk.Label(label="🌙 Dark" if is_dark else "☀️ Light")
            badge.get_style_context().add_class("badge-dark" if is_dark else "badge-light")
            h_box.pack_start(badge, False, False, 0)
            card.pack_start(h_box, False, False, 0)

            d_lbl = Gtk.Label()
            d_lbl.set_markup(f"<span size='9500'>{desc}</span>")
            d_lbl.set_xalign(0)
            card.pack_start(d_lbl, False, False, 0)

            swatches = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            for k in ["base", "surface0", "accent", "blue", "green", "yellow", "red", "mauve", "teal"]:
                hex_v = c.get(k, "#cba6f7")
                chip = self.parent_win._create_color_chip(hex_v, tooltip=k, size=20)
                swatches.pack_start(chip, False, False, 0)
            card.pack_start(swatches, False, False, 0)

            self.live_preview_box.pack_start(card, False, False, 0)
            self.live_preview_box.show_all()

        def _save_theme(self, apply_now=True):
            raw_id = self.entry_id.get_text().strip()
            name = self.entry_name.get_text().strip()
            icon = self.entry_icon.get_text().strip() or "🎨"
            is_dark = (self.combo_type.get_active() == 0)
            ttype = "dark" if is_dark else "light"
            desc = self.entry_desc.get_text().strip()

            # Sanitize Theme ID
            cleaned_id = re.sub(r"[^\w-]", "-", raw_id.lower()).strip("-")
            if not cleaned_id:
                cleaned_id = re.sub(r"[^\w-]", "-", name.lower()).strip("-") or "custom-theme"

            colors = self._get_current_colors()

            # Add extended Catppuccin compatibility keys
            for k in ["maroon", "flamingo", "rosewater", "sky", "sapphire"]:
                if k not in colors:
                    colors[k] = colors.get("peach" if k == "maroon" else ("pink" if k in ("flamingo", "rosewater") else "blue"), "#89b4fa")

            # Border & Shadow calculated variables
            acc = colors.get("accent", "#cba6f7")
            blu = colors.get("blue", "#89b4fa")
            s0 = colors.get("surface0", "#313244")
            cr = colors.get("crust", "#11111b")
            r, g, b = hex_to_rgb_tuple(cr)

            colors["active_border_1"] = f"rgba({acc.lstrip('#')}ee)"
            colors["active_border_2"] = f"rgba({blu.lstrip('#')}ee)"
            colors["inactive_border"] = f"rgba({s0.lstrip('#')}aa)"
            colors["shadow_hex"] = f"0xee{cr.lstrip('#')}"
            colors["shadow_css"] = f"rgba({r}, {g}, {b}, 0.6)"

            # Terminal palette colors
            terminal = {
                "color0": colors.get("surface1", "#45475a"),
                "color8": colors.get("surface2", "#585b70"),
                "color1": colors.get("red", "#f38ba8"),
                "color9": colors.get("red", "#f38ba8"),
                "color2": colors.get("green", "#a6e3a1"),
                "color10": colors.get("green", "#a6e3a1"),
                "color3": colors.get("yellow", "#f9e2af"),
                "color11": colors.get("yellow", "#f9e2af"),
                "color4": colors.get("blue", "#89b4fa"),
                "color12": colors.get("blue", "#89b4fa"),
                "color5": colors.get("mauve", colors.get("accent", "#cba6f7")),
                "color13": colors.get("mauve", colors.get("accent", "#cba6f7")),
                "color6": colors.get("teal", "#94e2d5"),
                "color14": colors.get("teal", "#94e2d5"),
                "color7": colors.get("subtext1", "#bac2de"),
                "color15": colors.get("subtext0", "#a6adc8"),
            }

            theme_json_data = {
                "id": cleaned_id,
                "name": name or cleaned_id.title(),
                "icon": icon,
                "type": ttype,
                "desc": desc or f"Custom {ttype} palette: {name}",
                "starship_palette": cleaned_id.replace("-", "_"),
                "colors": colors,
                "terminal": terminal,
            }

            THEME_DIR.mkdir(parents=True, exist_ok=True)
            target_files = [THEME_DIR / f"{cleaned_id}.json"]
            if FALLBACK_THEME_DIR.exists() and FALLBACK_THEME_DIR != THEME_DIR:
                target_files.append(FALLBACK_THEME_DIR / f"{cleaned_id}.json")

            for tf in target_files:
                try:
                    with open(tf, "w", encoding="utf-8") as f:
                        json.dump(theme_json_data, f, indent=2)
                except Exception as e:
                    print(f"Error saving theme to {tf}: {e}", file=sys.stderr)

            print(f"{C_GREEN}✓ Successfully saved theme:{C_RESET} {name} ({cleaned_id})")
            self.destroy()

            # Refresh and apply
            self.parent_win._reload_themes(select_id=cleaned_id, apply_immediately=apply_now)

    win = ThemeManagerWindow(themes, current_id)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


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

THEME_PAIRS = {
    "catppuccin-mocha": "catppuccin-latte",
    "catppuccin-macchiato": "catppuccin-latte",
    "catppuccin-frappe": "catppuccin-latte",
    "catppuccin-latte": "catppuccin-mocha",
    "everforest": "everforest-light",
    "everforest-light": "everforest",
    "gruvbox-dark": "gruvbox-light",
    "gruvbox-light": "gruvbox-dark",
    "nord": "nord-light",
    "nord-light": "nord",
    "one-dark": "one-light",
    "one-light": "one-dark",
    "rose-pine": "rose-pine-dawn",
    "rose-pine-dawn": "rose-pine",
    "tokyo-night": "tokyo-night-day",
    "tokyo-night-day": "tokyo-night",
    "solarized-dark": "solarized-light",
    "solarized-light": "solarized-dark",
    "cyberpunk": "catppuccin-latte",
    "dracula": "catppuccin-latte",
}

def set_mode(mode="toggle", themes=None, notify=True):
    """
    Switch or toggle between dark and light themes systemwide.
    mode can be 'dark', 'light', or 'toggle'.
    """
    if themes is None:
        themes = load_themes()

    current_id = get_current_theme(themes)
    current_data = themes.get(current_id, {})
    current_type = current_data.get("type", "dark").lower()

    if mode == "toggle":
        target_type = "light" if current_type == "dark" else "dark"
    elif mode in ["dark", "light"]:
        target_type = mode
    else:
        print(f"{C_RED}Invalid mode: {mode}. Use 'dark', 'light', or 'toggle'.{C_RESET}", file=sys.stderr)
        return False

    if current_type == target_type:
        # Re-apply current theme to ensure all systemwide settings are synchronized
        apply_theme(current_id, themes=themes, notify=notify)
        return True

    # Find paired theme if available
    paired_id = THEME_PAIRS.get(current_id)
    if paired_id and paired_id in themes and themes[paired_id].get("type", "").lower() == target_type:
        target_id = paired_id
    else:
        # Fallback to first theme matching target_type or defaults
        matching = [tid for tid, tdata in themes.items() if tdata.get("type", "").lower() == target_type]
        if matching:
            target_id = matching[0]
        else:
            target_id = "catppuccin-latte" if target_type == "light" else "catppuccin-mocha"

    return apply_theme(target_id, themes=themes, notify=notify)

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
    parser.add_argument("-g", "--gui", "--manager", action="store_true", help="Open modern GTK3 Theme Manager Window")
    parser.add_argument("-n", "--next", action="store_true", help="Cycle to the next theme")
    parser.add_argument("-p", "--prev", action="store_true", help="Cycle to the previous theme")
    parser.add_argument("-r", "--random", action="store_true", help="Apply a random theme")
    parser.add_argument("--dark", action="store_true", help="Set dark mode systemwide")
    parser.add_argument("--light", action="store_true", help="Set light mode systemwide")
    parser.add_argument("--toggle-mode", action="store_true", help="Toggle between dark and light mode systemwide")
    parser.add_argument("--mode", choices=["dark", "light", "toggle"], help="Set or toggle theme mode systemwide")
    parser.add_argument("--silent", action="store_true", help="Suppress desktop notifications")
    parser.add_argument("--git-skip", action="store_true", help="Mark theme files as skip-worktree to isolate them from git status")
    parser.add_argument("--git-unskip", action="store_true", help="Unmark theme files from skip-worktree")
    parser.add_argument("--git-sync", action="store_true", help="Sync, stage, and commit active theme changes to git")
    parser.add_argument("--check-git", action="store_true", help="Check for pending uncommitted theme changes")

    args = parser.parse_args()

    if args.git_skip:
        set_git_skip_worktree(skip=True)
        return
    elif args.git_unskip:
        set_git_skip_worktree(skip=False)
        return
    elif args.git_sync:
        sync_theme_git()
        return
    elif args.check_git:
        changes = check_pending_theme_changes()
        if changes:
            print(f"{C_YELLOW}Pending theme changes detected:{C_RESET}")
            for c in changes:
                print(f"  {c}")
            sys.exit(1)
        else:
            print(f"{C_GREEN}No pending theme changes.{C_RESET}")
            sys.exit(0)

    themes = load_themes()

    if args.list:
        list_themes(themes)
    elif args.dark or args.mode == "dark":
        set_mode("dark", themes=themes, notify=not args.silent)
    elif args.light or args.mode == "light":
        set_mode("light", themes=themes, notify=not args.silent)
    elif args.toggle_mode or args.mode == "toggle":
        set_mode("toggle", themes=themes, notify=not args.silent)
    elif args.set:
        apply_theme(args.set, themes=themes, notify=not args.silent)
    elif args.current:
        cur = get_current_theme(themes)
        name = themes.get(cur, {}).get("name", cur)
        print(f"Current theme: {name} ({cur})")
    elif args.gui:
        run_gui_theme_manager(themes)
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

