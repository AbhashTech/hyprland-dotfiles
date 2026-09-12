#!/usr/bin/env python3
"""
=============================================================================
 Hyprland Bluetooth Authentication Agent Daemon
 Provides BlueZ Agent1 implementation for handling Passkeys, PINs, and
 Authorizations (Keyboards, Mice, Audio, Gamepads).
 Displays desktop notifications (via notify-send/mako) for keyboard PINs.
=============================================================================
"""

import os
import sys
import time
import subprocess
import signal
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

AGENT_PATH = "/org/bluez/hyprland_agent"
CAPABILITY = "KeyboardDisplay"


class BluetoothAgent(dbus.service.Object):
    def __init__(self, bus, path):
        super().__init__(bus, path)
        self.bus = bus

    def _get_device_name(self, device_path):
        try:
            dev_obj = self.bus.get_object("org.bluez", device_path)
            props = dbus.Interface(dev_obj, "org.freedesktop.DBus.Properties")
            return str(props.Get("org.bluez.Device1", "Alias") or props.Get("org.bluez.Device1", "Name") or "Device")
        except Exception:
            return "Bluetooth Device"

    def _notify(self, title, message, urgency="normal", timeout=15000):
        try:
            subprocess.Popen([
                "notify-send",
                "-a", "Bluetooth",
                "-i", "bluetooth",
                "-u", urgency,
                "-t", str(timeout),
                title,
                message
            ])
        except Exception:
            pass

    def _prompt_user(self, title, message, timeout=25):
        """Prompt user via interactive notification with action buttons."""
        try:
            res = subprocess.run(
                [
                    "notify-send",
                    "-a", "Bluetooth",
                    "-i", "bluetooth",
                    "-u", "critical",
                    "-t", str(timeout * 1000),
                    "--action=allow=Allow",
                    "--action=deny=Deny",
                    title,
                    message
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return res.stdout.strip() == "allow"
        except Exception:
            return False

    def _is_device_trusted(self, device_path):
        try:
            dev_obj = self.bus.get_object("org.bluez", device_path)
            props = dbus.Interface(dev_obj, "org.freedesktop.DBus.Properties")
            return bool(props.Get("org.bluez.Device1", "Trusted"))
        except Exception:
            return False

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        pass

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        dev_name = self._get_device_name(device)
        if self._is_device_trusted(device):
            return

        is_hid = "1124" in uuid.lower() or "1812" in uuid.lower()
        svc_desc = "Keyboard/Mouse Input (HID)" if is_hid else "Bluetooth Service"

        allowed = self._prompt_user(
            f"󰌌 Authorize {svc_desc}",
            f"Device '{dev_name}' is requesting {svc_desc} access. Allow?"
        )
        if not allowed:
            raise dbus.exceptions.DBusException("Service authorization rejected", name="org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        dev_name = self._get_device_name(device)
        self._notify("󰂯 Bluetooth Pairing Blocked", f"Untrusted device '{dev_name}' requested legacy PIN. Auto-pairing rejected for security.", urgency="critical")
        raise dbus.exceptions.DBusException("Automatic PIN pairing is disabled for security", name="org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        dev_name = self._get_device_name(device)
        self._notify("󰂯 Bluetooth Pairing Blocked", f"Untrusted device '{dev_name}' requested legacy Passkey. Auto-pairing rejected for security.", urgency="critical")
        raise dbus.exceptions.DBusException("Automatic passkey pairing is disabled for security", name="org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        dev_name = self._get_device_name(device)
        passkey_str = f"{passkey:06d}"
        self._notify(
            f"󰌌 Pair Keyboard: {dev_name}",
            f"Type {passkey_str} on the keyboard and press Enter.",
            urgency="critical",
            timeout=30000
        )

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        dev_name = self._get_device_name(device)
        self._notify(
            f"󰂯 Pair Device: {dev_name}",
            f"PIN Code: {pincode}",
            urgency="critical",
            timeout=30000
        )

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        dev_name = self._get_device_name(device)
        passkey_str = f"{passkey:06d}"
        allowed = self._prompt_user(
            f"󰂯 Bluetooth Pairing Request",
            f"Pair with '{dev_name}'?\nConfirm passkey matches on device: {passkey_str}"
        )
        if not allowed:
            raise dbus.exceptions.DBusException("Pairing rejected by user", name="org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        dev_name = self._get_device_name(device)
        if self._is_device_trusted(device):
            return
        allowed = self._prompt_user(
            f"󰂯 Authorize Device",
            f"Do you want to trust and connect device '{dev_name}'?"
        )
        if not allowed:
            raise dbus.exceptions.DBusException("Authorization rejected by user", name="org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Cancel(self):
        pass


def run_agent():
    # Ensure single instance
    lock_file = "/tmp/hypr_bt_agent.lock"
    try:
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        # Already running
        sys.exit(0)

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    agent = BluetoothAgent(bus, AGENT_PATH)

    try:
        manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")
        try:
            manager.UnregisterAgent(AGENT_PATH)
        except Exception:
            pass
        manager.RegisterAgent(AGENT_PATH, CAPABILITY)
        manager.RequestDefaultAgent(AGENT_PATH)
    except Exception as e:
        sys.stderr.write(f"Failed to register BlueZ agent: {e}\n")
        sys.exit(1)

    loop = GLib.MainLoop()

    def signal_handler(signum, frame):
        try:
            manager.UnregisterAgent(AGENT_PATH)
        except Exception:
            pass
        loop.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run()
    except Exception:
        pass


if __name__ == "__main__":
    run_agent()
