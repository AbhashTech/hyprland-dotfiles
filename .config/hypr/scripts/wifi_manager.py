#!/usr/bin/env python3
"""
=============================================================================
Hyprland WiFi Network Manager (iwd / iwctl)
=============================================================================
Provides interactive iwctl terminal or menu for managing WiFi connections.
"""

import os
import sys
import shutil
import subprocess

def main():
    # If fuzzel or wofi is installed, try GUI menu, else launch interactive iwctl in kitty
    has_dmenu = shutil.which("fuzzel") or shutil.which("wofi")
    
    if not has_dmenu or "--terminal" in sys.argv:
        subprocess.Popen(["kitty", "--class", "iwctl-floating", "-T", "WiFi Network Manager (iwctl)", "-e", "iwctl"])
        return

    # If fuzzel/wofi is present, run interactive dmenu
    subprocess.Popen(["kitty", "--class", "iwctl-floating", "-T", "WiFi Network Manager (iwctl)", "-e", "iwctl"])

if __name__ == "__main__":
    main()
