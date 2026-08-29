#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha Power Profile Selector for Waybar & Hyprland
 High-contrast, polished GTK LayerShell popup with battery status,
 active profile badges, and outside-click dismissal.
=============================================================================
"""

import os
import re
import shutil
import signal
import subprocess
import sys


def get_battery_info(profile_color="#fab387"):
    try:
        bat_dirs = [d for d in os.listdir("/sys/class/power_supply") if d.startswith("BAT")]
        if bat_dirs:
            bpath = os.path.join("/sys/class/power_supply", bat_dirs[0])
            cap = "100"
            stat = "Unknown"
            if os.path.exists(os.path.join(bpath, "capacity")):
                with open(os.path.join(bpath, "capacity")) as f:
                    cap = f.read().strip()
            if os.path.exists(os.path.join(bpath, "status")):
                with open(os.path.join(bpath, "status")) as f:
                    stat = f.read().strip()

            cap_int = int(cap) if cap.isdigit() else 100
            if stat.lower() in ["charging", "full"]:
                icon = "󰂄" if stat.lower() == "charging" else "󰚥"
            else:
                icons = ["󰂎", "󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]
                idx = min(len(icons) - 1, max(0, cap_int // 10))
                icon = icons[idx]
            return f"<span color='{profile_color}'>{icon}</span>  {cap}% • {stat}"
    except Exception:
        pass
    return f"<span color='{profile_color}'>󰁹</span>  Battery Status"


def get_dbus_power_profiles():
    try:
        import dbus
        bus = dbus.SystemBus()
        pp = bus.get_object('net.hadess.PowerProfiles', '/net/hadess/PowerProfiles')
        props = dbus.Interface(pp, 'org.freedesktop.DBus.Properties')
        active = str(props.Get('net.hadess.PowerProfiles', 'ActiveProfile'))
        profiles_raw = props.Get('net.hadess.PowerProfiles', 'Profiles')
        profiles = [str(p['Profile']) for p in profiles_raw]
        return True, active, profiles
    except Exception:
        return False, "", []


def set_dbus_power_profile(profile_name):
    try:
        import dbus
        bus = dbus.SystemBus()
        pp = bus.get_object('net.hadess.PowerProfiles', '/net/hadess/PowerProfiles')
        props = dbus.Interface(pp, 'org.freedesktop.DBus.Properties')
        props.Set('net.hadess.PowerProfiles', 'ActiveProfile', profile_name)
        return True
    except Exception:
        pass
    if shutil.which("powerprofilesctl"):
        res = subprocess.run(["powerprofilesctl", "set", profile_name], capture_output=True, text=True)
        return res.returncode == 0
    return False


def notify(title, msg, icon="preferences-system"):
    try:
        subprocess.run([
            "notify-send",
            "-r", "9915",
            "-t", "2500",
            "-u", "low",
            "-a", "Power Profile",
            "-i", icon,
            "-h", "string:x-canonical-private-synchronous:power_profile",
            title,
            msg
        ], check=False)
    except Exception:
        pass


PROFILE_METADATA = {
    "power-saver": {
        "title": "Power Saver",
        "icon": "󰌪",
        "desc": "Extends battery life, reduces fan noise and power draw.",
        "class": "powersave",
        "notify_icon": "battery-profile"
    },
    "balanced": {
        "title": "Balanced",
        "icon": "󰗑",
        "desc": "Standard dynamic balance between performance and battery.",
        "class": "balanced",
        "notify_icon": "preferences-system"
    },
    "performance": {
        "title": "Performance",
        "icon": "󰓅",
        "desc": "Maximum CPU clock speed and responsiveness.",
        "class": "performance",
        "notify_icon": "speedometer"
    }
}


CSS = """
* {
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", "RobotoMono Nerd Font", monospace;
}

window {
    background-color: transparent;
}

.main-card {
    background-color: #181825;
    border: 1.5px solid rgba(203, 166, 247, 0.45);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.7);
}

.header-icon {
    font-size: 20px;
    color: #f9e2af;
    margin-right: 8px;
}

.header-title {
    font-size: 15px;
    font-weight: 800;
    color: #cdd6f4;
}

.header-subtitle {
    font-size: 12px;
    font-weight: 600;
    color: #bac2de;
    margin-top: 4px;
    margin-bottom: 12px;
}

button {
    background-image: none;
    box-shadow: none;
    text-shadow: none;
    border: none;
    outline: none;
}

.profile-btn {
    background-color: #1e1e2e;
    border: 1.5px solid #313244;
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 8px;
    transition: all 0.15s ease-in-out;
}

.profile-btn:hover {
    background-color: #313244;
    border-color: #585b70;
}

.profile-btn.active-powersave {
    background-color: #1c2b29;
    border: 2px solid #a6e3a1;
}

.profile-btn.active-balanced {
    background-color: #1b253b;
    border: 2px solid #89b4fa;
}

.profile-btn.active-performance {
    background-color: #32252b;
    border: 2px solid #fab387;
}

.icon-label {
    font-size: 24px;
    margin-right: 14px;
}

.icon-powersave { color: #a6e3a1; }
.icon-balanced { color: #89b4fa; }
.icon-performance { color: #fab387; }

.title-label {
    font-size: 14px;
    font-weight: 800;
    color: #ffffff;
}

.desc-label {
    font-size: 11px;
    font-weight: 500;
    color: #cdd6f4;
    margin-top: 3px;
}

.badge {
    font-size: 11px;
    font-weight: 800;
    border-radius: 8px;
    padding: 4px 10px;
}

.badge-powersave {
    background-color: #a6e3a1;
    color: #11111b;
}

.badge-balanced {
    background-color: #89b4fa;
    color: #11111b;
}

.badge-performance {
    background-color: #fab387;
    color: #11111b;
}
"""


def check_and_kill_existing():
    my_pid = os.getpid()
    try:
        out = subprocess.run(["pgrep", "-f", "power-profile.py"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            pid = int(line.strip())
            if pid != my_pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
                sys.exit(0)
    except Exception:
        pass


def launch_gtk_gui():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, GtkLayerShell, GLib

    # Get active profile and available profiles
    ok, active_profile, profiles = get_dbus_power_profiles()
    if not ok or not profiles:
        profiles = ["power-saver", "balanced", "performance"]
        active_profile = "balanced"

    active_clean = active_profile.lower().strip()
    profile_color = "#a6e3a1" if "save" in active_clean else ("#f38ba8" if "perf" in active_clean else "#fab387")
    bat_info = get_battery_info(profile_color)

    # Apply CSS
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS.encode('utf-8'))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    # 1. Fullscreen transparent backdrop for outside-click dismissal
    backdrop = Gtk.Window()
    backdrop.set_title("power-profile-backdrop")
    backdrop.set_decorated(False)
    backdrop.set_app_paintable(True)

    screen = backdrop.get_screen()
    visual = screen.get_rgba_visual()
    if visual:
        backdrop.set_visual(visual)

    GtkLayerShell.init_for_window(backdrop)
    GtkLayerShell.set_layer(backdrop, GtkLayerShell.Layer.TOP)
    GtkLayerShell.set_namespace(backdrop, "power-profile-backdrop")
    GtkLayerShell.set_keyboard_mode(backdrop, GtkLayerShell.KeyboardMode.NONE)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.BOTTOM, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.LEFT, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.RIGHT, True)

    def on_draw(widget, cr):
        cr.set_source_rgba(0, 0, 0, 0.001)
        cr.paint()
        return False

    backdrop.connect("draw", on_draw)
    backdrop.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def dismiss(widget=None, event=None):
        Gtk.main_quit()
        return True

    backdrop.connect("button-press-event", dismiss)
    backdrop.show_all()

    # 2. Main Popup Window
    win = Gtk.Window()
    win.set_title("power-profile-popup")
    win.set_decorated(False)
    win.set_app_paintable(True)
    if visual:
        win.set_visual(visual)

    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_namespace(win, "power-profile-popup")
    GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.ON_DEMAND)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT, True)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 48)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.RIGHT, 14)

    # Key press: Escape dismisses
    def on_key_press(widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    win.connect("key-press-event", on_key_press)

    # Main Card Container
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    card.get_style_context().add_class("main-card")
    card.set_size_request(360, -1)

    # Header Box
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    h_icon = Gtk.Label(label="⚡")
    h_icon.get_style_context().add_class("header-icon")
    h_title = Gtk.Label(label="Power Profile")
    h_title.get_style_context().add_class("header-title")
    header_box.pack_start(h_icon, False, False, 0)
    header_box.pack_start(h_title, False, False, 0)

    # Subtitle with Battery Status (Pango Markup)
    sub_label = Gtk.Label()
    sub_label.set_markup(bat_info)
    sub_label.set_xalign(0)
    sub_label.get_style_context().add_class("header-subtitle")

    card.pack_start(header_box, False, False, 0)
    card.pack_start(sub_label, False, False, 0)

    # Profile Rows
    for prof in profiles:
        meta = PROFILE_METADATA.get(prof, {
            "title": prof.capitalize(),
            "icon": "󰚥",
            "desc": f"Switch to {prof} profile",
            "class": "balanced",
            "notify_icon": "preferences-system"
        })

        is_active = (prof.lower() == active_clean or (active_clean and active_clean in prof.lower()))

        btn = Gtk.Button()
        btn.get_style_context().add_class("profile-btn")
        if is_active:
            btn.get_style_context().add_class(f"active-{meta['class']}")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        # Icon
        icon_lbl = Gtk.Label(label=meta["icon"])
        icon_lbl.get_style_context().add_class("icon-label")
        icon_lbl.get_style_context().add_class(f"icon-{meta['class']}")
        row.pack_start(icon_lbl, False, False, 0)

        # Text Box (Title + Description)
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label=meta["title"])
        title_lbl.set_xalign(0)
        title_lbl.get_style_context().add_class("title-label")

        desc_lbl = Gtk.Label(label=meta["desc"])
        desc_lbl.set_xalign(0)
        desc_lbl.set_line_wrap(True)
        desc_lbl.set_max_width_chars(28)
        desc_lbl.get_style_context().add_class("desc-label")

        text_box.pack_start(title_lbl, False, False, 0)
        text_box.pack_start(desc_lbl, False, False, 0)
        row.pack_start(text_box, True, True, 0)

        # Badge if Active
        if is_active:
            badge = Gtk.Label(label="󰄬 Active")
            badge.get_style_context().add_class("badge")
            badge.get_style_context().add_class(f"badge-{meta['class']}")
            row.pack_end(badge, False, False, 0)

        btn.add(row)

        def make_click_handler(target_prof, target_meta):
            def on_btn_clicked(widget):
                set_dbus_power_profile(target_prof)
                subprocess.run(["bash", "-c", "pgrep -x waybar >/dev/null && pkill -RTMIN+8 waybar || true"], check=False)
                notify(
                    "Power Profile Changed",
                    f"Switched to {target_meta['title']}",
                    icon=target_meta["notify_icon"]
                )
                Gtk.main_quit()
            return on_btn_clicked

        btn.connect("clicked", make_click_handler(prof, meta))
        card.pack_start(btn, False, False, 0)

    win.add(card)
    win.show_all()
    Gtk.main()


def main():
    check_and_kill_existing()
    try:
        launch_gtk_gui()
    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
