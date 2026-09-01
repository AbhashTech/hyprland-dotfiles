#!/usr/bin/env python3
"""
Hyprland Screenshot & Screen Recording Utility
Provides full screen, partial area, active window capture, screen recording with audio,
clipboard integration, annotation support, and an interactive dmenu launcher.
"""

import os
import sys
import time
import json
import shutil
import signal
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Paths
SCREENSHOT_DIR = Path.home() / "Pictures" / "Screenshots"
RECORDING_DIR = Path.home() / "Videos" / "Recordings"
PID_FILE = Path("/tmp/hypr_screen_recorder.pid")
INFO_FILE = Path("/tmp/hypr_screen_recorder.json")

# Colors for slurp (Hyprland style: accent border, semi-transparent selection)
SLURP_ARGS = ["-b", "00000044", "-c", "5e81acee", "-s", "00000000", "-w", "2"]

def ensure_dirs():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    RECORDING_DIR.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd, check=False):
    """Execute a command and return stdout as string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return None

def show_notification(title, body, icon="camera-photo", actions=None, timeout=4000):
    """Send desktop notification with optional actions."""
    if not shutil.which("notify-send"):
        return
    cmd = [
        "notify-send",
        "-a", "Screen Capture",
        "-i", str(icon),
        "-t", str(timeout),
    ]
    if actions:
        for act_id, act_label in actions:
            cmd.extend([f"--action={act_id}={act_label}"])
    cmd.extend([title, body])
    
    try:
        if actions:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
            def handle_action():
                out, _ = proc.communicate()
                selected = out.strip()
                if not selected:
                    return
                for act_id, act_func in actions:
                    if selected == act_id and callable(act_func):
                        act_func()
            import threading
            threading.Thread(target=handle_action, daemon=True).start()
        else:
            subprocess.Popen(cmd)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Hyprland Helpers
# -----------------------------------------------------------------------------

def get_active_window_geometry():
    """Get active window geometry (x,y wxh) from hyprctl."""
    raw = run_cmd(["hyprctl", "activewindow", "-j"])
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if not data or "at" not in data or "size" not in data:
            return None
        x, y = data["at"]
        w, h = data["size"]
        if w <= 0 or h <= 0:
            return None
        return f"{x},{y} {w}x{h}"
    except Exception:
        return None

def get_focused_monitor():
    """Get name of focused monitor from hyprctl."""
    raw = run_cmd(["hyprctl", "monitors", "-j"])
    if not raw:
        return None
    try:
        monitors = json.loads(raw)
        for m in monitors:
            if m.get("focused"):
                return m.get("name")
        if monitors:
            return monitors[0].get("name")
    except Exception:
        pass
    return None

def get_default_audio_source():
    """Get PulseAudio/PipeWire default source (mic) monitor name."""
    raw = run_cmd(["pactl", "get-default-source"])
    if raw:
        return raw
    return "default"

def get_default_audio_sink_monitor():
    """Get PulseAudio/PipeWire default sink monitor (desktop sound)."""
    raw = run_cmd(["pactl", "get-default-sink"])
    if raw:
        return f"{raw}.monitor"
    return "default.monitor"

# -----------------------------------------------------------------------------
# Screenshot Functions
# -----------------------------------------------------------------------------

def select_geometry():
    """Let user select region with slurp."""
    if not shutil.which("slurp"):
        show_notification("❌ Error", "slurp is not installed. Run: sudo pacman -S slurp", "dialog-error")
        return None
    res = subprocess.run(["slurp"] + SLURP_ARGS, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return None
    return res.stdout.strip()

def capture_screenshot(mode="area", delay=0, edit=False):
    """
    Take a screenshot.
    Modes:
      - area: Select region/window interactively
      - full: Capture all screens or focused screen
      - window: Capture currently focused window
    """
    ensure_dirs()
    if not shutil.which("grim"):
        show_notification("❌ Error", "grim is not installed. Run: sudo pacman -S grim", "dialog-error")
        return False

    if delay > 0:
        for remaining in range(delay, 0, -1):
            show_notification("⏱️ Screenshot in...", f"{remaining} second{'s' if remaining > 1 else ''}", "clock", timeout=950)
            time.sleep(1)

    geometry = None
    output = None

    if mode == "area":
        geometry = select_geometry()
        if not geometry:
            return False  # Selection cancelled
    elif mode == "window":
        geometry = get_active_window_geometry()
        if not geometry:
            show_notification("⚠️ Warning", "No active window found. Falling back to area selection.", "dialog-warning")
            geometry = select_geometry()
            if not geometry:
                return False
    elif mode == "full":
        # Full screen capture
        pass
    elif mode == "monitor":
        output = get_focused_monitor()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = SCREENSHOT_DIR / f"Screenshot_{timestamp}.png"

    # Annotation / Editor mode (e.g. swappy / satty)
    if edit:
        editor = shutil.which("satty") or shutil.which("swappy")
        if editor:
            grim_cmd = ["grim"]
            if geometry:
                grim_cmd.extend(["-g", geometry])
            elif output:
                grim_cmd.extend(["-o", output])
            grim_cmd.append("-")  # stdout
            
            p_grim = subprocess.Popen(grim_cmd, stdout=subprocess.PIPE)
            if "satty" in editor:
                subprocess.Popen([editor, "--filename", "-", "--output-filename", str(filepath)], stdin=p_grim.stdout)
            else:
                subprocess.Popen([editor, "-f", "-", "-o", str(filepath)], stdin=p_grim.stdout)
            return True

    # Standard capture
    grim_cmd = ["grim"]
    if geometry:
        grim_cmd.extend(["-g", geometry])
    elif output:
        grim_cmd.extend(["-o", output])
    grim_cmd.append(str(filepath))

    res = subprocess.run(grim_cmd)
    if res.returncode != 0 or not filepath.exists():
        show_notification("❌ Screenshot Failed", "Could not capture image.", "dialog-error")
        return False

    # Copy to clipboard if wl-copy is available
    if shutil.which("wl-copy"):
        try:
            with open(filepath, "rb") as f:
                subprocess.run(["wl-copy", "--type", "image/png"], stdin=f)
        except Exception:
            pass

    # Notification actions
    def action_open():
        subprocess.Popen(["xdg-open", str(filepath)])

    def action_folder():
        subprocess.Popen(["xdg-open", str(SCREENSHOT_DIR)])

    def action_edit():
        ed = shutil.which("satty") or shutil.which("swappy") or shutil.which("gimp")
        if ed:
            subprocess.Popen([ed, str(filepath)])
        else:
            subprocess.Popen(["xdg-open", str(filepath)])

    actions = [
        ("open", "View"),
        ("folder", "Folder"),
    ]
    if shutil.which("swappy") or shutil.which("satty"):
        actions.append(("edit", "Edit"))

    show_notification(
        "📸 Screenshot Captured",
        f"Saved to <b>{filepath.name}</b>\nCopied to clipboard.",
        icon=str(filepath),
        actions=[
            ("open", action_open),
            ("folder", action_folder),
            ("edit", action_edit)
        ]
    )
    return True

# -----------------------------------------------------------------------------
# Screen Recording Functions
# -----------------------------------------------------------------------------

def is_recording():
    """Check if wf-recorder is currently running via PID file."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, ProcessLookupError, PermissionError):
            PID_FILE.unlink(missing_ok=True)
            INFO_FILE.unlink(missing_ok=True)
    return None

def stop_recording():
    """Stop active recording process cleanly."""
    pid = is_recording()
    if not pid:
        show_notification("ℹ️ Screen Recorder", "No active screen recording found.", "dialog-information")
        return

    filepath = None
    if INFO_FILE.exists():
        try:
            info = json.loads(INFO_FILE.read_text())
            filepath = info.get("filepath")
        except Exception:
            pass

    # Send SIGINT so wf-recorder finalizes the MP4/MKV container cleanly
    try:
        os.kill(pid, signal.SIGINT)
    except Exception:
        pass

    # Wait up to 5 seconds for file finalize
    for _ in range(50):
        try:
            os.kill(pid, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            break

    PID_FILE.unlink(missing_ok=True)
    INFO_FILE.unlink(missing_ok=True)

    if filepath and Path(filepath).exists():
        target_path = Path(filepath)
        def action_play():
            subprocess.Popen(["xdg-open", str(target_path)])
        def action_folder():
            subprocess.Popen(["xdg-open", str(RECORDING_DIR)])

        file_size_mb = target_path.stat().st_size / (1024 * 1024)
        show_notification(
            "🎬 Recording Saved",
            f"Saved: <b>{target_path.name}</b>\nSize: {file_size_mb:.1f} MB",
            icon="video-x-generic",
            actions=[
                ("play", action_play),
                ("folder", action_folder)
            ]
        )
    else:
        show_notification("🎬 Recording Stopped", "Recording has finished.", "video-x-generic")

def start_recording(mode="area", audio="none", delay=0):
    """
    Start screen recording using wf-recorder.
    mode: 'area', 'full', 'window'
    audio: 'none', 'mic', 'desktop', 'both'
    """
    ensure_dirs()
    if is_recording():
        stop_recording()
        return

    if not shutil.which("wf-recorder"):
        show_notification("❌ Error", "wf-recorder is not installed. Run: sudo pacman -S wf-recorder", "dialog-error")
        return

    geometry = None
    if mode == "area":
        geometry = select_geometry()
        if not geometry:
            return  # Cancelled
    elif mode == "window":
        geometry = get_active_window_geometry()
        if not geometry:
            show_notification("⚠️ Warning", "No active window found. Falling back to area selection.", "dialog-warning")
            geometry = select_geometry()
            if not geometry:
                return

    if delay > 0:
        for remaining in range(delay, 0, -1):
            show_notification("⏱️ Recording in...", f"{remaining} second{'s' if remaining > 1 else ''}", "clock", timeout=950)
            time.sleep(1)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = RECORDING_DIR / f"Recording_{timestamp}.mp4"

    cmd = ["wf-recorder", "-f", str(filepath), "-c", "libx264", "-p", "preset=veryfast", "-p", "crf=23", "-x", "yuv420p"]

    if geometry:
        cmd.extend(["-g", geometry])

    # Audio device configuration
    if audio == "mic":
        src = get_default_audio_source()
        cmd.extend(["--audio", f"-a={src}"])
    elif audio == "desktop":
        sink_mon = get_default_audio_sink_monitor()
        cmd.extend(["--audio", f"-a={sink_mon}"])
    elif audio == "both":
        cmd.append("--audio")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PID_FILE.write_text(str(proc.pid))
        INFO_FILE.write_text(json.dumps({
            "pid": proc.pid,
            "filepath": str(filepath),
            "start_time": time.time(),
            "mode": mode,
            "audio": audio
        }))

        def action_stop():
            stop_recording()

        audio_desc = f" (Audio: {audio})" if audio != "none" else ""
        show_notification(
            "🎥 Recording Started",
            f"Recording {mode}{audio_desc}...\nClick 'Stop' or re-run utility to finish.",
            icon="media-record",
            actions=[("stop", action_stop)],
            timeout=8000
        )
    except Exception as e:
        show_notification("❌ Recording Failed", f"Could not start recorder: {e}", "dialog-error")

def toggle_recording(mode="area", audio="none"):
    """Toggle recording on/off."""
    if is_recording():
        stop_recording()
    else:
        start_recording(mode=mode, audio=audio)

# -----------------------------------------------------------------------------
# Interactive Menu (Fuzzel / Wofi / Rofi)
# -----------------------------------------------------------------------------

def open_interactive_menu():
    """Display an interactive launcher menu using Fuzzel or Wofi."""
    recording_active = is_recording() is not None

    options = []
    if recording_active:
        options.append("⏹️  Stop Active Recording")

    options.extend([
        "📸 Screenshot: Area / Selection",
        "🖥️  Screenshot: Full Screen",
        "🪟 Screenshot: Active Window",
        "🎨 Screenshot: Area & Annotate",
        "📱 Read QR Code from Screen",
        "⏱️  Screenshot: 5s Timer (Area)",
        "⏱️  Screenshot: 5s Timer (Full Screen)",
        "🎥 Record: Area (No Audio)",
        "🎙️ Record: Area (Microphone)",
        "🔊 Record: Area (Desktop Audio)",
        "🖥️  Record: Full Screen (No Audio)",
        "🎙️ Record: Full Screen (Microphone)",
        "🔊 Record: Full Screen (Desktop Audio)",
    ])

    input_str = "\n".join(options)

    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", "Capture: ", "--width", "36", "--lines", str(len(options) + 1)]
    elif shutil.which("wofi"):
        cmd = ["wofi", "--dmenu", "--prompt", "Screen Capture", "--width", "400", "--height", "380", "--hide-scroll", "--insensitive"]
    elif shutil.which("rofi"):
        cmd = ["rofi", "-dmenu", "-p", "Screen Capture"]
    else:
        show_notification("❌ Error", "No launcher found (install fuzzel, wofi, or rofi)", "dialog-error")
        return

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        choice, _ = proc.communicate(input=input_str)
        choice = choice.strip()
        if not choice:
            return

        if "Stop Active Recording" in choice:
            stop_recording()
        elif "Screenshot: Area & Annotate" in choice:
            capture_screenshot(mode="area", edit=True)
        elif "Read QR Code from Screen" in choice:
            qr_script = Path.home() / ".config" / "hypr" / "scripts" / "qr_reader.py"
            subprocess.Popen(["python3", str(qr_script)])
        elif "Screenshot: Area" in choice:
            capture_screenshot(mode="area")
        elif "Screenshot: Full Screen" in choice:
            capture_screenshot(mode="full")
        elif "Screenshot: Active Window" in choice:
            capture_screenshot(mode="window")
        elif "Screenshot: 5s Timer (Area)" in choice:
            capture_screenshot(mode="area", delay=5)
        elif "Screenshot: 5s Timer (Full" in choice:
            capture_screenshot(mode="full", delay=5)
        elif "Record: Area (No Audio)" in choice:
            start_recording(mode="area", audio="none")
        elif "Record: Area (Microphone)" in choice:
            start_recording(mode="area", audio="mic")
        elif "Record: Area (Desktop Audio)" in choice:
            start_recording(mode="area", audio="desktop")
        elif "Record: Full Screen (No Audio)" in choice:
            start_recording(mode="full", audio="none")
        elif "Record: Full Screen (Microphone)" in choice:
            start_recording(mode="full", audio="mic")
        elif "Record: Full Screen (Desktop Audio)" in choice:
            start_recording(mode="full", audio="desktop")
    except Exception as e:
        print(f"Error launching menu: {e}", file=sys.stderr)

# -----------------------------------------------------------------------------
# Main CLI Parser
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Hyprland Screenshot & Screen Recording Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  screen_capture.py screenshot --area         # Area screenshot to file & clipboard
  screen_capture.py screenshot --full         # Fullscreen screenshot
  screen_capture.py screenshot --window       # Active window screenshot
  screen_capture.py screenshot --edit         # Area screenshot and edit (swappy/satty)
  screen_capture.py screenshot --delay 5      # 5-second countdown screenshot
  screen_capture.py record --area             # Start recording selected area
  screen_capture.py record --full --mic       # Record full screen with microphone
  screen_capture.py record --desktop          # Record area with desktop sound
  screen_capture.py stop                      # Stop recording
  screen_capture.py toggle                    # Toggle recording on/off
  screen_capture.py menu                      # Open interactive GUI menu
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Screenshot subparser
    ss_parser = subparsers.add_parser("screenshot", aliases=["ss", "shot"], help="Take a screenshot")
    ss_group = ss_parser.add_mutually_exclusive_group()
    ss_group.add_argument("-a", "--area", action="store_true", default=True, help="Select an area/region (default)")
    ss_group.add_argument("-f", "--full", action="store_true", help="Capture entire screen")
    ss_group.add_argument("-w", "--window", action="store_true", help="Capture active window")
    ss_parser.add_argument("-e", "--edit", action="store_true", help="Open in annotation tool (swappy/satty)")
    ss_parser.add_argument("-d", "--delay", type=int, default=0, help="Countdown timer delay in seconds")

    # Record subparser
    rec_parser = subparsers.add_parser("record", aliases=["rec"], help="Start screen recording")
    rec_mode = rec_parser.add_mutually_exclusive_group()
    rec_mode.add_argument("-a", "--area", action="store_true", default=True, help="Record selected area (default)")
    rec_mode.add_argument("-f", "--full", action="store_true", help="Record full screen")
    rec_mode.add_argument("-w", "--window", action="store_true", help="Record active window")
    rec_audio = rec_parser.add_mutually_exclusive_group()
    rec_audio.add_argument("--mic", action="store_true", help="Record microphone audio")
    rec_audio.add_argument("--desktop", action="store_true", help="Record system/desktop audio")
    rec_audio.add_argument("--both", action="store_true", help="Record both mic and desktop audio")
    rec_parser.add_argument("-d", "--delay", type=int, default=0, help="Countdown delay in seconds")

    # Stop, Toggle & Menu
    subparsers.add_parser("stop", help="Stop any active screen recording")
    tog_parser = subparsers.add_parser("toggle", help="Toggle screen recording")
    tog_parser.add_argument("-f", "--full", action="store_true", help="Record full screen instead of area when toggling on")
    tog_parser.add_argument("--mic", action="store_true", help="Include mic audio")
    tog_parser.add_argument("--desktop", action="store_true", help="Include desktop audio")

    subparsers.add_parser("menu", help="Open interactive capture menu (default if no args given)")

    args = parser.parse_args()

    if not args.command or args.command == "menu":
        open_interactive_menu()
    elif args.command in ["screenshot", "ss", "shot"]:
        mode = "full" if args.full else ("window" if args.window else "area")
        capture_screenshot(mode=mode, delay=args.delay, edit=args.edit)
    elif args.command in ["record", "rec"]:
        mode = "full" if args.full else ("window" if args.window else "area")
        audio = "mic" if args.mic else ("desktop" if args.desktop else ("both" if args.both else "none"))
        start_recording(mode=mode, audio=audio, delay=args.delay)
    elif args.command == "stop":
        stop_recording()
    elif args.command == "toggle":
        mode = "full" if args.full else "area"
        audio = "mic" if args.mic else ("desktop" if args.desktop else "none")
        toggle_recording(mode=mode, audio=audio)

if __name__ == "__main__":
    main()
