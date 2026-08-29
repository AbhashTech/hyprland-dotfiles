#!/usr/bin/env python3
"""
=============================================================================
Application Launcher & Menu Shortcut Creator (Desktop Entry Manager)
=============================================================================
A modern utility to create, manage, test, and edit application shortcuts (.desktop
files) for Wayland/Hyprland app launchers (Fuzzel, Wofi, Rofi, App Menus).

Features:
- Full GTK3 GUI with Catppuccin Mocha styling, high contrast, readable typography & live preview
- Shortcut Manager tab to browse, edit, test-launch, and delete existing shortcuts
- CLI interactive wizard and direct command-line arguments for automated scripts
- Instant integration with XDG desktop menus and notifications
"""

import os
import sys
import re
import stat
import shutil
import argparse
import subprocess
from pathlib import Path

# Standard user applications directory
APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"

# Standard Freedesktop Categories
COMMON_CATEGORIES = [
    ("Utility", "🔧 Utility"),
    ("Development", "💻 Development"),
    ("System", "⚙️ System"),
    ("Office", "📝 Office"),
    ("Network", "🌐 Network"),
    ("AudioVideo", "🎬 Audio & Video"),
    ("Graphics", "🎨 Graphics"),
    ("Game", "🎮 Game"),
    ("Settings", "🛠️ Settings"),
    ("TerminalEmulator", "📟 Terminal"),
    ("Education", "📚 Education"),
    ("Science", "🔬 Science"),
]

# High-contrast, crystal-clear Catppuccin Mocha CSS Stylesheet for GTK3
CATPPUCCIN_CSS = b"""
* {
    font-family: system-ui, -apple-system, 'Inter', 'Roboto', 'Noto Sans', 'Cantarell', 'Ubuntu', sans-serif;
}

window {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-size: 13px;
}

headerbar {
    background-color: #11111b;
    background-image: none;
    border-bottom: 1px solid #313244;
    color: #cdd6f4;
    padding: 6px 12px;
}

headerbar label.title {
    font-weight: bold;
    font-size: 15px;
    color: #cba6f7;
}

headerbar label.subtitle {
    color: #bac2de;
    font-size: 12px;
}

notebook stack {
    background-color: #1e1e2e;
}

notebook tab {
    padding: 10px 22px;
    background-color: #181825;
    background-image: none;
    color: #a6adc8;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: bold;
    font-size: 13px;
}

notebook tab label {
    color: #a6adc8;
    font-weight: bold;
    font-size: 13px;
}

notebook tab:checked {
    color: #cba6f7;
    border-bottom: 2px solid #cba6f7;
    background-color: #1e1e2e;
}

notebook tab:checked label {
    color: #cba6f7;
}

label {
    color: #cdd6f4;
    font-size: 13px;
}

label.section-header {
    font-weight: bold;
    color: #89b4fa;
    font-size: 14px;
    margin-top: 8px;
}

label.field-label {
    color: #bac2de;
    font-size: 13px;
    font-weight: 600;
}

entry {
    background-color: #181825;
    background-image: none;
    box-shadow: none;
    color: #ffffff;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    caret-color: #cba6f7;
}

entry:focus {
    background-color: #11111b;
    border-color: #cba6f7;
    box-shadow: 0 0 0 1px #cba6f7;
    color: #ffffff;
}

entry placeholder,
entry.placeholder {
    color: #a6adc8;
    font-style: italic;
    font-size: 12px;
}

entry.error {
    border-color: #f38ba8;
    background-color: #2a1b24;
}

button {
    background-color: #313244;
    background-image: none;
    box-shadow: none;
    text-shadow: none;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 8px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 13px;
}

button label {
    color: #cdd6f4;
    font-weight: 600;
    font-size: 13px;
}

button:hover {
    background-color: #45475a;
    background-image: none;
    box-shadow: none;
    border-color: #89b4fa;
    color: #ffffff;
}

button:hover label {
    color: #ffffff;
}

button:active {
    background-color: #585b70;
    background-image: none;
}

button.suggested-action {
    background-color: #89b4fa;
    background-image: none;
    box-shadow: none;
    color: #11111b;
    border: 1px solid #74c7ec;
}

button.suggested-action label {
    color: #11111b;
    font-weight: bold;
    font-size: 13px;
}

button.suggested-action:hover {
    background-color: #b4befe;
    background-image: none;
    color: #11111b;
}

button.suggested-action:hover label {
    color: #11111b;
}

button.secondary-action {
    background-color: #cba6f7;
    background-image: none;
    box-shadow: none;
    color: #11111b;
    border: 1px solid #b4befe;
}

button.secondary-action label {
    color: #11111b;
    font-weight: bold;
    font-size: 13px;
}

button.secondary-action:hover {
    background-color: #f5c2e7;
    background-image: none;
    color: #11111b;
}

button.secondary-action:hover label {
    color: #11111b;
}

button.destructive-action {
    background-color: #f38ba8;
    background-image: none;
    box-shadow: none;
    color: #11111b;
    border: 1px solid #eba0ac;
}

button.destructive-action label {
    color: #11111b;
    font-weight: bold;
    font-size: 13px;
}

button.destructive-action:hover {
    background-color: #eba0ac;
    background-image: none;
    color: #11111b;
}

button.destructive-action:hover label {
    color: #11111b;
}

checkbutton {
    font-size: 13px;
}

checkbutton label {
    color: #cdd6f4;
    font-size: 13px;
    font-weight: 500;
}

checkbutton check {
    background-color: #313244;
    background-image: none;
    border: 1px solid #585b70;
    border-radius: 4px;
    min-width: 16px;
    min-height: 16px;
    color: #cba6f7;
}

checkbutton check:checked {
    background-color: #89b4fa;
    background-image: none;
    border-color: #89b4fa;
    color: #11111b;
}

frame > border {
    border: 1px solid #313244;
    border-radius: 8px;
}

scrolledwindow {
    border: 1px solid #313244;
    border-radius: 8px;
    background-color: #181825;
}

list {
    background-color: #181825;
    color: #cdd6f4;
}

row {
    padding: 10px 14px;
    border-bottom: 1px solid #313244;
}

row:hover {
    background-color: #313244;
}

row:selected {
    background-color: #45475a;
    color: #ffffff;
}

textview.preview {
    font-family: 'JetBrainsMono Nerd Font', 'Fira Code', monospace;
    font-size: 12px;
    background-color: #11111b;
    color: #a6e3a1;
}

infobar {
    border-radius: 8px;
    margin-bottom: 8px;
}
"""


def sanitize_filename(name: str) -> str:
    """Generate a clean, filesystem-safe filename for .desktop file."""
    if not name:
        return "custom-app.desktop"
    cleaned = re.sub(r"[^\w\s-]", "", name.lower())
    cleaned = re.sub(r"[\s_]+", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = "custom-app"
    if not cleaned.endswith(".desktop"):
        cleaned += ".desktop"
    return cleaned


def generate_desktop_content(
    name: str,
    exec_cmd: str,
    comment: str = "",
    icon: str = "application-x-executable",
    categories: list = None,
    terminal: bool = False,
    generic_name: str = "",
    working_dir: str = "",
    startup_notify: bool = True,
    startup_wm_class: str = "",
    keywords: list = None,
) -> str:
    """Generate standards-compliant .desktop file content."""
    lines = [
        "[Desktop Entry]",
        "Version=1.0",
        "Type=Application",
        f"Name={name.strip()}",
    ]

    if generic_name.strip():
        lines.append(f"GenericName={generic_name.strip()}")

    if comment.strip():
        lines.append(f"Comment={comment.strip()}")

    lines.append(f"Exec={exec_cmd.strip()}")

    if working_dir.strip():
        lines.append(f"Path={os.path.expanduser(working_dir.strip())}")

    icon_val = icon.strip() if icon.strip() else "application-x-executable"
    lines.append(f"Icon={icon_val}")

    lines.append(f"Terminal={'true' if terminal else 'false'}")

    if categories:
        cat_str = ";".join([c.strip() for c in categories if c.strip()])
        if cat_str and not cat_str.endswith(";"):
            cat_str += ";"
        lines.append(f"Categories={cat_str}")

    if keywords:
        kw_str = ";".join([k.strip() for k in keywords if k.strip()])
        if kw_str and not kw_str.endswith(";"):
            kw_str += ";"
        lines.append(f"Keywords={kw_str}")

    if startup_wm_class.strip():
        lines.append(f"StartupWMClass={startup_wm_class.strip()}")

    lines.append(f"StartupNotify={'true' if startup_notify else 'false'}")
    lines.append("")
    return "\n".join(lines)


def save_desktop_file(filepath: Path, content: str) -> tuple[bool, str]:
    """Save content to desktop file and set executable permissions."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        # Make file executable
        filepath.chmod(filepath.stat().st_mode | stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)

        # Update desktop database if available
        if shutil.which("update-desktop-database"):
            subprocess.run(
                ["update-desktop-database", str(filepath.parent)],
                capture_output=True,
                check=False,
            )

        return True, f"Successfully created shortcut at {filepath}"
    except Exception as e:
        return False, f"Failed to write desktop file: {e}"


def delete_desktop_file(filepath: Path) -> tuple[bool, str]:
    """Delete desktop file and update desktop database."""
    try:
        if filepath.exists():
            filepath.unlink()
            if shutil.which("update-desktop-database"):
                subprocess.run(
                    ["update-desktop-database", str(filepath.parent)],
                    capture_output=True,
                    check=False,
                )
            return True, f"Shortcut {filepath.name} removed."
        return False, f"File {filepath} does not exist."
    except Exception as e:
        return False, f"Failed to delete shortcut: {e}"


def send_notification(title: str, message: str, icon: str = "preferences-desktop-keyboard-shortcuts"):
    """Send desktop notification using notify-send."""
    if shutil.which("notify-send"):
        try:
            subprocess.Popen([
                "notify-send",
                "-a", "Shortcut Creator",
                "-i", icon,
                "-t", "4000",
                title,
                message,
            ])
        except Exception:
            pass


def list_custom_shortcuts() -> list[dict]:
    """List all custom .desktop files in ~/.local/share/applications."""
    if not APPLICATIONS_DIR.exists():
        return []

    entries = []
    for f in sorted(APPLICATIONS_DIR.glob("*.desktop")):
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                data = {}
                for line in fh:
                    line = line.strip()
                    if "=" in line and not line.startswith("#") and not line.startswith("["):
                        k, v = line.split("=", 1)
                        data[k.strip()] = v.strip()

                entries.append({
                    "path": f,
                    "filename": f.name,
                    "name": data.get("Name", f.stem),
                    "exec": data.get("Exec", ""),
                    "icon": data.get("Icon", "application-x-executable"),
                    "comment": data.get("Comment", ""),
                    "generic_name": data.get("GenericName", ""),
                    "categories": data.get("Categories", "").split(";") if data.get("Categories") else [],
                    "terminal": data.get("Terminal", "false").lower() == "true",
                    "path_dir": data.get("Path", ""),
                    "startup_wm_class": data.get("StartupWMClass", ""),
                    "startup_notify": data.get("StartupNotify", "true").lower() == "true",
                })
        except Exception:
            continue

    return entries


# =============================================================================
# GTK 3 GUI Implementation
# =============================================================================

def run_gtk_gui():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf

    # Apply Catppuccin Dark Theme CSS safely
    screen = Gdk.Screen.get_default()
    if screen:
        try:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(CATPPUCCIN_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except Exception as e:
            print(f"Warning: Custom CSS error: {e}", file=sys.stderr)

    class ShortcutCreatorApp(Gtk.Window):
        def __init__(self):
            super().__init__(title="Application Shortcut Creator")
            self.set_default_size(840, 690)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.set_wmclass("app-shortcut-creator", "app-shortcut-creator")
            self.set_role("app-shortcut-creator")

            # Header Bar
            header = Gtk.HeaderBar()
            header.set_show_close_button(True)
            header.set_title("App Shortcut Creator")
            header.set_subtitle("Create & Manage App Menu Launchers")
            self.set_titlebar(header)

            # Header icon
            header_icon = Gtk.Image.new_from_icon_name("preferences-desktop-keyboard-shortcuts", Gtk.IconSize.LARGE_TOOLBAR)
            header.pack_start(header_icon)

            # Main container
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_box)

            # In-App Info / Status Notification Bar
            self.infobar = Gtk.InfoBar()
            self.infobar.set_revealed(False)
            self.infobar_label = Gtk.Label()
            self.infobar.get_content_area().pack_start(self.infobar_label, True, True, 4)
            self.infobar.add_button("✕", Gtk.ResponseType.CLOSE)
            self.infobar.connect("response", lambda *args: self.infobar.set_revealed(False))
            main_box.pack_start(self.infobar, False, False, 4)

            # Notebook Tabs (Create / Edit & Manage)
            self.notebook = Gtk.Notebook()
            main_box.pack_start(self.notebook, True, True, 0)

            # Tab 1: Create & Edit Form
            self._init_create_tab()

            # Tab 2: Manage Existing Shortcuts
            self._init_manage_tab()

            # Initial preview render
            self._update_preview()

        def _show_msg(self, text: str, msg_type=Gtk.MessageType.INFO):
            self.infobar.set_message_type(msg_type)
            self.infobar_label.set_markup(f"<b>{text}</b>")
            self.infobar.set_revealed(True)
            # Auto-hide after 5s
            GLib.timeout_add_seconds(5, lambda: self.infobar.set_revealed(False))

        def _init_create_tab(self):
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            content_box.set_margin_start(22)
            content_box.set_margin_end(22)
            content_box.set_margin_top(16)
            content_box.set_margin_bottom(20)
            scroll.add(content_box)

            # --- Section 1: Basic Information ---
            sec1_label = Gtk.Label(xalign=0)
            sec1_label.set_markup("<b>󰘔 BASIC INFORMATION</b>")
            sec1_label.get_style_context().add_class("section-header")
            content_box.pack_start(sec1_label, False, False, 0)

            grid1 = Gtk.Grid()
            grid1.set_column_spacing(14)
            grid1.set_row_spacing(10)
            content_box.pack_start(grid1, False, False, 0)

            # Name Field (Required)
            name_lbl = Gtk.Label(label="App Name *:", xalign=0)
            name_lbl.get_style_context().add_class("field-label")
            self.entry_name = Gtk.Entry()
            self.entry_name.set_placeholder_text("e.g. Obsidian, Custom Backup, DBeaver")
            self.entry_name.set_hexpand(True)
            self.entry_name.connect("changed", self._on_name_changed)
            grid1.attach(name_lbl, 0, 0, 1, 1)
            grid1.attach(self.entry_name, 1, 0, 2, 1)

            # Generic Name
            gen_lbl = Gtk.Label(label="Generic Name:", xalign=0)
            gen_lbl.get_style_context().add_class("field-label")
            self.entry_generic = Gtk.Entry()
            self.entry_generic.set_placeholder_text("e.g. Note-taking, Database Tool, Text Editor")
            self.entry_generic.connect("changed", lambda *args: self._update_preview())
            grid1.attach(gen_lbl, 0, 1, 1, 1)
            grid1.attach(self.entry_generic, 1, 1, 2, 1)

            # Comment / Description
            desc_lbl = Gtk.Label(label="Description:", xalign=0)
            desc_lbl.get_style_context().add_class("field-label")
            self.entry_desc = Gtk.Entry()
            self.entry_desc.set_placeholder_text("e.g. Knowledge management and markdown notes")
            self.entry_desc.connect("changed", lambda *args: self._update_preview())
            grid1.attach(desc_lbl, 0, 2, 1, 1)
            grid1.attach(self.entry_desc, 1, 2, 2, 1)

            # --- Section 2: Command & Execution ---
            sec2_label = Gtk.Label(xalign=0)
            sec2_label.set_markup("<b>󰆍 COMMAND & EXECUTION</b>")
            sec2_label.get_style_context().add_class("section-header")
            content_box.pack_start(sec2_label, False, False, 4)

            grid2 = Gtk.Grid()
            grid2.set_column_spacing(14)
            grid2.set_row_spacing(10)
            content_box.pack_start(grid2, False, False, 0)

            # Exec Field (Required)
            exec_lbl = Gtk.Label(label="Command / Exec *:", xalign=0)
            exec_lbl.get_style_context().add_class("field-label")
            self.entry_exec = Gtk.Entry()
            self.entry_exec.set_placeholder_text("e.g. /opt/app/start.sh, /usr/bin/my-binary --flag")
            self.entry_exec.set_hexpand(True)
            self.entry_exec.connect("changed", lambda *args: self._update_preview())

            btn_browse_exec = Gtk.Button(label="📁 Browse...")
            btn_browse_exec.connect("clicked", self._on_browse_exec)

            btn_test_exec = Gtk.Button(label="▶ Test Run")
            btn_test_exec.get_style_context().add_class("secondary-action")
            btn_test_exec.connect("clicked", self._on_test_run)

            exec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            exec_box.pack_start(self.entry_exec, True, True, 0)
            exec_box.pack_start(btn_browse_exec, False, False, 0)
            exec_box.pack_start(btn_test_exec, False, False, 0)

            grid2.attach(exec_lbl, 0, 0, 1, 1)
            grid2.attach(exec_box, 1, 0, 2, 1)

            # Working Directory (Path)
            cwd_lbl = Gtk.Label(label="Working Directory:", xalign=0)
            cwd_lbl.get_style_context().add_class("field-label")
            self.entry_cwd = Gtk.Entry()
            self.entry_cwd.set_placeholder_text("Optional startup working directory (e.g. ~/Projects)")
            self.entry_cwd.connect("changed", lambda *args: self._update_preview())

            btn_browse_cwd = Gtk.Button(label="📁 Browse...")
            btn_browse_cwd.connect("clicked", self._on_browse_cwd)

            cwd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            cwd_box.pack_start(self.entry_cwd, True, True, 0)
            cwd_box.pack_start(btn_browse_cwd, False, False, 0)

            grid2.attach(cwd_lbl, 0, 1, 1, 1)
            grid2.attach(cwd_box, 1, 1, 2, 1)

            # --- Section 3: Icon & Visuals ---
            sec3_label = Gtk.Label(xalign=0)
            sec3_label.set_markup("<b>󰀻 ICON & APPEARANCE</b>")
            sec3_label.get_style_context().add_class("section-header")
            content_box.pack_start(sec3_label, False, False, 4)

            grid3 = Gtk.Grid()
            grid3.set_column_spacing(14)
            grid3.set_row_spacing(10)
            content_box.pack_start(grid3, False, False, 0)

            icon_lbl = Gtk.Label(label="Icon Name or Path:", xalign=0)
            icon_lbl.get_style_context().add_class("field-label")
            self.entry_icon = Gtk.Entry()
            self.entry_icon.set_text("application-x-executable")
            self.entry_icon.set_placeholder_text("e.g. code, terminal, /path/to/icon.png")
            self.entry_icon.set_hexpand(True)
            self.entry_icon.connect("changed", self._on_icon_changed)

            btn_browse_icon = Gtk.Button(label="🖼️ Browse...")
            btn_browse_icon.connect("clicked", self._on_browse_icon)

            self.icon_preview = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)
            self.icon_preview.set_pixel_size(36)

            icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            icon_box.pack_start(self.icon_preview, False, False, 0)
            icon_box.pack_start(self.entry_icon, True, True, 0)
            icon_box.pack_start(btn_browse_icon, False, False, 0)

            grid3.attach(icon_lbl, 0, 0, 1, 1)
            grid3.attach(icon_box, 1, 0, 2, 1)

            # --- Section 4: Categories & Desktop Options ---
            sec4_label = Gtk.Label(xalign=0)
            sec4_label.set_markup("<b>🏷️ CATEGORIES & LAUNCH OPTIONS</b>")
            sec4_label.get_style_context().add_class("section-header")
            content_box.pack_start(sec4_label, False, False, 4)

            # Category Checkboxes Grid
            cat_frame = Gtk.Frame()
            cat_box = Gtk.Grid()
            cat_box.set_column_spacing(20)
            cat_box.set_row_spacing(8)
            cat_box.set_margin_start(14)
            cat_box.set_margin_end(14)
            cat_box.set_margin_top(10)
            cat_box.set_margin_bottom(10)
            cat_frame.add(cat_box)
            content_box.pack_start(cat_frame, False, False, 0)

            self.cat_checks = {}
            for idx, (cat_key, cat_label) in enumerate(COMMON_CATEGORIES):
                col = idx % 4
                row = idx // 4
                chk = Gtk.CheckButton(label=cat_label)
                if cat_key == "Utility":
                    chk.set_active(True)
                chk.connect("toggled", lambda *args: self._update_preview())
                self.cat_checks[cat_key] = chk
                cat_box.attach(chk, col, row, 1, 1)

            # Toggles: Run in terminal & Startup Notify
            toggles_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=28)
            toggles_box.set_margin_top(4)
            self.chk_terminal = Gtk.CheckButton(label="📟 Run in Terminal (CLI / TUI application)")
            self.chk_terminal.connect("toggled", lambda *args: self._update_preview())

            self.chk_startup_notify = Gtk.CheckButton(label="🔔 Enable Startup Notification")
            self.chk_startup_notify.set_active(True)
            self.chk_startup_notify.connect("toggled", lambda *args: self._update_preview())

            toggles_box.pack_start(self.chk_terminal, False, False, 0)
            toggles_box.pack_start(self.chk_startup_notify, False, False, 0)
            content_box.pack_start(toggles_box, False, False, 0)

            # Optional WM Class & Filename
            grid_adv = Gtk.Grid()
            grid_adv.set_column_spacing(14)
            grid_adv.set_row_spacing(8)
            content_box.pack_start(grid_adv, False, False, 0)

            fn_lbl = Gtk.Label(label="Shortcut Filename:", xalign=0)
            fn_lbl.get_style_context().add_class("field-label")
            self.entry_filename = Gtk.Entry()
            self.entry_filename.set_placeholder_text("custom-app.desktop")
            self.entry_filename.set_hexpand(True)
            self.entry_filename.connect("changed", lambda *args: self._update_preview())
            grid_adv.attach(fn_lbl, 0, 0, 1, 1)
            grid_adv.attach(self.entry_filename, 1, 0, 1, 1)

            wm_lbl = Gtk.Label(label="Startup WM Class:", xalign=0)
            wm_lbl.get_style_context().add_class("field-label")
            self.entry_wmclass = Gtk.Entry()
            self.entry_wmclass.set_placeholder_text("Optional window class matching rule")
            self.entry_wmclass.set_hexpand(True)
            self.entry_wmclass.connect("changed", lambda *args: self._update_preview())
            grid_adv.attach(wm_lbl, 0, 1, 1, 1)
            grid_adv.attach(self.entry_wmclass, 1, 1, 1, 1)

            # --- Section 5: Live .desktop File Preview ---
            expander = Gtk.Expander(label="👁️ Live .desktop File Preview")
            expander.set_expanded(False)

            preview_scroll = Gtk.ScrolledWindow()
            preview_scroll.set_min_content_height(140)
            self.preview_text = Gtk.TextView()
            self.preview_text.set_editable(False)
            self.preview_text.get_style_context().add_class("preview")
            self.preview_text.set_left_margin(12)
            self.preview_text.set_right_margin(12)
            self.preview_text.set_top_margin(10)
            self.preview_text.set_bottom_margin(10)
            preview_scroll.add(self.preview_text)
            expander.add(preview_scroll)
            content_box.pack_start(expander, False, False, 0)

            # Action Buttons Bar
            actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            actions_box.set_margin_top(12)

            btn_reset = Gtk.Button(label="🧹 Reset Form")
            btn_reset.connect("clicked", lambda *args: self._reset_form())

            self.btn_save = Gtk.Button(label="➕ Create Shortcut in App Menu")
            self.btn_save.get_style_context().add_class("suggested-action")
            self.btn_save.connect("clicked", self._on_save_clicked)

            actions_box.pack_end(self.btn_save, False, False, 0)
            actions_box.pack_end(btn_reset, False, False, 0)
            content_box.pack_start(actions_box, False, False, 0)

            # Add Tab to Notebook
            tab_label = Gtk.Label(label="➕ Create Shortcut")
            self.notebook.append_page(scroll, tab_label)

        def _init_manage_tab(self):
            manage_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            manage_box.set_margin_start(18)
            manage_box.set_margin_end(18)
            manage_box.set_margin_top(14)
            manage_box.set_margin_bottom(18)

            # Search bar
            search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            self.search_entry = Gtk.SearchEntry()
            self.search_entry.set_placeholder_text("Search custom shortcuts...")
            self.search_entry.connect("search-changed", self._on_search_changed)
            search_box.pack_start(self.search_entry, True, True, 0)

            btn_refresh = Gtk.Button(label="🔄 Refresh")
            btn_refresh.connect("clicked", lambda *args: self._load_shortcuts_list())
            search_box.pack_start(btn_refresh, False, False, 0)
            manage_box.pack_start(search_box, False, False, 0)

            # Listbox Scrolled Window
            list_scroll = Gtk.ScrolledWindow()
            list_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.listbox = Gtk.ListBox()
            self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
            self.listbox.connect("row-selected", self._on_row_selected)
            list_scroll.add(self.listbox)
            manage_box.pack_start(list_scroll, True, True, 0)

            # Bottom Action Bar for Selected Item
            self.manage_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            self.manage_actions.set_sensitive(False)

            self.btn_edit = Gtk.Button(label="✏️ Edit")
            self.btn_edit.connect("clicked", self._on_edit_selected)

            self.btn_launch = Gtk.Button(label="▶️ Launch")
            self.btn_launch.get_style_context().add_class("secondary-action")
            self.btn_launch.connect("clicked", self._on_launch_selected)

            self.btn_open_folder = Gtk.Button(label="📂 Reveal in Dolphin")
            self.btn_open_folder.connect("clicked", self._on_reveal_selected)

            self.btn_delete = Gtk.Button(label="🗑️ Delete")
            self.btn_delete.get_style_context().add_class("destructive-action")
            self.btn_delete.connect("clicked", self._on_delete_selected)

            self.manage_actions.pack_start(self.btn_edit, False, False, 0)
            self.manage_actions.pack_start(self.btn_launch, False, False, 0)
            self.manage_actions.pack_start(self.btn_open_folder, False, False, 0)
            self.manage_actions.pack_end(self.btn_delete, False, False, 0)
            manage_box.pack_start(self.manage_actions, False, False, 0)

            tab_label = Gtk.Label(label="📋 Manage Shortcuts")
            self.notebook.append_page(manage_box, tab_label)

            self.notebook.connect("switch-page", self._on_tab_switched)

        def _on_tab_switched(self, notebook, page, page_num):
            if page_num == 1:
                self._load_shortcuts_list()

        def _on_name_changed(self, entry):
            name = entry.get_text()
            if name:
                entry.get_style_context().remove_class("error")
                # Auto update filename if not customized
                slug = sanitize_filename(name)
                self.entry_filename.set_text(slug)
            self._update_preview()

        def _on_icon_changed(self, entry):
            icon_str = entry.get_text().strip()
            self._update_icon_preview(icon_str)
            self._update_preview()

        def _update_icon_preview(self, icon_str):
            if not icon_str:
                self.icon_preview.set_from_icon_name("application-x-executable", Gtk.IconSize.DND)
                return

            if os.path.isabs(icon_str) and os.path.exists(icon_str):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_str, 36, 36, True)
                    self.icon_preview.set_from_pixbuf(pixbuf)
                    return
                except Exception:
                    pass

            theme = Gtk.IconTheme.get_default()
            if theme.has_icon(icon_str):
                self.icon_preview.set_from_icon_name(icon_str, Gtk.IconSize.DND)
            else:
                self.icon_preview.set_from_icon_name("application-x-executable", Gtk.IconSize.DND)

        def _on_browse_exec(self, button):
            dialog = Gtk.FileChooserDialog(
                title="Select Executable / Script",
                parent=self,
                action=Gtk.FileChooserAction.OPEN,
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            )
            dialog.set_current_folder(str(Path.home()))

            filter_all = Gtk.FileFilter()
            filter_all.set_name("Executable Files & Scripts")
            filter_all.add_pattern("*.sh")
            filter_all.add_pattern("*.py")
            filter_all.add_pattern("*.AppImage")
            filter_all.add_pattern("*.bin")
            filter_all.add_pattern("*.jar")
            filter_all.add_mime_type("application/x-executable")
            filter_all.add_mime_type("application/x-shellscript")
            dialog.add_filter(filter_all)

            filter_any = Gtk.FileFilter()
            filter_any.set_name("All Files")
            filter_any.add_pattern("*")
            dialog.add_filter(filter_any)

            if dialog.run() == Gtk.ResponseType.OK:
                path = dialog.get_filename()
                self.entry_exec.set_text(path)
                # Auto-set name if empty
                if not self.entry_name.get_text():
                    base = Path(path).stem.replace("_", " ").replace("-", " ").title()
                    self.entry_name.set_text(base)
            dialog.destroy()

        def _on_browse_cwd(self, button):
            dialog = Gtk.FileChooserDialog(
                title="Select Working Directory",
                parent=self,
                action=Gtk.FileChooserAction.SELECT_FOLDER,
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            )
            dialog.set_current_folder(str(Path.home()))
            if dialog.run() == Gtk.ResponseType.OK:
                self.entry_cwd.set_text(dialog.get_filename())
            dialog.destroy()

        def _on_browse_icon(self, button):
            dialog = Gtk.FileChooserDialog(
                title="Select Application Icon",
                parent=self,
                action=Gtk.FileChooserAction.OPEN,
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            )
            dialog.set_current_folder("/usr/share/icons")

            filter_img = Gtk.FileFilter()
            filter_img.set_name("Image Files (*.png, *.svg, *.ico)")
            filter_img.add_pattern("*.png")
            filter_img.add_pattern("*.svg")
            filter_img.add_pattern("*.ico")
            filter_img.add_pattern("*.xpm")
            dialog.add_filter(filter_img)

            if dialog.run() == Gtk.ResponseType.OK:
                self.entry_icon.set_text(dialog.get_filename())
            dialog.destroy()

        def _get_active_categories(self):
            return [cat for cat, chk in self.cat_checks.items() if chk.get_active()]

        def _get_current_desktop_content(self):
            name = self.entry_name.get_text().strip() or "Unnamed App"
            exec_cmd = self.entry_exec.get_text().strip() or "/usr/bin/true"
            generic = self.entry_generic.get_text().strip()
            desc = self.entry_desc.get_text().strip()
            icon = self.entry_icon.get_text().strip() or "application-x-executable"
            categories = self._get_active_categories()
            terminal = self.chk_terminal.get_active()
            cwd = self.entry_cwd.get_text().strip()
            wm_class = self.entry_wmclass.get_text().strip()
            startup_notify = self.chk_startup_notify.get_active()

            return generate_desktop_content(
                name=name,
                exec_cmd=exec_cmd,
                comment=desc,
                icon=icon,
                categories=categories,
                terminal=terminal,
                generic_name=generic,
                working_dir=cwd,
                startup_notify=startup_notify,
                startup_wm_class=wm_class,
            )

        def _update_preview(self):
            content = self._get_current_desktop_content()
            buf = self.preview_text.get_buffer()
            buf.set_text(content)

        def _reset_form(self):
            self.entry_name.set_text("")
            self.entry_generic.set_text("")
            self.entry_desc.set_text("")
            self.entry_exec.set_text("")
            self.entry_cwd.set_text("")
            self.entry_icon.set_text("application-x-executable")
            self.entry_filename.set_text("")
            self.entry_wmclass.set_text("")
            self.chk_terminal.set_active(False)
            self.chk_startup_notify.set_active(True)
            for cat, chk in self.cat_checks.items():
                chk.set_active(cat == "Utility")
            self.btn_save.set_label("➕ Create Shortcut in App Menu")
            self._update_preview()

        def _on_test_run(self, button):
            exec_cmd = self.entry_exec.get_text().strip()
            if not exec_cmd:
                self._show_msg("Please enter a command to test run.", Gtk.MessageType.WARNING)
                return

            cwd = self.entry_cwd.get_text().strip()
            working_dir = os.path.expanduser(cwd) if cwd else str(Path.home())

            try:
                if self.chk_terminal.get_active():
                    # Launch inside kitty
                    term_cmd = ["kitty", "--hold", "sh", "-c", exec_cmd]
                    subprocess.Popen(term_cmd, cwd=working_dir)
                else:
                    subprocess.Popen(exec_cmd, shell=True, cwd=working_dir)
                self._show_msg(f"Launched test command: {exec_cmd}", Gtk.MessageType.INFO)
            except Exception as e:
                self._show_msg(f"Failed to launch command: {e}", Gtk.MessageType.ERROR)

        def _on_save_clicked(self, button):
            name = self.entry_name.get_text().strip()
            exec_cmd = self.entry_exec.get_text().strip()

            if not name:
                self.entry_name.get_style_context().add_class("error")
                self._show_msg("App Name is required!", Gtk.MessageType.ERROR)
                self.entry_name.grab_focus()
                return

            if not exec_cmd:
                self.entry_exec.get_style_context().add_class("error")
                self._show_msg("Command / Exec path is required!", Gtk.MessageType.ERROR)
                self.entry_exec.grab_focus()
                return

            filename = self.entry_filename.get_text().strip()
            if not filename:
                filename = sanitize_filename(name)

            if not filename.endswith(".desktop"):
                filename += ".desktop"

            filepath = APPLICATIONS_DIR / filename
            content = self._get_current_desktop_content()

            success, msg = save_desktop_file(filepath, content)
            if success:
                self._show_msg(f"✅ Shortcut '{name}' saved to App Menu ({filename})!", Gtk.MessageType.INFO)
                send_notification("Shortcut Added", f"'{name}' is now available in your App Menu (Fuzzel/Wofi)!", self.entry_icon.get_text().strip())
                self._load_shortcuts_list()
            else:
                self._show_msg(f"❌ Error: {msg}", Gtk.MessageType.ERROR)

        def _load_shortcuts_list(self):
            # Clear listbox
            for child in self.listbox.get_children():
                self.listbox.remove(child)

            query = self.search_entry.get_text().strip().lower()
            shortcuts = list_custom_shortcuts()

            for item in shortcuts:
                if query:
                    match_str = f"{item['name']} {item['exec']} {item['filename']} {item['comment']}".lower()
                    if query not in match_str:
                        continue

                row = Gtk.ListBoxRow()
                row.item_data = item

                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
                row_box.set_margin_start(12)
                row_box.set_margin_end(12)
                row_box.set_margin_top(10)
                row_box.set_margin_bottom(10)

                # Icon
                icon_img = Gtk.Image()
                icon_str = item["icon"]
                if os.path.isabs(icon_str) and os.path.exists(icon_str):
                    try:
                        pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon_str, 32, 32, True)
                        icon_img.set_from_pixbuf(pb)
                    except Exception:
                        icon_img.set_from_icon_name("application-x-executable", Gtk.IconSize.DND)
                else:
                    icon_img.set_from_icon_name(icon_str, Gtk.IconSize.DND)
                icon_img.set_pixel_size(32)
                row_box.pack_start(icon_img, False, False, 0)

                # Details Box
                detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                name_lbl = Gtk.Label(xalign=0)
                name_lbl.set_markup(f"<span font_weight='bold' font_size='medium' color='#cdd6f4'>{GLib.markup_escape_text(item['name'])}</span> <small color='#a6adc8'>({GLib.markup_escape_text(item['filename'])})</small>")

                exec_lbl = Gtk.Label(xalign=0)
                exec_lbl.set_markup(f"<tt><small color='#89b4fa'>{GLib.markup_escape_text(item['exec'])}</small></tt>")

                detail_box.pack_start(name_lbl, False, False, 0)
                detail_box.pack_start(exec_lbl, False, False, 0)

                if item["comment"]:
                    comment_lbl = Gtk.Label(xalign=0)
                    comment_lbl.set_markup(f"<small color='#bac2de'><i>{GLib.markup_escape_text(item['comment'])}</i></small>")
                    detail_box.pack_start(comment_lbl, False, False, 0)

                row_box.pack_start(detail_box, True, True, 0)

                # Terminal Badge
                if item["terminal"]:
                    term_badge = Gtk.Label()
                    term_badge.set_markup("<span font_weight='bold' color='#fab387'>[TUI]</span>")
                    row_box.pack_end(term_badge, False, False, 0)

                row.add(row_box)
                self.listbox.add(row)

            self.listbox.show_all()
            self.manage_actions.set_sensitive(False)

        def _on_search_changed(self, entry):
            self._load_shortcuts_list()

        def _on_row_selected(self, listbox, row):
            self.manage_actions.set_sensitive(row is not None)

        def _get_selected_item(self):
            row = self.listbox.get_selected_row()
            if row and hasattr(row, "item_data"):
                return row.item_data
            return None

        def _on_edit_selected(self, button):
            item = self._get_selected_item()
            if not item:
                return

            self.entry_name.set_text(item["name"])
            self.entry_generic.set_text(item["generic_name"])
            self.entry_desc.set_text(item["comment"])
            self.entry_exec.set_text(item["exec"])
            self.entry_cwd.set_text(item["path_dir"])
            self.entry_icon.set_text(item["icon"])
            self.entry_filename.set_text(item["filename"])
            self.entry_wmclass.set_text(item["startup_wm_class"])
            self.chk_terminal.set_active(item["terminal"])
            self.chk_startup_notify.set_active(item["startup_notify"])

            for cat, chk in self.cat_checks.items():
                chk.set_active(cat in item["categories"])

            self.btn_save.set_label("💾 Update Shortcut")
            self.notebook.set_current_page(0)
            self._update_preview()

        def _on_launch_selected(self, button):
            item = self._get_selected_item()
            if not item:
                return

            exec_cmd = item["exec"]
            cwd = os.path.expanduser(item["path_dir"]) if item["path_dir"] else str(Path.home())

            try:
                if item["terminal"]:
                    subprocess.Popen(["kitty", "--hold", "sh", "-c", exec_cmd], cwd=cwd)
                else:
                    subprocess.Popen(exec_cmd, shell=True, cwd=cwd)
                self._show_msg(f"Launched '{item['name']}'", Gtk.MessageType.INFO)
            except Exception as e:
                self._show_msg(f"Failed to launch: {e}", Gtk.MessageType.ERROR)

        def _on_reveal_selected(self, button):
            item = self._get_selected_item()
            if not item:
                return
            if shutil.which("dolphin"):
                subprocess.Popen(["dolphin", "--select", str(item["path"])])
            elif shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(item["path"].parent)])

        def _on_delete_selected(self, button):
            item = self._get_selected_item()
            if not item:
                return

            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                message_format=f"Delete shortcut '{item['name']}'?",
            )
            dialog.format_secondary_text(f"This will permanently remove '{item['filename']}' from ~/.local/share/applications.")
            res = dialog.run()
            dialog.destroy()

            if res == Gtk.ResponseType.OK:
                success, msg = delete_desktop_file(item["path"])
                if success:
                    self._show_msg(f"🗑️ Shortcut '{item['name']}' deleted.", Gtk.MessageType.INFO)
                    send_notification("Shortcut Removed", f"'{item['name']}' removed from App Menu.")
                    self._load_shortcuts_list()
                else:
                    self._show_msg(f"Error: {msg}", Gtk.MessageType.ERROR)

    app = ShortcutCreatorApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


# =============================================================================
# CLI Interactive & Flag Mode
# =============================================================================

def run_cli_interactive():
    print("\n\033[1;35m⚡ Hyprland Application Shortcut Creator\033[0m")
    print("\033[2mCreate custom launcher shortcuts in ~/.local/share/applications\033[0m\n")

    name = input("\033[1;34mApp Name\033[0m (e.g. Obsidian): ").strip()
    if not name:
        print("\033[1;31mError: Name is required.\033[0m")
        sys.exit(1)

    exec_cmd = input("\033[1;34mExecutable / Command\033[0m (e.g. /home/user/app.AppImage): ").strip()
    if not exec_cmd:
        print("\033[1;31mError: Command is required.\033[0m")
        sys.exit(1)

    generic_name = input("\033[1;34mGeneric Name / Subtitle\033[0m [optional]: ").strip()
    comment = input("\033[1;34mDescription\033[0m [optional]: ").strip()
    icon = input("\033[1;34mIcon name or path\033[0m [default: application-x-executable]: ").strip() or "application-x-executable"

    term_in = input("\033[1;34mRun in Terminal? (y/N)\033[0m: ").strip().lower()
    terminal = term_in in ["y", "yes", "true", "1"]

    cwd = input("\033[1;34mWorking Directory\033[0m [optional]: ").strip()
    categories_raw = input("\033[1;34mCategories\033[0m (e.g. Utility;Development) [default: Utility]: ").strip()
    categories = [c.strip() for c in categories_raw.split(";") if c.strip()] if categories_raw else ["Utility"]

    filename = sanitize_filename(name)
    filepath = APPLICATIONS_DIR / filename

    content = generate_desktop_content(
        name=name,
        exec_cmd=exec_cmd,
        comment=comment,
        icon=icon,
        categories=categories,
        terminal=terminal,
        generic_name=generic_name,
        working_dir=cwd,
    )

    print("\n\033[1;32mGenerated .desktop content:\033[0m")
    print(content)

    confirm = input(f"Save shortcut to {filepath}? (Y/n): ").strip().lower()
    if confirm in ["", "y", "yes"]:
        success, msg = save_desktop_file(filepath, content)
        if success:
            print(f"\033[1;32m{msg}\033[0m")
            send_notification("Shortcut Added", f"'{name}' added to App Menu!", icon)
        else:
            print(f"\033[1;31m{msg}\033[0m")
    else:
        print("Aborted.")


def run_cli_direct(args):
    filename = args.output or sanitize_filename(args.name)
    if not filename.endswith(".desktop"):
        filename += ".desktop"

    filepath = APPLICATIONS_DIR / filename
    categories = [c.strip() for c in args.categories.split(";") if c.strip()] if args.categories else ["Utility"]

    content = generate_desktop_content(
        name=args.name,
        exec_cmd=args.exec,
        comment=args.desc or "",
        icon=args.icon or "application-x-executable",
        categories=categories,
        terminal=args.terminal,
        generic_name=args.generic or "",
        working_dir=args.path or "",
        startup_wm_class=args.wmclass or "",
    )

    success, msg = save_desktop_file(filepath, content)
    if success:
        print(f"\033[1;32m✔ {msg}\033[0m")
        send_notification("Shortcut Added", f"'{args.name}' added to App Menu!", args.icon or "application-x-executable")
    else:
        print(f"\033[1;31m✖ {msg}\033[0m", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Application Launcher & Menu Shortcut Creator (.desktop Entry Manager)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--gui", action="store_true", help="Launch interactive GTK3 GUI (Default in desktop sessions)")
    parser.add_argument("--cli", "--interactive", action="store_true", help="Launch terminal interactive prompt")
    parser.add_argument("--list", "-l", action="store_true", help="List all custom user shortcuts")
    parser.add_argument("--delete", "-d", type=str, metavar="FILENAME", help="Delete a shortcut by filename or name")

    # Direct creation flags
    parser.add_argument("--name", "-n", type=str, help="Application display name")
    parser.add_argument("--exec", "-e", type=str, help="Executable command or binary path")
    parser.add_argument("--icon", "-i", type=str, help="Icon name or image path")
    parser.add_argument("--desc", "--comment", type=str, help="Description / tooltip comment")
    parser.add_argument("--generic", "-g", type=str, help="Generic name (e.g. Text Editor)")
    parser.add_argument("--categories", "-c", type=str, help="Semicolon-separated categories (e.g. Utility;Development;)")
    parser.add_argument("--path", "-p", type=str, help="Working directory path")
    parser.add_argument("--wmclass", type=str, help="StartupWMClass string")
    parser.add_argument("--terminal", "-t", action="store_true", help="Run application inside terminal")
    parser.add_argument("--output", "-o", type=str, help="Custom filename (e.g. my-app.desktop)")

    args = parser.parse_args()

    # List mode
    if args.list:
        shortcuts = list_custom_shortcuts()
        print(f"\n\033[1;35m📋 Custom Shortcuts in {APPLICATIONS_DIR}:\033[0m")
        if not shortcuts:
            print("  (No custom desktop shortcuts found)")
            return
        for s in shortcuts:
            tui_badge = " \033[1;33m[TUI]\033[0m" if s["terminal"] else ""
            print(f"  • \033[1;34m{s['name']}\033[0m{tui_badge} \033[2m({s['filename']})\033[0m")
            print(f"    Exec: \033[1;32m{s['exec']}\033[0m | Icon: {s['icon']}")
        print()
        return

    # Delete mode
    if args.delete:
        target = args.delete
        if not target.endswith(".desktop"):
            target += ".desktop"
        target_path = APPLICATIONS_DIR / target
        if not target_path.exists():
            # Search by name
            for s in list_custom_shortcuts():
                if s["name"].lower() == args.delete.lower():
                    target_path = s["path"]
                    break
        success, msg = delete_desktop_file(target_path)
        if success:
            print(f"\033[1;32m✔ {msg}\033[0m")
            send_notification("Shortcut Removed", f"'{target}' removed from App Menu.")
        else:
            print(f"\033[1;31m✖ {msg}\033[0m", file=sys.stderr)
            sys.exit(1)
        return

    # Direct creation flags
    if args.name and args.exec:
        run_cli_direct(args)
        return

    # Interactive CLI flag
    if args.cli:
        run_cli_interactive()
        return

    # Default to GUI if WAYLAND_DISPLAY or DISPLAY is set, or if --gui passed
    if args.gui or os.getenv("WAYLAND_DISPLAY") or os.getenv("DISPLAY"):
        try:
            run_gtk_gui()
        except Exception as e:
            print(f"GUI failed to run ({e}). Falling back to interactive CLI...", file=sys.stderr)
            run_cli_interactive()
    else:
        run_cli_interactive()


if __name__ == "__main__":
    main()
