#!/usr/bin/env python3
"""
=============================================================================
Hyprland Bluetooth Device Manager (bluetoothctl)
=============================================================================
Provides interactive bluetoothctl terminal or quick toggle.
"""

import os
import sys
import shutil
import subprocess

def main():
    if "--toggle" in sys.argv:
        try:
            res = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, check=False)
            powered = "Powered: yes" in res.stdout
            new_state = "off" if powered else "on"
            subprocess.run(["bluetoothctl", "power", new_state], check=False)
            msg = "Powered Off" if powered else "Powered On"
            subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth Power", f"Bluetooth is now {msg}"], check=False)
        except Exception:
            pass
        return

    subprocess.Popen(["kitty", "--class", "bt-floating", "-T", "Bluetooth Manager (bluetoothctl)", "-e", "bluetoothctl"])

if __name__ == "__main__":
    main()
