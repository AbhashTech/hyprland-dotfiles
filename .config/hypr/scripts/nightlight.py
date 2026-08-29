#!/usr/bin/env python3
"""
Hyprland Night Light / Blue Light Filter Utility
Uses hyprsunset (or wlsunset) to dynamically adjust color temperature.
"""

import sys
import os
import signal
import shutil
import subprocess
from pathlib import Path

PID_FILE = Path("/tmp/hypr_nightlight.pid")
STATE_FILE = Path("/tmp/hypr_nightlight.state")
WARM_TEMP = 3800

def notify(title, body, icon="weather-clear-night"):
    if not shutil.which("notify-send"):
        return
    subprocess.Popen([
        "notify-send",
        "-a", "Night Light",
        "-i", icon,
        "-t", "2500",
        title, body
    ])

def is_running():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return pid
        except Exception:
            PID_FILE.unlink(missing_ok=True)
            STATE_FILE.unlink(missing_ok=True)
    return None

def stop():
    pid = is_running()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        PID_FILE.unlink(missing_ok=True)
        STATE_FILE.unlink(missing_ok=True)
        notify("☀️ Night Light Disabled", "Display color temperature restored to normal (6500K).", "weather-clear")
    else:
        # Check for any stray instances
        subprocess.run(["pkill", "-x", "hyprsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-x", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start(temp=WARM_TEMP):
    stop()
    binary = shutil.which("hyprsunset") or shutil.which("wlsunset")
    if not binary:
        notify("❌ Error", "Neither hyprsunset nor wlsunset is installed.\nRun: sudo pacman -S hyprsunset (or wlsunset)", "dialog-error")
        return

    cmd = []
    if "hyprsunset" in binary:
        cmd = ["hyprsunset", "-t", str(temp)]
    else:
        cmd = ["wlsunset", "-t", str(temp), "-T", "6500"]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PID_FILE.write_text(str(proc.pid))
        STATE_FILE.write_text(str(temp))
        notify("🌙 Night Light Enabled", f"Warm color temperature set to <b>{temp}K</b>.", "weather-clear-night")
    except Exception as e:
        notify("❌ Error", f"Could not start night light: {e}", "dialog-error")

def toggle():
    if is_running():
        stop()
    else:
        start()

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "toggle":
        toggle()
    elif sys.argv[1] in ["on", "start"]:
        temp = int(sys.argv[2]) if len(sys.argv) > 2 else WARM_TEMP
        start(temp)
    elif sys.argv[1] in ["off", "stop"]:
        stop()
    elif sys.argv[1] == "status":
        print("active" if is_running() else "inactive")

if __name__ == "__main__":
    main()
