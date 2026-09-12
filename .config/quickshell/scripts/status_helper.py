#!/usr/bin/env python3
"""
High-Performance Unified System Status Collector for Quickshell
Consolidates Audio, Brightness, Wi-Fi, Bluetooth, and Battery metrics into a single JSON output.
Uses direct sysfs/proc reads where possible for sub-millisecond execution.
"""

import sys
import os
import glob
import json
import subprocess

def clean_audio_name(desc, is_mic=False):
    if not desc:
        return "Digital Mic" if is_mic else "Speakers"
    desc = " ".join(desc.split()).strip()
    if "Speaker" in desc or "speaker" in desc:
        return "Speakers"
    if "Headphone" in desc or "Headset" in desc:
        return "Headphones"
    if "Digital Microphone" in desc or "Mic" in desc:
        return "Microphone"
    parts = desc.split(")")
    if len(parts) > 1 and parts[-1].strip():
        return parts[-1].strip()[:24]
    desc = desc.replace("(HD Audio)", "").strip()
    return desc[:24]

def get_audio_info():
    vol = 50
    muted = False
    s_desc = "Speakers"
    mic_vol = 100
    mic_muted = False
    m_desc = "Microphone"

    # Default sink info via wpctl
    try:
        res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, timeout=1).stdout.strip()
        parts = res.split()
        if len(parts) > 1:
            vol = int(round(float(parts[1]) * 100))
        muted = "[MUTED]" in res
    except Exception:
        pass

    # Sink name description via pactl
    try:
        s_name = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=1).stdout.strip()
        sinks_json = json.loads(subprocess.run(["pactl", "-f", "json", "list", "sinks"], capture_output=True, text=True, timeout=1).stdout)
        for s in sinks_json:
            if s.get("name") == s_name:
                s_desc = clean_audio_name(s.get("description", ""))
                break
    except Exception:
        pass

    # Default source info via wpctl
    try:
        m_res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"], capture_output=True, text=True, timeout=1).stdout.strip()
        m_parts = m_res.split()
        if len(m_parts) > 1:
            mic_vol = int(round(float(m_parts[1]) * 100))
        mic_muted = "[MUTED]" in m_res
    except Exception:
        pass

    # Source name description via pactl
    try:
        m_name = subprocess.run(["pactl", "get-default-source"], capture_output=True, text=True, timeout=1).stdout.strip()
        srcs_json = json.loads(subprocess.run(["pactl", "-f", "json", "list", "sources"], capture_output=True, text=True, timeout=1).stdout)
        for s in srcs_json:
            if s.get("name") == m_name:
                m_desc = clean_audio_name(s.get("description", ""), is_mic=True)
                break
    except Exception:
        pass

    return {
        "vol": vol,
        "muted": muted,
        "sink": s_desc,
        "mic_vol": mic_vol,
        "mic_muted": mic_muted,
        "mic": m_desc
    }

def is_internal_display(name):
    name_upper = (name or "").upper()
    return name_upper.startswith("EDP") or name_upper.startswith("LVDS") or name_upper.startswith("DSI")

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

def get_active_monitor():
    try:
        raw = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=0.6).stdout
        if raw:
            mons = json.loads(raw)
            for m in mons:
                if m.get("focused"):
                    return m
            cursor_raw = subprocess.run(["hyprctl", "cursorpos"], capture_output=True, text=True, timeout=0.4).stdout
            if cursor_raw and "," in cursor_raw:
                try:
                    cx, cy = [int(v.strip()) for v in cursor_raw.split(",")]
                    for m in mons:
                        x = m.get("x", 0)
                        y = m.get("y", 0)
                        w = m.get("width", 1920)
                        h = m.get("height", 1080)
                        if x <= cx < x + w and y <= cy < y + h:
                            return m
                except Exception:
                    pass
            if mons:
                return mons[0]
    except Exception:
        pass
    return None

def get_internal_backlight_pct():
    backlights = glob.glob("/sys/class/backlight/*")
    if backlights:
        try:
            bl = backlights[0]
            cur = int(open(os.path.join(bl, "brightness")).read().strip())
            mx = int(open(os.path.join(bl, "max_brightness")).read().strip())
            if mx > 0:
                return int(round((cur / mx) * 100))
        except Exception:
            pass
    return 50

def get_brightness_info(screen_name=""):
    target_screen = screen_name
    active_mon = None

    if not target_screen:
        active_mon = get_active_monitor()
        if active_mon:
            target_screen = active_mon.get("name", "")

    is_internal = is_internal_display(target_screen) if target_screen else True

    if is_internal:
        pct = get_internal_backlight_pct()
        label = "Laptop Screen"
        if active_mon and active_mon.get("model"):
            label = active_mon.get("model")
        return {
            "brightness": pct,
            "name": target_screen or "eDP-1",
            "is_internal": True,
            "label": label
        }
    else:
        # External Monitor
        cache_path = os.path.expanduser("~/.cache/quickshell_brightness_cache.json")
        target_bus = get_i2c_bus_for_connector(target_screen)
        b_val = 50
        model_label = target_screen or "External Monitor"

        if os.path.isfile(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cdata = json.load(f)
                    monitors = cdata.get("monitors", [])
                    for m in monitors:
                        if (target_bus is not None and m.get("bus") == target_bus) or (target_screen and str(m.get("name")) == str(target_screen)):
                            b_val = m.get("brightness", 50)
                            model_label = m.get("model", model_label)
                            break
                    else:
                        if monitors:
                            b_val = monitors[0].get("brightness", 50)
                            model_label = monitors[0].get("model", model_label)
            except Exception:
                pass

        return {
            "brightness": b_val,
            "name": target_screen,
            "is_internal": False,
            "bus": target_bus,
            "label": model_label
        }

def get_wifi_info():
    iface = "wlan0"
    try:
        for net_if in os.listdir("/sys/class/net"):
            if net_if.startswith(("wl", "wlan", "wifi")):
                iface = net_if
                break
    except Exception:
        pass

    powered = True
    try:
        # Check rfkill via sysfs
        rfkill_dirs = glob.glob("/sys/class/rfkill/rfkill*")
        for rfd in rfkill_dirs:
            try:
                t_type = open(os.path.join(rfd, "type")).read().strip()
                if t_type == "wlan":
                    soft = open(os.path.join(rfd, "soft")).read().strip()
                    hard = open(os.path.join(rfd, "hard")).read().strip()
                    if soft == "1" or hard == "1":
                        powered = False
            except Exception:
                pass
    except Exception:
        pass

    if powered:
        if not os.path.exists(f"/sys/class/net/{iface}"):
            powered = False
        else:
            try:
                flags_str = open(f"/sys/class/net/{iface}/flags").read().strip()
                flags = int(flags_str, 16)
                if not (flags & 1):
                    powered = False
            except Exception:
                pass

    ssid = ""
    sig = 0
    rssi = ""
    ip = ""
    sec = ""
    freq = ""
    connected = False

    # Check operational state from sysfs
    operstate = "down"
    try:
        operstate = open(f"/sys/class/net/{iface}/operstate").read().strip()
    except Exception:
        pass

    if operstate == "up":
        # Fast iwctl query
        try:
            res = subprocess.run(["iwctl", "station", iface, "show"], capture_output=True, text=True, timeout=1).stdout
            for l in res.splitlines():
                if "Connected network" in l:
                    ssid = l.split("Connected network")[-1].strip()
                    connected = bool(ssid)
                elif "IPv4 address" in l:
                    ip = l.split("IPv4 address")[-1].strip()
                elif "Security" in l:
                    sec = l.split("Security")[-1].strip()
                elif "Frequency" in l:
                    f_val = l.split("Frequency")[-1].strip()
                    try:
                        freq = "5 GHz" if int(f_val.split()[0]) > 3000 else "2.4 GHz"
                    except Exception:
                        freq = f_val
                elif "RSSI" in l and not sig:
                    try:
                        r_str = l.split("RSSI")[-1].strip()
                        rssi = r_str
                        val = int(r_str.split()[0])
                        sig = max(0, min(100, int(2 * (val + 100))))
                    except Exception:
                        pass
        except Exception:
            pass

        # Fallback to nmcli if iwctl didn't provide SSID
        if not ssid:
            try:
                res = subprocess.run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY,FREQ,DEVICE", "dev", "wifi"], capture_output=True, text=True, timeout=1).stdout
                for l in res.splitlines():
                    if l.startswith("yes:"):
                        p = l.split(":")
                        if len(p) >= 3:
                            ssid = p[1]
                            connected = True
                            sig = int(p[2] or 0)
                            if len(p) >= 4:
                                sec = p[3]
                            if len(p) >= 5:
                                freq = p[4]
                            if len(p) >= 6:
                                iface = p[5]
            except Exception:
                pass

        if not ip and connected:
            try:
                ip_out = subprocess.run(["ip", "-brief", "address", "show", iface], capture_output=True, text=True, timeout=1).stdout
                parts = ip_out.split()
                if len(parts) >= 3:
                    ip = parts[2].split("/")[0]
            except Exception:
                pass

    return {
        "powered": powered,
        "connected": connected,
        "ssid": ssid,
        "sig": sig,
        "rssi": rssi,
        "ip": ip,
        "sec": sec,
        "freq": freq,
        "iface": iface
    }

def get_bt_info():
    powered = False
    connected = False
    connected_count = 0
    paired_count = 0
    devices = []

    try:
        show_out = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, timeout=1).stdout
        powered = "Powered: yes" in show_out
    except Exception:
        pass

    if powered:
        try:
            conn_out = subprocess.run(["bluetoothctl", "devices", "Connected"], capture_output=True, text=True, timeout=1).stdout
            conn_lines = [l for l in conn_out.splitlines() if l.strip().startswith("Device")]
            connected_count = len(conn_lines)
            connected = connected_count > 0

            paired_out = subprocess.run(["bluetoothctl", "devices", "Paired"], capture_output=True, text=True, timeout=1).stdout
            if not paired_out:
                paired_out = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=1).stdout
            paired_count = len([l for l in paired_out.splitlines() if l.strip().startswith("Device")])

            for l in conn_lines:
                parts = l.strip().split()
                if len(parts) >= 3:
                    mac = parts[1]
                    name = " ".join(parts[2:])
                    bat = -1
                    icon_type = "󰂱"
                    try:
                        info_out = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True, timeout=1).stdout
                        for il in info_out.splitlines():
                            if "Battery Percentage:" in il:
                                try:
                                    if "(" in il and ")" in il:
                                        bat = int(il.split("(")[-1].split(")")[0].strip())
                                    else:
                                        bat = int(il.split("Battery Percentage:")[-1].strip().replace("%", ""))
                                except Exception:
                                    pass
                            elif "Icon:" in il:
                                ic = il.lower()
                                if "audio" in ic or "headset" in ic or "headphone" in ic:
                                    icon_type = "󰋋"
                                elif "mouse" in ic:
                                    icon_type = "󰍽"
                                elif "keyboard" in ic:
                                    icon_type = "󰌌"
                                elif "phone" in ic:
                                    icon_type = "󰄜"
                    except Exception:
                        pass
                    devices.append({"name": name, "mac": mac, "battery": bat, "icon": icon_type})
        except Exception:
            pass

    return {
        "powered": powered,
        "connected": connected,
        "connected_count": connected_count,
        "paired_count": paired_count,
        "devices": devices
    }

def get_battery_info():
    cap = 100
    status = "Full"
    power_w = 0.0
    health = 100.0
    time_str = ""
    prof = "balanced"

    bats = glob.glob("/sys/class/power_supply/BAT*")
    if bats:
        b = bats[0]
        try:
            cap = int(open(os.path.join(b, "capacity")).read().strip())
        except Exception:
            pass
        try:
            status = open(os.path.join(b, "status")).read().strip()
        except Exception:
            pass
        try:
            p_now = int(open(os.path.join(b, "power_now")).read().strip())
            power_w = p_now / 1000000.0
        except Exception:
            try:
                c_now = int(open(os.path.join(b, "current_now")).read().strip())
                v_now = int(open(os.path.join(b, "voltage_now")).read().strip())
                power_w = (c_now * v_now) / 1e12
            except Exception:
                pass
        try:
            efull = int(open(os.path.join(b, "energy_full")).read().strip())
            edes = int(open(os.path.join(b, "energy_full_design")).read().strip())
            health = round((efull / edes) * 100, 1)
        except Exception:
            try:
                cfull = int(open(os.path.join(b, "charge_full")).read().strip())
                cdes = int(open(os.path.join(b, "charge_full_design")).read().strip())
                health = round((cfull / cdes) * 100, 1)
            except Exception:
                pass

        if power_w > 0.5:
            try:
                enow = 0
                efull = 0
                if os.path.exists(os.path.join(b, "energy_now")):
                    enow = int(open(os.path.join(b, "energy_now")).read().strip()) / 1000000.0
                    efull = int(open(os.path.join(b, "energy_full")).read().strip()) / 1000000.0
                elif os.path.exists(os.path.join(b, "charge_now")):
                    v_now = int(open(os.path.join(b, "voltage_now")).read().strip()) / 1000000.0
                    enow = (int(open(os.path.join(b, "charge_now")).read().strip()) / 1000000.0) * v_now
                    efull = (int(open(os.path.join(b, "charge_full")).read().strip()) / 1000000.0) * v_now

                if status.lower() == "discharging" and enow > 0:
                    hours = enow / power_w
                    h = int(hours)
                    m = int((hours - h) * 60)
                    time_str = f"{h}h {m}m left" if h > 0 else f"{m}m left"
                elif status.lower() == "charging" and efull > enow:
                    hours = (efull - enow) / power_w
                    h = int(hours)
                    m = int((hours - h) * 60)
                    time_str = f"{h}h {m}m to full" if h > 0 else f"{m}m to full"
            except Exception:
                pass

    try:
        res = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0 and res.stdout.strip():
            prof = res.stdout.strip()
    except Exception:
        pass

    return {
        "cap": cap,
        "status": status,
        "profile": prof,
        "power_w": round(power_w, 1),
        "health": health,
        "time_str": time_str
    }

def main():
    screen_name = ""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--screen" and len(sys.argv) > 2:
            screen_name = sys.argv[2]
        else:
            screen_name = sys.argv[1]

    audio = get_audio_info()
    bright = get_brightness_info(screen_name)
    wifi = get_wifi_info()
    bt = get_bt_info()
    bat = get_battery_info()

    output = {
        "audio": audio,
        "bright": bright,
        "wifi": wifi,
        "bt": bt,
        "bat": bat
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
