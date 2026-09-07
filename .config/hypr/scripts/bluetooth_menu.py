#!/usr/bin/env python3
"""
=============================================================================
Hyprland Bluetooth Device Manager (bluetoothctl)
=============================================================================
Provides an interactive menu for toggling bluetooth, scanning, connecting,
and disconnecting paired/available devices via Fuzzel/Wofi or interactive
bluetoothctl terminal.
"""

import os
import sys
import re
import shutil
import subprocess

def get_bt_status():
    try:
        res = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, check=False)
        powered = "Powered: yes" in res.stdout
        return powered
    except Exception:
        return False

def get_devices():
    paired_devices = []
    try:
        res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, check=False)
        for line in res.stdout.splitlines():
            parts = line.strip().split(maxsplit=2)
            if len(parts) >= 3 and parts[0] == "Device":
                mac = parts[1]
                name = parts[2]
                paired_devices.append({"mac": mac, "name": name})
    except Exception:
        pass
    return paired_devices

def get_connected_macs():
    connected = set()
    try:
        res = subprocess.run(["bluetoothctl", "devices", "Connected"], capture_output=True, text=True, check=False)
        for line in res.stdout.splitlines():
            parts = line.strip().split(maxsplit=2)
            if len(parts) >= 2 and parts[0] == "Device":
                connected.add(parts[1])
    except Exception:
        pass
    return connected

def show_menu():
    powered = get_bt_status()
    devices = get_devices()
    connected_macs = get_connected_macs()

    items = []
    item_map = {}

    # Power toggle option
    p_status = "Enabled (ON)" if powered else "Disabled (OFF)"
    lbl_power = f"󰂯 Bluetooth: {p_status} ➜ [Toggle Power]"
    items.append(lbl_power)
    item_map[lbl_power] = ("toggle_power", None)

    if powered:
        for dev in devices:
            is_conn = dev["mac"] in connected_macs
            if is_conn:
                lbl = f"󰂱 Connected: {dev['name']} ({dev['mac']}) ➜ [Disconnect]"
                items.append(lbl)
                item_map[lbl] = ("disconnect", dev["mac"])
            else:
                lbl = f"󰂯 Paired: {dev['name']} ({dev['mac']}) ➜ [Connect]"
                items.append(lbl)
                item_map[lbl] = ("connect", dev["mac"])

    lbl_term = "󰆍 Open Interactive bluetoothctl Terminal"
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
                    "-p", " 󰂯 Bluetooth Devices: ",
                    "-w", "52",
                    "-l", str(min(10, len(items))),
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
            subprocess.Popen(["kitty", "--class", "bt-floating", "-T", "Bluetooth Control (bluetoothctl)", "bluetoothctl"])
        elif action == "toggle_power":
            new_state = "off" if powered else "on"
            subprocess.run(["bluetoothctl", "power", new_state], check=False)
            msg = "Powered Off" if powered else "Powered On"
            subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth Power", f"Bluetooth is now {msg}"], check=False)
        elif action == "disconnect":
            subprocess.run(["bluetoothctl", "disconnect", target], check=False)
            subprocess.run(["notify-send", "-a", "Bluetooth", "Disconnected", f"Disconnected from {target}"], check=False)
        elif action == "connect":
            subprocess.run(["bluetoothctl", "connect", target], check=False)
            subprocess.run(["notify-send", "-a", "Bluetooth", "Connected", f"Connecting to {target}..."], check=False)

def main():
    if "--terminal" in sys.argv:
        subprocess.Popen(["kitty", "--class", "bt-floating", "-T", "Bluetooth Control (bluetoothctl)", "bluetoothctl"])
        return
    show_menu()

if __name__ == "__main__":
    main()
