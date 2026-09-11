#!/usr/bin/env bash
# =============================================================================
# Custom Plugins Loader for Quickshell
# Generates runtime QML manifests for dynamic plugin auto-discovery
# =============================================================================

CUSTOM_PLUGINS_DIR="${HOME}/.config/quickshell/custom_plugins"
GEN_DIR="${HOME}/.config/quickshell/generated"

mkdir -p "$GEN_DIR"

python3 - << 'EOF'
import os
import json

custom_dir = os.path.expanduser("~/.config/quickshell/custom_plugins")
gen_dir = os.path.expanduser("~/.config/quickshell/generated")
os.makedirs(gen_dir, exist_ok=True)

left_widgets = []
center_widgets = []
right_widgets = []
windows = []
services = []
plugin_toggles = []

if os.path.isdir(custom_dir):
    for entry in sorted(os.listdir(custom_dir)):
        plugin_path = os.path.join(custom_dir, entry)
        if not os.path.isdir(plugin_path) or entry.startswith("."):
            continue

        manifest_file = os.path.join(plugin_path, "manifest.json")
        manifest = {}
        if os.path.isfile(manifest_file):
            try:
                with open(manifest_file, "r") as f:
                    manifest = json.load(f)
            except Exception:
                pass

        if manifest.get("enabled", True) is False:
            continue

        plugin_id = manifest.get("id", entry)
        position = manifest.get("position", "center").lower()
        entry_points = manifest.get("entryPoints", {})

        # 1. Bar Widget
        bar_widget = entry_points.get("barWidget")
        if not bar_widget:
            for candidate in ["Widget.qml", "BarWidget.qml", f"{entry.capitalize()}Module.qml", f"{entry}Module.qml", "Module.qml"]:
                if os.path.isfile(os.path.join(plugin_path, candidate)):
                    bar_widget = candidate
                    break

        if bar_widget:
            qml_url = f"file://{plugin_path}/{bar_widget}"
            widget_entry = {"id": plugin_id, "url": qml_url}
            if position == "left":
                left_widgets.append(widget_entry)
            elif position == "right":
                right_widgets.append(widget_entry)
            else:
                center_widgets.append(widget_entry)

        # 2. Windows / Panels
        plugin_windows = []
        if "window" in entry_points:
            plugin_windows.append(entry_points["window"])
        elif "windows" in entry_points and isinstance(entry_points["windows"], list):
            plugin_windows.extend(entry_points["windows"])
        else:
            for f in sorted(os.listdir(plugin_path)):
                if f.endswith("Window.qml"):
                    plugin_windows.append(f)

        for win in plugin_windows:
            if os.path.isfile(os.path.join(plugin_path, win)):
                windows.append({"id": plugin_id, "url": f"file://{plugin_path}/{win}"})

        # 3. Services / Background items
        plugin_services = []
        if "service" in entry_points:
            plugin_services.append(entry_points["service"])
        elif "services" in entry_points and isinstance(entry_points["services"], list):
            plugin_services.extend(entry_points["services"])
        else:
            for f in sorted(os.listdir(plugin_path)):
                if f.endswith("Service.qml"):
                    plugin_services.append(f)

        for srv in plugin_services:
            if os.path.isfile(os.path.join(plugin_path, srv)):
                services.append({"id": plugin_id, "url": f"file://{plugin_path}/{srv}"})

        plugin_toggles.append(plugin_id)

def generate_widget_group(widgets):
    items = []
    for w in widgets:
        items.append(f'        Loader {{\n            source: "{w["url"]}"\n            asynchronous: false\n            width: item ? item.implicitWidth : 0\n            height: item ? item.implicitHeight : 0\n            onLoaded: {{\n                if (item && item.hasOwnProperty("barWindow")) item.barWindow = root.barWindow;\n            }}\n        }}')
    return "\n".join(items)

def generate_window_loaders(services, windows):
    items = []
    for s in services:
        items.append(f'    Loader {{\n        source: "{s["url"]}"\n        asynchronous: true\n    }}')
    for w in windows:
        items.append(f'    Loader {{\n        property bool _cached: false\n        active: PluginManager.isPluginVisible("{w["id"]}") || _cached\n        onLoaded: _cached = true\n        source: "{w["url"]}"\n        asynchronous: false\n    }}')
    return "\n".join(items)

# Generate CustomWidgetsLeft.qml
left_qml = f"""import QtQuick
import Quickshell

Row {{
    id: root
    property var barWindow: null
    spacing: 6
{generate_widget_group(left_widgets)}
}}
"""

# Generate CustomWidgetsCenter.qml
center_qml = f"""import QtQuick
import Quickshell

Row {{
    id: root
    property var barWindow: null
    spacing: 6
{generate_widget_group(center_widgets)}
}}
"""

# Generate CustomWidgetsRight.qml
right_qml = f"""import QtQuick
import Quickshell

Row {{
    id: root
    property var barWindow: null
    spacing: 6
{generate_widget_group(right_widgets)}
}}
"""

# Generate CustomWindows.qml
windows_qml = f"""import QtQuick
import Quickshell
import ".."

Item {{
    id: root
{generate_window_loaders(services, windows)}
}}
"""

with open(os.path.join(gen_dir, "CustomWidgetsLeft.qml"), "w") as f:
    f.write(left_qml)

with open(os.path.join(gen_dir, "CustomWidgetsCenter.qml"), "w") as f:
    f.write(center_qml)

with open(os.path.join(gen_dir, "CustomWidgetsRight.qml"), "w") as f:
    f.write(right_qml)

with open(os.path.join(gen_dir, "CustomWindows.qml"), "w") as f:
    f.write(windows_qml)

EOF
