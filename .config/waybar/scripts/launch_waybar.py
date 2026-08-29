#!/usr/bin/env python3
"""
Waybar Hyprland IPC Compatibility Bridge
Fixes workspace on-click actions when running Hyprland with Lua configuration (v0.55+ / v0.56+).
Translates legacy text-based IPC dispatch commands sent by Waybar into modern Lua dispatchers.
"""

import os
import sys
import socket
import select
import signal
import subprocess
import re
import shutil

def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.exit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    with open('/dev/null', 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())
    with open('/dev/null', 'a+') as devnull:
        os.dup2(devnull.fileno(), sys.stdout.fileno())
        os.dup2(devnull.fileno(), sys.stderr.fileno())

def get_hypr_paths():
    real_sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    if not real_sig:
        hypr_dir = os.path.join(xdg_runtime, "hypr")
        if os.path.exists(hypr_dir):
            instances = [d for d in os.listdir(hypr_dir) if os.path.isdir(os.path.join(hypr_dir, d)) and not d.endswith("_waybar") and not d.endswith("_test")]
            if instances:
                real_sig = sorted(instances)[-1]
                os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = real_sig

    if not real_sig:
        print("[Waybar Proxy] HYPRLAND_INSTANCE_SIGNATURE not found. Launching waybar directly...", file=sys.stderr)
        os.execvp("waybar", ["waybar"] + [arg for arg in sys.argv[1:] if arg != "--daemon"])

    real_dir = os.path.join(xdg_runtime, "hypr", real_sig)
    real_sock = os.path.join(real_dir, ".socket.sock")
    real_sock2 = os.path.join(real_dir, ".socket2.sock")
    
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
    # Matches: dispatch workspace 1, dispatch workspace name:work, dispatch focusworkspaceoncurrentmonitor 2, etc.
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
    if re.search(r"dispatch\s+closewindow\s+(\S+)", text):
        m_win = re.search(r"dispatch\s+closewindow\s+(\S+)", text)
        return f'[[BATCH]]/dispatch hl.dsp.window.close("{m_win.group(1)}")\n'.encode("utf-8")

    return data

def main():
    args = sys.argv[1:]
    is_daemon = "--daemon" in args or "-d" in args
    filtered_args = [a for a in args if a not in ("--daemon", "-d")]

    if is_daemon:
        daemonize()

    real_sig, real_sock, real_sock2, proxy_sig, proxy_dir, proxy_sock, proxy_sock2 = get_hypr_paths()

    os.makedirs(proxy_dir, exist_ok=True)

    # Setup .socket2.sock symlink (event listener)
    if os.path.exists(proxy_sock2) or os.path.islink(proxy_sock2):
        try:
            os.remove(proxy_sock2)
        except OSError:
            pass
    if os.path.exists(real_sock2):
        os.symlink(real_sock2, proxy_sock2)

    # Setup .socket.sock listener (command dispatcher)
    if os.path.exists(proxy_sock):
        try:
            os.remove(proxy_sock)
        except OSError:
            pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(proxy_sock)
    server.listen(32)
    server.setblocking(False)

    # Launch waybar subprocess with proxy signature
    env = dict(os.environ)
    env["HYPRLAND_INSTANCE_SIGNATURE"] = proxy_sig

    waybar_proc = subprocess.Popen(["waybar"] + filtered_args, env=env)

    def cleanup(*args):
        if waybar_proc.poll() is None:
            waybar_proc.terminate()
            try:
                waybar_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                waybar_proc.kill()
        try:
            server.close()
        except Exception:
            pass
        shutil.rmtree(proxy_dir, ignore_errors=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    inputs = [server]

    while True:
        # Check if waybar exited
        if waybar_proc.poll() is not None:
            break

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

if __name__ == "__main__":
    main()
