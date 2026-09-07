#!/usr/bin/env python3
"""
Desktop Applications Indexer & Search Provider for Quickshell App Menu
Scans /usr/share/applications and ~/.local/share/applications and generates
a fast cached JSON catalog with fuzzy search capability.
"""

import os
import sys
import glob
import json
import configparser
from pathlib import Path

CACHE_FILE = Path.home() / ".cache" / "quickshell_apps.json"

CATEGORIES = {
    "Development": ["Development", "IDE", "TextEditor"],
    "Internet": ["Network", "WebBrowser", "Email", "Chat", "InstantMessaging"],
    "Multimedia": ["AudioVideo", "Audio", "Video", "Player", "Recorder"],
    "Graphics": ["Graphics", "RasterGraphics", "VectorGraphics", "Photography"],
    "Office": ["Office", "WordProcessor", "Spreadsheet"],
    "System": ["System", "Monitor", "Settings", "TerminalEmulator", "FileManager"],
    "Utilities": ["Utility", "Core", "Archiving", "Compression", "Calculator"],
}

CATEGORY_ICONS = {
    "All": "󰀻",
    "Internet": "󰖟",
    "Development": "󰅩",
    "Multimedia": "󰕼",
    "Graphics": "󰹉",
    "Office": "󰈙",
    "System": "󰒋",
    "Utilities": "󰋜",
}

ICON_ALIASES = {
    "firefox": "firefox",
    "kitty": "kitty",
    "dolphin": "system-file-manager",
    "code": "visual-studio-code",
    "spotify": "spotify",
    "discord": "discord",
    "telegram": "telegram",
    "vlc": "vlc",
    "btop": "utilities-system-monitor",
}

def scan_desktop_files():
    apps = []
    seen = set()
    dirs = [
        Path.home() / ".local" / "share" / "applications",
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
        Path("/var/lib/flatpak/exports/share/applications"),
    ]

    for d in dirs:
        if not d.is_dir():
            continue
        for f in d.glob("*.desktop"):
            base = f.name
            if base in seen:
                continue
            seen.add(base)

            config = configparser.ConfigParser(interpolation=None)
            try:
                config.read(f, encoding="utf-8")
                if not config.has_section("Desktop Entry"):
                    continue
                entry = config["Desktop Entry"]
                if entry.getboolean("NoDisplay", fallback=False):
                    continue
                if entry.getboolean("Hidden", fallback=False):
                    continue
                if entry.get("Type", "Application") != "Application":
                    continue

                name = entry.get("Name", "").strip()
                if not name:
                    continue
                exec_cmd = entry.get("Exec", "").strip()
                if not exec_cmd:
                    continue

                # Strip field codes (%f, %u, %F, %U, etc.)
                clean_exec = " ".join([part for part in exec_cmd.split() if not part.startswith("%")])

                comment = entry.get("Comment", "").strip()
                icon = entry.get("Icon", "application-x-executable").strip()
                raw_cats = entry.get("Categories", "").strip().split(";")

                assigned_cat = "Utilities"
                for cat_label, match_keys in CATEGORIES.items():
                    if any(k in raw_cats for k in match_keys):
                        assigned_cat = cat_label
                        break

                apps.append({
                    "id": base,
                    "name": name,
                    "exec": clean_exec,
                    "comment": comment,
                    "icon": icon,
                    "category": assigned_cat,
                    "terminal": entry.getboolean("Terminal", fallback=False)
                })
            except Exception:
                continue

    apps.sort(key=lambda a: a["name"].lower())
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as out:
            json.dump(apps, out, indent=2)
    except Exception:
        pass
    return apps

def load_apps():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return scan_desktop_files()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--scan":
        apps = scan_desktop_files()
        print(json.dumps(apps))
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--launch" and len(sys.argv) > 2:
        exec_str = " ".join(sys.argv[2:])
        os.system(f"{exec_str} &")
        return

    apps = load_apps()
    print(json.dumps(apps))

if __name__ == "__main__":
    main()
