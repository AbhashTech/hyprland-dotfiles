#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha Display Brightness & Contrast Control Center
 for Waybar & Hyprland
 Features:
   - Ultra-Fast Instant Launch (<30ms) via Cached Display Metadata &
     Non-blocking Asynchronous Background DDC/CI Sync
   - Modern GTK3 Layer Shell GUI:
       * Built-in Laptop Display Brightness Range Slider & Presets
       * External Monitor(s) Brightness & Contrast Range Sliders via DDC/CI
       * Night Light (Blue Light Filter) Toggle & Color Temp Sliders
       * Smooth Asynchronous Debounced DDC/CI Hardware Writes
       * Auto-dismiss on Outside Click or Escape Key
       * Waybar Single-Instance Toggle Support
   - Interactive Curses TUI Mode (--tui)
   - Fast Fuzzel / Wofi Menu Fallback (--menu)
=============================================================================
"""

import curses
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

BRIGHTNESS_NOTIF_ID = "9124"
DDC_NOTIF_ID = "9125"
NIGHTLIGHT_PID_FILE = "/tmp/hypr_nightlight.pid"
NIGHTLIGHT_STATE_FILE = "/tmp/hypr_nightlight.state"
CACHE_FILE = "/tmp/brightness_display_cache.json"


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def run_cmd(cmd, check=False):
    """Execute command and return stripped stdout or empty string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""


def build_progress_bar(percentage, length=12):
    """Create a visual ASCII progress bar."""
    pct = max(0, min(100, percentage))
    filled = int(round((pct / 100.0) * length))
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"


def show_notification(title, body, icon="display-brightness-high", percentage=None, notif_id=BRIGHTNESS_NOTIF_ID, tag="brightness_osd"):
    """Display desktop OSD notification."""
    cmd = [
        "notify-send",
        "-r", str(notif_id),
        "-t", "1500",
        "-u", "low",
        "-a", "BrightnessManager",
        "-c", "osd",
        "-i", icon,
        "-h", f"string:x-canonical-private-synchronous:{tag}",
        "-h", "boolean:transient:true",
        "-h", "boolean:history-ignore:true"
    ]
    if percentage is not None:
        cmd.extend(["-h", f"int:value:{int(min(100, max(0, percentage)))}"])
    cmd.extend([title, body])
    subprocess.Popen(cmd)


# =============================================================================
# HARDWARE BACKENDS
# =============================================================================

class DisplayBackend:
    @staticmethod
    def get_laptop_brightness():
        """Retrieve current internal backlight percentage and device name (<3ms)."""
        raw = run_cmd(["brightnessctl", "-m"])
        if raw:
            lines = raw.strip().splitlines()
            if lines:
                parts = lines[0].split(",")
                if len(parts) >= 4:
                    dev = parts[0]
                    pct_str = parts[3].rstrip("%")
                    try:
                        pct = int(pct_str)
                    except ValueError:
                        pct = 50
                    return pct, dev
        return None, None

    @staticmethod
    def set_laptop_brightness(percent):
        pct = max(1, min(100, int(percent)))
        run_cmd(["brightnessctl", "set", f"{pct}%"])

    @staticmethod
    def get_instant_displays():
        """Instantly read connected monitors via hyprctl + local cache (<10ms)."""
        cache = load_cache()
        laptop_pct, laptop_dev = DisplayBackend.get_laptop_brightness()
        
        ext_monitors = []
        raw_monitors = run_cmd(["hyprctl", "-j", "monitors"])
        if raw_monitors:
            try:
                monitors = json.loads(raw_monitors)
                disp_counter = 1
                for m in monitors:
                    name = m.get("name", "")
                    if not name.startswith("eDP"):
                        disp_desc = m.get("description") or m.get("model") or f"External Display ({name})"
                        cached_vals = cache.get(name, {})
                        ext_monitors.append({
                            "display_num": disp_counter,
                            "connector": name,
                            "name": disp_desc,
                            "brightness": cached_vals.get("brightness", 50),
                            "contrast": cached_vals.get("contrast", 50)
                        })
                        disp_counter += 1
            except Exception:
                pass

        # Fallback if no hyprctl monitors found
        if not ext_monitors and cache.get("fallback_ext"):
            ext_monitors = cache["fallback_ext"]

        return laptop_pct, laptop_dev, ext_monitors

    @staticmethod
    def get_ddc_values(display_num=1):
        """Read brightness (0x10) and contrast (0x12) from external monitor in background."""
        res = run_cmd(["ddcutil", "--noverify", "-d", str(display_num), "getvcp", "10", "12"])
        brightness = None
        contrast = None
        for line in res.splitlines():
            if "0x10" in line or "Brightness" in line:
                m = re.search(r"current value =\s*(\d+)", line)
                if m:
                    brightness = int(m.group(1))
            elif "0x12" in line or "Contrast" in line:
                m = re.search(r"current value =\s*(\d+)", line)
                if m:
                    contrast = int(m.group(1))
        return brightness, contrast

    @staticmethod
    def set_ddc_brightness(display_num, val):
        val = max(0, min(100, int(val)))
        run_cmd(["ddcutil", "--noverify", "-d", str(display_num), "setvcp", "10", str(val)])

    @staticmethod
    def set_ddc_contrast(display_num, val):
        val = max(0, min(100, int(val)))
        run_cmd(["ddcutil", "--noverify", "-d", str(display_num), "setvcp", "12", str(val)])


class NightLightBackend:
    @staticmethod
    def is_active():
        if os.path.exists(NIGHTLIGHT_PID_FILE):
            try:
                with open(NIGHTLIGHT_PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                return True
            except Exception:
                try:
                    os.remove(NIGHTLIGHT_PID_FILE)
                except OSError:
                    pass
        return False

    @staticmethod
    def get_current_temp():
        if os.path.exists(NIGHTLIGHT_STATE_FILE):
            try:
                with open(NIGHTLIGHT_STATE_FILE, "r") as f:
                    return int(f.read().strip())
            except Exception:
                pass
        return 3800

    @staticmethod
    def toggle(temp=3800):
        if NightLightBackend.is_active():
            NightLightBackend.stop()
        else:
            NightLightBackend.start(temp)

    @staticmethod
    def start(temp=3800):
        NightLightBackend.stop()
        binary = shutil.which("hyprsunset") or shutil.which("wlsunset")
        if not binary:
            return False
        cmd = ["hyprsunset", "-t", str(temp)] if "hyprsunset" in binary else ["wlsunset", "-t", str(temp), "-T", "6500"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(NIGHTLIGHT_PID_FILE, "w") as f:
                f.write(str(proc.pid))
            with open(NIGHTLIGHT_STATE_FILE, "w") as f:
                f.write(str(temp))
            show_notification("🌙 Night Light Enabled", f"Warm color temperature set to <b>{temp}K</b>.", "weather-clear-night")
            return True
        except Exception:
            return False

    @staticmethod
    def stop():
        if os.path.exists(NIGHTLIGHT_PID_FILE):
            try:
                with open(NIGHTLIGHT_PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            try:
                os.remove(NIGHTLIGHT_PID_FILE)
            except OSError:
                pass
        if os.path.exists(NIGHTLIGHT_STATE_FILE):
            try:
                os.remove(NIGHTLIGHT_STATE_FILE)
            except OSError:
                pass
        subprocess.run(["pkill", "-x", "hyprsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-x", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        show_notification("☀️ Night Light Disabled", "Display color temperature restored to normal (6500K).", "weather-clear")


# =============================================================================
# SINGLETON TOGGLE HANDLER
# =============================================================================

def check_and_kill_existing():
    my_pid = os.getpid()
    try:
        out = subprocess.run(["pgrep", "-f", "brightness-manager.py"], capture_output=True, text=True).stdout
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


# =============================================================================
# ASYNC DEBOUNCED DDC WORKER
# =============================================================================

class AsyncDDCWorker:
    """Thread-safe debounced writer for DDC/CI to ensure zero UI stutter."""
    def __init__(self):
        self._lock = threading.Lock()
        self._pending_tasks = {}  # (disp_num, vcp_code): target_val
        self._worker_thread = None
        self._running = True

    def queue_vcp(self, display_num, vcp_code, val, connector=None):
        with self._lock:
            self._pending_tasks[(display_num, vcp_code)] = val
            # Update cache immediately so next open has latest value
            if connector:
                cache = load_cache()
                if connector not in cache:
                    cache[connector] = {}
                if vcp_code == 10:
                    cache[connector]["brightness"] = val
                elif vcp_code == 12:
                    cache[connector]["contrast"] = val
                save_cache(cache)

            if not self._worker_thread or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
                self._worker_thread.start()

    def _run_loop(self):
        while self._running:
            time.sleep(0.06)  # Fast debounce delay
            task = None
            with self._lock:
                if self._pending_tasks:
                    key = next(iter(self._pending_tasks))
                    val = self._pending_tasks.pop(key)
                    task = (key[0], key[1], val)
                else:
                    break
            if task:
                disp_num, vcp_code, val = task
                if vcp_code == 10:
                    DisplayBackend.set_ddc_brightness(disp_num, val)
                elif vcp_code == 12:
                    DisplayBackend.set_ddc_contrast(disp_num, val)


ddc_worker = AsyncDDCWorker()


# =============================================================================
# GTK3 LAYER SHELL GUI WITH RANGE SLIDERS & PRESETS
# =============================================================================

def get_brightness_theme_colors():
    """Load colors from active theme JSON file with fallback."""
    cache_state = Path.home() / ".cache" / "hypr_theme_state.json"
    current_txt = Path.home() / ".cache" / "current_theme"
    theme_id = "catppuccin-mocha"
    
    if cache_state.exists():
        try:
            with open(cache_state, "r") as f:
                theme_id = json.load(f).get("current_theme", theme_id)
        except Exception:
            pass
    elif current_txt.exists():
        try:
            theme_id = current_txt.read_text().strip() or theme_id
        except Exception:
            pass

    for d in [Path.home() / ".config" / "theme", Path.home() / ".dotfiles" / ".config" / "theme"]:
        tfile = d / f"{theme_id}.json"
        if tfile.exists():
            try:
                with open(tfile, "r") as f:
                    tdata = json.load(f)
                    return tdata.get("colors", {}), tdata.get("type", "dark")
            except Exception:
                pass

    return {
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
        "accent": "#cba6f7", "blue": "#89b4fa", "green": "#a6e3a1",
        "yellow": "#f9e2af", "peach": "#fab387", "red": "#f38ba8",
        "mauve": "#cba6f7", "teal": "#94e2d5", "pink": "#f5c2e7",
    }, "dark"

def get_brightness_gtk_css():
    c, ttype = get_brightness_theme_colors()
    return f"""
* {{
    all: unset;
    font-family: 'Inter', 'Noto Sans', 'JetBrains Mono Nerd Font', 'JetBrains Mono', 'Ubuntu', sans-serif;
}}

window {{
    background-color: transparent;
}}

.main-card {{
    background-color: {c.get("mantle", "#181825")};
    border: 2px solid {c.get("accent", "#cba6f7")};
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65);
}}

.header-title {{
    font-size: 16px;
    font-weight: 900;
    color: {c.get("text", "#cdd6f4")};
}}

.header-icon {{
    font-size: 20px;
    color: {c.get("yellow", "#f9e2af")};
    margin-right: 8px;
}}

.section-box {{
    background-color: {c.get("base", "#1e1e2e")};
    border: 1px solid {c.get("surface0", "#313244")};
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 10px;
}}

.section-label {{
    font-size: 12px;
    font-weight: 800;
    color: {c.get("yellow", "#f9e2af")};
    margin-bottom: 4px;
}}

.section-label-ext {{
    color: {c.get("blue", "#89b4fa")};
}}

.section-label-night {{
    color: {c.get("peach", "#fab387")};
}}

.row-label {{
    font-size: 12px;
    font-weight: 700;
    color: {c.get("text", "#cdd6f4")};
    min-width: 90px;
}}

/* Range Select Sliders (GtkScale) */
scale {{
    margin: 6px 0px 4px 0px;
}}

scale trough {{
    background-color: {c.get("surface0", "#313244")};
    border-radius: 8px;
    min-height: 10px;
    min-width: 200px;
}}

scale highlight {{
    background: {c.get("yellow", "#f9e2af")};
    border-radius: 8px;
    min-height: 10px;
}}

scale.ext-scale highlight {{
    background: {c.get("blue", "#89b4fa")};
}}

scale.contrast-scale highlight {{
    background: {c.get("accent", "#cba6f7")};
}}

scale.temp-scale highlight {{
    background: {c.get("peach", "#fab387")};
}}

scale slider {{
    background-color: {c.get("text", "#ffffff")};
    border: 2px solid {c.get("yellow", "#f9e2af")};
    border-radius: 12px;
    min-width: 18px;
    min-height: 18px;
    margin: -4px 0px;
}}

scale.ext-scale slider {{
    border-color: {c.get("blue", "#89b4fa")};
}}

scale.contrast-scale slider {{
    border-color: {c.get("accent", "#cba6f7")};
}}

scale.temp-scale slider {{
    border-color: {c.get("peach", "#fab387")};
}}

scale slider:hover {{
    background-color: {c.get("accent", "#cba6f7")};
    border-color: {c.get("text", "#ffffff")};
}}

/* Value Badge */
.val-badge {{
    font-size: 13px;
    font-weight: 900;
    color: {c.get("yellow", "#f9e2af")};
    min-width: 48px;
}}

.val-badge-ext {{
    color: {c.get("blue", "#89b4fa")};
}}

.val-badge-contrast {{
    color: {c.get("accent", "#cba6f7")};
}}

.val-badge-temp {{
    color: {c.get("peach", "#fab387")};
    min-width: 60px;
}}

/* Preset Buttons */
.btn-preset {{
    background-color: {c.get("base", "#1e1e2e")};
    border: 1px solid {c.get("surface1", "#45475a")};
    border-radius: 8px;
    padding: 3px 8px;
    color: {c.get("subtext0", "#a6adc8")};
    font-size: 11px;
    font-weight: 700;
    margin: 3px 2px 0px 2px;
}}

.btn-preset:hover {{
    background-color: {c.get("yellow", "#f9e2af")};
    color: #11111b;
    border-color: {c.get("yellow", "#f9e2af")};
}}

.btn-preset-ext:hover {{
    background-color: {c.get("blue", "#89b4fa")};
    color: #11111b;
    border-color: {c.get("blue", "#89b4fa")};
}}

.btn-preset-contrast:hover {{
    background-color: {c.get("accent", "#cba6f7")};
    color: #11111b;
    border-color: {c.get("accent", "#cba6f7")};
}}

/* Toggle / Action Buttons */
.btn-toggle {{
    background-color: {c.get("surface0", "#313244")};
    border: 1.5px solid {c.get("surface1", "#45475a")};
    border-radius: 10px;
    padding: 6px 14px;
    color: {c.get("text", "#cdd6f4")};
    font-size: 12.5px;
    font-weight: 800;
}}

.btn-toggle:hover {{
    background-color: {c.get("surface1", "#45475a")};
    border-color: {c.get("peach", "#fab387")};
}}

.btn-toggle.active {{
    background-color: {c.get("surface1", "#45475a")};
    border: 1.5px solid {c.get("peach", "#fab387")};
    color: {c.get("peach", "#fab387")};
}}

.btn-action {{
    background-color: {c.get("surface0", "#313244")};
    border: 1px solid {c.get("surface1", "#45475a")};
    border-radius: 10px;
    padding: 6px 12px;
    color: {c.get("text", "#cdd6f4")};
    font-size: 11.5px;
    font-weight: 700;
}}

.btn-action:hover {{
    background-color: {c.get("surface1", "#45475a")};
    color: {c.get("text", "#ffffff")};
    border-color: {c.get("yellow", "#f9e2af")};
}}
""".encode('utf-8')

def launch_gtk_gui():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, GtkLayerShell, GLib

    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(get_brightness_gtk_css())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    # 1. Fullscreen transparent backdrop for outside-click dismissal
    backdrop = Gtk.Window()
    backdrop.set_title("brightness-control-backdrop")
    backdrop.set_decorated(False)
    backdrop.set_app_paintable(True)

    screen = backdrop.get_screen()
    visual = screen.get_rgba_visual()
    if visual:
        backdrop.set_visual(visual)

    GtkLayerShell.init_for_window(backdrop)
    GtkLayerShell.set_layer(backdrop, GtkLayerShell.Layer.TOP)
    GtkLayerShell.set_namespace(backdrop, "brightness-control-backdrop")
    GtkLayerShell.set_keyboard_mode(backdrop, GtkLayerShell.KeyboardMode.NONE)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.BOTTOM, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.LEFT, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.RIGHT, True)

    def on_draw_backdrop(widget, cr):
        cr.set_source_rgba(0, 0, 0, 0.001)
        cr.paint()
        return False

    backdrop.connect("draw", on_draw_backdrop)
    backdrop.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def dismiss(widget=None, event=None):
        Gtk.main_quit()
        return True

    backdrop.connect("button-press-event", dismiss)
    backdrop.show_all()

    # 2. Main Popup Window
    win = Gtk.Window()
    win.set_title("brightness-control-popup")
    win.set_decorated(False)
    win.set_app_paintable(True)
    if visual:
        win.set_visual(visual)

    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_namespace(win, "brightness-control-popup")
    GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.ON_DEMAND)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT, True)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 48)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.RIGHT, 14)

    def on_key_press(widget, event):
        if event.keyval in [Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q]:
            Gtk.main_quit()
            return True
        return False

    win.connect("key-press-event", on_key_press)

    # Main Card
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    card.get_style_context().add_class("main-card")
    card.set_size_request(450, -1)

    # Header
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    h_icon = Gtk.Label(label="󰃠")
    h_icon.get_style_context().add_class("header-icon")
    h_title = Gtk.Label(label="Display & Brightness Control Center")
    h_title.get_style_context().add_class("header-title")
    header_box.pack_start(h_icon, False, False, 0)
    header_box.pack_start(h_title, False, False, 0)

    btn_close = Gtk.Button(label="󰅖")
    btn_close.get_style_context().add_class("btn-action")
    btn_close.connect("clicked", lambda b: Gtk.main_quit())
    header_box.pack_end(btn_close, False, False, 0)
    card.pack_start(header_box, False, False, 0)

    # Fast Instant Detection (<10ms)
    laptop_pct, laptop_dev, ext_monitors = DisplayBackend.get_instant_displays()

    # -------------------------------------------------------------
    # SECTION 1: BUILT-IN LAPTOP DISPLAY
    # -------------------------------------------------------------
    if laptop_pct is not None:
        int_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        int_box.get_style_context().add_class("section-box")

        int_lbl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        int_lbl = Gtk.Label(label=f"☀️ BUILT-IN DISPLAY ({laptop_dev})")
        int_lbl.get_style_context().add_class("section-label")
        int_lbl_box.pack_start(int_lbl, False, False, 0)
        int_box.pack_start(int_lbl_box, False, False, 0)

        # Range slider row
        int_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        int_row_lbl = Gtk.Label(label="󰃠 Brightness")
        int_row_lbl.get_style_context().add_class("row-label")
        int_row.pack_start(int_row_lbl, False, False, 0)

        int_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        int_scale.set_value(laptop_pct)
        int_scale.set_hexpand(True)
        int_scale.set_draw_value(False)
        int_row.pack_start(int_scale, True, True, 0)

        int_badge = Gtk.Label(label=f"{laptop_pct}%")
        int_badge.set_xalign(1.0)
        int_badge.get_style_context().add_class("val-badge")
        int_row.pack_start(int_badge, False, False, 0)
        int_box.pack_start(int_row, False, False, 0)

        def on_int_scale_change(slider):
            val = int(slider.get_value())
            int_badge.set_text(f"{val}%")
            DisplayBackend.set_laptop_brightness(val)

        int_scale.connect("value-changed", on_int_scale_change)

        # Presets
        int_presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for p in [10, 25, 50, 75, 100]:
            btn_p = Gtk.Button(label=f"{p}%")
            btn_p.get_style_context().add_class("btn-preset")
            btn_p.connect("clicked", lambda b, val=p: int_scale.set_value(val))
            int_presets_box.pack_start(btn_p, True, True, 0)
        int_box.pack_start(int_presets_box, False, False, 0)

        card.pack_start(int_box, False, False, 0)

    # -------------------------------------------------------------
    # SECTION 2: EXTERNAL DISPLAY(S) (BRIGHTNESS & CONTRAST)
    # -------------------------------------------------------------
    bg_sync_targets = []

    for mon in ext_monitors:
        disp_num = mon["display_num"]
        disp_name = mon["name"]
        connector = mon.get("connector", f"disp_{disp_num}")
        curr_b = mon["brightness"]
        curr_c = mon["contrast"]

        ext_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ext_box.get_style_context().add_class("section-box")

        ext_lbl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ext_lbl = Gtk.Label(label=f"🖥️ EXTERNAL DISPLAY: {disp_name}")
        ext_lbl.get_style_context().add_class("section-label")
        ext_lbl.get_style_context().add_class("section-label-ext")
        ext_lbl_box.pack_start(ext_lbl, False, False, 0)
        ext_box.pack_start(ext_lbl_box, False, False, 0)

        # 1. External Brightness Slider
        b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b_lbl = Gtk.Label(label="󰃠 Brightness")
        b_lbl.get_style_context().add_class("row-label")
        b_row.pack_start(b_lbl, False, False, 0)

        b_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        b_scale.get_style_context().add_class("ext-scale")
        b_scale.set_value(curr_b)
        b_scale.set_hexpand(True)
        b_scale.set_draw_value(False)
        b_row.pack_start(b_scale, True, True, 0)

        b_badge = Gtk.Label(label=f"{curr_b}%")
        b_badge.set_xalign(1.0)
        b_badge.get_style_context().add_class("val-badge")
        b_badge.get_style_context().add_class("val-badge-ext")
        b_row.pack_start(b_badge, False, False, 0)
        ext_box.pack_start(b_row, False, False, 0)

        def on_ext_b_change(slider, d_num=disp_num, conn=connector, badge=b_badge):
            val = int(slider.get_value())
            badge.set_text(f"{val}%")
            ddc_worker.queue_vcp(d_num, 10, val, conn)

        b_scale.connect("value-changed", on_ext_b_change)

        # Brightness Presets
        b_presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for p in [20, 40, 60, 80, 100]:
            btn_bp = Gtk.Button(label=f"{p}%")
            btn_bp.get_style_context().add_class("btn-preset")
            btn_bp.get_style_context().add_class("btn-preset-ext")
            btn_bp.connect("clicked", lambda b, val=p, sc=b_scale: sc.set_value(val))
            b_presets_box.pack_start(btn_bp, True, True, 0)
        ext_box.pack_start(b_presets_box, False, False, 0)

        # 2. External Contrast Slider
        c_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        c_lbl = Gtk.Label(label="󰃟 Contrast")
        c_lbl.get_style_context().add_class("row-label")
        c_row.pack_start(c_lbl, False, False, 0)

        c_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        c_scale.get_style_context().add_class("contrast-scale")
        c_scale.set_value(curr_c)
        c_scale.set_hexpand(True)
        c_scale.set_draw_value(False)
        c_row.pack_start(c_scale, True, True, 0)

        c_badge = Gtk.Label(label=f"{curr_c}%")
        c_badge.set_xalign(1.0)
        c_badge.get_style_context().add_class("val-badge")
        c_badge.get_style_context().add_class("val-badge-contrast")
        c_row.pack_start(c_badge, False, False, 0)
        ext_box.pack_start(c_row, False, False, 0)

        def on_ext_c_change(slider, d_num=disp_num, conn=connector, badge=c_badge):
            val = int(slider.get_value())
            badge.set_text(f"{val}%")
            ddc_worker.queue_vcp(d_num, 12, val, conn)

        c_scale.connect("value-changed", on_ext_c_change)

        # Contrast Presets
        c_presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for p in [30, 50, 70, 85, 100]:
            btn_cp = Gtk.Button(label=f"{p}%")
            btn_cp.get_style_context().add_class("btn-preset")
            btn_cp.get_style_context().add_class("btn-preset-contrast")
            btn_cp.connect("clicked", lambda b, val=p, sc=c_scale: sc.set_value(val))
            c_presets_box.pack_start(btn_cp, True, True, 0)
        ext_box.pack_start(c_presets_box, False, False, 0)

        card.pack_start(ext_box, False, False, 0)
        bg_sync_targets.append((disp_num, connector, b_scale, b_badge, c_scale, c_badge))

    # -------------------------------------------------------------
    # SECTION 3: NIGHT LIGHT & COLOR TEMPERATURE
    # -------------------------------------------------------------
    night_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    night_box.get_style_context().add_class("section-box")

    night_lbl = Gtk.Label(label="🌙 NIGHT LIGHT / BLUE LIGHT FILTER")
    night_lbl.get_style_context().add_class("section-label")
    night_lbl.get_style_context().add_class("section-label-night")
    night_box.pack_start(night_lbl, False, False, 0)

    is_night_active = NightLightBackend.is_active()
    curr_temp = NightLightBackend.get_current_temp()

    toggle_btn = Gtk.Button(label="☀️ Night Light: Disabled (Click to Enable)" if not is_night_active else "🌙 Night Light: Active (Click to Disable)")
    toggle_btn.get_style_context().add_class("btn-toggle")
    if is_night_active:
        toggle_btn.get_style_context().add_class("active")

    temp_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    temp_lbl = Gtk.Label(label="🌡️ Color Temp")
    temp_lbl.get_style_context().add_class("row-label")
    temp_row.pack_start(temp_lbl, False, False, 0)

    temp_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 2500, 6500, 100)
    temp_scale.get_style_context().add_class("temp-scale")
    temp_scale.set_value(curr_temp)
    temp_scale.set_hexpand(True)
    temp_scale.set_draw_value(False)
    temp_row.pack_start(temp_scale, True, True, 0)

    temp_badge = Gtk.Label(label=f"{curr_temp}K")
    temp_badge.set_xalign(1.0)
    temp_badge.get_style_context().add_class("val-badge")
    temp_badge.get_style_context().add_class("val-badge-temp")
    temp_row.pack_start(temp_badge, False, False, 0)

    def on_temp_change(slider):
        val = int(slider.get_value())
        temp_badge.set_text(f"{val}K")
        if NightLightBackend.is_active():
            NightLightBackend.start(val)

    temp_scale.connect("value-changed", on_temp_change)

    def on_night_toggle(btn):
        if NightLightBackend.is_active():
            NightLightBackend.stop()
            btn.set_label("☀️ Night Light: Disabled (Click to Enable)")
            btn.get_style_context().remove_class("active")
        else:
            t = int(temp_scale.get_value())
            NightLightBackend.start(t)
            btn.set_label("🌙 Night Light: Active (Click to Disable)")
            btn.get_style_context().add_class("active")

    toggle_btn.connect("clicked", on_night_toggle)
    night_box.pack_start(toggle_btn, False, False, 0)
    night_box.pack_start(temp_row, False, False, 0)

    # Temperature Presets
    temp_presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    temp_presets = [("3000K Candle", 3000), ("3800K Warm", 3800), ("4500K Soft", 4500), ("6500K Daylight", 6500)]
    for label, temp_val in temp_presets:
        btn_tp = Gtk.Button(label=label)
        btn_tp.get_style_context().add_class("btn-preset")
        btn_tp.connect("clicked", lambda b, val=temp_val: (temp_scale.set_value(val), NightLightBackend.start(val) if NightLightBackend.is_active() else None))
        temp_presets_box.pack_start(btn_tp, True, True, 0)
    night_box.pack_start(temp_presets_box, False, False, 0)

    card.pack_start(night_box, False, False, 0)

    # -------------------------------------------------------------
    # FOOTER ACTIONS
    # -------------------------------------------------------------
    footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    footer_box.set_margin_top(12)

    btn_res = Gtk.Button(label="🖥️ Resolution & Display Layout")
    btn_res.get_style_context().add_class("btn-action")
    btn_res.connect("clicked", lambda b: (subprocess.Popen(["/home/kunal/.config/hypr/scripts/resolution_menu.py"]), Gtk.main_quit()))
    footer_box.pack_start(btn_res, True, True, 0)

    card.pack_start(footer_box, False, False, 0)

    win.add(card)
    win.show_all()

    # -------------------------------------------------------------
    # NON-BLOCKING ASYNC BACKGROUND HARDWARE PROBE
    # -------------------------------------------------------------
    def bg_sync_worker():
        for d_num, conn, b_sc, b_bdg, c_sc, c_bdg in bg_sync_targets:
            live_b, live_c = DisplayBackend.get_ddc_values(d_num)
            if live_b is not None or live_c is not None:
                cache = load_cache()
                if conn not in cache:
                    cache[conn] = {}
                if live_b is not None:
                    cache[conn]["brightness"] = live_b
                if live_c is not None:
                    cache[conn]["contrast"] = live_c
                save_cache(cache)

                def update_widgets(b=live_b, c=live_c, b_scale=b_sc, b_badge=b_bdg, c_scale=c_sc, c_badge=c_bdg):
                    if b is not None:
                        b_scale.handler_block_by_func(on_ext_b_change)
                        b_scale.set_value(b)
                        b_badge.set_text(f"{b}%")
                        b_scale.handler_unblock_by_func(on_ext_b_change)
                    if c is not None:
                        c_scale.handler_block_by_func(on_ext_c_change)
                        c_scale.set_value(c)
                        c_badge.set_text(f"{c}%")
                        c_scale.handler_unblock_by_func(on_ext_c_change)
                    return False

                GLib.idle_add(update_widgets)

    if bg_sync_targets:
        threading.Thread(target=bg_sync_worker, daemon=True).start()

    Gtk.main()


# =============================================================================
# CURSES TUI INTERACTIVE MIXER (--tui)
# =============================================================================

def launch_curses_tui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)

    laptop_pct, laptop_dev, ext_monitors = DisplayBackend.get_instant_displays()

    # Build items: (Type, Label, CurrentVal, DisplayNum, VcpCode, Connector)
    items = []
    if laptop_pct is not None:
        items.append({"type": "laptop", "label": f"Built-in Display ({laptop_dev})", "val": laptop_pct, "disp": 0, "vcp": 0, "conn": None})
    for mon in ext_monitors:
        items.append({"type": "ext_b", "label": f"{mon['name']} - Brightness", "val": mon["brightness"], "disp": mon["display_num"], "vcp": 10, "conn": mon.get("connector")})
        items.append({"type": "ext_c", "label": f"{mon['name']} - Contrast", "val": mon["contrast"], "disp": mon["display_num"], "vcp": 12, "conn": mon.get("connector")})
    items.append({"type": "night", "label": "🌙 Night Light", "val": NightLightBackend.get_current_temp(), "disp": 0, "vcp": 0, "conn": None})

    idx = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        title = " 󰃠 DISPLAY BRIGHTNESS & CONTRAST MANAGER (TUI) "
        stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, 2, "─" * (w - 4), curses.A_DIM)

        for i, item in enumerate(items):
            y = 4 + i * 3
            if y + 2 >= h:
                break
            is_sel = (i == idx)
            prefix = "▶ " if is_sel else "  "

            if item["type"] == "night":
                st = "ACTIVE" if NightLightBackend.is_active() else "OFF"
                val_str = f"[{st} - {item['val']}K]"
                bar = build_progress_bar(int((item["val"] - 2500) / 4000 * 100), length=max(8, w - 40))
            else:
                val_str = f"[{item['val']}%]"
                bar = build_progress_bar(item["val"], length=max(8, w - 40))

            color = curses.color_pair(4 if is_sel else 1)
            stdscr.addstr(y, 2, f"{prefix}{item['label']}", color | curses.A_BOLD)
            stdscr.addstr(y + 1, 4, f"{bar}  {val_str}", curses.color_pair(2) | curses.A_BOLD)

        help_txt = " [↑/↓] Navigate  |  [←/→] Adjust (±5%)  |  [Space/Enter] Toggle Nightlight  |  [Q/Esc] Quit "
        stdscr.addstr(h - 2, max(0, (w - len(help_txt)) // 2), help_txt, curses.A_DIM)
        stdscr.refresh()

        ch = stdscr.getch()
        if ch in [ord('q'), ord('Q'), 27]:
            break
        elif ch in [curses.KEY_UP, ord('k')]:
            idx = (idx - 1) % len(items)
        elif ch in [curses.KEY_DOWN, ord('j')]:
            idx = (idx + 1) % len(items)
        elif ch in [curses.KEY_LEFT, ord('h')]:
            curr = items[idx]
            if curr["type"] == "laptop":
                curr["val"] = max(1, curr["val"] - 5)
                DisplayBackend.set_laptop_brightness(curr["val"])
            elif curr["type"] == "ext_b":
                curr["val"] = max(0, curr["val"] - 5)
                ddc_worker.queue_vcp(curr["disp"], 10, curr["val"], curr["conn"])
            elif curr["type"] == "ext_c":
                curr["val"] = max(0, curr["val"] - 5)
                ddc_worker.queue_vcp(curr["disp"], 12, curr["val"], curr["conn"])
            elif curr["type"] == "night":
                curr["val"] = max(2500, curr["val"] - 200)
                if NightLightBackend.is_active():
                    NightLightBackend.start(curr["val"])
        elif ch in [curses.KEY_RIGHT, ord('l')]:
            curr = items[idx]
            if curr["type"] == "laptop":
                curr["val"] = min(100, curr["val"] + 5)
                DisplayBackend.set_laptop_brightness(curr["val"])
            elif curr["type"] == "ext_b":
                curr["val"] = min(100, curr["val"] + 5)
                ddc_worker.queue_vcp(curr["disp"], 10, curr["val"], curr["conn"])
            elif curr["type"] == "ext_c":
                curr["val"] = min(100, curr["val"] + 5)
                ddc_worker.queue_vcp(curr["disp"], 12, curr["val"], curr["conn"])
            elif curr["type"] == "night":
                curr["val"] = min(6500, curr["val"] + 200)
                if NightLightBackend.is_active():
                    NightLightBackend.start(curr["val"])
        elif ch in [ord(' '), 10, 13]:
            curr = items[idx]
            if curr["type"] == "night":
                NightLightBackend.toggle(curr["val"])


# =============================================================================
# FUZZEL / WOFI MENU FALLBACK (--menu)
# =============================================================================

def launch_dmenu():
    laptop_pct, laptop_dev, ext_monitors = DisplayBackend.get_instant_displays()

    options = []
    if laptop_pct is not None:
        options.append(f"☀️ Built-in Display: {laptop_pct}%")
        options.append("  [+] Laptop Brightness +10%")
        options.append("  [-] Laptop Brightness -10%")
        options.append("  [=] Laptop 100% (Max)")
        options.append("  [=] Laptop 50% (Medium)")
        options.append("  [=] Laptop 20% (Dim)")

    for mon in ext_monitors:
        options.append(f"🖥️ {mon['name']} (DDC/CI)")
        options.append(f"  [+] Ext Brightness +10% (Now: {mon['brightness']}%)")
        options.append(f"  [-] Ext Brightness -10% (Now: {mon['brightness']}%)")
        options.append(f"  [+] Ext Contrast +10% (Now: {mon['contrast']}%)")
        options.append(f"  [-] Ext Contrast -10% (Now: {mon['contrast']}%)")

    nl_state = "ON" if NightLightBackend.is_active() else "OFF"
    options.append(f"🌙 Night Light: {nl_state} (Toggle)")
    options.append("🖥️ Screen Resolution & Scaling Manager")

    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", " 󰃠 Display Controls: ", "--width", "42", "--lines", "12"]
    else:
        cmd = ["wofi", "--dmenu", "--prompt", "Display Controls", "--width", "450", "--height", "400", "--allow-markup"]

    try:
        proc = subprocess.run(cmd, input="\n".join(options), text=True, capture_output=True)
        chosen = proc.stdout.strip()
    except Exception:
        return

    if not chosen:
        return

    if "Laptop Brightness +10%" in chosen:
        DisplayBackend.set_laptop_brightness((laptop_pct or 50) + 10)
    elif "Laptop Brightness -10%" in chosen:
        DisplayBackend.set_laptop_brightness((laptop_pct or 50) - 10)
    elif "Laptop 100%" in chosen:
        DisplayBackend.set_laptop_brightness(100)
    elif "Laptop 50%" in chosen:
        DisplayBackend.set_laptop_brightness(50)
    elif "Laptop 20%" in chosen:
        DisplayBackend.set_laptop_brightness(20)
    elif "Ext Brightness +10%" in chosen:
        if ext_monitors:
            ddc_worker.queue_vcp(ext_monitors[0]["display_num"], 10, ext_monitors[0]["brightness"] + 10, ext_monitors[0].get("connector"))
    elif "Ext Brightness -10%" in chosen:
        if ext_monitors:
            ddc_worker.queue_vcp(ext_monitors[0]["display_num"], 10, ext_monitors[0]["brightness"] - 10, ext_monitors[0].get("connector"))
    elif "Ext Contrast +10%" in chosen:
        if ext_monitors:
            ddc_worker.queue_vcp(ext_monitors[0]["display_num"], 12, ext_monitors[0]["contrast"] + 10, ext_monitors[0].get("connector"))
    elif "Ext Contrast -10%" in chosen:
        if ext_monitors:
            ddc_worker.queue_vcp(ext_monitors[0]["display_num"], 12, ext_monitors[0]["contrast"] - 10, ext_monitors[0].get("connector"))
    elif "Night Light" in chosen:
        NightLightBackend.toggle()
    elif "Screen Resolution" in chosen:
        subprocess.Popen(["/home/kunal/.config/hypr/scripts/resolution_menu.py"])


# =============================================================================
def get_active_monitor_info():
    cache = load_cache()
    laptop_pct, laptop_dev, ext_monitors = DisplayBackend.get_instant_displays()
    raw = run_cmd(["hyprctl", "-j", "monitors"])
    focused_name = None
    if raw:
        try:
            for m in json.loads(raw):
                if m.get("focused"):
                    focused_name = m.get("name")
                    break
        except Exception:
            pass

    if not focused_name:
        if ext_monitors:
            focused_name = ext_monitors[0]["connector"]
        else:
            focused_name = "eDP-1"

    if focused_name.startswith("eDP") or focused_name.startswith("LVDS"):
        return "internal", 0, focused_name, "Built-in Display", (laptop_pct if laptop_pct is not None else 50)
    else:
        for mon in ext_monitors:
            if mon["connector"] == focused_name:
                return "external", mon["display_num"], mon["connector"], mon["name"], mon["brightness"]
        if ext_monitors:
            return "external", ext_monitors[0]["display_num"], ext_monitors[0]["connector"], ext_monitors[0]["name"], ext_monitors[0]["brightness"]
        return "internal", 0, "eDP-1", "Built-in Display", (laptop_pct if laptop_pct is not None else 50)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["--gui", "-g"]:
        check_and_kill_existing()
        launch_gtk_gui()
        return

    arg = sys.argv[1].lower()
    if arg in ["--tui", "-t", "tui"]:
        curses.wrapper(launch_curses_tui)
    elif arg in ["--menu", "-m", "--dmenu", "menu"]:
        launch_dmenu()
    elif arg in ["up", "+"]:
        step = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        disp_type, disp_num, connector, disp_name, curr = get_active_monitor_info()
        new_val = min(100, curr + step)
        if disp_type == "internal":
            DisplayBackend.set_laptop_brightness(new_val)
            show_notification(f"☀️ Brightness: {new_val}%", f"<b>{disp_name}</b>\n{build_progress_bar(new_val)}", "display-brightness-high", percentage=new_val)
        else:
            ddc_worker.queue_vcp(disp_num, 10, new_val, connector)
            # Give debounce thread a tiny fraction of a second to start
            time.sleep(0.08)
            show_notification(f"🖥️ Brightness: {new_val}%", f"<b>{disp_name}</b>\n{build_progress_bar(new_val)}", "video-display", percentage=new_val)
        subprocess.run(["pkill", "-RTMIN+11", "waybar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif arg in ["down", "-"]:
        step = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        disp_type, disp_num, connector, disp_name, curr = get_active_monitor_info()
        new_val = max(1 if disp_type == "internal" else 0, curr - step)
        if disp_type == "internal":
            DisplayBackend.set_laptop_brightness(new_val)
            show_notification(f"☀️ Brightness: {new_val}%", f"<b>{disp_name}</b>\n{build_progress_bar(new_val)}", "display-brightness-low", percentage=new_val)
        else:
            ddc_worker.queue_vcp(disp_num, 10, new_val, connector)
            time.sleep(0.08)
            show_notification(f"🖥️ Brightness: {new_val}%", f"<b>{disp_name}</b>\n{build_progress_bar(new_val)}", "video-display", percentage=new_val)
        subprocess.run(["pkill", "-RTMIN+11", "waybar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif arg in ["set"]:
        if len(sys.argv) > 2:
            val = int(sys.argv[2])
            disp_type, disp_num, connector, disp_name, _ = get_active_monitor_info()
            if disp_type == "internal":
                DisplayBackend.set_laptop_brightness(val)
            else:
                ddc_worker.queue_vcp(disp_num, 10, val, connector)
                time.sleep(0.08)
            subprocess.run(["pkill", "-RTMIN+11", "waybar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif arg in ["nightlight", "night", "-n"]:
        NightLightBackend.toggle()
    else:
        check_and_kill_existing()
        launch_gtk_gui()


if __name__ == "__main__":
    main()
