#!/usr/bin/env python3
"""
Hyprland Screen Brightness Control Utility with OSD & Interactive Menu
Supports laptop internal backlight (brightnessctl) and external monitors (ddcutil).
Provides active-screen awareness based on Hyprland focused monitor & cursor location.
"""

import sys
import subprocess
import os
import shutil
import re
import json
import time
import glob

BRIGHTNESS_NOTIF_ID = "9124"
DEFAULT_STEP = 5
CACHE_FILE = os.path.expanduser("~/.cache/quickshell_brightness_cache.json")

def run_cmd(cmd, timeout=2):
    """Run a shell command and return stdout as string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return res.stdout.strip()
    except Exception:
        return ""

def build_progress_bar(percentage, length=12):
    """Generate a visual ASCII progress bar."""
    pct = max(0, min(100, percentage))
    filled = int(round((pct / 100.0) * length))
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"

def show_notification(title, body, icon, percentage=None, notif_id=BRIGHTNESS_NOTIF_ID, tag="brightness_osd"):
    """Send an on-screen display (OSD) notification via notify-send without saving to history."""
    cmd = [
        "notify-send",
        "-r", str(notif_id),
        "-t", "1200",
        "-u", "low",
        "-a", "BrightnessControl",
        "-c", "osd",
        "-i", icon,
        "-h", f"string:x-canonical-private-synchronous:{tag}",
        "-h", "boolean:transient:true",
        "-h", "boolean:history-ignore:true"
    ]
    if percentage is not None:
        cmd.extend(["-h", f"int:value:{int(percentage)}"])
    
    cmd.extend([title, body])
    try:
        subprocess.Popen(cmd)
    except Exception:
        pass

# ---------------------------------------------------------
# Active Monitor Detection (Hyprland)
# ---------------------------------------------------------

def is_internal_name(name):
    """Check if display connector name represents an internal laptop panel."""
    name_upper = (name or "").upper()
    return name_upper.startswith("EDP") or name_upper.startswith("LVDS") or name_upper.startswith("DSI")

def get_active_monitor_info():
    """Detect the currently active/focused monitor in Hyprland."""
    raw = run_cmd(["hyprctl", "monitors", "-j"], timeout=1)
    if not raw:
        return {"name": "default", "is_internal": True, "description": "Display", "model": "Built-in Screen"}

    try:
        monitors = json.loads(raw)
    except Exception:
        return {"name": "default", "is_internal": True, "description": "Display", "model": "Built-in Screen"}

    if not monitors:
        return {"name": "default", "is_internal": True, "description": "Display", "model": "Built-in Screen"}

    # 1. First priority: Check monitor with focused == True
    for m in monitors:
        if m.get("focused"):
            name = m.get("name", "")
            is_int = is_internal_name(name)
            desc = m.get("description", "") or m.get("model", "") or name
            return {
                "name": name,
                "is_internal": is_int,
                "description": desc,
                "model": m.get("model", desc),
                "make": m.get("make", "")
            }

    # 2. Second priority: Match cursor coordinates with monitor geometry
    cursor_raw = run_cmd(["hyprctl", "cursorpos"], timeout=1)
    if cursor_raw and "," in cursor_raw:
        try:
            cx, cy = [int(v.strip()) for v in cursor_raw.split(",")]
            for m in monitors:
                x = m.get("x", 0)
                y = m.get("y", 0)
                w = m.get("width", 1920)
                h = m.get("height", 1080)
                if x <= cx < x + w and y <= cy < y + h:
                    name = m.get("name", "")
                    is_int = is_internal_name(name)
                    desc = m.get("description", "") or m.get("model", "") or name
                    return {
                        "name": name,
                        "is_internal": is_int,
                        "description": desc,
                        "model": m.get("model", desc),
                        "make": m.get("make", "")
                    }
        except Exception:
            pass

    # Default to the first monitor
    first = monitors[0]
    name = first.get("name", "")
    return {
        "name": name,
        "is_internal": is_internal_name(name),
        "description": first.get("description", name),
        "model": first.get("model", name),
        "make": first.get("make", "")
    }

# ---------------------------------------------------------
# Laptop Screen Backlight (brightnessctl)
# ---------------------------------------------------------

def get_brightness_info():
    """Retrieve current internal brightness percentage and device name."""
    raw = run_cmd(["brightnessctl", "-m"], timeout=1)
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
                dev_label = "Laptop Screen"
                if "intel" in dev or "amdgpu" in dev or "nvidia" in dev:
                    dev_label = "Built-in Display"
                return pct, dev_label
    return 50, "Display"

def notify_brightness_osd(device_label=None, target_pct=None):
    """Display OSD notification for screen brightness."""
    pct, dev = get_brightness_info()
    if target_pct is not None:
        pct = target_pct
    if device_label:
        dev = device_label
    bar = build_progress_bar(pct)

    if pct <= 33:
        icon = "display-brightness-low"
    elif pct <= 66:
        icon = "display-brightness-medium"
    else:
        icon = "display-brightness-high"

    title = f"☀️ Brightness: {pct}%"
    body = f"<b>{dev}</b>\n{bar}"
    show_notification(title, body, icon, percentage=pct, tag="brightness_osd")

def change_brightness(delta):
    """Adjust laptop display brightness by delta percentage."""
    if delta > 0:
        run_cmd(["brightnessctl", "set", f"{delta}%+"])
    else:
        run_cmd(["brightnessctl", "set", f"{abs(delta)}%-"])
    notify_brightness_osd()

def set_brightness(target_percent):
    """Set exact brightness percentage."""
    target_percent = max(1, min(100, target_percent))
    run_cmd(["brightnessctl", "set", f"{target_percent}%"])
    notify_brightness_osd(target_pct=target_percent)

# ---------------------------------------------------------
# External Monitor Brightness & Contrast (ddcutil)
# ---------------------------------------------------------

def load_cache():
    """Load cached monitor states."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(data):
    """Save monitor states to cache."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def get_i2c_bus_for_connector(connector_name):
    if not connector_name:
        return None
    for p in glob.glob(f"/sys/class/drm/*-{connector_name}/ddc"):
        try:
            target = os.path.realpath(p)
            base = os.path.basename(target)
            if base.startswith("i2c-"):
                return int(base.split("-")[-1])
        except Exception:
            pass
    for p in glob.glob(f"/sys/class/drm/*{connector_name}*/ddc"):
        try:
            target = os.path.realpath(p)
            base = os.path.basename(target)
            if base.startswith("i2c-"):
                return int(base.split("-")[-1])
        except Exception:
            pass
    return None

def get_ddc_bus(screen_name=None):
    """Find the active DDC bus from connector name, cache or discovery."""
    target_screen = screen_name
    if not target_screen:
        mon = get_active_monitor_info()
        if not mon["is_internal"]:
            target_screen = mon.get("name")

    mapped_bus = get_i2c_bus_for_connector(target_screen) if target_screen else None

    cache = load_cache()
    monitors = cache.get("monitors", [])
    if monitors:
        for m in monitors:
            if mapped_bus is not None and m.get("bus") == mapped_bus:
                return m.get("bus"), m.get("model", "External Monitor"), m.get("brightness", 50), m.get("contrast", 50)
            if target_screen and str(m.get("name")) == str(target_screen):
                return m.get("bus", 1), m.get("model", "External Monitor"), m.get("brightness", 50), m.get("contrast", 50)
        # Fallback to first monitor in cache
        first = monitors[0]
        if first.get("bus") is not None:
            return first.get("bus"), first.get("model", "External Monitor"), first.get("brightness", 50), first.get("contrast", 50)

    if mapped_bus is not None:
        return mapped_bus, f"External Monitor ({target_screen})", 50, 50

    # Fallback to probing known buses
    for b in [1, 2, 3, 4, 5, 0, 6, 7]:
        if os.path.exists(f"/dev/i2c-{b}"):
            res = run_cmd(["ddcutil", "--bus", str(b), "--noverify", "getvcp", "10"], timeout=1.5)
            if res and "current value" in res:
                match = re.search(r'current value =\s*(\d+)', res)
                val = int(match.group(1)) if match else 50
                return b, f"External Monitor (I2C-{b})", val, 50
    return 1, "External Monitor", 50, 50

def update_cached_external(bus, brightness=None, contrast=None):
    """Update cache immediately for snappy responsive feel."""
    cache = load_cache()
    monitors = cache.get("monitors", [])
    found = False
    for m in monitors:
        if str(m.get("bus")) == str(bus):
            if brightness is not None:
                m["brightness"] = brightness
            if contrast is not None:
                m["contrast"] = contrast
            found = True
    if not found:
        monitors.append({
            "id": 1,
            "bus": bus,
            "model": "External Monitor",
            "brightness": brightness if brightness is not None else 50,
            "contrast": contrast if contrast is not None else 50,
            "supported": True
        })
    cache["timestamp"] = time.time()
    cache["monitors"] = monitors
    save_cache(cache)

def change_ddc_brightness(delta, bus=None):
    """Adjust external monitor brightness asynchronously via ddcutil with instant OSD."""
    if bus is None:
        bus, model, cur_b, cur_c = get_ddc_bus()
    else:
        cache = load_cache()
        cur_b, cur_c, model = 50, 50, "External Display"
        for m in cache.get("monitors", []):
            if str(m.get("bus")) == str(bus):
                cur_b = m.get("brightness", 50)
                cur_c = m.get("contrast", 50)
                model = m.get("model", model)

    new_val = max(0, min(100, cur_b + delta))
    update_cached_external(bus, brightness=new_val)

    # Spawn ddcutil in background
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "10", str(new_val)])

    bar = build_progress_bar(new_val)
    icon = "video-display"
    title = f"🖥️ Ext Brightness: {new_val}%"
    body = f"<b>{model}</b>\n{bar}"
    show_notification(title, body, icon, percentage=new_val, tag="ext_brightness_osd")
    return new_val

def set_ddc_brightness(target_val, bus=None):
    """Set exact external monitor brightness."""
    target_val = max(0, min(100, int(target_val)))
    if bus is None:
        bus, model, _, _ = get_ddc_bus()
    else:
        cache = load_cache()
        model = "External Display"
        for m in cache.get("monitors", []):
            if str(m.get("bus")) == str(bus):
                model = m.get("model", model)

    update_cached_external(bus, brightness=target_val)
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "10", str(target_val)])

    bar = build_progress_bar(target_val)
    icon = "video-display"
    title = f"🖥️ Ext Brightness: {target_val}%"
    body = f"<b>{model}</b>\n{bar}"
    show_notification(title, body, icon, percentage=target_val, tag="ext_brightness_osd")

def change_ddc_contrast(delta, bus=None):
    """Adjust external monitor contrast asynchronously via ddcutil with instant OSD."""
    if bus is None:
        bus, model, cur_b, cur_c = get_ddc_bus()
    else:
        cache = load_cache()
        cur_b, cur_c, model = 50, 50, "External Display"
        for m in cache.get("monitors", []):
            if str(m.get("bus")) == str(bus):
                cur_b = m.get("brightness", 50)
                cur_c = m.get("contrast", 50)
                model = m.get("model", model)

    new_val = max(0, min(100, cur_c + delta))
    update_cached_external(bus, contrast=new_val)

    # Spawn ddcutil in background
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "12", str(new_val)])

    bar = build_progress_bar(new_val)
    icon = "video-display"
    title = f"🖥️ Ext Contrast: {new_val}%"
    body = f"<b>{model}</b>\n{bar}"
    show_notification(title, body, icon, percentage=new_val, tag="ext_contrast_osd")
    return new_val

def set_ddc_contrast(target_val, bus=None):
    """Set exact external monitor contrast."""
    target_val = max(0, min(100, int(target_val)))
    if bus is None:
        bus, model, _, _ = get_ddc_bus()
    else:
        cache = load_cache()
        model = "External Display"
        for m in cache.get("monitors", []):
            if str(m.get("bus")) == str(bus):
                model = m.get("model", model)

    update_cached_external(bus, contrast=target_val)
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "12", str(target_val)])

    bar = build_progress_bar(target_val)
    icon = "video-display"
    title = f"🖥️ Ext Contrast: {target_val}%"
    body = f"<b>{model}</b>\n{bar}"
    show_notification(title, body, icon, percentage=target_val, tag="ext_contrast_osd")

# ---------------------------------------------------------
# Screen-Aware Active Adjustments
# ---------------------------------------------------------

def change_active_brightness(delta):
    """Adjust brightness of whichever display is currently active (internal vs external)."""
    mon = get_active_monitor_info()
    if mon["is_internal"]:
        change_brightness(delta)
    else:
        change_ddc_brightness(delta)

def set_active_brightness(val):
    """Set brightness of active display to exact value."""
    mon = get_active_monitor_info()
    if mon["is_internal"]:
        set_brightness(val)
    else:
        set_ddc_brightness(val)

def get_active_state():
    """Return JSON state for Quickshell StatusGroup."""
    mon = get_active_monitor_info()
    if mon["is_internal"]:
        pct, label = get_brightness_info()
        return {
            "brightness": pct,
            "is_internal": True,
            "device": "internal",
            "name": mon.get("name", "eDP-1"),
            "label": label
        }
    else:
        bus, model, b_val, c_val = get_ddc_bus()
        return {
            "brightness": b_val,
            "contrast": c_val,
            "is_internal": False,
            "device": "external",
            "bus": bus,
            "name": mon.get("name", "HDMI-A-1"),
            "label": model
        }

def get_screen_state(screen_name=None):
    """Return JSON state for a specific screen (e.g. eDP-1 or HDMI-A-1) or active display."""
    if not screen_name:
        return get_active_state()

    if is_internal_name(screen_name):
        pct, label = get_brightness_info()
        return {
            "brightness": pct,
            "is_internal": True,
            "device": "internal",
            "name": screen_name,
            "label": label
        }
    else:
        bus, model, b_val, c_val = get_ddc_bus(screen_name)
        return {
            "brightness": b_val,
            "contrast": c_val,
            "is_internal": False,
            "device": "external",
            "bus": bus,
            "name": screen_name,
            "label": model
        }

def change_screen_brightness(screen_name, delta):
    """Adjust brightness for a specific screen or fall back to active screen."""
    if not screen_name:
        change_active_brightness(delta)
    elif is_internal_name(screen_name):
        change_brightness(delta)
    else:
        bus, _, _, _ = get_ddc_bus(screen_name)
        change_ddc_brightness(delta, bus=bus)

# ---------------------------------------------------------
# Interactive Menu
# ---------------------------------------------------------

def open_dmenu(prompt, options):
    """Display an interactive menu using fuzzel or wofi."""
    input_str = "\n".join(options)
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", f"{prompt}: ", "--width", "42", "--lines", "16"]
    else:
        cmd = [
            "wofi",
            "--dmenu",
            "--prompt", prompt,
            "--width", "440",
            "--height", "450",
            "--cache-file", "/dev/null",
            "--hide-scroll",
            "--allow-markup",
            "--insensitive"
        ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, _ = proc.communicate(input=input_str)
        return stdout.strip()
    except Exception:
        return ""

def interactive_menu():
    """Run interactive brightness presets menu."""
    active_mon = get_active_monitor_info()
    curr_int_pct, _ = get_brightness_info()
    _, ext_model, ext_b, ext_c = get_ddc_bus()

    options = [
        f"<b>★ Active Screen:</b> {active_mon.get('model', active_mon.get('name'))} ({'Internal' if active_mon['is_internal'] else 'External'})",
        "─── LAPTOP / INTERNAL PRESETS ───",
        f"💻 Laptop 100% Brightness {'(Current: ' + str(curr_int_pct) + '%)' if curr_int_pct == 100 else ''}",
        f"💻 Laptop 75% Brightness {'(Current: ' + str(curr_int_pct) + '%)' if curr_int_pct == 75 else ''}",
        f"💻 Laptop 50% Brightness {'(Current: ' + str(curr_int_pct) + '%)' if curr_int_pct == 50 else ''}",
        f"💻 Laptop 25% Brightness {'(Current: ' + str(curr_int_pct) + '%)' if curr_int_pct == 25 else ''}",
        f"💻 Laptop 10% Brightness {'(Current: ' + str(curr_int_pct) + '%)' if curr_int_pct == 10 else ''}",
        "─── EXTERNAL MONITOR PRESETS ───",
        f"🖥️ Ext Monitor: 100% Brightness {'(Current: ' + str(ext_b) + '%)' if ext_b == 100 else ''}",
        f"🖥️ Ext Monitor: 75% Brightness {'(Current: ' + str(ext_b) + '%)' if ext_b == 75 else ''}",
        f"🖥️ Ext Monitor: 50% Brightness {'(Current: ' + str(ext_b) + '%)' if ext_b == 50 else ''}",
        f"🖥️ Ext Monitor: 25% Brightness {'(Current: ' + str(ext_b) + '%)' if ext_b == 25 else ''}",
        f"🖥️ Ext Monitor: 10% Brightness {'(Current: ' + str(ext_b) + '%)' if ext_b == 10 else ''}",
        "─── EXTERNAL CONTRAST PRESETS ───",
        f"🎨 Ext Contrast: 100% {'(Current: ' + str(ext_c) + '%)' if ext_c == 100 else ''}",
        f"🎨 Ext Contrast: 75% {'(Current: ' + str(ext_c) + '%)' if ext_c == 75 else ''}",
        f"🎨 Ext Contrast: 50% {'(Current: ' + str(ext_c) + '%)' if ext_c == 50 else ''}",
        f"🎨 Ext Contrast: 25% {'(Current: ' + str(ext_c) + '%)' if ext_c == 25 else ''}",
        "─── ACTIONS ───",
        "🎛️ Open Display & Brightness Sliders (GUI)",
        "🌙 Toggle Warm Night Light",
    ]

    selected = open_dmenu("Screen Brightness & Presets", options)
    if not selected:
        return

    if "Open Display & Brightness Sliders" in selected:
        subprocess.Popen(["bash", os.path.expanduser("~/.config/quickshell/scripts/toggle_plugin.sh"), "brightness"])
    elif "Toggle Warm Night Light" in selected:
        subprocess.Popen(["python3", os.path.expanduser("~/.config/hypr/scripts/sunset_idle_manager.py"), "--sunset-toggle"])
    elif "Laptop 100%" in selected:
        set_brightness(100)
    elif "Laptop 75%" in selected:
        set_brightness(75)
    elif "Laptop 50%" in selected:
        set_brightness(50)
    elif "Laptop 25%" in selected:
        set_brightness(25)
    elif "Laptop 10%" in selected:
        set_brightness(10)
    elif "Ext Monitor: 100% Brightness" in selected:
        set_ddc_brightness(100)
    elif "Ext Monitor: 75% Brightness" in selected:
        set_ddc_brightness(75)
    elif "Ext Monitor: 50% Brightness" in selected:
        set_ddc_brightness(50)
    elif "Ext Monitor: 25% Brightness" in selected:
        set_ddc_brightness(25)
    elif "Ext Monitor: 10% Brightness" in selected:
        set_ddc_brightness(10)
    elif "Ext Contrast: 100%" in selected:
        set_ddc_contrast(100)
    elif "Ext Contrast: 75%" in selected:
        set_ddc_contrast(75)
    elif "Ext Contrast: 50%" in selected:
        set_ddc_contrast(50)
    elif "Ext Contrast: 25%" in selected:
        set_ddc_contrast(25)

# ---------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        interactive_menu()
        return

    cmd = sys.argv[1].lower()
    step = DEFAULT_STEP

    if len(sys.argv) >= 3:
        try:
            step = int(sys.argv[2])
        except ValueError:
            pass

    # Screen-specific controls (per-monitor bar)
    if cmd in ["get-screen", "screen-status"]:
        sname = sys.argv[2] if len(sys.argv) >= 3 else None
        print(json.dumps(get_screen_state(sname)))
    elif cmd in ["screen-up", "screen-scroll-up"]:
        sname = sys.argv[2] if len(sys.argv) >= 3 else None
        step_val = int(sys.argv[3]) if len(sys.argv) >= 4 else step
        change_screen_brightness(sname, step_val)
    elif cmd in ["screen-down", "screen-scroll-down"]:
        sname = sys.argv[2] if len(sys.argv) >= 3 else None
        step_val = int(sys.argv[3]) if len(sys.argv) >= 4 else step
        change_screen_brightness(sname, -step_val)

    # Screen-aware controls (active display)
    elif cmd in ["active-up", "scroll-up"]:
        change_active_brightness(step)
    elif cmd in ["active-down", "scroll-down"]:
        change_active_brightness(-step)
    elif cmd in ["active-set"]:
        set_active_brightness(step)
    elif cmd in ["get-active", "active-status"]:
        print(json.dumps(get_active_state()))

    # Explicit internal controls (fallback / direct)
    elif cmd in ["up", "+", "raise", "increase"]:
        # By default 'up' will check active screen unless specified
        change_active_brightness(step)
    elif cmd in ["down", "-", "lower", "decrease"]:
        change_active_brightness(-step)
    elif cmd in ["internal-up"]:
        change_brightness(step)
    elif cmd in ["internal-down"]:
        change_brightness(-step)
    elif cmd in ["set"]:
        set_brightness(step)
    elif cmd in ["show", "status", "info"]:
        notify_brightness_osd()

    # Explicit external controls
    elif cmd in ["ddc-up", "ext-up", "ext-bright-up"]:
        change_ddc_brightness(step if len(sys.argv) >= 3 else 10)
    elif cmd in ["ddc-down", "ext-down", "ext-bright-down"]:
        change_ddc_brightness(-step if len(sys.argv) >= 3 else -10)
    elif cmd in ["ddc-set", "ext-bright", "ext-set-brightness"] and len(sys.argv) >= 3:
        set_ddc_brightness(sys.argv[2])
    elif cmd in ["ddc-contrast-up", "ext-contrast-up"]:
        change_ddc_contrast(step if len(sys.argv) >= 3 else 10)
    elif cmd in ["ddc-contrast-down", "ext-contrast-down"]:
        change_ddc_contrast(-step if len(sys.argv) >= 3 else -10)
    elif cmd in ["ddc-contrast-set", "ext-contrast", "ext-set-contrast"] and len(sys.argv) >= 3:
        set_ddc_contrast(sys.argv[2])

    elif cmd in ["menu", "dmenu", "gui"]:
        interactive_menu()
    else:
        print(f"Unknown action: {cmd}")
        print("Usage: brightness_control.py [active-up|active-down|active-set|get-active|up|down|ddc-up|ddc-down|ext-set-brightness|ext-set-contrast|menu]")
        sys.exit(1)

if __name__ == "__main__":
    main()
