#!/usr/bin/env python3
"""
Hyprland Screen Brightness Control Utility with OSD & Interactive Menu
Supports laptop internal backlight (brightnessctl) and external monitors (ddcutil).
"""

import sys
import subprocess
import os
import shutil
import re

BRIGHTNESS_NOTIF_ID = "9124"
DEFAULT_STEP = 5

def run_cmd(cmd):
    """Run a shell command and return stdout as string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

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
    run_cmd(cmd)

# ---------------------------------------------------------
# Laptop Screen Backlight (brightnessctl)
# ---------------------------------------------------------

def get_brightness_info():
    """Retrieve current brightness percentage and device name."""
    raw = run_cmd(["brightnessctl", "-m"])
    # Format: device_name,class,current_val,percentage,max_val
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

def notify_brightness_osd(device_label=None):
    """Display OSD notification for screen brightness."""
    pct, dev = get_brightness_info()
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
    show_notification(title, body, icon, percentage=pct)

def change_brightness(delta):
    """Adjust laptop display brightness by delta percentage."""
    if delta > 0:
        run_cmd(["brightnessctl", "-e4", "-n2", "set", f"{delta}%+"])
    else:
        run_cmd(["brightnessctl", "-e4", "-n2", "set", f"{abs(delta)}%-"])
    notify_brightness_osd()

def set_brightness(target_percent):
    """Set exact brightness percentage."""
    target_percent = max(1, min(100, target_percent))
    run_cmd(["brightnessctl", "-e4", "-n2", "set", f"{target_percent}%"])
    notify_brightness_osd()

# ---------------------------------------------------------
# External Monitor Brightness (ddcutil)
# ---------------------------------------------------------

def change_ddc_brightness(delta):
    """Adjust external monitor brightness via ddcutil."""
    sign = "+" if delta > 0 else "-"
    run_cmd(["ddcutil", "--noverify", "setvcp", "10", sign, str(abs(delta))])
    
    # Try reading current value
    val = None
    res = run_cmd(["ddcutil", "--noverify", "getvcp", "10"])
    if res:
        match = re.search(r'current value =\s*(\d+)', res)
        if match:
            val = int(match.group(1))

    pct = val if val is not None else (50 if delta > 0 else 40)
    bar = build_progress_bar(pct)
    icon = "video-display"
    title = f"🖥️ Ext Monitor Brightness: {pct}%" if val is not None else "🖥️ External Monitor Brightness"
    body = f"<b>External Display (DDC/CI)</b>\n{bar}"
    show_notification(title, body, icon, percentage=pct, tag="ext_brightness_osd")

# ---------------------------------------------------------
# Interactive Menu
# ---------------------------------------------------------

def open_dmenu(prompt, options):
    """Display an interactive menu using fuzzel or wofi."""
    input_str = "\n".join(options)
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", f"{prompt}: ", "--width", "38", "--lines", "10"]
    else:
        cmd = [
            "wofi",
            "--dmenu",
            "--prompt", prompt,
            "--width", "420",
            "--height", "380",
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
    curr_pct, dev = get_brightness_info()
    options = [
        f"<b>★ Current:</b> {dev} ({curr_pct}%)",
        "─── BRIGHTNESS PRESETS ───",
        "☀️ 100% (Maximum / Daylight)",
        "☀️ 80%",
        "☀️ 60%",
        "☀️ 50% (Balanced)",
        "☀️ 40%",
        "☀️ 25% (Dim / Indoor)",
        "☀️ 10% (Night / Low Power)",
        "☀️ 1% (Minimum)",
        "─── ACTIONS ───",
        "🖥️ Adjust External Monitor (+10%)",
        "🖥️ Adjust External Monitor (-10%)",
    ]

    selected = open_dmenu("Screen Brightness", options)
    if not selected:
        return

    if "100%" in selected:
        set_brightness(100)
    elif "80%" in selected:
        set_brightness(80)
    elif "60%" in selected:
        set_brightness(60)
    elif "50%" in selected:
        set_brightness(50)
    elif "40%" in selected:
        set_brightness(40)
    elif "25%" in selected:
        set_brightness(25)
    elif "10%" in selected:
        set_brightness(10)
    elif "1%" in selected:
        set_brightness(1)
    elif "Adjust External Monitor (+10%)" in selected:
        change_ddc_brightness(10)
    elif "Adjust External Monitor (-10%)" in selected:
        change_ddc_brightness(-10)

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

    if cmd in ["up", "+", "raise", "increase"]:
        change_brightness(step)
    elif cmd in ["down", "-", "lower", "decrease"]:
        change_brightness(-step)
    elif cmd in ["set"]:
        set_brightness(step)
    elif cmd in ["show", "status", "info"]:
        notify_brightness_osd()
    elif cmd in ["ddc-up", "ext-up"]:
        change_ddc_brightness(step if len(sys.argv) >= 3 else 10)
    elif cmd in ["ddc-down", "ext-down"]:
        change_ddc_brightness(-step if len(sys.argv) >= 3 else -10)
    elif cmd in ["menu", "dmenu", "gui"]:
        interactive_menu()
    else:
        print(f"Unknown action: {cmd}")
        print("Usage: brightness_control.py [up|down|set|show|ddc-up|ddc-down|menu]")
        sys.exit(1)

if __name__ == "__main__":
    main()
