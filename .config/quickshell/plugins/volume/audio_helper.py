#!/usr/bin/env python3
"""
Audio backend helper for QuickShell Volume Mixer and desktop audio controls.
Handles master sinks/sources, per-app volume streams, device switching, and sound server restarting.
"""

import sys
import json
import subprocess
import os
import re

def run_cmd(cmd, timeout=3):
    """Run a command and return stdout string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return res.stdout.strip()
    except Exception:
        return ""

def clean_device_name(raw_desc, is_source=False):
    """Format verbose hardware names into clean user-friendly labels."""
    if not raw_desc:
        return "Microphone" if is_source else "Speakers"
    desc = raw_desc
    if "Chipset Family" in desc or "Audio Controller" in desc or "High Definition Audio" in desc:
        parts = desc.split(")")
        if len(parts) > 1 and parts[-1].strip():
            desc = parts[-1].strip()
    desc = re.sub(r'\(HD Audio\)', '', desc).strip()
    return desc or raw_desc

def get_port_availability():
    """Retrieve ALSA card port availability states."""
    port_avail = {}
    raw = run_cmd(["pactl", "-f", "json", "list", "cards"])
    if raw:
        try:
            cards = json.loads(raw)
            for c in cards:
                ports = c.get("ports", {})
                if isinstance(ports, dict):
                    for pname, pinfo in ports.items():
                        avail = pinfo.get("availability")
                        port_avail[pname] = avail
                        short_name = pname.split("]")[-1].strip() if "]" in pname else pname
                        port_avail[short_name] = avail
        except Exception:
            pass
    return port_avail

def get_master_sink():
    out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    vol_pct = 50
    muted = False
    if out:
        parts = out.strip().split()
        if len(parts) >= 2:
            try:
                vol_pct = int(round(float(parts[1]) * 100))
            except ValueError:
                vol_pct = 50
        if "[MUTED]" in out:
            muted = True

    default_sink_name = run_cmd(["pactl", "get-default-sink"])
    return vol_pct, muted, default_sink_name

def get_master_source():
    out = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])
    vol_pct = 50
    muted = False
    if out:
        parts = out.strip().split()
        if len(parts) >= 2:
            try:
                vol_pct = int(round(float(parts[1]) * 100))
            except ValueError:
                vol_pct = 50
        if "[MUTED]" in out:
            muted = True

    default_src_name = run_cmd(["pactl", "get-default-source"])
    return vol_pct, muted, default_src_name

def get_sinks():
    default_sink = run_cmd(["pactl", "get-default-sink"])
    port_avail = get_port_availability()
    raw_sinks = run_cmd(["pactl", "-f", "json", "list", "sinks"])
    results = []
    seen_names = set()
    if raw_sinks:
        try:
            sinks = json.loads(raw_sinks)
            for s in reversed(sinks):
                name = s.get("name", "")
                ports = s.get("ports", [])
                active_port = s.get("active_port")

                is_unavail = False
                if ports:
                    is_unavail = all(p.get("availability") == "not available" for p in ports)
                elif active_port and port_avail.get(active_port) == "not available":
                    is_unavail = True
                else:
                    for p_key, status in port_avail.items():
                        if f"__{p_key}__" in name and status == "not available":
                            is_unavail = True
                            break

                desc = clean_device_name(s.get("description", name))
                idx = s.get("index")
                is_default = (name == default_sink)

                if is_unavail and not is_default:
                    continue
                if desc in seen_names and not is_default:
                    continue
                seen_names.add(desc)

                vol_pct = 50
                vol_map = s.get("volume", {})
                for ch, ch_info in vol_map.items():
                    if isinstance(ch_info, dict) and "value_percent" in ch_info:
                        try:
                            vol_pct = int(ch_info["value_percent"].replace("%", ""))
                            break
                        except ValueError:
                            pass

                icon = "󰕾"
                if "hdmi" in name.lower() or "displayport" in name.lower():
                    icon = "󰡁"
                elif "headphone" in desc.lower() or "headset" in desc.lower() or "bluez" in name.lower():
                    icon = "󰋋"
                elif "speaker" in desc.lower():
                    icon = "󰕾"

                results.append({
                    "id": idx,
                    "name": name,
                    "description": desc,
                    "icon": icon,
                    "is_default": is_default,
                    "muted": s.get("mute", False),
                    "volume": vol_pct
                })
            results.reverse()
        except Exception:
            pass
    return results

def get_sources():
    default_src = run_cmd(["pactl", "get-default-source"])
    port_avail = get_port_availability()
    raw_srcs = run_cmd(["pactl", "-f", "json", "list", "sources"])
    results = []
    seen_names = set()
    if raw_srcs:
        try:
            srcs = json.loads(raw_srcs)
            for s in reversed(srcs):
                name = s.get("name", "")
                if name.endswith(".monitor"):
                    continue

                ports = s.get("ports", [])
                active_port = s.get("active_port")

                is_unavail = False
                if ports:
                    is_unavail = all(p.get("availability") == "not available" for p in ports)
                elif active_port and port_avail.get(active_port) == "not available":
                    is_unavail = True
                else:
                    for p_key, status in port_avail.items():
                        if f"__{p_key}__" in name and status == "not available":
                            is_unavail = True
                            break

                desc = clean_device_name(s.get("description", name), is_source=True)
                idx = s.get("index")
                is_default = (name == default_src)

                if is_unavail and not is_default:
                    continue
                if desc in seen_names and not is_default:
                    continue
                seen_names.add(desc)

                vol_pct = 50
                vol_map = s.get("volume", {})
                for ch, ch_info in vol_map.items():
                    if isinstance(ch_info, dict) and "value_percent" in ch_info:
                        try:
                            vol_pct = int(ch_info["value_percent"].replace("%", ""))
                            break
                        except ValueError:
                            pass

                icon = "󰍬"
                if "headphone" in desc.lower() or "headset" in desc.lower() or "bluez" in name.lower():
                    icon = "󰋎"

                results.append({
                    "id": idx,
                    "name": name,
                    "description": desc,
                    "icon": icon,
                    "is_default": is_default,
                    "muted": s.get("mute", False),
                    "volume": vol_pct
                })
            results.reverse()
        except Exception:
            pass
    return results

def get_apps():
    """Retrieve active sink-inputs (applications currently producing audio)."""
    raw_inputs = run_cmd(["pactl", "-f", "json", "list", "sink-inputs"])
    results = []
    if raw_inputs:
        try:
            inputs = json.loads(raw_inputs)
            for inp in inputs:
                idx = inp.get("index")
                props = inp.get("properties", {})
                
                app_name = props.get("application.name") or props.get("media.name") or props.get("application.process.binary") or "Audio Stream"
                app_bin = props.get("application.process.binary", "").lower()
                icon_name = props.get("application.icon_name", "").lower()

                icon = "󰓃"
                if "firefox" in app_bin or "firefox" in icon_name:
                    icon = "󰈹"
                elif "chrome" in app_bin or "chromium" in app_bin or "brave" in app_bin:
                    icon = "󰊯"
                elif "spotify" in app_bin or "spotify" in icon_name:
                    icon = "󰓇"
                elif "discord" in app_bin or "vesktop" in app_bin:
                    icon = "󰙯"
                elif "mpv" in app_bin or "vlc" in app_bin or "video" in app_bin:
                    icon = "󰕼"
                elif "steam" in app_bin or "game" in app_bin:
                    icon = "󰊴"
                elif "telegram" in app_bin:
                    icon = "󰀨"

                vol_pct = 100
                vol_map = inp.get("volume", {})
                for ch, ch_info in vol_map.items():
                    if isinstance(ch_info, dict) and "value_percent" in ch_info:
                        try:
                            vol_pct = int(ch_info["value_percent"].replace("%", ""))
                            break
                        except ValueError:
                            pass

                results.append({
                    "id": idx,
                    "name": app_name,
                    "binary": app_bin,
                    "icon": icon,
                    "volume": vol_pct,
                    "muted": inp.get("mute", False)
                })
        except Exception:
            pass
    return results

def get_all_state():
    """Aggregate all audio states into a single fast JSON payload."""
    sv, sm, def_sink_name = get_master_sink()
    mv, mm, def_src_name = get_master_source()
    sinks = get_sinks()
    sources = get_sources()
    apps = get_apps()

    active_sink_desc = "Speakers / Output"
    for s in sinks:
        if s["is_default"]:
            active_sink_desc = s["description"]
            break

    active_src_desc = "Microphone"
    for s in sources:
        if s["is_default"]:
            active_src_desc = s["description"]
            break

    return {
        "master_sink": {
            "volume": sv,
            "muted": sm,
            "name": def_sink_name,
            "description": active_sink_desc
        },
        "master_source": {
            "volume": mv,
            "muted": mm,
            "name": def_src_name,
            "description": active_src_desc
        },
        "sinks": sinks,
        "sources": sources,
        "apps": apps
    }

def set_sink_volume(val):
    val = max(0, min(150, int(val)))
    val_float = round(val / 100.0, 2)
    run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", str(val_float)])
    run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"])

def toggle_sink_mute():
    run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])

def set_source_volume(val):
    val = max(0, min(100, int(val)))
    val_float = round(val / 100.0, 2)
    run_cmd(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", str(val_float)])
    run_cmd(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{val}%"])

def toggle_source_mute():
    run_cmd(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])

def set_default_sink(sink_id_or_name):
    run_cmd(["pactl", "set-default-sink", str(sink_id_or_name)])
    sinks = get_sinks()
    for s in sinks:
        if str(s.get("name")) == str(sink_id_or_name) or str(s.get("id")) == str(sink_id_or_name):
            run_cmd(["wpctl", "set-default", str(s.get("id"))])
            break
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

def set_default_source(source_id_or_name):
    run_cmd(["pactl", "set-default-source", str(source_id_or_name)])
    sources = get_sources()
    for s in sources:
        if str(s.get("name")) == str(source_id_or_name) or str(s.get("id")) == str(source_id_or_name):
            run_cmd(["wpctl", "set-default", str(s.get("id"))])
            break
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

def set_app_volume(stream_id, val):
    val = max(0, min(150, int(val)))
    run_cmd(["pactl", "set-sink-input-volume", str(stream_id), f"{val}%"])

def toggle_app_mute(stream_id):
    run_cmd(["pactl", "set-sink-input-mute", str(stream_id), "toggle"])

def restart_sound_server():
    """Restart pipewire, pipewire-pulse, wireplumber user services."""
    subprocess.Popen([
        "notify-send",
        "-t", "2000",
        "-a", "VolumeMixer",
        "-i", "audio-speakers",
        "🔊 Restarting Audio Server",
        "Restarting PipeWire and WirePlumber..."
    ])
    subprocess.run(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"])
    subprocess.Popen([
        "notify-send",
        "-t", "2500",
        "-a", "VolumeMixer",
        "-i", "audio-volume-high",
        "✓ Audio Stack Ready",
        "PipeWire and WirePlumber restarted successfully."
    ])

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["get-all", "status", "json"]:
        print(json.dumps(get_all_state()))
        return

    cmd = sys.argv[1].lower()
    if cmd == "set-sink-vol" and len(sys.argv) >= 3:
        set_sink_volume(sys.argv[2])
    elif cmd == "toggle-sink-mute":
        toggle_sink_mute()
    elif cmd == "set-source-vol" and len(sys.argv) >= 3:
        set_source_volume(sys.argv[2])
    elif cmd == "toggle-source-mute":
        toggle_source_mute()
    elif cmd == "set-default-sink" and len(sys.argv) >= 3:
        set_default_sink(sys.argv[2])
    elif cmd == "set-default-source" and len(sys.argv) >= 3:
        set_default_source(sys.argv[2])
    elif cmd == "set-app-vol" and len(sys.argv) >= 4:
        set_app_volume(sys.argv[2], sys.argv[3])
    elif cmd == "toggle-app-mute" and len(sys.argv) >= 3:
        toggle_app_mute(sys.argv[2])
    elif cmd in ["restart", "restart-server", "restart-sound"]:
        restart_sound_server()
    else:
        print(f"Unknown action: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
