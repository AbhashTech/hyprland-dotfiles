#!/usr/bin/env python3
"""
Hyprland OCR Text Grabber
Select any area on your screen, extract text using Tesseract OCR (with configurable language),
copy it to your Wayland clipboard, and show a notification with the result.
"""

import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".config" / "hypr"
OCR_CONFIG_PATH = CONFIG_DIR / "ocr_config.json"
USER_TESSDATA_DIR = Path.home() / ".local" / "share" / "tessdata"
SYSTEM_TESSDATA_DIR = Path("/usr/share/tessdata")
LANG_MANAGER_SCRIPT = CONFIG_DIR / "scripts" / "ocr_language_manager.py"

# Slurp styling matching Hyprland Catppuccin theme
SLURP_ARGS = ["-b", "00000044", "-c", "cba6f7ee", "-s", "00000000", "-w", "2"]

def notify(title, body, icon="edit-copy", actions=None, timeout=5000):
    if not shutil.which("notify-send"):
        return
    cmd = [
        "notify-send",
        "-a", "OCR Text Grabber",
        "-i", icon,
        "-t", str(timeout),
    ]
    if actions:
        for act_id, act_label in actions:
            cmd.append(f"--action={act_id}={act_label}")
    cmd.extend([title, body])

    try:
        if actions:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
            out, _ = proc.communicate()
            return out.strip()
        else:
            subprocess.Popen(cmd)
    except Exception:
        pass
    return None

def get_active_ocr_language():
    """Retrieve active OCR language code from config, falling back to 'eng'."""
    if OCR_CONFIG_PATH.exists():
        try:
            with open(OCR_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_language", "eng"), data.get("psm", "6")
        except Exception:
            pass
    return "eng", "6"

def get_tessdata_dir():
    """Determine best tessdata directory path."""
    if USER_TESSDATA_DIR.exists() and any(USER_TESSDATA_DIR.glob("*.traineddata")):
        return str(USER_TESSDATA_DIR)
    if SYSTEM_TESSDATA_DIR.exists():
        return str(SYSTEM_TESSDATA_DIR)
    return None

def main():
    parser = argparse.ArgumentParser(description="Grab screen text with OCR")
    parser.add_argument("-l", "--lang", type=str, help="Override OCR language (e.g. 'eng', 'hin', 'fra', 'eng+hin')")
    parser.add_argument("--psm", type=str, help="Page segmentation mode (default: 6)")
    args = parser.parse_args()

    # 1. Check dependencies
    if not shutil.which("grim"):
        notify("❌ Error", "grim is not installed. Run: sudo pacman -S grim", "dialog-error")
        sys.exit(1)
    if not shutil.which("slurp"):
        notify("❌ Error", "slurp is not installed. Run: sudo pacman -S slurp", "dialog-error")
        sys.exit(1)
    if not shutil.which("tesseract"):
        notify("❌ Error", "tesseract is not installed. Run: sudo pacman -S tesseract", "dialog-error")
        sys.exit(1)
    if not shutil.which("wl-copy"):
        notify("❌ Error", "wl-clipboard is not installed. Run: sudo pacman -S wl-clipboard", "dialog-error")
        sys.exit(1)

    # 2. Determine OCR language and options
    cfg_lang, cfg_psm = get_active_ocr_language()
    lang = args.lang or cfg_lang
    psm = args.psm or cfg_psm

    # 3. Select region
    res = subprocess.run(["slurp"] + SLURP_ARGS, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        sys.exit(0) # Selection cancelled by user

    geometry = res.stdout.strip()

    # 4. Capture image to grim stdout and pipe directly to tesseract
    try:
        tess_cmd = ["tesseract", "stdin", "stdout", "-l", lang, "--psm", str(psm)]
        tess_dir = get_tessdata_dir()
        if tess_dir:
            tess_cmd.extend(["--tessdata-dir", tess_dir])

        p_grim = subprocess.Popen(["grim", "-g", geometry, "-"], stdout=subprocess.PIPE)
        p_tess = subprocess.Popen(
            tess_cmd,
            stdin=p_grim.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        p_grim.stdout.close()
        text_output, stderr_out = p_tess.communicate()

        # Handle missing language model error
        if p_tess.returncode != 0 and "Failed loading language" in stderr_out:
            actions = [("manage", "🌐 Manage Languages")]
            sel = notify(
                "⚠️ OCR Language Missing",
                f"Model for language '<b>{lang}</b>' is not installed.\nOpen the Language Manager to install it.",
                icon="dialog-warning",
                actions=actions,
                timeout=7000
            )
            if sel == "manage" and LANG_MANAGER_SCRIPT.exists():
                subprocess.Popen(["python3", str(LANG_MANAGER_SCRIPT), "--gui"])
            sys.exit(1)

        text = text_output.strip()
        if not text:
            notify("⚠️ OCR Result", f"No text detected in selected area ({lang}).", "dialog-warning")
            sys.exit(0)

        # 5. Copy to clipboard
        p_copy = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
        p_copy.communicate(input=text)

        # Print to stdout
        print(text)

        # 6. Show notification preview (truncate if very long)
        preview = text[:180] + ("..." if len(text) > 180 else "")
        preview_escaped = preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        actions = [("manage", "🌐 Change Language")]
        sel = notify(
            f"📋 Text Copied ({lang.upper()})",
            f"<i>{preview_escaped}</i>",
            icon="edit-copy",
            actions=actions,
            timeout=5000
        )
        if sel == "manage" and LANG_MANAGER_SCRIPT.exists():
            subprocess.Popen(["python3", str(LANG_MANAGER_SCRIPT), "--gui"])

    except Exception as e:
        notify("❌ OCR Error", f"Failed to extract text: {e}", "dialog-error")
        sys.exit(1)

if __name__ == "__main__":
    main()
