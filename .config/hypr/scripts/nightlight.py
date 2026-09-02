#!/usr/bin/env python3
"""
Hyprland Night Light / Blue Light Filter Utility
Unified wrapper delegating to sunset_idle_manager.py
"""

import sys
import subprocess
from pathlib import Path

MANAGER_SCRIPT = Path(__file__).parent / "sunset_idle_manager.py"


def main():
    if not MANAGER_SCRIPT.exists():
        print("sunset_idle_manager.py not found!", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    if not args or args[0] == "toggle":
        cmd = [sys.executable, str(MANAGER_SCRIPT), "--sunset-toggle"]
    elif args[0] in ["on", "start"]:
        temp = args[1] if len(args) > 1 else "3800"
        cmd = [sys.executable, str(MANAGER_SCRIPT), "--sunset-on", "--set-temp", temp]
    elif args[0] in ["off", "stop"]:
        cmd = [sys.executable, str(MANAGER_SCRIPT), "--sunset-off"]
    elif args[0] == "status":
        cmd = [sys.executable, str(MANAGER_SCRIPT), "--status"]
    elif args[0] in ["menu", "--menu"]:
        cmd = [sys.executable, str(MANAGER_SCRIPT), "--menu"]
    elif args[0] in ["gui", "--gui"]:
        cmd = [sys.executable, str(MANAGER_SCRIPT), "--gui"]
    else:
        cmd = [sys.executable, str(MANAGER_SCRIPT)] + args

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
