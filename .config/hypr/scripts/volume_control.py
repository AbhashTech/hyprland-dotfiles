#!/usr/bin/env python3
"""
Hyprland Audio & Volume Control Utility with OSD & Interactive Menu
Manages speaker/mic volume, mute states, and output/input audio device switching.
"""

import sys
import json
import subprocess
import os
import shutil
import re

SINK_NOTIF_ID = "9122"
SOURCE_NOTIF_ID = "9123"
DEFAULT_STEP = 5
MAX_VOLUME = 100  # Default cap for standard adjustments (can be boosted up to 150%)
BOOST_MAX_VOLUME = 150

def run_cmd(cmd):
    """Run a shell command and return stdout as string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return None

def build_progress_bar(percentage, length=12):
    """Generate a visual ASCII progress bar."""
    pct = max(0, min(100, percentage))
    filled = int(round((pct / 100.0) * length))
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}]"

def show_notification(title, body, icon, percentage=None, notif_id=SINK_NOTIF_ID, tag="volume_osd"):
    """Send an on-screen display (OSD) notification via notify-send."""
    cmd = [
        "notify-send",
        "-r", str(notif_id),
        "-t", "1200",
        "-u", "low",
        "-a", "VolumeControl",
        "-c", "osd",
        "-i", icon,
        "-h", f"string:x-canonical-private-synchronous:{tag}",
        "-h", "boolean:transient:true",
        "-h", "boolean:history-ignore:true"
    ]
    if percentage is not None:
        cmd.extend(["-h", f"int:value:{int(percentage)}"])
    
    cmd.extend([title, body])
    run_cmd(cmd)

# ---------------------------------------------------------
# Audio Sink (Speaker / Headphones) Operations
# ---------------------------------------------------------

import threading

def get_sink_info():
    """Retrieve volume, mute status, and device name for the default sink."""
    out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    vol_pct = 0
    muted = False
    if out:
        parts = out.strip().split()
        if len(parts) >= 2:
            try:
                vol_pct = int(round(float(parts[1]) * 100))
            except ValueError:
                vol_pct = 0
        if "[MUTED]" in out:
            muted = True

    sink_name = "Speakers / Output"
    return vol_pct, muted, sink_name

def notify_sink_osd(vol=None, muted=None, name="Speakers / Output"):
    """Show OSD notification for sink volume status."""
    if vol is None or muted is None:
        vol, muted, name = get_sink_info()
    bar = build_progress_bar(vol)
    
    if muted:
        icon = "audio-volume-muted"
        title = "🔇 Muted"
        body = f"<b>{name}</b>\nVolume: {vol}% (Sound Off)"
        show_notification(title, body, icon, percentage=0, notif_id=SINK_NOTIF_ID, tag="volume_osd")
    else:
        if vol == 0:
            icon = "audio-volume-muted"
        elif vol <= 33:
            icon = "audio-volume-low"
        elif vol <= 66:
            icon = "audio-volume-medium"
        elif vol <= 100:
            icon = "audio-volume-high"
        else:
            icon = "audio-volume-overamplified"

        title = f"🔊 Volume: {vol}%"
        body = f"<b>{name}</b>\n{bar}"
        show_notification(title, body, icon, percentage=vol, notif_id=SINK_NOTIF_ID, tag="volume_osd")

def _sync_all_sinks_async(val_float, target_percent):
    def _worker():
        raw_sinks = run_cmd(["pactl", "-f", "json", "list", "sinks"])
        if raw_sinks:
            try:
                sinks = json.loads(raw_sinks)
                for s in sinks:
                    idx = s.get("index")
                    if idx is not None:
                        run_cmd(["wpctl", "set-volume", str(idx), str(val_float)])
                        run_cmd(["pactl", "set-sink-volume", str(idx), f"{target_percent}%"])
            except Exception:
                pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def _sync_all_mute_async(new_mute, new_mute_bool):
    def _worker():
        raw_sinks = run_cmd(["pactl", "-f", "json", "list", "sinks"])
        if raw_sinks:
            try:
                sinks = json.loads(raw_sinks)
                for s in sinks:
                    idx = s.get("index")
                    if idx is not None:
                        run_cmd(["wpctl", "set-mute", str(idx), new_mute])
                        run_cmd(["pactl", "set-sink-mute", str(idx), "1" if new_mute_bool else "0"])
            except Exception:
                pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def change_sink_volume(delta, allow_boost=False):
    """Adjust sink volume by delta percentage."""
    curr_vol, muted, _ = get_sink_info()
    if muted and delta > 0:
        run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
        run_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"])
        _sync_all_mute_async("0", False)
        muted = False

    max_cap = BOOST_MAX_VOLUME if allow_boost else MAX_VOLUME
    new_vol = max(0, min(max_cap, curr_vol + delta))
    set_sink_volume(new_vol, muted=muted)

def set_sink_volume(target_percent, muted=False):
    """Set exact sink volume percentage across all active sink nodes."""
    target_percent = max(0, min(BOOST_MAX_VOLUME, target_percent))
    val_float = round(target_percent / 100.0, 2)
    run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", str(val_float)])
    run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target_percent}%"])
    _sync_all_sinks_async(val_float, target_percent)
    notify_sink_osd(vol=target_percent, muted=muted)

def toggle_sink_mute():
    """Toggle mute for default sink across all node instances."""
    curr_vol, muted, _ = get_sink_info()
    new_mute = "0" if muted else "1"
    new_mute_bool = not muted
    
    run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", new_mute])
    run_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if new_mute_bool else "0"])
    _sync_all_mute_async(new_mute, new_mute_bool)
    notify_sink_osd(vol=curr_vol, muted=new_mute_bool)

# ---------------------------------------------------------
# Audio Source (Microphone) Operations
# ---------------------------------------------------------

def get_source_info():
    """Retrieve volume, mute status, and device name for the default source."""
    out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])
    vol_pct = 0
    muted = False
    if out:
        parts = out.strip().split()
        if len(parts) >= 2:
            try:
                vol_pct = int(round(float(parts[1]) * 100))
            except ValueError:
                vol_pct = 0
        if "[MUTED]" in out:
            muted = True

    source_name = "Microphone"
    return vol_pct, muted, source_name

def notify_source_osd(vol=None, muted=None, name="Microphone"):
    """Show OSD notification for microphone volume & mute status."""
    if vol is None or muted is None:
        vol, muted, name = get_source_info()
    bar = build_progress_bar(vol)

    if muted:
        icon = "microphone-sensitivity-muted"
        title = "🎤 Microphone Muted"
        body = f"<b>{name}</b>\nInput Muted"
        show_notification(title, body, icon, percentage=0, notif_id=SOURCE_NOTIF_ID, tag="mic_osd")
    else:
        icon = "audio-input-microphone"
        title = f"🎤 Mic Volume: {vol}%"
        body = f"<b>{name}</b>\n{bar}"
        show_notification(title, body, icon, percentage=vol, notif_id=SOURCE_NOTIF_ID, tag="mic_osd")

def _sync_all_sources_async(val_float, target_percent):
    def _worker():
        raw_srcs = run_cmd(["pactl", "-f", "json", "list", "sources"])
        if raw_srcs:
            try:
                sources = json.loads(raw_srcs)
                for s in sources:
                    idx = s.get("index")
                    if idx is not None:
                        run_cmd(["wpctl", "set-volume", str(idx), str(val_float)])
                        run_cmd(["pactl", "set-source-volume", str(idx), f"{target_percent}%"])
            except Exception:
                pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def _sync_all_source_mute_async(new_mute, new_mute_bool):
    def _worker():
        raw_srcs = run_cmd(["pactl", "-f", "json", "list", "sources"])
        if raw_srcs:
            try:
                sources = json.loads(raw_srcs)
                for s in sources:
                    idx = s.get("index")
                    if idx is not None:
                        run_cmd(["wpctl", "set-mute", str(idx), new_mute])
                        run_cmd(["pactl", "set-source-mute", str(idx), "1" if new_mute_bool else "0"])
            except Exception:
                pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def change_source_volume(delta):
    """Adjust mic volume by delta percentage."""
    curr_vol, muted, _ = get_source_info()
    if muted and delta > 0:
        run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "0"])
        run_cmd(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0"])
        _sync_all_source_mute_async("0", False)
        muted = False

    new_vol = max(0, min(100, curr_vol + delta))
    set_source_volume(new_vol, muted=muted)

def set_source_volume(target_percent, muted=False):
    """Set exact mic volume percentage across all source instances."""
    target_percent = max(0, min(100, target_percent))
    val_float = round(target_percent / 100.0, 2)
    run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", str(val_float)])
    run_cmd(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{target_percent}%"])
    _sync_all_sources_async(val_float, target_percent)
    notify_source_osd(vol=target_percent, muted=muted)

def toggle_source_mute():
    """Toggle mute for default microphone across all instances."""
    curr_vol, muted, _ = get_source_info()
    new_mute = "0" if muted else "1"
    new_mute_bool = not muted
    
    run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", new_mute])
    run_cmd(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "1" if new_mute_bool else "0"])
    _sync_all_source_mute_async(new_mute, new_mute_bool)
    notify_source_osd(vol=curr_vol, muted=new_mute_bool)

# ---------------------------------------------------------
# Audio Devices (Sinks / Sources) Listing & Switching
# ---------------------------------------------------------

def get_sinks_list():
    """Return a list of available audio sink devices."""
    default_sink = run_cmd(["pactl", "get-default-sink"])
    raw_sinks = run_cmd(["pactl", "-f", "json", "list", "sinks"])
    results = []
    if raw_sinks:
        try:
            sinks = json.loads(raw_sinks)
            for s in sinks:
                name = s.get("name")
                desc = s.get("description", name)
                idx = s.get("index")
                is_default = (name == default_sink)
                results.append({
                    "index": idx,
                    "name": name,
                    "description": desc,
                    "is_default": is_default,
                    "mute": s.get("mute", False)
                })
        except Exception:
            pass
    return results

def get_sources_list():
    """Return a list of available audio input source devices (excluding monitors)."""
    default_src = run_cmd(["pactl", "get-default-source"])
    raw_srcs = run_cmd(["pactl", "-f", "json", "list", "sources"])
    results = []
    if raw_srcs:
        try:
            srcs = json.loads(raw_srcs)
            for s in srcs:
                name = s.get("name", "")
                if name.endswith(".monitor"):
                    continue
                desc = s.get("description", name)
                idx = s.get("index")
                is_default = (name == default_src)
                results.append({
                    "index": idx,
                    "name": name,
                    "description": desc,
                    "is_default": is_default,
                    "mute": s.get("mute", False)
                })
        except Exception:
            pass
    return results

def set_default_sink(sink_id_or_name):
    """Set the system default audio sink and migrate active playback streams."""
    run_cmd(["pactl", "set-default-sink", str(sink_id_or_name)])
    
    # Set WirePlumber default node
    sinks = get_sinks_list()
    target_idx = None
    for s in sinks:
        if s.get("name") == str(sink_id_or_name) or str(s.get("index")) == str(sink_id_or_name):
            target_idx = s.get("index")
            break
    if target_idx is not None:
        run_cmd(["wpctl", "set-default", str(target_idx)])
    elif str(sink_id_or_name).isdigit():
        run_cmd(["wpctl", "set-default", str(sink_id_or_name)])

    # Move active playback streams to new sink
    raw_inputs = run_cmd(["pactl", "-f", "json", "list", "sink-inputs"])
    if raw_inputs:
        try:
            inputs = json.loads(raw_inputs)
            for inp in inputs:
                idx = inp.get("index")
                if idx is not None:
                    run_cmd(["pactl", "move-sink-input", str(idx), str(sink_id_or_name)])
        except Exception:
            pass

    notify_sink_osd()

def set_default_source(source_id_or_name):
    """Set the system default audio source and migrate active recording streams."""
    run_cmd(["pactl", "set-default-source", str(source_id_or_name)])
    
    # Set WirePlumber default node
    sources = get_sources_list()
    target_idx = None
    for s in sources:
        if s.get("name") == str(source_id_or_name) or str(s.get("index")) == str(source_id_or_name):
            target_idx = s.get("index")
            break
    if target_idx is not None:
        run_cmd(["wpctl", "set-default", str(target_idx)])
    elif str(source_id_or_name).isdigit():
        run_cmd(["wpctl", "set-default", str(source_id_or_name)])

    # Move active recording streams
    raw_outputs = run_cmd(["pactl", "-f", "json", "list", "source-outputs"])
    if raw_outputs:
        try:
            outputs = json.loads(raw_outputs)
            for out_item in outputs:
                s_idx = out_item.get("index")
                if s_idx is not None:
                    run_cmd(["pactl", "move-source-output", str(s_idx), str(source_id_or_name)])
        except Exception:
            pass

    notify_source_osd()

def cycle_sink(direction=1):
    """Cycle to the next or previous audio sink."""
    sinks = get_sinks_list()
    if not sinks or len(sinks) < 2:
        notify_sink_osd()
        return

    curr_idx = 0
    for i, s in enumerate(sinks):
        if s["is_default"]:
            curr_idx = i
            break

    next_idx = (curr_idx + direction) % len(sinks)
    target_sink = sinks[next_idx]
    set_default_sink(target_sink["name"])
    show_notification(
        "🎧 Audio Output Switched",
        f"<b>{target_sink['description']}</b>",
        "audio-speakers",
        notif_id=SINK_NOTIF_ID
    )

def cycle_source(direction=1):
    """Cycle to the next or previous audio input source."""
    sources = get_sources_list()
    if not sources or len(sources) < 2:
        notify_source_osd()
        return

    curr_idx = 0
    for i, s in enumerate(sources):
        if s["is_default"]:
            curr_idx = i
            break

    next_idx = (curr_idx + direction) % len(sources)
    target_src = sources[next_idx]
    set_default_source(target_src["name"])
    show_notification(
        "🎤 Microphone Switched",
        f"<b>{target_src['description']}</b>",
        "audio-input-microphone",
        notif_id=SOURCE_NOTIF_ID
    )

# ---------------------------------------------------------
# Interactive GUI Menu (Fuzzel / Wofi)
# ---------------------------------------------------------

def open_dmenu(prompt, options):
    """Display an interactive menu using fuzzel or wofi."""
    input_str = "\n".join(options)
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", f"{prompt}: ", "--width", "42", "--lines", "12"]
    else:
        cmd = [
            "wofi",
            "--dmenu",
            "--prompt", prompt,
            "--width", "450",
            "--height", "420",
            "--cache-file", "/dev/null",
            "--hide-scroll",
            "--allow-markup",
            "--insensitive"
        ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, _ = proc.communicate(input=input_str)
        return stdout.strip()
    except Exception:
        return ""

def interactive_menu():
    """Run interactive audio control & switcher menu."""
    vol, sink_muted, sink_name = get_sink_info()
    mic_vol, mic_muted, mic_name = get_source_info()
    sinks = get_sinks_list()
    sources = get_sources_list()

    sink_mute_label = "🔊 Unmute Output" if sink_muted else "🔇 Mute Output"
    mic_mute_label = "🎙️ Unmute Microphone" if mic_muted else "🎤 Mute Microphone"

    options = [
        f"<b>★ Output:</b> {sink_name} ({vol}%{' [Muted]' if sink_muted else ''})",
        f"<b>★ Input:</b> {mic_name} ({mic_vol}%{' [Muted]' if mic_muted else ''})",
        "─── CONTROLS ───",
        f"⏯ {sink_mute_label}",
        f"⏯ {mic_mute_label}",
        "─── PRESET VOLUMES ───",
        "🔊 Volume: 100% (Maximum Standard)",
        "🔊 Volume: 80%",
        "🔊 Volume: 60%",
        "🔊 Volume: 40%",
        "🔉 Volume: 20%",
        "🔈 Volume: 10%",
        "🔇 Volume: 0% (Silent)",
        "─── OUTPUT DEVICES (SINKS) ───",
    ]

    for s in sinks:
        check = "✓ " if s["is_default"] else "  "
        options.append(f"🎧 [Output] {check}{s['description']}::sink::{s['name']}")

    options.append("─── INPUT DEVICES (SOURCES) ───")
    for s in sources:
        check = "✓ " if s["is_default"] else "  "
        options.append(f"🎤 [Input] {check}{s['description']}::src::{s['name']}")

    selected = open_dmenu("Audio Control", options)
    if not selected:
        return

    if "Mute Output" in selected or "Unmute Output" in selected:
        toggle_sink_mute()
    elif "Mute Microphone" in selected or "Unmute Microphone" in selected:
        toggle_source_mute()
    elif "Volume: 100%" in selected:
        set_sink_volume(100)
    elif "Volume: 80%" in selected:
        set_sink_volume(80)
    elif "Volume: 60%" in selected:
        set_sink_volume(60)
    elif "Volume: 40%" in selected:
        set_sink_volume(40)
    elif "Volume: 20%" in selected:
        set_sink_volume(20)
    elif "Volume: 10%" in selected:
        set_sink_volume(10)
    elif "Volume: 0%" in selected:
        set_sink_volume(0)
    elif "::sink::" in selected:
        target_sink = selected.split("::sink::")[-1].strip()
        set_default_sink(target_sink)
    elif "::src::" in selected:
        target_src = selected.split("::src::")[-1].strip()
        set_default_source(target_src)

# ---------------------------------------------------------
# Main CLI Entry Point
# ---------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        interactive_menu()
        return

    cmd = sys.argv[1].lower()
    step = DEFAULT_STEP

    if len(sys.argv) >= 3:
        try:
            step = int(sys.argv[2])
        except ValueError:
            pass

    allow_boost = "--boost" in sys.argv or "--allow-boost" in sys.argv

    if cmd in ["up", "+", "raise", "increase"]:
        change_sink_volume(step, allow_boost=allow_boost)
    elif cmd in ["down", "-", "lower", "decrease"]:
        change_sink_volume(-step)
    elif cmd in ["set", "volume"]:
        set_sink_volume(step)
    elif cmd in ["mute", "toggle-mute", "togglemute"]:
        toggle_sink_mute()
    elif cmd in ["unmute"]:
        run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
        notify_sink_osd()
    elif cmd in ["show", "status", "info"]:
        notify_sink_osd()
    elif cmd in ["mic-up", "mic+"]:
        change_source_volume(step)
    elif cmd in ["mic-down", "mic-"]:
        change_source_volume(-step)
    elif cmd in ["mic-set"]:
        set_source_volume(step)
    elif cmd in ["mic-mute", "toggle-mic", "togglemic"]:
        toggle_source_mute()
    elif cmd in ["mic-unmute"]:
        run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "0"])
        notify_source_osd()
    elif cmd in ["mic-show", "mic-status", "mic-info"]:
        notify_source_osd()
    elif cmd in ["next-sink", "cycle-sink"]:
        cycle_sink(1)
    elif cmd in ["prev-sink"]:
        cycle_sink(-1)
    elif cmd in ["next-source", "cycle-source"]:
        cycle_source(1)
    elif cmd in ["prev-source"]:
        cycle_source(-1)
    elif cmd in ["set-sink"] and len(sys.argv) >= 3:
        set_default_sink(sys.argv[2])
    elif cmd in ["set-source"] and len(sys.argv) >= 3:
        set_default_source(sys.argv[2])
    elif cmd in ["list-sinks"]:
        print(json.dumps(get_sinks_list(), indent=2))
    elif cmd in ["list-sources"]:
        print(json.dumps(get_sources_list(), indent=2))
    elif cmd in ["menu", "dmenu", "gui"]:
        interactive_menu()
    else:
        print(f"Unknown action: {cmd}")
        print("Usage: volume_control.py [up|down|set|mute|mic-up|mic-down|mic-mute|next-sink|next-source|menu|show]")
        sys.exit(1)

if __name__ == "__main__":
    main()
