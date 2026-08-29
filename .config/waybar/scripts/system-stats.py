#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha System Hardware & Stats Dashboard for Waybar & Hyprland
 High-contrast, polished GTK LayerShell popup displaying live CPU, Memory,
 Disk, Temperature, Uptime and top processes with outside-click dismissal.
=============================================================================
"""

import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time


def check_and_kill_existing():
    my_pid = os.getpid()
    try:
        out = subprocess.run(["pgrep", "-f", "system-stats.py"], capture_output=True, text=True).stdout
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


def get_cpu_info():
    model = "CPU"
    cores = os.cpu_count() or 1
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    model = line.split(":", 1)[1].strip()
                    # Shorten verbose CPU names
                    model = re.sub(r'\(R\)|\(TM\)|Processor|CPU|Core|Eight-Core|Six-Core|Quad-Core', '', model).strip()
                    model = re.sub(r'\s+', ' ', model)
                    break
    except Exception:
        pass

    # Read /proc/stat for accurate CPU usage percentage
    def read_stat():
        try:
            with open("/proc/stat", "r") as f:
                first_line = f.readline()
                parts = [float(x) for x in first_line.split()[1:8]]
                idle = parts[3] + parts[4]  # idle + iowait
                total = sum(parts)
                return idle, total
        except Exception:
            return 0.0, 1.0

    idle1, total1 = read_stat()
    time.sleep(0.08)
    idle2, total2 = read_stat()
    
    total_diff = total2 - total1
    idle_diff = idle2 - idle1
    cpu_pct = 0.0
    if total_diff > 0:
        cpu_pct = max(0.0, min(100.0, ((total_diff - idle_diff) / total_diff) * 100.0))

    try:
        load1, load5, load15 = os.getloadavg()
    except Exception:
        load1, load5, load15 = 0.0, 0.0, 0.0

    return {
        "model": model,
        "cores": cores,
        "usage": round(cpu_pct, 1),
        "load": f"{load1:.2f}, {load5:.2f}, {load15:.2f}"
    }


def get_memory_info():
    mem_total = 0
    mem_avail = 0
    swap_total = 0
    swap_free = 0

    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                key = parts[0].strip()
                val = int(parts[1].split()[0])
                if key == "MemTotal":
                    mem_total = val
                elif key == "MemAvailable":
                    mem_avail = val
                elif key == "SwapTotal":
                    swap_total = val
                elif key == "SwapFree":
                    swap_free = val
    except Exception:
        pass

    mem_used = max(0, mem_total - mem_avail)
    mem_pct = (mem_used / mem_total * 100) if mem_total > 0 else 0.0

    swap_used = max(0, swap_total - swap_free)
    swap_pct = (swap_used / swap_total * 100) if swap_total > 0 else 0.0

    return {
        "used_gib": round(mem_used / (1024 * 1024), 2),
        "total_gib": round(mem_total / (1024 * 1024), 2),
        "pct": round(mem_pct, 1),
        "swap_used_gib": round(swap_used / (1024 * 1024), 2),
        "swap_total_gib": round(swap_total / (1024 * 1024), 2),
        "swap_pct": round(swap_pct, 1)
    }


def get_disk_info(path="/"):
    try:
        total, used, free = shutil.disk_usage(path)
        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        pct = (used / total) * 100 if total > 0 else 0.0
        return {
            "path": path,
            "used_gb": round(used_gb, 1),
            "total_gb": round(total_gb, 1),
            "free_gb": round(free_gb, 1),
            "pct": round(pct, 1)
        }
    except Exception:
        return {"path": path, "used_gb": 0, "total_gb": 0, "free_gb": 0, "pct": 0}


def get_temp_info():
    temp_c = 0
    # Try thermal zones
    for zone in range(10):
        t_path = f"/sys/class/thermal/thermal_zone{zone}/temp"
        if os.path.exists(t_path):
            try:
                with open(t_path, "r") as f:
                    val = int(f.read().strip())
                    if val > 0:
                        temp_c = round(val / 1000)
                        break
            except Exception:
                pass

    status = "Normal"
    color_class = "temp-good"
    if temp_c >= 80:
        status = "Critical"
        color_class = "temp-critical"
    elif temp_c >= 65:
        status = "Warm"
        color_class = "temp-warm"

    return {"temp_c": temp_c, "status": status, "class": color_class}


def get_system_summary():
    uptime_str = "Unknown"
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.readline().split()[0])
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            days = hours // 24
            if days > 0:
                uptime_str = f"{days}d {hours % 24}h {mins}m"
            else:
                uptime_str = f"{hours}h {mins}m"
    except Exception:
        pass

    host = platform.node() or "ArchLinux"
    kernel = platform.release().split("-")[0]
    return {
        "hostname": host,
        "kernel": kernel,
        "uptime": uptime_str
    }


def get_top_processes():
    try:
        res = subprocess.run(
            ["ps", "-eo", "comm,%cpu,%mem", "--sort=-%cpu"],
            capture_output=True, text=True, check=False
        )
        lines = res.stdout.strip().splitlines()
        top_procs = []
        for line in lines[1:4]:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                cpu = parts[1]
                top_procs.append(f"{name} ({cpu}%)")
        return ", ".join(top_procs) if top_procs else "None"
    except Exception:
        return "N/A"


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
    padding: 18px 22px;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.7);
}

.header-icon {
    font-size: 22px;
    color: #cba6f7;
    margin-right: 8px;
}

.header-title {
    font-size: 16px;
    font-weight: 800;
    color: #cdd6f4;
}

.header-subtitle {
    font-size: 11px;
    font-weight: 600;
    color: #a6adc8;
    margin-top: 2px;
    margin-bottom: 14px;
}

.stat-box {
    background-color: #1e1e2e;
    border: 1.5px solid #313244;
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.stat-box:hover {
    border-color: rgba(203, 166, 247, 0.4);
    background-color: #24253a;
}

.stat-icon {
    font-size: 18px;
    margin-right: 10px;
}

.stat-name {
    font-size: 13px;
    font-weight: 800;
    color: #cdd6f4;
}

.stat-value {
    font-size: 13px;
    font-weight: 800;
}

.stat-desc {
    font-size: 11px;
    font-weight: 500;
    color: #a6adc8;
    margin-top: 2px;
    margin-bottom: 6px;
}

/* Progress bar styling */
progressbar {
    border-radius: 6px;
    min-height: 8px;
}

progressbar trough {
    background-color: #313244;
    border-radius: 6px;
    min-height: 8px;
}

progressbar progress {
    border-radius: 6px;
    min-height: 8px;
}

.progress-cpu progress {
    background: linear-gradient(90deg, #89b4fa, #74c7ec);
}

.progress-ram progress {
    background: linear-gradient(90deg, #f5c2e7, #cba6f7);
}

.progress-disk progress {
    background: linear-gradient(90deg, #94e2d5, #a6e3a1);
}

.color-cpu { color: #89b4fa; }
.color-ram { color: #f5c2e7; }
.color-disk { color: #94e2d5; }
.color-temp { color: #fab387; }

.temp-good { color: #a6e3a1; }
.temp-warm { color: #fab387; }
.temp-critical { color: #f38ba8; }

.action-btn {
    background-color: #313244;
    border: 1.5px solid rgba(203, 166, 247, 0.3);
    border-radius: 12px;
    padding: 10px 14px;
    margin-top: 4px;
    transition: all 0.15s ease-in-out;
}

.action-btn:hover {
    background-color: #cba6f7;
    border-color: #cba6f7;
}

.action-btn:hover label {
    color: #11111b;
    font-weight: 800;
}

.action-btn-text {
    font-size: 13px;
    font-weight: 700;
    color: #cdd6f4;
}

.action-btn-icon {
    font-size: 15px;
    margin-right: 8px;
}
"""


def launch_gtk_gui():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, GtkLayerShell

    # Fetch stats
    cpu = get_cpu_info()
    mem = get_memory_info()
    disk = get_disk_info("/")
    temp = get_temp_info()
    sys_sum = get_system_summary()
    top_proc = get_top_processes()

    # Apply CSS
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS.encode('utf-8'))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    # 1. Transparent Backdrop for outside-click dismissal
    backdrop = Gtk.Window()
    backdrop.set_title("system-stats-backdrop")
    backdrop.set_decorated(False)
    backdrop.set_app_paintable(True)

    screen = backdrop.get_screen()
    visual = screen.get_rgba_visual()
    if visual:
        backdrop.set_visual(visual)

    GtkLayerShell.init_for_window(backdrop)
    GtkLayerShell.set_layer(backdrop, GtkLayerShell.Layer.TOP)
    GtkLayerShell.set_namespace(backdrop, "system-stats-backdrop")
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
    win.set_title("system-stats-popup")
    win.set_decorated(False)
    win.set_app_paintable(True)
    if visual:
        win.set_visual(visual)

    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_namespace(win, "system-stats-popup")
    GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.ON_DEMAND)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT, True)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 48)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.RIGHT, 14)

    def on_key_press(widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    win.connect("key-press-event", on_key_press)

    # Main Card Container
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    card.get_style_context().add_class("main-card")
    card.set_size_request(380, -1)

    # --- Header Box ---
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    h_icon = Gtk.Label(label="󰍛")
    h_icon.get_style_context().add_class("header-icon")
    h_title = Gtk.Label(label="System Hardware & Stats")
    h_title.get_style_context().add_class("header-title")
    header_box.pack_start(h_icon, False, False, 0)
    header_box.pack_start(h_title, False, False, 0)

    sub_label = Gtk.Label()
    sub_label.set_markup(f"<b>{sys_sum['hostname']}</b> • Linux {sys_sum['kernel']} • Uptime: <b>{sys_sum['uptime']}</b>")
    sub_label.set_xalign(0)
    sub_label.get_style_context().add_class("header-subtitle")

    card.pack_start(header_box, False, False, 0)
    card.pack_start(sub_label, False, False, 0)

    # --- CPU Box ---
    cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    cpu_box.get_style_context().add_class("stat-box")

    cpu_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    cpu_icon = Gtk.Label(label="󰍛")
    cpu_icon.get_style_context().add_class("stat-icon")
    cpu_icon.get_style_context().add_class("color-cpu")
    cpu_name = Gtk.Label(label="CPU Utilization")
    cpu_name.get_style_context().add_class("stat-name")
    cpu_val = Gtk.Label(label=f"{cpu['usage']}%")
    cpu_val.get_style_context().add_class("stat-value")
    cpu_val.get_style_context().add_class("color-cpu")

    cpu_row.pack_start(cpu_icon, False, False, 0)
    cpu_row.pack_start(cpu_name, False, False, 0)
    cpu_row.pack_end(cpu_val, False, False, 0)

    cpu_desc = Gtk.Label()
    cpu_desc.set_markup(f"{cpu['model']} ({cpu['cores']} Cores) • Load: {cpu['load']}")
    cpu_desc.set_xalign(0)
    cpu_desc.get_style_context().add_class("stat-desc")

    cpu_bar = Gtk.ProgressBar()
    cpu_bar.set_fraction(min(1.0, max(0.0, cpu['usage'] / 100.0)))
    cpu_bar.get_style_context().add_class("progress-cpu")

    cpu_box.pack_start(cpu_row, False, False, 0)
    cpu_box.pack_start(cpu_desc, False, False, 0)
    cpu_box.pack_start(cpu_bar, False, False, 0)
    card.pack_start(cpu_box, False, False, 0)

    # --- Memory Box ---
    mem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    mem_box.get_style_context().add_class("stat-box")

    mem_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    mem_icon = Gtk.Label(label="󰘚")
    mem_icon.get_style_context().add_class("stat-icon")
    mem_icon.get_style_context().add_class("color-ram")
    mem_name = Gtk.Label(label="Memory (RAM & Swap)")
    mem_name.get_style_context().add_class("stat-name")
    mem_val = Gtk.Label(label=f"{mem['pct']}%")
    mem_val.get_style_context().add_class("stat-value")
    mem_val.get_style_context().add_class("color-ram")

    mem_row.pack_start(mem_icon, False, False, 0)
    mem_row.pack_start(mem_name, False, False, 0)
    mem_row.pack_end(mem_val, False, False, 0)

    mem_desc = Gtk.Label()
    mem_desc.set_markup(f"RAM: <b>{mem['used_gib']} GiB</b> / {mem['total_gib']} GiB • Swap: <b>{mem['swap_used_gib']} GiB</b> / {mem['swap_total_gib']} GiB")
    mem_desc.set_xalign(0)
    mem_desc.get_style_context().add_class("stat-desc")

    mem_bar = Gtk.ProgressBar()
    mem_bar.set_fraction(min(1.0, max(0.0, mem['pct'] / 100.0)))
    mem_bar.get_style_context().add_class("progress-ram")

    mem_box.pack_start(mem_row, False, False, 0)
    mem_box.pack_start(mem_desc, False, False, 0)
    mem_box.pack_start(mem_bar, False, False, 0)
    card.pack_start(mem_box, False, False, 0)

    # --- Storage & Temperature Dual Box ---
    bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

    # Disk Box (Left)
    disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    disk_box.get_style_context().add_class("stat-box")
    disk_box.set_hexpand(True)

    disk_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    disk_icon = Gtk.Label(label="󰋊")
    disk_icon.get_style_context().add_class("stat-icon")
    disk_icon.get_style_context().add_class("color-disk")
    disk_title = Gtk.Label(label="Disk (/)")
    disk_title.get_style_context().add_class("stat-name")
    disk_val = Gtk.Label(label=f"{disk['pct']}%")
    disk_val.get_style_context().add_class("stat-value")
    disk_val.get_style_context().add_class("color-disk")

    disk_header.pack_start(disk_icon, False, False, 0)
    disk_header.pack_start(disk_title, False, False, 0)
    disk_header.pack_end(disk_val, False, False, 0)

    disk_desc = Gtk.Label()
    disk_desc.set_markup(f"Free: <b>{disk['free_gb']} GB</b> / {disk['total_gb']} GB")
    disk_desc.set_xalign(0)
    disk_desc.get_style_context().add_class("stat-desc")

    disk_bar = Gtk.ProgressBar()
    disk_bar.set_fraction(min(1.0, max(0.0, disk['pct'] / 100.0)))
    disk_bar.get_style_context().add_class("progress-disk")

    disk_box.pack_start(disk_header, False, False, 0)
    disk_box.pack_start(disk_desc, False, False, 0)
    disk_box.pack_start(disk_bar, False, False, 0)
    bottom_row.pack_start(disk_box, True, True, 0)

    # Temperature Box (Right)
    temp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    temp_box.get_style_context().add_class("stat-box")
    temp_box.set_hexpand(True)

    temp_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    temp_icon = Gtk.Label(label="󰔏")
    temp_icon.get_style_context().add_class("stat-icon")
    temp_icon.get_style_context().add_class("color-temp")
    temp_title = Gtk.Label(label="Temperature")
    temp_title.get_style_context().add_class("stat-name")
    temp_val = Gtk.Label(label=f"{temp['temp_c']}°C")
    temp_val.get_style_context().add_class("stat-value")
    temp_val.get_style_context().add_class(temp["class"])

    temp_header.pack_start(temp_icon, False, False, 0)
    temp_header.pack_start(temp_title, False, False, 0)
    temp_header.pack_end(temp_val, False, False, 0)

    temp_desc = Gtk.Label()
    temp_desc.set_markup(f"Thermal State: <b>{temp['status']}</b>")
    temp_desc.set_xalign(0)
    temp_desc.get_style_context().add_class("stat-desc")

    top_label = Gtk.Label()
    top_label.set_markup(f"Top: <small>{top_proc}</small>")
    top_label.set_xalign(0)
    top_label.get_style_context().add_class("stat-desc")

    temp_box.pack_start(temp_header, False, False, 0)
    temp_box.pack_start(temp_desc, False, False, 0)
    temp_box.pack_start(top_label, False, False, 0)
    bottom_row.pack_start(temp_box, True, True, 0)

    card.pack_start(bottom_row, False, False, 0)

    # --- Footer / Btop Action Button ---
    btop_btn = Gtk.Button()
    btop_btn.get_style_context().add_class("action-btn")

    btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    b_icon = Gtk.Label(label="󰞷")
    b_icon.get_style_context().add_class("action-btn-icon")
    b_text = Gtk.Label(label="Launch Btop Task Monitor (Right-Click)")
    b_text.get_style_context().add_class("action-btn-text")
    btn_box.pack_start(b_icon, False, False, 0)
    btn_box.pack_start(b_text, False, False, 0)
    btop_btn.add(btn_box)

    def on_btop_clicked(widget):
        subprocess.Popen(["kitty", "--class", "btop", "-e", "btop"])
        Gtk.main_quit()

    btop_btn.connect("clicked", on_btop_clicked)
    card.pack_start(btop_btn, False, False, 0)

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
