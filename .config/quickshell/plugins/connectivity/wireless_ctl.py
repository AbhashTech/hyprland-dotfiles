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
import time
import signal

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

def get_wifi_devices() -> list:
    devs = []
    out = run_cmd(['iwctl', 'device', 'list'])
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and (parts[0].startswith('wlan') or parts[0].startswith('wlp') or parts[0].startswith('wlo')):
            devs.append(parts[0])
    if not devs:
        try:
            for iface in os.listdir('/sys/class/net'):
                if iface.startswith(('wl', 'wlan', 'wifi')):
                    devs.append(iface)
        except Exception:
            pass
    if not devs:
        devs = ["wlan0"]
    return list(dict.fromkeys(devs))

def is_wifi_powered(iface: str = None) -> bool:
    if not iface:
        iface = get_wifi_interface()
    rf = run_cmd(['rfkill', 'list', 'wifi'])
    if 'Soft blocked: yes' in rf or 'Hard blocked: yes' in rf:
        return False

    dev_out = run_cmd(['iwctl', 'device', 'list'])
    for line in dev_out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == iface:
            return parts[2].lower() == 'on'
        if iface in line and 'off' in line:
            return False

    if shutil.which('nmcli'):
        nm = run_cmd(['nmcli', 'radio', 'wifi'])
        if 'disabled' in nm.lower():
            return False

    try:
        if os.path.exists(f"/sys/class/net/{iface}/flags"):
            flags = int(open(f"/sys/class/net/{iface}/flags").read().strip(), 16)
            if not (flags & 1):
                return False
    except Exception:
        pass

    return True

def get_wifi_status() -> dict:
    iface = get_wifi_interface()
    powered = is_wifi_powered(iface)

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
        if parts and parts[0] and parts[0] not in ('Name', 'Known Networks', '---') and not parts[0].startswith('-'):
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
                'known': name in known_set,
                'in_range': True
            })

    # If current connected network not in list, prepend it
    if result['connected'] and result['ssid'] and not any(n['ssid'] == result['ssid'] for n in result['networks']):
        result['networks'].insert(0, {
            'ssid': result['ssid'],
            'security': result['security'] or 'psk',
            'signal': result['signal'] or 85,
            'connected': True,
            'known': True,
            'in_range': True
        })
        seen_ssids.add(result['ssid'])

    # Add known networks that are currently out of range so the user can manage/forget them
    for kname in sorted(known_set):
        if kname and kname not in seen_ssids:
            result['networks'].append({
                'ssid': kname,
                'security': 'psk',
                'signal': 0,
                'connected': False,
                'known': True,
                'in_range': False
            })

    # Sort networks: connected first, then in-range by signal, then out-of-range
    result['networks'].sort(key=lambda n: (
        1 if n['connected'] else 0,
        1 if n.get('in_range', True) else 0,
        n['signal']
    ), reverse=True)
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
    if not ssid:
        return False
    ok = False
    try:
        res = subprocess.run(['iwctl', 'known-networks', ssid, 'forget'], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            ok = True
    except Exception:
        pass

    if not ok and shutil.which('nmcli'):
        try:
            res = subprocess.run(['nmcli', 'con', 'delete', ssid], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                ok = True
        except Exception:
            pass
    return ok

def wifi_toggle() -> bool:
    try:
        iface = get_wifi_interface()
        devices = get_wifi_devices()
        currently_powered = is_wifi_powered(iface)

        if currently_powered:
            for dev in devices:
                subprocess.run(['iwctl', 'device', dev, 'set-property', 'Powered', 'off'], timeout=3)
            if shutil.which('nmcli'):
                subprocess.run(['nmcli', 'radio', 'wifi', 'off'], timeout=3)
        else:
            subprocess.run(['rfkill', 'unblock', 'wifi'], timeout=3)
            for dev in devices:
                subprocess.run(['iwctl', 'device', dev, 'set-property', 'Powered', 'on'], timeout=3)
            if shutil.which('nmcli'):
                subprocess.run(['nmcli', 'radio', 'wifi', 'on'], timeout=3)
            try:
                subprocess.run(['iwctl', 'station', iface, 'scan'], timeout=2)
            except Exception:
                pass
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

BT_SCAN_PID_FILE = "/tmp/quickshell_bt_scan.pid"
BT_CACHE_FILE = "/tmp/quickshell_bt_discovered.json"

def get_dbus_adapter():
    try:
        import dbus
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
        objects = manager.GetManagedObjects()
        for path, ifaces in objects.items():
            if 'org.bluez.Adapter1' in ifaces:
                return bus, path, ifaces['org.bluez.Adapter1'], objects
        return bus, None, None, objects
    except Exception:
        return None, None, None, {}

def get_bt_icon(device_class: str, icon_str: str) -> str:
    i = icon_str.lower()
    c = str(device_class).lower()
    if any(k in i or k in c for k in ['headset', 'headphone', 'audio', 'earbud']):
        return 'audio-headset'
    if 'mouse' in i or 'mouse' in c:
        return 'input-mouse'
    if 'keyboard' in i or 'keyboard' in c:
        return 'input-keyboard'
    if 'phone' in i or 'phone' in c:
        return 'phone'
    if 'computer' in i or 'laptop' in i or 'desktop' in c:
        return 'computer'
    return 'bluetooth'

def get_bt_status() -> dict:
    bus, adapter_path, adapter, objects = get_dbus_adapter()
    if not bus or not adapter_path:
        # Fallback if DBus query fails
        show_out = run_cmd(['bluetoothctl', 'show'])
        powered = 'Powered: yes' in show_out
        discovering = 'Discovering: yes' in show_out
        discoverable = 'Discoverable: yes' in show_out
        return {
            "powered": powered,
            "discovering": discovering,
            "discoverable": discoverable,
            "pairable": True,
            "adapter_name": "abhashtech",
            "adapter_mac": "",
            "connected_count": 0,
            "devices": [],
            "discovered": []
        }

    powered = bool(adapter.get('Powered', False))
    discovering = bool(adapter.get('Discovering', False))
    discoverable = bool(adapter.get('Discoverable', False))
    pairable = bool(adapter.get('Pairable', False))
    adapter_name = str(adapter.get('Alias', adapter.get('Name', 'abhashtech')))
    adapter_mac = str(adapter.get('Address', ''))

    if powered and not pairable:
        try:
            import dbus
            props = dbus.Interface(bus.get_object('org.bluez', adapter_path), 'org.freedesktop.DBus.Properties')
            props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(True))
            pairable = True
        except Exception:
            pass

    # Check if detached scan daemon is running to verify discovering flag
    if not discovering and os.path.exists(BT_SCAN_PID_FILE):
        try:
            with open(BT_SCAN_PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            discovering = True
        except Exception:
            if os.path.exists(BT_SCAN_PID_FILE):
                try:
                    os.remove(BT_SCAN_PID_FILE)
                except Exception:
                    pass

    paired_devices = []
    discovered_devices = []
    connected_count = 0

    for path, ifaces in objects.items():
        if 'org.bluez.Device1' in ifaces:
            d = ifaces['org.bluez.Device1']
            mac = str(d.get('Address', ''))
            name = str(d.get('Name', ''))
            alias = str(d.get('Alias', ''))
            display_name = name or alias
            if not display_name or display_name.replace('-', ':').replace('_', ':').upper() == mac.upper():
                display_name = f"Device ({mac[-8:]})"

            is_paired = bool(d.get('Paired', False))
            is_conn = bool(d.get('Connected', False))
            rssi = int(d.get('RSSI', 0))
            icon_raw = str(d.get('Icon', ''))
            class_num = str(d.get('Class', ''))
            icon_type = get_bt_icon(class_num, icon_raw)

            battery = -1
            if 'org.bluez.Battery1' in ifaces:
                try:
                    battery = int(ifaces['org.bluez.Battery1'].get('Percentage', -1))
                except Exception:
                    pass

            dev_info = {
                'mac': mac,
                'name': display_name,
                'icon': icon_type,
                'connected': is_conn,
                'paired': is_paired,
                'battery': battery,
                'rssi': rssi
            }

            if is_paired:
                if is_conn:
                    connected_count += 1
                paired_devices.append(dev_info)
            else:
                discovered_devices.append(dev_info)

    paired_devices.sort(key=lambda d: (d['connected'], d['name'].lower()), reverse=True)
    discovered_devices.sort(key=lambda d: (d.get('rssi', -999) if d.get('rssi', 0) != 0 else -100), reverse=True)

    # Persist or read cache for discovered devices so list doesn't immediately clear when scan stops
    if discovered_devices:
        try:
            with open(BT_CACHE_FILE, 'w') as f:
                json.dump({'timestamp': time.time(), 'devices': discovered_devices}, f)
        except Exception:
            pass
    elif not discovering and os.path.exists(BT_CACHE_FILE):
        try:
            with open(BT_CACHE_FILE) as f:
                cached = json.load(f)
                if time.time() - cached.get('timestamp', 0) < 300:
                    discovered_devices = cached.get('devices', [])
        except Exception:
            pass

    return {
        "powered": powered,
        "discovering": discovering,
        "discoverable": discoverable,
        "pairable": pairable,
        "adapter_name": adapter_name,
        "adapter_mac": adapter_mac,
        "connected_count": connected_count,
        "devices": paired_devices,
        "discovered": discovered_devices
    }

def bt_toggle() -> bool:
    bus, adapter_path, adapter, _ = get_dbus_adapter()
    if bus and adapter_path:
        try:
            import dbus
            props = dbus.Interface(bus.get_object('org.bluez', adapter_path), 'org.freedesktop.DBus.Properties')
            cur = bool(adapter.get('Powered', False))
            if not cur:
                run_cmd(['rfkill', 'unblock', 'bluetooth'])
            props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(not cur))
            return True
        except Exception:
            pass

    # Subprocess fallback
    show_out = run_cmd(['bluetoothctl', 'show'])
    powered = 'Powered: yes' in show_out
    if powered:
        run_cmd(['bluetoothctl', 'power', 'off'])
    else:
        run_cmd(['rfkill', 'unblock', 'bluetooth'])
        run_cmd(['bluetoothctl', 'power', 'on'])
    return True

def bt_scan_daemon(duration: int = 30):
    """Background daemon that holds BlueZ discovery active for `duration` seconds."""
    try:
        import dbus
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
        objects = manager.GetManagedObjects()
        adapter_path = None
        for path, ifaces in objects.items():
            if 'org.bluez.Adapter1' in ifaces:
                adapter_path = path
                break
        if not adapter_path:
            sys.exit(1)

        adapter = dbus.Interface(bus.get_object('org.bluez', adapter_path), 'org.bluez.Adapter1')

        def cleanup(signum, frame):
            try:
                adapter.StopDiscovery()
            except Exception:
                pass
            if os.path.exists(BT_SCAN_PID_FILE):
                try:
                    os.remove(BT_SCAN_PID_FILE)
                except Exception:
                    pass
            sys.exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)

        with open(BT_SCAN_PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        try:
            adapter.StartDiscovery()
        except Exception as e:
            if 'Already' not in str(e):
                if os.path.exists(BT_SCAN_PID_FILE):
                    try:
                        os.remove(BT_SCAN_PID_FILE)
                    except Exception:
                        pass
                sys.exit(1)

        for _ in range(duration * 10):
            time.sleep(0.1)

        try:
            adapter.StopDiscovery()
        except Exception:
            pass
        if os.path.exists(BT_SCAN_PID_FILE):
            try:
                os.remove(BT_SCAN_PID_FILE)
            except Exception:
                pass
    except Exception:
        if os.path.exists(BT_SCAN_PID_FILE):
            try:
                os.remove(BT_SCAN_PID_FILE)
            except Exception:
                pass
        sys.exit(1)

def bt_scan_start(duration: int = 30) -> bool:
    bt_scan_stop()
    if os.path.exists(BT_CACHE_FILE):
        try:
            os.remove(BT_CACHE_FILE)
        except Exception:
            pass

    script_path = os.path.abspath(__file__)
    subprocess.Popen(
        [sys.executable, script_path, 'bt-scan-daemon', str(duration)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True
    )
    time.sleep(0.2)
    return True

def bt_scan_stop() -> bool:
    if os.path.exists(BT_SCAN_PID_FILE):
        try:
            with open(BT_SCAN_PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
        except Exception:
            pass
        try:
            os.remove(BT_SCAN_PID_FILE)
        except Exception:
            pass

    try:
        import dbus
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
        for path, ifaces in manager.GetManagedObjects().items():
            if 'org.bluez.Adapter1' in ifaces:
                adapter = dbus.Interface(bus.get_object('org.bluez', path), 'org.bluez.Adapter1')
                adapter.StopDiscovery()
                break
    except Exception:
        pass
    return True

def bt_scan_toggle() -> bool:
    is_scanning = False
    if os.path.exists(BT_SCAN_PID_FILE):
        try:
            with open(BT_SCAN_PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            is_scanning = True
        except Exception:
            if os.path.exists(BT_SCAN_PID_FILE):
                try:
                    os.remove(BT_SCAN_PID_FILE)
                except Exception:
                    pass

    if not is_scanning:
        try:
            import dbus
            bus = dbus.SystemBus()
            manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
            for path, ifaces in manager.GetManagedObjects().items():
                if 'org.bluez.Adapter1' in ifaces:
                    is_scanning = bool(ifaces['org.bluez.Adapter1'].get('Discovering', False))
                    break
        except Exception:
            pass

    if is_scanning:
        return bt_scan_stop()
    else:
        return bt_scan_start(duration=30)

def bt_discoverable_toggle() -> bool:
    try:
        import dbus
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
        for path, ifaces in manager.GetManagedObjects().items():
            if 'org.bluez.Adapter1' in ifaces:
                props = dbus.Interface(bus.get_object('org.bluez', path), 'org.freedesktop.DBus.Properties')
                cur = bool(props.Get('org.bluez.Adapter1', 'Discoverable'))
                new_val = not cur
                props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(new_val))
                props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(True))
                if new_val:
                    props.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(180))
                return new_val
    except Exception:
        pass
    return False

def bt_discoverable_set(val: bool) -> bool:
    try:
        import dbus
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
        for path, ifaces in manager.GetManagedObjects().items():
            if 'org.bluez.Adapter1' in ifaces:
                props = dbus.Interface(bus.get_object('org.bluez', path), 'org.freedesktop.DBus.Properties')
                props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(val))
                props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(True))
                if val:
                    props.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(180))
                return True
    except Exception:
        pass
    return False

def bt_connect(mac: str) -> bool:
    out = run_cmd(['bluetoothctl', 'connect', mac], timeout=8)
    return "Connection successful" in out or "already connected" in out

def bt_disconnect(mac: str) -> bool:
    out = run_cmd(['bluetoothctl', 'disconnect', mac], timeout=5)
    return "Successful disconnected" in out

def bt_pair(mac: str) -> dict:
    if not mac:
        return {"success": False, "error": "No MAC address provided"}
    mac = mac.strip().upper()
    try:
        pair_out = run_cmd(['bluetoothctl', 'pair', mac], timeout=15)
        trust_out = run_cmd(['bluetoothctl', 'trust', mac], timeout=5)
        conn_out = run_cmd(['bluetoothctl', 'connect', mac], timeout=10)
        ok = "successful" in pair_out.lower() or "already paired" in pair_out.lower() or "connection successful" in conn_out.lower()
        if os.path.exists(BT_CACHE_FILE):
            try:
                with open(BT_CACHE_FILE) as f:
                    c = json.load(f)
                c['devices'] = [d for d in c.get('devices', []) if d.get('mac', '').upper() != mac]
                with open(BT_CACHE_FILE, 'w') as f:
                    json.dump(c, f)
            except Exception:
                pass
        return {"success": ok, "output": f"{pair_out} {conn_out}".strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    elif action == 'bt-scan-start':
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        ok = bt_scan_start(duration)
        print(json.dumps({"success": ok}))
    elif action == 'bt-scan-stop':
        ok = bt_scan_stop()
        print(json.dumps({"success": ok}))
    elif action == 'bt-scan-daemon':
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        bt_scan_daemon(duration)
    elif action == 'bt-discoverable-toggle':
        val = bt_discoverable_toggle()
        print(json.dumps({"success": True, "discoverable": val}))
    elif action == 'bt-discoverable-on':
        ok = bt_discoverable_set(True)
        print(json.dumps({"success": ok, "discoverable": True}))
    elif action == 'bt-discoverable-off':
        ok = bt_discoverable_set(False)
        print(json.dumps({"success": ok, "discoverable": False}))
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
        res = bt_pair(mac)
        print(json.dumps(res))
    elif action == 'bt-remove':
        mac = sys.argv[2] if len(sys.argv) > 2 else ""
        ok = bt_remove(mac)
        print(json.dumps({"success": ok}))
    else:
        print(json.dumps({"error": f"Unknown action {action}"}))
        sys.exit(1)

if __name__ == '__main__':
    main()
