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

custom_bar_modules = {}     # module_id -> {"id": plugin_id, "url": qml_url}
custom_modules_meta = {}    # module_id -> dict(id, name, icon, description, category, defaultSection)

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

        # Determine icon for plugin
        icon = manifest.get("icon")
        if not icon:
            lower_entry = (manifest.get("name", "") + " " + plugin_id + " " + entry).lower()
            if "whatsapp" in lower_entry:
                icon = "󰖣"
            elif "calendar" in lower_entry:
                icon = "󰸗"
            elif "weather" in lower_entry:
                icon = "󰖐"
            else:
                icon = "󰏖"

        plugin_meta = {
            "id": f"plugin_{plugin_id}",
            "name": manifest.get("name", entry),
            "icon": icon,
            "description": manifest.get("description", f"Custom plugin: {entry}"),
            "category": "Custom Plugins",
            "defaultSection": position
        }

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

            # Register individual module identifiers
            for mid in [f"plugin_{plugin_id}", plugin_id, f"plugin_{entry}", entry]:
                custom_bar_modules[mid] = widget_entry
                custom_modules_meta[mid] = plugin_meta

            if override_module:
                bar_overrides[override_module] = widget_entry
                custom_modules_meta[override_module] = plugin_meta
            else:
                pos_key = f"custom_{position}"
                if pos_key not in custom_modules_meta:
                    custom_modules_meta[pos_key] = {
                        "id": pos_key,
                        "name": plugin_meta["name"],
                        "icon": plugin_meta["icon"],
                        "description": plugin_meta["description"],
                        "category": "Custom Plugins",
                        "defaultSection": position
                    }
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

def generate_widget_group(widgets, group_pos):
    if not widgets:
        return "        Item { implicitWidth: 0; implicitHeight: 0 }"
    items = []
    for i, w in enumerate(widgets):
        w_id = w["id"]
        lid = f"loader_{group_pos}_{i}"
        items.append(f'''        Loader {{
            id: {lid}
            source: "{w["url"]}"
            asynchronous: false
            width: item ? item.implicitWidth : 0
            height: item ? item.implicitHeight : 0

            Binding {{
                target: {lid}.item
                property: "barWindow"
                value: root.barWindow
                when: {lid}.item !== null && {lid}.item.hasOwnProperty("barWindow")
            }}
            Binding {{
                target: {lid}.item
                property: "barSection"
                value: root.barSection
                when: {lid}.item !== null && {lid}.item.hasOwnProperty("barSection")
            }}
            Binding {{
                target: {lid}.item
                property: "barIndex"
                value: root.barIndex
                when: {lid}.item !== null && {lid}.item.hasOwnProperty("barIndex")
            }}
            Binding {{
                target: {lid}.item
                property: "barContainer"
                value: root.barContainer
                when: {lid}.item !== null && {lid}.item.hasOwnProperty("barContainer")
            }}
            Binding {{
                target: {lid}.item
                property: "moduleId"
                value: root.moduleId ? root.moduleId : "{w_id}"
                when: {lid}.item !== null && {lid}.item.hasOwnProperty("moduleId")
            }}
        }}''')
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

def generate_override_components(bar_ovs, custom_mods):
    all_targets = dict(bar_ovs)
    all_targets.update(custom_mods)

    url_to_comp_id = {}
    comps = []
    cases = []

    for mod_id, meta in sorted(all_targets.items()):
        url = meta["url"]
        if url not in url_to_comp_id:
            safe_id = meta["id"].replace("-", "_").replace(".", "_")
            comp_id = f"comp_{safe_id}_{len(url_to_comp_id)}"
            url_to_comp_id[url] = comp_id
            comps.append(f'    readonly property var {comp_id}: Qt.createComponent("{url}")')
        else:
            comp_id = url_to_comp_id[url]
        cases.append(f'            case "{mod_id}":\n                return {comp_id};')

    return "\n".join(cases), "\n".join(comps)

cases_code, comps_code = generate_override_components(bar_overrides, custom_bar_modules)

# Generate PluginOverrides.qml
bar_overrides_json = json.dumps({k: v["url"] for k, v in bar_overrides.items()}, indent=4)
win_overrides_json = json.dumps({k: v["url"] for k, v in window_overrides.items()}, indent=4)
act_overrides_json = json.dumps(action_overrides, indent=4)
custom_meta_json = json.dumps(custom_modules_meta, indent=4)

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

    // Metadata dictionary for custom plugins & modules
    readonly property var customModulesMeta: ({custom_meta_json})

    function hasBarOverride(moduleId) {{
        if (!moduleId) return false;
        var key = moduleId.toLowerCase();
        return barOverrides.hasOwnProperty(moduleId) || barOverrides.hasOwnProperty(key);
    }}

    function getBarOverrideUrl(moduleId) {{
        if (!moduleId) return "";
        var key = moduleId.toLowerCase();
        return barOverrides[moduleId] || barOverrides[key] || "";
    }}

    function hasCustomMeta(moduleId) {{
        if (!moduleId) return false;
        var key = moduleId.toLowerCase();
        return customModulesMeta.hasOwnProperty(moduleId) || customModulesMeta.hasOwnProperty(key);
    }}

    function getCustomMeta(moduleId) {{
        if (!moduleId) return null;
        var key = moduleId.toLowerCase();
        return customModulesMeta[moduleId] || customModulesMeta[key] || null;
    }}

    function hasWindowOverride(windowId) {{
        if (!windowId) return false;
        var key = windowId.toLowerCase();
        return windowOverrides.hasOwnProperty(windowId) || windowOverrides.hasOwnProperty(key);
    }}

    function getWindowOverrideUrl(windowId) {{
        if (!windowId) return "";
        var key = windowId.toLowerCase();
        return windowOverrides[windowId] || windowOverrides[key] || "";
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
    property string barSection: "left"
    property int barIndex: -1
    property var barContainer: null
    property string moduleId: "custom_left"
    spacing: 6
{generate_widget_group(left_widgets, "left")}
}}
"""

# Generate CustomWidgetsCenter.qml
center_qml = f"""import QtQuick
import Quickshell

Row {{
    id: root
    property var barWindow: null
    property string barSection: "center"
    property int barIndex: -1
    property var barContainer: null
    property string moduleId: "custom_center"
    spacing: 6
{generate_widget_group(center_widgets, "center")}
}}
"""

# Generate CustomWidgetsRight.qml
right_qml = f"""import QtQuick
import Quickshell

Row {{
    id: root
    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null
    property string moduleId: "custom_right"
    spacing: 6
{generate_widget_group(right_widgets, "right")}
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

