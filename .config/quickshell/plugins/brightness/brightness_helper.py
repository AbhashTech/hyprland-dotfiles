#!/usr/bin/env python3
"""
Screen Brightness & Display Resolution / Scaling Helper for QuickShell & Hyprland.
Provides fast querying and async adjustments for:
- Internal laptop backlight & external monitor (DDC/CI) brightness/contrast
- Hyprland display resolutions, refresh rates, and UI scaling factors
- Idle dimming/restore, OSD notifications, and user/monitors.lua persistence
"""

import sys
import json
import subprocess
import os
import re
import time
import glob
import shutil

CACHE_FILE = os.path.expanduser("~/.cache/quickshell_brightness_cache.json")
DIM_STATE_FILE = os.path.expanduser("~/.cache/hypr_ext_dim_saved.json")
USER_MONITORS_FILE = os.path.expanduser("~/.config/hypr/user/monitors.lua")
BRIGHTNESS_NOTIF_ID = 9100
DEFAULT_STEP = 5

def run_cmd(cmd, timeout=3):
    """Run a shell command and return stdout."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return res.stdout.strip()
    except Exception:
        return ""

def build_progress_bar(percentage, length=12):
    """Build a visual UTF-8 progress bar string."""
    filled = int(round((percentage / 100.0) * length))
    filled = max(0, min(length, filled))
    return "━" * filled + "╸" + "─" * (length - filled)

def show_notification(title, body, icon="display-brightness", percentage=None, notif_id=BRIGHTNESS_NOTIF_ID, tag="brightness_osd"):
    """Send unified desktop OSD notification with progress level."""
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
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def decode_edid_mfg(b1, b2):
    """Decode 2-byte EDID manufacturer code into 3-letter abbreviation."""
    c1 = chr(((b1 & 0x7C) >> 2) + ord('A') - 1)
    c2 = chr((((b1 & 0x03) << 3) | ((b2 & 0xE0) >> 5)) + ord('A') - 1)
    c3 = chr((b2 & 0x1F) + ord('A') - 1)
    return f"{c1}{c2}{c3}"

def get_drm_monitor_names():
    """Read EDID descriptors directly from sysfs for instant monitor name resolution."""
    names = {}
    for p in glob.glob("/sys/class/drm/card*-*/edid"):
        try:
            data = open(p, "rb").read()
            if len(data) >= 128:
                mfg = decode_edid_mfg(data[8], data[9])
                model_name = ""
                for block_start in [54, 72, 90, 108]:
                    if data[block_start:block_start+4] == b'\x00\x00\x00\xfc':
                        model_name = data[block_start+5:block_start+18].decode('latin1', errors='ignore').strip()
                        break
                
                label = model_name or mfg
                if mfg and model_name and not model_name.startswith(mfg):
                    mfg_names = {
                        "LEN": "Lenovo", "SAM": "Samsung", "DEL": "Dell",
                        "AOC": "AOC", "LG": "LG", "ASU": "ASUS", "ACR": "Acer",
                        "BNQ": "BenQ", "HPN": "HP", "HWP": "HP", "MSI": "MSI",
                        "SNY": "Sony", "VSC": "ViewSonic", "GGL": "Google", "APP": "Apple"
                    }
                    mfg_display = mfg_names.get(mfg, mfg)
                    label = f"{mfg_display} {model_name}"

                conn = p.split('/')[-2]
                if "eDP" not in conn:  # only external
                    names[conn] = label
        except Exception:
            pass
    return names

def is_internal_name(name):
    name_upper = (name or "").upper()
    return name_upper.startswith("EDP") or name_upper.startswith("LVDS") or name_upper.startswith("DSI")

def get_internal_brightness():
    """Retrieve internal laptop display brightness."""
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
                dev_label = "Built-in Display"
                if "intel" in dev or "amdgpu" in dev or "nvidia" in dev:
                    dev_label = "Laptop Screen"
                return {"available": True, "device": dev, "label": dev_label, "brightness": pct}
    return {"available": False, "device": "", "label": "No Internal Display", "brightness": 50}

def get_brightness_info():
    """Retrieve active brightness percentage and device label."""
    info = get_internal_brightness()
    if info["available"]:
        return info["brightness"], info["label"]
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

def set_internal_brightness(val):
    val = max(1, min(100, int(val)))
    run_cmd(["brightnessctl", "set", f"{val}%"])
    notify_brightness_osd(target_pct=val)

def get_night_light_status():
    """Check if hyprsunset / night light filter is active."""
    out = run_cmd(["pgrep", "-x", "hyprsunset"])
    return bool(out)

def probe_ddc_bus(bus_num):
    """Query VCP 10 (Brightness) and 12 (Contrast) on a specific I2C bus."""
    try:
        res = run_cmd(["ddcutil", "--bus", str(bus_num), "--noverify", "getvcp", "10", "12"], timeout=2)
        if not res:
            return None
        
        b_match = re.search(r'VCP code 0x10.*?current value =\s*(\d+)', res)
        c_match = re.search(r'VCP code 0x12.*?current value =\s*(\d+)', res)

        if b_match or c_match:
            b_val = int(b_match.group(1)) if b_match else 50
            c_val = int(c_match.group(1)) if c_match else 50
            return {"brightness": b_val, "contrast": c_val}
    except Exception:
        pass
    return None

def get_connector_for_bus(bus_num):
    """Find DRM connector name associated with an I2C bus."""
    for p in glob.glob(f"/sys/class/drm/*-*/ddc"):
        try:
            target = os.path.realpath(p)
            base = os.path.basename(target)
            if base == f"i2c-{bus_num}":
                parent_dir = os.path.basename(os.path.dirname(p))
                if "-" in parent_dir:
                    return parent_dir.split("-", 1)[1]
                return parent_dir
        except Exception:
            pass
    return f"I2C-{bus_num}"

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

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def update_cached_external(bus, brightness=None, contrast=None):
    cache = load_cache()
    monitors = cache.get("monitors", [])
    found = False
    for m in monitors:
        if m.get("bus") == bus:
            if brightness is not None:
                m["brightness"] = brightness
            if contrast is not None:
                m["contrast"] = contrast
            found = True
            break
    if not found:
        monitors.append({
            "id": len(monitors) + 1,
            "name": get_connector_for_bus(bus),
            "bus": bus,
            "model": f"External Monitor (I2C-{bus})",
            "brightness": brightness if brightness is not None else 50,
            "contrast": contrast if contrast is not None else 50,
            "supported": True
        })
    cache["monitors"] = monitors
    cache["timestamp"] = time.time()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass

def get_active_monitor_info():
    """Detect currently focused / active monitor in Hyprland."""
    raw = run_cmd(["hyprctl", "monitors", "-j"], timeout=1)
    if raw:
        try:
            monitors = json.loads(raw)
            for m in monitors:
                if m.get("focused"):
                    name = m.get("name", "")
                    return {
                        "name": name,
                        "is_internal": is_internal_name(name),
                        "model": m.get("model", "") or m.get("description", "") or name,
                        "description": m.get("description", name)
                    }
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
                            return {
                                "name": name,
                                "is_internal": is_internal_name(name),
                                "model": m.get("model", "") or m.get("description", "") or name,
                                "description": m.get("description", name)
                            }
                except Exception:
                    pass
            if monitors:
                first = monitors[0]
                name = first.get("name", "")
                return {
                    "name": name,
                    "is_internal": is_internal_name(name),
                    "model": first.get("model", "") or name,
                    "description": first.get("description", name)
                }
        except Exception:
            pass
    return {"name": "eDP-1", "is_internal": True, "model": "Built-in Display", "description": "Laptop Screen"}

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
        first = monitors[0]
        return first.get("bus", 1), first.get("model", "External Monitor"), first.get("brightness", 50), first.get("contrast", 50)

    for dev in sorted(glob.glob("/dev/i2c-[0-9]*")):
        try:
            b = int(dev.split("-")[-1])
            vals = probe_ddc_bus(b)
            if vals:
                conn_name = get_connector_for_bus(b)
                label = f"External Monitor ({conn_name})"
                update_cached_external(b, vals["brightness"], vals["contrast"])
                return b, label, vals["brightness"], vals["contrast"]
        except Exception:
            continue
    return 1, "External Monitor", 50, 50

def detect_external_monitors(force_rescan=False):
    """Detect DDC/CI capable external monitors with smart caching and EDID lookup."""
    drm_names = get_drm_monitor_names()

    if not force_rescan and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                if time.time() - data.get("timestamp", 0) < 60:
                    cached_monitors = data.get("monitors", [])
                    for mon in cached_monitors:
                        bus = mon.get("bus")
                        if bus is not None:
                            vals = probe_ddc_bus(bus)
                            if vals:
                                mon["brightness"] = vals["brightness"]
                                mon["contrast"] = vals["contrast"]
                            if "name" not in mon or not mon["name"]:
                                mon["name"] = get_connector_for_bus(bus)
                    return cached_monitors
        except Exception:
            pass

    monitors = []
    i2c_devs = sorted(glob.glob("/dev/i2c-[0-9]*"))
    bus_nums = []
    for dev in i2c_devs:
        try:
            num = int(dev.split("-")[-1])
            bus_nums.append(num)
        except ValueError:
            pass

    for b in bus_nums:
        vals = probe_ddc_bus(b)
        if vals:
            conn_name = get_connector_for_bus(b)
            model_label = f"External Monitor ({conn_name})"
            if drm_names:
                for dconn, dname in drm_names.items():
                    if conn_name in dconn or dconn in conn_name:
                        model_label = dname
                        break
                else:
                    model_label = list(drm_names.values())[0]

            monitors.append({
                "id": len(monitors) + 1,
                "name": conn_name,
                "bus": b,
                "model": model_label,
                "brightness": vals["brightness"],
                "contrast": vals["contrast"],
                "supported": True
            })

    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"timestamp": time.time(), "monitors": monitors}, f)
    except Exception:
        pass

    return monitors

def set_ext_brightness(bus, val):
    val = max(0, min(100, int(val)))
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "10", str(val)])
    update_cached_external(int(bus), brightness=val)

def set_ext_contrast(bus, val):
    val = max(0, min(100, int(val)))
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "12", str(val)])
    update_cached_external(int(bus), contrast=val)

def change_ddc_brightness(delta, bus=None):
    b, model, curr_b, _ = get_ddc_bus() if bus is None else (bus, "External Monitor", 50, 50)
    new_b = max(0, min(100, curr_b + delta))
    set_ext_brightness(b, new_b)
    bar = build_progress_bar(new_b)
    title = f"🖥️ External Brightness: {new_b}%"
    body = f"<b>{model}</b>\n{bar}"
    show_notification(title, body, "display-brightness", percentage=new_b, tag="ddc_brightness_osd")

def change_ddc_contrast(delta, bus=None):
    b, model, _, curr_c = get_ddc_bus() if bus is None else (bus, "External Monitor", 50, 50)
    new_c = max(0, min(100, curr_c + delta))
    set_ext_contrast(b, new_c)
    bar = build_progress_bar(new_c)
    title = f"🎨 External Contrast: {new_c}%"
    body = f"<b>{model}</b>\n{bar}"
    show_notification(title, body, "preferences-desktop-display", percentage=new_c, tag="ddc_contrast_osd")

def change_active_brightness(delta):
    active_mon = get_active_monitor_info()
    if active_mon["is_internal"]:
        change_brightness(delta)
    else:
        change_ddc_brightness(delta)

def change_screen_brightness(screen_name, delta):
    if not screen_name or is_internal_name(screen_name):
        change_brightness(delta)
    else:
        bus = get_i2c_bus_for_connector(screen_name)
        change_ddc_brightness(delta, bus=bus)

def get_all_external_buses():
    buses = []
    for p in glob.glob("/sys/class/drm/*-*/ddc"):
        parent = os.path.basename(os.path.dirname(p))
        if "eDP" in parent or "LVDS" in parent or "DSI" in parent:
            continue
        try:
            target = os.path.realpath(p)
            base = os.path.basename(target)
            if base.startswith("i2c-"):
                b_num = int(base.split("-")[-1])
                if b_num not in buses:
                    buses.append(b_num)
        except Exception:
            pass
    if not buses:
        cache = load_cache()
        for m in cache.get("monitors", []):
            b = m.get("bus")
            if b is not None and b not in buses:
                buses.append(b)
    return buses

def dim_screens(dim_pct=10):
    dim_pct = max(0, min(100, int(dim_pct)))
    run_cmd(["brightnessctl", "-s", "set", f"{dim_pct}%"])
    ext_buses = get_all_external_buses()
    if not ext_buses:
        return

    saved_state = {}
    if os.path.exists(DIM_STATE_FILE):
        try:
            with open(DIM_STATE_FILE, "r") as f:
                saved_state = json.load(f)
        except Exception:
            saved_state = {}

    cache = load_cache()
    cached_mons = {str(m.get("bus")): m.get("brightness", 50) for m in cache.get("monitors", [])}

    updated_saved = False
    for b in ext_buses:
        b_str = str(b)
        if b_str not in saved_state:
            saved_state[b_str] = cached_mons.get(b_str, 50)
            updated_saved = True
        subprocess.Popen(["ddcutil", "--bus", str(b), "--noverify", "setvcp", "10", str(dim_pct)])

    if updated_saved or not os.path.exists(DIM_STATE_FILE):
        try:
            with open(DIM_STATE_FILE, "w") as f:
                json.dump(saved_state, f)
        except Exception:
            pass

def restore_screens():
    run_cmd(["brightnessctl", "-r"])
    if not os.path.exists(DIM_STATE_FILE):
        return

    saved_state = {}
    try:
        with open(DIM_STATE_FILE, "r") as f:
            saved_state = json.load(f)
    except Exception:
        pass

    try:
        os.remove(DIM_STATE_FILE)
    except Exception:
        pass

    for b_str, orig_val in saved_state.items():
        try:
            b = int(b_str)
            update_cached_external(b, brightness=int(orig_val))
            subprocess.Popen(["ddcutil", "--bus", str(b), "--noverify", "setvcp", "10", str(orig_val)])
        except Exception:
            pass

def toggle_nightlight():
    subprocess.Popen(["python3", os.path.expanduser("~/.config/hypr/scripts/sunset_idle_manager.py"), "--sunset-toggle"])

# ---------------------------------------------------------
# Display Resolution & Scaling Functions
# ---------------------------------------------------------

def get_hyprland_monitors():
    """Retrieve all active Hyprland displays with resolution, refresh rate, and scale."""
    raw = run_cmd(["hyprctl", "monitors", "-j"], timeout=2)
    if not raw:
        return []
    try:
        monitors = json.loads(raw)
        result = []
        for m in monitors:
            name = m.get("name", "")
            raw_modes = m.get("availableModes", [])
            seen_modes = set()
            clean_modes = []
            for mode_str in raw_modes:
                if mode_str not in seen_modes:
                    seen_modes.add(mode_str)
                    clean_modes.append(mode_str)
            
            result.append({
                "id": m.get("id", 0),
                "name": name,
                "model": m.get("model", "") or m.get("description", "") or name,
                "description": m.get("description", name),
                "width": m.get("width", 1920),
                "height": m.get("height", 1080),
                "refreshRate": round(float(m.get("refreshRate", 60.0)), 2),
                "scale": round(float(m.get("scale", 1.0)), 2),
                "focused": bool(m.get("focused", False)),
                "is_internal": is_internal_name(name),
                "availableModes": clean_modes
            })
        return result
    except Exception:
        return []

def apply_resolution(monitor_name, mode, scale, save_config=False):
    """Apply resolution and scale to Hyprland monitor using hyprctl eval."""
    try:
        scale_float = float(scale)
    except (ValueError, TypeError):
        scale_float = 1.0
    scale_str = f"{scale_float:.2f}".rstrip("0").rstrip(".")
    if scale_str.endswith("."):
        scale_str += "0"

    lua_code = f'hl.monitor({{ output = "{monitor_name}", mode = "{mode}", position = "auto", scale = {scale_str} }})'
    run_cmd(["hyprctl", "eval", lua_code])

    show_notification(
        f"🖥️ Display Configured: {monitor_name}",
        f"Resolution: <b>{mode}</b>\nScaling: <b>{scale_str}x ({int(scale_float * 100)}%)</b>",
        icon="video-display",
        tag="screen_resolution"
    )

    if save_config:
        save_to_monitors_lua(monitor_name, mode, scale_str)

def set_monitor_scale(monitor_name, scale, save_config=False):
    """Set display scale while preserving current mode."""
    mons = get_hyprland_monitors()
    target_mon = next((m for m in mons if m["name"] == monitor_name), None)
    if not target_mon:
        target_mon = mons[0] if mons else None
    
    if target_mon:
        w = target_mon["width"]
        h = target_mon["height"]
        rr = target_mon["refreshRate"]
        mode = f"{w}x{h}@{rr:.2f}"
        name = target_mon["name"]
    else:
        name = monitor_name
        mode = "preferred"

    apply_resolution(name, mode, scale, save_config=save_config)

def save_to_monitors_lua(monitor_name, mode, scale):
    """Save monitor configuration to user personal monitors.lua (untracked)."""
    os.makedirs(os.path.dirname(USER_MONITORS_FILE), exist_ok=True)
    new_entry = f"""hl.monitor({{
    output   = "{monitor_name}",
    mode     = "{mode}",
    position = "auto",
    scale    = {scale},
}})"""

    try:
        content = ""
        if os.path.isfile(USER_MONITORS_FILE):
            with open(USER_MONITORS_FILE, "r", encoding="utf-8") as f:
                content = f.read()

        pattern = rf'hl\.monitor\(\s*\{{[^}}]*output\s*=\s*["\']{re.escape(monitor_name)}["\'][^}}]*\}}\)'
        if re.search(pattern, content):
            content = re.sub(pattern, new_entry, content)
        elif content.strip():
            content = content.rstrip() + "\n\n" + new_entry + "\n"
        else:
            content = f"""--------------------------------------------------------------------------------
-- User Personal Monitor Configuration (Untracked)
--------------------------------------------------------------------------------
-- Auto-generated by QuickShell Display Manager

{new_entry}
"""
        with open(USER_MONITORS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        sys.stderr.write(f"Failed to save {USER_MONITORS_FILE}: {e}\n")
        return False

def scale_step(delta):
    """Step scale by delta for focused monitor."""
    mons = get_hyprland_monitors()
    target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
    if not target:
        return
    current_scale = float(target["scale"])
    new_scale = round(current_scale + delta, 2)
    new_scale = max(0.5, min(3.0, new_scale))
    set_monitor_scale(target["name"], new_scale, save_config=False)

def show_resolution_notification(monitor_name=None):
    """Display current resolution OSD notification."""
    mons = get_hyprland_monitors()
    target = None
    if monitor_name:
        target = next((m for m in mons if m["name"] == monitor_name), None)
    if not target:
        target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
    if target:
        w, h = target["width"], target["height"]
        scale = target["scale"]
        rr = target["refreshRate"]
        name = target["name"]
        show_notification(
            f"🖥️ {name} Resolution",
            f"<b>{w} × {h}</b> @ {rr:.2f}Hz\nScale: <b>{scale}x ({int(float(scale)*100)}%)</b>",
            icon="video-display",
            tag="screen_resolution"
        )

# ---------------------------------------------------------
# Aggregator State
# ---------------------------------------------------------

def get_all_state(force_rescan=False):
    """Aggregate internal/external display states, active monitor info, and display modes."""
    internal = get_internal_brightness()
    external = detect_external_monitors(force_rescan=force_rescan)
    night_light = get_night_light_status()
    active_mon = get_active_monitor_info()
    monitors = get_hyprland_monitors()

    return {
        "internal": internal,
        "external": external,
        "night_light": night_light,
        "active": active_mon,
        "monitors": monitors
    }

# ---------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["get-all", "status", "json"]:
        force = "--rescan" in sys.argv or "--force" in sys.argv
        print(json.dumps(get_all_state(force_rescan=force)))
        return

    cmd = sys.argv[1].lower()
    step = DEFAULT_STEP
    if len(sys.argv) >= 3:
        try:
            step = int(sys.argv[2])
        except ValueError:
            pass

    # Brightness controls
    if cmd in ["set-internal", "internal"] and len(sys.argv) >= 3:
        set_internal_brightness(sys.argv[2])
    elif cmd in ["set-ext-brightness", "ext-bright"] and len(sys.argv) >= 4:
        set_ext_brightness(sys.argv[2], sys.argv[3])
    elif cmd in ["set-ext-contrast", "ext-contrast"] and len(sys.argv) >= 4:
        set_ext_contrast(sys.argv[2], sys.argv[3])
    elif cmd in ["toggle-nightlight", "nightlight"]:
        toggle_nightlight()
    elif cmd in ["rescan", "detect"]:
        print(json.dumps(get_all_state(force_rescan=True)))

    # Hotkey / Screen-aware controls
    elif cmd in ["active-up", "scroll-up"]:
        change_active_brightness(step)
    elif cmd in ["active-down", "scroll-down"]:
        change_active_brightness(-step)
    elif cmd in ["screen-up", "screen-scroll-up"]:
        sname = sys.argv[2] if len(sys.argv) >= 3 else None
        s_step = int(sys.argv[3]) if len(sys.argv) >= 4 else step
        change_screen_brightness(sname, s_step)
    elif cmd in ["screen-down", "screen-scroll-down"]:
        sname = sys.argv[2] if len(sys.argv) >= 3 else None
        s_step = int(sys.argv[3]) if len(sys.argv) >= 4 else step
        change_screen_brightness(sname, -s_step)
    elif cmd in ["ddc-up", "ext-up"]:
        change_ddc_brightness(step if len(sys.argv) >= 3 else 10)
    elif cmd in ["ddc-down", "ext-down"]:
        change_ddc_brightness(-step if len(sys.argv) >= 3 else -10)
    elif cmd in ["ddc-contrast-up"]:
        change_ddc_contrast(step if len(sys.argv) >= 3 else 10)
    elif cmd in ["ddc-contrast-down"]:
        change_ddc_contrast(-step if len(sys.argv) >= 3 else -10)
    elif cmd in ["dim", "idle-dim"]:
        dim_pct = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        dim_screens(dim_pct)
    elif cmd in ["restore", "undim", "idle-resume"]:
        restore_screens()

    # Resolution & Scaling controls
    elif cmd in ["get-monitors", "monitors"]:
        print(json.dumps(get_hyprland_monitors()))
    elif cmd == "set-resolution" and len(sys.argv) >= 5:
        mon_name = sys.argv[2]
        mode = sys.argv[3]
        scale = sys.argv[4]
        save = len(sys.argv) > 5 and sys.argv[5].lower() in ["true", "1", "save"]
        apply_resolution(mon_name, mode, scale, save_config=save)
    elif cmd == "set-scale" and len(sys.argv) >= 4:
        mon_name = sys.argv[2]
        scale = sys.argv[3]
        save = len(sys.argv) > 4 and sys.argv[4].lower() in ["true", "1", "save"]
        set_monitor_scale(mon_name, scale, save_config=save)
    elif cmd == "save-display" and len(sys.argv) >= 5:
        mon_name = sys.argv[2]
        mode = sys.argv[3]
        scale = sys.argv[4]
        ok = save_to_monitors_lua(mon_name, mode, scale)
        if ok:
            show_notification(
                "Display Settings Saved",
                f"Saved <b>{mon_name}</b> ({mode}, {scale}x) to monitors.lua",
                icon="document-save"
            )
            print("saved")
        else:
            print("failed")
    elif cmd in ["scale_up", "scale+", "zoom_in"]:
        scale_step(0.1)
    elif cmd in ["scale_down", "scale-", "zoom_out"]:
        scale_step(-0.1)
    elif cmd in ["scale-show", "show-scale", "show"]:
        show_resolution_notification()
    elif cmd.startswith("scale:") or cmd.startswith("scale="):
        try:
            val = float(cmd.split(":", 1)[-1].split("=", 1)[-1])
            mons = get_hyprland_monitors()
            target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
            if target:
                set_monitor_scale(target["name"], val, save_config=False)
        except ValueError:
            pass
    elif cmd in ["1", "1.0", "1.00", "1x", "100%", "100"]:
        scale_step(0)  # or set exact
        mons = get_hyprland_monitors()
        target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
        if target:
            set_monitor_scale(target["name"], 1.0, save_config=False)
    elif cmd in ["1.25", "1.25x", "125%", "125"]:
        mons = get_hyprland_monitors()
        target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
        if target:
            set_monitor_scale(target["name"], 1.25, save_config=False)
    elif cmd in ["1.5", "1.50", "1.5x", "150%", "150"]:
        mons = get_hyprland_monitors()
        target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
        if target:
            set_monitor_scale(target["name"], 1.5, save_config=False)
    elif cmd in ["1.75", "1.75x", "175%", "175"]:
        mons = get_hyprland_monitors()
        target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
        if target:
            set_monitor_scale(target["name"], 1.75, save_config=False)
    elif cmd in ["2", "2.0", "2.00", "2x", "200%", "200"]:
        mons = get_hyprland_monitors()
        target = next((m for m in mons if m["focused"]), mons[0] if mons else None)
        if target:
            set_monitor_scale(target["name"], 2.0, save_config=False)
    else:
        print(f"Unknown action: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
