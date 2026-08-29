#!/usr/bin/env python3
"""
=============================================================================
 Hyprland Monitor Workspace Manager
 Automatically assigns the next available workspace (from default 1-4)
 to newly connected external monitors instead of spawning on workspace 5/6+.
=============================================================================
"""

import json
import os
import re
import select
import socket
import subprocess
import sys
import time

LOG_FILE = os.path.expanduser("~/.cache/monitor_workspace_manager.log")
DEFAULT_WORKSPACE_COUNT = 4


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [Monitor Manager] {msg}\n"
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(formatted)
    except Exception:
        pass


def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    with open('/dev/null', 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    with open('/dev/null', 'a+') as devnull:
        os.dup2(devnull.fileno(), sys.stdout.fileno())
        os.dup2(devnull.fileno(), sys.stderr.fileno())


def run_hyprctl(args: list) -> str:
    try:
        res = subprocess.run(["hyprctl"] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        log(f"Error running hyprctl {args}: {e}")
        return ""


def get_monitors():
    raw = run_hyprctl(["monitors", "-j"])
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def get_workspaces():
    raw = run_hyprctl(["workspaces", "-j"])
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def get_clients():
    raw = run_hyprctl(["clients", "-j"])
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def find_available_workspace(target_monitor_name: str, monitors: list, clients: list) -> int:
    """
    Find the best available workspace to assign to target_monitor_name.
    Prioritizes lowest numbered workspace in 1..DEFAULT_WORKSPACE_COUNT:
    1. Not active on any other monitor AND has no windows
    2. Not active on any other monitor
    3. Next unused workspace ID
    """
    # Active workspace IDs on other monitors
    other_monitors_active_ws = set()
    for m in monitors:
        if m.get("name") != target_monitor_name:
            active_ws = m.get("activeWorkspace", {})
            if active_ws and isinstance(active_ws, dict) and "id" in active_ws:
                other_monitors_active_ws.add(active_ws["id"])

    # Workspaces that contain windows
    ws_with_windows = set()
    for c in clients:
        ws = c.get("workspace", {})
        if ws and isinstance(ws, dict) and "id" in ws:
            ws_with_windows.add(ws["id"])

    # 1. Look for an empty workspace in 1..DEFAULT_WORKSPACE_COUNT not active on another monitor
    for ws_id in range(1, DEFAULT_WORKSPACE_COUNT + 1):
        if ws_id not in other_monitors_active_ws and ws_id not in ws_with_windows:
            return ws_id

    # 2. Look for any workspace in 1..DEFAULT_WORKSPACE_COUNT not active on another monitor
    for ws_id in range(1, DEFAULT_WORKSPACE_COUNT + 1):
        if ws_id not in other_monitors_active_ws:
            return ws_id

    # 3. Fallback: next unused workspace number
    used_ids = other_monitors_active_ws.union(ws_with_windows)
    cand = 1
    while cand in used_ids:
        cand += 1
    return cand


def assign_workspaces():
    """
    Checks all connected monitors. If any secondary/external monitor is showing an
    unexpected high workspace (e.g. >= 5) while 1..4 are available, reassign it.
    """
    monitors = get_monitors()
    if len(monitors) <= 1:
        return

    clients = get_clients()
    log(f"Evaluating {len(monitors)} connected monitors: {[m.get('name') for m in monitors]}")

    for m in monitors:
        m_name = m.get("name")
        active_ws = m.get("activeWorkspace", {}).get("id", 1)
        
        # If external monitor ended up on workspace > DEFAULT_WORKSPACE_COUNT
        if active_ws > DEFAULT_WORKSPACE_COUNT:
            best_ws = find_available_workspace(m_name, monitors, clients)
            log(f"Monitor {m_name} is on workspace {active_ws}. Reassigning to available workspace {best_ws}...")
            
            # Move target workspace to this monitor and focus it
            run_hyprctl(["dispatch", "moveworkspacetomonitor", f"{best_ws},{m_name}"])
            run_hyprctl(["dispatch", "focusmonitor", m_name])
            run_hyprctl(["dispatch", "workspace", str(best_ws)])
            
            # Refresh local monitors state
            monitors = get_monitors()


def assign_monitor_workspace(monitor_name: str):
    """
    Assign an available workspace specifically to the newly added monitor_name.
    """
    time.sleep(0.15)  # Allow Hyprland to finish monitor setup
    monitors = get_monitors()
    clients = get_clients()
    
    target_mon = next((m for m in monitors if m.get("name") == monitor_name), None)
    if not target_mon:
        log(f"Monitor {monitor_name} not found in monitors list.")
        return

    best_ws = find_available_workspace(monitor_name, monitors, clients)
    log(f"New monitor {monitor_name} connected. Assigning available workspace {best_ws}...")
    
    run_hyprctl(["dispatch", "moveworkspacetomonitor", f"{best_ws},{monitor_name}"])
    run_hyprctl(["dispatch", "focusmonitor", monitor_name])
    run_hyprctl(["dispatch", "workspace", str(best_ws)])


def get_hypr_socket2(timeout_sec=15.0):
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    start_time = time.time()
    
    while (time.time() - start_time) < timeout_sec:
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
                os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = sig

        if sig:
            sock2_path = os.path.join(xdg_runtime, "hypr", sig, ".socket2.sock")
            if os.path.exists(sock2_path):
                return sock2_path

        time.sleep(0.3)
    return None


def listen_events():
    sock2_path = get_hypr_socket2()
    if not sock2_path:
        log("Could not locate Hyprland socket2.sock")
        return

    log(f"Connected to Hyprland event socket: {sock2_path}")
    
    # Run initial assignment in case monitor was plugged before script started
    try:
        assign_workspaces()
    except Exception as e:
        log(f"Error in initial assign_workspaces: {e}")

    while True:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(sock2_path)
            buffer = ""
            
            while True:
                data = s.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="ignore")
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for monitor connection events
                    # Events: 'monitoradded>>HDMI-A-1' or 'monitoraddedv2>>0,HDMI-A-1,...'
                    if line.startswith("monitoradded>>"):
                        mon_name = line.split(">>", 1)[1].strip()
                        log(f"Received event: {line}")
                        assign_monitor_workspace(mon_name)
                    elif line.startswith("monitoraddedv2>>"):
                        parts = line.split(">>", 1)[1].split(",")
                        mon_name = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                        log(f"Received event: {line}")
                        assign_monitor_workspace(mon_name)
        except Exception as e:
            log(f"Socket connection error: {e}. Retrying in 2 seconds...")
            time.sleep(2.0)


def main():
    args = sys.argv[1:]
    if "--daemon" in args or "-d" in args:
        daemonize()
        listen_events()
    elif "--once" in args or "--assign" in args:
        assign_workspaces()
    else:
        listen_events()


if __name__ == "__main__":
    main()
