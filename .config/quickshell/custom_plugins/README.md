# Quickshell Custom Plugins & Auto-Discovery Guide

Welcome to the **Quickshell Custom Plugins** directory (`~/.config/quickshell/custom_plugins/`).
This directory is untracked by Git (`.gitignore`). **No code modification in this dotfiles repository is required** to add or use your own custom plugins, topbar widgets, or popup windows.

Plugins placed in this directory are **automatically discovered, registered, and activated** upon shell startup or reload via `manifest.json`.

---

## 📁 Directory & Plugin Structure

Create a subdirectory under `custom_plugins/` for your plugin with a `manifest.json` file:

```text
~/.config/quickshell/custom_plugins/
├── README.md                   <-- This documentation
├── plugin-manager/             <-- Built-in GUI & CLI Plugin Manager
└── my_plugin/                  <-- Your custom plugin folder
    ├── manifest.json           <-- Plugin metadata, position & entrypoints (Automatic discovery!)
    ├── MyBarWidget.qml         <-- Topbar widget (optional)
    ├── MyWindow.qml            <-- Floating popup panel (optional)
    └── MyService.qml           <-- Background service (optional)
```

---

## 📋 The `manifest.json` Specification

Every custom plugin should contain a `manifest.json` file at its root. This instructs Quickshell where to place your widget and which windows or services to activate.

### Example `manifest.json`:

```json
{
  "schemaVersion": 1,
  "id": "my_weather",
  "name": "Weather Widget",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Live weather widget and 7-day forecast drawer",
  "kinds": ["bar-widget", "window"],
  "position": "center",
  "dependencies": ["curl", "python3"],
  "enabled": true,
  "entryPoints": {
    "barWidget": "WeatherModule.qml",
    "windows": ["WeatherWindow.qml"],
    "service": "WeatherService.qml"
  }
}
```

### Manifest Fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique identifier for your plugin. Used for IPC triggers and toggles. |
| `name` | `string` | Human-readable name. |
| `position` | `string` | Where the topbar widget appears: `"left"`, `"center"`, or `"right"` (default: `"center"`). |
| `kinds` | `array` | Types of components provided: `["bar-widget", "window", "service"]`. |
| `dependencies` | `array` | Optional list of required system CLI binaries (e.g. `["curl", "playerctl"]`). |
| `entryPoints.barWidget` | `string` | QML file for the topbar capsule (e.g. `Widget.qml`, `WeatherModule.qml`). |
| `entryPoints.windows` | `array` / `string` | Floating popup window QML file(s) (e.g. `["WeatherWindow.qml"]`). |
| `entryPoints.service` | `string` | Background QML service file (e.g. `WeatherService.qml`). |
| `enabled` | `boolean` | Set to `false` to disable the plugin without deleting it (default: `true`). |

*(Note: If `manifest.json` is omitted, the auto-discovery engine will look for standard filenames like `*Module.qml` or `Widget.qml` for topbar widgets and `*Window.qml` for popup windows).*

---

## 🔌 Enabling and Disabling Plugins

You can enable or disable any custom plugin using any of the following 3 methods:

### Method 1: Via Graphical UI (Plugin Manager)
1. Click the **Plugin Manager capsule** on the top status bar or press the toggle keybinding.
2. Find your plugin in the list.
3. Click the **toggle switch** to enable or disable it.
4. Quickshell will automatically update the manifests and reload widgets in real-time.

### Method 2: Via `manifest.json`
1. Open `~/.config/quickshell/custom_plugins/<your-plugin>/manifest.json`.
2. Modify the `"enabled"` boolean:
   ```json
   "enabled": false
   ```
3. Regenerate loader manifests and restart Quickshell:
   ```bash
   bash ~/.config/quickshell/scripts/launch_quickshell.sh --restart
   ```

### Method 3: Via CLI (`plugin_helper.py`)
Use the backend helper script to toggle plugins from scripts or terminal:
```bash
# Enable a plugin
python3 ~/.config/quickshell/custom_plugins/plugin-manager/plugin_helper.py toggle <plugin-id> true

# Disable a plugin
python3 ~/.config/quickshell/custom_plugins/plugin-manager/plugin_helper.py toggle <plugin-id> false
```

---

## 🧩 1. Creating a Topbar Widget (`barWidget`)

Topbar widgets are automatically injected into the status bar according to the `position` defined in your manifest (`"left"`, `"center"`, or `"right"`).

### Example `MyBarWidget.qml`:
```qml
import QtQuick
import Quickshell
import Quickshell.Io
import "../.." // Access Theme and components

Rectangle {
    id: root

    // Injected automatically by the shell loader
    property var barWindow: null

    implicitHeight: Theme.barHeight - 8
    implicitWidth: contentRow.implicitWidth + 20
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 180 } }
    Behavior on border.color { ColorAnimation { duration: 180 } }

    // Optional: Tooltip on hover
    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: ""
        iconColor: Theme.yellow
        title: "My Custom Plugin"
        description: "Click to toggle custom window"
        shortcuts: [
            { action: "Toggle Window", key: "Left Click" }
        ]
    }

    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: ""
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeIcon
            color: Theme.yellow
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "My Status"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            PluginManager.toggle("my_weather");
        }
    }
}
```

---

## 🪟 2. Creating a Popup Window (`window`)

Popup windows are automatically instantiated in the shell root and can be toggled using `PluginManager.toggle("<plugin-id>")` or keybinds.

### Example `MyWindow.qml`:
```qml
import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: myWindow

    // Listen to PluginManager visibility or custom service state
    visible: PluginManager.isPluginVisible("my_weather")

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:my_weather"
    WlrLayershell.keyboardFocus: visible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    // Backdrop click to dismiss
    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        // Main modal card
        Rectangle {
            anchors.centerIn: parent
            implicitWidth: 420
            implicitHeight: 320
            radius: Theme.barRadius
            color: Theme.barBg
            border.color: Theme.barBorder
            border.width: 1

            // Prevent clicks inside card from closing
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }

            Text {
                anchors.centerIn: parent
                text: "Hello from Custom Plugin!"
                color: Theme.text
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
            }
        }
    }
}
```

---

## ⚡ 3. Activating and Reloading Plugins

Because plugins are auto-discovered dynamically:

1. Place your plugin folder in `~/.config/quickshell/custom_plugins/<your-plugin>/`.
2. Reload quickshell:
   ```bash
   bash ~/.config/quickshell/scripts/launch_quickshell.sh --restart
   ```
3. Your topbar widget will appear in its specified position (`left`, `center`, or `right`), and windows/services will be active!

---

## ⌨️ 4. Keybindings and IPC

You can toggle your plugin from the terminal, scripts, or Hyprland keybinds using:

```bash
bash ~/.config/quickshell/scripts/toggle_plugin.sh <plugin-id>
```

In `~/.config/hypr/modules/keybinds.lua`:
```lua
hl.bind("SUPER + ALT + P", hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh my_weather"))
```
