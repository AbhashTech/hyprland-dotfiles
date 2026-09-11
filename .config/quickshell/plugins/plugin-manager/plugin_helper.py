#!/usr/bin/env python3
"""
Quickshell Plugin Manager Helper
Handles plugin discovery, enabling/disabling, deletion, template scaffolding, git installation,
manifest editing, dependency checks, export/backup, git pull/log, curated store, and shell reload.
"""

import sys
import os
import json
import shutil
import subprocess
import re
import tarfile
import zipfile
import time
from pathlib import Path

CUSTOM_PLUGINS_DIR = Path(os.path.expanduser("~/.config/quickshell/custom_plugins"))
BUILTIN_PLUGINS_DIR = Path(os.path.expanduser("~/.config/quickshell/plugins"))
SCRIPTS_DIR = Path(os.path.expanduser("~/.config/quickshell/scripts"))
BACKUP_DIR = Path(os.path.expanduser("~/.cache/quickshell_backups"))

# Curated Community & Built-in Store Catalog
STORE_CATALOG = [
    {
        "id": "pomodoro",
        "name": "Pomodoro & Focus Timer",
        "category": "Productivity",
        "version": "1.0.0",
        "author": "Quickshell Community",
        "icon": "󰔛",
        "description": "Customizable 25/5 interval focus timer with ringing chime, topbar countdown capsule, and stats tracking drawer.",
        "position": "center",
        "hasWidget": True,
        "hasWindow": True,
        "hasService": True,
        "dependencies": ["paplay", "notify-send"],
        "tags": ["Timer", "Focus", "Sound", "Widget"]
    },
    {
        "id": "weather_forecast",
        "name": "Live Weather & 7-Day Forecast",
        "category": "Utility",
        "version": "1.1.0",
        "author": "Quickshell Community",
        "icon": "󰖐",
        "description": "Real-time weather conditions, hourly forecast graphs, UV index, and 7-day predictive cards powered by Open-Meteo API.",
        "position": "center",
        "hasWidget": True,
        "hasWindow": True,
        "hasService": True,
        "dependencies": ["curl", "python3"],
        "tags": ["Weather", "Forecast", "OpenMeteo", "API"]
    },
    {
        "id": "media_visualizer",
        "name": "MPRIS Media & Audio Visualizer",
        "category": "Media",
        "version": "1.0.0",
        "author": "Quickshell Community",
        "icon": "󰎈",
        "description": "Interactive media playback capsule with animated audio visualizer waves, album art caching, lyrics drawer, and seek bar.",
        "position": "left",
        "hasWidget": True,
        "hasWindow": True,
        "hasService": False,
        "dependencies": ["playerctl"],
        "tags": ["Audio", "MPRIS", "Spotify", "Music"]
    },
    {
        "id": "sys_resource_monitor",
        "name": "Hardware & GPU Resource Monitor",
        "category": "System",
        "version": "1.0.0",
        "author": "Quickshell Community",
        "icon": "󰘚",
        "description": "Live CPU per-core frequencies, GPU VRAM & temp sensors, NVMe drive I/O speed, and memory pressure gauges.",
        "position": "right",
        "hasWidget": True,
        "hasWindow": True,
        "hasService": True,
        "dependencies": ["sensors", "python3"],
        "tags": ["Hardware", "GPU", "CPU", "Sensors"]
    },
    {
        "id": "github_tracker",
        "name": "GitHub Pull Requests & CI Tracker",
        "category": "Development",
        "version": "1.0.0",
        "author": "Quickshell Community",
        "icon": "󰊤",
        "description": "Status bar badge for unread GitHub notifications, open pull request reviews, and GitHub Actions workflow status alerts.",
        "position": "right",
        "hasWidget": True,
        "hasWindow": True,
        "hasService": True,
        "dependencies": ["gh", "curl"],
        "tags": ["GitHub", "Git", "CI/CD", "Notifications"]
    }
]


def run_cmd(cmd, cwd=None):
    """Execute command safely and return output."""
    try:
        res = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def get_dir_size(path: Path) -> int:
    """Calculate directory size in bytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file() and not entry.is_symlink():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def format_bytes(size: int) -> str:
    """Format bytes into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} B"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_git_info(path: Path):
    """Check if directory is a git repo and return branch & remote."""
    git_dir = path / ".git"
    if not git_dir.exists():
        return False, "", "", 0
    
    branch = ""
    remote = ""
    ok, out, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(path))
    if ok and out:
        branch = out
    ok, out, _ = run_cmd(["git", "config", "--get", "remote.origin.url"], cwd=str(path))
    if ok and out:
        remote = out
        
    # Count commits
    commit_count = 0
    ok, out, _ = run_cmd(["git", "rev-list", "--count", "HEAD"], cwd=str(path))
    if ok and out and out.isdigit():
        commit_count = int(out)

    return True, branch, remote, commit_count


def check_dependencies(dep_list):
    """Verify which CLI binaries are available on the OS."""
    if not dep_list or not isinstance(dep_list, list):
        return {"allSatisfied": True, "deps": []}
    
    results = []
    all_ok = True
    for dep in dep_list:
        clean = str(dep).strip()
        if not clean:
            continue
        found = shutil.which(clean) is not None
        if not found:
            all_ok = False
        results.append({
            "name": clean,
            "installed": found,
            "path": shutil.which(clean) or ""
        })
    return {"allSatisfied": all_ok, "deps": results}


def trigger_loader_only():
    """Trigger plugin manifest loader without restarting full shell."""
    loader_script = SCRIPTS_DIR / "plugin_loader.sh"
    if loader_script.is_file():
        run_cmd(["bash", str(loader_script)])
    return True


def reload_quickshell():
    """Trigger plugin manifest loader and quickshell restart."""
    trigger_loader_only()
    launch_script = SCRIPTS_DIR / "launch_quickshell.sh"
    if launch_script.is_file():
        run_cmd(["bash", str(launch_script), "--restart"])
    return True


def find_custom_plugin_path(plugin_id_or_folder: str):
    """Find the directory path of a custom plugin by ID or folder name."""
    if not CUSTOM_PLUGINS_DIR.is_dir():
        return None, None
    for entry in os.listdir(CUSTOM_PLUGINS_DIR):
        p = CUSTOM_PLUGINS_DIR / entry
        if not p.is_dir():
            continue
        m_file = p / "manifest.json"
        if entry == plugin_id_or_folder:
            return p, m_file
        if m_file.is_file():
            try:
                with open(m_file, "r") as f:
                    data = json.load(f)
                    if data.get("id") == plugin_id_or_folder:
                        return p, m_file
            except Exception:
                pass
    return None, None


def list_plugins():
    """Scan both custom and builtin plugins and return structured JSON."""
    custom_plugins = []
    builtin_plugins = []

    # 1. Custom Plugins
    if CUSTOM_PLUGINS_DIR.is_dir():
        for entry in sorted(os.listdir(CUSTOM_PLUGINS_DIR)):
            plugin_path = CUSTOM_PLUGINS_DIR / entry
            if not plugin_path.is_dir() or entry.startswith("."):
                continue

            manifest_file = plugin_path / "manifest.json"
            manifest = {}
            has_manifest = False
            if manifest_file.is_file():
                try:
                    with open(manifest_file, "r") as f:
                        manifest = json.load(f)
                        has_manifest = True
                except Exception:
                    pass

            plugin_id = manifest.get("id", entry)
            name = manifest.get("name", entry.replace("-", " ").replace("_", " ").title())
            version = manifest.get("version", "1.0.0")
            author = manifest.get("author", "User")
            description = manifest.get("description", "Custom Quickshell plugin component")
            enabled = manifest.get("enabled", True)
            position = manifest.get("position", "center").lower()
            kinds = manifest.get("kinds", [])
            entry_points = manifest.get("entryPoints", {})
            dependencies = manifest.get("dependencies", [])

            # Infer kinds if empty
            if not kinds:
                kinds = []
                if entry_points.get("barWidget") or any(f.endswith("Module.qml") for f in os.listdir(plugin_path)):
                    kinds.append("bar-widget")
                if entry_points.get("windows") or any(f.endswith("Window.qml") for f in os.listdir(plugin_path)):
                    kinds.append("window")
                if entry_points.get("service") or any(f.endswith("Service.qml") for f in os.listdir(plugin_path)):
                    kinds.append("service")

            is_git, git_branch, git_remote, git_commits = get_git_info(plugin_path)
            size_bytes = get_dir_size(plugin_path)
            files_count = len([p for p in plugin_path.rglob("*") if p.is_file() and not p.name.startswith(".")])
            dep_status = check_dependencies(dependencies)

            custom_plugins.append({
                "id": plugin_id,
                "folderName": entry,
                "name": name,
                "version": version,
                "author": author,
                "description": description,
                "enabled": enabled,
                "position": position,
                "kinds": kinds,
                "entryPoints": entry_points,
                "dependencies": dependencies,
                "dependencyStatus": dep_status,
                "path": str(plugin_path),
                "isCustom": True,
                "hasManifest": has_manifest,
                "hasGit": is_git,
                "gitBranch": git_branch,
                "gitRemote": git_remote,
                "gitCommits": git_commits,
                "sizeBytes": size_bytes,
                "sizeFormatted": format_bytes(size_bytes),
                "filesCount": files_count
            })

    # 2. Builtin Plugins
    if BUILTIN_PLUGINS_DIR.is_dir():
        for entry in sorted(os.listdir(BUILTIN_PLUGINS_DIR)):
            builtin_path = BUILTIN_PLUGINS_DIR / entry
            if not builtin_path.is_dir() or entry.startswith("."):
                continue

            builtin_plugins.append({
                "id": entry,
                "folderName": entry,
                "name": entry.replace("-", " ").replace("_", " ").title(),
                "version": "Core",
                "author": "Quickshell System",
                "description": f"Built-in core module ({entry})",
                "enabled": True,
                "position": "core",
                "kinds": ["window", "core"],
                "entryPoints": {},
                "dependencies": [],
                "dependencyStatus": {"allSatisfied": True, "deps": []},
                "path": str(builtin_path),
                "isCustom": False,
                "hasManifest": False,
                "hasGit": False,
                "gitBranch": "",
                "gitRemote": "",
                "gitCommits": 0,
                "sizeBytes": get_dir_size(builtin_path),
                "sizeFormatted": format_bytes(get_dir_size(builtin_path)),
                "filesCount": len([p for p in builtin_path.rglob("*") if p.is_file()])
            })

    total_custom = len(custom_plugins)
    active_custom = len([p for p in custom_plugins if p["enabled"]])
    disabled_custom = total_custom - active_custom

    return {
        "success": True,
        "stats": {
            "totalCustom": total_custom,
            "activeCustom": active_custom,
            "disabledCustom": disabled_custom,
            "totalBuiltin": len(builtin_plugins)
        },
        "customPlugins": custom_plugins,
        "builtinPlugins": builtin_plugins
    }


def toggle_plugin(plugin_id_or_folder: str, enabled_state: bool):
    """Enable or disable a custom plugin."""
    target_path, manifest_file = find_custom_plugin_path(plugin_id_or_folder)
    if not target_path:
        return {"success": False, "error": f"Plugin '{plugin_id_or_folder}' not found"}

    manifest = {}
    if manifest_file and manifest_file.is_file():
        try:
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    manifest["schemaVersion"] = manifest.get("schemaVersion", 1)
    manifest["id"] = manifest.get("id", target_path.name)
    manifest["name"] = manifest.get("name", target_path.name.replace("-", " ").replace("_", " ").title())
    manifest["enabled"] = enabled_state

    with open(target_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    trigger_loader_only()

    return {
        "success": True,
        "pluginId": manifest["id"],
        "folderName": target_path.name,
        "enabled": enabled_state
    }


def update_manifest(plugin_id_or_folder: str, updates: dict):
    """Update fields in a plugin's manifest.json (e.g. position, name, desc)."""
    target_path, manifest_file = find_custom_plugin_path(plugin_id_or_folder)
    if not target_path:
        return {"success": False, "error": f"Plugin '{plugin_id_or_folder}' not found"}

    manifest = {}
    if manifest_file and manifest_file.is_file():
        try:
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    # Merge updates
    for key, val in updates.items():
        if key in ["position", "name", "description", "author", "version", "enabled", "dependencies"]:
            manifest[key] = val

    manifest["schemaVersion"] = manifest.get("schemaVersion", 1)
    manifest["id"] = manifest.get("id", target_path.name)

    with open(target_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    trigger_loader_only()

    return {
        "success": True,
        "pluginId": manifest["id"],
        "folderName": target_path.name,
        "manifest": manifest
    }


def delete_plugin(plugin_id_or_folder: str):
    """Safely delete a custom plugin folder."""
    if plugin_id_or_folder in ["plugin-manager", "plugin_manager"]:
        return {"success": False, "error": "Cannot delete the Plugin Manager itself!"}

    target_path, _ = find_custom_plugin_path(plugin_id_or_folder)
    if not target_path or not target_path.exists():
        return {"success": False, "error": f"Plugin '{plugin_id_or_folder}' not found"}

    # Safety check: Ensure target_path is strictly within CUSTOM_PLUGINS_DIR
    try:
        resolved = target_path.resolve()
        if not str(resolved).startswith(str(CUSTOM_PLUGINS_DIR.resolve())):
            return {"success": False, "error": "Target path is outside custom plugins directory"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    shutil.rmtree(target_path)
    trigger_loader_only()

    return {
        "success": True,
        "deletedFolder": target_path.name,
        "pluginId": plugin_id_or_folder
    }


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase for QML components."""
    words = re.split(r'[-_\s]+', text)
    return ''.join(word.capitalize() for word in words if word)


def create_plugin(config: dict):
    """Scaffold a new custom plugin from template."""
    raw_id = config.get("id", "").strip()
    if not raw_id:
        return {"success": False, "error": "Plugin ID is required"}

    # Sanitize ID
    clean_id = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_id.lower())
    folder_name = clean_id
    plugin_path = CUSTOM_PLUGINS_DIR / folder_name

    if plugin_path.exists():
        return {"success": False, "error": f"Directory '{folder_name}' already exists"}

    name = config.get("name", "").strip() or clean_id.replace("_", " ").replace("-", " ").title()
    author = config.get("author", "").strip() or "Kunal Gautam"
    description = config.get("description", "").strip() or f"Custom Quickshell plugin for {name}"
    position = config.get("position", "center").lower()
    if position not in ["left", "center", "right"]:
        position = "center"

    has_widget = config.get("hasWidget", True)
    has_window = config.get("hasWindow", True)
    has_service = config.get("hasService", False)
    init_git = config.get("initGit", True)
    dependencies = config.get("dependencies", [])

    pascal_name = to_pascal_case(clean_id)

    # 1. Create directory
    plugin_path.mkdir(parents=True, exist_ok=True)

    kinds = []
    entry_points = {}

    # 2. Topbar Capsule Widget
    if has_widget:
        kinds.append("bar-widget")
        widget_file = f"{pascal_name}Module.qml"
        entry_points["barWidget"] = widget_file

        widget_qml = f"""import QtQuick
import Quickshell
import Quickshell.Io
import qs
import qs.components
import "."

Rectangle {{
    id: root

    property var barWindow: null
    readonly property bool isHovered: mouseArea.containsMouse

    implicitHeight: Theme.barHeight - 8
    implicitWidth: contentRow.implicitWidth + 20
    radius: Theme.capsuleRadius

    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on color {{ ColorAnimation {{ duration: 180 }} }}
    Behavior on border.color {{ ColorAnimation {{ duration: 180 }} }}

    Row {{
        id: contentRow
        anchors.centerIn: parent
        spacing: 6

        Text {{
            anchors.verticalCenter: parent.verticalCenter
            text: ""
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeIcon
            color: Theme.accent
        }}

        Text {{
            anchors.verticalCenter: parent.verticalCenter
            text: "{name}"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
        }}
    }}

    MouseArea {{
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {{
            PluginManager.toggle("{clean_id}");
        }}
    }}
}}
"""
        with open(plugin_path / widget_file, "w") as f:
            f.write(widget_qml)

    # 3. Popup Window & Menu View
    if has_window:
        kinds.append("window")
        window_file = f"{pascal_name}Window.qml"
        menu_file = f"{pascal_name}Menu.qml"
        entry_points["windows"] = [window_file]

        window_qml = f"""import QtQuick
import Quickshell
import Quickshell.Wayland
import qs
import "."

PanelWindow {{
    id: windowRoot

    visible: PluginManager.isPluginVisible("{clean_id}")

    anchors {{
        top: true
        left: true
        right: true
        bottom: true
    }}

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:{clean_id}"
    WlrLayershell.keyboardFocus: PluginManager.isPluginVisible("{clean_id}") ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {{
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        {pascal_name}Menu {{
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.horizontalCenter: parent.horizontalCenter

            MouseArea {{
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }}
        }}
    }}
}}
"""
        menu_qml = f"""import QtQuick
import QtQuick.Layouts
import qs
import "."

Rectangle {{
    id: root

    implicitWidth: 480
    implicitHeight: 340
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    ColumnLayout {{
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // Header
        RowLayout {{
            Layout.fillWidth: true
            spacing: 12

            Text {{
                text: ""
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge + 4
                color: Theme.accent
            }}

            Text {{
                text: "{name}"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.text
                Layout.fillWidth: true
            }}

            Rectangle {{
                implicitWidth: 28
                implicitHeight: 28
                radius: 14
                color: closeHover.containsMouse ? Theme.surface1 : "transparent"

                Text {{
                    anchors.centerIn: parent
                    text: "✕"
                    color: Theme.subtext0
                    font.pixelSize: 13
                }}

                MouseArea {{
                    id: closeHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManager.closeAll()
                }}
            }}
        }}

        // Divider
        Rectangle {{
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.surface0
        }}

        // Body Content
        ColumnLayout {{
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8

            Text {{
                text: "{description}"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                color: Theme.subtext0
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }}

            Rectangle {{
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.pillRadius
                color: Theme.surface0
                border.color: Theme.surface1
                border.width: 1

                Text {{
                    anchors.centerIn: parent
                    text: "Welcome to {name}!\\nEdit {pascal_name}Menu.qml to build your widget interface."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.subtext1
                    horizontalAlignment: Text.AlignHCenter
                }}
            }}
        }}
    }}
}}
"""
        with open(plugin_path / window_file, "w") as f:
            f.write(window_qml)
        with open(plugin_path / menu_file, "w") as f:
            f.write(menu_qml)

    # 4. Background Service
    if has_service:
        kinds.append("service")
        service_file = f"{pascal_name}Service.qml"
        entry_points["service"] = service_file

        service_qml = f"""pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {{
    id: root

    property string status: "active"
    property int counter: 0

    Timer {{
        interval: 5000
        running: true
        repeat: true
        onTriggered: {{
            root.counter++;
        }}
    }}
}}
"""
        with open(plugin_path / service_file, "w") as f:
            f.write(service_qml)

    # 5. manifest.json
    manifest_data = {
        "schemaVersion": 1,
        "id": clean_id,
        "name": name,
        "version": "1.0.0",
        "author": author,
        "description": description,
        "kinds": kinds,
        "position": position,
        "entryPoints": entry_points,
        "dependencies": dependencies,
        "enabled": True
    }
    with open(plugin_path / "manifest.json", "w") as f:
        json.dump(manifest_data, f, indent=2)

    # 6. qmldir
    qmldir_lines = []
    if has_service:
        qmldir_lines.append(f"{pascal_name}Service 1.0 {pascal_name}Service.qml")
    if has_widget:
        qmldir_lines.append(f"{pascal_name}Module 1.0 {pascal_name}Module.qml")
    if has_window:
        qmldir_lines.append(f"{pascal_name}Window 1.0 {pascal_name}Window.qml")
        qmldir_lines.append(f"{pascal_name}Menu 1.0 {pascal_name}Menu.qml")

    with open(plugin_path / "qmldir", "w") as f:
        f.write("\n".join(qmldir_lines) + "\n")

    # 7. .gitignore
    with open(plugin_path / ".gitignore", "w") as f:
        f.write("__pycache__/\n*.pyc\n.DS_Store\n")

    # 8. README.md
    readme_content = f"""# {name}

{description}

## Installation & Discovery
This custom plugin is auto-discovered by Quickshell.
Location: `~/.config/quickshell/custom_plugins/{folder_name}/`

## Features
- **Topbar Module**: `{"Yes" if has_widget else "No"}`
- **Popup Window**: `{"Yes" if has_window else "No"}`
- **Background Service**: `{"Yes" if has_service else "No"}`
- **Position**: `{position}`
"""
    with open(plugin_path / "README.md", "w") as f:
        f.write(readme_content)

    # 9. Initialize Git if requested
    if init_git:
        run_cmd(["git", "init"], cwd=str(plugin_path))
        run_cmd(["git", "add", "."], cwd=str(plugin_path))
        run_cmd(["git", "commit", "-m", f"feat: initial scaffold for {name}"], cwd=str(plugin_path))

    # 10. Update loader manifests
    trigger_loader_only()

    return {
        "success": True,
        "pluginId": clean_id,
        "folderName": folder_name,
        "path": str(plugin_path),
        "manifest": manifest_data
    }


def git_pull(plugin_id_or_folder: str):
    """Execute git pull for a custom plugin repo."""
    target_path, _ = find_custom_plugin_path(plugin_id_or_folder)
    if not target_path or not (target_path / ".git").exists():
        return {"success": False, "error": f"Plugin '{plugin_id_or_folder}' is not a Git repository"}

    ok, out, err = run_cmd(["git", "pull"], cwd=str(target_path))
    if not ok:
        return {"success": False, "error": err or out}
    
    trigger_loader_only()
    return {
        "success": True,
        "pluginId": plugin_id_or_folder,
        "message": out or "Already up to date."
    }


def git_log(plugin_id_or_folder: str, limit: int = 10):
    """Fetch recent git commits for a plugin."""
    target_path, _ = find_custom_plugin_path(plugin_id_or_folder)
    if not target_path or not (target_path / ".git").exists():
        return {"success": False, "error": f"Plugin '{plugin_id_or_folder}' is not a Git repository"}

    # Format: hash|author|relative_date|subject
    format_str = "%h|%an|%cr|%s"
    ok, out, err = run_cmd(["git", "log", f"-n{limit}", f"--pretty=format:{format_str}"], cwd=str(target_path))
    if not ok:
        return {"success": False, "error": err or out, "commits": []}

    commits = []
    if out:
        for line in out.split("\n"):
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })

    return {
        "success": True,
        "pluginId": plugin_id_or_folder,
        "commits": commits
    }


def export_plugin(plugin_id_or_folder: str):
    """Archive and export a custom plugin to a .tar.gz bundle."""
    target_path, _ = find_custom_plugin_path(plugin_id_or_folder)
    if not target_path:
        return {"success": False, "error": f"Plugin '{plugin_id_or_folder}' not found"}

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    archive_name = f"{target_path.name}_{timestamp}.tar.gz"
    archive_path = BACKUP_DIR / archive_name

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(target_path, arcname=target_path.name)
        
        size = archive_path.stat().st_size
        return {
            "success": True,
            "archivePath": str(archive_path),
            "archiveName": archive_name,
            "sizeFormatted": format_bytes(size)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def import_plugin(archive_path_str: str):
    """Extract a .tar.gz or .zip plugin archive into custom_plugins."""
    archive_path = Path(archive_path_str).expanduser()
    if not archive_path.is_file():
        return {"success": False, "error": f"File '{archive_path_str}' not found"}

    try:
        if archive_path.suffix in [".gz", ".tgz"] or archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:*") as tar:
                tar.extractall(path=CUSTOM_PLUGINS_DIR)
        elif archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(path=CUSTOM_PLUGINS_DIR)
        else:
            return {"success": False, "error": "Unsupported archive format (expected .tar.gz or .zip)"}

        trigger_loader_only()
        return {"success": True, "message": "Plugin imported successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def install_git(repo_url: str, custom_folder_name: str = None):
    """Clone a git repository into custom_plugins."""
    if not repo_url or not repo_url.strip():
        return {"success": False, "error": "Repository URL is required"}

    repo_url = repo_url.strip()
    if not custom_folder_name or not custom_folder_name.strip():
        base = repo_url.rstrip("/").split("/")[-1]
        if base.endswith(".git"):
            base = base[:-4]
        custom_folder_name = base

    clean_folder = re.sub(r'[^a-zA-Z0-9_-]', '_', custom_folder_name.lower())
    dest_path = CUSTOM_PLUGINS_DIR / clean_folder

    if dest_path.exists():
        return {"success": False, "error": f"Folder '{clean_folder}' already exists"}

    ok, out, err = run_cmd(["git", "clone", repo_url, str(dest_path)])
    if not ok:
        if dest_path.exists():
            shutil.rmtree(dest_path, ignore_errors=True)
        return {"success": False, "error": f"Git clone failed: {err or out}"}

    manifest_file = dest_path / "manifest.json"
    if not manifest_file.exists():
        default_manifest = {
            "schemaVersion": 1,
            "id": clean_folder,
            "name": clean_folder.replace("-", " ").replace("_", " ").title(),
            "version": "1.0.0",
            "author": "Git Community",
            "description": f"Installed from {repo_url}",
            "kinds": ["bar-widget", "window"],
            "position": "center",
            "enabled": True
        }
        with open(manifest_file, "w") as f:
            json.dump(default_manifest, f, indent=2)

    trigger_loader_only()

    return {
        "success": True,
        "folderName": clean_folder,
        "path": str(dest_path),
        "repoUrl": repo_url
    }


def open_folder(path_str: str):
    """Open folder in system file manager."""
    p = Path(path_str).expanduser()
    if p.exists():
        subprocess.Popen(["xdg-open", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "path": str(p)}
    return {"success": False, "error": "Path does not exist"}


# ── Keybinding Management Engine ─────────────────────────────────────────────

HYPR_KEYBINDS_FILE = Path.home() / ".config" / "hypr" / "modules" / "keybinds.lua"
DOTFILES_KEYBINDS_FILE = Path.home() / ".dotfiles" / ".config" / "hypr" / "modules" / "keybinds.lua"

KEY_ALIASES = {
    "return": "Return", "enter": "Return",
    "space": "Space",
    "tab": "Tab",
    "escape": "Escape", "esc": "Escape",
    "grave": "grave", "`": "grave",
    "slash": "slash", "/": "slash",
    "backslash": "backslash", "\\": "backslash",
    "equal": "equal", "=": "equal",
    "minus": "minus", "-": "minus",
    "period": "period", ".": "period",
    "comma": "comma", ",": "comma",
    "semicolon": "semicolon", ";": "semicolon",
    "apostrophe": "apostrophe", "'": "apostrophe", "\"": "apostrophe",
    "left": "left", "right": "right", "up": "up", "down": "down",
    "bracketleft": "bracketleft", "[": "bracketleft",
    "bracketright": "bracketright", "]": "bracketright",
    "print": "Print", "printscreen": "Print"
}

KNOWN_BIND_DESCRIPTIONS = {
    "SUPER + Return": "Open Kitty Terminal",
    "SUPER + grave": "Toggle Dropdown Scratchpad Terminal",
    "SUPER + Space": "Open Application Launcher (Quickshell App Menu)",
    "SUPER + B": "Launch Web Browser (Firefox)",
    "SUPER + E": "Open Dolphin File Manager",
    "SUPER + SHIFT + E": "Open Yazi File Manager",
    "SUPER + C": "Close Active Window",
    "ALT + F4": "Close Active Window",
    "SUPER + F": "Toggle Window Fullscreen",
    "SUPER + V": "Toggle Window Floating",
    "SUPER + P": "Toggle Pseudo Tiling",
    "SUPER + J": "Toggle Layout Split Orientation",
    "SUPER + L": "Lock Screen Immediately (Hyprlock)",
    "SUPER + Escape": "Open Power & Session Menu",
    "SUPER + SHIFT + W": "Toggle Quickshell Status Bar",
    "SUPER + slash": "Open Keyboard Shortcuts Cheat Sheet",
    "ALT + Tab": "Cycle Focus to Next Window",
    "SUPER + Tab": "Open Workspace Overview & App Viewer",
    "SUPER + S": "Toggle Magic Scratchpad Workspace",
    "SUPER + SHIFT + S": "Move Window to Magic Scratchpad",
    "SUPER + N": "Open Notification Center (Quickshell)",
    "SUPER + SHIFT + N": "Toggle Do-Not-Disturb (DND) Mode",
    "SUPER + ALT + N": "Toggle Night Light (Hyprsunset)",
    "SUPER + CTRL + N": "Night Light Temperature Menu",
    "SUPER + ALT + S": "Toggle Screen Reader / Speech",
    "SUPER + ALT + O": "OCR Screen Capture (Extract Text)",
    "SUPER + ALT + R": "Screen Recorder / GIF Tool",
    "SUPER + ALT + K": "Kill / Force Quit Application",
    "SUPER + ALT + W": "WhatsApp / Messaging Widget",
    "SUPER + SHIFT + D": "Wiktionary Dictionary Search",
    "SUPER + ALT + M": "Plugin Manager Center",
    "SUPER + CTRL + S": "Scratchpad Notes Workspace",
    "SUPER + CTRL + equal": "Scale Window Up (+40px)",
    "SUPER + CTRL + minus": "Scale Window Down (-40px)",
    "SUPER + CTRL + right": "Resize Window Width Right",
    "SUPER + CTRL + left": "Resize Window Width Left",
    "SUPER + CTRL + up": "Resize Window Height Up",
    "SUPER + CTRL + down": "Resize Window Height Down",
    "SUPER + CTRL + L": "Resize Window Right",
    "SUPER + CTRL + H": "Resize Window Left",
    "SUPER + CTRL + K": "Resize Window Up",
    "SUPER + CTRL + J": "Resize Window Down"
}

def normalize_key(k):
    """Normalize single key string."""
    k_strip = k.strip()
    k_low = k_strip.lower()
    if k_low in KEY_ALIASES:
        return KEY_ALIASES[k_low]
    if len(k_strip) == 1:
        return k_strip.upper()
    if k_low.startswith("f") and k_low[1:].isdigit():
        return f"F{k_low[1:]}"
    return k_strip

def normalize_keybind(raw_key):
    """Normalize key string like 'super+alt+m' or 'SUPER + M' into canonical 'SUPER + ALT + M'."""
    if not raw_key:
        return ""
    parts = re.split(r'[\s+]+', raw_key.strip())
    mods = []
    keys = []
    
    for p in parts:
        p_up = p.upper()
        if p_up in ["SUPER", "MOD4", "WIN", "LOGO", "META"]:
            if "SUPER" not in mods:
                mods.append("SUPER")
        elif p_up in ["CTRL", "CONTROL"]:
            if "CTRL" not in mods:
                mods.append("CTRL")
        elif p_up in ["ALT", "MOD1"]:
            if "ALT" not in mods:
                mods.append("ALT")
        elif p_up in ["SHIFT"]:
            if "SHIFT" not in mods:
                mods.append("SHIFT")
        elif p:
            keys.append(normalize_key(p))
    
    ordered_mods = [m for m in ["SUPER", "CTRL", "ALT", "SHIFT"] if m in mods]
    return " + ".join(ordered_mods + keys)

def get_all_system_keybinds(exclude_plugin="plugin_manager"):
    """Extract all active bindings from Hyprland compositor (hyprctl) and Lua configs."""
    binds = {}
    target_files = [HYPR_KEYBINDS_FILE, DOTFILES_KEYBINDS_FILE]
    for f in target_files:
        if f.is_file():
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                    lines = fp.readlines()
                    
                last_desc = ""
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("--"):
                        comment = stripped.lstrip("-").strip()
                        if comment and not comment.startswith("="):
                            last_desc = comment
                        continue
                        
                    match = re.search(r'hl\.bind\(\s*([^\,]+)', line)
                    if match:
                        expr = match.group(1).strip()
                        key_str = expr.replace('mainMod', 'SUPER').replace('"', '').replace("'", '').replace('..', '+')
                        norm = normalize_keybind(key_str)
                        if norm:
                            is_target = exclude_plugin in line or "Plugin Manager" in last_desc
                            binds[norm] = {
                                "rawKey": key_str,
                                "description": last_desc or KNOWN_BIND_DESCRIPTIONS.get(norm, "Custom binding"),
                                "line": line.strip(),
                                "isTarget": is_target
                            }
                    if stripped and not stripped.startswith("--"):
                        last_desc = ""
            except Exception:
                pass
            break

    # Add Workspace 1-10
    for i in range(1, 11):
        k = str(i % 10)
        w_norm = f"SUPER + {k}"
        w_move = f"SUPER + SHIFT + {k}"
        if w_norm not in binds:
            binds[w_norm] = {"description": f"Switch to Workspace {i}", "isTarget": False}
        if w_move not in binds:
            binds[w_move] = {"description": f"Move Window to Workspace {i}", "isTarget": False}

    # Query Live Hyprland Compositor
    try:
        res = subprocess.run(["hyprctl", "binds", "-j"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            live_binds = json.loads(res.stdout)
            for b in live_binds:
                modmask = b.get("modmask", 0)
                mods = []
                if modmask & 64: mods.append("SUPER")
                if modmask & 4:  mods.append("CTRL")
                if modmask & 8:  mods.append("ALT")
                if modmask & 1:  mods.append("SHIFT")
                
                key_name = normalize_key(b.get("key", ""))
                combo = " + ".join(mods + [key_name])
                norm = normalize_keybind(combo)
                
                dispatcher = b.get("dispatcher", "")
                arg = b.get("arg", "")
                is_target = exclude_plugin in arg or exclude_plugin in dispatcher

                desc = binds.get(norm, {}).get("description")
                if not desc:
                    desc = KNOWN_BIND_DESCRIPTIONS.get(norm)
                if not desc:
                    if dispatcher == "exec" and arg:
                        desc = f"Exec: {arg[:30]}"
                    elif dispatcher:
                        desc = f"Action: {dispatcher}"
                    else:
                        desc = "Active System Binding"

                if desc == "Plugin Manager Center" or "plugin_manager" in str(desc).lower() or norm == "SUPER + ALT + M":
                    is_target = True

                binds[norm] = {
                    "rawKey": combo,
                    "description": desc,
                    "dispatcher": dispatcher,
                    "arg": arg,
                    "isTarget": is_target
                }
    except Exception:
        pass

    # Check other custom plugins
    target_names = [exclude_plugin, exclude_plugin.replace("_", "-"), exclude_plugin.replace("-", "_")]
    if CUSTOM_PLUGINS_DIR.is_dir():
        for p in CUSTOM_PLUGINS_DIR.iterdir():
            if p.is_dir() and p.name not in target_names:
                kb_f = p / "keybinding.json"
                if kb_f.is_file():
                    try:
                        with open(kb_f, "r", encoding="utf-8") as kf:
                            kdata = json.load(kf)
                            p_key = kdata.get("keybind")
                            if p_key:
                                p_norm = normalize_keybind(p_key)
                                binds[p_norm] = {
                                    "rawKey": p_key,
                                    "description": f"Custom Plugin: {p.name}",
                                    "isTarget": False
                                }
                    except Exception:
                        pass

    return binds

def get_plugin_keybinding(plugin_id="plugin_manager"):
    """Get keybinding for specified plugin."""
    p_dir, _ = find_custom_plugin_path(plugin_id)
    if not p_dir:
        p_dir = CUSTOM_PLUGINS_DIR / "plugin-manager"
    kb_f = p_dir / "keybinding.json"
    if kb_f.is_file():
        try:
            with open(kb_f, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("keybind"):
                    return normalize_keybind(data["keybind"])
        except Exception:
            pass
            
    system_binds = get_all_system_keybinds(plugin_id)
    for norm_k, info in system_binds.items():
        if info.get("isTarget"):
            return norm_k
            
    return "SUPER + ALT + M"

def check_plugin_keybind(key_combo, plugin_id="plugin_manager"):
    """Check key combination validity and conflict for a plugin."""
    norm = normalize_keybind(key_combo)
    if not norm:
        return {
            "valid": False,
            "normalizedKey": "",
            "hasConflict": False,
            "conflictDesc": "",
            "isCurrent": False,
            "message": "Please enter a key combination (e.g. SUPER + ALT + M)."
        }
        
    current = get_plugin_keybinding(plugin_id)
    is_curr = (current and current == norm)
    system_binds = get_all_system_keybinds(plugin_id)
    
    if norm in system_binds and not system_binds[norm].get("isTarget"):
        desc = system_binds[norm].get("description", "Existing action")
        candidates = ["SUPER + ALT + M", "SUPER + CTRL + M", "SUPER + ALT + Return", "SUPER + ALT + P"]
        available_recs = [c for c in candidates if normalize_keybind(c) not in system_binds and normalize_keybind(c) != norm]
        return {
            "valid": True,
            "normalizedKey": norm,
            "hasConflict": True,
            "conflictDesc": desc,
            "isCurrent": is_curr,
            "recommended": available_recs[:3],
            "message": f"Conflict detected: '{norm}' is already used by '{desc}'."
        }
        
    if is_curr:
        return {
            "valid": True,
            "normalizedKey": norm,
            "hasConflict": False,
            "conflictDesc": "",
            "isCurrent": True,
            "message": f"✓ '{norm}' is currently configured."
        }
        
    return {
        "valid": True,
        "normalizedKey": norm,
        "hasConflict": False,
        "conflictDesc": "",
        "isCurrent": False,
        "message": f"✓ '{norm}' is available with no conflicts."
    }

def apply_plugin_keybind(plugin_id="plugin_manager", key_combo=None):
    """Apply the keybinding dynamically to the active Hyprland session."""
    norm = normalize_keybind(key_combo) if key_combo else get_plugin_keybinding(plugin_id)
    if not norm:
        return {"success": False, "error": "No keybinding configured"}
        
    ipc_cmd = f"quickshell ipc call pluginManager toggle {plugin_id}"
    lua_call = f'hl.bind("{norm}", hl.dsp.exec_cmd("{ipc_cmd}"))'
    
    try:
        subprocess.run(
            ["hyprctl", "eval", lua_call],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return {"success": True, "applied": norm}
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_plugin_keybind(plugin_id="plugin_manager", key_combo=None):
    """Save custom keybinding in plugin configuration and apply dynamically."""
    norm = normalize_keybind(key_combo)
    if not norm:
        return {"success": False, "error": "Invalid key combination"}
        
    p_dir, _ = find_custom_plugin_path(plugin_id)
    if not p_dir:
        p_dir = CUSTOM_PLUGINS_DIR / "plugin-manager"
    kb_f = p_dir / "keybinding.json"
    
    ipc_cmd = f"quickshell ipc call pluginManager toggle {plugin_id}"
    lua_snippet = f'hl.bind("{norm}", hl.dsp.exec_cmd("{ipc_cmd}"))'
    
    try:
        with open(kb_f, "w", encoding="utf-8") as f:
            json.dump({
                "keybind": norm,
                "ipcCommand": ipc_cmd,
                "luaSnippet": lua_snippet
            }, f, indent=2)
    except Exception as e:
        return {"success": False, "error": f"Failed to write keybinding.json: {e}"}
            
    apply_plugin_keybind(plugin_id, norm)

    return {
        "success": True,
        "keybind": norm,
        "ipcCommand": ipc_cmd,
        "luaSnippet": lua_snippet,
        "applied": True
    }

def remove_plugin_keybind(plugin_id="plugin_manager"):
    """Remove plugin keybinding config."""
    p_dir, _ = find_custom_plugin_path(plugin_id)
    if not p_dir:
        p_dir = CUSTOM_PLUGINS_DIR / "plugin-manager"
    kb_f = p_dir / "keybinding.json"
    if kb_f.is_file():
        try:
            kb_f.unlink()
        except Exception:
            pass
    return {"success": True}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No command provided"}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd in ["list", "list-plugins"]:
        res = list_plugins()
        print(json.dumps(res))

    elif cmd in ["catalog", "get-catalog"]:
        # Mark whether catalog item is already installed
        catalog_copy = []
        for item in STORE_CATALOG:
            installed = (CUSTOM_PLUGINS_DIR / item["id"]).is_dir()
            c = dict(item)
            c["isInstalled"] = installed
            c["dependencyStatus"] = check_dependencies(item.get("dependencies", []))
            catalog_copy.append(c)
        print(json.dumps({"success": True, "catalog": catalog_copy}))

    elif cmd in ["toggle", "toggle-plugin"]:
        if len(sys.argv) < 4:
            print(json.dumps({"success": False, "error": "Usage: toggle <plugin_id> <true|false>"}))
            sys.exit(1)
        plugin_id = sys.argv[2]
        enabled_state = sys.argv[3].lower() in ["true", "1", "yes"]
        res = toggle_plugin(plugin_id, enabled_state)
        print(json.dumps(res))

    elif cmd in ["update-manifest", "manifest"]:
        if len(sys.argv) < 4:
            print(json.dumps({"success": False, "error": "Usage: update-manifest <plugin_id> '<json_updates>'"}))
            sys.exit(1)
        plugin_id = sys.argv[2]
        try:
            updates = json.loads(sys.argv[3])
        except Exception as e:
            print(json.dumps({"success": False, "error": f"Invalid JSON updates: {e}"}))
            sys.exit(1)
        res = update_manifest(plugin_id, updates)
        print(json.dumps(res))

    elif cmd in ["delete", "delete-plugin"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: delete <plugin_id>"}))
            sys.exit(1)
        plugin_id = sys.argv[2]
        res = delete_plugin(plugin_id)
        print(json.dumps(res))

    elif cmd in ["create", "create-plugin"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: create '<json_config>'"}))
            sys.exit(1)
        try:
            config = json.loads(sys.argv[2])
        except Exception as e:
            print(json.dumps({"success": False, "error": f"Invalid JSON payload: {e}"}))
            sys.exit(1)
        res = create_plugin(config)
        print(json.dumps(res))

    elif cmd in ["git-pull", "pull"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: git-pull <plugin_id>"}))
            sys.exit(1)
        res = git_pull(sys.argv[2])
        print(json.dumps(res))

    elif cmd in ["git-log", "log"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: git-log <plugin_id>"}))
            sys.exit(1)
        res = git_log(sys.argv[2])
        print(json.dumps(res))

    elif cmd in ["export", "export-plugin"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: export-plugin <plugin_id>"}))
            sys.exit(1)
        res = export_plugin(sys.argv[2])
        print(json.dumps(res))

    elif cmd in ["import", "import-plugin"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: import-plugin <archive_path>"}))
            sys.exit(1)
        res = import_plugin(sys.argv[2])
        print(json.dumps(res))

    elif cmd in ["install-git", "git-clone"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: install-git <repo_url> [folder_name]"}))
            sys.exit(1)
        repo_url = sys.argv[2]
        folder_name = sys.argv[3] if len(sys.argv) > 3 else None
        res = install_git(repo_url, folder_name)
        print(json.dumps(res))

    elif cmd in ["check-deps"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: check-deps '<json_list>'"}))
            sys.exit(1)
        try:
            deps = json.loads(sys.argv[2])
        except Exception:
            deps = [sys.argv[2]]
        res = check_dependencies(deps)
        print(json.dumps({"success": True, "result": res}))

    elif cmd in ["reload", "reload-shell"]:
        reload_quickshell()
        print(json.dumps({"success": True, "message": "Quickshell reloaded"}))

    elif cmd in ["open", "open-folder"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: open-folder <path>"}))
            sys.exit(1)
    elif cmd in ["get-keybind", "get-key"]:
        plugin_id = sys.argv[2] if len(sys.argv) > 2 else "plugin_manager"
        kb = get_plugin_keybinding(plugin_id)
        ipc = f"quickshell ipc call pluginManager toggle {plugin_id}"
        print(json.dumps({
            "success": True,
            "pluginId": plugin_id,
            "keybind": kb,
            "ipcCommand": ipc,
            "luaSnippet": f'hl.bind("{kb}", hl.dsp.exec_cmd("{ipc}"))'
        }))

    elif cmd in ["check-keybind", "check-key"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: check-keybind <combo> [plugin_id]"}))
            sys.exit(1)
        combo = sys.argv[2]
        plugin_id = sys.argv[3] if len(sys.argv) > 3 else "plugin_manager"
        res = check_plugin_keybind(combo, plugin_id)
        print(json.dumps(res))

    elif cmd in ["set-keybind", "set-key"]:
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "Usage: set-keybind <combo> [plugin_id]"}))
            sys.exit(1)
        combo = sys.argv[2]
        plugin_id = sys.argv[3] if len(sys.argv) > 3 else "plugin_manager"
        res = set_plugin_keybind(plugin_id, combo)
        print(json.dumps(res))

    elif cmd in ["apply-keybind", "apply-key"]:
        plugin_id = sys.argv[2] if len(sys.argv) > 2 else "plugin_manager"
        combo = sys.argv[3] if len(sys.argv) > 3 else None
        res = apply_plugin_keybind(plugin_id, combo)
        print(json.dumps(res))

    elif cmd in ["remove-keybind", "remove-key"]:
        plugin_id = sys.argv[2] if len(sys.argv) > 2 else "plugin_manager"
        res = remove_plugin_keybind(plugin_id)
        print(json.dumps(res))

    else:
        print(json.dumps({"success": False, "error": f"Unknown command '{cmd}'"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
