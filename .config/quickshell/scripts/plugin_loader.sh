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
bar_overrides = {}      # target_module_id -> {"id": plugin_id, "url": qml_url}
window_overrides = {}   # target_window_id -> {"id": plugin_id, "url": qml_url}
action_overrides = {}   # target_action_name -> plugin_id

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
        overrides = manifest.get("overrides", {})

        # Parse overrides mapping if present
        # Format can be:
        # "overrides": { "module": "volume", "window": "volume", "action": "volume" }
        # or list of actions: "actions": ["volume", "volumemenu"]
        override_module = overrides.get("module") or overrides.get("barModule") or overrides.get("barWidget")
        override_window = overrides.get("window")
        override_actions = overrides.get("action") or overrides.get("actions") or []
        if isinstance(override_actions, str):
            override_actions = [override_actions]

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

            if override_module:
                bar_overrides[override_module] = widget_entry
            else:
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
                win_url = f"file://{plugin_path}/{win}"
                windows.append({"id": plugin_id, "url": win_url})
                if override_window:
                    window_overrides[override_window] = {"id": plugin_id, "url": win_url}

        # 3. Action overrides (intercepting PluginManager.toggle)
        for act in override_actions:
            action_overrides[str(act).lower()] = plugin_id
        if override_module and not override_actions:
            action_overrides[str(override_module).lower()] = plugin_id
        if override_window and str(override_window).lower() not in action_overrides:
            action_overrides[str(override_window).lower()] = plugin_id

        # 4. Services / Background items
        plugin_services = []
        qmldir_path = os.path.join(plugin_path, "qmldir")
        singletons = set()
        if os.path.isfile(qmldir_path):
            try:
                with open(qmldir_path, "r") as qf:
                    for qline in qf:
                        parts = qline.strip().split()
                        if len(parts) >= 4 and parts[0] == "singleton":
                            singletons.add(parts[3])
            except Exception:
                pass

        if "service" in entry_points and entry_points["service"]:
            plugin_services.append(entry_points["service"])
        elif "services" in entry_points and isinstance(entry_points["services"], list):
            plugin_services.extend(entry_points["services"])
        else:
            for f in sorted(os.listdir(plugin_path)):
                if f.endswith("Service.qml"):
                    plugin_services.append(f)

        for srv in plugin_services:
            if srv in singletons:
                continue
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
        if w["id"] in ["plugin_manager", "plugin-manager"]:
            continue
        items.append(f'    Loader {{\n        property bool _cached: false\n        active: (PluginManager.customPluginVersion >= 0 && PluginManager.isPluginVisible("{w["id"]}")) || _cached\n        onLoaded: _cached = true\n        source: "{w["url"]}"\n        asynchronous: false\n    }}')
    return "\n".join(items)

def generate_override_components(bar_ovs):
    cases = []
    comps = []
    for mod_id, meta in sorted(bar_ovs.items()):
        comp_id = f"comp_{mod_id.replace('-', '_')}"
        cases.append(f'            case "{mod_id}":\n                return {comp_id};')
        # Create a direct Component so moduleLoader in DynamicBarSection loads the plugin
        # item directly without intermediate wrappers or nested loaders.
        comps.append(f'    readonly property var {comp_id}: Qt.createComponent("{meta["url"]}")')
    return "\n".join(cases), "\n".join(comps)

cases_code, comps_code = generate_override_components(bar_overrides)

# Generate PluginOverrides.qml
bar_overrides_json = json.dumps({k: v["url"] for k, v in bar_overrides.items()}, indent=4)
win_overrides_json = json.dumps({k: v["url"] for k, v in window_overrides.items()}, indent=4)
act_overrides_json = json.dumps(action_overrides, indent=4)

plugin_overrides_qml = f"""pragma Singleton
import QtQuick

QtObject {{
    id: root

    // Mapping of module ID -> Custom QML file URL
    readonly property var barOverrides: ({bar_overrides_json})

    // Mapping of window/panel ID -> Custom Window QML file URL
    readonly property var windowOverrides: ({win_overrides_json})

    // Mapping of action/toggle name -> Plugin ID to toggle
    readonly property var actionOverrides: ({act_overrides_json})

    function hasBarOverride(moduleId) {{
        return barOverrides.hasOwnProperty(moduleId);
    }}

    function getBarOverrideUrl(moduleId) {{
        return barOverrides[moduleId] || "";
    }}

    function hasWindowOverride(windowId) {{
        return windowOverrides.hasOwnProperty(windowId);
    }}

    function getWindowOverrideUrl(windowId) {{
        return windowOverrides[windowId] || "";
    }}

    function isActionOverridden(actionName) {{
        if (!actionName) return false;
        return actionOverrides.hasOwnProperty(actionName.toLowerCase());
    }}

    function getTargetPluginForAction(actionName) {{
        if (!actionName) return "";
        return actionOverrides[actionName.toLowerCase()] || "";
    }}
}}
"""

# Generate OverrideComponents.qml for DynamicBarSection
override_components_qml = f"""import QtQuick

Item {{
    id: root
    property var barWindow: null

    function getComponentForModule(moduleId) {{
        switch (moduleId) {{
{cases_code}
            default:
                return null;
        }}
    }}

{comps_code}
}}
"""

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

with open(os.path.join(gen_dir, "PluginOverrides.qml"), "w") as f:
    f.write(plugin_overrides_qml)

with open(os.path.join(gen_dir, "OverrideComponents.qml"), "w") as f:
    f.write(override_components_qml)

with open(os.path.join(gen_dir, "CustomWidgetsLeft.qml"), "w") as f:
    f.write(left_qml)

with open(os.path.join(gen_dir, "CustomWidgetsCenter.qml"), "w") as f:
    f.write(center_qml)

with open(os.path.join(gen_dir, "CustomWidgetsRight.qml"), "w") as f:
    f.write(right_qml)

with open(os.path.join(gen_dir, "CustomWindows.qml"), "w") as f:
    f.write(windows_qml)

# Update generated/qmldir to export PluginOverrides singleton
qmldir_gen = f"""singleton PluginOverrides 1.0 PluginOverrides.qml
CustomWidgetsLeft 1.0 CustomWidgetsLeft.qml
CustomWidgetsCenter 1.0 CustomWidgetsCenter.qml
CustomWidgetsRight 1.0 CustomWidgetsRight.qml
CustomWindows 1.0 CustomWindows.qml
OverrideComponents 1.0 OverrideComponents.qml
"""
with open(os.path.join(gen_dir, "qmldir"), "w") as f:
    f.write(qmldir_gen)


EOF
