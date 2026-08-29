#!/usr/bin/env python3
"""
=============================================================================
 Waybar Custom Battery Status & Power Profile Module
 Outputs JSON with live capacity, charging state, power profile,
 health metrics, and Pango color formatting for the battery icon.
=============================================================================
"""

import glob
import json
import os
import sys


def get_profile():
    try:
        import dbus
        bus = dbus.SystemBus()
        pp = bus.get_object('net.hadess.PowerProfiles', '/net/hadess/PowerProfiles')
        props = dbus.Interface(pp, 'org.freedesktop.DBus.Properties')
        return str(props.Get('net.hadess.PowerProfiles', 'ActiveProfile'))
    except Exception:
        pass
    
    try:
        import shutil, subprocess
        if shutil.which("powerprofilesctl"):
            res = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True)
            if res.stdout:
                return res.stdout.strip()
    except Exception:
        pass
    return "balanced"


def get_battery_info():
    bats = glob.glob('/sys/class/power_supply/BAT*')
    if not bats:
        return {
            "capacity": 100,
            "status": "Full",
            "health": 100,
            "time_rem": ""
        }
    
    bp = bats[0]
    cap = 100
    status = "Full"
    health = 100
    time_rem = ""

    try:
        if os.path.exists(f"{bp}/capacity"):
            with open(f"{bp}/capacity") as f:
                cap = int(f.read().strip())
    except Exception:
        pass

    try:
        if os.path.exists(f"{bp}/status"):
            with open(f"{bp}/status") as f:
                status = f.read().strip()
    except Exception:
        pass

    try:
        ef = ef_des = None
        if os.path.exists(f"{bp}/energy_full"):
            with open(f"{bp}/energy_full") as f:
                ef = int(f.read().strip())
        if os.path.exists(f"{bp}/energy_full_design"):
            with open(f"{bp}/energy_full_design") as f:
                ef_des = int(f.read().strip())
        elif os.path.exists(f"{bp}/charge_full") and os.path.exists(f"{bp}/charge_full_design"):
            with open(f"{bp}/charge_full") as f:
                ef = int(f.read().strip())
            with open(f"{bp}/charge_full_design") as f:
                ef_des = int(f.read().strip())

        if ef and ef_des and ef_des > 0:
            health = min(100, max(0, int((ef / ef_des) * 100)))
    except Exception:
        pass

    try:
        en = pn = None
        if os.path.exists(f"{bp}/energy_now"):
            with open(f"{bp}/energy_now") as f:
                en = int(f.read().strip())
        if os.path.exists(f"{bp}/power_now"):
            with open(f"{bp}/power_now") as f:
                pn = int(f.read().strip())

        if en and pn and pn > 0:
            if status.lower() == "discharging":
                hours = en / pn
                hrs = int(hours)
                mins = int((hours - hrs) * 60)
                time_rem = f"{hrs}h {mins:02d}m remaining"
            elif status.lower() == "charging" and ef:
                hours = (ef - en) / pn
                hrs = int(hours)
                mins = int((hours - hrs) * 60)
                time_rem = f"{hrs}h {mins:02d}m until full"
    except Exception:
        pass

    return {
        "capacity": cap,
        "status": status,
        "health": health,
        "time_rem": time_rem
    }


def main():
    info = get_battery_info()
    cap = info["capacity"]
    status = info["status"]
    health = info["health"]
    time_rem = info["time_rem"]

    profile = get_profile().lower().strip()
    if "save" in profile:
        profile_key = "power-saver"
        profile_label = "Power Saver"
        profile_icon = "󰌪"
        icon_color = "#a6e3a1"  # Green
    elif "perf" in profile:
        profile_key = "performance"
        profile_label = "Performance"
        profile_icon = "󰓅"
        icon_color = "#f38ba8"  # Red
    else:
        profile_key = "balanced"
        profile_label = "Balanced"
        profile_icon = "󰗑"
        icon_color = "#fab387"  # Orange

    if status.lower() == "charging":
        icon = "󰂄"
    elif status.lower() == "full" or status.lower() == "not charging":
        icon = "󰚥"
    else:
        icons = ["󰂎", "󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]
        idx = min(len(icons) - 1, max(0, cap // 10))
        icon = icons[idx]

    classes = [profile_key]
    if status.lower() == "charging":
        classes.append("charging")
    elif status.lower() == "full":
        classes.append("plugged")

    if cap <= 15:
        classes.append("critical")
    elif cap <= 30:
        classes.append("warning")

    tooltip_lines = [
        f"<b>⚡ Mode:</b> <span color='{icon_color}'><b>{profile_icon} {profile_label}</b></span>",
        f"<b>󰁹 Battery:</b> {cap}% ({status})",
    ]
    if time_rem:
        tooltip_lines.append(f"<b>⏱ Time:</b> {time_rem}")
    tooltip_lines.append(f"<b>󰂑 Health:</b> {health}%")
    tooltip_lines.append("<i>• Right Click: Change Power Profile</i>")

    # Format text with colored icon
    formatted_text = f"<span color='{icon_color}'>{icon}</span> {cap}%"

    out = {
        "text": formatted_text,
        "alt": formatted_text,
        "tooltip": "\n".join(tooltip_lines),
        "class": " ".join(classes),
        "percentage": cap
    }

    print(json.dumps(out))


if __name__ == "__main__":
    main()
