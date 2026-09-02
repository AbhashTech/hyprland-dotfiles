#!/usr/bin/env python3
"""
=============================================================================
Hyprsunset & Hypridle Manager (Display Power & Night Light Control Suite)
=============================================================================
A comprehensive graphical and CLI management utility for Hyprland:
  - Hyprsunset / Blue Light Filter: Dynamic color temperature (1000K-6500K),
    instant presets (Daylight, Soft, Night, Candle, Ember), toggle & persistence.
  - Hypridle & DPMS: Configurable idle timeouts (Monitor Turn Off / DPMS, Screen
    Lock, Screen Dimming, System Suspend), instant "Turn Off Displays Now",
    and Caffeine mode (Inhibit Idle/Sleep).
  - Interfaces: Modern Catppuccin GTK3 GUI, Fast Fuzzel / Wofi Dmenu, and CLI flags.
=============================================================================
"""

import os
import sys
import re
import json
import time
import signal
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".config" / "hypr"
HYPRIDLE_CONF = CONFIG_DIR / "hypridle.conf"
STATE_DIR = Path.home() / ".cache"
STATE_FILE = STATE_DIR / "sunset_idle_state.json"
NIGHTLIGHT_PID_FILE = Path("/tmp/hypr_nightlight.pid")
NIGHTLIGHT_STATE_FILE = Path("/tmp/hypr_nightlight.state")
CAFFEINE_PID_FILE = Path("/tmp/hypr_caffeine.pid")
APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"

DEFAULT_WARM_TEMP = 3800
DEFAULT_DAY_TEMP = 6500

TEMP_PRESETS = [
    ("6500", "☀️ Daylight (6500K - Normal)", "Display color temperature set to normal daylight."),
    ("5000", "🍵 Soft Warm (5000K - Relax)", "Comfortable light warm filter for late afternoon."),
    ("3800", "🌙 Night Light (3800K - Warm)", "Balanced blue-light filter for evening work."),
    ("2500", "🕯️ Candlelight (2500K - Relaxed)", "Deep amber tint to promote sleepiness."),
    ("1800", "🔴 Deep Ember (1800K - Sleep)", "Maximum red tint for pitch-dark environments.")
]

DPMS_TIMEOUT_PRESETS = [
    (60, "1 Minute"),
    (120, "2 Minutes"),
    (150, "2.5 Minutes"),
    (300, "5 Minutes"),
    (330, "5.5 Minutes (Default)"),
    (600, "10 Minutes"),
    (900, "15 Minutes"),
    (1800, "30 Minutes"),
    (3600, "1 Hour"),
    (0, "Disabled (Never Turn Off)")
]

LOCK_TIMEOUT_PRESETS = [
    (120, "2 Minutes"),
    (300, "5 Minutes (Default)"),
    (600, "10 Minutes"),
    (900, "15 Minutes"),
    (1800, "30 Minutes"),
    (0, "Disabled (Never Lock)")
]

DIM_TIMEOUT_PRESETS = [
    (60, "1 Minute"),
    (120, "2 Minutes"),
    (150, "2.5 Minutes (Default)"),
    (300, "5 Minutes"),
    (0, "Disabled (Never Dim)")
]

SUSPEND_TIMEOUT_PRESETS = [
    (900, "15 Minutes"),
    (1800, "30 Minutes (Default)"),
    (3600, "1 Hour"),
    (7200, "2 Hours"),
    (0, "Disabled (Never Suspend)")
]


# =============================================================================
# Helper Utilities & Notifications
# =============================================================================

def notify(title, body, icon="preferences-desktop-display", urgency="low"):
    """Send standard desktop notification."""
    if not shutil.which("notify-send"):
        return
    subprocess.Popen([
        "notify-send",
        "-a", "Sunset & Idle Manager",
        "-i", icon,
        "-u", urgency,
        "-t", "2500",
        title, body
    ])


def load_state():
    """Load persistent state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "sunset_enabled": False,
        "sunset_temp": DEFAULT_WARM_TEMP,
        "caffeine_enabled": False,
        "dpms_timeout": 330,
        "lock_timeout": 300,
        "dim_timeout": 150,
        "suspend_timeout": 1800
    }


def save_state(state):
    """Save persistent state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def get_active_theme_colors():
    """Load colors from active theme JSON file with fallback."""
    cache_state = Path.home() / ".cache" / "hypr_theme_state.json"
    current_txt = Path.home() / ".cache" / "current_theme"
    theme_id = "catppuccin-mocha"

    if cache_state.exists():
        try:
            with open(cache_state, "r") as f:
                theme_id = json.load(f).get("current_theme", theme_id)
        except Exception:
            pass
    elif current_txt.exists():
        try:
            theme_id = current_txt.read_text().strip() or theme_id
        except Exception:
            pass

    theme_file = Path.home() / ".config" / "theme" / f"{theme_id}.json"
    if theme_file.exists():
        try:
            with open(theme_file, "r") as f:
                return json.load(f).get("colors", {})
        except Exception:
            pass

    # Default Catppuccin Mocha colors
    return {
        "base": "#1e1e2e",
        "mantle": "#181825",
        "crust": "#11111b",
        "text": "#cdd6f4",
        "subtext0": "#a6adc8",
        "subtext1": "#bac2de",
        "surface0": "#313244",
        "surface1": "#45475a",
        "surface2": "#585b70",
        "overlay0": "#6c7086",
        "accent": "#cba6f7",
        "mauve": "#cba6f7",
        "blue": "#89b4fa",
        "sapphire": "#74c7ec",
        "sky": "#89dceb",
        "teal": "#94e2d5",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "peach": "#fab387",
        "maroon": "#eba0ac",
        "red": "#f38ba8",
        "pink": "#f5c2e7",
        "flamingo": "#f2cdcd",
        "rosewater": "#f5e0dc"
    }


# =============================================================================
# Hyprsunset & Night Light Controller
# =============================================================================

class SunsetController:
    @staticmethod
    def get_pid():
        """Get running PID of hyprsunset or wlsunset."""
        if NIGHTLIGHT_PID_FILE.exists():
            try:
                pid = int(NIGHTLIGHT_PID_FILE.read_text().strip())
                os.kill(pid, 0)
                return pid
            except Exception:
                NIGHTLIGHT_PID_FILE.unlink(missing_ok=True)
                NIGHTLIGHT_STATE_FILE.unlink(missing_ok=True)

        # Look for running process by name
        for binary in ["hyprsunset", "wlsunset"]:
            try:
                res = subprocess.run(["pgrep", "-x", binary], capture_output=True, text=True)
                if res.stdout.strip():
                    pids = res.stdout.strip().split()
                    if pids:
                        pid = int(pids[0])
                        NIGHTLIGHT_PID_FILE.write_text(str(pid))
                        return pid
            except Exception:
                pass
        return None

    @staticmethod
    def is_active():
        return SunsetController.get_pid() is not None

    @staticmethod
    def get_current_temp():
        if NIGHTLIGHT_STATE_FILE.exists():
            try:
                return int(NIGHTLIGHT_STATE_FILE.read_text().strip())
            except Exception:
                pass
        state = load_state()
        return state.get("sunset_temp", DEFAULT_WARM_TEMP)

    @staticmethod
    def stop(silent=False):
        pid = SunsetController.get_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        NIGHTLIGHT_PID_FILE.unlink(missing_ok=True)
        NIGHTLIGHT_STATE_FILE.unlink(missing_ok=True)

        # Cleanup stray processes
        subprocess.run(["pkill", "-x", "hyprsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-x", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        state = load_state()
        state["sunset_enabled"] = False
        save_state(state)

        if not silent:
            notify("☀️ Night Light Disabled", "Display color temperature restored to daylight (6500K).", "weather-clear")

    @staticmethod
    def start(temp=None, silent=False):
        if temp is None:
            temp = SunsetController.get_current_temp()
        temp = int(temp)

        SunsetController.stop(silent=True)

        binary = shutil.which("hyprsunset") or shutil.which("wlsunset")
        if not binary:
            notify("❌ Error", "Neither hyprsunset nor wlsunset is installed.\nRun: sudo pacman -S hyprsunset", "dialog-error", urgency="critical")
            return False

        if "hyprsunset" in binary:
            cmd = [binary, "-t", str(temp)]
        else:
            cmd = [binary, "-t", str(temp), "-T", "6500"]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            NIGHTLIGHT_PID_FILE.write_text(str(proc.pid))
            NIGHTLIGHT_STATE_FILE.write_text(str(temp))

            state = load_state()
            state["sunset_enabled"] = True
            state["sunset_temp"] = temp
            save_state(state)

            if not silent:
                notify("🌙 Night Light Active", f"Warm color temperature set to <b>{temp}K</b>.", "weather-clear-night")
            return True
        except Exception as e:
            notify("❌ Error", f"Failed to start night light daemon: {e}", "dialog-error")
            return False

    @staticmethod
    def toggle():
        if SunsetController.is_active():
            SunsetController.stop()
        else:
            state = load_state()
            SunsetController.start(state.get("sunset_temp", DEFAULT_WARM_TEMP))

    @staticmethod
    def set_temperature(temp, silent=False):
        temp = int(temp)
        state = load_state()
        state["sunset_temp"] = temp
        save_state(state)
        # If currently active, apply immediately
        if SunsetController.is_active() or state.get("sunset_enabled", False):
            SunsetController.start(temp, silent=silent)
        elif not silent:
            notify("⚙️ Night Light Preset Updated", f"Target temperature set to <b>{temp}K</b> (Currently Disabled).", "preferences-desktop-display")


# =============================================================================
# Hypridle & DPMS Monitor Controller
# =============================================================================

class IdleController:
    @staticmethod
    def is_running():
        try:
            res = subprocess.run(["pgrep", "-x", "hypridle"], capture_output=True, text=True)
            return bool(res.stdout.strip())
        except Exception:
            return False

    @staticmethod
    def restart_daemon():
        """Restart hypridle to apply new configuration."""
        subprocess.run(["pkill", "-x", "hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.1)
        try:
            subprocess.Popen(["hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    @staticmethod
    def parse_config():
        """Parse current hypridle.conf listener timeouts."""
        config_data = {
            "dim_timeout": 150,
            "lock_timeout": 300,
            "dpms_timeout": 330,
            "suspend_timeout": 1800,
            "ignore_dbus_inhibit": False
        }

        if not HYPRIDLE_CONF.exists():
            return config_data

        try:
            content = HYPRIDLE_CONF.read_text()
            # Parse listener blocks
            # Look for brightnessctl set (dim)
            dim_match = re.search(r'listener\s*\{[^}]*timeout\s*=\s*(\d+)[^}]*brightnessctl', content, re.DOTALL)
            if dim_match:
                config_data["dim_timeout"] = int(dim_match.group(1))

            # Look for lock-session (lock)
            lock_match = re.search(r'listener\s*\{[^}]*timeout\s*=\s*(\d+)[^}]*lock-session', content, re.DOTALL)
            if lock_match:
                config_data["lock_timeout"] = int(lock_match.group(1))

            # Look for dpms off (monitor off)
            dpms_match = re.search(r'listener\s*\{[^}]*timeout\s*=\s*(\d+)[^}]*dpms\s+off', content, re.DOTALL)
            if dpms_match:
                config_data["dpms_timeout"] = int(dpms_match.group(1))

            # Look for suspend
            suspend_match = re.search(r'listener\s*\{[^}]*timeout\s*=\s*(\d+)[^}]*systemctl\s+suspend', content, re.DOTALL)
            if suspend_match:
                config_data["suspend_timeout"] = int(suspend_match.group(1))

            if "ignore_dbus_inhibit = true" in content:
                config_data["ignore_dbus_inhibit"] = True
        except Exception as e:
            print(f"Error parsing hypridle.conf: {e}", file=sys.stderr)

        return config_data

    @staticmethod
    def generate_config(dim_timeout=150, lock_timeout=300, dpms_timeout=330, suspend_timeout=1800, ignore_dbus_inhibit=False):
        """Generate standardized hypridle.conf content."""
        lines = [
            "# =============================================================================",
            "# Hypridle Configuration - Hyprland Idle Daemon",
            "# (Managed by Sunset & Idle Control Suite)",
            "# =============================================================================",
            "",
            "general {",
            "    lock_cmd = pidof hyprlock || hyprlock       # Command to run on dbus lock-session",
            "    before_sleep_cmd = loginctl lock-session    # Lock before suspend",
            "    after_sleep_cmd = hyprctl dispatch dpms on  # Turn display back on after resume",
            f"    ignore_dbus_inhibit = {'true' if ignore_dbus_inhibit else 'false'}                 # Respect media players inhibiting idle",
            "}",
            ""
        ]

        # 1. Dim screen
        if dim_timeout and dim_timeout > 0:
            lines.extend([
                f"# 1. Dim screen brightness after {dim_timeout}s ({dim_timeout//60}m {dim_timeout%60}s)",
                "listener {",
                f"    timeout = {dim_timeout}",
                "    on-timeout = brightnessctl -s set 10%",
                "    on-resume = brightnessctl -r",
                "}",
                ""
            ])

        # 2. Lock screen
        if lock_timeout and lock_timeout > 0:
            lines.extend([
                f"# 2. Lock screen after {lock_timeout}s ({lock_timeout//60}m {lock_timeout%60}s)",
                "listener {",
                f"    timeout = {lock_timeout}",
                "    on-timeout = loginctl lock-session",
                "}",
                ""
            ])

        # 3. Turn off monitor (DPMS off)
        if dpms_timeout and dpms_timeout > 0:
            lines.extend([
                f"# 3. Turn off displays (DPMS) after {dpms_timeout}s ({dpms_timeout//60}m {dpms_timeout%60}s)",
                "listener {",
                f"    timeout = {dpms_timeout}",
                "    on-timeout = hyprctl dispatch dpms off",
                "    on-resume = hyprctl dispatch dpms on",
                "}",
                ""
            ])

        # 4. Suspend
        if suspend_timeout and suspend_timeout > 0:
            lines.extend([
                f"# 4. Suspend system after {suspend_timeout}s ({suspend_timeout//60}m {suspend_timeout%60}s)",
                "listener {",
                f"    timeout = {suspend_timeout}",
                "    on-timeout = systemctl suspend",
                "}",
                ""
            ])

        return "\n".join(lines)

    @staticmethod
    def apply_config(dim_timeout=None, lock_timeout=None, dpms_timeout=None, suspend_timeout=None, silent=False):
        """Write new configuration to hypridle.conf and restart daemon."""
        current = IdleController.parse_config()
        if dim_timeout is not None:
            current["dim_timeout"] = int(dim_timeout)
        if lock_timeout is not None:
            current["lock_timeout"] = int(lock_timeout)
        if dpms_timeout is not None:
            current["dpms_timeout"] = int(dpms_timeout)
        if suspend_timeout is not None:
            current["suspend_timeout"] = int(suspend_timeout)

        content = IdleController.generate_config(
            dim_timeout=current["dim_timeout"],
            lock_timeout=current["lock_timeout"],
            dpms_timeout=current["dpms_timeout"],
            suspend_timeout=current["suspend_timeout"]
        )

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            HYPRIDLE_CONF.write_text(content)
            IdleController.restart_daemon()

            state = load_state()
            state.update(current)
            save_state(state)

            if not silent:
                dpms_desc = f"{current['dpms_timeout']}s" if current['dpms_timeout'] > 0 else "Disabled"
                notify("💤 Hypridle Configured", f"Monitor Turn-off: <b>{dpms_desc}</b>\nLock: <b>{current['lock_timeout']}s</b> | Suspend: <b>{current['suspend_timeout']}s</b>", "preferences-desktop-display")
            return True
        except Exception as e:
            notify("❌ Error", f"Failed to update hypridle.conf: {e}", "dialog-error")
            return False

    # Immediate actions
    @staticmethod
    def turn_off_monitors():
        """Immediately turn off monitor via DPMS."""
        subprocess.run(["hyprctl", "dispatch", "dpms", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def turn_on_monitors():
        """Turn on monitors via DPMS."""
        subprocess.run(["hyprctl", "dispatch", "dpms", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def toggle_monitors():
        """Toggle monitor power state via DPMS."""
        subprocess.run(["hyprctl", "dispatch", "dpms", "toggle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def lock_screen():
        """Immediately lock screen."""
        subprocess.run(["loginctl", "lock-session"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Caffeine / Inhibit Idle Mode
    @staticmethod
    def is_caffeine_active():
        if CAFFEINE_PID_FILE.exists():
            try:
                pid = int(CAFFEINE_PID_FILE.read_text().strip())
                os.kill(pid, 0)
                return True
            except Exception:
                CAFFEINE_PID_FILE.unlink(missing_ok=True)
        return False

    @staticmethod
    def toggle_caffeine():
        if IdleController.is_caffeine_active():
            # Disable caffeine
            try:
                pid = int(CAFFEINE_PID_FILE.read_text().strip())
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            CAFFEINE_PID_FILE.unlink(missing_ok=True)
            # Restart hypridle
            IdleController.restart_daemon()
            state = load_state()
            state["caffeine_enabled"] = False
            save_state(state)
            notify("☕ Caffeine Mode Disabled", "Screen idle timeouts and auto-lock restored.", "preferences-desktop-screensaver")
        else:
            # Enable caffeine: stop hypridle or run systemd-inhibit
            subprocess.run(["pkill", "-x", "hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Spawn a lightweight sleep inhibitor in background
            try:
                proc = subprocess.Popen(
                    ["systemd-inhibit", "--what=idle:sleep", "--who=SunsetIdleManager", "--why=Caffeine Mode", "sleep", "infinity"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                CAFFEINE_PID_FILE.write_text(str(proc.pid))
            except Exception:
                # Fallback: create PID file for dummy
                CAFFEINE_PID_FILE.write_text(str(os.getpid()))

            state = load_state()
            state["caffeine_enabled"] = True
            save_state(state)
            notify("☕ Caffeine Mode Active", "Screen will NOT turn off or lock while active.", "caffeine")


# =============================================================================
# Interactive Fuzzel / Wofi Menu
# =============================================================================

def show_menu():
    """Launch keyboard-driven interactive Fuzzel/Wofi selection menu."""
    launcher = shutil.which("fuzzel") or shutil.which("wofi")
    if not launcher:
        # Fallback to GUI
        show_gui()
        return

    sunset_active = SunsetController.is_active()
    current_temp = SunsetController.get_current_temp()
    caffeine_active = IdleController.is_caffeine_active()
    idle_config = IdleController.parse_config()
    dpms_time = idle_config.get("dpms_timeout", 330)
    dpms_label = f"{dpms_time//60}m {dpms_time%60}s" if dpms_time > 0 else "Never (Disabled)"

    menu_items = [
        f"🌙 Toggle Night Light ({'ON' if sunset_active else 'OFF'} • {current_temp}K)",
        f"🌡️  Set Night Light Temperature...",
        f"⏱️  Set Monitor Turn-Off Timeout (Currently: {dpms_label})...",
        f"🔒 Set Screen Lock Timeout (Currently: {idle_config.get('lock_timeout', 300)}s)...",
        f"🖥️  Turn Off Displays Now (DPMS Off)",
        f"☕ Toggle Caffeine Mode ({'ACTIVE' if caffeine_active else 'OFF'})",
        f"🔒 Lock Screen Immediately",
        f"🔄 Restart Hypridle Daemon",
        f"⚙️  Open Full Graphical Control Center (GUI)"
    ]

    choice = prompt_menu(launcher, menu_items, "Display Power & Night Light")
    if not choice:
        return

    if "Toggle Night Light" in choice:
        SunsetController.toggle()
    elif "Set Night Light Temperature" in choice:
        temp_items = [f"{temp}K • {label}" for temp, label, _ in TEMP_PRESETS]
        temp_items.append("Custom Temperature...")
        t_choice = prompt_menu(launcher, temp_items, "Select Color Temperature")
        if t_choice:
            if "Custom" in t_choice:
                custom_t = prompt_input(launcher, "Enter temperature in Kelvin (1000 - 6500):", "3800")
                if custom_t and custom_t.isdigit():
                    SunsetController.set_temperature(int(custom_t))
            else:
                k_val = t_choice.split("K")[0].strip()
                if k_val.isdigit():
                    SunsetController.set_temperature(int(k_val))
    elif "Set Monitor Turn-Off Timeout" in choice:
        dpms_items = [f"{label} ({sec}s)" if sec > 0 else label for sec, label in DPMS_TIMEOUT_PRESETS]
        dpms_items.append("Custom Timeout in Seconds...")
        d_choice = prompt_menu(launcher, dpms_items, "Turn Off Monitor After")
        if d_choice:
            if "Custom" in d_choice:
                custom_s = prompt_input(launcher, "Enter idle timeout in seconds (0 to disable):", "300")
                if custom_s and custom_s.isdigit():
                    IdleController.apply_config(dpms_timeout=int(custom_s))
            else:
                for sec, label in DPMS_TIMEOUT_PRESETS:
                    if label in d_choice:
                        IdleController.apply_config(dpms_timeout=sec)
                        break
    elif "Set Screen Lock Timeout" in choice:
        lock_items = [f"{label} ({sec}s)" if sec > 0 else label for sec, label in LOCK_TIMEOUT_PRESETS]
        l_choice = prompt_menu(launcher, lock_items, "Lock Screen After")
        if l_choice:
            for sec, label in LOCK_TIMEOUT_PRESETS:
                if label in l_choice:
                    IdleController.apply_config(lock_timeout=sec)
                    break
    elif "Turn Off Displays Now" in choice:
        IdleController.turn_off_monitors()
    elif "Toggle Caffeine Mode" in choice:
        IdleController.toggle_caffeine()
    elif "Lock Screen Immediately" in choice:
        IdleController.lock_screen()
    elif "Restart Hypridle" in choice:
        IdleController.restart_daemon()
        notify("🔄 Hypridle Restarted", "Hyprland idle daemon reloaded successfully.", "system-run")
    elif "Open Full Graphical Control Center" in choice:
        show_gui()


def prompt_menu(launcher, items, prompt="Select"):
    """Run fuzzel or wofi with list of items."""
    input_str = "\n".join(items)
    if "fuzzel" in launcher:
        cmd = ["fuzzel", "--dmenu", "--prompt", f"{prompt} > ", "-l", str(min(15, len(items) + 1)), "-w", "50"]
    else:
        cmd = ["wofi", "--dmenu", "--prompt", prompt, "-L", str(min(15, len(items) + 1)), "-W", "500"]

    try:
        res = subprocess.run(cmd, input=input_str, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return None


def prompt_input(launcher, prompt_text, default=""):
    """Prompt for a single line text input."""
    if "fuzzel" in launcher:
        cmd = ["fuzzel", "--dmenu", "--prompt", f"{prompt_text} > ", "-l", "0", "-w", "45"]
    else:
        cmd = ["wofi", "--dmenu", "--prompt", prompt_text, "-L", "1", "-W", "450"]

    try:
        res = subprocess.run(cmd, input=default, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return None


# =============================================================================
# Modern GTK3 Graphical Interface
# =============================================================================

def show_gui():
    """Launch full GTK3 Control Center GUI."""
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Gdk, GLib
    except Exception as e:
        print(f"GTK3/PyGObject unavailable: {e}. Falling back to menu mode.", file=sys.stderr)
        show_menu()
        return

    colors = get_active_theme_colors()

    # Create GTK Window
    win = Gtk.Window(title="Night Light & Display Idle Manager")
    win.set_default_size(580, 680)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_border_width(18)

    # Apply CSS styling
    css = f"""
    window {{
        background-color: {colors.get('base', '#1e1e2e')};
        color: {colors.get('text', '#cdd6f4')};
        font-family: 'JetBrains Mono Nerd Font', 'Noto Sans', sans-serif;
    }}
    .header-box {{
        background-color: {colors.get('mantle', '#181825')};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        border: 1px solid {colors.get('surface0', '#313244')};
    }}
    .card-box {{
        background-color: {colors.get('mantle', '#181825')};
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        border: 1px solid {colors.get('surface0', '#313244')};
    }}
    .title-label {{
        font-size: 16pt;
        font-weight: bold;
        color: {colors.get('mauve', '#cba6f7')};
    }}
    .subtitle-label {{
        font-size: 9.5pt;
        color: {colors.get('subtext0', '#a6adc8')};
    }}
    .section-title {{
        font-size: 11pt;
        font-weight: bold;
        color: {colors.get('blue', '#89b4fa')};
    }}
    .preset-btn {{
        background-color: {colors.get('surface0', '#313244')};
        color: {colors.get('text', '#cdd6f4')};
        border-radius: 8px;
        border: 1px solid {colors.get('surface1', '#45475a')};
        padding: 6px 12px;
        font-size: 9pt;
    }}
    .preset-btn:hover {{
        background-color: {colors.get('surface1', '#45475a')};
        border-color: {colors.get('mauve', '#cba6f7')};
    }}
    .action-btn {{
        background-color: {colors.get('surface0', '#313244')};
        color: {colors.get('text', '#cdd6f4')};
        border-radius: 8px;
        border: 1px solid {colors.get('surface1', '#45475a')};
        padding: 8px 16px;
        font-weight: bold;
    }}
    .action-btn:hover {{
        background-color: {colors.get('surface1', '#45475a')};
    }}
    .primary-btn {{
        background-color: {colors.get('mauve', '#cba6f7')};
        color: {colors.get('crust', '#11111b')};
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 16px;
        border: none;
    }}
    .primary-btn:hover {{
        background-color: {colors.get('pink', '#f5c2e7')};
    }}
    .danger-btn {{
        background-color: {colors.get('red', '#f38ba8')};
        color: {colors.get('crust', '#11111b')};
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 14px;
        border: none;
    }}
    .caffeine-active {{
        background-color: {colors.get('peach', '#fab387')};
        color: {colors.get('crust', '#11111b')};
        font-weight: bold;
    }}
    scale trough {{
        background-color: {colors.get('surface0', '#313244')};
        border-radius: 6px;
        min-height: 8px;
    }}
    scale highlight {{
        background-color: {colors.get('mauve', '#cba6f7')};
        border-radius: 6px;
    }}
    scale slider {{
        background-color: {colors.get('rosewater', '#f5e0dc')};
        min-width: 18px;
        min-height: 18px;
        border-radius: 50%;
    }}
    combobox button {{
        background-color: {colors.get('surface0', '#313244')};
        color: {colors.get('text', '#cdd6f4')};
        border-radius: 8px;
        border: 1px solid {colors.get('surface1', '#45475a')};
        padding: 4px 8px;
    }}
    """
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(css.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    win.add(main_vbox)

    # 1. Header Box
    header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    header.get_style_context().add_class("header-box")

    header_icon = Gtk.Label()
    header_icon.set_markup(f"<span font='24' color='{colors.get('mauve', '#cba6f7')}'>🌅</span>")
    header.pack_start(header_icon, False, False, 4)

    title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    title_lbl = Gtk.Label(xalign=0)
    title_lbl.set_markup(f"<span font='14' weight='bold' color='{colors.get('mauve', '#cba6f7')}'>Display Power &amp; Night Light Control</span>")
    sub_lbl = Gtk.Label(xalign=0)
    sub_lbl.set_markup(f"<span color='{colors.get('subtext0', '#a6adc8')}'>Unified manager for Hyprsunset &amp; Hypridle idle timeouts</span>")
    title_vbox.pack_start(title_lbl, False, False, 0)
    title_vbox.pack_start(sub_lbl, False, False, 0)
    header.pack_start(title_vbox, True, True, 4)

    main_vbox.pack_start(header, False, False, 0)

    # Scrolled container for settings
    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    main_vbox.pack_start(scroller, True, True, 0)

    content_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    scroller.add(content_vbox)

    # =========================================================================
    # SECTION 1: Hyprsunset (Night Light)
    # =========================================================================
    sunset_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    sunset_card.get_style_context().add_class("card-box")

    sunset_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    sunset_title = Gtk.Label(xalign=0)
    sunset_title.set_markup(f"<span font='11' weight='bold' color='{colors.get('peach', '#fab387')}'>🌙 Night Light (Hyprsunset)</span>")
    sunset_hdr.pack_start(sunset_title, True, True, 0)

    sunset_switch = Gtk.Switch()
    sunset_switch.set_active(SunsetController.is_active())
    sunset_switch.set_valign(Gtk.Align.CENTER)
    sunset_hdr.pack_end(sunset_switch, False, False, 0)
    sunset_card.pack_start(sunset_hdr, False, False, 0)

    # Temperature Slider
    slider_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    slider_lbl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    slider_desc = Gtk.Label(label="Color Temperature:", xalign=0)
    slider_val_lbl = Gtk.Label(xalign=1)
    current_t = SunsetController.get_current_temp()
    slider_val_lbl.set_markup(f"<b>{current_t}K</b>")
    slider_lbl_box.pack_start(slider_desc, True, True, 0)
    slider_lbl_box.pack_end(slider_val_lbl, False, False, 0)
    slider_box.pack_start(slider_lbl_box, False, False, 0)

    temp_adj = Gtk.Adjustment(value=current_t, lower=1000, upper=6500, step_increment=100, page_increment=500)
    temp_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=temp_adj)
    temp_scale.set_digits(0)
    temp_scale.set_draw_value(False)
    slider_box.pack_start(temp_scale, False, False, 0)
    sunset_card.pack_start(slider_box, False, False, 0)

    # Presets Flow Box / Button Row
    presets_lbl = Gtk.Label(label="Quick Temperature Presets:", xalign=0)
    sunset_card.pack_start(presets_lbl, False, False, 0)

    presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    for p_temp, p_label, _ in TEMP_PRESETS:
        btn = Gtk.Button(label=p_label.split("(")[0].strip())
        btn.get_style_context().add_class("preset-btn")
        btn.set_tooltip_text(f"{p_temp}K: {p_label}")

        def on_preset_click(b, t=int(p_temp)):
            temp_scale.set_value(t)
            slider_val_lbl.set_markup(f"<b>{t}K</b>")
            if sunset_switch.get_active():
                SunsetController.start(t, silent=True)
            else:
                SunsetController.set_temperature(t, silent=True)

        btn.connect("clicked", on_preset_click)
        presets_box.pack_start(btn, True, True, 0)
    sunset_card.pack_start(presets_box, False, False, 0)

    content_vbox.pack_start(sunset_card, False, False, 0)

    # =========================================================================
    # SECTION 2: Hypridle & Monitor Turn Off Controls
    # =========================================================================
    idle_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    idle_card.get_style_context().add_class("card-box")

    idle_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    idle_title = Gtk.Label(xalign=0)
    idle_title.set_markup(f"<span font='11' weight='bold' color='{colors.get('blue', '#89b4fa')}'>💤 Display Power &amp; Idle (Hypridle)</span>")
    idle_hdr.pack_start(idle_title, True, True, 0)

    # Caffeine Toggle Button
    caffeine_btn = Gtk.Button(label="☕ Caffeine: OFF")
    if IdleController.is_caffeine_active():
        caffeine_btn.set_label("☕ Caffeine: ACTIVE")
        caffeine_btn.get_style_context().add_class("caffeine-active")
    else:
        caffeine_btn.get_style_context().add_class("action-btn")
    idle_hdr.pack_end(caffeine_btn, False, False, 0)
    idle_card.pack_start(idle_hdr, False, False, 0)

    # Current config
    parsed_config = IdleController.parse_config()

    # Helper function to create dropdown settings row
    def create_timeout_row(title_text, desc_text, presets_list, current_val):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        r_title = Gtk.Label(xalign=0)
        r_title.set_markup(f"<b>{title_text}</b>")
        r_desc = Gtk.Label(xalign=0)
        r_desc.set_markup(f"<span size='small' color='{colors.get('subtext0', '#a6adc8')}'>{desc_text}</span>")
        lbl_box.pack_start(r_title, False, False, 0)
        lbl_box.pack_start(r_desc, False, False, 0)
        row.pack_start(lbl_box, True, True, 0)

        combo = Gtk.ComboBoxText()
        active_idx = 0
        match_found = False
        for idx, (secs, label) in enumerate(presets_list):
            combo.append(str(secs), label)
            if secs == current_val:
                active_idx = idx
                match_found = True

        if not match_found:
            combo.append(str(current_val), f"Custom ({current_val}s)")
            active_idx = len(presets_list)

        combo.set_active(active_idx)
        row.pack_end(combo, False, False, 0)
        return row, combo

    # 1. Turn Off Display Timeout (DPMS)
    dpms_row, dpms_combo = create_timeout_row(
        "🖥️ Turn Off Monitor After:",
        "Power down display panels via DPMS after idle time",
        DPMS_TIMEOUT_PRESETS,
        parsed_config.get("dpms_timeout", 330)
    )
    idle_card.pack_start(dpms_row, False, False, 0)

    # 2. Lock Screen Timeout
    lock_row, lock_combo = create_timeout_row(
        "🔒 Lock Screen After:",
        "Lock desktop session using hyprlock",
        LOCK_TIMEOUT_PRESETS,
        parsed_config.get("lock_timeout", 300)
    )
    idle_card.pack_start(lock_row, False, False, 0)

    # 3. Dim Screen Brightness Timeout
    dim_row, dim_combo = create_timeout_row(
        "🔅 Dim Brightness After:",
        "Lower display brightness to 10% before locking",
        DIM_TIMEOUT_PRESETS,
        parsed_config.get("dim_timeout", 150)
    )
    idle_card.pack_start(dim_row, False, False, 0)

    # 4. Suspend System Timeout
    suspend_row, suspend_combo = create_timeout_row(
        "💤 Suspend System After:",
        "Put computer to low-power sleep state",
        SUSPEND_TIMEOUT_PRESETS,
        parsed_config.get("suspend_timeout", 1800)
    )
    idle_card.pack_start(suspend_row, False, False, 0)

    content_vbox.pack_start(idle_card, False, False, 0)

    # =========================================================================
    # SECTION 3: Instant Quick Actions Bar
    # =========================================================================
    actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

    turn_off_now_btn = Gtk.Button(label="⚡ Turn Off Displays Now")
    turn_off_now_btn.get_style_context().add_class("action-btn")
    turn_off_now_btn.set_tooltip_text("Immediately trigger DPMS display power off (wakes on mouse/key)")
    actions_box.pack_start(turn_off_now_btn, True, True, 0)

    lock_now_btn = Gtk.Button(label="🔒 Lock Screen")
    lock_now_btn.get_style_context().add_class("action-btn")
    actions_box.pack_start(lock_now_btn, True, True, 0)

    apply_btn = Gtk.Button(label="💾 Apply & Save Settings")
    apply_btn.get_style_context().add_class("primary-btn")
    actions_box.pack_start(apply_btn, True, True, 0)

    main_vbox.pack_end(actions_box, False, False, 0)

    # =========================================================================
    # Event Handlers & Signals
    # =========================================================================

    def on_temp_scale_changed(scale):
        val = int(scale.get_value())
        slider_val_lbl.set_markup(f"<b>{val}K</b>")
        if sunset_switch.get_active():
            SunsetController.start(val, silent=True)
        else:
            SunsetController.set_temperature(val, silent=True)

    temp_scale.connect("value-changed", on_temp_scale_changed)

    def on_sunset_switch_toggled(sw, gparam):
        active = sw.get_active()
        if active:
            SunsetController.start(int(temp_scale.get_value()))
        else:
            SunsetController.stop()

    sunset_switch.connect("notify::active", on_sunset_switch_toggled)

    def on_caffeine_clicked(btn):
        IdleController.toggle_caffeine()
        if IdleController.is_caffeine_active():
            btn.set_label("☕ Caffeine: ACTIVE")
            btn.get_style_context().remove_class("action-btn")
            btn.get_style_context().add_class("caffeine-active")
        else:
            btn.set_label("☕ Caffeine: OFF")
            btn.get_style_context().remove_class("caffeine-active")
            btn.get_style_context().add_class("action-btn")

    caffeine_btn.connect("clicked", on_caffeine_clicked)

    def on_turn_off_now_clicked(btn):
        IdleController.turn_off_monitors()

    turn_off_now_btn.connect("clicked", on_turn_off_now_clicked)

    def on_lock_now_clicked(btn):
        IdleController.lock_screen()

    lock_now_btn.connect("clicked", on_lock_now_clicked)

    def on_apply_clicked(btn):
        dpms_s = int(dpms_combo.get_active_id() or 330)
        lock_s = int(lock_combo.get_active_id() or 300)
        dim_s = int(dim_combo.get_active_id() or 150)
        suspend_s = int(suspend_combo.get_active_id() or 1800)

        IdleController.apply_config(
            dim_timeout=dim_s,
            lock_timeout=lock_s,
            dpms_timeout=dpms_s,
            suspend_timeout=suspend_s
        )

        if sunset_switch.get_active():
            SunsetController.start(int(temp_scale.get_value()))
        else:
            SunsetController.stop()

    apply_btn.connect("clicked", on_apply_clicked)

    # Key press handler for Escape key dismissal
    def on_key_press(widget, event):
        if event.keyval == Gdk.KEY_Escape:
            win.close()
            return True
        return False

    win.connect("key-press-event", on_key_press)
    win.connect("destroy", Gtk.main_quit)

    win.show_all()
    Gtk.main()


# =============================================================================
# CLI Entrypoint & Argument Parser
# =============================================================================

def get_status_json():
    """Return complete status dictionary."""
    sunset_active = SunsetController.is_active()
    sunset_temp = SunsetController.get_current_temp()
    caffeine = IdleController.is_caffeine_active()
    idle_config = IdleController.parse_config()
    return {
        "sunset": {
            "active": sunset_active,
            "temperature_k": sunset_temp,
            "pid": SunsetController.get_pid()
        },
        "hypridle": {
            "running": IdleController.is_running(),
            "caffeine_active": caffeine,
            "dim_timeout_seconds": idle_config.get("dim_timeout", 150),
            "lock_timeout_seconds": idle_config.get("lock_timeout", 300),
            "dpms_timeout_seconds": idle_config.get("dpms_timeout", 330),
            "suspend_timeout_seconds": idle_config.get("suspend_timeout", 1800)
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Hyprsunset & Hypridle Manager (Display Power & Night Light Control Suite)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sunset_idle_manager.py --gui                      # Launch GTK3 Control Center
  sunset_idle_manager.py --menu                     # Launch Fuzzel/Wofi interactive menu
  sunset_idle_manager.py --sunset-toggle            # Toggle Night Light On/Off
  sunset_idle_manager.py --set-temp 3800            # Set Night Light temperature to 3800K
  sunset_idle_manager.py --dpms-off                 # Immediately turn off all displays
  sunset_idle_manager.py --set-dpms-timeout 300     # Set idle monitor turn-off to 5 minutes
  sunset_idle_manager.py --caffeine-toggle          # Toggle Caffeine mode (inhibit sleep/turn off)
  sunset_idle_manager.py --status                   # Print current status in JSON
        """
    )

    parser.add_argument("--gui", action="store_true", help="Launch GTK3 Control Center GUI")
    parser.add_argument("--menu", action="store_true", help="Launch interactive Fuzzel/Wofi menu")
    parser.add_argument("--sunset-toggle", "--toggle", action="store_true", help="Toggle Hyprsunset night light")
    parser.add_argument("--sunset-on", action="store_true", help="Turn on Hyprsunset night light")
    parser.add_argument("--sunset-off", action="store_true", help="Turn off Hyprsunset night light")
    parser.add_argument("--set-temp", type=int, metavar="KELVIN", help="Set color temperature (1000 - 6500K)")
    parser.add_argument("--dpms-off", action="store_true", help="Turn off monitor immediately (DPMS off)")
    parser.add_argument("--dpms-on", action="store_true", help="Turn on monitor (DPMS on)")
    parser.add_argument("--dpms-toggle", action="store_true", help="Toggle monitor power (DPMS)")
    parser.add_argument("--lock", action="store_true", help="Immediately lock screen")
    parser.add_argument("--set-dpms-timeout", type=int, metavar="SECONDS", help="Set idle monitor turn-off timeout in seconds (0 to disable)")
    parser.add_argument("--set-lock-timeout", type=int, metavar="SECONDS", help="Set idle screen lock timeout in seconds (0 to disable)")
    parser.add_argument("--set-dim-timeout", type=int, metavar="SECONDS", help="Set idle screen dimming timeout in seconds (0 to disable)")
    parser.add_argument("--set-suspend-timeout", type=int, metavar="SECONDS", help="Set idle system suspend timeout in seconds (0 to disable)")
    parser.add_argument("--caffeine-toggle", "--inhibit", action="store_true", help="Toggle Caffeine mode (Inhibit idle & display turn off)")
    parser.add_argument("--restart-idle", action="store_true", help="Restart hypridle daemon")
    parser.add_argument("--status", action="store_true", help="Print current status in JSON")
    parser.add_argument("--init", action="store_true", help="Initialize sunset according to saved state")

    args = parser.parse_args()

    # Handle commands
    if args.status:
        print(json.dumps(get_status_json(), indent=2))
        return

    if args.gui:
        show_gui()
        return

    if args.menu:
        show_menu()
        return

    if args.sunset_toggle:
        SunsetController.toggle()
        return

    if args.sunset_on:
        temp = args.set_temp or SunsetController.get_current_temp()
        SunsetController.start(temp)
        return

    if args.sunset_off:
        SunsetController.stop()
        return

    if args.set_temp is not None:
        SunsetController.set_temperature(args.set_temp)
        return

    if args.dpms_off:
        IdleController.turn_off_monitors()
        return

    if args.dpms_on:
        IdleController.turn_on_monitors()
        return

    if args.dpms_toggle:
        IdleController.toggle_monitors()
        return

    if args.lock:
        IdleController.lock_screen()
        return

    if args.caffeine_toggle:
        IdleController.toggle_caffeine()
        return

    if args.restart_idle:
        IdleController.restart_daemon()
        notify("🔄 Hypridle Restarted", "Hyprland idle daemon reloaded successfully.", "system-run")
        return

    if any(x is not None for x in [args.set_dpms_timeout, args.set_lock_timeout, args.set_dim_timeout, args.set_suspend_timeout]):
        IdleController.apply_config(
            dim_timeout=args.set_dim_timeout,
            lock_timeout=args.set_lock_timeout,
            dpms_timeout=args.set_dpms_timeout,
            suspend_timeout=args.set_suspend_timeout
        )
        return

    if args.init:
        state = load_state()
        if state.get("sunset_enabled", False):
            SunsetController.start(state.get("sunset_temp", DEFAULT_WARM_TEMP), silent=True)
        return

    # Default action if no arguments: launch GUI or menu
    show_gui()


if __name__ == "__main__":
    main()
