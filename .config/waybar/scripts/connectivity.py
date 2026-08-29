#!/usr/bin/env python3
"""
=============================================================================
 Combined Network & Bluetooth Status for Waybar
 Merges Wi-Fi / Ethernet and Bluetooth into a single unified Waybar module
=============================================================================
"""

import json
import os
import re
import subprocess
import sys


def get_network_info():
    """Get active network status, SSID, signal, and IP."""
    net_icon = "󰤭"
    net_text = "Disconnected"
    net_ip = ""
    net_ssid = ""
    signal_pct = None

    try:
        # Check default route
        route_out = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=1).stdout
        match = re.search(r'dev\s+(\S+)', route_out)
        if match:
            iface = match.group(1)
            
            # Get IP
            ip_out = subprocess.run(["ip", "-4", "addr", "show", iface], capture_output=True, text=True, timeout=1).stdout
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_out)
            if ip_match:
                net_ip = ip_match.group(1)

            if iface.startswith("wl") or iface.startswith("wlan"):
                # Wireless interface
                # Check iwgetid or iw
                try:
                    ssid_proc = subprocess.run(["iwgetid", "-r", iface], capture_output=True, text=True, timeout=1)
                    if ssid_proc.stdout.strip():
                        net_ssid = ssid_proc.stdout.strip()
                except Exception:
                    pass

                # Check signal from /proc/net/wireless
                if os.path.exists("/proc/net/wireless"):
                    try:
                        with open("/proc/net/wireless", "r") as f:
                            for line in f:
                                if iface in line:
                                    parts = line.split()
                                    if len(parts) >= 3:
                                        qual = float(parts[2].replace(".", ""))
                                        # Usually out of 70
                                        signal_pct = min(100, int((qual / 70.0) * 100))
                                    break
                    except Exception:
                        pass

                # Fallback to nmcli if ssid or signal not found
                if not net_ssid or signal_pct is None:
                    try:
                        nm_out = subprocess.run(
                            ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"],
                            capture_output=True, text=True, timeout=1
                        ).stdout
                        for line in nm_out.splitlines():
                            if line.startswith("yes:"):
                                parts = line.split(":")
                                if len(parts) >= 3:
                                    net_ssid = parts[1]
                                    signal_pct = int(parts[2])
                                break
                    except Exception:
                        pass

                if signal_pct is not None:
                    if signal_pct >= 80:
                        net_icon = "󰤨"
                    elif signal_pct >= 60:
                        net_icon = "󰤥"
                    elif signal_pct >= 40:
                        net_icon = "󰤢"
                    elif signal_pct >= 20:
                        net_icon = "󰤟"
                    else:
                        net_icon = "󰤯"
                    net_text = f"{net_ssid} ({signal_pct}%)" if net_ssid else f"{signal_pct}%"
                else:
                    net_icon = "󰤨"
                    net_text = net_ssid if net_ssid else "Connected"
            else:
                # Ethernet / other
                net_icon = "󰈀"
                net_text = f"Ethernet ({iface})"
    except Exception:
        pass

    return {
        "icon": net_icon,
        "text": net_text,
        "ip": net_ip,
        "ssid": net_ssid,
        "signal": signal_pct,
        "connected": net_icon != "󰤭"
    }


def get_bluetooth_info():
    """Get bluetooth power status and connected devices."""
    bt_icon = "󰂲"
    bt_state = "Off"
    connected_devices = []

    try:
        import dbus
        bus = dbus.SystemBus()
        bluez = bus.get_object('org.bluez', '/')
        manager = dbus.Interface(bluez, 'org.freedesktop.DBus.ObjectManager')
        objects = manager.GetManagedObjects()

        powered = False
        for path, ifaces in objects.items():
            if 'org.bluez.Adapter1' in ifaces:
                powered = bool(ifaces['org.bluez.Adapter1'].get('Powered', False))
            if 'org.bluez.Device1' in ifaces:
                d = ifaces['org.bluez.Device1']
                if d.get('Connected'):
                    name = str(d.get('Name', d.get('Alias', 'Device')))
                    bat = d.get('BatteryPercentage')
                    connected_devices.append({
                        'name': name,
                        'battery': int(bat) if bat is not None else None
                    })

        if powered:
            if connected_devices:
                bt_icon = "󰂱"
                bt_state = f"{len(connected_devices)} connected"
            else:
                bt_icon = "󰂯"
                bt_state = "On"
        else:
            bt_icon = "󰂲"
            bt_state = "Off"
    except Exception:
        # Fallback to rfkill
        try:
            res = subprocess.run(['rfkill', 'list', 'bluetooth'], capture_output=True, text=True, timeout=1)
            if "Soft blocked: yes" not in res.stdout and "Hard blocked: yes" not in res.stdout:
                bt_icon = "󰂯"
                bt_state = "On"
        except Exception:
            pass

    return {
        "icon": bt_icon,
        "state": bt_state,
        "devices": connected_devices
    }


def main():
    net = get_network_info()
    bt = get_bluetooth_info()

    # Formatted combined text
    combined_text = f"{net['icon']}  {bt['icon']}"

    # Build rich tooltip
    tooltip_lines = [
        "<b>󰤨 Network</b>",
        f"• Status: {net['text']}"
    ]
    if net['ip']:
        tooltip_lines.append(f"• IP Address: {net['ip']}")
    
    tooltip_lines.append("")
    tooltip_lines.append("<b>󰂯 Bluetooth</b>")
    tooltip_lines.append(f"• Status: {bt['state']}")
    if bt['devices']:
        for dev in bt['devices']:
            bat_str = f" ({dev['battery']}%)" if dev['battery'] is not None else ""
            tooltip_lines.append(f"• {dev['name']}{bat_str}")

    tooltip_lines.append("")
    tooltip_lines.append("<b>Actions:</b>")
    tooltip_lines.append("• Left Click: Wi-Fi Menu")
    tooltip_lines.append("• Right Click: Bluetooth Menu")
    tooltip_lines.append("• Middle Click: Netctl TUI Manager")

    classes = ["connectivity"]
    if net['connected']:
        classes.append("net-connected")
    if bt['devices']:
        classes.append("bt-connected")
    elif bt['state'] == "Off":
        classes.append("bt-off")

    output = {
        "text": combined_text,
        "tooltip": "\n".join(tooltip_lines),
        "class": " ".join(classes)
    }

    print(json.dumps(output))


if __name__ == '__main__':
    main()
