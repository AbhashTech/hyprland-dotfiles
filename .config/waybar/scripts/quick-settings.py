#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha Glassmorphic Quick Settings / Control Center Menu
 Integrated Wofi popup for Waybar & Hyprland
=============================================================================
"""

import os
import re
import subprocess
import sys


def run_cmd(cmd, check=False):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""


def run_dmenu(prompt, options, width=38, lines=10):
    import shutil
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", f" {prompt}: ", "--width", str(width), "--lines", str(lines)]
    else:
        cmd = [
            "wofi", "--dmenu",
            "--prompt", prompt,
            "--width", "480",
            "--height", "420",
            "--cache-file", "/dev/null",
            "--hide-scroll",
            "--allow-markup",
            "--insensitive"
        ]
    try:
        proc = subprocess.run(cmd, input="\n".join(options), text=True, capture_output=True)
        return proc.stdout.strip()
    except Exception:
        return ""


def notify(title, msg, icon="preferences-system"):
    run_cmd([
        "notify-send",
        "-r", "9910",
        "-t", "2500",
        "-u", "low",
        "-a", "Control Center",
        "-i", icon,
        "-h", "string:x-canonical-private-synchronous:quick_settings",
        title,
        msg
    ])


def get_volume():
    out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    if not out:
        return "Unknown", False
    # Format: "Volume: 0.65 [MUTED]" or "Volume: 0.65"
    is_muted = "[MUTED]" in out
    vol_match = re.search(r'([0-9\.]+)', out)
    if vol_match:
        pct = int(float(vol_match.group(1)) * 100)
        return f"{pct}%", is_muted
    return "Unknown", is_muted


def get_brightness():
    try:
        curr = run_cmd(["brightnessctl", "get"])
        max_b = run_cmd(["brightnessctl", "max"])
        if curr and max_b and int(max_b) > 0:
            pct = int((int(curr) / int(max_b)) * 100)
            return f"{pct}%"
    except Exception:
        pass
    return "N/A"


def get_network_info():
    # Check wifi SSID
    out = run_cmd(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"])
    for line in out.splitlines():
        if line.startswith("yes:"):
            parts = line.split(":")
            ssid = parts[1] if len(parts) > 1 else "Connected"
            sig = parts[2] if len(parts) > 2 else "100"
            return f"{ssid} ({sig}%)"
    
    # Check default route
    ip_route = run_cmd(["ip", "route", "show", "default"])
    if "dev" in ip_route:
        return "Connected (Ethernet/LAN)"
    return "Offline / Disconnected"


def get_bluetooth_info():
    rf = run_cmd(["rfkill", "list", "bluetooth"])
    if "Soft blocked: yes" in rf or "Hard blocked: yes" in rf:
        return "Off (Disabled)"
    
    # Check connected device
    out = run_cmd(["bluetoothctl", "info"])
    if "Name:" in out:
        match = re.search(r'Name:\s+(.*)', out)
        if match:
            return f"Connected: {match.group(1).strip()}"
    return "On (Ready)"


def get_system_stats():
    # Memory
    mem_used = "N/A"
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_total = 0
        mem_avail = 0
        for l in lines:
            if l.startswith("MemTotal:"):
                mem_total = int(l.split()[1])
            elif l.startswith("MemAvailable:"):
                mem_avail = int(l.split()[1])
        if mem_total > 0:
            pct = int(((mem_total - mem_avail) / mem_total) * 100)
            mem_used = f"{pct}%"
    except Exception:
        pass

    # Disk
    disk_used = "N/A"
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        avail = st.f_bavail * st.f_frsize
        if total > 0:
            pct = int(((total - avail) / total) * 100)
            disk_used = f"{pct}%"
    except Exception:
        pass

    return mem_used, disk_used


def open_menu():
    vol_str, vol_muted = get_volume()
    vol_display = "Muted" if vol_muted else vol_str
    bright_str = get_brightness()
    net_str = get_network_info()
    bt_str = get_bluetooth_info()
    mem_str, disk_str = get_system_stats()

    options = [
        "─── 󰍜 QUICK CONTROLS ───",
        f"󰕾  Volume: {vol_display} (Toggle Mute / Options)",
        f"󰃠  Brightness: {bright_str} (Adjust / Presets)",
        f"󰤨  Wi-Fi / Network: {net_str}",
        f"󰂯  Bluetooth: {bt_str}",
        f"󰂚  Notifications & History (Click to View)",
        "󰅍  Clipboard History Manager",
        "─── 󰍛 SYSTEM & TOOLS ───",
        f"󰘚  System Monitor (RAM: {mem_str} | Disk: {disk_str} | Open BTop)",
        "🖥️  Screen Resolution & Scaling Manager",
        "󰞷  Open Kitty Terminal",
        "󰉋  Open Dolphin File Manager",
        "─── 󰐥 SESSION & POWER ───",
        "󰌾  Lock Screen",
        "󰒲  Suspend System",
        "󰍃  Logout Hyprland",
        "󰑐  Reboot Computer",
        "󰐥  Shutdown Power Off",
    ]

    chosen = run_dmenu("󰍜 Control Center", options, width=38, lines=12)
    if not chosen:
        return

    # Handle Selection
    if "Volume:" in chosen:
        volume_submenu()
    elif "Brightness:" in chosen:
        subprocess.Popen(["/home/kunal/.config/waybar/scripts/brightness-manager.py"])
    elif "Wi-Fi / Network:" in chosen:
        network_submenu()
    elif "Bluetooth:" in chosen:
        bluetooth_submenu()
    elif "Notifications" in chosen:
        subprocess.Popen(["/home/kunal/.config/waybar/scripts/notifications.py"])
    elif "Clipboard" in chosen:
        subprocess.Popen(["/home/kunal/.config/hypr/scripts/clipboard_manager.py", "--menu"])
    elif "System Monitor" in chosen:
        subprocess.Popen(["kitty", "--class=btop", "-e", "btop"])
    elif "Screen Resolution" in chosen:
        subprocess.Popen(["/home/kunal/.config/hypr/scripts/resolution_menu.py"])
    elif "Open Kitty Terminal" in chosen:
        subprocess.Popen(["kitty"])
    elif "Open Dolphin" in chosen:
        subprocess.Popen(["dolphin"])
    elif "Lock Screen" in chosen:
        if os.path.exists("/usr/bin/hyprlock"):
            subprocess.Popen(["hyprlock"])
        elif os.path.exists("/usr/bin/swaylock"):
            subprocess.Popen(["swaylock", "-f", "-c", "1e1e2e"])
    elif "Suspend System" in chosen:
        subprocess.Popen(["systemctl", "suspend"])
    elif "Logout Hyprland" in chosen:
        subprocess.Popen(["hyprctl", "dispatch", "exit", "0"])
    elif "Reboot Computer" in chosen:
        subprocess.Popen(["systemctl", "reboot"])
    elif "Shutdown Power Off" in chosen:
        subprocess.Popen(["systemctl", "poweroff"])


def volume_submenu():
    curr_vol, is_muted = get_volume()
    mute_label = "󰝟  Unmute Audio" if is_muted else "󰝟  Mute Audio"

    options = [
        f"─── VOLUME CONTROLS (Current: {curr_vol}) ───",
        mute_label,
        "󰕾  Volume 100% (Maximum)",
        "󰕾  Volume 75%",
        "󰕾  Volume 50%",
        "󰕾  Volume 25%",
        "󰕾  Volume 10% (Low)",
        "󰝝  Volume +5% (Step Up)",
        "󰝞  Volume -5% (Step Down)",
        "󰓃  Open Volume Mixer / Pavucontrol",
        "󰌍  « Back to Control Center",
    ]

    chosen = run_dmenu("󰕾 Audio Volume", options, width=34, lines=11)
    if not chosen or "Back to Control Center" in chosen:
        if "Back" in chosen:
            open_menu()
        return

    if "Mute Audio" in chosen or "Unmute Audio" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "mute"])
    elif "100%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "set", "100"])
    elif "75%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "set", "75"])
    elif "50%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "set", "50"])
    elif "25%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "set", "25"])
    elif "10%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "set", "10"])
    elif "+5%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "up", "5"])
    elif "-5%" in chosen:
        run_cmd(["python3", "/home/kunal/.config/hypr/scripts/volume_control.py", "down", "5"])
    elif "Volume Mixer" in chosen:
        if os.path.exists("/usr/bin/pavucontrol"):
            subprocess.Popen(["pavucontrol"])
        else:
            subprocess.Popen(["kitty", "--hold", "-e", "wpctl", "status"])


def brightness_submenu():
    curr_b = get_brightness()
    options = [
        f"─── DISPLAY BRIGHTNESS (Current: {curr_b}) ───",
        "󰃠  Brightness 100% (Full)",
        "󰃟  Brightness 75%",
        "󰃟  Brightness 50% (Standard)",
        "󰃞  Brightness 25% (Dim)",
        "󰃞  Brightness 10% (Low Light)",
        "󰃠  Brightness +10% (Increase)",
        "󰃞  Brightness -10% (Decrease)",
        "󰌍  « Back to Control Center",
    ]

    chosen = run_dmenu("󰃠 Screen Brightness", options, width=34, lines=9)
    if not chosen or "Back to Control Center" in chosen:
        if "Back" in chosen:
            open_menu()
        return


    if "100%" in chosen:
        run_cmd(["brightnessctl", "set", "100%"])
    elif "75%" in chosen:
        run_cmd(["brightnessctl", "set", "75%"])
    elif "50%" in chosen:
        run_cmd(["brightnessctl", "set", "50%"])
    elif "25%" in chosen:
        run_cmd(["brightnessctl", "set", "25%"])
    elif "10%" in chosen:
        run_cmd(["brightnessctl", "set", "10%"])
    elif "+10%" in chosen:
        run_cmd(["brightnessctl", "set", "10%+"])
    elif "-10%" in chosen:
        run_cmd(["brightnessctl", "set", "10%-"])


def network_submenu():
    subprocess.Popen(["kitty", "--class=netctl-floating", "-e", "/home/kunal/.config/waybar/scripts/netctl-tui.py"])


def bluetooth_submenu():
    subprocess.Popen(["/home/kunal/.config/waybar/scripts/bluetooth-menu.sh"])


if __name__ == "__main__":
    open_menu()
