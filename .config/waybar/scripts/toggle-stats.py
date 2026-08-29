#!/usr/bin/env python3
"""
=============================================================================
 Stats View Toggle Controller for Waybar
 Toggles right-side bar between Status Mode and Hardware Stats Mode
=============================================================================
"""

import json
import os
import subprocess
import sys

STATE_FILE = "/tmp/waybar_stats_mode"


def get_current_mode():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                mode = f.read().strip()
                if mode in ("status", "hardware"):
                    return mode
        except Exception:
            pass
    return "status"


def set_mode(mode):
    try:
        with open(STATE_FILE, "w") as f:
            f.write(mode)
    except Exception:
        pass


def send_waybar_signal():
    try:
        subprocess.run(["bash", "-c", "pgrep -x waybar >/dev/null && pkill -RTMIN+9 waybar || true"], capture_output=True)
    except Exception:
        pass


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--toggle":
        curr = get_current_mode()
        new_mode = "hardware" if curr == "status" else "status"
        set_mode(new_mode)
        send_waybar_signal()
        return

    # Default output for Waybar custom module
    mode = get_current_mode()
    output = {
        "text": "",
        "tooltip": "",
        "class": f"mode-{mode}"
    }
    print(json.dumps(output))


if __name__ == '__main__':
    main()
