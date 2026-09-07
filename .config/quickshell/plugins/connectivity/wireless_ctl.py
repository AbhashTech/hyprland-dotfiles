#!/usr/bin/env python3
"""
Wireless & Bluetooth Backend Controller for Quickshell Connectivity Plugin.
Supports iwctl (iwd) with nmcli fallback, and BlueZ (bluetoothctl).
"""

import sys
import os
import re
import json
import subprocess
import shutil

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)

def run_cmd(cmd: list, timeout: int = 5) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return strip_ansi(res.stdout or "")
    except Exception:
        return ""

def get_wifi_interface() -> str:
    # First check iwctl device list
    out = run_cmd(['iwctl', 'device', 'list'])
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and (parts[0].startswith('wlan') or parts[0].startswith('wlp') or parts[0].startswith('wlo')):
            return parts[0]
    # Fallback to looking in /sys/class/net
    try:
        for iface in os.listdir('/sys/class/net'):
            if iface.startswith(('wl', 'wlan', 'wifi')):
                return iface
    except Exception:
        pass
    return "wlan0"

def get_wifi_status() -> dict:
    iface = get_wifi_interface()
    powered = True
    rf = run_cmd(['rfkill', 'list', 'wifi'])
    if 'Soft blocked: yes' in rf or 'Hard blocked: yes' in rf:
        powered = False

    dev_out = run_cmd(['iwctl', 'device', 'list'])
    for line in dev_out.splitlines():
        if iface in line and 'off' in line:
            powered = False

    result = {
        "iface": iface,
        "powered": powered,
        "connected": False,
        "ssid": "",
        "signal": 0,
        "ip": "",
        "security": "",
        "networks": []
    }

    if not powered:
        return result

    # Check station status
    show_out = run_cmd(['iwctl', 'station', iface, 'show'])
    for l in show_out.splitlines():
        if 'Connected network' in l:
            result['ssid'] = l.split('Connected network')[-1].strip()
            result['connected'] = bool(result['ssid'])
        elif 'IPv4 address' in l:
            result['ip'] = l.split('IPv4 address')[-1].strip()
        elif 'Security' in l and ('WPA' in l or 'Open' in l or 'WEP' in l):
            result['security'] = l.split('Security')[-1].strip()
        elif 'RSSI' in l and not result['signal']:
            try:
                rssi_val = int(l.split('RSSI')[-1].strip().split()[0])
                result['signal'] = max(0, min(100, int(2 * (rssi_val + 100))))
            except Exception:
                result['signal'] = 75

    # Known / Saved networks
    known_set = set()
    known_out = run_cmd(['iwctl', 'known-networks', 'list'])
    for l in known_out.splitlines():
        parts = re.split(r'\s{2,}', l.strip())
        if parts and parts[0] not in ('Name', 'Known Networks', '---') and not parts[0].startswith('-'):
            known_set.add(parts[0])

    # Available networks
    net_out = run_cmd(['iwctl', 'station', iface, 'get-networks'])
    seen_ssids = set()
    for l in net_out.splitlines():
        if not l.strip() or 'Available networks' in l or 'Network name' in l or '---' in l:
            continue
        is_conn = '>' in l[:6]
        content = l[6:] if len(l) > 6 else l
        parts = re.split(r'\s{2,}', content.strip())
        if parts and len(parts) >= 1:
            name = parts[0].strip()
            if not name or name in seen_ssids:
                continue
            seen_ssids.add(name)
            sec = parts[1].strip() if len(parts) > 1 else 'open'
            sig_str = parts[2].strip() if len(parts) > 2 else '****'
            sig_val = sig_str.count('*') * 25 if '*' in sig_str else 60
            result['networks'].append({
                'ssid': name,
                'security': sec,
                'signal': sig_val,
                'connected': is_conn or (name == result['ssid'] and result['connected']),
                'known': name in known_set
            })

    # If current connected network not in list, prepend it
    if result['connected'] and result['ssid'] and not any(n['ssid'] == result['ssid'] for n in result['networks']):
        result['networks'].insert(0, {
            'ssid': result['ssid'],
            'security': result['security'] or 'psk',
            'signal': result['signal'] or 85,
            'connected': True,
            'known': True
        })

    # Sort networks: connected first, then known, then by signal strength
    result['networks'].sort(key=lambda n: (n['connected'], n['known'], n['signal']), reverse=True)
    return result

def wifi_connect(ssid: str, password: str = None) -> bool:
    iface = get_wifi_interface()
    if password:
        cmd = ['iwctl', '--passphrase', password, 'station', iface, 'connect', ssid]
    else:
        cmd = ['iwctl', 'station', iface, 'connect', ssid]
    try:
        subprocess.run(cmd, timeout=10, check=True)
        return True
    except Exception:
        return False

def wifi_disconnect() -> bool:
    iface = get_wifi_interface()
    try:
        subprocess.run(['iwctl', 'station', iface, 'disconnect'], timeout=5, check=True)
        return True
    except Exception:
        return False

def wifi_forget(ssid: str) -> bool:
    try:
        subprocess.run(['iwctl', 'known-networks', ssid, 'forget'], timeout=5, check=True)
        return True
    except Exception:
        return False

def wifi_toggle() -> bool:
    try:
        rf = run_cmd(['rfkill', 'list', 'wifi'])
        if 'Soft blocked: yes' in rf or 'Hard blocked: yes' in rf:
            subprocess.run(['rfkill', 'unblock', 'wifi'], timeout=3)
            iface = get_wifi_interface()
            subprocess.run(['iwctl', 'device', iface, 'set-property', 'Powered', 'on'], timeout=3)
        else:
            iface = get_wifi_interface()
            subprocess.run(['iwctl', 'device', iface, 'set-property', 'Powered', 'off'], timeout=3)
        return True
    except Exception:
        return False

def wifi_scan() -> bool:
    iface = get_wifi_interface()
    try:
        subprocess.run(['iwctl', 'station', iface, 'scan'], timeout=5)
        return True
    except Exception:
        return False

def get_bt_icon(device_class: str, icon_str: str) -> str:
    i = icon_str.lower()
    c = device_class.lower()
    if 'headset' in i or 'headphone' in i or 'audio' in i or 'headset' in c:
        return 'audio-headset'
    if 'mouse' in i or 'mouse' in c:
        return 'input-mouse'
    if 'keyboard' in i or 'keyboard' in c:
        return 'input-keyboard'
    if 'phone' in i or 'phone' in c:
        return 'phone'
    return 'bluetooth'

def get_bt_status() -> dict:
    show_out = run_cmd(['bluetoothctl', 'show'])
    powered = 'Powered: yes' in show_out
    discovering = 'Discovering: yes' in show_out

    result = {
        "powered": powered,
        "discovering": discovering,
        "connected_count": 0,
        "devices": [],
        "discovered": []
    }

    # Fetch paired devices
    paired_out = run_cmd(['bluetoothctl', 'devices', 'Paired'])
    if not paired_out:
        paired_out = run_cmd(['bluetoothctl', 'devices'])

    conn_out = run_cmd(['bluetoothctl', 'devices', 'Connected'])
    conn_macs = set()
    for l in conn_out.splitlines():
        p = l.split()
        if len(p) >= 2 and p[0] == 'Device':
            conn_macs.add(p[1])

    paired_macs = set()
    for l in paired_out.splitlines():
        p = l.split()
        if len(p) >= 3 and p[0] == 'Device':
            mac = p[1]
            name = ' '.join(p[2:])
            paired_macs.add(mac)
            is_conn = mac in conn_macs

            # Get detail info
            d_info = run_cmd(['bluetoothctl', 'info', mac])
            icon_type = 'bluetooth'
            battery = -1
            for dl in d_info.splitlines():
                if 'Icon:' in dl:
                    icon_type = get_bt_icon('', dl.split('Icon:')[-1].strip())
                elif 'Connected: yes' in dl:
                    is_conn = True
                elif 'Battery Percentage:' in dl:
                    try:
                        m = re.search(r'\((\d+)\)', dl)
                        if m:
                            battery = int(m.group(1))
                    except Exception:
                        pass

            if is_conn:
                result['connected_count'] += 1

            result['devices'].append({
                'mac': mac,
                'name': name,
                'icon': icon_type,
                'connected': is_conn,
                'paired': True,
                'battery': battery
            })

    # Sort devices: connected first, then alphabetical
    result['devices'].sort(key=lambda d: (d['connected'], d['name'].lower()), reverse=True)

    # If discovering, look for unpaired devices
    if discovering:
        all_devs = run_cmd(['bluetoothctl', 'devices'])
        for l in all_devs.splitlines():
            p = l.split()
            if len(p) >= 3 and p[0] == 'Device':
                mac = p[1]
                name = ' '.join(p[2:])
                if mac not in paired_macs and not name.replace('-', ':').replace('_', ':') == mac:
                    result['discovered'].append({
                        'mac': mac,
                        'name': name,
                        'icon': 'bluetooth'
                    })

    return result

def bt_toggle() -> bool:
    show_out = run_cmd(['bluetoothctl', 'show'])
    powered = 'Powered: yes' in show_out
    if powered:
        run_cmd(['bluetoothctl', 'power', 'off'])
    else:
        run_cmd(['rfkill', 'unblock', 'bluetooth'])
        run_cmd(['bluetoothctl', 'power', 'on'])
    return True

def bt_scan_toggle() -> bool:
    show_out = run_cmd(['bluetoothctl', 'show'])
    discovering = 'Discovering: yes' in show_out
    if discovering:
        run_cmd(['bluetoothctl', 'scan', 'off'])
    else:
        run_cmd(['bluetoothctl', 'scan', 'on'])
    return True

def bt_connect(mac: str) -> bool:
    out = run_cmd(['bluetoothctl', 'connect', mac], timeout=8)
    return "Connection successful" in out or "already connected" in out

def bt_disconnect(mac: str) -> bool:
    out = run_cmd(['bluetoothctl', 'disconnect', mac], timeout=5)
    return "Successful disconnected" in out

def bt_pair(mac: str) -> bool:
    run_cmd(['bluetoothctl', 'pair', mac], timeout=10)
    run_cmd(['bluetoothctl', 'trust', mac], timeout=5)
    run_cmd(['bluetoothctl', 'connect', mac], timeout=8)
    return True

def bt_remove(mac: str) -> bool:
    out = run_cmd(['bluetoothctl', 'remove', mac], timeout=5)
    return "Device has been removed" in out

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No action specified"}))
        sys.exit(1)

    action = sys.argv[1]

    if action == 'status-wifi':
        print(json.dumps(get_wifi_status()))
    elif action == 'wifi-scan':
        wifi_scan()
        print(json.dumps(get_wifi_status()))
    elif action == 'wifi-connect':
        ssid = sys.argv[2] if len(sys.argv) > 2 else ""
        password = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "NONE" else None
        ok = wifi_connect(ssid, password)
        print(json.dumps({"success": ok}))
    elif action == 'wifi-disconnect':
        ok = wifi_disconnect()
        print(json.dumps({"success": ok}))
    elif action == 'wifi-forget':
        ssid = sys.argv[2] if len(sys.argv) > 2 else ""
        ok = wifi_forget(ssid)
        print(json.dumps({"success": ok}))
    elif action == 'wifi-toggle':
        ok = wifi_toggle()
        print(json.dumps({"success": ok}))

    elif action == 'status-bt':
        print(json.dumps(get_bt_status()))
    elif action == 'bt-toggle':
        ok = bt_toggle()
        print(json.dumps({"success": ok}))
    elif action == 'bt-scan-toggle':
        ok = bt_scan_toggle()
        print(json.dumps({"success": ok}))
    elif action == 'bt-connect':
        mac = sys.argv[2] if len(sys.argv) > 2 else ""
        ok = bt_connect(mac)
        print(json.dumps({"success": ok}))
    elif action == 'bt-disconnect':
        mac = sys.argv[2] if len(sys.argv) > 2 else ""
        ok = bt_disconnect(mac)
        print(json.dumps({"success": ok}))
    elif action == 'bt-pair':
        mac = sys.argv[2] if len(sys.argv) > 2 else ""
        ok = bt_pair(mac)
        print(json.dumps({"success": ok}))
    elif action == 'bt-remove':
        mac = sys.argv[2] if len(sys.argv) > 2 else ""
        ok = bt_remove(mac)
        print(json.dumps({"success": ok}))
    else:
        print(json.dumps({"error": f"Unknown action {action}"}))
        sys.exit(1)

if __name__ == '__main__':
    main()
