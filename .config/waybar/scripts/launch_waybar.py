#!/usr/bin/env python3
"""
Waybar Hyprland IPC Compatibility Bridge & Robust Supervisor
Fixes workspace on-click actions when running Hyprland with Lua configuration (v0.55+ / v0.56+).
Translates legacy text-based IPC dispatch commands sent by Waybar into modern Lua dispatchers.
Ensures Waybar reliably probes Hyprland IPC socket readiness before launching.
"""

import os
import sys
import time
import socket
import select
import signal
import subprocess
import re
import shutil
import traceback

LOG_FILE = os.path.expanduser("~/.cache/waybar_proxy.log")
WAYBAR_LOG = os.path.expanduser("~/.cache/waybar.log")
stop_requested = False

def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [Waybar Proxy] {msg}\n"
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

def probe_socket(sock_path: str) -> bool:
    """Test if Hyprland's socket is genuinely accepting connections and responding."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(sock_path)
        s.sendall(b"j/monitors")
        data = s.recv(256)
        s.close()
        return bool(data)
    except Exception:
        return False

def get_hypr_paths(timeout_sec=20.0):
    start_time = time.time()
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    
    real_sig = None
    real_sock = None
    real_sock2 = None

    while (time.time() - start_time) < timeout_sec:
        real_sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        hypr_dir = os.path.join(xdg_runtime, "hypr")
        
        if not real_sig and os.path.exists(hypr_dir):
            instances = [
                d for d in os.listdir(hypr_dir)
                if os.path.isdir(os.path.join(hypr_dir, d))
                and not d.endswith("_waybar")
                and not d.endswith("_test")
            ]
            if instances:
                real_sig = sorted(instances)[-1]
                os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = real_sig

        if real_sig:
            real_dir = os.path.join(xdg_runtime, "hypr", real_sig)
            sock1 = os.path.join(real_dir, ".socket.sock")
            sock2 = os.path.join(real_dir, ".socket2.sock")
            if os.path.exists(sock1) and os.path.exists(sock2):
                if probe_socket(sock1):
                    real_sock = sock1
                    real_sock2 = sock2
                    break

        time.sleep(0.2)

    if not real_sig or not real_sock or not real_sock2:
        log("Hyprland sockets probe timed out. Launching Waybar directly.")
        os.execvp("waybar", ["waybar"] + [arg for arg in sys.argv[1:] if arg not in ("--daemon", "-d")])

    proxy_sig = f"{real_sig}_waybar"
    proxy_dir = os.path.join(xdg_runtime, "hypr", proxy_sig)
    proxy_sock = os.path.join(proxy_dir, ".socket.sock")
    proxy_sock2 = os.path.join(proxy_dir, ".socket2.sock")

    return real_sig, real_sock, real_sock2, proxy_sig, proxy_dir, proxy_sock, proxy_sock2

def translate_command(data: bytes) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data

    # Translate workspace switching
    m_ws = re.search(r"dispatch\s+(?:focusworkspaceoncurrentmonitor|workspace)\s+(name:)?(\S+)", text)
    if m_ws:
        is_name, ws = m_ws.groups()
        if is_name:
            target = f'\"name:{ws}\"'
        elif ws.isdigit() or (ws.startswith("-") and ws[1:].isdigit()):
            target = ws
        elif ws in ("e+1", "e-1", "m+1", "m-1"):
            target = f'\"{ws}\"'
        else:
            target = f'\"{ws}\"'
        return f"[[BATCH]]/dispatch hl.dsp.focus({{ workspace = {target} }})\n".encode("utf-8")

    # Translate special workspace toggle
    m_special = re.search(r"dispatch\s+togglespecialworkspace(?:\s+(\S+))?", text)
    if m_special:
        sp = m_special.group(1)
        if sp:
            return f'[[BATCH]]/dispatch hl.dsp.workspace.toggle_special("{sp}")\n'.encode("utf-8")
        else:
            return b"[[BATCH]]/dispatch hl.dsp.workspace.toggle_special()\n"

    # Translate window close / kill
    m_win = re.search(r"dispatch\s+closewindow\s+(\S+)", text)
    if m_win:
        return f'[[BATCH]]/dispatch hl.dsp.window.close("{m_win.group(1)}")\n'.encode("utf-8")

    return data

def main():
    global stop_requested
    try:
        args = sys.argv[1:]
        is_daemon = "--daemon" in args or "-d" in args
        filtered_args = [a for a in args if a not in ("--daemon", "-d")]

        if is_daemon:
            daemonize()

        log("Starting Waybar launcher bridge & supervisor...")
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

        real_sig, real_sock, real_sock2, proxy_sig, proxy_dir, proxy_sock, proxy_sock2 = get_hypr_paths()
        log(f"Hyprland signature verified & ready: {real_sig}")

        os.makedirs(proxy_dir, exist_ok=True)

        # Setup .socket2.sock symlink (event listener)
        if os.path.exists(proxy_sock2) or os.path.islink(proxy_sock2):
            try:
                os.remove(proxy_sock2)
            except OSError:
                pass
        try:
            os.symlink(real_sock2, proxy_sock2)
        except Exception as e:
            log(f"Error creating socket2 symlink: {e}")

        # Setup .socket.sock listener (command dispatcher)
        if os.path.exists(proxy_sock):
            try:
                os.remove(proxy_sock)
            except OSError:
                pass

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(proxy_sock)
        server.listen(64)
        server.setblocking(False)

        # Launch waybar subprocess with proxy signature and verified Wayland display
        env = dict(os.environ)
        env["HYPRLAND_INSTANCE_SIGNATURE"] = proxy_sig
        
        curr_wd = os.environ.get("WAYLAND_DISPLAY")
        if not curr_wd or not os.path.exists(os.path.join(xdg_runtime, curr_wd)):
            try:
                wl_socks = [
                    f for f in os.listdir(xdg_runtime)
                    if f.startswith("wayland-") and not f.endswith(".lock")
                ]
                if wl_socks:
                    wl_socks.sort(key=lambda s: os.path.getmtime(os.path.join(xdg_runtime, s)), reverse=True)
                    curr_wd = wl_socks[0]
            except Exception:
                pass
        if curr_wd:
            env["WAYLAND_DISPLAY"] = curr_wd
            log(f"Wayland display resolved: {curr_wd}")

        env["GDK_BACKEND"] = "wayland"
        env["XDG_CURRENT_DESKTOP"] = "Hyprland"
        env["XDG_SESSION_TYPE"] = "wayland"
        env["XDG_SESSION_DESKTOP"] = "Hyprland"

        log(f"Spawning waybar with args: {filtered_args}")
        waybar_log_fd = open(WAYBAR_LOG, "a")
        waybar_proc = subprocess.Popen(["waybar"] + filtered_args, env=env, stdout=waybar_log_fd, stderr=waybar_log_fd)
        last_spawn_time = time.time()
        crash_count = 0

        def cleanup(*args):
            global stop_requested
            stop_requested = True
            log("Cleaning up Waybar proxy bridge...")
            if waybar_proc and waybar_proc.poll() is None:
                waybar_proc.terminate()
                try:
                    waybar_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    waybar_proc.kill()
            try:
                server.close()
            except Exception:
                pass
            try:
                waybar_log_fd.close()
            except Exception:
                pass
            shutil.rmtree(proxy_dir, ignore_errors=True)
            sys.exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)

        inputs = [server]

        while not stop_requested:
            # Check if waybar exited unexpectedly and auto-restart if needed
            if waybar_proc.poll() is not None:
                code = waybar_proc.returncode
                log(f"Waybar process exited with code {code}")
                if stop_requested:
                    break
                
                # Reset crash count if Waybar was running stably for more than 5s
                if (time.time() - last_spawn_time) > 5.0:
                    crash_count = 0

                crash_count += 1
                if crash_count > 15:
                    log("Too many consecutive Waybar crashes. Exiting supervisor.")
                    break

                log(f"Auto-recovering: restarting Waybar (attempt {crash_count})...")
                time.sleep(0.5)
                waybar_proc = subprocess.Popen(["waybar"] + filtered_args, env=env, stdout=waybar_log_fd, stderr=waybar_log_fd)
                last_spawn_time = time.time()
                continue

            readable, _, exceptional = select.select(inputs, [], inputs, 0.5)

            for s in readable:
                if s is server:
                    try:
                        client_sock, _ = server.accept()
                        client_sock.settimeout(2.0)
                        data = client_sock.recv(4096)
                        if data:
                            translated = translate_command(data)
                            real_client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                            real_client.settimeout(2.0)
                            real_client.connect(real_sock)
                            real_client.sendall(translated)
                            
                            resp = b""
                            while True:
                                chunk = real_client.recv(4096)
                                if not chunk:
                                    break
                                resp += chunk
                            real_client.close()
                            client_sock.sendall(resp)
                        client_sock.close()
                    except Exception:
                        pass

        cleanup()
    except Exception as e:
        log(f"Fatal error in launch_waybar: {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
