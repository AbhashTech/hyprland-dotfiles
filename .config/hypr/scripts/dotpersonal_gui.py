#!/usr/bin/env python3
"""
=============================================================================
Personal Settings & Modular Configurations Manager (Desktop GUI)
=============================================================================
A native GTK3 utility that dynamically adapts to the active system theme to:
- Inspect and manage modular, untracked personal configurations across
  Hyprland, Neovim, Shell, and Quickshell
- Create new modular configuration files from pre-defined templates
- Inspect, view, and edit personal files in your editor
- One-click export and import of personal settings backup archives (.tar.gz)
- Manage standalone private Git repository (~/.dotfiles-personal) with
  init, diff, commit/save, push, and pull actions
"""

import os
import sys
import json
import shutil
import tarfile
import subprocess
from datetime import datetime
from pathlib import Path

# Paths
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
DOTFILES_DIR = HOME / ".dotfiles"
DOTFILES_CONFIG_DIR = DOTFILES_DIR / ".config"
PERSONAL_REPO_DIR = HOME / ".dotfiles-personal"
PERSONAL_SCRIPT = DOTFILES_DIR / "scripts" / "dotfiles-personal.sh"

TEMPLATES = {
    "Hyprland Monitor Override (user/monitors.lua)": {
        "rel_path": ".config/hypr/user/monitors.lua",
        "category": "Hyprland",
        "content": """--------------------------------------------------------------------------------
-- User Personal Monitor Configuration (Untracked)
--------------------------------------------------------------------------------

hl.monitor({
    output   = "eDP-1",
    mode     = "preferred",
    position = "auto",
    scale    = 1.0,
})
"""
    },
    "Hyprland Input / Keyboard (user/input.lua)": {
        "rel_path": ".config/hypr/user/input.lua",
        "category": "Hyprland",
        "content": """--------------------------------------------------------------------------------
-- User Personal Input Configuration (Untracked)
--------------------------------------------------------------------------------

hl.config({
    input = {
        kb_layout  = "us",
        kb_variant = "",
        kb_options = "",
        sensitivity = 0,
        touchpad = {
            natural_scroll = true,
        },
    },
})
"""
    },
    "Hyprland Custom Keybinds (user/keybinds.lua)": {
        "rel_path": ".config/hypr/user/keybinds.lua",
        "category": "Hyprland",
        "content": """--------------------------------------------------------------------------------
-- User Personal Keybindings (Untracked)
--------------------------------------------------------------------------------
local mainMod = "SUPER"

-- Example custom application shortcut:
-- hl.bind(mainMod .. " + ALT + T", hl.dsp.exec_cmd("foot -e btop"))
"""
    },
    "Hyprland Window Rules (user/rules.lua)": {
        "rel_path": ".config/hypr/user/rules.lua",
        "category": "Hyprland",
        "content": """--------------------------------------------------------------------------------
-- User Personal Window Rules (Untracked)
--------------------------------------------------------------------------------

-- hl.window_rule({
--     name  = "float",
--     match = { class = "pavucontrol" },
-- })
"""
    },
    "Hyprland Autostart Apps (user/autostart.lua)": {
        "rel_path": ".config/hypr/user/autostart.lua",
        "category": "Hyprland",
        "content": """--------------------------------------------------------------------------------
-- User Personal Autostart Applications (Untracked)
--------------------------------------------------------------------------------

-- hl.exec_cmd("discord --start-minimized")
"""
    },
    "Shell Aliases (user/aliases.sh)": {
        "rel_path": ".config/shell/user/aliases.sh",
        "category": "Shell",
        "content": """# Personal Custom Shell Aliases (Untracked)
alias ll='ls -la'
alias gs='git status'
"""
    },
    "Shell Environment & Paths (user/env.sh)": {
        "rel_path": ".config/shell/user/env.sh",
        "category": "Shell",
        "content": """# Personal Custom Environment & Paths (Untracked)
export PATH="$HOME/.local/bin:$HOME/go/bin:$PATH"
"""
    },
    "Neovim Custom Plugin (personal_custom.lua)": {
        "rel_path": ".config/nvim/lua/plugins/personal_custom.lua",
        "category": "Neovim",
        "content": """-- User Personal Neovim Plugin Configuration (Untracked)
return {
  -- Add LazyVim plugin specifications here
}
"""
    }
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


def get_personal_files_list():
    """Retrieve all active personal files organized by package."""
    items = []

    # 1. Shell ~/.zshenv
    zshenv = HOME / ".zshenv"
    if zshenv.is_file():
        items.append({
            "path": zshenv,
            "rel_path": "~/.zshenv",
            "pkg": "Shell",
            "badge": "shell",
            "size": zshenv.stat().st_size,
            "mtime": datetime.fromtimestamp(zshenv.stat().st_mtime)
        })

    # 2. Neovim personal plugins
    nvim_plugins = DOTFILES_DIR / ".config" / "nvim" / "lua" / "plugins"
    if nvim_plugins.is_dir():
        for p in nvim_plugins.glob("personal_*.lua"):
            if p.is_file():
                items.append({
                    "path": p,
                    "rel_path": f".config/nvim/lua/plugins/{p.name}",
                    "pkg": "Neovim",
                    "badge": "nvim",
                    "size": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime)
                })

    nvim_custom = DOTFILES_DIR / ".config" / "nvim" / "lua" / "custom"
    if nvim_custom.is_dir():
        for p in nvim_custom.rglob("*"):
            if p.is_file() and p.name != "README.md":
                rel = p.relative_to(DOTFILES_DIR)
                items.append({
                    "path": p,
                    "rel_path": str(rel),
                    "pkg": "Neovim",
                    "badge": "nvim",
                    "size": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime)
                })

    # 3. Shell personal files
    shell_user = DOTFILES_DIR / ".config" / "shell" / "user"
    if shell_user.is_dir():
        for p in shell_user.rglob("*"):
            if p.is_file() and p.name != "README.md":
                rel = p.relative_to(DOTFILES_DIR)
                items.append({
                    "path": p,
                    "rel_path": str(rel),
                    "pkg": "Shell",
                    "badge": "shell",
                    "size": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime)
                })

    shell_dir = DOTFILES_DIR / ".config" / "shell"
    if shell_dir.is_dir():
        for p in shell_dir.glob("*.local.sh"):
            if p.is_file():
                rel = p.relative_to(DOTFILES_DIR)
                items.append({
                    "path": p,
                    "rel_path": str(rel),
                    "pkg": "Shell",
                    "badge": "shell",
                    "size": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime)
                })

    # 4. Hyprland personal modules
    hypr_user = DOTFILES_DIR / ".config" / "hypr" / "user"
    if hypr_user.is_dir():
        for p in hypr_user.rglob("*"):
            if p.is_file() and p.name != "README.md":
                rel = p.relative_to(DOTFILES_DIR)
                items.append({
                    "path": p,
                    "rel_path": str(rel),
                    "pkg": "Hyprland",
                    "badge": "hypr",
                    "size": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime)
                })

    # 5. Quickshell custom plugins
    qs_plugins = DOTFILES_DIR / ".config" / "quickshell" / "custom_plugins"
    if qs_plugins.is_dir():
        for p in qs_plugins.rglob("*"):
            if p.is_file() and p.name != "README.md" and ".git" not in p.parts and "__pycache__" not in p.parts:
                rel = p.relative_to(DOTFILES_DIR)
                items.append({
                    "path": p,
                    "rel_path": str(rel),
                    "pkg": "Quickshell",
                    "badge": "qs",
                    "size": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime)
                })

    # Sort items by package name and relative path
    items.sort(key=lambda x: (x["pkg"], x["rel_path"]))
    return items


def format_size(num_bytes):
    """Format bytes to human readable size string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}" if unit != 'B' else f"{int(num_bytes)} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def run_cmd(cmd, cwd=None):
    """Execute command safely and return (success, stdout, stderr)."""
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return (res.returncode == 0, res.stdout.strip(), res.stderr.strip())
    except Exception as e:
        return (False, "", str(e))


def open_in_editor(file_path):
    """Open file in user's default editor or graphical editor."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not editor:
        if shutil.which("code"):
            editor = "code"
        elif shutil.which("kate"):
            editor = "kate"
        elif shutil.which("gedit"):
            editor = "gedit"
        else:
            editor = "nvim"

    if editor in ["nvim", "vim", "nano", "hx"]:
        if shutil.which("foot"):
            subprocess.Popen(["foot", editor, str(file_path)])
            return
        elif shutil.which("xterm"):
            subprocess.Popen(["xterm", "-e", f"{editor} '{file_path}'"])
            return

    subprocess.Popen([editor, str(file_path)])


def launch_dotpersonal_gui():
    """Initialize and launch the GTK3 GUI application."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib, Pango

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
    blue_fg = get_contrast_color(c_blue)

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
        padding: 6px 14px;
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
    button.accent:hover {{
        opacity: 0.9;
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

    .card {{
        background-color: {c_mantle};
        border: 1px solid {c_surface0};
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
    }}

    .card:hover {{
        border-color: {c_surface1};
        background-color: {c_surface0};
    }}

    .badge {{
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 7px;
    }}

    .badge-hypr {{ background-color: {c_accent}; color: {accent_fg}; }}
    .badge-nvim {{ background-color: {c_green}; color: {green_fg}; }}
    .badge-shell {{ background-color: {c_yellow}; color: #11111b; }}
    .badge-qs {{ background-color: {c_sapphire}; color: #11111b; }}

    .status-box {{
        background-color: {c_mantle};
        border: 1px solid {c_surface0};
        border-radius: 8px;
        padding: 16px;
    }}

    .section-title {{
        font-size: 13px;
        font-weight: 700;
        color: {c_text};
        margin-bottom: 6px;
    }}

    .stat-label {{
        font-size: 11px;
        color: {c_subtext0};
    }}

    .stat-value {{
        font-size: 13px;
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

    class PersonalManagerWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Personal Settings Manager")
            self.set_default_size(880, 620)
            self.set_position(Gtk.WindowPosition.CENTER)

            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_box)

            # Top Header
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header.get_style_context().add_class("top-header")

            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_title = Gtk.Label(label="🧩 Personal Settings Manager", xalign=0)
            lbl_title.get_style_context().add_class("window-title")
            self.lbl_sub = Gtk.Label(label=f"Active System Theme: {theme_name.title()} ({theme_type})", xalign=0)
            self.lbl_sub.get_style_context().add_class("window-subtitle")
            title_box.pack_start(lbl_title, False, False, 0)
            title_box.pack_start(self.lbl_sub, False, False, 0)
            header.pack_start(title_box, True, True, 0)

            btn_refresh = Gtk.Button(label="󰑐  Refresh")
            btn_refresh.connect("clicked", lambda b: self.refresh_all())
            header.pack_end(btn_refresh, False, False, 0)

            btn_new = Gtk.Button(label="󰐕  New Config")
            btn_new.get_style_context().add_class("accent")
            btn_new.connect("clicked", lambda b: self.show_new_config_dialog())
            header.pack_end(btn_new, False, False, 0)

            main_box.pack_start(header, False, False, 0)

            # Notebook Tabs
            self.notebook = Gtk.Notebook()
            main_box.pack_start(self.notebook, True, True, 0)

            # Tab 1: Personal Files
            self.tab_files = self.build_files_tab()
            self.notebook.append_page(self.tab_files, Gtk.Label(label="📂 Active Files"))

            # Tab 2: Backup & Migration
            self.tab_backup = self.build_backup_tab()
            self.notebook.append_page(self.tab_backup, Gtk.Label(label="📦 Backup & Export"))

            # Tab 3: Version Control (Private Repo)
            self.tab_vcs = self.build_vcs_tab()
            self.notebook.append_page(self.tab_vcs, Gtk.Label(label="🌿 Version Control"))

            self.refresh_all()

        def build_files_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            container.set_margin_top(14)
            container.set_margin_bottom(14)
            container.set_margin_start(16)
            container.set_margin_end(16)

            # Filter row
            filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            self.search_entry = Gtk.Entry()
            self.search_entry.set_placeholder_text("🔍 Filter personal files...")
            self.search_entry.connect("changed", lambda e: self.populate_files_list())
            filter_row.pack_start(self.search_entry, True, True, 0)

            self.pkg_filter = Gtk.ComboBoxText()
            self.pkg_filter.append("all", "All Packages")
            self.pkg_filter.append("Hyprland", "Hyprland")
            self.pkg_filter.append("Neovim", "Neovim")
            self.pkg_filter.append("Shell", "Shell")
            self.pkg_filter.append("Quickshell", "Quickshell")
            self.pkg_filter.set_active(0)
            self.pkg_filter.connect("changed", lambda c: self.populate_files_list())
            filter_row.pack_start(self.pkg_filter, False, False, 0)

            container.pack_start(filter_row, False, False, 0)

            # Listbox Scroller
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.files_listbox = Gtk.ListBox()
            self.files_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            scroller.add(self.files_listbox)
            container.pack_start(scroller, True, True, 0)

            # Bottom Status Summary
            self.lbl_files_count = Gtk.Label(label="", xalign=0)
            self.lbl_files_count.get_style_context().add_class("stat-label")
            container.pack_start(self.lbl_files_count, False, False, 0)

            return container

        def populate_files_list(self):
            for child in self.files_listbox.get_children():
                self.files_listbox.remove(child)

            query = self.search_entry.get_text().strip().lower()
            selected_pkg = self.pkg_filter.get_active_id()

            files = get_personal_files_list()
            visible_count = 0

            for f in files:
                if selected_pkg and selected_pkg != "all" and f["pkg"] != selected_pkg:
                    continue
                if query and query not in f["rel_path"].lower() and query not in f["pkg"].lower():
                    continue

                visible_count += 1
                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                card.get_style_context().add_class("card")

                # Package badge
                badge = Gtk.Label(label=f["pkg"])
                badge.get_style_context().add_class("badge")
                badge.get_style_context().add_class(f"badge-{f['badge']}")
                card.pack_start(badge, False, False, 0)

                # Path info
                path_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                lbl_name = Gtk.Label(label=f["rel_path"], xalign=0)
                lbl_name.get_style_context().add_class("stat-value")
                lbl_name.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

                mtime_str = f["mtime"].strftime("%Y-%m-%d %H:%M")
                lbl_meta = Gtk.Label(label=f"Size: {format_size(f['size'])}  •  Modified: {mtime_str}", xalign=0)
                lbl_meta.get_style_context().add_class("stat-label")

                path_box.pack_start(lbl_name, False, False, 0)
                path_box.pack_start(lbl_meta, False, False, 0)
                card.pack_start(path_box, True, True, 0)

                # Action buttons
                btn_view = Gtk.Button(label="👁️ View")
                btn_view.connect("clicked", lambda b, target=f["path"], title=f["rel_path"]: self.view_file_content(target, title))
                card.pack_end(btn_view, False, False, 0)

                btn_edit = Gtk.Button(label="✏️ Edit")
                btn_edit.connect("clicked", lambda b, target=f["path"]: open_in_editor(target))
                card.pack_end(btn_edit, False, False, 0)

                self.files_listbox.add(card)

            self.files_listbox.show_all()
            self.lbl_files_count.set_text(f"Showing {visible_count} of {len(files)} active personal files (all ignored by Git).")

        def build_backup_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            container.set_margin_top(18)
            container.set_margin_bottom(18)
            container.set_margin_start(20)
            container.set_margin_end(20)

            # Export Card
            card_export = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card_export.get_style_context().add_class("status-box")

            lbl_exp_title = Gtk.Label(label="📦 Export Personal Configurations", xalign=0)
            lbl_exp_title.get_style_context().add_class("section-title")
            card_export.pack_start(lbl_exp_title, False, False, 0)

            lbl_exp_desc = Gtk.Label(
                label="Create a compressed .tar.gz backup archive of all your personal settings across Hyprland, Neovim, Shell, and Quickshell. Ideal for transferring to a second computer or storing safe backups.",
                xalign=0
            )
            lbl_exp_desc.set_line_wrap(True)
            lbl_exp_desc.get_style_context().add_class("stat-label")
            card_export.pack_start(lbl_exp_desc, False, False, 0)

            exp_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            btn_export = Gtk.Button(label="📤  Export Archive (.tar.gz)...")
            btn_export.get_style_context().add_class("accent")
            btn_export.connect("clicked", lambda b: self.export_backup_dialog())
            exp_actions.pack_start(btn_export, False, False, 0)
            card_export.pack_start(exp_actions, False, False, 0)

            container.pack_start(card_export, False, False, 0)

            # Import Card
            card_import = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card_import.get_style_context().add_class("status-box")

            lbl_imp_title = Gtk.Label(label="📥 Import & Restore Configurations", xalign=0)
            lbl_imp_title.get_style_context().add_class("section-title")
            card_import.pack_start(lbl_imp_title, False, False, 0)

            lbl_imp_desc = Gtk.Label(
                label="Restore personal configuration files from an existing .tar.gz archive or folder. Safe non-destructive import preserves existing files by default.",
                xalign=0
            )
            lbl_imp_desc.set_line_wrap(True)
            lbl_imp_desc.get_style_context().add_class("stat-label")
            card_import.pack_start(lbl_imp_desc, False, False, 0)

            imp_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            btn_import = Gtk.Button(label="📥  Import from Archive...")
            btn_import.connect("clicked", lambda b: self.import_backup_dialog())
            imp_actions.pack_start(btn_import, False, False, 0)
            card_import.pack_start(imp_actions, False, False, 0)

            container.pack_start(card_import, False, False, 0)

            return container

        def build_vcs_tab(self):
            container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            container.set_margin_top(18)
            container.set_margin_bottom(18)
            container.set_margin_start(20)
            container.set_margin_end(20)

            # VCS Status Box
            self.vcs_status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.vcs_status_box.get_style_context().add_class("status-box")

            lbl_vcs_title = Gtk.Label(label="🌿 Private Git Repository (~/.dotfiles-personal)", xalign=0)
            lbl_vcs_title.get_style_context().add_class("section-title")
            self.vcs_status_box.pack_start(lbl_vcs_title, False, False, 0)

            self.lbl_vcs_desc = Gtk.Label(xalign=0)
            self.lbl_vcs_desc.set_line_wrap(True)
            self.lbl_vcs_desc.get_style_context().add_class("stat-label")
            self.vcs_status_box.pack_start(self.lbl_vcs_desc, False, False, 0)

            # VCS Action Buttons
            self.vcs_actions_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            self.vcs_status_box.pack_start(self.vcs_actions_row, False, False, 0)

            container.pack_start(self.vcs_status_box, False, False, 0)

            # Diff Viewer Box
            lbl_diff_title = Gtk.Label(label="📝 Live Repository Diff & Status Log", xalign=0)
            lbl_diff_title.get_style_context().add_class("section-title")
            container.pack_start(lbl_diff_title, False, False, 0)

            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.diff_textview = Gtk.TextView()
            self.diff_textview.set_editable(False)
            self.diff_textview.set_cursor_visible(False)
            self.diff_textview.set_monospace(True)
            scroller.add(self.diff_textview)
            container.pack_start(scroller, True, True, 0)

            return container

        def refresh_vcs_status(self):
            for child in self.vcs_actions_row.get_children():
                self.vcs_actions_row.remove(child)

            is_initialized = (PERSONAL_REPO_DIR / ".git").is_dir()

            if not is_initialized:
                self.lbl_vcs_desc.set_text(
                    "Personal Git repository is not initialized. Initializing will create a private Git repository at ~/.dotfiles-personal to track, version control, and push your personal files safely to a private remote."
                )
                btn_init = Gtk.Button(label="🚀  Initialize Personal Repo")
                btn_init.get_style_context().add_class("accent")
                btn_init.connect("clicked", lambda b: self.vcs_init_repo())
                self.vcs_actions_row.pack_start(btn_init, False, False, 0)

                buf = self.diff_textview.get_buffer()
                buf.set_text("Personal Git repository not initialized.\nClick 'Initialize Personal Repo' above to set up version control.")
            else:
                ok, branch, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=PERSONAL_REPO_DIR)
                ok, log_str, _ = run_cmd(["git", "log", "-1", "--pretty=format:%h - %s (%cr)"], cwd=PERSONAL_REPO_DIR)
                ok, diff_stat, _ = run_cmd(["bash", str(PERSONAL_SCRIPT), "diff"], cwd=DOTFILES_DIR)

                self.lbl_vcs_desc.set_text(
                    f"Repository: ~/.dotfiles-personal  •  Branch: {branch or 'main'}\nLatest Commit: {log_str or 'None'}"
                )

                btn_save = Gtk.Button(label="💾  Commit / Save Changes...")
                btn_save.get_style_context().add_class("success")
                btn_save.connect("clicked", lambda b: self.vcs_save_dialog())
                self.vcs_actions_row.pack_start(btn_save, False, False, 0)

                btn_diff = Gtk.Button(label="🔍  Refresh Diff")
                btn_diff.connect("clicked", lambda b: self.refresh_diff())
                self.vcs_actions_row.pack_start(btn_diff, False, False, 0)

                btn_push = Gtk.Button(label="📤  Push to Remote")
                btn_push.connect("clicked", lambda b: self.vcs_push())
                self.vcs_actions_row.pack_start(btn_push, False, False, 0)

                btn_pull = Gtk.Button(label="📥  Pull Updates")
                btn_pull.connect("clicked", lambda b: self.vcs_pull())
                self.vcs_actions_row.pack_start(btn_pull, False, False, 0)

                self.refresh_diff()

            self.vcs_status_box.show_all()

        def refresh_diff(self):
            ok, diff_out, _ = run_cmd(["bash", str(PERSONAL_SCRIPT), "diff"], cwd=DOTFILES_DIR)
            buf = self.diff_textview.get_buffer()
            buf.set_text(diff_out if diff_out.strip() else "Clean: No unsaved personal configuration changes.")

        def vcs_init_repo(self):
            ok, out, err = run_cmd(["bash", str(PERSONAL_SCRIPT), "init-repo"], cwd=DOTFILES_DIR)
            self.show_info_dialog("Initialize Repository", out if ok else f"Error:\n{err}")
            self.refresh_all()

        def vcs_save_dialog(self):
            dialog = Gtk.Dialog(title="Save / Commit Personal Configs", flags=0)
            dialog.set_default_size(440, 160)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(10)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl = Gtk.Label(label="Enter commit message for this personal update:", xalign=0)
            box.pack_start(lbl, False, False, 0)

            entry = Gtk.Entry()
            entry.set_text(f"feat: update personal settings ({datetime.now().strftime('%Y-%m-%d')})")
            box.pack_start(entry, False, False, 0)

            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            btn_ok = dialog.add_button("Commit & Save", Gtk.ResponseType.OK)
            btn_ok.get_style_context().add_class("success")

            dialog.show_all()
            res = dialog.run()
            msg = entry.get_text().strip()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and msg:
                ok, out, err = run_cmd(["bash", str(PERSONAL_SCRIPT), "save", msg], cwd=DOTFILES_DIR)
                self.show_info_dialog("Save Result", out if ok else f"Error:\n{err}")
                self.refresh_all()

        def vcs_push(self):
            ok, out, err = run_cmd(["bash", str(PERSONAL_SCRIPT), "push"], cwd=DOTFILES_DIR)
            self.show_info_dialog("Push Result", out if ok else f"Error pushing to remote:\n{err}\n\nMake sure remote is configured with:\ncd ~/.dotfiles-personal && git remote add origin <url>")
            self.refresh_all()

        def vcs_pull(self):
            ok, out, err = run_cmd(["bash", str(PERSONAL_SCRIPT), "pull"], cwd=DOTFILES_DIR)
            self.show_info_dialog("Pull Result", out if ok else f"Error pulling from remote:\n{err}")
            self.refresh_all()

        def view_file_content(self, file_path, title):
            dialog = Gtk.Dialog(title=f"Viewing: {title}", flags=0)
            dialog.set_default_size(680, 520)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(8)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(12)
            box.set_margin_end(12)

            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            tv = Gtk.TextView()
            tv.set_editable(False)
            tv.set_monospace(True)
            try:
                tv.get_buffer().set_text(Path(file_path).read_text(encoding="utf-8"))
            except Exception as e:
                tv.get_buffer().set_text(f"Could not read file: {e}")
            scroller.add(tv)
            box.pack_start(scroller, True, True, 0)

            dialog.add_button("Close", Gtk.ResponseType.CLOSE)
            btn_edit = dialog.add_button("Open in Editor", Gtk.ResponseType.YES)
            btn_edit.get_style_context().add_class("accent")

            dialog.show_all()
            res = dialog.run()
            dialog.destroy()

            if res == Gtk.ResponseType.YES:
                open_in_editor(file_path)

        def show_new_config_dialog(self):
            dialog = Gtk.Dialog(title="Create New Personal Configuration", flags=0)
            dialog.set_default_size(520, 260)
            dialog.set_position(Gtk.WindowPosition.CENTER)

            box = dialog.get_content_area()
            box.set_spacing(10)
            box.set_margin_top(14)
            box.set_margin_bottom(14)
            box.set_margin_start(16)
            box.set_margin_end(16)

            lbl = Gtk.Label(label="Select configuration module type:", xalign=0)
            box.pack_start(lbl, False, False, 0)

            combo = Gtk.ComboBoxText()
            template_keys = list(TEMPLATES.keys())
            for key in template_keys:
                combo.append_text(key)
            combo.set_active(0)
            box.pack_start(combo, False, False, 0)

            lbl_note = Gtk.Label(
                label="Personal files are placed in untracked user directories (~/.config/hypr/user/, ~/.config/shell/user/, etc.) and automatically ignored by Git.",
                xalign=0
            )
            lbl_note.set_line_wrap(True)
            lbl_note.get_style_context().add_class("stat-label")
            box.pack_start(lbl_note, False, False, 0)

            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            btn_create = dialog.add_button("Create & Edit", Gtk.ResponseType.OK)
            btn_create.get_style_context().add_class("accent")

            dialog.show_all()
            res = dialog.run()
            chosen = combo.get_active_text()
            dialog.destroy()

            if res == Gtk.ResponseType.OK and chosen in TEMPLATES:
                tdata = TEMPLATES[chosen]
                target = DOTFILES_DIR / tdata["rel_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_text(tdata["content"], encoding="utf-8")
                open_in_editor(target)
                self.refresh_all()

        def export_backup_dialog(self):
            dialog = Gtk.FileChooserDialog(
                title="Save Personal Settings Archive",
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
            dialog.set_current_name(f"dotfiles-personal-{datetime.now().strftime('%Y%m%d')}.tar.gz")
            dialog.set_do_overwrite_confirmation(True)

            res = dialog.run()
            if res == Gtk.ResponseType.OK:
                dest = dialog.get_filename()
                dialog.destroy()
                ok, out, err = run_cmd(["bash", str(PERSONAL_SCRIPT), "export", dest], cwd=DOTFILES_DIR)
                self.show_info_dialog("Export Complete", out if ok else f"Export Error:\n{err}")
            else:
                dialog.destroy()

        def import_backup_dialog(self):
            dialog = Gtk.FileChooserDialog(
                title="Select Personal Settings Archive to Import",
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            filter_tar = Gtk.FileFilter()
            filter_tar.set_name("Tar Archives (*.tar.gz, *.tgz)")
            filter_tar.add_pattern("*.tar.gz")
            filter_tar.add_pattern("*.tgz")
            dialog.add_filter(filter_tar)

            res = dialog.run()
            if res == Gtk.ResponseType.OK:
                src = dialog.get_filename()
                dialog.destroy()
                ok, out, err = run_cmd(["bash", str(PERSONAL_SCRIPT), "import", src], cwd=DOTFILES_DIR)
                self.show_info_dialog("Import Complete", out if ok else f"Import Error:\n{err}")
                self.refresh_all()
            else:
                dialog.destroy()

        def show_info_dialog(self, title, message):
            dialog = Gtk.MessageDialog(
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            dialog.format_secondary_text(message)
            dialog.run()
            dialog.destroy()

        def refresh_all(self):
            self.populate_files_list()
            self.refresh_vcs_status()

    win = PersonalManagerWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    launch_dotpersonal_gui()
