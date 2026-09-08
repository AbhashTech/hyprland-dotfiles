#!/usr/bin/env python3
import sys
import os
import re
import json
import subprocess
from pathlib import Path

THUMB_DIR = Path.home() / ".cache" / "cliphist_thumbs"

def ensure_thumb_dir():
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

def get_thumbnail(clip_id, raw_line):
    ensure_thumb_dir()
    thumb_path = THUMB_DIR / f"thumb_{clip_id}.png"
    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return str(thumb_path)
    try:
        p = subprocess.run(
            ["cliphist", "decode"],
            input=raw_line.encode("utf-8"),
            capture_output=True,
            timeout=3
        )
        if p.stdout.startswith(b"\x89PNG") or p.stdout[:2] == b"\xff\xd8":
            thumb_path.write_bytes(p.stdout)
            return str(thumb_path)
    except Exception:
        pass
    return ""

def list_clips(limit=60):
    try:
        res = subprocess.run(
            ["cliphist", "list"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=5
        )
        lines = [l for l in res.stdout.splitlines() if l.strip()]
    except Exception:
        lines = []

    items = []
    for l in lines[:limit]:
        parts = l.split("\t", 1)
        clip_id = parts[0].strip()
        txt = parts[1].strip() if len(parts) > 1 else ""

        is_image = False
        thumb = ""
        category = "text"
        icon = "󰅍"

        if "[[ binary data" in txt.lower() or txt.startswith("[[ binary"):
            is_image = True
            category = "image"
            icon = "󰋩"
            match = re.search(r'\[\[\s*binary\s+data\s+(.*?)\s*\]\]', txt, re.IGNORECASE)
            details = match.group(1) if match else "Image"
            txt = f"Screenshot / Image ({details})"
            thumb = get_thumbnail(clip_id, l)
        elif re.match(r'^https?:\/\/', txt):
            category = "url"
            icon = "󰖟"
        elif any(kw in txt for kw in ["function", "const ", "let ", "var ", "class ", "def ", "import ", "select ", "return "]) and any(c in txt for c in ["{", ";", ":", "("]):
            category = "code"
            icon = "󰅪"
        elif "\n" in txt or len(txt) > 80:
            category = "multiline"
            icon = "󰉿"

        items.append({
            "id": clip_id,
            "raw": l,
            "text": txt,
            "category": category,
            "icon": icon,
            "isImage": is_image,
            "thumbnail": thumb
        })

    print(json.dumps(items))

def copy_clip(clip_id, raw_line=None):
    try:
        if not raw_line or "\t" not in raw_line:
            res = subprocess.run(["cliphist", "list"], capture_output=True, text=True, errors="replace")
            for l in res.stdout.splitlines():
                if l.startswith(f"{clip_id}\t"):
                    raw_line = l
                    break
        if not raw_line:
            return

        p_decode = subprocess.Popen(["cliphist", "decode"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        decoded, _ = p_decode.communicate(input=raw_line.encode("utf-8"))
        if not decoded:
            return

        is_png = decoded.startswith(b"\x89PNG")
        mime = "image/png" if is_png else "text/plain;charset=utf-8"

        p_copy = subprocess.Popen(["wl-copy", "--type", mime], stdin=subprocess.PIPE)
        p_copy.communicate(input=decoded)

        subprocess.run(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"], capture_output=True)
    except Exception as e:
        sys.stderr.write(f"Copy error: {e}\n")

def delete_clip(clip_id, raw_line=None):
    try:
        # If raw_line not provided or incomplete, look up full line from cliphist list
        if not raw_line or "\t" not in raw_line:
            res = subprocess.run(["cliphist", "list"], capture_output=True, text=True, errors="replace")
            for l in res.stdout.splitlines():
                if l.startswith(f"{clip_id}\t"):
                    raw_line = l
                    break

        if raw_line:
            p = subprocess.Popen(["cliphist", "delete"], stdin=subprocess.PIPE)
            p.communicate(input=raw_line.encode("utf-8"))

        # Remove cached thumbnail if present
        if clip_id:
            thumb_path = THUMB_DIR / f"thumb_{clip_id}.png"
            if thumb_path.exists():
                thumb_path.unlink()
    except Exception as e:
        sys.stderr.write(f"Delete error: {e}\n")

def wipe():
    try:
        subprocess.run(["cliphist", "wipe"], check=True)
        if THUMB_DIR.exists():
            for f in THUMB_DIR.glob("thumb_*.png"):
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception as e:
        sys.stderr.write(f"Wipe error: {e}\n")

PAUSE_STATE_FILE = Path.home() / ".cache" / "cliphist_paused"

def is_paused():
    return PAUSE_STATE_FILE.exists()

def toggle_private():
    try:
        mgr_script = Path.home() / ".config" / "hypr" / "scripts" / "clipboard_manager.py"
        if mgr_script.exists():
            subprocess.run(["python3", str(mgr_script), "--toggle-private"], timeout=3)
        else:
            if is_paused():
                try:
                    PAUSE_STATE_FILE.unlink()
                except Exception:
                    pass
                subprocess.Popen(["notify-send", "-r", "9920", "-t", "2500", "-a", "Clipboard Manager", "-i", "edit-paste", "󰅍 Clipboard Private Mode Inactive", "Clipboard recording is now ACTIVE."], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                PAUSE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                PAUSE_STATE_FILE.write_text("1")
                subprocess.Popen(["notify-send", "-r", "9920", "-t", "2500", "-a", "Clipboard Manager", "-i", "security-high", "󰈉 Clipboard Private Mode Active", "Private mode active. Copying is not recorded."], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        sys.stderr.write(f"Toggle Private Mode error: {e}\n")

def get_status():
    dnd = is_paused()
    try:
        res = subprocess.run(
            ["cliphist", "list"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=3
        )
        lines = [l for l in res.stdout.splitlines() if l.strip()]
        count = len(lines)
    except Exception:
        count = 0
    print(json.dumps({"dnd": dnd, "private": dnd, "count": count}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_clips()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        list_clips()
    elif cmd == "status":
        get_status()
    elif cmd in ["toggle-private", "private", "toggle-dnd", "toggle-pause", "dnd"]:
        toggle_private()
    elif cmd in ["is-private", "is-dnd"]:
        print("1" if is_paused() else "0")
    elif cmd == "copy":
        cid = sys.argv[2] if len(sys.argv) > 2 else ""
        raw = sys.argv[3] if len(sys.argv) > 3 else ""
        copy_clip(cid, raw)
    elif cmd == "delete":
        cid = sys.argv[2] if len(sys.argv) > 2 else ""
        raw = sys.argv[3] if len(sys.argv) > 3 else ""
        delete_clip(cid, raw)
    elif cmd == "wipe":
        wipe()
