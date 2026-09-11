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
    "foot": "foot",
    "dolphin": "system-file-manager",
    "code": "visual-studio-code",
    "spotify": "spotify",
    "discord": "discord",
    "telegram": "telegram",
    "vlc": "vlc",
    "btop": "utilities-system-monitor",
}

def get_current_icon_theme():
    gtk3_ini = Path.home() / ".config" / "gtk-3.0" / "settings.ini"
    if gtk3_ini.exists():
        cp = configparser.ConfigParser()
        try:
            cp.read(gtk3_ini)
            if "Settings" in cp and "gtk-icon-theme-name" in cp["Settings"]:
                return cp["Settings"]["gtk-icon-theme-name"].strip()
        except Exception:
            pass
    return "Papirus-Light"

ICON_EXTS = [".svg", ".png", ".xpm"]

def resolve_icon_path(icon_name):
    if not icon_name:
        return ""
    if icon_name.startswith("/") or icon_name.startswith("file://"):
        p = icon_name.replace("file://", "")
        return f"file://{p}" if os.path.exists(p) else ""

    theme = get_current_icon_theme()
    base_name = os.path.splitext(icon_name)[0]

    theme_dirs = [
        Path.home() / ".local" / "share" / "icons",
        Path(f"/usr/share/icons/{theme}"),
        Path("/usr/share/icons/Papirus"),
        Path("/usr/share/icons/Papirus-Dark"),
        Path("/usr/share/icons/Papirus-Light"),
        Path.home() / ".local" / "share" / "icons" / "hicolor",
        Path("/usr/share/icons/hicolor"),
        Path("/usr/share/pixmaps"),
    ]

    for b in theme_dirs:
        if not b.exists():
            continue
        for name_variant in (icon_name, base_name):
            for ext in ICON_EXTS:
                cand = b / f"{name_variant}{ext}"
                if cand.exists():
                    return f"file://{cand}"

        for sub in [
            "48x48/apps", "scalable/apps", "64x64/apps", "32x32/apps", "128x128/apps", "256x256/apps",
            "48x48/categories", "64x64/categories", "32x32/categories",
            "symbolic/apps", "24x24/apps", "16x16/apps", "22x22/apps"
        ]:
            d = b / sub
            if d.exists():
                for name_variant in (icon_name, base_name):
                    for ext in ICON_EXTS:
                        cand = d / f"{name_variant}{ext}"
                        if cand.exists():
                            return f"file://{cand}"
    return ""


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

                icon_path = resolve_icon_path(icon)

                apps.append({
                    "id": base,
                    "name": name,
                    "exec": clean_exec,
                    "comment": comment,
                    "icon": icon,
                    "iconPath": icon_path,
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
            cache_mtime = CACHE_FILE.stat().st_mtime
            dirs = [
                Path.home() / ".local" / "share" / "applications",
                Path("/usr/local/share/applications"),
                Path("/usr/share/applications"),
                Path("/var/lib/flatpak/exports/share/applications"),
            ]
            stale = any(
                d.exists() and (
                    d.stat().st_mtime > cache_mtime or
                    any(f.stat().st_mtime > cache_mtime for f in d.glob("*.desktop"))
                )
                for d in dirs
            )
            if not stale:
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
        os.system(f"env -u LD_PRELOAD nohup {exec_str} </dev/null >/dev/null 2>&1 &")
        return

    apps = load_apps()
    print(json.dumps(apps))

if __name__ == "__main__":
    main()
