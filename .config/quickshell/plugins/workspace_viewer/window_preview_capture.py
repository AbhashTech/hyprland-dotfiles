#!/usr/bin/env python3
"""
=============================================================================
 Quickshell Window Preview Snapshot Capture Daemon
 Automatically captures and caches thumbnail snapshots of open windows
 for the Workspace Viewer and Hover Preview in Quickshell using grim.
=============================================================================
"""

import json
import os
import re
import socket
import subprocess
import sys
import time

CACHE_DIR = os.path.expanduser("~/.cache/quickshell/window_previews")
os.makedirs(CACHE_DIR, exist_ok=True)


def sanitize_address(addr: str) -> str:
    if not addr:
        return ""
    return addr.strip().replace("0x", "")


def run_hyprctl(args: list) -> str:
    try:
        res = subprocess.run(["hyprctl"] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""


def capture_window(client: dict):
    try:
        addr = client.get("address", "")
        clean_addr = sanitize_address(addr)
        if not clean_addr:
            return

        at = client.get("at", [0, 0])
        size = client.get("size", [0, 0])
        x, y = at[0], at[1]
        w, h = size[0], size[1]

        if w <= 10 or h <= 10:
            return

        out_path = os.path.join(CACHE_DIR, f"{clean_addr}.png")
        geom = f"{x},{y} {w}x{h}"
        subprocess.run(["grim", "-g", geom, out_path], capture_output=True)
    except Exception:
        pass


def capture_all_visible():
    try:
        raw = run_hyprctl(["clients", "-j"])
        if not raw:
            return
        clients = json.loads(raw)
        
        # Get active workspace
        raw_ws = run_hyprctl(["activeworkspace", "-j"])
        active_ws_id = 1
        if raw_ws:
            active_ws = json.loads(raw_ws)
            active_ws_id = active_ws.get("id", 1)

        for c in clients:
            if c.get("workspace", {}).get("id") == active_ws_id and not c.get("hidden", False):
                capture_window(c)
    except Exception:
        pass


def get_hypr_socket():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    sock_path = os.path.join(xdg_runtime, "hypr", sig, ".socket2.sock")
    return sock_path


def main():
    # Initial capture
    capture_all_visible()

    sock_path = get_hypr_socket()
    if not os.path.exists(sock_path):
        # Fallback to periodic loop if socket2 is unavailable
        while True:
            time.sleep(3)
            capture_all_visible()
        return

    while True:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(sock_path)
            last_capture = time.time()

            while True:
                data = s.recv(4096)
                if not data:
                    break
                events = data.decode("utf-8", errors="ignore").splitlines()
                for ev in events:
                    if any(ev.startswith(prefix) for prefix in ("activewindow>>", "workspace>>", "openwindow>>", "movewindow>>", "fullscreen>>")):
                        now = time.time()
                        if now - last_capture > 0.3:
                            time.sleep(0.1)  # small delay for compositor render
                            capture_all_visible()
                            last_capture = time.time()
        except Exception:
            time.sleep(2)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "capture-now":
        capture_all_visible()
    else:
        main()
