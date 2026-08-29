#!/usr/bin/env python3
"""
Hyprland Window Scaler & On-Screen Display (OSD) Notification
Allows scaling/resizing the active window and immediately displays its dimensions on screen.
"""

import sys
import json
import subprocess
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STEP = 40  # pixels per step

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

def get_active_window():
    raw = run_cmd(["hyprctl", "activewindow", "-j"])
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def get_active_monitor():
    raw = run_cmd(["hyprctl", "monitors", "-j"])
    if not raw:
        return None
    try:
        monitors = json.loads(raw)
        for m in monitors:
            if m.get("focused"):
                return m
        if monitors:
            return monitors[0]
    except Exception:
        return None
    return None

def main():
    dx = 0
    dy = 0
    action_label = "Current Size"

    if len(sys.argv) >= 3:
        try:
            dx = int(sys.argv[1])
            dy = int(sys.argv[2])
            action_label = "Resized"
        except ValueError:
            pass
    elif len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg in ["scale_up", "grow", "in", "+", "plus", "expand"]:
            dx, dy = STEP, STEP
            action_label = "Scaled Up"
        elif arg in ["scale_down", "shrink", "out", "-", "minus"]:
            dx, dy = -STEP, -STEP
            action_label = "Scaled Down"
        elif arg in ["right", "widen"]:
            dx, dy = STEP, 0
            action_label = "Widened"
        elif arg in ["left", "narrow"]:
            dx, dy = -STEP, 0
            action_label = "Narrowed"
        elif arg in ["up", "taller"]:
            dx, dy = 0, -STEP
            action_label = "Shrunk Height"
        elif arg in ["down", "shorter"]:
            dx, dy = 0, STEP
            action_label = "Expanded Height"
        elif arg in ["show", "info"]:
            dx, dy = 0, 0
            action_label = "Window Size"

    # Execute resize dispatch if delta given
    if dx != 0 or dy != 0:
        lua_dispatch = f"hl.dsp.window.resize({{ x = {dx}, y = {dy}, relative = true }})"
        run_cmd(["hyprctl", "dispatch", lua_dispatch])

    win = get_active_window()
    if not win or not win.get("address"):
        run_cmd([
            "notify-send",
            "-r", "9119",
            "-t", "1000",
            "-u", "low",
            "-a", "Hyprland",
            "-h", "string:x-canonical-private-synchronous:window_scale",
            "Window Scaling",
            "No active window focused"
        ])
        return

    # Window details
    title = win.get("title", "")
    if len(title) > 32:
        title = title[:29] + "..."
    app_class = win.get("class", "App")
    size = win.get("size", [0, 0])
    pos = win.get("at", [0, 0])
    w, h = size[0], size[1]
    floating = win.get("floating", False)
    mode = "Floating" if floating else "Tiled"

    # Monitor info to compute screen coverage percentage
    mon = get_active_monitor()
    pct_info = ""
    if mon:
        mon_w = mon.get("width", 1)
        mon_h = mon.get("height", 1)
        scale = mon.get("scale", 1.0)
        # Convert physical monitor size to logical size
        log_w = int(mon_w / scale)
        log_h = int(mon_h / scale)
        pct_w = int((w / log_w) * 100)
        pct_h = int((h / log_h) * 100)
        pct_info = f" ({pct_w}% × {pct_h}% screen)"

    summary = f"📐 {w} × {h} px{pct_info}"
    body = f"<b>{app_class}</b>  ·  <i>{mode}</i>\nPosition: ({pos[0]}, {pos[1]})  ·  {action_label}"

    run_cmd([
        "notify-send",
        "-r", "9119",
        "-t", "1200",
        "-u", "low",
        "-a", "Hyprland",
        "-h", "string:x-canonical-private-synchronous:window_scale",
        summary,
        body
    ])

if __name__ == "__main__":
    main()
