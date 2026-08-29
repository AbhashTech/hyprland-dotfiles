#!/usr/bin/env python3
"""
=============================================================================
 NETCTL-TUI: Modern Terminal Interface for Wi-Fi & Bluetooth Management
 Tailored for Hyprland / Waybar with Catppuccin Aesthetic
=============================================================================
"""

import curses
import os
import re
import subprocess
import sys
import threading
import time

# Version & Metadata
APP_NAME = "NETCTL TUI"
VERSION = "1.1.0"


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[mGKHJ]', '', text)


# =============================================================================
# BACKEND: Wi-Fi Management (iwd / iwctl / rfkill)
# =============================================================================

class WifiManager:
    def __init__(self, interface="wlan0"):
        self.interface = interface
        self.status = {}
        self.networks = []
        self.known_networks = set()
        self.is_scanning = False
        self.last_scan_time = 0

    def refresh_status(self):
        try:
            res = subprocess.run(
                ['iwctl', 'station', self.interface, 'show'],
                capture_output=True, text=True, timeout=2
            )
            status = {}
            for line in res.stdout.splitlines():
                clean = strip_ansi(line).strip()
                if '  ' in clean:
                    parts = [p.strip() for p in re.split(r'\s{2,}', clean) if p.strip()]
                    if len(parts) >= 2:
                        status[parts[0]] = parts[1]
            self.status = status
        except Exception:
            self.status = {"State": "unknown"}

    def refresh_known_networks(self):
        try:
            res = subprocess.run(
                ['iwctl', 'known-networks', 'list'],
                capture_output=True, text=True, timeout=2
            )
            known = set()
            for line in res.stdout.splitlines():
                clean = strip_ansi(line).strip()
                if not clean or 'Known Networks' in clean or '----' in clean or 'Name' in clean:
                    continue
                parts = [p.strip() for p in re.split(r'\s{2,}', clean) if p.strip()]
                if parts:
                    known.add(parts[0])
            self.known_networks = known
        except Exception:
            self.known_networks = set()

    def is_powered(self) -> bool:
        try:
            res = subprocess.run(['rfkill', 'list', 'wlan'], capture_output=True, text=True, timeout=1)
            return "Soft blocked: yes" not in res.stdout and "Hard blocked: yes" not in res.stdout
        except Exception:
            return True

    def toggle_power(self) -> bool:
        try:
            subprocess.run(['rfkill', 'toggle', 'wlan'], timeout=2)
            time.sleep(0.3)
            return True
        except Exception:
            return False

    def scan(self):
        try:
            self.is_scanning = True
            subprocess.run(['iwctl', 'station', self.interface, 'scan'], timeout=4)
            time.sleep(1.2)
            self.refresh_networks()
        except Exception:
            pass
        finally:
            self.is_scanning = False
            self.last_scan_time = time.time()

    def refresh_networks(self):
        self.refresh_known_networks()
        networks = []
        seen = set()

        # Method 1: Try DBus for exact dBm signal accuracy
        try:
            import dbus
            bus = dbus.SystemBus()
            iwd = bus.get_object('net.connman.iwd', '/')
            manager = dbus.Interface(iwd, 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()

            station_path = None
            for path, ifaces in objects.items():
                if 'net.connman.iwd.Station' in ifaces:
                    station_path = path
                    break

            if station_path:
                station_obj = bus.get_object('net.connman.iwd', station_path)
                station_iface = dbus.Interface(station_obj, 'net.connman.iwd.Station')
                ordered = station_iface.GetOrderedNetworks()
                for net_path, signal in ordered:
                    net_props = objects.get(net_path, {}).get('net.connman.iwd.Network', {})
                    name = str(net_props.get('Name', 'Unknown'))
                    if name and name not in seen:
                        seen.add(name)
                        sec = str(net_props.get('Type', 'psk'))
                        is_conn = bool(net_props.get('Connected', False))
                        dbm = signal / 100.0
                        
                        # Calculate accurate Wi-Fi percentage
                        if dbm >= -50:
                            pct = 100
                        elif dbm <= -100:
                            pct = 0
                        else:
                            pct = max(0, min(100, int(2 * (dbm + 100))))

                        # Signal bars
                        if pct >= 75:
                            bars = "▂▄▆█"
                        elif pct >= 50:
                            bars = "▂▄▆_"
                        elif pct >= 25:
                            bars = "▂▄__"
                        else:
                            bars = "▂___"

                        networks.append({
                            'name': name,
                            'security': sec,
                            'signal_bars': bars,
                            'signal_pct': pct,
                            'dbm': dbm,
                            'connected': is_conn,
                            'known': name in self.known_networks
                        })
        except Exception:
            networks = []

        # Method 2: Fallback to iwctl with ANSI color-aware star parsing
        if not networks:
            try:
                res = subprocess.run(
                    ['iwctl', 'station', self.interface, 'get-networks'],
                    capture_output=True, text=True, timeout=3
                )
                for raw_line in res.stdout.splitlines():
                    clean = strip_ansi(raw_line)
                    if not clean.strip() or 'Network name' in clean or '----' in clean:
                        continue
                    is_connected = '>' in clean[:5]
                    clean_content = clean.lstrip('> ').strip()
                    parts = re.split(r'\s{2,}', clean_content)
                    if len(parts) >= 3:
                        name, sec = parts[0], parts[1]
                        if name not in seen:
                            seen.add(name)
                            
                            # In iwctl, bright stars precede ANSI dim codes
                            sig_match = re.search(r'([*]+(?:\x1b\[[0-9;]*m[*]+)?)', raw_line)
                            if sig_match:
                                raw_sig = sig_match.group(1)
                                bright_stars = raw_sig.split('\x1b')[0].count('*') if '\x1b' in raw_sig else raw_sig.count('*')
                            else:
                                bright_stars = 2
                            
                            pct = min(100, max(0, bright_stars * 25))
                            bars = "▂▄▆█"[:bright_stars] + "____"[bright_stars:]

                            networks.append({
                                'name': name,
                                'security': sec,
                                'signal_bars': bars,
                                'signal_pct': pct,
                                'connected': is_connected,
                                'known': name in self.known_networks
                            })
            except Exception:
                pass

        self.networks = networks

    def connect(self, ssid: str, password: str = None) -> tuple[bool, str]:
        try:
            if password:
                cmd = ['iwctl', '--passphrase', password, 'station', self.interface, 'connect', ssid]
            else:
                cmd = ['iwctl', 'station', self.interface, 'connect', ssid]
            
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                self.refresh_known_networks()
                return True, f"Connected to '{ssid}'"
            else:
                err = strip_ansi(res.stderr or res.stdout).strip()
                return False, f"{err or 'Connection failed'}"
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            return False, str(e)

    def forget(self, ssid: str) -> tuple[bool, str]:
        try:
            res = subprocess.run(['iwctl', 'known-networks', ssid, 'forget'], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                self.refresh_known_networks()
                return True, f"Forgot network '{ssid}'"
            return False, "Could not forget network"
        except Exception as e:
            return False, str(e)

    def disconnect(self) -> tuple[bool, str]:
        try:
            res = subprocess.run(['iwctl', 'station', self.interface, 'disconnect'], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                return True, "Disconnected from Wi-Fi"
            return False, "Failed to disconnect"
        except Exception as e:
            return False, str(e)


# =============================================================================
# BACKEND: Bluetooth Management (rfkill / bluetoothctl)
# =============================================================================

class BluetoothManager:
    def __init__(self):
        self.devices = []
        self.is_scanning = False
        self.service_active = False
        self.adapter_path = None

    def check_service(self) -> bool:
        try:
            import dbus
            bus = dbus.SystemBus()
            bluez = bus.get_object('org.bluez', '/')
            manager = dbus.Interface(bluez, 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()
            for path, ifaces in objects.items():
                if 'org.bluez.Adapter1' in ifaces:
                    self.adapter_path = path
                    self.service_active = True
                    return True
        except Exception:
            pass
        self.service_active = False
        return False

    def is_powered(self) -> bool:
        if self.check_service() and self.adapter_path:
            try:
                import dbus
                bus = dbus.SystemBus()
                adapter = bus.get_object('org.bluez', self.adapter_path)
                props = dbus.Interface(adapter, 'org.freedesktop.DBus.Properties')
                return bool(props.Get('org.bluez.Adapter1', 'Powered'))
            except Exception:
                pass
        try:
            res = subprocess.run(['rfkill', 'list', 'bluetooth'], capture_output=True, text=True, timeout=1)
            return "Soft blocked: yes" not in res.stdout and "Hard blocked: yes" not in res.stdout
        except Exception:
            return False

    def toggle_power(self) -> bool:
        if self.check_service() and self.adapter_path:
            try:
                import dbus
                bus = dbus.SystemBus()
                adapter = bus.get_object('org.bluez', self.adapter_path)
                props = dbus.Interface(adapter, 'org.freedesktop.DBus.Properties')
                current = bool(props.Get('org.bluez.Adapter1', 'Powered'))
                props.Set('org.bluez.Adapter1', 'Powered', not current)
                time.sleep(0.3)
                return True
            except Exception:
                pass
        try:
            subprocess.run(['rfkill', 'toggle', 'bluetooth'], timeout=2)
            time.sleep(0.3)
            return True
        except Exception:
            return False

    def scan(self):
        if not self.check_service() or not self.adapter_path:
            return
        self.is_scanning = True
        try:
            import dbus
            bus = dbus.SystemBus()
            adapter = bus.get_object('org.bluez', self.adapter_path)
            adapter_iface = dbus.Interface(adapter, 'org.bluez.Adapter1')
            
            try:
                adapter_iface.StartDiscovery()
            except Exception:
                pass

            # Scan for 6 seconds, updating live discovered devices every second
            for _ in range(6):
                time.sleep(1)
                self.refresh()

            try:
                adapter_iface.StopDiscovery()
            except Exception:
                pass
        except Exception:
            pass
        finally:
            self.is_scanning = False
            self.refresh()

    def refresh(self):
        if not self.check_service():
            self.devices = []
            return

        devices = []
        try:
            import dbus
            bus = dbus.SystemBus()
            bluez = bus.get_object('org.bluez', '/')
            manager = dbus.Interface(bluez, 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()

            for path, ifaces in objects.items():
                if 'org.bluez.Device1' in ifaces:
                    dev = ifaces['org.bluez.Device1']
                    mac = str(dev.get('Address', ''))
                    name = str(dev.get('Name', dev.get('Alias', 'Unknown Device')))
                    is_paired = bool(dev.get('Paired', False))
                    is_trusted = bool(dev.get('Trusted', False))
                    is_conn = bool(dev.get('Connected', False))
                    rssi = int(dev.get('RSSI', 0)) if 'RSSI' in dev else None

                    devices.append({
                        'path': path,
                        'mac': mac,
                        'name': name,
                        'paired': is_paired,
                        'trusted': is_trusted,
                        'connected': is_conn,
                        'rssi': rssi
                    })

            # Sort: Connected first, then Paired, then alphabetically
            devices.sort(key=lambda d: (not d['connected'], not d['paired'], d['name'].lower()))

        except Exception:
            pass

        self.devices = devices

    def connect_device(self, mac: str) -> tuple[bool, str]:
        if not self.check_service():
            return False, "bluetooth.service is inactive"
        try:
            # Ensure device is trusted before connecting to prevent auto-disconnect
            subprocess.run(['bluetoothctl', '--timeout', '3', 'trust', mac], capture_output=True, text=True, timeout=4)
            res = subprocess.run(['bluetoothctl', '--timeout', '7', 'connect', mac], capture_output=True, text=True, timeout=8)
            if res.returncode == 0 or "Connection successful" in res.stdout:
                return True, f"Connected to {mac}"
            return False, f"{res.stdout.strip() or 'Failed to connect'}"
        except Exception as e:
            return False, str(e)

    def disconnect_device(self, mac: str) -> tuple[bool, str]:
        if not self.check_service():
            return False, "bluetooth.service is inactive"
        try:
            res = subprocess.run(['bluetoothctl', '--timeout', '4', 'disconnect', mac], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 or "Successful disconnected" in res.stdout:
                return True, f"Disconnected from {mac}"
            return False, f"Failed to disconnect"
        except Exception as e:
            return False, str(e)

    def trust_device(self, mac: str) -> tuple[bool, str]:
        if not self.check_service():
            return False, "bluetooth.service is inactive"
        try:
            res = subprocess.run(['bluetoothctl', '--timeout', '4', 'trust', mac], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 or "trust succeeded" in res.stdout.lower():
                return True, f"Trusted {mac}"
            return False, f"{res.stdout.strip() or 'Failed to trust device'}"
        except Exception as e:
            return False, str(e)

    def untrust_device(self, mac: str) -> tuple[bool, str]:
        if not self.check_service():
            return False, "bluetooth.service is inactive"
        try:
            res = subprocess.run(['bluetoothctl', '--timeout', '4', 'untrust', mac], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 or "untrust succeeded" in res.stdout.lower():
                return True, f"Untrusted {mac}"
            return False, f"{res.stdout.strip() or 'Failed to untrust device'}"
        except Exception as e:
            return False, str(e)

    def toggle_trust_device(self, mac: str) -> tuple[bool, str]:
        dev = next((d for d in self.devices if d['mac'] == mac), None)
        if dev and dev.get('trusted'):
            return self.untrust_device(mac)
        else:
            return self.trust_device(mac)

    def pair_device(self, mac: str) -> tuple[bool, str]:
        if not self.check_service():
            return False, "bluetooth.service is inactive"
        try:
            # Ensure adapter is pairable
            subprocess.run(['bluetoothctl', '--timeout', '2', 'pairable', 'on'], capture_output=True, text=True, timeout=3)
            res = subprocess.run(['bluetoothctl', '--timeout', '12', 'pair', mac], capture_output=True, text=True, timeout=13)
            if res.returncode == 0 or "Pairing successful" in res.stdout:
                # Automatically trust on pairing!
                subprocess.run(['bluetoothctl', '--timeout', '3', 'trust', mac], capture_output=True, text=True, timeout=4)
                # Auto connect after pairing and trusting
                conn_res = self.connect_device(mac)
                if conn_res[0]:
                    return True, f"Paired, Trusted & Connected to {mac}"
                return True, f"Paired & Trusted {mac}"
            return False, f"{res.stdout.strip() or 'Pairing failed'}"
        except Exception as e:
            return False, str(e)

    def unpair_device(self, mac: str) -> tuple[bool, str]:
        if not self.check_service():
            return False, "bluetooth.service is inactive"
        try:
            res = subprocess.run(['bluetoothctl', '--timeout', '3', 'remove', mac], capture_output=True, text=True, timeout=4)
            if res.returncode == 0:
                return True, f"Removed {mac}"
            return False, "Failed to remove device"
        except Exception as e:
            return False, str(e)


# =============================================================================
# TUI INTERFACE (Curses Application)
# =============================================================================

class NetctlTUI:
    SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, stdscr, initial_tab: int = 0):
        self.stdscr = stdscr
        self.tab = initial_tab  # 0 = Wi-Fi, 1 = Bluetooth
        self.wifi = WifiManager()
        self.bt = BluetoothManager()
        
        self.selected_idx = 0
        self.status_msg = "Initializing..."
        self.status_msg_time = time.time() + 10
        self.running = True
        self.is_initial_loading = True
        self.spinner_idx = 0
        self.busy_task = None  # Tracks live background operation
        
        self.init_curses()
        
        # Immediate first frame draw so the screen renders instantly (<10ms)
        try:
            max_y, max_x = self.stdscr.getmaxyx()
            self.draw_header(max_y, max_x)
            self.draw_wifi_tab(max_y, max_x)
            self.draw_footer(max_y, max_x)
            self.stdscr.refresh()
        except Exception:
            pass

        # Asynchronous initial load in background thread
        threading.Thread(target=self._initial_load_worker, daemon=True).start()

    def get_spinner(self) -> str:
        self.spinner_idx = (self.spinner_idx + 1) % len(self.SPINNER)
        return self.SPINNER[self.spinner_idx]

    def dispatch_async(self, task_name: str, target_id: str, action_func, on_success_refresh: bool = True):
        """Run an action in background without blocking the UI or key events."""
        if self.busy_task:
            self.set_toast(f"Busy: {self.busy_task['name']} in progress...")
            return
        
        self.busy_task = {
            "name": task_name,
            "target_id": target_id,
            "start_time": time.time()
        }
        self.set_toast(f"⚡ {task_name}...")

        def _worker():
            try:
                result = action_func()
                if isinstance(result, tuple) and len(result) == 2:
                    ok, msg = result
                elif isinstance(result, bool):
                    ok, msg = result, "Operation completed"
                else:
                    ok, msg = True, str(result or "Done")
                prefix = "✔" if ok else "✖"
                self.set_toast(f"{prefix} {msg}")
            except Exception as e:
                self.set_toast(f"✖ Error: {e}")
            finally:
                self.busy_task = None
                if on_success_refresh:
                    try:
                        self.refresh_all_data()
                    except Exception:
                        pass

        threading.Thread(target=_worker, daemon=True).start()

    def _initial_load_worker(self):
        try:
            self.wifi.refresh_status()
            self.wifi.refresh_networks()
            self.bt.check_service()
            self.bt.refresh()
        except Exception:
            pass
        finally:
            self.is_initial_loading = False
            self.set_toast("Ready. [Tab] Switch Tab, [Enter] Connect, [s] Scan, [?] Help")

    def init_curses(self):
        try:
            curses.curs_set(0)
        except Exception:
            pass
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, -1)              # Normal
            curses.init_pair(2, curses.COLOR_MAGENTA, -1)            # Mauve Header / Titles
            curses.init_pair(3, curses.COLOR_CYAN, -1)               # Accent / Sapphire
            curses.init_pair(4, curses.COLOR_GREEN, -1)              # Success / Connected
            curses.init_pair(5, curses.COLOR_YELLOW, -1)             # Warning / Scanning
            curses.init_pair(6, curses.COLOR_RED, -1)                # Error / Disconnected
            curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN) # Highlighted Row

    def set_toast(self, message: str, duration: int = 5):
        self.status_msg = message
        self.status_msg_time = time.time() + duration

    def refresh_all_data(self):
        if not self.is_initial_loading:
            self.wifi.refresh_status()
            self.wifi.refresh_networks()
            self.bt.check_service()
            self.bt.refresh()

    def draw_header(self, max_y, max_x):
        title = f"  󰤨  {APP_NAME}  󰂯  v{VERSION}  "
        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(1, 2, title)
        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        tab0_label = "  [1] 󰤨  Wi-Fi (iwd)  "
        tab1_label = "  [2] 󰂯  Bluetooth  "

        tab0_attr = (curses.color_pair(7) | curses.A_BOLD) if self.tab == 0 else (curses.color_pair(1))
        tab1_attr = (curses.color_pair(7) | curses.A_BOLD) if self.tab == 1 else (curses.color_pair(1))

        self.stdscr.attron(tab0_attr)
        self.stdscr.addstr(3, 4, tab0_label)
        self.stdscr.attroff(tab0_attr)

        self.stdscr.attron(tab1_attr)
        self.stdscr.addstr(3, 26, tab1_label)
        self.stdscr.attroff(tab1_attr)

        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.hline(4, 2, curses.ACS_HLINE, max_x - 4)
        self.stdscr.attroff(curses.color_pair(3))

    def draw_footer(self, max_y, max_x):
        if self.busy_task:
            elapsed = time.time() - self.busy_task['start_time']
            task_str = f" {self.get_spinner()} {self.busy_task['name']} ({elapsed:.1f}s)...  [Press 'q' or Esc to exit]"
            self.stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
            self.stdscr.addstr(max_y - 3, 2, f"{task_str:<{max_x - 4}}")
            self.stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
        elif time.time() < self.status_msg_time:
            self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            self.stdscr.addstr(max_y - 3, 3, f"● {self.status_msg[:max_x - 6]}")
            self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        else:
            self.stdscr.addstr(max_y - 3, 3, " " * (max_x - 6))

        if self.tab == 0:
            keys = "[Tab] Tab  [↑/↓] Select  [Enter/c] Connect  [d] Disconnect  [f] Forget  [s] Scan  [p] Power  [q] Quit"
        else:
            keys = "[Tab] Tab  [↑/↓] Select  [Enter/c] Connect  [t] Trust/Untrust  [u] Unpair  [d] Disconnect  [s] Scan  [p] Power  [q] Quit"
        self.stdscr.attron(curses.color_pair(1) | curses.A_DIM)
        self.stdscr.addstr(max_y - 2, 3, keys[:max_x - 6])
        self.stdscr.attroff(curses.color_pair(1) | curses.A_DIM)

    def draw_wifi_tab(self, max_y, max_x):
        powered = self.wifi.is_powered()
        state = self.wifi.status.get("State", "disconnected")
        connected_ssid = self.wifi.status.get("Connected network", "None")
        ip_addr = self.wifi.status.get("IPv4 address", "N/A")
        rssi = self.wifi.status.get("RSSI", "N/A")
        bitrate = self.wifi.status.get("TxBitrate", "N/A")
        if bitrate != "N/A":
            try:
                bitrate = f"{int(bitrate) // 1000} Mbps"
            except Exception:
                pass

        self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(5, 3, "┌─ Wi-Fi Interface & Status ──────────────────────────────────────────────┐")
        self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        power_str = "● POWER ON " if powered else "○ POWER OFF"
        power_color = curses.color_pair(4) if powered else curses.color_pair(6)
        self.stdscr.addstr(6, 5, "Radio: ")
        self.stdscr.attron(power_color | curses.A_BOLD)
        self.stdscr.addstr(6, 12, power_str)
        self.stdscr.attroff(power_color | curses.A_BOLD)

        state_str = f"● {state.upper()}" if state == "connected" else f"○ {state.upper()}"
        state_color = curses.color_pair(4) if state == "connected" else curses.color_pair(5)
        self.stdscr.addstr(6, 28, "State: ")
        self.stdscr.attron(state_color | curses.A_BOLD)
        self.stdscr.addstr(6, 35, state_str)
        self.stdscr.attroff(state_color | curses.A_BOLD)

        self.stdscr.addstr(7, 5, "SSID: ")
        self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.addstr(7, 11, f"{connected_ssid:<20}")
        self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

        self.stdscr.addstr(7, 33, f"IP: {ip_addr:<15}  Signal: {rssi:<9}  Speed: {bitrate}")

        self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(8, 3, "└─────────────────────────────────────────────────────────────────────────┘")
        self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        table_top = 10
        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(table_top, 3, f"Available Wi-Fi Networks ({len(self.wifi.networks)})")
        if self.wifi.is_scanning:
            self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(table_top, 32, "⚡ Scanning...")
            self.stdscr.attroff(curses.color_pair(5))
        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        self.stdscr.attron(curses.color_pair(1) | curses.A_DIM)
        header_fmt = "  {:<3} {:<26} {:<12} {:<14} {:<12}"
        self.stdscr.addstr(table_top + 1, 3, header_fmt.format("STA", "NETWORK NAME / SSID", "SAVED", "SECURITY", "SIGNAL"))
        self.stdscr.attroff(curses.color_pair(1) | curses.A_DIM)

        list_start_y = table_top + 2
        visible_rows = max(1, max_y - list_start_y - 4)

        if not self.wifi.networks:
            if self.is_initial_loading:
                self.stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
                self.stdscr.addstr(list_start_y + 1, 6, f"{self.get_spinner()}  Initializing Wi-Fi interfaces & discovering networks...")
                self.stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
            else:
                self.stdscr.addstr(list_start_y + 1, 6, "No networks found. Press [s] to scan for available Wi-Fi networks.")
            return

        if self.selected_idx >= len(self.wifi.networks):
            self.selected_idx = len(self.wifi.networks) - 1
        if self.selected_idx < 0:
            self.selected_idx = 0

        start_offset = 0
        if self.selected_idx >= visible_rows:
            start_offset = self.selected_idx - visible_rows + 1

        for i in range(visible_rows):
            item_idx = start_offset + i
            if item_idx >= len(self.wifi.networks):
                break
            
            net = self.wifi.networks[item_idx]
            y = list_start_y + i
            is_selected = (item_idx == self.selected_idx)
            is_conn = net.get('connected', False)
            is_known = net.get('known', False)

            status_icon = "●" if is_conn else " "
            saved_badge = "★ Saved" if is_known else "       "

            row_str = f" {status_icon:<2} {net['name'][:24]:<26} {saved_badge:<12} {net['security'][:12]:<14} {net['signal_bars']} {net['signal_pct']}%"

            if is_selected:
                self.stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
                self.stdscr.addstr(y, 3, f" ▶ {row_str:<{max_x - 9}} ")
                self.stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)
            else:
                conn_color = curses.color_pair(4) if is_conn else (curses.color_pair(3) if is_known else curses.color_pair(1))
                self.stdscr.attron(conn_color)
                self.stdscr.addstr(y, 3, f"   {row_str}")
                self.stdscr.attroff(conn_color)

    def draw_bluetooth_tab(self, max_y, max_x):
        powered = self.bt.is_powered()
        service_ok = self.bt.service_active

        self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(5, 3, "┌─ Bluetooth Hardware & Service Status ──────────────────────────────────┐")
        self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        power_str = "● POWER ON " if powered else "○ POWER OFF / BLOCKED"
        power_color = curses.color_pair(4) if powered else curses.color_pair(6)
        self.stdscr.addstr(6, 5, "Radio: ")
        self.stdscr.attron(power_color | curses.A_BOLD)
        self.stdscr.addstr(6, 12, power_str)
        self.stdscr.attroff(power_color | curses.A_BOLD)

        service_str = "● ACTIVE" if service_ok else "○ INACTIVE (Disabled)"
        service_color = curses.color_pair(4) if service_ok else curses.color_pair(5)
        self.stdscr.addstr(6, 38, "Service: ")
        self.stdscr.attron(service_color | curses.A_BOLD)
        self.stdscr.addstr(6, 47, service_str)
        self.stdscr.attroff(service_color | curses.A_BOLD)

        if not service_ok:
            self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(7, 5, "Notice: Start daemon via terminal: 'sudo systemctl start bluetooth'")
            self.stdscr.attroff(curses.color_pair(5))
        else:
            self.stdscr.addstr(7, 5, "Daemon: BlueZ (bluetoothctl) Ready   Press [s] to Scan nearby devices")

        self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(8, 3, "└─────────────────────────────────────────────────────────────────────────┘")
        self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        table_top = 10
        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        self.stdscr.addstr(table_top, 3, f"Bluetooth Devices ({len(self.bt.devices)})")
        if self.bt.is_scanning:
            self.stdscr.attron(curses.color_pair(5))
            self.stdscr.addstr(table_top, 28, "⚡ Scanning (5s)...")
            self.stdscr.attroff(curses.color_pair(5))
        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        list_start_y = table_top + 2
        visible_rows = max(1, max_y - list_start_y - 4)

        if not service_ok:
            self.stdscr.addstr(list_start_y, 5, "Bluetooth service is currently stopped.")
            self.stdscr.addstr(list_start_y + 1, 5, "• Press [p] to Toggle hardware radio power.")
            self.stdscr.addstr(list_start_y + 3, 5, "• To enable Bluetooth scan/pairing, start the service in a terminal:")
            self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            self.stdscr.addstr(list_start_y + 4, 7, "sudo systemctl enable --now bluetooth")
            self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
            return

        if not self.bt.devices:
            if self.is_initial_loading:
                self.stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
                self.stdscr.addstr(list_start_y, 6, f"{self.get_spinner()}  Checking Bluetooth daemon & discovering devices...")
                self.stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
            else:
                self.stdscr.addstr(list_start_y, 5, "No devices found. Press [s] to scan for discoverable devices.")
            return

        if self.selected_idx >= len(self.bt.devices):
            self.selected_idx = len(self.bt.devices) - 1
        if self.selected_idx < 0:
            self.selected_idx = 0

        self.stdscr.attron(curses.color_pair(1) | curses.A_DIM)
        header_fmt = "  {:<24} {:<18} {:<10} {:<10} {:<14}"
        self.stdscr.addstr(table_top + 1, 3, header_fmt.format("DEVICE NAME", "MAC ADDRESS", "PAIRED", "TRUSTED", "STATUS"))
        self.stdscr.attroff(curses.color_pair(1) | curses.A_DIM)

        for i, dev in enumerate(self.bt.devices[:visible_rows]):
            y = list_start_y + i
            is_selected = (i == self.selected_idx)
            is_conn = dev.get('connected', False)
            is_paired = dev.get('paired', False)
            is_trusted = dev.get('trusted', False)

            if self.busy_task and self.busy_task.get('target_id') == dev['mac']:
                status_str = f"{self.get_spinner()} Working..."
            else:
                status_str = "● Connected" if is_conn else ("○ Ready" if is_paired else "󰂯 Nearby")
            paired_str = "★ Yes" if is_paired else "No"
            trusted_str = "✔ Yes" if is_trusted else "No"

            row_str = f" {dev['name'][:22]:<24} {dev['mac']:<18} {paired_str:<10} {trusted_str:<10} {status_str:<14}"
            if is_selected:
                self.stdscr.attron(curses.color_pair(7) | curses.A_BOLD)
                self.stdscr.addstr(y, 3, f" ▶ {row_str:<{max_x - 9}} ")
                self.stdscr.attroff(curses.color_pair(7) | curses.A_BOLD)
            else:
                if self.busy_task and self.busy_task.get('target_id') == dev['mac']:
                    conn_color = curses.color_pair(5) | curses.A_BOLD
                else:
                    conn_color = curses.color_pair(4) if is_conn else curses.color_pair(1)
                self.stdscr.attron(conn_color)
                self.stdscr.addstr(y, 3, f"   {row_str}")
                self.stdscr.attroff(conn_color)

    def prompt_password_modal(self, ssid: str) -> str | None:
        try:
            curses.curs_set(1)
        except Exception:
            pass
        max_y, max_x = self.stdscr.getmaxyx()
        
        box_w = min(60, max_x - 6)
        box_h = 10
        start_y = max(2, (max_y - box_h) // 2)
        start_x = max(2, (max_x - box_w) // 2)

        win = curses.newwin(box_h, box_w, start_y, start_x)
        win.keypad(True)
        win.box()

        password = []
        show_plain = False

        while True:
            win.erase()
            win.box()
            win.attron(curses.color_pair(2) | curses.A_BOLD)
            win.addstr(1, 3, f" Connect to '{ssid[:box_w - 20]}' ")
            win.attroff(curses.color_pair(2) | curses.A_BOLD)

            win.addstr(3, 3, "Password:")
            
            pw_display = "".join(password) if show_plain else ("*" * len(password))
            win.attron(curses.color_pair(7))
            win.addstr(4, 3, f" {pw_display:<{box_w - 8}} ")
            win.attroff(curses.color_pair(7))

            win.attron(curses.color_pair(1) | curses.A_DIM)
            win.addstr(6, 3, "[Enter] Submit   [Esc] Cancel   [Ctrl+V] Toggle View")
            win.attroff(curses.color_pair(1) | curses.A_DIM)

            win.refresh()

            try:
                ch = win.getch()
            except Exception:
                continue

            if ch in (10, 13, curses.KEY_ENTER):
                try:
                    curses.curs_set(0)
                except Exception:
                    pass
                return "".join(password)
            elif ch in (27,):  # Esc
                try:
                    curses.curs_set(0)
                except Exception:
                    pass
                return None
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if password:
                    password.pop()
            elif ch == 22:  # Ctrl+V
                show_plain = not show_plain
            elif 32 <= ch <= 126:
                if len(password) < 64:
                    password.append(chr(ch))

    def show_help_modal(self):
        max_y, max_x = self.stdscr.getmaxyx()
        box_w = min(70, max_x - 4)
        box_h = 18
        start_y = max(2, (max_y - box_h) // 2)
        start_x = max(2, (max_x - box_w) // 2)

        win = curses.newwin(box_h, box_w, start_y, start_x)
        win.box()

        win.attron(curses.color_pair(2) | curses.A_BOLD)
        win.addstr(1, 3, f" {APP_NAME} - Controls & Tips ")
        win.attroff(curses.color_pair(2) | curses.A_BOLD)

        help_lines = [
            ("Tab / 1 / 2", "Switch between Wi-Fi and Bluetooth tabs"),
            ("↑ / ↓ or k / j", "Navigate through networks/devices"),
            ("Enter / c", "Connect to selected network/device (auto-trust on pair)"),
            ("t", "Toggle Trust/Untrust for selected Bluetooth device"),
            ("d", "Disconnect active network/device"),
            ("f", "Forget saved Wi-Fi network credentials"),
            ("P / e", "Enter/change password manually for Wi-Fi network"),
            ("s / r", "Scan for wireless networks / Bluetooth devices"),
            ("p", "Toggle Radio Power (ON / OFF)"),
            ("u", "Unpair / Remove Bluetooth device"),
            ("?", "Toggle this Help window"),
            ("q / Esc", "Quit NETCTL TUI"),
        ]

        for idx, (key, desc) in enumerate(help_lines):
            win.attron(curses.color_pair(3) | curses.A_BOLD)
            win.addstr(3 + idx, 4, f"{key:<16}")
            win.attroff(curses.color_pair(3) | curses.A_BOLD)
            win.addstr(3 + idx, 22, desc)

        win.attron(curses.color_pair(1) | curses.A_DIM)
        win.addstr(box_h - 2, 4, "Press any key to close...")
        win.attroff(curses.color_pair(1) | curses.A_DIM)

        win.refresh()
        while True:
            ch = win.getch()
            if ch != -1:
                break

    def run(self):
        last_refresh = 0

        while self.running:
            max_y, max_x = self.stdscr.getmaxyx()
            self.stdscr.erase()

            if time.time() - last_refresh > 5:
                self.refresh_all_data()
                last_refresh = time.time()

            self.draw_header(max_y, max_x)
            if self.tab == 0:
                self.draw_wifi_tab(max_y, max_x)
            else:
                self.draw_bluetooth_tab(max_y, max_x)
            self.draw_footer(max_y, max_x)

            self.stdscr.refresh()

            try:
                ch = self.stdscr.getch()
            except Exception:
                continue

            if ch == -1:
                time.sleep(0.05)
                continue

            # Instant Quit on 'q', 'Q', Escape, or Ctrl+C at any moment
            if ch in (ord('q'), ord('Q'), 27, 3):
                self.running = False
                break

            elif ch in (ord('\t'), curses.KEY_BTAB):
                self.tab = 1 if self.tab == 0 else 0
                self.selected_idx = 0
                self.set_toast(f"Switched to {'Wi-Fi' if self.tab == 0 else 'Bluetooth'}")

            elif ch == ord('1'):
                self.tab = 0
                self.selected_idx = 0

            elif ch == ord('2'):
                self.tab = 1
                self.selected_idx = 0

            elif ch in (curses.KEY_UP, ord('k')):
                if self.selected_idx > 0:
                    self.selected_idx -= 1

            elif ch in (curses.KEY_DOWN, ord('j')):
                max_items = len(self.wifi.networks) if self.tab == 0 else len(self.bt.devices)
                if self.selected_idx < max_items - 1:
                    self.selected_idx += 1

            elif ch in (ord('s'), ord('r'), ord('R')):
                if self.tab == 0:
                    self.set_toast("⚡ Scanning for Wi-Fi networks...")
                    threading.Thread(target=self.wifi.scan, daemon=True).start()
                else:
                    if self.bt.service_active:
                        self.set_toast("⚡ Scanning for Bluetooth devices (6s)...")
                        threading.Thread(target=self.bt.scan, daemon=True).start()
                    else:
                        self.set_toast("⚠ Bluetooth service is inactive. Run: sudo systemctl start bluetooth")

            elif ch in (ord('p'),):
                if self.tab == 0:
                    self.dispatch_async("Toggling Wi-Fi Radio", "", lambda: (self.wifi.toggle_power(), "Wi-Fi radio toggled"))
                else:
                    self.dispatch_async("Toggling Bluetooth Radio", "", lambda: (self.bt.toggle_power(), "Bluetooth radio toggled"))

            elif ch in (ord('t'), ord('T')):
                if self.tab == 1 and self.bt.devices:
                    selected_dev = self.bt.devices[self.selected_idx]
                    mac = selected_dev['mac']
                    dev_name = selected_dev['name']
                    self.dispatch_async(
                        f"Toggling Trust for {dev_name}",
                        mac,
                        lambda m=mac: self.bt.toggle_trust_device(m)
                    )
                elif self.tab == 0:
                    self.dispatch_async("Toggling Wi-Fi Radio", "", lambda: (self.wifi.toggle_power(), "Wi-Fi radio toggled"))

            elif ch in (10, 13, curses.KEY_ENTER, ord('c')):
                if self.tab == 0 and self.wifi.networks:
                    selected_net = self.wifi.networks[self.selected_idx]
                    ssid = selected_net['name']
                    sec = selected_net['security']
                    is_known = selected_net.get('known', False)

                    if selected_net.get('connected'):
                        self.set_toast(f"Already connected to '{ssid}'")
                    elif is_known or 'open' in sec.lower() or not sec:
                        # Auto-connect with saved credentials in background
                        self.dispatch_async(
                            f"Connecting to saved '{ssid}'",
                            ssid,
                            lambda s=ssid: self.wifi.connect(s)
                        )
                    else:
                        # Prompt for password, then connect in background
                        password = self.prompt_password_modal(ssid)
                        if password is not None:
                            self.dispatch_async(
                                f"Connecting to '{ssid}'",
                                ssid,
                                lambda s=ssid, p=password: self.wifi.connect(s, p)
                            )
                        else:
                            self.set_toast("Connection cancelled")

                elif self.tab == 1 and self.bt.devices:
                    selected_dev = self.bt.devices[self.selected_idx]
                    mac = selected_dev['mac']
                    dev_name = selected_dev['name']

                    if not selected_dev.get('paired'):
                        self.dispatch_async(
                            f"Pairing & Trusting {dev_name}",
                            mac,
                            lambda m=mac: self.bt.pair_device(m)
                        )
                    else:
                        self.dispatch_async(
                            f"Connecting to {dev_name}",
                            mac,
                            lambda m=mac: self.bt.connect_device(m)
                        )

            elif ch == ord('f'):  # Forget network
                if self.tab == 0 and self.wifi.networks:
                    selected_net = self.wifi.networks[self.selected_idx]
                    ssid = selected_net['name']
                    self.dispatch_async(f"Forgetting '{ssid}'", ssid, lambda s=ssid: self.wifi.forget(s))

            elif ch in (ord('P'), ord('e')):  # Force password prompt
                if self.tab == 0 and self.wifi.networks:
                    selected_net = self.wifi.networks[self.selected_idx]
                    ssid = selected_net['name']
                    password = self.prompt_password_modal(ssid)
                    if password is not None:
                        self.dispatch_async(
                            f"Connecting to '{ssid}'",
                            ssid,
                            lambda s=ssid, p=password: self.wifi.connect(s, p)
                        )

            elif ch == ord('u'):  # Unpair BT device
                if self.tab == 1 and self.bt.devices:
                    selected_dev = self.bt.devices[self.selected_idx]
                    mac = selected_dev['mac']
                    dev_name = selected_dev['name']
                    self.dispatch_async(f"Removing {dev_name}", mac, lambda m=mac: self.bt.unpair_device(m))

            elif ch == ord('d'):  # Disconnect
                if self.tab == 0:
                    self.dispatch_async("Disconnecting Wi-Fi", "", lambda: self.wifi.disconnect())
                elif self.tab == 1 and self.bt.devices:
                    selected_dev = self.bt.devices[self.selected_idx]
                    mac = selected_dev['mac']
                    dev_name = selected_dev['name']
                    self.dispatch_async(f"Disconnecting {dev_name}", mac, lambda m=mac: self.bt.disconnect_device(m))

            elif ch in (ord('?'), ord('h')):
                self.show_help_modal()


def main():
    initial_tab = 0
    if len(sys.argv) > 1 and sys.argv[1].lower() in ('bt', 'bluetooth', '--bluetooth', '-b', '2'):
        initial_tab = 1
    try:
        curses.wrapper(lambda stdscr: NetctlTUI(stdscr, initial_tab=initial_tab).run())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

