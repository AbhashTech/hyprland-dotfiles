#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha Sound Control Center & Audio Hub for Waybar & Hyprland
 Features:
   - Full Modern GTK3 Layer Shell GUI with:
       * Output Device (Sinks) Dropdown Selection
       * Input Device (Microphones) Dropdown Selection
       * Master Output Volume Range Slider (0% - 150% with Boost)
       * Master Microphone Volume Range Slider (0% - 100%)
       * Quick Preset Volume Buttons (20%, 50%, 80%, 100%, 150%)
       * Real-time Per-Application Audio Stream Mixers
       * Mute toggles with active status badges
       * Stereo Sound Test Tone & Audio Stack Recovery
       * Auto-dismiss on outside click or Escape key
   - Interactive Curses TUI Mixer overlay (--tui)
   - Fast Fuzzel / Wofi Menu Fallback (--fuzzel)
   - Seamless Waybar right-click singleton toggle integration
=============================================================================
"""

import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

SINK_NOTIF_ID = "9122"
SOURCE_NOTIF_ID = "9123"
BOOST_MAX_VOLUME = 150
DEFAULT_STEP = 5

def run_cmd(cmd, check=False):
    """Execute command and return stripped stdout or empty string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""

def build_progress_bar(percentage, length=12):
    """Create a visual ASCII progress bar."""
    pct = max(0, min(100, percentage))
    filled = int(round((pct / 100.0) * length))
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"

def show_notification(title, body, icon="audio-speakers", percentage=None, notif_id=SINK_NOTIF_ID, tag="sound_osd"):
    """Display desktop OSD notification."""
    cmd = [
        "notify-send",
        "-r", str(notif_id),
        "-t", "1500",
        "-u", "low",
        "-a", "Sound Manager",
        "-c", "osd",
        "-i", icon,
        "-h", f"string:x-canonical-private-synchronous:{tag}",
        "-h", "boolean:transient:true",
        "-h", "boolean:history-ignore:true"
    ]
    if percentage is not None:
        cmd.extend(["-h", f"int:value:{int(min(100, max(0, percentage)))}"])
    cmd.extend([title, body])
    subprocess.Popen(cmd)

# =============================================================================
# AUDIO BACKEND (PipeWire / PulseAudio / wpctl / pactl)
# =============================================================================

class SoundBackend:
    @staticmethod
    def get_default_sink_info():
        out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
        vol = 0
        muted = False
        if out:
            parts = out.strip().split()
            if len(parts) >= 2:
                try:
                    vol = int(round(float(parts[1]) * 100))
                except ValueError:
                    vol = 0
            if "[MUTED]" in out:
                muted = True

        name = "Speakers / Output"
        default_sink_name = run_cmd(["pactl", "get-default-sink"])
        raw = run_cmd(["pactl", "-f", "json", "list", "sinks"])
        if raw and default_sink_name:
            try:
                sinks = json.loads(raw)
                for s in sinks:
                    if s.get("name") == default_sink_name:
                        desc = s.get("description", "")
                        if desc:
                            name = SoundBackend.clean_device_name(desc)
                        break
            except Exception:
                pass
        return vol, muted, name

    @staticmethod
    def get_default_source_info():
        out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])
        vol = 0
        muted = False
        if out:
            parts = out.strip().split()
            if len(parts) >= 2:
                try:
                    vol = int(round(float(parts[1]) * 100))
                except ValueError:
                    vol = 0
            if "[MUTED]" in out:
                muted = True

        name = "Microphone"
        default_src_name = run_cmd(["pactl", "get-default-source"])
        raw = run_cmd(["pactl", "-f", "json", "list", "sources"])
        if raw and default_src_name:
            try:
                srcs = json.loads(raw)
                for s in srcs:
                    if s.get("name") == default_src_name:
                        desc = s.get("description", "")
                        if desc:
                            name = SoundBackend.clean_device_name(desc, is_source=True)
                        break
            except Exception:
                pass
        return vol, muted, name

    @staticmethod
    def clean_device_name(raw_desc, is_source=False):
        if not raw_desc:
            return "Microphone" if is_source else "Speakers"
        desc = raw_desc
        if "Chipset Family" in desc or "Audio Controller" in desc or "High Definition Audio" in desc:
            parts = desc.split(")")
            if len(parts) > 1 and parts[-1].strip():
                desc = parts[-1].strip()
        desc = re.sub(r'\(HD Audio\)', '', desc).strip()
        if not desc:
            desc = raw_desc
        return desc

    @staticmethod
    def get_sinks():
        default_sink = run_cmd(["pactl", "get-default-sink"])
        wp_status = run_cmd(["wpctl", "status"])
        default_wp_id = None
        if wp_status:
            in_sinks = False
            for line in wp_status.splitlines():
                if "Sinks:" in line:
                    in_sinks = True
                    continue
                elif "Sources:" in line or "Filters:" in line:
                    in_sinks = False
                if in_sinks and "*" in line:
                    m = re.search(r'\*\s+(\d+)\.', line)
                    if m:
                        try:
                            default_wp_id = int(m.group(1))
                        except ValueError:
                            pass
                        break

        raw = run_cmd(["pactl", "-f", "json", "list", "sinks"])
        results = []
        seen_names = set()
        if raw:
            try:
                sinks = json.loads(raw)
                # Check if friendly HiFi sinks exist
                has_hifi = any(".HiFi__" in s.get("name", "") for s in sinks)
                for s in reversed(sinks):
                    name = s.get("name", "")
                    if has_hifi and (".pro-output-" in name or "pro_output" in name):
                        continue
                    idx = s.get("index")
                    desc = SoundBackend.clean_device_name(s.get("description", name))
                    is_def = (idx == default_wp_id) or (name == default_sink and default_wp_id is None)
                    if desc in seen_names and not is_def:
                        continue
                    seen_names.add(desc)

                    muted = s.get("mute", False)
                    vol = 0
                    vol_dict = s.get("volume", {})
                    for ch, ch_data in vol_dict.items():
                        if isinstance(ch_data, dict) and "value_percent" in ch_data:
                            try:
                                vol = int(ch_data["value_percent"].replace("%", ""))
                                break
                            except Exception:
                                pass
                    results.append({
                        "index": idx,
                        "name": name,
                        "description": desc,
                        "is_default": is_def,
                        "mute": muted,
                        "volume": vol
                    })
                results.reverse()
            except Exception:
                pass
        return results

    @staticmethod
    def get_sources():
        default_src = run_cmd(["pactl", "get-default-source"])
        wp_status = run_cmd(["wpctl", "status"])
        default_wp_src_id = None
        if wp_status:
            in_sources = False
            for line in wp_status.splitlines():
                if "Sources:" in line:
                    in_sources = True
                    continue
                elif "Filters:" in line or "Streams:" in line:
                    in_sources = False
                if in_sources and "*" in line:
                    m = re.search(r'\*\s+(\d+)\.', line)
                    if m:
                        try:
                            default_wp_src_id = int(m.group(1))
                        except ValueError:
                            pass
                        break

        raw = run_cmd(["pactl", "-f", "json", "list", "sources"])
        results = []
        seen_names = set()
        if raw:
            try:
                srcs = json.loads(raw)
                has_hifi = any(".HiFi__" in s.get("name", "") for s in srcs)
                for s in reversed(srcs):
                    name = s.get("name", "")
                    if name.endswith(".monitor"):
                        continue
                    if has_hifi and (".pro-input-" in name or "pro_input" in name):
                        continue
                    idx = s.get("index")
                    desc = SoundBackend.clean_device_name(s.get("description", name), is_source=True)
                    is_def = (idx == default_wp_src_id) or (name == default_src and default_wp_src_id is None)
                    if desc in seen_names and not is_def:
                        continue
                    seen_names.add(desc)

                    muted = s.get("mute", False)
                    vol = 0
                    vol_dict = s.get("volume", {})
                    for ch, ch_data in vol_dict.items():
                        if isinstance(ch_data, dict) and "value_percent" in ch_data:
                            try:
                                vol = int(ch_data["value_percent"].replace("%", ""))
                                break
                            except Exception:
                                pass
                    results.append({
                        "index": idx,
                        "name": name,
                        "description": desc,
                        "is_default": is_def,
                        "mute": muted,
                        "volume": vol
                    })
                results.reverse()
            except Exception:
                pass
        return results

    @staticmethod
    def get_sink_inputs():
        """Retrieve per-application playback audio streams."""
        raw = run_cmd(["pactl", "-f", "json", "list", "sink-inputs"])
        results = []
        if raw:
            try:
                inputs = json.loads(raw)
                for item in inputs:
                    idx = item.get("index")
                    props = item.get("properties", {})
                    app_name = (
                        props.get("application.name") or
                        props.get("media.name") or
                        props.get("node.name") or
                        f"Stream #{idx}"
                    )
                    binary = props.get("application.process.binary", "")
                    muted = item.get("mute", False)
                    vol = 0
                    vol_dict = item.get("volume", {})
                    for ch, ch_data in vol_dict.items():
                        if isinstance(ch_data, dict) and "value_percent" in ch_data:
                            try:
                                vol = int(ch_data["value_percent"].replace("%", ""))
                                break
                            except Exception:
                                pass
                    results.append({
                        "index": idx,
                        "app_name": app_name,
                        "binary": binary,
                        "mute": muted,
                        "volume": vol,
                        "sink": item.get("sink")
                    })
            except Exception:
                pass
        return results

    @staticmethod
    def set_sink_volume(target_percent, target_sink=None, notify=True):
        target = max(0, min(BOOST_MAX_VOLUME, target_percent))
        val_float = round(target / 100.0, 2)
        run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", str(val_float)])
        if target_sink:
            run_cmd(["wpctl", "set-volume", str(target_sink), str(val_float)])
            run_cmd(["pactl", "set-sink-volume", str(target_sink), f"{target}%"])
        run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target}%"])
        
        # Synchronize all sink instances asynchronously to keep GUI smooth
        def _sync_sinks():
            raw = run_cmd(["pactl", "-f", "json", "list", "sinks"])
            if raw:
                try:
                    sinks = json.loads(raw)
                    for s in sinks:
                        idx = s.get("index")
                        if idx is not None:
                            run_cmd(["wpctl", "set-volume", str(idx), str(val_float)])
                            run_cmd(["pactl", "set-sink-volume", str(idx), f"{target}%"])
                except Exception:
                    pass
        threading.Thread(target=_sync_sinks, daemon=True).start()

        if notify:
            SoundBackend.notify_sink()

    @staticmethod
    def change_sink_volume(delta, allow_boost=True):
        vol, muted, _ = SoundBackend.get_default_sink_info()
        if muted and delta > 0:
            SoundBackend.toggle_sink_mute(notify=False)
            vol, muted, _ = SoundBackend.get_default_sink_info()
        max_limit = BOOST_MAX_VOLUME if allow_boost else 100
        new_vol = max(0, min(max_limit, vol + delta))
        SoundBackend.set_sink_volume(new_vol, notify=True)

    @staticmethod
    def toggle_sink_mute(target_sink=None, notify=True):
        _, muted, _ = SoundBackend.get_default_sink_info()
        new_mute = "0" if muted else "1"
        new_mute_bool = not muted
        
        run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", new_mute])
        run_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if new_mute_bool else "0"])
        if target_sink:
            run_cmd(["wpctl", "set-mute", str(target_sink), new_mute])
            run_cmd(["pactl", "set-sink-mute", str(target_sink), "1" if new_mute_bool else "0"])

        def _sync_mute():
            raw = run_cmd(["pactl", "-f", "json", "list", "sinks"])
            if raw:
                try:
                    sinks = json.loads(raw)
                    for s in sinks:
                        idx = s.get("index")
                        if idx is not None:
                            run_cmd(["wpctl", "set-mute", str(idx), new_mute])
                            run_cmd(["pactl", "set-sink-mute", str(idx), "1" if new_mute_bool else "0"])
                except Exception:
                    pass
        threading.Thread(target=_sync_mute, daemon=True).start()

        if notify:
            SoundBackend.notify_sink()

    @staticmethod
    def set_source_volume(target_percent, target_source=None, notify=True):
        target = max(0, min(100, target_percent))
        val_float = round(target / 100.0, 2)
        run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", str(val_float)])
        if target_source:
            run_cmd(["wpctl", "set-volume", str(target_source), str(val_float)])
            run_cmd(["pactl", "set-source-volume", str(target_source), f"{target}%"])
        run_cmd(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{target}%"])
        
        def _sync_srcs():
            raw = run_cmd(["pactl", "-f", "json", "list", "sources"])
            if raw:
                try:
                    sources = json.loads(raw)
                    for s in sources:
                        idx = s.get("index")
                        if idx is not None:
                            run_cmd(["wpctl", "set-volume", str(idx), str(val_float)])
                            run_cmd(["pactl", "set-source-volume", str(idx), f"{target}%"])
                except Exception:
                    pass
        threading.Thread(target=_sync_srcs, daemon=True).start()

        if notify:
            SoundBackend.notify_source()

    @staticmethod
    def change_source_volume(delta):
        vol, muted, _ = SoundBackend.get_default_source_info()
        if muted and delta > 0:
            SoundBackend.toggle_source_mute(notify=False)
            vol, muted, _ = SoundBackend.get_default_source_info()
        new_vol = max(0, min(100, vol + delta))
        SoundBackend.set_source_volume(new_vol, notify=True)

    @staticmethod
    def toggle_source_mute(target_source=None, notify=True):
        _, muted, _ = SoundBackend.get_default_source_info()
        new_mute = "0" if muted else "1"
        new_mute_bool = not muted
        
        run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", new_mute])
        run_cmd(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "1" if new_mute_bool else "0"])
        if target_source:
            run_cmd(["wpctl", "set-mute", str(target_source), new_mute])
            run_cmd(["pactl", "set-source-mute", str(target_source), "1" if new_mute_bool else "0"])

        def _sync_src_mute():
            raw = run_cmd(["pactl", "-f", "json", "list", "sources"])
            if raw:
                try:
                    sources = json.loads(raw)
                    for s in sources:
                        idx = s.get("index")
                        if idx is not None:
                            run_cmd(["wpctl", "set-mute", str(idx), new_mute])
                            run_cmd(["pactl", "set-source-mute", str(idx), "1" if new_mute_bool else "0"])
                except Exception:
                    pass
        threading.Thread(target=_sync_src_mute, daemon=True).start()

        if notify:
            SoundBackend.notify_source()

    @staticmethod
    def set_default_sink(sink_name_or_id):
        # 1. Set default sink in PulseAudio server
        run_cmd(["pactl", "set-default-sink", str(sink_name_or_id)])
        
        # 2. Find wireplumber node id and set default in WirePlumber
        sinks = SoundBackend.get_sinks()
        target_idx = None
        for s in sinks:
            if s.get("name") == str(sink_name_or_id) or str(s.get("index")) == str(sink_name_or_id):
                target_idx = s.get("index")
                break
        if target_idx is not None:
            run_cmd(["wpctl", "set-default", str(target_idx)])
        elif str(sink_name_or_id).isdigit():
            run_cmd(["wpctl", "set-default", str(sink_name_or_id)])

        # 3. Move all active playback streams to the newly selected sink
        sink_inputs = SoundBackend.get_sink_inputs()
        for inp in sink_inputs:
            stream_idx = inp.get("index")
            if stream_idx is not None:
                run_cmd(["pactl", "move-sink-input", str(stream_idx), str(sink_name_or_id)])
                
        SoundBackend.notify_sink(title="🎧 Output Device Switched")

    @staticmethod
    def set_default_source(source_name_or_id):
        # 1. Set default source in PulseAudio server
        run_cmd(["pactl", "set-default-source", str(source_name_or_id)])
        
        # 2. Find wireplumber node id and set default in WirePlumber
        sources = SoundBackend.get_sources()
        target_idx = None
        for s in sources:
            if s.get("name") == str(source_name_or_id) or str(s.get("index")) == str(source_name_or_id):
                target_idx = s.get("index")
                break
        if target_idx is not None:
            run_cmd(["wpctl", "set-default", str(target_idx)])
        elif str(source_name_or_id).isdigit():
            run_cmd(["wpctl", "set-default", str(source_name_or_id)])

        # 3. Move all active recording streams to the new source
        raw_outputs = run_cmd(["pactl", "-f", "json", "list", "source-outputs"])
        if raw_outputs:
            try:
                outputs = json.loads(raw_outputs)
                for out_item in outputs:
                    s_idx = out_item.get("index")
                    if s_idx is not None:
                        run_cmd(["pactl", "move-source-output", str(s_idx), str(source_name_or_id)])
            except Exception:
                pass

        SoundBackend.notify_source(title="🎤 Input Device Switched")

    @staticmethod
    def set_app_volume(stream_idx, target_percent):
        target = max(0, min(150, target_percent))
        run_cmd(["pactl", "set-sink-input-volume", str(stream_idx), f"{target}%"])

    @staticmethod
    def toggle_app_mute(stream_idx):
        run_cmd(["pactl", "set-sink-input-mute", str(stream_idx), "toggle"])

    @staticmethod
    def play_test_sound():
        test_files = [
            "/usr/share/sounds/freedesktop/stereo/audio-channel-front-center.oga",
            "/usr/share/sounds/freedesktop/stereo/audio-test-signal.oga",
            "/usr/share/sounds/freedesktop/stereo/bell.oga"
        ]
        chosen = None
        for tf in test_files:
            if os.path.isfile(tf):
                chosen = tf
                break

        if chosen and shutil.which("paplay"):
            subprocess.Popen(["paplay", chosen])
        elif shutil.which("canberra-gtk-play"):
            subprocess.Popen(["canberra-gtk-play", "-i", "audio-volume-change"])
        elif shutil.which("pw-play") and chosen:
            subprocess.Popen(["pw-play", chosen])
        show_notification("🔊 Sound Test", "Playing audio channel test tone...", "audio-volume-high")

    @staticmethod
    def restart_audio_services():
        subprocess.run(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"])
        show_notification("🔄 Audio Services", "PipeWire & WirePlumber restarted successfully", "preferences-system")

    @staticmethod
    def notify_sink(title=None):
        vol, muted, name = SoundBackend.get_default_sink_info()
        bar = build_progress_bar(vol)
        if muted:
            show_notification(
                "🔇 Audio Output Muted",
                f"<b>{name}</b>\nVolume: {vol}% (Sound Off)",
                icon="audio-volume-muted",
                percentage=0,
                notif_id=SINK_NOTIF_ID,
                tag="volume_osd"
            )
        else:
            icon = "audio-volume-high" if vol > 66 else ("audio-volume-medium" if vol > 33 else "audio-volume-low")
            if vol == 0:
                icon = "audio-volume-muted"
            t = title or f"🔊 Output Volume: {vol}%"
            show_notification(
                t,
                f"<b>{name}</b>\n{bar}",
                icon=icon,
                percentage=vol,
                notif_id=SINK_NOTIF_ID,
                tag="volume_osd"
            )

    @staticmethod
    def notify_source(title=None):
        vol, muted, name = SoundBackend.get_default_source_info()
        bar = build_progress_bar(vol)
        if muted:
            show_notification(
                "🎤 Microphone Muted",
                f"<b>{name}</b>\nInput Muted",
                icon="microphone-sensitivity-muted",
                percentage=0,
                notif_id=SOURCE_NOTIF_ID,
                tag="mic_osd"
            )
        else:
            t = title or f"🎤 Mic Volume: {vol}%"
            show_notification(
                t,
                f"<b>{name}</b>\n{bar}",
                icon="audio-input-microphone",
                percentage=vol,
                notif_id=SOURCE_NOTIF_ID,
                tag="mic_osd"
            )


# =============================================================================
# SINGLETON TOGGLE HANDLER
# =============================================================================

def check_and_kill_existing():
    my_pid = os.getpid()
    try:
        out = subprocess.run(["pgrep", "-f", "sound-manager.py"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            pid = int(line.strip())
            if pid != my_pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
                sys.exit(0)
    except Exception:
        pass


# =============================================================================
# GTK3 LAYER SHELL GUI WITH DROPDOWNS & RANGE SLIDERS
# =============================================================================

def get_sound_theme_colors():
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

    for d in [Path.home() / ".config" / "theme", Path.home() / ".dotfiles" / ".config" / "theme"]:
        tfile = d / f"{theme_id}.json"
        if tfile.exists():
            try:
                with open(tfile, "r") as f:
                    tdata = json.load(f)
                    return tdata.get("colors", {}), tdata.get("type", "dark")
            except Exception:
                pass

    return {
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
        "accent": "#cba6f7", "blue": "#89b4fa", "green": "#a6e3a1",
        "yellow": "#f9e2af", "peach": "#fab387", "red": "#f38ba8",
        "mauve": "#cba6f7", "teal": "#94e2d5", "pink": "#f5c2e7",
    }, "dark"


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


def get_sound_gtk_css():
    c, ttype = get_sound_theme_colors()
    blue_fg = get_contrast_color(c.get("blue", "#89b4fa"))
    accent_fg = get_contrast_color(c.get("accent", "#cba6f7"))
    peach_fg = get_contrast_color(c.get("peach", "#fab387"))
    return f"""
* {{
    all: unset;
    font-family: 'Inter', 'Noto Sans', 'JetBrains Mono Nerd Font', 'JetBrains Mono', 'Ubuntu', sans-serif;
}}

window {{
    background-color: transparent;
}}

.main-card {{
    background-color: {c.get("mantle", "#181825")};
    border: 2px solid {c.get("accent", "#89b4fa")};
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65);
}}

.header-title {{
    font-size: 16px;
    font-weight: 900;
    color: {c.get("text", "#cdd6f4")};
}}

.header-icon {{
    font-size: 20px;
    color: {c.get("blue", "#89b4fa")};
    margin-right: 8px;
}}

.section-box {{
    background-color: {c.get("base", "#1e1e2e")};
    border: 1px solid {c.get("surface0", "#313244")};
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 10px;
}}

.section-label {{
    font-size: 12px;
    font-weight: 800;
    color: {c.get("blue", "#89b4fa")};
    margin-bottom: 6px;
}}

.section-label-mic {{
    color: {c.get("peach", "#fab387")};
}}

.section-label-apps {{
    color: {c.get("pink", "#f5c2e7")};
}}

/* Dropdown ComboBox Styling */
combobox {{
    background-color: {c.get("surface0", "#313244")};
    border: 1.5px solid {c.get("surface1", "#45475a")};
    border-radius: 10px;
    padding: 4px 10px;
    color: {c.get("text", "#ffffff")};
    font-size: 12px;
    font-weight: 700;
}}

combobox:hover {{
    border-color: {c.get("blue", "#89b4fa")};
    background-color: {c.get("surface1", "#45475a")};
}}

combobox button {{
    padding: 4px 6px;
    color: {c.get("text", "#cdd6f4")};
}}

combobox window, combobox menu {{
    background-color: {c.get("mantle", "#181825")};
    border: 1.5px solid {c.get("blue", "#89b4fa")};
    border-radius: 10px;
    color: {c.get("text", "#cdd6f4")};
    padding: 4px;
}}

combobox menu menuitem {{
    padding: 6px 10px;
    border-radius: 6px;
    color: {c.get("text", "#cdd6f4")};
    font-size: 12px;
}}

combobox menu menuitem:hover {{
    background-color: {c.get("blue", "#89b4fa")};
    color: {blue_fg};
    font-weight: 800;
}}

/* Range Select Sliders (GtkScale) */
scale {{
    margin: 8px 0px 4px 0px;
}}

scale trough {{
    background-color: {c.get("surface0", "#313244")};
    border-radius: 8px;
    min-height: 10px;
    min-width: 220px;
}}

scale highlight {{
    background: {c.get("blue", "#89b4fa")};
    border-radius: 8px;
    min-height: 10px;
}}

scale.mic-scale highlight {{
    background: {c.get("peach", "#fab387")};
}}

scale.app-scale highlight {{
    background: {c.get("accent", "#cba6f7")};
}}

scale slider {{
    background-color: {c.get("text", "#ffffff")};
    border: 2px solid {c.get("blue", "#89b4fa")};
    border-radius: 12px;
    min-width: 18px;
    min-height: 18px;
    margin: -4px 0px;
}}

scale slider:hover {{
    background-color: {c.get("accent", "#cba6f7")};
    border-color: {c.get("text", "#ffffff")};
}}

/* Value Badge */
.val-badge {{
    font-size: 13px;
    font-weight: 900;
    color: {c.get("blue", "#89b4fa")};
    min-width: 48px;
}}

.val-badge-mic {{
    color: {c.get("peach", "#fab387")};
}}

/* Buttons */
.btn-mute {{
    background-color: {c.get("surface0", "#313244")};
    border: 1.5px solid {c.get("surface1", "#45475a")};
    border-radius: 10px;
    padding: 6px 12px;
    color: {c.get("text", "#cdd6f4")};
    font-size: 14px;
    font-weight: 800;
}}

.btn-mute:hover {{
    background-color: {c.get("surface1", "#45475a")};
    border-color: {c.get("blue", "#89b4fa")};
}}

.btn-mute.is-muted {{
    background-color: rgba(243, 139, 168, 0.2);
    border: 1.5px solid {c.get("red", "#f38ba8")};
    color: {c.get("red", "#f38ba8")};
}}

/* Preset Buttons */
.btn-preset {{
    background-color: {c.get("base", "#1e1e2e")};
    border: 1px solid {c.get("surface1", "#45475a")};
    border-radius: 8px;
    padding: 4px 8px;
    color: {c.get("subtext0", "#a6adc8")};
    font-size: 11px;
    font-weight: 700;
    margin: 4px 2px 0px 2px;
}}

.btn-preset:hover {{
    background-color: {c.get("blue", "#89b4fa")};
    color: {blue_fg};
    border-color: {c.get("blue", "#89b4fa")};
}}

/* Action Toolbar Buttons */
.btn-action {{
    background-color: {c.get("surface0", "#313244")};
    border: 1px solid {c.get("surface1", "#45475a")};
    border-radius: 10px;
    padding: 6px 12px;
    color: {c.get("text", "#cdd6f4")};
    font-size: 11.5px;
    font-weight: 700;
}}

.btn-action:hover {{
    background-color: {c.get("surface1", "#45475a")};
    color: {c.get("text", "#ffffff")};
    border-color: {c.get("accent", "#cba6f7")};
}}

.app-row {{
    margin-top: 6px;
    padding: 4px 0px;
}}

.app-title {{
    font-size: 11.5px;
    font-weight: 700;
    color: {c.get("text", "#cdd6f4")};
    min-width: 120px;
}}
""".encode('utf-8')

def launch_gtk_gui():
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import Gtk, Gdk, GtkLayerShell, GLib

    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(get_sound_gtk_css())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    # 1. Fullscreen transparent backdrop for outside-click dismissal
    backdrop = Gtk.Window()
    backdrop.set_title("sound-control-backdrop")
    backdrop.set_decorated(False)
    backdrop.set_app_paintable(True)

    screen = backdrop.get_screen()
    visual = screen.get_rgba_visual()
    if visual:
        backdrop.set_visual(visual)

    GtkLayerShell.init_for_window(backdrop)
    GtkLayerShell.set_layer(backdrop, GtkLayerShell.Layer.TOP)
    GtkLayerShell.set_namespace(backdrop, "sound-control-backdrop")
    GtkLayerShell.set_keyboard_mode(backdrop, GtkLayerShell.KeyboardMode.NONE)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.BOTTOM, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.LEFT, True)
    GtkLayerShell.set_anchor(backdrop, GtkLayerShell.Edge.RIGHT, True)

    def on_draw_backdrop(widget, cr):
        cr.set_source_rgba(0, 0, 0, 0.001)
        cr.paint()
        return False

    backdrop.connect("draw", on_draw_backdrop)
    backdrop.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def dismiss(widget=None, event=None):
        Gtk.main_quit()
        return True

    backdrop.connect("button-press-event", dismiss)
    backdrop.show_all()

    # 2. Main Popup Window
    win = Gtk.Window()
    win.set_title("sound-control-popup")
    win.set_decorated(False)
    win.set_app_paintable(True)
    if visual:
        win.set_visual(visual)

    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
    GtkLayerShell.set_namespace(win, "sound-control-popup")
    GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.ON_DEMAND)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT, True)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 48)
    GtkLayerShell.set_margin(win, GtkLayerShell.Edge.RIGHT, 14)

    def on_key_press(widget, event):
        if event.keyval in [Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q]:
            Gtk.main_quit()
            return True
        return False

    win.connect("key-press-event", on_key_press)

    # Main Card
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    card.get_style_context().add_class("main-card")
    card.set_size_request(420, -1)

    # Header
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    h_icon = Gtk.Label(label="󰕾")
    h_icon.get_style_context().add_class("header-icon")
    h_title = Gtk.Label(label="Audio & Sound Manager")
    h_title.get_style_context().add_class("header-title")
    header_box.pack_start(h_icon, False, False, 0)
    header_box.pack_start(h_title, False, False, 0)
    card.pack_start(header_box, False, False, 0)

    # -------------------------------------------------------------
    # SECTION 1: MASTER OUTPUT (SINK) CONTROLS
    # -------------------------------------------------------------
    sink_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    sink_box.get_style_context().add_class("section-box")

    sink_lbl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    sink_lbl = Gtk.Label(label="󰕾 OUTPUT DEVICE & VOLUME")
    sink_lbl.get_style_context().add_class("section-label")
    sink_lbl_box.pack_start(sink_lbl, False, False, 0)
    sink_box.pack_start(sink_lbl_box, False, False, 0)

    # Dropdown for Output Sinks
    sinks = SoundBackend.get_sinks()
    sink_combo = Gtk.ComboBoxText()
    active_sink_idx = 0
    for i, s in enumerate(sinks):
        sink_combo.append(str(s["index"]), f"🎧 {s['description']}")
        if s["is_default"]:
            active_sink_idx = i

    if sinks:
        sink_combo.set_active(active_sink_idx)

    sink_box.pack_start(sink_combo, False, False, 0)

    # Range Slider & Mute Row
    sink_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    curr_vol, curr_muted, _ = SoundBackend.get_default_sink_info()

    sink_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, BOOST_MAX_VOLUME, 1)
    sink_scale.set_value(curr_vol)
    sink_scale.set_draw_value(False)
    sink_scale.set_hexpand(True)

    sink_val_lbl = Gtk.Label(label=f"{curr_vol}%")
    sink_val_lbl.get_style_context().add_class("val-badge")

    sink_mute_btn = Gtk.Button(label="󰝟" if curr_muted else "󰕾")
    sink_mute_btn.get_style_context().add_class("btn-mute")
    if curr_muted:
        sink_mute_btn.get_style_context().add_class("is-muted")

    def update_sink_ui(vol, muted):
        sink_scale.set_value(vol)
        sink_val_lbl.set_text(f"{vol}%")
        sink_mute_btn.set_label("󰝟" if muted else "󰕾")
        if muted:
            sink_mute_btn.get_style_context().add_class("is-muted")
        else:
            sink_mute_btn.get_style_context().remove_class("is-muted")

    # State flag to prevent recursive updates
    updating_sink = False

    def on_sink_scale_changed(scale):
        nonlocal updating_sink
        if updating_sink:
            return
        val = int(scale.get_value())
        sink_val_lbl.set_text(f"{val}%")
        target_sink = sink_combo.get_active_id()
        SoundBackend.set_sink_volume(val, target_sink=target_sink, notify=False)

    sink_scale.connect("value-changed", on_sink_scale_changed)

    def on_sink_mute_clicked(btn):
        target_sink = sink_combo.get_active_id()
        SoundBackend.toggle_sink_mute(target_sink=target_sink, notify=False)
        v, m, _ = SoundBackend.get_default_sink_info()
        update_sink_ui(v, m)

    sink_mute_btn.connect("clicked", on_sink_mute_clicked)

    def on_sink_combo_changed(combo):
        nonlocal updating_sink
        target_sink = combo.get_active_id()
        if target_sink:
            SoundBackend.set_default_sink(target_sink)
            time.sleep(0.05)
            v, m, _ = SoundBackend.get_default_sink_info()
            updating_sink = True
            update_sink_ui(v, m)
            updating_sink = False

    sink_combo.connect("changed", on_sink_combo_changed)

    sink_row.pack_start(sink_mute_btn, False, False, 0)
    sink_row.pack_start(sink_scale, True, True, 0)
    sink_row.pack_start(sink_val_lbl, False, False, 0)
    sink_box.pack_start(sink_row, False, False, 0)

    # Preset Volume Buttons Row
    presets_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    for p_val, p_lbl in [(20, "20%"), (50, "50%"), (80, "80%"), (100, "100%"), (150, "150% 🚀")]:
        p_btn = Gtk.Button(label=p_lbl)
        p_btn.get_style_context().add_class("btn-preset")
        p_btn.set_hexpand(True)
        def make_preset_cb(v):
            return lambda b: (SoundBackend.set_sink_volume(v, target_sink=sink_combo.get_active_id(), notify=False), update_sink_ui(v, False))
        p_btn.connect("clicked", make_preset_cb(p_val))
        presets_row.pack_start(p_btn, True, True, 0)

    sink_box.pack_start(presets_row, False, False, 0)
    card.pack_start(sink_box, False, False, 0)

    # -------------------------------------------------------------
    # SECTION 2: MASTER INPUT (MICROPHONE) CONTROLS
    # -------------------------------------------------------------
    src_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    src_box.get_style_context().add_class("section-box")

    src_lbl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    src_lbl = Gtk.Label(label="󰍬 INPUT DEVICE & MICROPHONE")
    src_lbl.get_style_context().add_class("section-label")
    src_lbl.get_style_context().add_class("section-label-mic")
    src_lbl_box.pack_start(src_lbl, False, False, 0)
    src_box.pack_start(src_lbl_box, False, False, 0)

    # Dropdown for Input Sources
    sources = SoundBackend.get_sources()
    src_combo = Gtk.ComboBoxText()
    active_src_idx = 0
    for i, s in enumerate(sources):
        src_combo.append(str(s["index"]), f"🎙️ {s['description']}")
        if s["is_default"]:
            active_src_idx = i

    if sources:
        src_combo.set_active(active_src_idx)

    src_box.pack_start(src_combo, False, False, 0)

    # Mic Range Slider & Mute Row
    src_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    mic_vol, mic_muted, _ = SoundBackend.get_default_source_info()

    src_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
    src_scale.set_value(mic_vol)
    src_scale.set_draw_value(False)
    src_scale.set_hexpand(True)
    src_scale.get_style_context().add_class("mic-scale")

    src_val_lbl = Gtk.Label(label=f"{mic_vol}%")
    src_val_lbl.get_style_context().add_class("val-badge")
    src_val_lbl.get_style_context().add_class("val-badge-mic")

    src_mute_btn = Gtk.Button(label="󰍭" if mic_muted else "󰍬")
    src_mute_btn.get_style_context().add_class("btn-mute")
    if mic_muted:
        src_mute_btn.get_style_context().add_class("is-muted")

    def update_source_ui(vol, muted):
        src_scale.set_value(vol)
        src_val_lbl.set_text(f"{vol}%")
        src_mute_btn.set_label("󰍭" if muted else "󰍬")
        if muted:
            src_mute_btn.get_style_context().add_class("is-muted")
        else:
            src_mute_btn.get_style_context().remove_class("is-muted")

    updating_source = False

    def on_src_scale_changed(scale):
        nonlocal updating_source
        if updating_source:
            return
        val = int(scale.get_value())
        src_val_lbl.set_text(f"{val}%")
        target_src = src_combo.get_active_id()
        SoundBackend.set_source_volume(val, target_source=target_src, notify=False)

    src_scale.connect("value-changed", on_src_scale_changed)

    def on_src_mute_clicked(btn):
        target_src = src_combo.get_active_id()
        SoundBackend.toggle_source_mute(target_source=target_src, notify=False)
        v, m, _ = SoundBackend.get_default_source_info()
        update_source_ui(v, m)

    src_mute_btn.connect("clicked", on_src_mute_clicked)

    def on_src_combo_changed(combo):
        nonlocal updating_source
        target_src = combo.get_active_id()
        if target_src:
            SoundBackend.set_default_source(target_src)
            time.sleep(0.05)
            v, m, _ = SoundBackend.get_default_source_info()
            updating_source = True
            update_source_ui(v, m)
            updating_source = False

    src_combo.connect("changed", on_src_combo_changed)

    src_row.pack_start(src_mute_btn, False, False, 0)
    src_row.pack_start(src_scale, True, True, 0)
    src_row.pack_start(src_val_lbl, False, False, 0)
    src_box.pack_start(src_row, False, False, 0)

    card.pack_start(src_box, False, False, 0)

    # -------------------------------------------------------------
    # SECTION 3: APPLICATION VOLUME STREAMS (IF ANY ACTIVE)
    # -------------------------------------------------------------
    apps = SoundBackend.get_sink_inputs()
    if apps:
        app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        app_box.get_style_context().add_class("section-box")

        app_header = Gtk.Label(label="󰓓 APPLICATION STREAMS")
        app_header.get_style_context().add_class("section-label")
        app_header.get_style_context().add_class("section-label-apps")
        app_header.set_xalign(0)
        app_box.pack_start(app_header, False, False, 0)

        for app in apps:
            app_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            app_row.get_style_context().add_class("app-row")

            app_title = Gtk.Label(label=f"󰓓 {app['app_name'][:18]}")
            app_title.get_style_context().add_class("app-title")
            app_title.set_xalign(0)

            app_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 150, 1)
            app_scale.set_value(app["volume"])
            app_scale.set_draw_value(False)
            app_scale.set_hexpand(True)
            app_scale.get_style_context().add_class("app-scale")

            app_val = Gtk.Label(label=f"{app['volume']}%")
            app_val.get_style_context().add_class("val-badge")

            app_mute = Gtk.Button(label="󰝟" if app["mute"] else "󰕾")
            app_mute.get_style_context().add_class("btn-mute")
            if app["mute"]:
                app_mute.get_style_context().add_class("is-muted")

            def make_app_callbacks(stream_id, v_lbl, m_btn):
                def on_app_vol_change(sc):
                    val = int(sc.get_value())
                    v_lbl.set_text(f"{val}%")
                    SoundBackend.set_app_volume(stream_id, val)

                def on_app_mute(b):
                    SoundBackend.toggle_app_mute(stream_id)
                    time.sleep(0.02)
                    cur_apps = SoundBackend.get_sink_inputs()
                    for a in cur_apps:
                        if a["index"] == stream_id:
                            m_btn.set_label("󰝟" if a["mute"] else "󰕾")
                            if a["mute"]:
                                m_btn.get_style_context().add_class("is-muted")
                            else:
                                m_btn.get_style_context().remove_class("is-muted")
                            break
                return on_app_vol_change, on_app_mute

            app_cb_vol, app_cb_mute = make_app_callbacks(app["index"], app_val, app_mute)
            app_scale.connect("value-changed", app_cb_vol)
            app_mute.connect("clicked", app_cb_mute)

            app_row.pack_start(app_title, False, False, 0)
            app_row.pack_start(app_mute, False, False, 0)
            app_row.pack_start(app_scale, True, True, 0)
            app_row.pack_start(app_val, False, False, 0)
            app_box.pack_start(app_row, False, False, 0)

        card.pack_start(app_box, False, False, 0)

    # -------------------------------------------------------------
    # SECTION 4: ACTION TOOLBAR
    # -------------------------------------------------------------
    actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    actions_box.set_margin_top(12)

    test_btn = Gtk.Button(label="󰋋 Test Audio")
    test_btn.get_style_context().add_class("btn-action")
    test_btn.set_hexpand(True)
    test_btn.connect("clicked", lambda b: SoundBackend.play_test_sound())

    restart_btn = Gtk.Button(label="🔄 Restart PipeWire")
    restart_btn.get_style_context().add_class("btn-action")
    restart_btn.set_hexpand(True)
    restart_btn.connect("clicked", lambda b: SoundBackend.restart_audio_services())

    tui_btn = Gtk.Button(label="🎛️ Terminal TUI")
    tui_btn.get_style_context().add_class("btn-action")
    tui_btn.set_hexpand(True)
    def on_tui_click(b):
        Gtk.main_quit()
        subprocess.Popen([
            "kitty",
            "--class=soundctl-floating",
            "-e",
            sys.executable,
            os.path.abspath(__file__),
            "--tui"
        ])
    tui_btn.connect("clicked", on_tui_click)

    actions_box.pack_start(test_btn, True, True, 0)
    actions_box.pack_start(restart_btn, True, True, 0)
    actions_box.pack_start(tui_btn, True, True, 0)

    card.pack_start(actions_box, False, False, 0)

    win.add(card)
    win.show_all()
    Gtk.main()


# =============================================================================
# CURSES TUI SOUND MIXER (--tui)
# =============================================================================

class SoundMixerTUI:
    def __init__(self, stdscr):
        import curses
        self.curses = curses
        self.stdscr = stdscr
        self.running = True
        self.selected_idx = 0
        self.items = []

    def init_colors(self):
        self.curses.start_color()
        self.curses.use_default_colors()
        self.curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(500)

        self.curses.init_pair(1, self.curses.COLOR_MAGENTA, -1)
        self.curses.init_pair(2, self.curses.COLOR_CYAN, -1)
        self.curses.init_pair(3, self.curses.COLOR_GREEN, -1)
        self.curses.init_pair(4, self.curses.COLOR_YELLOW, -1)
        self.curses.init_pair(5, self.curses.COLOR_RED, -1)
        self.curses.init_pair(6, self.curses.COLOR_BLACK, self.curses.COLOR_CYAN)

    def refresh_data(self):
        vol, sink_muted, sink_name = SoundBackend.get_default_sink_info()
        mic_vol, mic_muted, mic_name = SoundBackend.get_default_source_info()
        sinks = SoundBackend.get_sinks()
        sources = SoundBackend.get_sources()
        apps = SoundBackend.get_sink_inputs()

        new_items = [
            {
                "type": "master_sink",
                "name": f"Master Output: {sink_name}",
                "volume": vol,
                "mute": sink_muted,
                "id": "@DEFAULT_AUDIO_SINK@"
            },
            {
                "type": "master_source",
                "name": f"Master Microphone: {mic_name}",
                "volume": mic_vol,
                "mute": mic_muted,
                "id": "@DEFAULT_AUDIO_SOURCE@"
            }
        ]

        for s in sinks:
            new_items.append({
                "type": "sink_device",
                "name": s["description"],
                "raw_name": s["name"],
                "is_default": s["is_default"],
                "volume": s["volume"],
                "mute": s["mute"],
                "id": s["name"]
            })

        for s in sources:
            new_items.append({
                "type": "source_device",
                "name": s["description"],
                "raw_name": s["name"],
                "is_default": s["is_default"],
                "volume": s["volume"],
                "mute": s["mute"],
                "id": s["name"]
            })

        for app in apps:
            new_items.append({
                "type": "app_stream",
                "name": f"App: {app['app_name']}",
                "volume": app["volume"],
                "mute": app["mute"],
                "id": app["index"]
            })

        self.items = new_items
        if self.selected_idx >= len(self.items):
            self.selected_idx = max(0, len(self.items) - 1)

    def draw_slider(self, volume, muted, width=24):
        pct = max(0, min(150, volume))
        filled = int(round((min(100, pct) / 100.0) * width))
        empty = width - filled
        bar = "█" * filled + "░" * empty
        if muted:
            return f"[{bar}]  0% [MUTED]"
        return f"[{bar}] {pct:>3}%"

    def render(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        if h < 14 or w < 60:
            self.stdscr.addstr(0, 0, "Terminal window too small for Sound Mixer!", self.curses.color_pair(5))
            self.stdscr.refresh()
            return

        header_text = "  󰕾 SOUND CONTROL CENTER & AUDIO MIXER  "
        self.stdscr.addstr(1, max(2, (w - len(header_text)) // 2), header_text, self.curses.color_pair(1) | self.curses.A_BOLD)

        sub_text = "PipeWire / WirePlumber High-Fidelity Audio Control"
        self.stdscr.addstr(2, max(2, (w - len(sub_text)) // 2), sub_text, self.curses.A_DIM)
        self.stdscr.addstr(3, 2, "─" * (w - 4), self.curses.A_DIM)

        curr_y = 4
        prev_type = None

        for idx, item in enumerate(self.items):
            if curr_y >= h - 4:
                break

            if item["type"] != prev_type:
                if item["type"] == "sink_device":
                    self.stdscr.addstr(curr_y, 2, "─── [ OUTPUT DEVICES ] " + "─" * max(0, w - 27), self.curses.color_pair(2) | self.curses.A_BOLD)
                    curr_y += 1
                elif item["type"] == "source_device":
                    self.stdscr.addstr(curr_y, 2, "─── [ INPUT DEVICES ] " + "─" * max(0, w - 26), self.curses.color_pair(4) | self.curses.A_BOLD)
                    curr_y += 1
                elif item["type"] == "app_stream":
                    self.stdscr.addstr(curr_y, 2, "─── [ APPLICATION STREAMS ] " + "─" * max(0, w - 30), self.curses.color_pair(1) | self.curses.A_BOLD)
                    curr_y += 1
                prev_type = item["type"]

            is_sel = (idx == self.selected_idx)
            cursor = " ➜ " if is_sel else "   "

            prefix = ""
            if item.get("is_default"):
                prefix = "● "
            elif item["type"] in ["sink_device", "source_device"]:
                prefix = "○ "

            name = item["name"]
            max_name_len = max(15, w - 45)
            if len(name) > max_name_len:
                name = name[:max_name_len-3] + "..."

            slider = self.draw_slider(item["volume"], item["mute"], width=max(12, min(24, w - max_name_len - 30)))
            line = f"{cursor}{prefix}{name:<{max_name_len}} {slider}"[:w - 2]

            attr = self.curses.A_NORMAL
            if is_sel:
                attr = self.curses.color_pair(6) | self.curses.A_BOLD
            elif item["mute"]:
                attr = self.curses.color_pair(5)
            elif item.get("is_default"):
                attr = self.curses.color_pair(3) | self.curses.A_BOLD
            elif item["type"] == "master_sink":
                attr = self.curses.color_pair(2) | self.curses.A_BOLD
            elif item["type"] == "master_source":
                attr = self.curses.color_pair(4) | self.curses.A_BOLD

            try:
                self.stdscr.addstr(curr_y, 2, line, attr)
            except self.curses.error:
                pass
            curr_y += 1

        footer_y = h - 2
        self.stdscr.addstr(footer_y - 1, 2, "─" * (w - 4), self.curses.A_DIM)
        footer_keys = "[↑/↓] Navigate  [←/→] Vol ±5%  [m] Mute  [Enter/Space] Set Default  [t] Test Tone  [r] Restart  [q] Quit"
        self.stdscr.addstr(footer_y, max(2, (w - len(footer_keys)) // 2), footer_keys[:w-4], self.curses.color_pair(1))
        self.stdscr.refresh()

    def handle_input(self, key):
        if key in [ord('q'), ord('Q'), 27]:
            self.running = False
            return

        if not self.items:
            return

        sel = self.items[self.selected_idx]

        if key in [self.curses.KEY_UP, ord('k'), ord('K')]:
            self.selected_idx = (self.selected_idx - 1) % len(self.items)
        elif key in [self.curses.KEY_DOWN, ord('j'), ord('J'), 9]:
            self.selected_idx = (self.selected_idx + 1) % len(self.items)
        elif key in [self.curses.KEY_RIGHT, ord('l'), ord('+'), ord('=')]:
            if sel["type"] == "master_sink":
                SoundBackend.change_sink_volume(5)
            elif sel["type"] == "master_source":
                SoundBackend.change_source_volume(5)
            elif sel["type"] == "sink_device":
                run_cmd(["pactl", "set-sink-volume", sel["raw_name"], "+5%"])
            elif sel["type"] == "source_device":
                run_cmd(["pactl", "set-source-volume", sel["raw_name"], "+5%"])
            elif sel["type"] == "app_stream":
                run_cmd(["pactl", "set-sink-input-volume", str(sel["id"]), "+5%"])
        elif key in [self.curses.KEY_LEFT, ord('h'), ord('-')]:
            if sel["type"] == "master_sink":
                SoundBackend.change_sink_volume(-5)
            elif sel["type"] == "master_source":
                SoundBackend.change_source_volume(-5)
            elif sel["type"] == "sink_device":
                run_cmd(["pactl", "set-sink-volume", sel["raw_name"], "-5%"])
            elif sel["type"] == "source_device":
                run_cmd(["pactl", "set-source-volume", sel["raw_name"], "-5%"])
            elif sel["type"] == "app_stream":
                run_cmd(["pactl", "set-sink-input-volume", str(sel["id"]), "-5%"])
        elif key in [ord('m'), ord('M')]:
            if sel["type"] == "master_sink":
                SoundBackend.toggle_sink_mute()
            elif sel["type"] == "master_source":
                SoundBackend.toggle_source_mute()
            elif sel["type"] == "sink_device":
                run_cmd(["pactl", "set-sink-mute", sel["raw_name"], "toggle"])
            elif sel["type"] == "source_device":
                run_cmd(["pactl", "set-source-mute", sel["raw_name"], "toggle"])
            elif sel["type"] == "app_stream":
                SoundBackend.toggle_app_mute(sel["id"])
        elif key in [10, 13, ord(' ')]:
            if sel["type"] == "sink_device":
                SoundBackend.set_default_sink(sel["raw_name"])
            elif sel["type"] == "source_device":
                SoundBackend.set_default_source(sel["raw_name"])
            elif sel["type"] == "master_sink":
                SoundBackend.toggle_sink_mute()
            elif sel["type"] == "master_source":
                SoundBackend.toggle_source_mute()
        elif key in [ord('t'), ord('T')]:
            SoundBackend.play_test_sound()
        elif key in [ord('r'), ord('R')]:
            SoundBackend.restart_audio_services()

    def run(self):
        self.init_colors()
        while self.running:
            self.refresh_data()
            self.render()
            try:
                ch = self.stdscr.getch()
                if ch != -1:
                    self.handle_input(ch)
            except Exception:
                pass


def run_tui():
    import curses
    curses.wrapper(lambda stdscr: SoundMixerTUI(stdscr).run())


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    if "--tui" in sys.argv or "-t" in sys.argv:
        run_tui()
        return

    if "--toggle-mute" in sys.argv or "mute" in sys.argv:
        SoundBackend.toggle_sink_mute()
        return

    if "--toggle-mic" in sys.argv or "mic-mute" in sys.argv:
        SoundBackend.toggle_source_mute()
        return

    if "--up" in sys.argv or "up" in sys.argv:
        SoundBackend.change_sink_volume(DEFAULT_STEP)
        return

    if "--down" in sys.argv or "down" in sys.argv:
        SoundBackend.change_sink_volume(-DEFAULT_STEP)
        return

    if "--test" in sys.argv:
        SoundBackend.play_test_sound()
        return

    if "--restart" in sys.argv:
        SoundBackend.restart_audio_services()
        return

    # Check and toggle existing popup if already open
    check_and_kill_existing()

    try:
        launch_gtk_gui()
    except Exception as e:
        # Fallback to TUI or notification
        show_notification("Audio Manager", f"Starting in TUI mode ({e})", "preferences-system")
        subprocess.Popen([
            "kitty",
            "--class=soundctl-floating",
            "-e",
            sys.executable,
            os.path.abspath(__file__),
            "--tui"
        ])

if __name__ == "__main__":
    main()
