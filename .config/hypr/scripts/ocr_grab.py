#!/usr/bin/env python3
"""
Hyprland OCR Text Grabber
Select any area on your screen, extract text using Tesseract OCR,
copy it to your Wayland clipboard, and show a notification with the result.
"""

import sys
import shutil
import subprocess
from pathlib import Path

# Slurp styling matching Hyprland Catppuccin theme
SLURP_ARGS = ["-b", "00000044", "-c", "cba6f7ee", "-s", "00000000", "-w", "2"]

def notify(title, body, icon="edit-copy", timeout=5000):
    if not shutil.which("notify-send"):
        return
    cmd = [
        "notify-send",
        "-a", "OCR Text Grabber",
        "-i", icon,
        "-t", str(timeout),
        title,
        body
    ]
    try:
        subprocess.Popen(cmd)
    except Exception:
        pass

def main():
    # 1. Check dependencies
    if not shutil.which("grim"):
        notify("❌ Error", "grim is not installed. Run: sudo pacman -S grim", "dialog-error")
        sys.exit(1)
    if not shutil.which("slurp"):
        notify("❌ Error", "slurp is not installed. Run: sudo pacman -S slurp", "dialog-error")
        sys.exit(1)
    if not shutil.which("tesseract"):
        notify("❌ Error", "tesseract is not installed. Run: sudo pacman -S tesseract tesseract-data-eng", "dialog-error")
        sys.exit(1)
    if not shutil.which("wl-copy"):
        notify("❌ Error", "wl-clipboard is not installed. Run: sudo pacman -S wl-clipboard", "dialog-error")
        sys.exit(1)

    # 2. Select region
    res = subprocess.run(["slurp"] + SLURP_ARGS, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        sys.exit(0) # Selection cancelled by user

    geometry = res.stdout.strip()

    # 3. Capture image to grim stdout and pipe directly to tesseract
    try:
        p_grim = subprocess.Popen(["grim", "-g", geometry, "-"], stdout=subprocess.PIPE)
        p_tess = subprocess.Popen(
            ["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "6"],
            stdin=p_grim.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        p_grim.stdout.close()
        text_output, _ = p_tess.communicate()

        text = text_output.strip()
        if not text:
            notify("⚠️ OCR Result", "No text detected in the selected area.", "dialog-warning")
            sys.exit(0)

        # 4. Copy to clipboard
        p_copy = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
        p_copy.communicate(input=text)

        # 5. Show notification preview (truncate if very long)
        preview = text[:180] + ("..." if len(text) > 180 else "")
        preview_escaped = preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        notify(
            "📋 Text Copied to Clipboard",
            f"<i>{preview_escaped}</i>",
            icon="edit-copy",
            timeout=5000
        )

    except Exception as e:
        notify("❌ OCR Error", f"Failed to extract text: {e}", "dialog-error")
        sys.exit(1)

if __name__ == "__main__":
    main()
