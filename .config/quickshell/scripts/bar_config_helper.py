#!/usr/bin/env python3
"""
Bar Configuration Helper for Quickshell
Handles loading, saving, resetting, and applying presets for the dynamic bar layout.
"""

import os
import sys
import json
import argparse
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "quickshell" / "bar_config.json"

DEFAULT_CONFIG = {
    "version": 1,
    "position": "top",             # "top" | "bottom"
    "floating": True,
    "barHeight": 38,
    "barRadius": 16,
    "capsuleRadius": 12,
    "spacing": 6,
    "marginTop": 8,
    "marginBottom": 8,
    "marginLeft": 12,
    "marginRight": 12,
    "compactMode": False,
    "leftModules": [
        "launcher",
        "workspaces",
        "activewindow",
        "custom_left"
    ],
    "centerModules": [
        "mpris",
        "custom_center",
        "language"
    ],
    "rightModules": [
        "custom_right",
        "recording",
        "traynotif",
        "status",
        "stats",
        "power",
        "clock"
    ],
    "hiddenModules": []
}

PRESETS = {
    "default": DEFAULT_CONFIG,
    "minimal": {
        "version": 1,
        "position": "top",
        "floating": True,
        "barHeight": 36,
        "barRadius": 14,
        "capsuleRadius": 10,
        "spacing": 6,
        "marginTop": 8,
        "marginBottom": 8,
        "marginLeft": 12,
        "marginRight": 12,
        "compactMode": True,
        "leftModules": ["launcher", "workspaces"],
        "centerModules": ["activewindow"],
        "rightModules": ["status", "clock"],
        "hiddenModules": ["mpris", "language", "recording", "traynotif", "stats", "power"]
    },
    "poweruser": {
        "version": 1,
        "position": "top",
        "floating": True,
        "barHeight": 40,
        "barRadius": 16,
        "capsuleRadius": 12,
        "spacing": 6,
        "marginTop": 8,
        "marginBottom": 8,
        "marginLeft": 12,
        "marginRight": 12,
        "compactMode": False,
        "leftModules": ["launcher", "workspaces", "activewindow", "custom_left"],
        "centerModules": ["mpris", "custom_center"],
        "rightModules": ["custom_right", "recording", "traynotif", "status", "stats", "language", "power", "clock"],
        "hiddenModules": []
    },
    "dock": {
        "version": 1,
        "position": "bottom",
        "floating": True,
        "barHeight": 44,
        "barRadius": 22,
        "capsuleRadius": 14,
        "spacing": 8,
        "marginTop": 8,
        "marginBottom": 10,
        "marginLeft": 24,
        "marginRight": 24,
        "compactMode": False,
        "leftModules": ["launcher", "workspaces"],
        "centerModules": ["activewindow", "mpris"],
        "rightModules": ["traynotif", "status", "clock", "power"],
        "hiddenModules": ["stats", "recording", "language"]
    },
    "split": {
        "version": 1,
        "position": "top",
        "floating": True,
        "barHeight": 38,
        "barRadius": 16,
        "capsuleRadius": 12,
        "spacing": 6,
        "marginTop": 8,
        "marginBottom": 8,
        "marginLeft": 12,
        "marginRight": 12,
        "compactMode": False,
        "leftModules": ["launcher", "workspaces", "activewindow"],
        "centerModules": ["clock"],
        "rightModules": ["mpris", "traynotif", "status", "power"],
        "hiddenModules": ["stats", "recording", "language"]
    }
}

MODULE_CATALOG = [
    {
        "id": "launcher",
        "name": "Application Launcher",
        "icon": "󰣇",
        "description": "App menu launcher and quick system power toggle",
        "category": "navigation",
        "defaultSection": "left"
    },
    {
        "id": "workspaces",
        "name": "Workspaces",
        "icon": "󰨇",
        "description": "Virtual desktops indicator and interactive switcher",
        "category": "navigation",
        "defaultSection": "left"
    },
    {
        "id": "activewindow",
        "name": "Active Window",
        "icon": "󰘔",
        "description": "Displays current focused window title and app class",
        "category": "info",
        "defaultSection": "left"
    },
    {
        "id": "mpris",
        "name": "Media Player (MPRIS)",
        "icon": "󰎈",
        "description": "Now playing track information and playback controls",
        "category": "media",
        "defaultSection": "center"
    },
    {
        "id": "language",
        "name": "Keyboard Layout",
        "icon": "󰌌",
        "description": "Current active keyboard layout and language switcher",
        "category": "system",
        "defaultSection": "center"
    },
    {
        "id": "recording",
        "name": "Screen Recording Indicator",
        "icon": "󰑋",
        "description": "Active screen capture / recording status and stop trigger",
        "category": "system",
        "defaultSection": "right"
    },
    {
        "id": "traynotif",
        "name": "Tray & Notification Hub",
        "icon": "󰂚",
        "description": "System tray icons, clipboard history quick button, and notifications",
        "category": "system",
        "defaultSection": "right"
    },
    {
        "id": "status",
        "name": "Status Group",
        "icon": "󰤨",
        "description": "Audio volume, brightness, Wi-Fi, Bluetooth, and battery gauges",
        "category": "hardware",
        "defaultSection": "right"
    },
    {
        "id": "stats",
        "name": "System Hardware Stats",
        "icon": "󰍛",
        "description": "Live CPU, RAM, GPU, and system resource monitors",
        "category": "hardware",
        "defaultSection": "right"
    },
    {
        "id": "power",
        "name": "Power & Session",
        "icon": "",
        "description": "System logout, lock, reboot, and shutdown menu launcher",
        "category": "system",
        "defaultSection": "right"
    },
    {
        "id": "clock",
        "name": "Clock & Calendar",
        "icon": "",
        "description": "Time display, date toggling, and interactive calendar popup",
        "category": "time",
        "defaultSection": "right"
    },
    {
        "id": "custom_left",
        "name": "Left Custom Plugins",
        "icon": "󰏖",
        "description": "Custom user plugins placed in the left section",
        "category": "plugins",
        "defaultSection": "left"
    },
    {
        "id": "custom_center",
        "name": "Center Custom Plugins",
        "icon": "󰏖",
        "description": "Custom user plugins placed in the center section",
        "category": "plugins",
        "defaultSection": "center"
    },
    {
        "id": "custom_right",
        "name": "Right Custom Plugins",
        "icon": "󰏖",
        "description": "Custom user plugins placed in the right section",
        "category": "plugins",
        "defaultSection": "right"
    }
]

def load_config():
    if CONFIG_PATH.is_file():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(DEFAULT_CONFIG)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = CONFIG_PATH.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    temp_path.replace(CONFIG_PATH)

def get_discovered_custom_plugins():
    custom_dir = Path.home() / ".config" / "quickshell" / "custom_plugins"
    plugins = []
    if custom_dir.is_dir():
        for item in sorted(custom_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                manifest_path = item / "manifest.json"
                name = item.name
                icon = "󰏖"
                desc = f"Custom plugin: {item.name}"
                pos = "center"
                if manifest_path.is_file():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            m = json.load(f)
                            name = m.get("name", name)
                            icon = m.get("icon", icon)
                            desc = m.get("description", desc)
                            pos = m.get("position", pos).lower()
                    except Exception:
                        pass
                plugins.append({
                    "id": f"plugin_{item.name}",
                    "name": name,
                    "icon": icon,
                    "description": desc,
                    "category": "custom",
                    "defaultSection": pos
                })
    return plugins

def get_full_catalog():
    catalog = list(MODULE_CATALOG)
    custom = get_discovered_custom_plugins()
    for cp in custom:
        if not any(c["id"] == cp["id"] for c in catalog):
            catalog.append(cp)
    return catalog

def main():
    parser = argparse.ArgumentParser(description="Quickshell Bar Configuration Manager")
    parser.add_argument("action", choices=[
        "get", "save", "reset", "preset", "move", "reorder", "toggle", 
        "catalog", "set-position", "set-metric"
    ], help="Action to perform")
    parser.add_argument("--json-data", help="JSON data string for save action")
    parser.add_argument("--preset-name", help="Preset name for preset action")
    parser.add_argument("--module-id", help="Module ID for move/toggle action")
    parser.add_argument("--target-section", choices=["left", "center", "right", "hidden"], help="Target section")
    parser.add_argument("--target-index", type=int, default=-1, help="Target index in section")
    parser.add_argument("--from-section", choices=["left", "center", "right"], help="From section for reorder")
    parser.add_argument("--from-index", type=int, help="From index for reorder")
    parser.add_argument("--to-section", choices=["left", "center", "right"], help="To section for reorder")
    parser.add_argument("--to-index", type=int, help="To index for reorder")
    parser.add_argument("--direction", choices=["left", "right", "up", "down"], help="Direction for step move")
    parser.add_argument("--position", choices=["top", "bottom"], help="Bar position")
    parser.add_argument("--key", help="Key for set-metric")
    parser.add_argument("--value", help="Value for set-metric")

    args = parser.parse_args()

    if args.action == "get":
        cfg = load_config()
        print(json.dumps(cfg, indent=2))
        return

    if args.action == "catalog":
        cat = get_full_catalog()
        print(json.dumps(cat, indent=2))
        return

    if args.action == "reset":
        save_config(DEFAULT_CONFIG)
        print(json.dumps({"success": True, "config": DEFAULT_CONFIG}))
        return

    if args.action == "preset":
        name = (args.preset_name or "default").lower()
        preset = PRESETS.get(name, DEFAULT_CONFIG)
        save_config(preset)
        print(json.dumps({"success": True, "preset": name, "config": preset}))
        return

    if args.action == "save":
        if args.json_data:
            try:
                data = json.loads(args.json_data)
                save_config(data)
                print(json.dumps({"success": True}))
                return
            except Exception as e:
                print(json.dumps({"success": False, "error": str(e)}))
                sys.exit(1)
        else:
            print(json.dumps({"success": False, "error": "Missing --json-data"}))
            sys.exit(1)

    if args.action == "set-position":
        if args.position:
            cfg = load_config()
            cfg["position"] = args.position
            save_config(cfg)
            print(json.dumps({"success": True, "position": args.position}))
            return

    if args.action == "set-metric":
        if args.key and args.value is not None:
            cfg = load_config()
            try:
                if args.value.lower() in ["true", "false"]:
                    val = (args.value.lower() == "true")
                elif args.value.isdigit():
                    val = int(args.value)
                else:
                    try:
                        val = float(args.value)
                    except ValueError:
                        val = args.value
                cfg[args.key] = val
                save_config(cfg)
                print(json.dumps({"success": True, "key": args.key, "value": val}))
                return
            except Exception as e:
                print(json.dumps({"success": False, "error": str(e)}))
                sys.exit(1)

    if args.action == "move":
        if not args.module_id or not args.target_section:
            print(json.dumps({"success": False, "error": "Missing module-id or target-section"}))
            sys.exit(1)

        cfg = load_config()
        mod_id = args.module_id
        target = args.target_section
        idx = args.target_index

        for sec in ["leftModules", "centerModules", "rightModules", "hiddenModules"]:
            if mod_id in cfg.get(sec, []):
                cfg[sec].remove(mod_id)

        target_key = f"{target}Modules" if target != "hidden" else "hiddenModules"
        if target_key not in cfg:
            cfg[target_key] = []

        if idx is not None and 0 <= idx <= len(cfg[target_key]):
            cfg[target_key].insert(idx, mod_id)
        else:
            cfg[target_key].append(mod_id)

        save_config(cfg)
        print(json.dumps({"success": True, "config": cfg}))
        return

    if args.action == "reorder":
        from_sec = f"{args.from_section}Modules"
        to_sec = f"{args.to_section}Modules"
        from_idx = args.from_index
        to_idx = args.to_index

        cfg = load_config()
        if from_sec in cfg and 0 <= from_idx < len(cfg[from_sec]):
            item = cfg[from_sec].pop(from_idx)
            if to_sec not in cfg:
                cfg[to_sec] = []
            if 0 <= to_idx <= len(cfg[to_sec]):
                cfg[to_sec].insert(to_idx, item)
            else:
                cfg[to_sec].append(item)
            save_config(cfg)
            print(json.dumps({"success": True, "config": cfg}))
            return

    if args.action == "toggle":
        if not args.module_id:
            print(json.dumps({"success": False, "error": "Missing module-id"}))
            sys.exit(1)

        cfg = load_config()
        mod_id = args.module_id
        is_hidden = mod_id in cfg.get("hiddenModules", [])

        if is_hidden:
            cfg["hiddenModules"].remove(mod_id)
            cat = get_full_catalog()
            def_sec = "center"
            for m in cat:
                if m["id"] == mod_id:
                    def_sec = m.get("defaultSection", "center")
                    break
            sec_key = f"{def_sec}Modules"
            if sec_key not in cfg:
                cfg[sec_key] = []
            cfg[sec_key].append(mod_id)
        else:
            for sec in ["leftModules", "centerModules", "rightModules"]:
                if mod_id in cfg.get(sec, []):
                    cfg[sec].remove(mod_id)
            if "hiddenModules" not in cfg:
                cfg["hiddenModules"] = []
            cfg["hiddenModules"].append(mod_id)

        save_config(cfg)
        print(json.dumps({"success": True, "config": cfg}))
        return

if __name__ == "__main__":
    main()
