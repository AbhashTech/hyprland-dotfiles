#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha Glassmorphic Clipboard Manager for Hyprland & Waybar
 Full Support for Text, URLs, Code Snippets, Binary Images & Screenshots
 With Individual Item Deletion, Continuous Multi-Delete & Fuzzel Previews
=============================================================================
"""

import html
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PAUSE_STATE_FILE = os.path.expanduser("~/.cache/cliphist_paused")
THUMB_DIR = Path.home() / ".cache" / "cliphist_thumbs"
SCREENSHOT_DIR = Path.home() / "Pictures" / "Screenshots"


def ensure_dirs():
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd, check=False):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""


def run_cmd_bytes(cmd, check=False):
    try:
        res = subprocess.run(cmd, capture_output=True, check=check)
        return res.stdout
    except Exception:
        return b""


def notify(title, msg, icon="edit-paste", urgency="low"):
    cmd = [
        "notify-send",
        "-r", "9920",
        "-t", "2500",
        "-u", urgency,
        "-a", "Clipboard Manager",
        "-i", str(icon),
        "-h", "string:x-canonical-private-synchronous:clipboard_mgr",
        title,
        msg
    ]
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def notify_waybar():
    """Trigger signal 9 on Waybar to instantly refresh clipboard module."""
    run_cmd(["pkill", "-RTMIN+9", "waybar"])


def is_paused():
    return os.path.exists(PAUSE_STATE_FILE)


def toggle_pause():
    if is_paused():
        try:
            os.remove(PAUSE_STATE_FILE)
        except Exception:
            pass
        start_daemon(silent=True)
        notify("󰅍 Clipboard Resumed", "Clipboard recording is now ACTIVE.", "edit-paste")
    else:
        try:
            os.makedirs(os.path.dirname(PAUSE_STATE_FILE), exist_ok=True)
            with open(PAUSE_STATE_FILE, "w") as f:
                f.write("1")
        except Exception:
            pass
        stop_daemon_watchers()
        notify("󰂛 Clipboard Paused", "Private mode active. Copying is not recorded.", "security-high", urgency="normal")
    notify_waybar()


def stop_daemon_watchers():
    """Kill running wl-paste clipboard watchers."""
    try:
        out = run_cmd(["pgrep", "-f", "wl-paste.*cliphist"])
        for pid in out.split():
            if pid.isdigit():
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except Exception:
                    pass
    except Exception:
        pass


def is_daemon_running():
    out = run_cmd(["pgrep", "-f", "wl-paste.*cliphist"])
    return bool(out.strip())


def start_daemon(silent=False):
    """Start wl-paste watchers for text and binary images."""
    if is_paused():
        return

    stop_daemon_watchers()

    cmd_text = (
        'wl-paste --type text --watch bash -c "'
        'cliphist store && pkill -RTMIN+9 waybar"'
    )
    cmd_image = (
        'wl-paste --type image --watch bash -c "'
        'cliphist store && pkill -RTMIN+9 waybar"'
    )

    try:
        subprocess.Popen(
            cmd_text,
            shell=True,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        subprocess.Popen(
            cmd_image,
            shell=True,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        if not silent:
            notify("󰅍 Clipboard Daemon", "Tracking text and screenshot/image clips.", "edit-paste")
    except Exception as e:
        if not silent:
            notify("Clipboard Error", f"Failed to start daemon: {e}", "dialog-error", urgency="critical")


def get_clip_list():
    """Retrieve raw items from cliphist list."""
    out = run_cmd(["cliphist", "list"])
    if not out or "please store something first" in out:
        return []
    lines = out.splitlines()
    return lines


def get_image_thumbnail(clip_id, raw_line):
    """Ensure a cached PNG thumbnail exists for an image cliphist entry."""
    ensure_dirs()
    thumb_path = THUMB_DIR / f"thumb_{clip_id}.png"
    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return str(thumb_path)

    try:
        decode_proc = subprocess.Popen(
            ["cliphist", "decode"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=False
        )
        data, _ = decode_proc.communicate(input=raw_line.encode("utf-8"))
        if data and len(data) > 0:
            thumb_path.write_bytes(data)
            return str(thumb_path)
    except Exception:
        pass
    return None


def format_clip_item(raw_line, create_thumb=True):
    """Parse cliphist line 'id\tcontent' and return metadata, type, icon, and thumbnail."""
    if "\t" not in raw_line:
        return raw_line, "", "text", "󰅍", None
    
    clip_id, content = raw_line.split("\t", 1)
    content_clean = content.strip()
    thumb_path = None

    if "[[ binary data" in content_clean.lower() or content_clean.startswith("[[ binary"):
        item_type = "image"
        icon = "󰋩"
        match = re.search(r'\[\[\s*binary\s+data\s+(.*?)\s*\]\]', content_clean, re.IGNORECASE)
        details = match.group(1) if match else "Image"
        content_clean = f"[Screenshot / Image: {details}]"
        if create_thumb:
            thumb_path = get_image_thumbnail(clip_id, raw_line)
    elif re.match(r'^https?:\/\/', content_clean):
        item_type = "url"
        icon = "󰖟"
    elif any(kw in content_clean for kw in ["function", "const ", "let ", "var ", "class ", "def ", "import ", "select ", "return "]) and ("{" in content_clean or ";" in content_clean or ":" in content_clean):
        item_type = "code"
        icon = "󰅪"
    elif "\n" in content or len(content_clean) > 80:
        item_type = "multiline"
        icon = "󰉿"
    else:
        item_type = "text"
        icon = "󰅍"

    return clip_id, content_clean, item_type, icon, thumb_path


def run_dmenu(prompt, options, width=46, lines=12):
    """Launch Fuzzel dmenu (with icon support) or fallback to wofi."""
    if shutil.which("fuzzel"):
        cmd = [
            "fuzzel", "--dmenu",
            "--prompt", f" {prompt}: ",
            "--width", str(width),
            "--lines", str(lines)
        ]
    elif shutil.which("wofi"):
        cmd = [
            "wofi", "--dmenu",
            "--prompt", prompt,
            "--width", "560",
            "--height", "450",
            "--cache-file", "/dev/null",
            "--hide-scroll",
            "--allow-markup",
            "--insensitive"
        ]
    else:
        return ""
    try:
        proc = subprocess.run(cmd, input="\n".join(options), text=True, capture_output=True)
        return proc.stdout.strip()
    except Exception:
        return ""


def decode_and_copy(raw_line):
    """Decode item and push to Wayland clipboard with appropriate MIME type."""
    try:
        clip_id, content, item_type, icon, thumb_path = format_clip_item(raw_line, create_thumb=True)

        decode_proc = subprocess.Popen(
            ["cliphist", "decode"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=False
        )
        stdout_data, _ = decode_proc.communicate(input=raw_line.encode("utf-8"))
        
        if stdout_data is not None and len(stdout_data) > 0:
            if item_type == "image":
                wl_proc = subprocess.Popen(["wl-copy", "--type", "image/png"], stdin=subprocess.PIPE)
                wl_proc.communicate(input=stdout_data)
                
                notif_icon = thumb_path if (thumb_path and os.path.exists(thumb_path)) else "camera-photo"
                notify("📸 Screenshot / Image Copied", f"Restored #{clip_id}: {content}\nReady to paste!", icon=notif_icon)
            else:
                wl_proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                wl_proc.communicate(input=stdout_data)
                
                preview = content[:45] + ("..." if len(content) > 45 else "")
                notify("󰅍 Copied to Clipboard", f"Restored {item_type}: {preview}")

            notify_waybar()
            return True
    except Exception as e:
        notify("Clipboard Error", f"Failed to decode item: {e}", "dialog-error", urgency="critical")
    return False


def delete_item(raw_line):
    """Delete a single entry from cliphist database and remove thumbnail."""
    try:
        clip_id, content, item_type, icon, _ = format_clip_item(raw_line, create_thumb=False)
        proc = subprocess.Popen(["cliphist", "delete"], stdin=subprocess.PIPE, text=False)
        proc.communicate(input=raw_line.encode("utf-8"))
        
        thumb_file = THUMB_DIR / f"thumb_{clip_id}.png"
        if thumb_file.exists():
            try:
                thumb_file.unlink()
            except Exception:
                pass

        preview = content[:40] + ("..." if len(content) > 40 else "")
        notify("󰅖 Item Deleted", f"Removed #{clip_id}: {preview}", icon="edit-delete")
        notify_waybar()
        return True
    except Exception as e:
        notify("Clipboard Error", f"Failed to delete item: {e}", "dialog-error")
        return False


def clear_history():
    """Wipe all clipboard history and clear thumbnail cache with confirmation."""
    confirm_options = [
        "󰅖  Cancel (Keep History)",
        "󰃢  Yes, Clear All Clipboard History",
    ]
    ans = run_dmenu("󰃢 Clear Entire Clipboard History?", confirm_options, width=38, lines=2)
    if ans and "Yes, Clear" in ans:
        run_cmd(["cliphist", "wipe"])
        run_cmd(["wl-copy", "--clear"])
        
        if THUMB_DIR.exists():
            for f in THUMB_DIR.glob("thumb_*.png"):
                try:
                    f.unlink()
                except Exception:
                    pass

        notify("󰃢 Clipboard Cleared", "All clipboard history and image caches wiped.")
        notify_waybar()


def open_delete_menu():
    """Interactive individual item deletion menu with continuous multi-delete support."""
    while True:
        items = get_clip_list()
        count = len(items)
        if count == 0:
            notify("󰅍 Clipboard History", "All clipboard items have been cleared.")
            return

        options = [
            "󰌍  « Done / Back to Clipboard Menu",
            "󰃢  Clear ALL Clipboard History",
            f"─── 󰅖 SELECT AN ITEM TO DELETE ({count} items) ───",
        ]

        raw_map = {}
        for line in items:
            clip_id, content, item_type, icon, thumb_path = format_clip_item(line, create_thumb=True)
            one_liner = " ".join(content.split())
            if len(one_liner) > 60:
                one_liner = one_liner[:57] + "..."
            
            display_line = f"󰅖 [{clip_id}] {icon} {one_liner}"
            raw_map[clip_id] = line
            if thumb_path and os.path.exists(thumb_path):
                display_line = f"{display_line}\0icon\x1f{thumb_path}"
            options.append(display_line)

        chosen = run_dmenu("󰅖 Delete Item from History", options, width=48, lines=12)
        if not chosen or "Done / Back" in chosen:
            return

        chosen_clean = chosen.split("\0")[0].strip()

        if "Clear ALL" in chosen_clean:
            clear_history()
            return
        elif "[" in chosen_clean and "]" in chosen_clean:
            match = re.search(r'\[(\d+)\]', chosen_clean)
            if match:
                target_id = match.group(1)
                raw_line = raw_map.get(target_id)
                if not raw_line:
                    for l in items:
                        if l.startswith(target_id + "\t") or l == target_id:
                            raw_line = l
                            break
                if raw_line:
                    delete_item(raw_line)
                    # Loop continues for next deletion


def show_image_menu(raw_line):
    """Submenu for handling an image/screenshot clipboard item."""
    clip_id, content, item_type, icon, thumb_path = format_clip_item(raw_line, create_thumb=True)
    
    options = [
        f"─── 📸 SCREENSHOT / IMAGE #{clip_id} ───",
        f"Info: {content}",
        "─── ACTIONS ───",
        "󰅍  Copy Image to Clipboard (Ready to Paste)",
        "󰋩  Open / View Full Image",
        "🎨  Edit / Annotate Image (Swappy)",
        "💾  Save to Pictures/Screenshots Folder",
        "󰅖  Delete this Image from History",
        "󰌍  « Back to Clipboard History",
    ]

    chosen = run_dmenu(f"📸 Image #{clip_id}", options, width=46, lines=9)
    if not chosen or "Back to Clipboard" in chosen:
        open_history_menu()
        return

    if "Copy Image to Clipboard" in chosen:
        decode_and_copy(raw_line)
    elif "Open / View Full Image" in chosen:
        if thumb_path and os.path.exists(thumb_path):
            viewer = shutil.which("xdg-open")
            if viewer:
                subprocess.Popen([viewer, thumb_path])
            else:
                notify(f"Image #{clip_id}", "Image preview", icon=thumb_path)
    elif "Edit / Annotate" in chosen:
        if thumb_path and os.path.exists(thumb_path):
            ed = shutil.which("satty") or shutil.which("swappy") or shutil.which("gimp")
            if ed:
                subprocess.Popen([ed, thumb_path])
            else:
                subprocess.Popen(["xdg-open", thumb_path])
    elif "Save to Pictures/Screenshots" in chosen:
        if thumb_path and os.path.exists(thumb_path):
            ensure_dirs()
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            dest = SCREENSHOT_DIR / f"Clipboard_Screenshot_{timestamp}.png"
            shutil.copy2(thumb_path, dest)
            notify("💾 Screenshot Saved", f"Saved to <b>{dest.name}</b> in Screenshots folder.", icon=str(dest))
    elif "Delete this Image" in chosen:
        delete_item(raw_line)
        open_history_menu()


def open_history_menu():
    """Main interactive clipboard browser with thumbnail icons and delete support."""
    paused = is_paused()
    items = get_clip_list()
    count = len(items)

    pause_label = "󰅍  Pause State: PAUSED (Click to Resume)" if paused else "󰂛  Pause State: ACTIVE (Click to Pause)"

    options = [
        "─── 󰅍 CLIPBOARD CONTROLS ───",
        pause_label,
        "󰅖  Delete Individual Item from History...",
        "󰃢  Clear All Clipboard History",
        "󰐥  Sync / Restart Clipboard Watcher",
    ]

    raw_map = {}

    if count > 0:
        options.append(f"─── 󰅍 HISTORY ENTRIES ({count}) ───")
        for line in items:
            clip_id, content, item_type, icon, thumb_path = format_clip_item(line, create_thumb=True)
            one_liner = " ".join(content.split())
            if len(one_liner) > 65:
                one_liner = one_liner[:62] + "..."

            display_line = f"{icon} [{clip_id}] {one_liner}"
            raw_map[clip_id] = line

            if thumb_path and os.path.exists(thumb_path):
                display_line = f"{display_line}\0icon\x1f{thumb_path}"

            options.append(display_line)
    else:
        options.append("─── HISTORY ENTRIES (0) ───")
        options.append("󰄴  No items in clipboard history")

    chosen = run_dmenu("󰅍 Clipboard Manager", options, width=48, lines=12)
    if not chosen:
        return

    chosen_clean = chosen.split("\0")[0].strip()

    if "Pause State:" in chosen_clean:
        toggle_pause()
    elif "Delete Individual Item" in chosen_clean:
        open_delete_menu()
    elif "Clear All" in chosen_clean:
        clear_history()
    elif "Sync / Restart" in chosen_clean:
        start_daemon(silent=False)
        notify_waybar()
    elif "[" in chosen_clean and "]" in chosen_clean:
        match = re.search(r'\[(\d+)\]', chosen_clean)
        if match:
            target_id = match.group(1)
            raw_line = raw_map.get(target_id)
            if not raw_line:
                for l in items:
                    if l.startswith(target_id + "\t") or l == target_id:
                        raw_line = l
                        break
            if raw_line:
                decode_and_copy(raw_line)


def waybar_status():
    """Format and print Waybar module JSON."""
    paused = is_paused()
    items = get_clip_list()
    count = len(items)

    if paused:
        icon = "󰂛"
        text = f"{icon} Off"
        alt = "paused"
        css_class = "paused"
    elif count > 0:
        icon = "󰅍"
        text = f"{icon} {count}"
        alt = "has-items"
        css_class = "has-items"
    else:
        icon = "󰅌"
        text = f"{icon}"
        alt = "empty"
        css_class = "empty"

    tooltip_lines = []
    if paused:
        tooltip_lines.append("<b>󰂛 Clipboard Recording: PAUSED (Private)</b>")
    else:
        tooltip_lines.append(f"<b>󰅍 Clipboard History ({count} items)</b>")

    if count > 0:
        tooltip_lines.append("────────────────────────")
        for raw_line in items[:6]:
            clip_id, content, item_type, icon, thumb_path = format_clip_item(raw_line, create_thumb=False)
            one_liner = " ".join(content.split())
            if len(one_liner) > 38:
                one_liner = one_liner[:35] + "..."
            escaped_content = html.escape(one_liner)
            tooltip_lines.append(f"• {icon} <b>#{clip_id}</b>: {escaped_content}")
        
        if count > 6:
            tooltip_lines.append(f"<i>... and {count - 6} more</i>")
    else:
        tooltip_lines.append("<i>Clipboard history is empty</i>")

    tooltip_lines.append("────────────────────────")
    tooltip_lines.append("<b>Left Click:</b> Browse & Search History / Screenshots")
    tooltip_lines.append("<b>Right Click:</b> Delete Items / Manage History")
    tooltip_lines.append("<b>Middle Click:</b> Toggle Private Mode (Pause/Resume)")

    output = {
        "text": text,
        "alt": alt,
        "tooltip": "\n".join(tooltip_lines),
        "class": css_class
    }
    print(json.dumps(output))


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ["--status", "-s", "status"]:
            waybar_status()
            return
        elif arg in ["--menu", "-m", "menu"]:
            open_history_menu()
            return
        elif arg in ["--daemon", "-d", "daemon"]:
            start_daemon(silent=True)
            return
        elif arg in ["--toggle-pause", "-p", "toggle-pause"]:
            toggle_pause()
            return
        elif arg in ["--clear", "--wipe", "-c", "clear"]:
            clear_history()
            return
        elif arg in ["--delete", "-d", "delete"]:
            if len(sys.argv) > 2:
                target_id = sys.argv[2]
                items = get_clip_list()
                for line in items:
                    if line.startswith(target_id + "\t") or line == target_id:
                        delete_item(line)
                        break
            else:
                open_delete_menu()
            return

    open_history_menu()


if __name__ == "__main__":
    main()
