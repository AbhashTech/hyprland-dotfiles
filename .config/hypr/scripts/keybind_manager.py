#!/usr/bin/env python3
"""
=============================================================================
Hyprland Keybindings Manager (Desktop GUI & CLI)
=============================================================================
A modern GTK3 utility that dynamically adapts to the active system theme to:
- Inspect and manage default Hyprland keybindings
- Override or disable/enable default keybindings non-destructively
- Add, edit, delete, and enable/disable custom user keybindings
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


def normalize_key_str(raw_key):
    """Normalize Lua key combo to standard SUPER + Key format."""
    k = raw_key.replace('mainMod .. "', 'SUPER').replace("mainMod .. '", 'SUPER')
    k = k.replace('"', '').replace("'", "").replace(' .. ', ' ')
    k = k.replace("mainMod", "SUPER").strip()
    k = re.sub(r"\s+", " ", k)
    return k


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
            # Extract content inside outer parentheses
            m = re.match(r"^hl\.bind\((.+)\)(?:.*)$", sline)
            if m:
                inner = m.group(1).strip()
                args = split_lua_args(inner)
                if len(args) >= 2:
                    raw_key = args[0]
                    action = args[1]
                    flags = args[2] if len(args) > 2 else ""

                    norm_key = normalize_key_str(raw_key)
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


def load_user_keybinds_state():
    """
    Parse ~/.config/hypr/user/keybinds.lua.
    Returns:
      disabled_defaults: set of normalized keys that are disabled (hl.unbind)
      overrides: dict mapping normalized default key -> custom key & action
      custom_binds: list of custom keybind dicts
    """
    disabled_defaults = set()
    overrides = {}
    custom_binds = []

    if not USER_KEYBINDS_PATH.is_file():
        return disabled_defaults, overrides, custom_binds

    lines = USER_KEYBINDS_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines:
        sline = line.strip()
        if not sline:
            continue

        # 1. Unbinds for disabled defaults or overrides
        if sline.startswith("hl.unbind("):
            m = re.search(r'hl\.unbind\(\s*["\']([^"\']+)["\']\s*\)', sline)
            if m:
                unbound_key = normalize_key_str(m.group(1))
                if "@disabled" in sline:
                    disabled_defaults.add(unbound_key)

        # 2. Overrides or Custom binds
        is_disabled_custom = sline.startswith("-- [DISABLED]")
        code_part = sline.replace("-- [DISABLED]", "").strip()

        if code_part.startswith("hl.bind("):
            # Split off trailing comment
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

                    norm_k = normalize_key_str(raw_k)

                    ov_match = re.search(r'@override:([^|]+)', trailing)
                    desc_match = re.search(r'@desc:([^|]+)', trailing)
                    cat_match = re.search(r'@category:([^|]+)', trailing)

                    desc = desc_match.group(1).strip() if desc_match else ""
                    cat = cat_match.group(1).strip() if cat_match else "Personal Shortcuts"

                    if ov_match:
                        orig_key = normalize_key_str(ov_match.group(1).strip())
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
                            "enabled": not is_disabled_custom,
                            "type": "custom"
                        })

    return disabled_defaults, overrides, custom_binds


def save_user_keybinds_state(disabled_defaults, overrides, custom_binds):
    """Serialize user keybinding configurations cleanly to ~/.config/hypr/user/keybinds.lua."""
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
            new_k = ov["new_key"]
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
            k = cb["key"]
            act = cb["action"]
            flg = f", {cb['flags']}" if cb.get("flags") else ""
            desc = cb.get("desc", "Custom Action")
            cat = cb.get("category", "Personal Shortcuts")
            prefix = "" if cb.get("enabled", True) else "-- [DISABLED] "
            lines.append(f'{prefix}hl.bind("{k}", {act}{flg}) -- @custom | @desc:{desc} | @category:{cat}')
        lines.append("")

    content = "\n".join(lines) + "\n"
    USER_KEYBINDS_PATH.write_text(content, encoding="utf-8")

    # Apply live to Hyprland
    run_cmd(["hyprctl", "reload"])


def launch_keybind_manager_gui():
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

    css_provider = Gtk.CssProvider()
    css_data = f"""
    * {{
        font-family: system-ui, -apple-system, 'Inter', 'Roboto', 'Noto Sans', 'JetBrainsMono Nerd Font', sans-serif;
    }}

    window {{
        background-color: {c_base};
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

    notebook tab:checked {{
        color: {c_accent};
        border-bottom: 2px solid {c_accent};
    }}

    button {{
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        padding: 5px 12px;
        border: 1px solid {c_surface1};
        background-color: {c_mantle};
        color: {c_text};
        transition: all 120ms ease-in-out;
    }}

    button:hover {{
        background-color: {c_surface0};
        border-color: {c_surface2};
    }}

    button.accent {{
        background-color: {c_accent};
        color: {accent_fg};
        border: 1px solid {c_accent};
    }}

    button.success {{
        background-color: {c_green};
        color: {green_fg};
        border: 1px solid {c_green};
    }}

    button.danger {{
        background-color: {c_red};
        color: {red_fg};
        border: 1px solid {c_red};
    }}

    entry, textview {{
        background-color: {c_mantle};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 6px;
        padding: 6px 10px;
    }}

    entry:focus, textview:focus {{
        border-color: {c_accent};
    }}

    .key-badge {{
        background-color: {c_surface0};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 6px;
        font-family: 'JetBrainsMono Nerd Font', monospace;
        font-size: 12px;
        font-weight: 700;
        padding: 3px 8px;
    }}

    .key-badge-overridden {{
        background-color: {c_yellow};
        color: #11111b;
        border: 1px solid {c_yellow};
    }}

    .key-badge-disabled {{
        background-color: {c_surface0};
        color: {c_subtext0};
        text-decoration: line-through;
        opacity: 0.6;
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

    .status-tag {{
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
    }}

    .status-default {{ background-color: {c_surface1}; color: {c_text}; }}
    .status-active {{ background-color: {c_green}; color: {green_fg}; }}
    .status-override {{ background-color: {c_yellow}; color: #11111b; }}
    .status-disabled {{ background-color: {c_red}; color: {red_fg}; }}

    .stat-label {{
        font-size: 11px;
        color: {c_subtext0};
    }}

    .stat-value {{
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
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    class KeybindsManagerWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Hyprland Keybindings Manager")
            self.set_default_size(920, 640)
            self.set_position(Gtk.WindowPosition.CENTER)

            self.default_binds = parse_default_keybinds()
            self.disabled_defaults, self.overrides, self.custom_binds = load_user_keybinds_state()

            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_box)

            # Top Header
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header.get_style_context().add_class("top-header")

            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_title = Gtk.Label(label="⌨️ Hyprland Keybindings Manager", xalign=0)
            lbl_title.get_style_context().add_class("window-title")
            self.lbl_sub = Gtk.Label(
                label=f"Active System Theme: {theme_name.title()}  •  {len(self.default_binds)} Defaults  •  {len(self.custom_binds)} Custom",
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

            # Tab 1: Default Keybinds
            self.tab_defaults = self.build_defaults_tab()
            self.notebook.append_page(self.tab_defaults, Gtk.Label(label="󰌌  Default Keybinds"))

            # Tab 2: Custom Keybinds
            self.tab_custom = self.build_custom_tab()
            self.notebook.append_page(self.tab_custom, Gtk.Label(label="⚡  Custom Keybinds"))

            # Tab 3: Generated Lua Config
            self.tab_lua = self.build_lua_tab()
            self.notebook.append_page(self.tab_lua, Gtk.Label(label="📄  user/keybinds.lua"))

            self.refresh_all()

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

            self.defaults_listbox.show_all()
            self.lbl_def_summary.set_text(
                f"Showing {visible_count} of {len(self.default_binds)} default keybinds  •  "
                f"{len(self.disabled_defaults)} disabled  •  {len(self.overrides)} overridden"
            )

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
                empty_card.get_style_context().add_class("card")
                lbl_empty = Gtk.Label(
                    label="No custom keybindings configured yet.\nClick '+ Add Custom Keybind' above to create personal shortcuts!",
                    xalign=0.5
                )
                lbl_empty.set_justify(Gtk.Justification.CENTER)
                empty_card.pack_start(lbl_empty, False, False, 16)
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

        def show_override_dialog(self, default_item):
            orig_key = default_item["key"]
            curr_override = self.overrides.get(orig_key, {})

            dialog = Gtk.Dialog(title=f"Override Default: {default_item['desc']}", flags=0)
            dialog.set_default_size(520, 280)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(10)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_orig = Gtk.Label(label=f"Original Shortcut: <b>{orig_key}</b>", xalign=0, use_markup=True)
            box.pack_start(lbl_orig, False, False, 0)

            lbl_key = Gtk.Label(label="New Keyboard Shortcut (e.g. SUPER + T, SUPER + SHIFT + K):", xalign=0)
            box.pack_start(lbl_key, False, False, 0)
            entry_key = Gtk.Entry()
            entry_key.set_text(curr_override.get("new_key") or orig_key)
            box.pack_start(entry_key, False, False, 0)

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
            new_key = normalize_key_str(entry_key.get_text().strip())
            new_act = entry_act.get_text().strip()
            new_desc = entry_desc.get_text().strip()
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
            dialog.set_default_size(540, 320)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(8)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_k = Gtk.Label(label="Keyboard Shortcut (e.g. SUPER + ALT + T):", xalign=0)
            box.pack_start(lbl_k, False, False, 0)
            entry_k = Gtk.Entry()
            entry_k.set_text("SUPER + ")
            box.pack_start(entry_k, False, False, 0)

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
            k = normalize_key_str(entry_k.get_text().strip())
            cmd = entry_act.get_text().strip()
            desc = entry_desc.get_text().strip() or "Custom Shortcut"
            preset = combo_preset.get_active_id()
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
            dialog.set_default_size(540, 280)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(8)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl_k = Gtk.Label(label="Keyboard Shortcut:", xalign=0)
            box.pack_start(lbl_k, False, False, 0)
            entry_k = Gtk.Entry()
            entry_k.set_text(cb["key"])
            box.pack_start(entry_k, False, False, 0)

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
            k = normalize_key_str(entry_k.get_text().strip())
            act = entry_act.get_text().strip()
            desc = entry_desc.get_text().strip()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and k and act:
                self.custom_binds[idx]["key"] = k
                self.custom_binds[idx]["action"] = act
                self.custom_binds[idx]["desc"] = desc or "Custom Shortcut"
                self.save_and_sync()

        def save_and_sync(self):
            save_user_keybinds_state(self.disabled_defaults, self.overrides, self.custom_binds)
            self.refresh_all()

        def open_in_editor(self):
            editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nvim"
            if shutil.which("foot") and editor in ["nvim", "vim", "nano"]:
                subprocess.Popen(["foot", editor, str(USER_KEYBINDS_PATH)])
            else:
                subprocess.Popen([editor, str(USER_KEYBINDS_PATH)])

        def reload_hyprland(self):
            run_cmd(["hyprctl", "reload"])
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
            self.refresh_lua_view()
            self.lbl_sub.set_text(
                f"Active System Theme: {theme_name.title()}  •  {len(self.default_binds)} Defaults  •  {len(self.custom_binds)} Custom"
            )

    win = KeybindsManagerWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    launch_keybind_manager_gui()
