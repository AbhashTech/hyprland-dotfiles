#!/usr/bin/env python3
"""
=============================================================================
 Waybar Active Workspace Display Brightness Monitor
 Dynamically detects the currently active / focused monitor in Hyprland
 and outputs real-time brightness metrics for that specific display.
 Supports Laptop Backlight (sysfs) and External Monitors (DDC/CI via cache).
=============================================================================
"""

import glob
import json
import os
import select
import signal
import socket
import subprocess
import sys
import time

CACHE_FILE = "/tmp/brightness_display_cache.json"


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_laptop_brightness():
    """Directly read sysfs for internal laptop backlight (<0.1ms)."""
    for dev_path in glob.glob("/sys/class/backlight/*"):
        b_file = os.path.join(dev_path, "brightness")
        m_file = os.path.join(dev_path, "max_brightness")
        if os.path.exists(b_file) and os.path.exists(m_file):
            try:
                with open(b_file, "r") as f:
                    curr = int(f.read().strip())
                with open(m_file, "r") as f:
                    max_b = int(f.read().strip())
                if max_b > 0:
                    pct = int(round((curr / max_b) * 100))
                    dev_name = os.path.basename(dev_path)
                    return pct, dev_name
            except Exception:
                pass

    try:
        res = subprocess.run(["brightnessctl", "-m"], capture_output=True, text=True, check=True)
        if res.stdout:
            lines = res.stdout.strip().splitlines()
            if lines:
                parts = lines[0].split(",")
                if len(parts) >= 4:
                    dev = parts[0]
                    pct = int(parts[3].rstrip("%"))
                    return pct, dev
    except Exception:
        pass

    return 50, "intel_backlight"


def get_hyprland_monitors():
    """Retrieve connected monitors list from Hyprland IPC (<2ms)."""
    try:
        res = subprocess.run(["hyprctl", "-j", "monitors"], capture_output=True, text=True, check=True)
        if res.stdout:
            return json.loads(res.stdout)
    except Exception:
        pass
    return []


def get_brightness_icon(pct):
    """Return standard brightness sun icons matching original Waybar module."""
    if pct <= 33:
        return "󰃞"
    elif pct <= 66:
        return "󰃟"
    else:
        return "󰃠"


def generate_status():
    """Generate status JSON for Waybar based on currently active display."""
    cache = load_cache()
    monitors = get_hyprland_monitors()
    laptop_pct, laptop_dev = get_laptop_brightness()

    active_mon = None
    all_displays = []

    # Map monitors
    for m in monitors:
        name = m.get("name", "")
        is_focused = m.get("focused", False)
        ws_info = m.get("activeWorkspace", {})
        ws_name = ws_info.get("name", str(ws_info.get("id", "")))
        desc = m.get("description") or m.get("model") or name

        if name.startswith("eDP") or name.startswith("LVDS"):
            pct = laptop_pct
            disp_type = "internal"
            disp_icon = "󰌢"
        else:
            cached_data = cache.get(name, {})
            pct = cached_data.get("brightness", 80)
            disp_type = "external"
            disp_icon = "🖥️"

        disp_entry = {
            "name": name,
            "desc": desc,
            "pct": pct,
            "type": disp_type,
            "icon": disp_icon,
            "ws": ws_name,
            "focused": is_focused
        }
        all_displays.append(disp_entry)
        if is_focused:
            active_mon = disp_entry

    if not active_mon and all_displays:
        active_mon = all_displays[0]
    elif not active_mon:
        active_mon = {
            "name": "eDP-1",
            "desc": "Built-in Display",
            "pct": laptop_pct,
            "type": "internal",
            "icon": "󰌢",
            "ws": "1",
            "focused": True
        }
        all_displays.append(active_mon)

    act_pct = active_mon["pct"]
    act_name = active_mon["name"]
    act_desc = active_mon["desc"]
    act_type = active_mon["type"]
    act_ws = active_mon["ws"]
    is_ext = (act_type == "external")

    # Use standard brightness sun icon (󰃞, 󰃟, 󰃠)
    sun_icon = get_brightness_icon(act_pct)
    text = f"{sun_icon} {act_pct}%"

    # Tooltip construction
    tooltip_lines = [
        f"<b>Active Display:</b> {act_desc} ({act_name})",
        f"<b>Active Workspace:</b> {act_ws}",
        f"<b>Current Brightness:</b> {act_pct}%",
        "",
        "<b>Connected Displays:</b>"
    ]

    for d in all_displays:
        star = " ★" if d["focused"] else ""
        tooltip_lines.append(f"  • {d['icon']} <b>{d['name']}</b>: {d['pct']}% ({d['desc']}){star}")

    tooltip_lines.extend([
        "",
        "• Scroll: Adjust Active Screen Brightness (±5%)",
        "• Left Click: Display & Brightness Sliders",
        "• Right Click: Toggle Night Light",
        "• Middle Click: Interactive TUI Mixer"
    ])

    classes = [act_type, "active"]
    if is_ext:
        classes.append("external-display")
    else:
        classes.append("laptop-display")

    out = {
        "text": text,
        "alt": text,
        "tooltip": "\n".join(tooltip_lines),
        "class": " ".join(classes),
        "percentage": act_pct
    }
    return out


def find_hyprland_socket2():
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    hypr_dir = os.path.join(xdg_runtime, "hypr")
    
    if not sig and os.path.exists(hypr_dir):
        instances = [
            d for d in os.listdir(hypr_dir)
            if os.path.isdir(os.path.join(hypr_dir, d))
            and not d.endswith("_waybar")
            and not d.endswith("_test")
        ]
        if instances:
            sig = sorted(instances)[-1]

    if sig:
        sock2 = os.path.join(hypr_dir, sig, ".socket2.sock")
        if os.path.exists(sock2):
            return sock2
    return None


def run_stream():
    """Event-driven live streaming mode for Waybar with zero idle CPU."""
    print(json.dumps(generate_status(), ensure_ascii=False), flush=True)

    sock_path = find_hyprland_socket2()
    sock = None
    if sock_path:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(sock_path)
            sock.setblocking(False)
        except Exception:
            sock = None

    last_output_time = time.time()

    def signal_handler(signum, frame):
        try:
            print(json.dumps(generate_status(), ensure_ascii=False), flush=True)
        except Exception:
            pass

    signal.signal(signal.SIGUSR1, signal_handler)
    try:
        signal.signal(signal.SIGRTMIN + 11, signal_handler)
    except Exception:
        pass

    buffer = ""
    while True:
        try:
            rlist = [sock] if sock else []
            readable, _, _ = select.select(rlist, [], [], 2.0)

            if readable and sock in readable:
                data = sock.recv(4096)
                if not data:
                    sock.close()
                    sock = None
                    time.sleep(1)
                    sock_path = find_hyprland_socket2()
                    if sock_path:
                        try:
                            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                            sock.connect(sock_path)
                            sock.setblocking(False)
                        except Exception:
                            sock = None
                    continue

                buffer += data.decode("utf-8", errors="ignore")
                lines = buffer.split("\n")
                buffer = lines[-1]
                events = lines[:-1]

                should_update = False
                for evt in events:
                    if any(evt.startswith(prefix) for prefix in [
                        "focusedmon>>", "workspace>>", "activewindow>>",
                        "monitoradded>>", "monitorremoved>>", "configreloaded>>"
                    ]):
                        should_update = True
                        break

                if should_update:
                    print(json.dumps(generate_status(), ensure_ascii=False), flush=True)
                    last_output_time = time.time()
            else:
                curr_time = time.time()
                if curr_time - last_output_time >= 2.0:
                    print(json.dumps(generate_status(), ensure_ascii=False), flush=True)
                    last_output_time = curr_time

        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(1)
            print(json.dumps(generate_status(), ensure_ascii=False), flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--stream", "-s", "stream"]:
        run_stream()
    else:
        print(json.dumps(generate_status(), ensure_ascii=False))


if __name__ == "__main__":
    main()
