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
import math
import signal
import shutil
import datetime
import argparse
import subprocess
import threading
import urllib.request
from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".config" / "hypr"
HYPRIDLE_CONF = CONFIG_DIR / "hypridle.conf"
STATE_DIR = Path.home() / ".cache"
STATE_FILE = STATE_DIR / "sunset_idle_state.json"
NIGHTLIGHT_PID_FILE = Path("/tmp/hypr_nightlight.pid")
NIGHTLIGHT_STATE_FILE = Path("/tmp/hypr_nightlight.state")
CAFFEINE_PID_FILE = Path("/tmp/hypr_caffeine.pid")
DAEMON_PID_FILE = Path("/tmp/hypr_sunset_daemon.pid")
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
                data = json.load(f)
                return data
        except Exception:
            pass
    return {
        "sunset_enabled": False,
        "sunset_temp": DEFAULT_WARM_TEMP,
        "schedule_mode": "manual",  # "manual" | "custom" | "location"
        "schedule_on": "20:00",
        "schedule_off": "06:30",
        "latitude": 18.52,
        "longitude": 73.85,
        "location_name": "Auto / Pune, India",
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
    """Load colors and theme type from active theme JSON file with fallback."""
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

    for d in [Path.home() / ".config" / "theme", Path.home() / ".dotfiles" / ".config" / "theme"]:
        tfile = d / f"{theme_id}.json"
        if tfile.exists():
            try:
                with open(tfile, "r") as f:
                    tdata = json.load(f)
                    return tdata.get("colors", {}), tdata.get("type", "dark"), theme_id
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
    }, "dark", "catppuccin-mocha"


def get_contrast_color(hex_color, dark_fg="#11111b", light_fg="#ffffff"):
    """Calculate WCAG high-contrast foreground color based on background luminance."""
    if not hex_color or not isinstance(hex_color, str) or not hex_color.startswith("#"):
        return light_fg
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c + c for c in hex_clean)
    if len(hex_clean) < 6:
        return light_fg
    try:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return dark_fg if lum > 140 else light_fg
    except Exception:
        return light_fg


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
        """Cleanly terminate all night light instances and ensure unbinding."""
        # 1. Kill recorded pid if exists
        if NIGHTLIGHT_PID_FILE.exists():
            try:
                pid = int(NIGHTLIGHT_PID_FILE.read_text().strip())
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            NIGHTLIGHT_PID_FILE.unlink(missing_ok=True)
            NIGHTLIGHT_STATE_FILE.unlink(missing_ok=True)

        # 2. Terminate all instances
        subprocess.run(["pkill", "-x", "hyprsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-x", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Wait up to 300ms for clean unbinding from hyprland-ctm-control
        for _ in range(15):
            res_hs = subprocess.run(["pgrep", "-x", "hyprsunset"], capture_output=True, text=True)
            res_ws = subprocess.run(["pgrep", "-x", "wlsunset"], capture_output=True, text=True)
            if not res_hs.stdout.strip() and not res_ws.stdout.strip():
                break
            time.sleep(0.02)
        else:
            subprocess.run(["pkill", "-9", "-x", "hyprsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-x", "wlsunset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.05)

        state = load_state()
        state["sunset_enabled"] = False
        save_state(state)

        if not silent:
            notify("☀️ Night Light Disabled", "Display color temperature restored to daylight (6500K).", "weather-clear")

    @staticmethod
    def start(temp=None, silent=False):
        """Start hyprsunset with clean process isolation."""
        if temp is None:
            temp = SunsetController.get_current_temp()
        temp = int(temp)

        # If already running at this exact temperature, just update state
        if SunsetController.is_active() and SunsetController.get_current_temp() == temp:
            state = load_state()
            state["sunset_enabled"] = True
            state["sunset_temp"] = temp
            save_state(state)
            return True

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
            time.sleep(0.06)
            if proc.poll() is not None:
                # Retrying once after full kill cleanup
                SunsetController.stop(silent=True)
                time.sleep(0.08)
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.06)

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
        if SunsetController.is_active() or state.get("sunset_enabled", False):
            SunsetController.start(temp, silent=silent)
        elif not silent:
            notify("⚙️ Night Light Preset Updated", f"Target temperature set to <b>{temp}K</b> (Currently Disabled).", "preferences-desktop-display")


# =============================================================================
# Night Light Schedule & Solar Location Manager
# =============================================================================

class ScheduleManager:
    @staticmethod
    def calculate_sun_times(lat, lon, date=None):
        """Calculate sunrise and sunset times (local time) for given latitude and longitude."""
        if date is None:
            date = datetime.date.today()
        day_of_year = date.timetuple().tm_yday
        gamma = 2 * math.pi / 365 * (day_of_year - 1)
        eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
        decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma) - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)

        lat_rad = math.radians(float(lat))
        zenith_rad = math.radians(90.833)  # Official solar zenith with atmospheric refraction

        cos_ha = (math.cos(zenith_rad) / (math.cos(lat_rad) * math.cos(decl))) - (math.tan(lat_rad) * math.tan(decl))
        if cos_ha > 1.0 or cos_ha < -1.0:
            return None, None  # Polar day / night

        ha = math.degrees(math.acos(cos_ha))
        sunrise_utc_min = 720 - 4 * (float(lon) + ha) - eqtime
        sunset_utc_min = 720 - 4 * (float(lon) - ha) - eqtime

        now = datetime.datetime.now()
        utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        tz_offset = (now - utc_now).total_seconds() / 60.0

        sunrise_local_min = (sunrise_utc_min + tz_offset) % 1440
        sunset_local_min = (sunset_utc_min + tz_offset) % 1440

        sunrise_time = datetime.time(int(sunrise_local_min // 60), int(sunrise_local_min % 60))
        sunset_time = datetime.time(int(sunset_local_min // 60), int(sunset_local_min % 60))
        return sunrise_time, sunset_time

    @staticmethod
    def auto_detect_location():
        """Auto-detect geographic coordinates and city via free IP geolocation."""
        endpoints = [
            ("http://ip-api.com/json/?fields=status,country,city,lat,lon", lambda d: (d.get("lat"), d.get("lon"), f"{d.get('city', '')}, {d.get('country', '')}".strip(", ")) if d.get("status") == "success" else None),
            ("https://ipapi.co/json/", lambda d: (d.get("latitude"), d.get("longitude"), f"{d.get('city', '')}, {d.get('country_name', '')}".strip(", ")) if "latitude" in d else None)
        ]
        for url, parser in endpoints:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "SunsetIdleManager/1.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode())
                    res = parser(data)
                    if res and res[0] is not None and res[1] is not None:
                        return float(res[0]), float(res[1]), res[2]
            except Exception:
                continue
        return None, None, None

    @staticmethod
    def is_time_in_range(start_time, end_time, current_time=None):
        """Check if current time is within [start_time, end_time] accounting for midnight wrap."""
        if current_time is None:
            current_time = datetime.datetime.now().time()
        if start_time < end_time:
            return start_time <= current_time <= end_time
        else:
            # Over midnight (e.g. 20:00 to 06:30)
            return current_time >= start_time or current_time <= end_time

    @staticmethod
    def should_nightlight_be_active(state=None):
        """Determine if night light should currently be active according to schedule rules."""
        if state is None:
            state = load_state()

        mode = state.get("schedule_mode", "manual")
        if mode == "manual":
            return state.get("sunset_enabled", False), "manual"

        now_time = datetime.datetime.now().time()

        if mode == "custom":
            on_str = state.get("schedule_on", "20:00")
            off_str = state.get("schedule_off", "06:30")
            try:
                on_h, on_m = map(int, on_str.split(":"))
                off_h, off_m = map(int, off_str.split(":"))
                start_t = datetime.time(on_h, on_m)
                end_t = datetime.time(off_h, off_m)
                active = ScheduleManager.is_time_in_range(start_t, end_t, now_time)
                return active, f"custom ({on_str} - {off_str})"
            except Exception:
                return False, "invalid_custom_time"

        elif mode == "location":
            lat = state.get("latitude")
            lon = state.get("longitude")
            if lat is None or lon is None:
                lat, lon, loc_name = ScheduleManager.auto_detect_location()
                if lat is not None and lon is not None:
                    state["latitude"] = lat
                    state["longitude"] = lon
                    state["location_name"] = loc_name or "Auto Location"
                    save_state(state)

            if lat is not None and lon is not None:
                s_rise, s_set = ScheduleManager.calculate_sun_times(lat, lon)
                if s_rise and s_set:
                    # Night light is ON from sunset to sunrise
                    active = ScheduleManager.is_time_in_range(s_set, s_rise, now_time)
                    return active, f"solar (Sunset {s_set.strftime('%H:%M')} - Sunrise {s_rise.strftime('%H:%M')})"

        return False, "unknown"

    @staticmethod
    def evaluate_and_apply(silent=True):
        """Evaluate schedule and apply night light status."""
        state = load_state()
        mode = state.get("schedule_mode", "manual")
        if mode == "manual":
            return

        should_be_on, reason = ScheduleManager.should_nightlight_be_active(state)
        target_temp = state.get("sunset_temp", DEFAULT_WARM_TEMP)
        is_currently_active = SunsetController.is_active()

        if should_be_on and not is_currently_active:
            SunsetController.start(target_temp, silent=silent)
        elif not should_be_on and is_currently_active:
            SunsetController.stop(silent=silent)


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
            dpms_match = re.search(r'listener\s*\{[^}]*timeout\s*=\s*(\d+)[^}]*dpms', content, re.DOTALL)
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
        """Generate standardized hypridle.conf content with Lua & standard DPMS dispatchers."""
        lines = [
            "# =============================================================================",
            "# Hypridle Configuration - Hyprland Idle Daemon",
            "# (Managed by Sunset & Idle Control Suite)",
            "# =============================================================================",
            "",
            "general {",
            "    lock_cmd = pidof hyprlock || hyprlock       # Command to run on dbus lock-session",
            "    before_sleep_cmd = loginctl lock-session    # Lock before suspend",
            "    after_sleep_cmd = hyprctl dispatch 'hl.dsp.dpms(\"on\")' 2>/dev/null || hyprctl dispatch dpms on  # Turn display back on after resume",
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
                "    on-timeout = hyprctl dispatch 'hl.dsp.dpms(\"off\")' 2>/dev/null || hyprctl dispatch dpms off",
                "    on-resume = hyprctl dispatch 'hl.dsp.dpms(\"on\")' 2>/dev/null || hyprctl dispatch dpms on",
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
    def _dispatch_hypr(action):
        """Execute Hyprland DPMS dispatcher with Lua & standard fallbacks."""
        # 1. Try Hyprland Lua dispatcher
        lua_cmd = ["hyprctl", "dispatch", f'hl.dsp.dpms("{action}")']
        res = subprocess.run(lua_cmd, capture_output=True, text=True)
        if "ok" in res.stdout:
            return True
        # 2. Fallback to standard Hyprland legacy dispatcher
        std_cmd = ["hyprctl", "dispatch", "dpms", action]
        res_std = subprocess.run(std_cmd, capture_output=True, text=True)
        return "ok" in res_std.stdout

    @staticmethod
    def turn_off_monitors():
        """Immediately turn off monitor via DPMS."""
        return IdleController._dispatch_hypr("off")

    @staticmethod
    def turn_on_monitors():
        """Turn on monitors via DPMS."""
        return IdleController._dispatch_hypr("on")

    @staticmethod
    def toggle_monitors():
        """Toggle monitor power state via DPMS."""
        return IdleController._dispatch_hypr("toggle")

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
    state = load_state()
    sched_mode = state.get("schedule_mode", "manual")
    sched_label = "Manual" if sched_mode == "manual" else ("Custom Times" if sched_mode == "custom" else "Solar / Location")

    menu_items = [
        f"🌙 Toggle Night Light ({'ON' if sunset_active else 'OFF'} • {current_temp}K)",
        f"🌡️  Set Night Light Temperature...",
        f"⏰ Configure Night Light Schedule (Mode: {sched_label})...",
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
    elif "Configure Night Light Schedule" in choice:
        sched_items = [
            "1. Manual (Disabled / Controlled Manually)",
            "2. Custom Schedule (Fixed Time Range)",
            "3. Solar Sunset to Sunrise (Location Coordinates)"
        ]
        s_choice = prompt_menu(launcher, sched_items, "Night Light Schedule Mode")
        if s_choice:
            state = load_state()
            if "1. Manual" in s_choice:
                state["schedule_mode"] = "manual"
                save_state(state)
                notify("⏰ Schedule Updated", "Night Light schedule set to Manual mode.", "preferences-desktop-display")
            elif "2. Custom" in s_choice:
                on_t = prompt_input(launcher, "Enter Turn-On Time (HH:MM e.g. 20:00):", state.get("schedule_on", "20:00"))
                off_t = prompt_input(launcher, "Enter Turn-Off Time (HH:MM e.g. 06:30):", state.get("schedule_off", "06:30"))
                if on_t and off_t:
                    state["schedule_mode"] = "custom"
                    state["schedule_on"] = on_t
                    state["schedule_off"] = off_t
                    save_state(state)
                    ScheduleManager.evaluate_and_apply(silent=False)
                    notify("⏰ Custom Schedule Saved", f"Night Light active from <b>{on_t}</b> to <b>{off_t}</b>.", "preferences-desktop-display")
            elif "3. Solar" in s_choice:
                loc_opts = [
                    "📍 Auto-Detect Location via IP",
                    "✏️  Enter Latitude & Longitude Manually"
                ]
                loc_choice = prompt_menu(launcher, loc_opts, "Location Setup")
                if loc_choice:
                    if "Auto-Detect" in loc_choice:
                        lat, lon, loc_name = ScheduleManager.auto_detect_location()
                        if lat is not None and lon is not None:
                            state["schedule_mode"] = "location"
                            state["latitude"] = lat
                            state["longitude"] = lon
                            state["location_name"] = loc_name or "Auto Location"
                            save_state(state)
                            s_rise, s_set = ScheduleManager.calculate_sun_times(lat, lon)
                            ScheduleManager.evaluate_and_apply(silent=False)
                            notify("📍 Location Configured", f"Location: <b>{loc_name}</b>\nSunset: <b>{s_set.strftime('%H:%M')}</b> | Sunrise: <b>{s_rise.strftime('%H:%M')}</b>", "mark-location")
                        else:
                            notify("❌ Error", "Could not detect location via IP.", "dialog-error")
                    elif "Manually" in loc_choice:
                        lat_in = prompt_input(launcher, "Enter Latitude (e.g. 18.52):", str(state.get("latitude", "18.52")))
                        lon_in = prompt_input(launcher, "Enter Longitude (e.g. 73.85):", str(state.get("longitude", "73.85")))
                        if lat_in and lon_in:
                            try:
                                state["schedule_mode"] = "location"
                                state["latitude"] = float(lat_in)
                                state["longitude"] = float(lon_in)
                                save_state(state)
                                s_rise, s_set = ScheduleManager.calculate_sun_times(float(lat_in), float(lon_in))
                                ScheduleManager.evaluate_and_apply(silent=False)
                                notify("📍 Location Saved", f"Solar Sunset: <b>{s_set.strftime('%H:%M')}</b> | Sunrise: <b>{s_rise.strftime('%H:%M')}</b>", "mark-location")
                            except Exception as e:
                                notify("❌ Error", f"Invalid coordinates: {e}", "dialog-error")
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

    colors, theme_type, theme_id = get_active_theme_colors()

    c_base = colors.get("base", "#1e1e2e")
    c_mantle = colors.get("mantle", "#181825")
    c_crust = colors.get("crust", "#11111b")
    c_surface0 = colors.get("surface0", "#313244")
    c_surface1 = colors.get("surface1", "#45475a")
    c_surface2 = colors.get("surface2", "#585b70")
    c_text = colors.get("text", "#cdd6f4")
    c_subtext0 = colors.get("subtext0", "#a6adc8")
    c_accent = colors.get("accent", colors.get("mauve", "#cba6f7"))
    c_blue = colors.get("blue", "#89b4fa")
    c_peach = colors.get("peach", "#fab387")
    c_red = colors.get("red", "#f38ba8")
    c_green = colors.get("green", "#a6e3a1")

    # Dynamic contrast foregrounds for buttons
    primary_fg = get_contrast_color(c_accent)
    danger_fg = get_contrast_color(c_red)
    caffeine_fg = get_contrast_color(c_peach)
    accent_fg = get_contrast_color(c_accent)

    # Create GTK Window
    win = Gtk.Window(title="Night Light & Display Idle Manager")
    win.set_default_size(580, 680)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.set_border_width(18)

    # Apply CSS styling
    css = f"""
    * {{
        font-family: 'Inter', 'JetBrains Mono Nerd Font', 'Noto Sans', sans-serif;
    }}
    window {{
        background-color: {c_base};
        color: {c_text};
    }}
    .header-box {{
        background-color: {c_mantle};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        border: 1px solid {c_surface0};
    }}
    .card-box {{
        background-color: {c_mantle};
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        border: 1px solid {c_surface0};
    }}
    label {{
        color: {c_text};
    }}
    .title-label {{
        font-size: 16pt;
        font-weight: bold;
        color: {c_accent};
    }}
    .subtitle-label {{
        font-size: 9.5pt;
        color: {c_subtext0};
    }}
    .section-title {{
        font-size: 11pt;
        font-weight: bold;
        color: {c_blue};
    }}
    button {{
        background-image: none;
        box-shadow: none;
        text-shadow: none;
    }}
    .preset-btn, .preset-btn label {{
        background-color: {c_surface0};
        color: {c_text};
        border-radius: 8px;
        border: 1px solid {c_surface1};
        padding: 6px 10px;
        font-size: 9pt;
        font-weight: 600;
    }}
    .preset-btn:hover, .preset-btn:hover label {{
        background-color: {c_accent};
        color: {accent_fg};
        border-color: {c_accent};
    }}
    .action-btn, .action-btn label {{
        background-color: {c_surface0};
        color: {c_text};
        border-radius: 8px;
        border: 1px solid {c_surface1};
        padding: 8px 14px;
        font-weight: bold;
    }}
    .action-btn:hover, .action-btn:hover label {{
        background-color: {c_surface1};
        color: {c_text};
        border-color: {c_accent};
    }}
    .primary-btn, .primary-btn label {{
        background-color: {c_accent};
        color: {primary_fg};
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 16px;
        border: 1px solid {c_accent};
    }}
    .primary-btn:hover, .primary-btn:hover label {{
        background-color: {c_surface1};
        color: {c_text};
        border-color: {c_accent};
    }}
    .danger-btn, .danger-btn label {{
        background-color: {c_red};
        color: {danger_fg};
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 14px;
        border: none;
    }}
    .caffeine-active, .caffeine-active label {{
        background-color: {c_peach};
        color: {caffeine_fg};
        font-weight: bold;
        border: 1px solid {c_peach};
    }}
    scale trough {{
        background-color: {c_surface0};
        border-radius: 6px;
        min-height: 8px;
    }}
    scale highlight {{
        background-color: {c_accent};
        border-radius: 6px;
    }}
    scale slider {{
        background-color: {c_accent};
        min-width: 18px;
        min-height: 18px;
        border-radius: 50%;
    }}
    combobox button, combobox button label, combobox button cellview {{
        background-color: {c_surface0};
        color: {c_text};
        border-radius: 8px;
        border: 1px solid {c_surface1};
        padding: 4px 8px;
        font-weight: 600;
    }}
    combobox button:hover {{
        border-color: {c_accent};
    }}
    menu, combobox menu, combobox window {{
        background-color: {c_mantle};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 8px;
        padding: 4px;
    }}
    menuitem, menuitem label {{
        color: {c_text};
        font-weight: 600;
        padding: 4px 8px;
    }}
    menuitem:hover, menuitem:hover label {{
        background-color: {c_accent};
        color: {accent_fg};
        border-radius: 6px;
    }}
    entry {{
        background-color: {c_surface0};
        color: {c_text};
        border-radius: 8px;
        border: 1px solid {c_surface1};
        padding: 5px 8px;
        font-weight: 600;
    }}
    entry:focus {{
        border-color: {c_accent};
    }}
    separator {{
        background-color: {c_surface0};
        min-height: 1px;
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

    # Schedule Section
    sched_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sunset_card.pack_start(sched_sep, False, False, 6)

    sched_hdr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    sched_title = Gtk.Label(xalign=0)
    sched_title.set_markup(f"<b>⏰ Auto Schedule:</b>")
    sched_hdr_box.pack_start(sched_title, True, True, 0)

    sched_mode_combo = Gtk.ComboBoxText()
    sched_mode_combo.append("manual", "Manual (Controlled Manually)")
    sched_mode_combo.append("custom", "Custom Hours (Fixed Times)")
    sched_mode_combo.append("location", "Solar Sunset to Sunrise (Location)")
    
    current_state = load_state()
    sched_mode_combo.set_active_id(current_state.get("schedule_mode", "manual"))
    sched_hdr_box.pack_end(sched_mode_combo, False, False, 0)
    sunset_card.pack_start(sched_hdr_box, False, False, 0)

    # 1. Custom Time Container Box
    custom_time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    on_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    on_lbl = Gtk.Label(label="Turn On At:", xalign=0)
    on_entry = Gtk.Entry()
    on_entry.set_text(current_state.get("schedule_on", "20:00"))
    on_entry.set_max_length(5)
    on_entry.set_width_chars(6)
    on_entry.set_placeholder_text("20:00")
    on_box.pack_start(on_lbl, False, False, 0)
    on_box.pack_start(on_entry, False, False, 0)
    custom_time_box.pack_start(on_box, True, True, 0)

    off_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    off_lbl = Gtk.Label(label="Turn Off At:", xalign=0)
    off_entry = Gtk.Entry()
    off_entry.set_text(current_state.get("schedule_off", "06:30"))
    off_entry.set_max_length(5)
    off_entry.set_width_chars(6)
    off_entry.set_placeholder_text("06:30")
    off_box.pack_start(off_lbl, False, False, 0)
    off_box.pack_start(off_entry, False, False, 0)
    custom_time_box.pack_start(off_box, True, True, 0)
    sunset_card.pack_start(custom_time_box, False, False, 0)

    # 2. Location Container Box
    location_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    loc_inputs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    
    lat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    lat_lbl = Gtk.Label(label="Latitude:", xalign=0)
    lat_entry = Gtk.Entry()
    lat_entry.set_text(str(current_state.get("latitude", 18.52)))
    lat_entry.set_width_chars(8)
    lat_box.pack_start(lat_lbl, False, False, 0)
    lat_box.pack_start(lat_entry, False, False, 0)
    loc_inputs_box.pack_start(lat_box, True, True, 0)

    lon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    lon_lbl = Gtk.Label(label="Longitude:", xalign=0)
    lon_entry = Gtk.Entry()
    lon_entry.set_text(str(current_state.get("longitude", 73.85)))
    lon_entry.set_width_chars(8)
    lon_box.pack_start(lon_lbl, False, False, 0)
    lon_box.pack_start(lon_entry, False, False, 0)
    loc_inputs_box.pack_start(lon_box, True, True, 0)

    detect_loc_btn = Gtk.Button(label="📍 Auto-Detect")
    detect_loc_btn.get_style_context().add_class("action-btn")
    detect_loc_btn.set_tooltip_text("Auto-detect coordinates via IP geolocation")
    loc_inputs_box.pack_end(detect_loc_btn, False, False, 0)
    location_box.pack_start(loc_inputs_box, False, False, 0)

    # Solar times badge
    solar_info_lbl = Gtk.Label(xalign=0)
    def update_solar_info_label(lat_v, lon_v, loc_name=None):
        try:
            s_rise, s_set = ScheduleManager.calculate_sun_times(float(lat_v), float(lon_v))
            if s_rise and s_set:
                loc_str = f" ({loc_name})" if loc_name else ""
                solar_info_lbl.set_markup(
                    f"<span size='small' color='{colors.get('peach', '#fab387')}'>☀️ Solar times today{loc_str}: <b>Sunrise {s_rise.strftime('%H:%M')}</b> • <b>Sunset {s_set.strftime('%H:%M')}</b></span>"
                )
            else:
                solar_info_lbl.set_markup("<span size='small' color='{colors.get('subtext0', '#a6adc8')}'>Polar day/night region</span>")
        except Exception:
            solar_info_lbl.set_markup("<span size='small' color='{colors.get('red', '#f38ba8')}'>Invalid coordinates</span>")

    update_solar_info_label(lat_entry.get_text(), lon_entry.get_text(), current_state.get("location_name"))
    location_box.pack_start(solar_info_lbl, False, False, 0)
    sunset_card.pack_start(location_box, False, False, 0)

    def on_sched_mode_changed(combo):
        m = combo.get_active_id()
        custom_time_box.set_visible(m == "custom")
        location_box.set_visible(m == "location")

    sched_mode_combo.connect("changed", on_sched_mode_changed)
    on_sched_mode_changed(sched_mode_combo)

    def on_detect_loc_clicked(btn):
        btn.set_label("📍 Detecting...")
        btn.set_sensitive(False)
        def _bg_detect():
            lat_res, lon_res, name_res = ScheduleManager.auto_detect_location()
            def _apply_ui():
                btn.set_label("📍 Auto-Detect")
                btn.set_sensitive(True)
                if lat_res is not None and lon_res is not None:
                    lat_entry.set_text(f"{lat_res:.4f}")
                    lon_entry.set_text(f"{lon_res:.4f}")
                    update_solar_info_label(lat_res, lon_res, name_res)
                    notify("📍 Location Detected", f"Found coordinates: <b>{name_res}</b> ({lat_res:.2f}, {lon_res:.2f})", "mark-location")
                else:
                    notify("❌ Location Error", "Could not detect location via IP. Please enter coordinates manually.", "dialog-error")
                return False
            GLib.idle_add(_apply_ui)
        threading.Thread(target=_bg_detect, daemon=True).start()

    detect_loc_btn.connect("clicked", on_detect_loc_clicked)

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

    scale_debounce_timer = [None]
    updating_switch_ui = [False]

    def _apply_debounced_temp(target_val):
        if sunset_switch.get_active():
            SunsetController.start(target_val, silent=True)
        else:
            SunsetController.set_temperature(target_val, silent=True)
        scale_debounce_timer[0] = None
        return False

    def on_temp_scale_changed(scale):
        val = int(scale.get_value())
        slider_val_lbl.set_markup(f"<b>{val}K</b>")
        if scale_debounce_timer[0] is not None:
            GLib.source_remove(scale_debounce_timer[0])
        scale_debounce_timer[0] = GLib.timeout_add(150, _apply_debounced_temp, val)

    temp_scale.connect("value-changed", on_temp_scale_changed)

    def on_sunset_switch_toggled(sw, gparam):
        if updating_switch_ui[0]:
            return
        active = sw.get_active()
        target_temp = int(temp_scale.get_value())
        if active:
            SunsetController.start(target_temp)
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
        # Brief delay so mouse button release does not cancel DPMS sleep immediately
        threading.Timer(0.35, IdleController.turn_off_monitors).start()

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

        m = sched_mode_combo.get_active_id() or "manual"
        state = load_state()
        state["schedule_mode"] = m
        state["schedule_on"] = on_entry.get_text().strip() or "20:00"
        state["schedule_off"] = off_entry.get_text().strip() or "06:30"
        try:
            state["latitude"] = float(lat_entry.get_text().strip())
            state["longitude"] = float(lon_entry.get_text().strip())
        except Exception:
            pass
        target_temp = int(temp_scale.get_value())
        state["sunset_temp"] = target_temp
        save_state(state)

        if m != "manual":
            ScheduleManager.evaluate_and_apply(silent=False)
            notify("💾 Settings & Schedule Saved", f"Schedule mode: <b>{m.title()}</b> applied.", "document-save")
        else:
            if sunset_switch.get_active():
                SunsetController.start(target_temp, silent=True)
            else:
                SunsetController.stop(silent=True)
            notify("💾 Settings Saved", "Display idle timeouts and Night Light preferences applied.", "document-save")

    apply_btn.connect("clicked", on_apply_clicked)

    def sync_ui_state():
        """Periodic real-time UI state synchronization."""
        # 1. Night Light switch state
        is_nl_active = SunsetController.is_active()
        if sunset_switch.get_active() != is_nl_active:
            updating_switch_ui[0] = True
            sunset_switch.set_active(is_nl_active)
            updating_switch_ui[0] = False

        # 2. Caffeine button state
        is_caff = IdleController.is_caffeine_active()
        classes = caffeine_btn.get_style_context().list_classes()
        if is_caff and "action-btn" in classes:
            caffeine_btn.set_label("☕ Caffeine: ACTIVE")
            caffeine_btn.get_style_context().remove_class("action-btn")
            caffeine_btn.get_style_context().add_class("caffeine-active")
        elif not is_caff and "caffeine-active" in classes:
            caffeine_btn.set_label("☕ Caffeine: OFF")
            caffeine_btn.get_style_context().remove_class("caffeine-active")
            caffeine_btn.get_style_context().add_class("action-btn")

        return True

    GLib.timeout_add(1000, sync_ui_state)

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
# Background Daemon & CLI Entrypoint
# =============================================================================

def run_daemon():
    """Run persistent background scheduler daemon."""
    # Check if another daemon is already running
    if DAEMON_PID_FILE.exists():
        try:
            old_pid = int(DAEMON_PID_FILE.read_text().strip())
            if old_pid != os.getpid():
                os.kill(old_pid, 0)
                print(f"Sunset scheduler daemon is already active (PID {old_pid}). Exiting.")
                return
        except Exception:
            pass

    DAEMON_PID_FILE.write_text(str(os.getpid()))

    def _cleanup_daemon(*args):
        DAEMON_PID_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup_daemon)
    signal.signal(signal.SIGTERM, _cleanup_daemon)

    print("Sunset & Idle Manager background scheduler daemon running...", flush=True)

    # Initial check on launch
    try:
        ScheduleManager.evaluate_and_apply(silent=True)
    except Exception as e:
        print(f"Initial schedule error: {e}", file=sys.stderr)

    while True:
        time.sleep(60)
        try:
            ScheduleManager.evaluate_and_apply(silent=True)
        except Exception as e:
            print(f"Schedule evaluation error: {e}", file=sys.stderr)


def get_status_json():
    """Return complete status dictionary."""
    sunset_active = SunsetController.is_active()
    sunset_temp = SunsetController.get_current_temp()
    caffeine = IdleController.is_caffeine_active()
    idle_config = IdleController.parse_config()
    state = load_state()
    sched_mode = state.get("schedule_mode", "manual")
    should_be_active, reason = ScheduleManager.should_nightlight_be_active(state)

    solar_times = {}
    if state.get("latitude") is not None and state.get("longitude") is not None:
        try:
            s_rise, s_set = ScheduleManager.calculate_sun_times(state["latitude"], state["longitude"])
            if s_rise and s_set:
                solar_times = {
                    "sunrise": s_rise.strftime("%H:%M"),
                    "sunset": s_set.strftime("%H:%M")
                }
        except Exception:
            pass

    return {
        "sunset": {
            "active": sunset_active,
            "temperature_k": sunset_temp,
            "pid": SunsetController.get_pid()
        },
        "schedule": {
            "mode": sched_mode,
            "custom_on": state.get("schedule_on", "20:00"),
            "custom_off": state.get("schedule_off", "06:30"),
            "latitude": state.get("latitude"),
            "longitude": state.get("longitude"),
            "location_name": state.get("location_name"),
            "solar_times_today": solar_times,
            "should_be_active_now": should_be_active,
            "rule_reason": reason
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
  sunset_idle_manager.py --schedule-mode location   # Enable Solar Sunset/Sunrise auto-schedule
  sunset_idle_manager.py --auto-location            # Auto-detect coordinates via IP geolocation
  sunset_idle_manager.py --schedule-mode custom --schedule-on 21:00 --schedule-off 07:00
  sunset_idle_manager.py --daemon                   # Run background schedule evaluator daemon
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
    
    # Schedule options
    parser.add_argument("--schedule-mode", choices=["manual", "custom", "location"], help="Set Night Light schedule mode")
    parser.add_argument("--schedule-on", metavar="HH:MM", help="Set custom schedule start time (e.g. 20:00)")
    parser.add_argument("--schedule-off", metavar="HH:MM", help="Set custom schedule stop time (e.g. 06:30)")
    parser.add_argument("--schedule-lat", type=float, metavar="LAT", help="Set geographic latitude")
    parser.add_argument("--schedule-lon", type=float, metavar="LON", help="Set geographic longitude")
    parser.add_argument("--auto-location", action="store_true", help="Auto-detect latitude and longitude via IP geolocation")
    parser.add_argument("--check-schedule", action="store_true", help="Evaluate schedule rules and apply state once")
    parser.add_argument("--daemon", action="store_true", help="Run persistent background scheduler daemon")

    # DPMS & Idle options
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
    parser.add_argument("--init", action="store_true", help="Initialize sunset according to saved state or schedule")

    args = parser.parse_args()

    # Handle daemon
    if args.daemon:
        run_daemon()
        return

    # Handle status
    if args.status:
        print(json.dumps(get_status_json(), indent=2))
        return

    # Handle auto-location
    if args.auto_location:
        lat, lon, name = ScheduleManager.auto_detect_location()
        if lat is not None and lon is not None:
            state = load_state()
            state["latitude"] = lat
            state["longitude"] = lon
            state["location_name"] = name or "Auto Location"
            save_state(state)
            s_rise, s_set = ScheduleManager.calculate_sun_times(lat, lon)
            print(f"Location Detected: {name} (Lat: {lat:.4f}, Lon: {lon:.4f})")
            if s_rise and s_set:
                print(f"Solar Times Today: Sunrise {s_rise.strftime('%H:%M')} | Sunset {s_set.strftime('%H:%M')}")
            notify("📍 Location Detected", f"<b>{name}</b> ({lat:.2f}, {lon:.2f})", "mark-location")
        else:
            print("Failed to auto-detect location.", file=sys.stderr)
            notify("❌ Error", "Could not detect location via IP.", "dialog-error")
        return

    # Handle schedule updates
    schedule_changed = False
    state = load_state()
    if args.schedule_mode:
        state["schedule_mode"] = args.schedule_mode
        schedule_changed = True
    if args.schedule_on:
        state["schedule_on"] = args.schedule_on
        schedule_changed = True
    if args.schedule_off:
        state["schedule_off"] = args.schedule_off
        schedule_changed = True
    if args.schedule_lat is not None:
        state["latitude"] = args.schedule_lat
        schedule_changed = True
    if args.schedule_lon is not None:
        state["longitude"] = args.schedule_lon
        schedule_changed = True

    if schedule_changed:
        save_state(state)
        ScheduleManager.evaluate_and_apply(silent=False)
        notify("⏰ Schedule Configured", f"Night Light Schedule Mode: <b>{state['schedule_mode'].title()}</b>", "preferences-desktop-display")
        return

    if args.check_schedule:
        ScheduleManager.evaluate_and_apply(silent=False)
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
        if state.get("schedule_mode", "manual") != "manual":
            ScheduleManager.evaluate_and_apply(silent=True)
        elif state.get("sunset_enabled", False):
            SunsetController.start(state.get("sunset_temp", DEFAULT_WARM_TEMP), silent=True)
        return

    # Default action if no arguments: launch GUI
    show_gui()


if __name__ == "__main__":
    main()
