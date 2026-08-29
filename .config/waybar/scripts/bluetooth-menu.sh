#!/usr/bin/env python3
"""
=============================================================================
 Fast Bluetooth Menu for Waybar using DBus & Wofi
 Instant (<20ms) response time without slow bluetoothctl subprocess loops
=============================================================================
"""

import os
import re
import subprocess
import sys


def get_dbus_state():
    try:
        import dbus
        bus = dbus.SystemBus()
        bluez = bus.get_object('org.bluez', '/')
        manager = dbus.Interface(bluez, 'org.freedesktop.DBus.ObjectManager')
        objects = manager.GetManagedObjects()
        
        adapter_path = None
        powered = False
        devices = []

        for path, ifaces in objects.items():
            if 'org.bluez.Adapter1' in ifaces:
                adapter_path = path
                powered = bool(ifaces['org.bluez.Adapter1'].get('Powered', False))
            if 'org.bluez.Device1' in ifaces:
                d = ifaces['org.bluez.Device1']
                if d.get('Paired'):
                    devices.append({
                        'name': str(d.get('Name', d.get('Alias', 'Unknown Device'))),
                        'mac': str(d.get('Address', '')),
                        'connected': bool(d.get('Connected', False))
                    })
        
        devices.sort(key=lambda d: (not d['connected'], d['name'].lower()))
        return True, powered, adapter_path, devices
    except Exception:
        # Fallback to rfkill if dbus is unavailable
        try:
            res = subprocess.run(['rfkill', 'list', 'bluetooth'], capture_output=True, text=True, timeout=1)
            powered = "Soft blocked: yes" not in res.stdout and "Hard blocked: yes" not in res.stdout
            return False, powered, None, []
        except Exception:
            return False, False, None, []


def toggle_power(current_state: bool, adapter_path: str = None):
    try:
        if adapter_path:
            import dbus
            bus = dbus.SystemBus()
            adapter = bus.get_object('org.bluez', adapter_path)
            props = dbus.Interface(adapter, 'org.freedesktop.DBus.Properties')
            props.Set('org.bluez.Adapter1', 'Powered', not current_state)
            return
    except Exception:
        pass
    
    # Fallback to rfkill
    try:
        subprocess.run(['rfkill', 'toggle', 'bluetooth'], timeout=1)
    except Exception:
        pass


def main():
    service_ok, powered, adapter_path, devices = get_dbus_state()

    options = []
    if powered:
        options.append("󰂲  Turn Bluetooth OFF")
        options.append("󰤨  Open NETCTL TUI (Wi-Fi & Bluetooth)")
        if devices:
            options.append("--- Paired Devices ---")
            for dev in devices:
                status = "Connected" if dev['connected'] else "Disconnected"
                icon = "󰂱" if dev['connected'] else "󰂯"
                options.append(f"{icon}  {dev['name']} [{status}] ({dev['mac']})")
        options.append("󰑐  Scan for Devices")
        options.append("󰞷  Open Bluetooth Terminal")
    else:
        options.append("󰂯  Turn Bluetooth ON")
        options.append("󰤨  Open NETCTL TUI (Wi-Fi & Bluetooth)")
        if not service_ok:
            options.append("󰚥  Service Inactive (sudo systemctl start bluetooth)")

    menu_input = "\n".join(options)

    # Open dmenu with fuzzel
    import shutil
    if shutil.which("fuzzel"):
        dmenu_cmd = ["fuzzel", "--dmenu", "--prompt", " 󰂯 Bluetooth: ", "--width", "36", "--lines", str(min(max(len(options), 4), 10))]
    else:
        dmenu_cmd = [
            "wofi", "--dmenu",
            "--prompt", "Bluetooth",
            "--width", "420",
            "--height", "320",
            "--cache-file", "/dev/null",
            "--hide-scroll",
            "--allow-markup",
            "--insensitive"
        ]

    try:
        proc = subprocess.run(dmenu_cmd, input=menu_input, text=True, capture_output=True)
        chosen = proc.stdout.strip()
    except Exception:
        return

    if not chosen:
        return

    if "Turn Bluetooth ON" in chosen or "Turn Bluetooth OFF" in chosen:
        toggle_power(powered, adapter_path)
    elif "Open NETCTL TUI" in chosen or "Scan for Devices" in chosen:
        subprocess.Popen(["kitty", "--class=netctl-floating", "-e", "/home/kunal/.config/waybar/scripts/netctl-tui.py", "bt"])
    elif "Open Bluetooth Terminal" in chosen:
        subprocess.Popen(["kitty", "--class=bt-floating", "-e", "bluetoothctl"])
    elif "[Connected]" in chosen:
        match = re.search(r'([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})', chosen)
        if match:
            mac = match.group(1)
            subprocess.Popen(["bluetoothctl", "--timeout", "3", "disconnect", mac])
    elif "[Disconnected]" in chosen:
        match = re.search(r'([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})', chosen)
        if match:
            mac = match.group(1)
            # Trust and connect
            subprocess.run(["bluetoothctl", "--timeout", "2", "trust", mac], capture_output=True)
            subprocess.Popen(["bluetoothctl", "--timeout", "6", "connect", mac])


if __name__ == '__main__':
    main()
