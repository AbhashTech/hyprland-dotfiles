#!/usr/bin/env python3
"""
=============================================================================
Hyprland WiFi Network Manager (iwd / iwctl / nmcli)
=============================================================================
Provides an interactive menu for scanning, selecting, connecting, and 
disconnecting WiFi networks via Fuzzel/Wofi GUI or falling back to interactive
iwctl in Kitty terminal.
"""

import os
import sys
import re
import shutil
import subprocess

def get_wifi_device():
    try:
        res = subprocess.run(["iwctl", "device", "list"], capture_output=True, text=True, check=False)
        for line in res.stdout.splitlines():
            line_clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
            parts = line_clean.strip().split()
            if len(parts) >= 2 and parts[0] not in ["Name", "---", "Param"]:
                return parts[0]
    except Exception:
        pass
    return "wlan0"

def get_current_connection(dev):
    try:
        res = subprocess.run(["iwctl", "station", dev, "show"], capture_output=True, text=True, check=False)
        ssid = ""
        rssi = ""
        state = ""
        for line in res.stdout.splitlines():
            line_clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
            if "Connected network" in line_clean:
                ssid = line_clean.split("Connected network")[-1].strip()
            elif "State" in line_clean:
                state = line_clean.split("State")[-1].strip()
            elif "RSSI" in line_clean and not rssi:
                rssi = line_clean.split("RSSI")[-1].strip()
        if state == "connected" and ssid:
            return ssid, rssi
    except Exception:
        pass
    return None, None

def scan_networks(dev):
    networks = []
    try:
        subprocess.run(["iwctl", "station", dev, "scan"], capture_output=True, check=False)
        res = subprocess.run(["iwctl", "station", dev, "get-networks"], capture_output=True, text=True, check=False)
        for line in res.stdout.splitlines():
            line_clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
            parts = line_clean.strip().split()
            if not parts or parts[0] in ["Network", "name", "---"] or "---" in line_clean:
                continue
            is_connected = ">" in line_clean or line_clean.startswith("*")
            name = line_clean.replace(">", "").replace("*", "").strip()
            match = re.search(r"^\s*([^\s].*?)\s{2,}(psk|open|8021x|wep)?", name, re.IGNORECASE)
            if match:
                ssid = match.group(1).strip()
            else:
                ssid = parts[0]
            if ssid and ssid not in [n["ssid"] for n in networks]:
                networks.append({"ssid": ssid, "connected": is_connected})
    except Exception:
        pass
    return networks

def show_menu():
    dev = get_wifi_device()
    curr_ssid, curr_rssi = get_current_connection(dev)
    networks = scan_networks(dev)

    items = []
    item_map = {}

    if curr_ssid:
        lbl = f"󰤨 Connected: {curr_ssid} ({curr_rssi}) ➜ [Disconnect]"
        items.append(lbl)
        item_map[lbl] = ("disconnect", curr_ssid)

    lbl_rescan = "󰑐 Rescan Networks..."
    items.append(lbl_rescan)
    item_map[lbl_rescan] = ("rescan", None)

    for n in networks:
        if n["ssid"] == curr_ssid:
            continue
        lbl_net = f"󰤢 {n['ssid']}"
        items.append(lbl_net)
        item_map[lbl_net] = ("connect", n["ssid"])

    lbl_term = "󰆍 Open Interactive iwctl Terminal"
    items.append(lbl_term)
    item_map[lbl_term] = ("terminal", None)

    menu_input = "\n".join(items)
    selected = None

    if shutil.which("fuzzel"):
        try:
            res = subprocess.run(
                [
                    "fuzzel",
                    "--dmenu",
                    "-p", " 󰤨 WiFi Networks: ",
                    "-w", "50",
                    "-l", str(min(12, len(items))),
                ],
                input=menu_input,
                capture_output=True,
                text=True,
                check=False
            )
            selected = res.stdout.strip()
        except Exception:
            pass

    if not selected:
        return

    if selected in item_map:
        action, target = item_map[selected]
        if action == "terminal":
            subprocess.Popen(["kitty", "--class", "iwctl-floating", "-T", "WiFi Manager (iwctl)", "iwctl"])
        elif action == "disconnect":
            subprocess.run(["iwctl", "station", dev, "disconnect"], check=False)
            subprocess.run(["notify-send", "-a", "WiFi", "Disconnected", f"Disconnected from {target}"], check=False)
        elif action == "rescan":
            show_menu()
        elif action == "connect":
            passphrase = ""
            if shutil.which("fuzzel"):
                try:
                    p_res = subprocess.run(
                        ["fuzzel", "--dmenu", "--password", "-p", f" Password for {target}: ", "-w", "40", "-l", "0"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    passphrase = p_res.stdout.strip()
                except Exception:
                    pass
            if passphrase:
                cmd = ["iwctl", "--passphrase", passphrase, "station", dev, "connect", target]
            else:
                cmd = ["iwctl", "station", dev, "connect", target]
            
            c_res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if c_res.returncode == 0:
                subprocess.run(["notify-send", "-a", "WiFi", "Connected", f"Successfully connected to {target}"], check=False)
            else:
                subprocess.Popen(["kitty", "--class", "iwctl-floating", "-T", "WiFi Manager (iwctl)", "iwctl"])

def main():
    if "--terminal" in sys.argv:
        subprocess.Popen(["kitty", "--class", "iwctl-floating", "-T", "WiFi Manager (iwctl)", "iwctl"])
        return
    show_menu()

if __name__ == "__main__":
    main()
