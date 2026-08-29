#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha System Hardware & Stats Dashboard for Waybar & Hyprland
 High-contrast, polished GTK LayerShell popup displaying live CPU, Memory,
 Disk, all Hardware Temperature Sensors, Uptime and Top Active Processes
 with 90% screen height adaptation and smooth scrolling support.
=============================================================================
"""

import json
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


def get_screen_dimensions():
    try:
        out = subprocess.run(["hyprctl", "-j", "monitors"], capture_output=True, text=True).stdout
        monitors = json.loads(out)
        for m in monitors:
            if m.get("focused", False) or len(monitors) == 1:
                scale = float(m.get("scale", 1.0))
                h = int(float(m.get("height", 1080)) / scale)
                w = int(float(m.get("width", 1920)) / scale)
                return w, h
    except Exception:
        pass

    try:
        import gi
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gdk
        s = Gdk.Screen.get_default()
        if s:
            return s.get_width(), s.get_height()
    except Exception:
        pass

    return 1920, 1080


def get_cpu_info():
    model = "CPU"
    cores = os.cpu_count() or 1
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    model = line.split(":", 1)[1].strip()
                    model = re.sub(r'\(R\)|\(TM\)|Processor|CPU|Core|Eight-Core|Six-Core|Quad-Core', '', model).strip()
                    model = re.sub(r'\s+', ' ', model)
                    break
    except Exception:
        pass

    def read_stat():
        try:
            with open("/proc/stat", "r") as f:
                first_line = f.readline()
                parts = [float(x) for x in first_line.split()[1:8]]
                idle = parts[3] + parts[4]
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


def get_all_temperatures():
    raw_sensors = []

    # 1. Inspect hwmon devices
    hwmon_dir = "/sys/class/hwmon"
    if os.path.exists(hwmon_dir):
        for h in sorted(os.listdir(hwmon_dir)):
            h_path = os.path.join(hwmon_dir, h)
            name_file = os.path.join(h_path, "name")
            h_name = ""
            if os.path.exists(name_file):
                try:
                    with open(name_file) as f:
                        h_name = f.read().strip()
                except Exception:
                    pass

            for entry in sorted(os.listdir(h_path)):
                if entry.startswith("temp") and entry.endswith("_input"):
                    prefix = entry[:-6]
                    input_file = os.path.join(h_path, entry)
                    label_file = os.path.join(h_path, f"{prefix}_label")
                    label = ""
                    if os.path.exists(label_file):
                        try:
                            with open(label_file) as f:
                                label = f.read().strip()
                        except Exception:
                            pass

                    if not label:
                        label = f"{h_name} {prefix}".strip()

                    try:
                        with open(input_file) as f:
                            val = int(f.read().strip())
                            if 5000 < val < 130000:
                                temp_c = round(val / 1000)
                                raw_sensors.append({
                                    "device": h_name,
                                    "label": label,
                                    "temp_c": temp_c
                                })
                    except Exception:
                        pass

    # 2. Inspect thermal zones
    has_cpu_pkg = any("package" in s["label"].lower() or "core" in s["label"].lower() for s in raw_sensors)
    tz_dir = "/sys/class/thermal"
    if os.path.exists(tz_dir):
        for tz in sorted(os.listdir(tz_dir)):
            if tz.startswith("thermal_zone"):
                tz_path = os.path.join(tz_dir, tz)
                type_file = os.path.join(tz_path, "type")
                temp_file = os.path.join(tz_path, "temp")
                tz_type = tz
                if os.path.exists(type_file):
                    try:
                        with open(type_file) as f:
                            tz_type = f.read().strip()
                    except Exception:
                        pass
                if os.path.exists(temp_file):
                    try:
                        with open(temp_file) as f:
                            val = int(f.read().strip())
                            if 15000 < val < 130000:
                                if has_cpu_pkg and tz_type in ("x86_pkg_temp", "TCPU"):
                                    continue
                                raw_sensors.append({
                                    "device": "Thermal",
                                    "label": tz_type,
                                    "temp_c": round(val / 1000)
                                })
                    except Exception:
                        pass

    # Normalize labels & deduplicate
    clean_sensors = []
    seen_labels = set()
    for s in raw_sensors:
        lbl = s["label"]
        dev = s["device"].lower()
        if "package id" in lbl.lower():
            friendly = "CPU Pkg"
        elif "core " in lbl.lower():
            friendly = lbl.title()
        elif "composite" in lbl.lower() or (dev == "nvme" and "sensor" not in lbl.lower()):
            friendly = "NVMe SSD"
        elif dev == "nvme" and "sensor 1" in lbl.lower():
            continue
        elif "int3400" in lbl.lower():
            friendly = "Ambient"
        elif lbl.upper() in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5"):
            friendly = f"Sensor {lbl[-1]}"
        else:
            friendly = lbl.title()

        if friendly not in seen_labels:
            seen_labels.add(friendly)
            clean_sensors.append({
                "device": s["device"],
                "label": friendly,
                "temp_c": s["temp_c"]
            })

    max_c = max([s["temp_c"] for s in clean_sensors], default=45)

    status = "Normal"
    status_class = "temp-good"
    if max_c >= 80:
        status = "Critical"
        status_class = "temp-critical"
    elif max_c >= 65:
        status = "Warm"
        status_class = "temp-warm"

    return {
        "sensors": clean_sensors,
        "max_c": max_c,
        "status": status,
        "class": status_class
    }


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
            ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
            capture_output=True, text=True, check=False
        )
        lines = res.stdout.strip().splitlines()
        procs = []
        for line in lines[1:6]:  # Show top 5 processes
            parts = line.split()
            if len(parts) >= 4:
                pid, comm, cpu, mem = parts[0], parts[1], parts[2], parts[3]
                try:
                    cpu_f = float(cpu)
                    mem_f = float(mem)
                except Exception:
                    cpu_f, mem_f = 0.0, 0.0
                procs.append({
                    "pid": pid,
                    "name": comm,
                    "cpu": f"{cpu_f:.1f}%",
                    "mem": f"{mem_f:.1f}%"
                })
        return procs
    except Exception:
        return []


CSS = """
* {
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", "RobotoMono Nerd Font", monospace;
}

window {
    background-color: transparent;
}

scrolledwindow,
.scrolled-window {
    background-color: transparent;
    border: none;
    padding: 0;
    margin: 0;
}

scrollbar {
    background-color: transparent;
    border: none;
    -GtkScrollbar-has-backward-stepper: false;
    -GtkScrollbar-has-forward-stepper: false;
    min-width: 6px;
}

scrollbar trough {
    background-color: transparent;
    border: none;
}

scrollbar slider {
    background-color: rgba(203, 166, 247, 0.4);
    border-radius: 6px;
    min-width: 5px;
    border: none;
}

scrollbar slider:hover {
    background-color: #cba6f7;
}

button {
    background-image: none;
    background-color: transparent;
    box-shadow: none;
    text-shadow: none;
    border: none;
    outline: none;
}

button:focus {
    box-shadow: none;
    outline: none;
}

.main-card {
    background-color: #181825;
    border: 1.5px solid rgba(203, 166, 247, 0.45);
    border-radius: 18px;
    padding: 16px 20px;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.7);
}

.header-icon {
    font-size: 20px;
    color: #cba6f7;
    margin-right: 8px;
}

.header-title {
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
}

.header-subtitle {
    font-size: 11px;
    font-weight: 600;
    color: #cdd6f4;
    margin-top: 2px;
    margin-bottom: 10px;
}

.stat-box {
    background-color: #1e1e2e;
    border: 1.5px solid #313244;
    border-radius: 13px;
    padding: 9px 13px;
    margin-bottom: 7px;
}

.stat-box:hover {
    border-color: rgba(203, 166, 247, 0.4);
    background-color: #24253a;
}

.stat-icon {
    font-size: 16px;
    margin-right: 8px;
}

.stat-name {
    font-size: 12.5px;
    font-weight: 800;
    color: #ffffff;
}

.stat-value {
    font-size: 12.5px;
    font-weight: 800;
}

.stat-desc {
    font-size: 10.5px;
    font-weight: 600;
    color: #cdd6f4;
    margin-top: 2px;
    margin-bottom: 5px;
}

/* Progress bar styling */
progressbar {
    border-radius: 5px;
    min-height: 6px;
}

progressbar trough {
    background-color: #313244;
    border-radius: 5px;
    min-height: 6px;
}

progressbar progress {
    border-radius: 5px;
    min-height: 6px;
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
.color-proc { color: #cba6f7; }

.temp-good { color: #a6e3a1; }
.temp-warm { color: #fab387; }
.temp-critical { color: #f38ba8; }

/* Thermal Pill Badges */
.temp-grid {
    margin-top: 5px;
    margin-bottom: 2px;
}

.temp-pill {
    background-color: #181825;
    border: 1.5px solid #313244;
    border-radius: 8px;
    padding: 3px 8px;
    margin: 2px 2px;
}

.temp-pill-label {
    font-size: 10.5px;
    font-weight: 600;
    color: #cdd6f4;
    margin-right: 5px;
}

.temp-pill-val {
    font-size: 10.5px;
    font-weight: 800;
}

/* Top Process Rows */
.proc-item {
    background-color: #181825;
    border: 1.5px solid #313244;
    border-radius: 8px;
    padding: 4px 8px;
    margin-top: 3px;
}

.proc-item:hover {
    border-color: #45475a;
    background-color: #24253a;
}

.proc-name {
    font-size: 11.5px;
    font-weight: 800;
    color: #ffffff;
}

.proc-pid {
    font-size: 9.5px;
    font-weight: 500;
    color: #a6adc8;
    margin-left: 5px;
}

.proc-cpu-badge {
    font-size: 10.5px;
    font-weight: 800;
    color: #fab387;
    background-color: #313244;
    border-radius: 5px;
    padding: 1px 6px;
    margin-left: 5px;
}

.proc-mem-badge {
    font-size: 10.5px;
    font-weight: 800;
    color: #f5c2e7;
    background-color: #313244;
    border-radius: 5px;
    padding: 1px 6px;
    margin-left: 4px;
}

/* Action Button - High Contrast Styling */
.action-btn {
    background-color: #1e1e2e;
    border: 1.5px solid #cba6f7;
    border-radius: 12px;
    padding: 9px 14px;
    margin-top: 5px;
    transition: all 0.15s ease-in-out;
}

.action-btn:focus {
    background-color: #1e1e2e;
    border: 1.5px solid #cba6f7;
}

.action-btn:hover {
    background-color: #cba6f7;
    border-color: #cba6f7;
}

.action-btn .action-btn-text {
    font-size: 12.5px;
    font-weight: 800;
    color: #ffffff;
}

.action-btn .action-btn-icon {
    font-size: 15px;
    font-weight: 800;
    color: #cba6f7;
    margin-right: 8px;
}

.action-btn:hover .action-btn-text,
.action-btn:hover .action-btn-icon {
    color: #11111b;
}
"""


def launch_gtk_gui():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, GtkLayerShell

    # Fetch screen dimensions
    screen_w, screen_h = get_screen_dimensions()
    target_popup_height = min(int(screen_h * 0.88), screen_h - 55)
    popup_width = 440

    # Fetch system metrics
    cpu = get_cpu_info()
    mem = get_memory_info()
    disk = get_disk_info("/")
    thermals = get_all_temperatures()
    sys_sum = get_system_summary()
    top_procs = get_top_processes()

    # Apply CSS
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(CSS.encode('utf-8'))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    # 1. Fullscreen Backdrop for outside click dismiss
    backdrop = Gtk.Window()
    backdrop.set_title("system-stats-backdrop")
    backdrop.set_decorated(False)
    backdrop.set_app_paintable(True)

    screen = backdrop.get_screen()
    visual = screen.get_rgba_visual() if screen else None
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
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 42)
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
    card.set_size_request(popup_width - 16, -1)

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
    cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
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
    cpu_desc.set_markup(f"{cpu['model']} ({cpu['cores']} Cores) • Load: <b>{cpu['load']}</b>")
    cpu_desc.set_xalign(0)
    cpu_desc.get_style_context().add_class("stat-desc")

    cpu_bar = Gtk.ProgressBar()
    cpu_bar.set_fraction(min(1.0, max(0.0, cpu['usage'] / 100.0)))
    cpu_bar.get_style_context().add_class("progress-cpu")

    cpu_box.pack_start(cpu_row, False, False, 0)
    cpu_box.pack_start(cpu_desc, False, False, 0)
    cpu_box.pack_start(cpu_bar, False, False, 0)
    card.pack_start(cpu_box, False, False, 0)

    # --- Memory & Disk Row ---
    mem_disk_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

    # Memory Box (Left)
    mem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    mem_box.get_style_context().add_class("stat-box")
    mem_box.set_hexpand(True)

    mem_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    mem_icon = Gtk.Label(label="󰘚")
    mem_icon.get_style_context().add_class("stat-icon")
    mem_icon.get_style_context().add_class("color-ram")
    mem_name = Gtk.Label(label="Memory")
    mem_name.get_style_context().add_class("stat-name")
    mem_val = Gtk.Label(label=f"{mem['pct']}%")
    mem_val.get_style_context().add_class("stat-value")
    mem_val.get_style_context().add_class("color-ram")

    mem_header.pack_start(mem_icon, False, False, 0)
    mem_header.pack_start(mem_name, False, False, 0)
    mem_header.pack_end(mem_val, False, False, 0)

    mem_desc = Gtk.Label()
    mem_desc.set_markup(f"<b>{mem['used_gib']}</b>/{mem['total_gib']} GiB • Swap: <b>{mem['swap_used_gib']}</b> GiB")
    mem_desc.set_xalign(0)
    mem_desc.get_style_context().add_class("stat-desc")

    mem_bar = Gtk.ProgressBar()
    mem_bar.set_fraction(min(1.0, max(0.0, mem['pct'] / 100.0)))
    mem_bar.get_style_context().add_class("progress-ram")

    mem_box.pack_start(mem_header, False, False, 0)
    mem_box.pack_start(mem_desc, False, False, 0)
    mem_box.pack_start(mem_bar, False, False, 0)
    mem_disk_row.pack_start(mem_box, True, True, 0)

    # Disk Box (Right)
    disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
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
    mem_disk_row.pack_start(disk_box, True, True, 0)

    card.pack_start(mem_disk_row, False, False, 0)

    # --- All Hardware Temperatures Box ---
    temp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    temp_box.get_style_context().add_class("stat-box")

    temp_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    temp_icon = Gtk.Label(label="󰔏")
    temp_icon.get_style_context().add_class("stat-icon")
    temp_icon.get_style_context().add_class("color-temp")
    temp_title = Gtk.Label(label="Hardware Temperatures")
    temp_title.get_style_context().add_class("stat-name")
    temp_val = Gtk.Label(label=f"{thermals['max_c']}°C • {thermals['status']}")
    temp_val.get_style_context().add_class("stat-value")
    temp_val.get_style_context().add_class(thermals["class"])

    temp_header.pack_start(temp_icon, False, False, 0)
    temp_header.pack_start(temp_title, False, False, 0)
    temp_header.pack_end(temp_val, False, False, 0)
    temp_box.pack_start(temp_header, False, False, 0)

    # FlowBox of temperature pills
    temp_flow = Gtk.FlowBox()
    temp_flow.set_valign(Gtk.Align.START)
    temp_flow.set_max_children_per_line(4)
    temp_flow.set_selection_mode(Gtk.SelectionMode.NONE)
    temp_flow.set_homogeneous(True)
    temp_flow.get_style_context().add_class("temp-grid")

    for sensor in thermals["sensors"]:
        pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        pill.get_style_context().add_class("temp-pill")

        s_lbl = Gtk.Label(label=sensor["label"])
        s_lbl.get_style_context().add_class("temp-pill-label")
        pill.pack_start(s_lbl, False, False, 0)

        t_val = sensor["temp_c"]
        color_cls = "temp-good" if t_val < 60 else ("temp-warm" if t_val < 80 else "temp-critical")
        v_lbl = Gtk.Label(label=f"{t_val}°C")
        v_lbl.get_style_context().add_class("temp-pill-val")
        v_lbl.get_style_context().add_class(color_cls)
        pill.pack_end(v_lbl, False, False, 0)

        temp_flow.add(pill)

    temp_box.pack_start(temp_flow, False, False, 0)
    card.pack_start(temp_box, False, False, 0)

    # --- Separate Top Processes Box ---
    proc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    proc_box.get_style_context().add_class("stat-box")

    proc_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    p_icon = Gtk.Label(label="󰒋")
    p_icon.get_style_context().add_class("stat-icon")
    p_icon.get_style_context().add_class("color-proc")
    p_title = Gtk.Label(label="Top Active Processes")
    p_title.get_style_context().add_class("stat-name")
    proc_header.pack_start(p_icon, False, False, 0)
    proc_header.pack_start(p_title, False, False, 0)
    proc_box.pack_start(proc_header, False, False, 0)

    for proc in top_procs:
        p_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        p_row.get_style_context().add_class("proc-item")

        p_name = Gtk.Label(label=proc["name"])
        p_name.get_style_context().add_class("proc-name")
        p_pid = Gtk.Label(label=f"PID {proc['pid']}")
        p_pid.get_style_context().add_class("proc-pid")

        p_row.pack_start(p_name, False, False, 0)
        p_row.pack_start(p_pid, False, False, 0)

        mem_badge = Gtk.Label(label=f"{proc['mem']} RAM")
        mem_badge.get_style_context().add_class("proc-mem-badge")
        cpu_badge = Gtk.Label(label=f"{proc['cpu']} CPU")
        cpu_badge.get_style_context().add_class("proc-cpu-badge")

        p_row.pack_end(mem_badge, False, False, 0)
        p_row.pack_end(cpu_badge, False, False, 0)

        proc_box.pack_start(p_row, False, False, 0)

    card.pack_start(proc_box, False, False, 0)

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

    # --- Scrolled Window Container utilizing ~90% Screen Height ---
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_propagate_natural_width(True)
    scrolled.set_propagate_natural_height(False)
    scrolled.set_min_content_height(target_popup_height)
    scrolled.set_max_content_height(target_popup_height)
    scrolled.get_style_context().add_class("scrolled-window")
    scrolled.add(card)

    win.set_size_request(popup_width, target_popup_height)
    win.set_default_size(popup_width, target_popup_height)
    win.add(scrolled)
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
