#!/usr/bin/env python3
"""
Screen Brightness & External Monitor (DDC/CI) Helper for QuickShell & Hyprland.
Provides fast querying and async adjustments for internal backlight and external monitor brightness/contrast.
"""

import sys
import json
import subprocess
import os
import re
import time
import glob

CACHE_FILE = os.path.expanduser("~/.cache/quickshell_brightness_cache.json")

def run_cmd(cmd, timeout=3):
    """Run a shell command and return stdout."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return res.stdout.strip()
    except Exception:
        return ""

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
                
                # Full display label
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

def is_internal_name(name):
    name_upper = (name or "").upper()
    return name_upper.startswith("EDP") or name_upper.startswith("LVDS") or name_upper.startswith("DSI")

def get_connector_for_bus(bus_num):
    """Find DRM connector name associated with an I2C bus."""
    for p in glob.glob(f"/sys/class/drm/*-*/ddc"):
        try:
            target = os.path.realpath(p)
            base = os.path.basename(target)
            if base == f"i2c-{bus_num}":
                parent_dir = os.path.basename(os.path.dirname(p))
                # card1-HDMI-A-1 -> HDMI-A-1
                if "-" in parent_dir:
                    return parent_dir.split("-", 1)[1]
                return parent_dir
        except Exception:
            pass
    return f"I2C-{bus_num}"

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

def detect_external_monitors(force_rescan=False):
    """Detect DDC/CI capable external monitors with smart caching and EDID lookup."""
    drm_names = get_drm_monitor_names()

    # Check cache freshness
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

    # Perform discovery
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
            # Use EDID parsed name if available
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

def get_all_state(force_rescan=False):
    """Aggregate internal and external display states along with active monitor info."""
    internal = get_internal_brightness()
    external = detect_external_monitors(force_rescan=force_rescan)
    night_light = get_night_light_status()
    active_mon = get_active_monitor_info()

    return {
        "internal": internal,
        "external": external,
        "night_light": night_light,
        "active": active_mon
    }

def set_internal_brightness(val):
    val = max(1, min(100, int(val)))
    run_cmd(["brightnessctl", "set", f"{val}%"])

def set_ext_brightness(bus, val):
    val = max(0, min(100, int(val)))
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "10", str(val)])
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
            for m in data.get("monitors", []):
                if str(m.get("bus")) == str(bus):
                    m["brightness"] = val
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

def set_ext_contrast(bus, val):
    val = max(0, min(100, int(val)))
    subprocess.Popen(["ddcutil", "--bus", str(bus), "--noverify", "setvcp", "12", str(val)])
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
            for m in data.get("monitors", []):
                if str(m.get("bus")) == str(bus):
                    m["contrast"] = val
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

def toggle_nightlight():
    subprocess.Popen(["python3", os.path.expanduser("~/.config/hypr/scripts/sunset_idle_manager.py"), "--sunset-toggle"])

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["get-all", "status", "json"]:
        force = "--rescan" in sys.argv or "--force" in sys.argv
        print(json.dumps(get_all_state(force_rescan=force)))
        return

    cmd = sys.argv[1].lower()
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
    else:
        print(f"Unknown action: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
