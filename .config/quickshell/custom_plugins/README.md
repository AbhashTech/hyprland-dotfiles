# Quickshell Custom Plugins & Modules Guide

Welcome to the **Quickshell Custom Plugins** directory (`~/.config/quickshell/custom_plugins/`).
This directory is untracked by version control (`.gitignore`), giving you complete freedom to develop, test, and maintain your own custom topbar modules, popup panels, and interactive widgets without getting overwritten by dotfiles updates.

---

## 📁 Directory Structure Overview

A standard custom plugin/widget can be organized as follows:

```text
~/.config/quickshell/
├── custom_plugins/            <-- YOU ARE HERE (Untracked)
│   ├── README.md              <-- This documentation guide
│   ├── sample_widget/         <-- Example: custom topbar widget
│   │   └── SampleWidget.qml
│   └── weather/               <-- Example: custom popup plugin
│       ├── WeatherModule.qml  (Topbar pill/button)
│       ├── WeatherWindow.qml  (Floating popup panel)
│       └── WeatherCard.qml    (Popup content UI)
├── components/                <-- Built-in topbar components
├── plugins/                   <-- Built-in popup plugins (appmenu, volume, etc.)
├── PluginManager.qml          <-- State manager singleton for toggles & IPC
├── Theme.qml                  <-- Theme singleton (colors, fonts, metrics)
└── shell.qml                  <-- Main shell layout (topbar & windows)
```

---

## 🧩 1. Creating a Custom Topbar Widget

Topbar widgets sit inside the status bar in `shell.qml`.

### Step 1: Create your Widget QML file
Create a folder and file: `custom_plugins/my_widget/MyWidget.qml`

```qml
import QtQuick
import Quickshell
import Quickshell.Io
import "../.." // Access Theme and components

Rectangle {
    id: root

    // Reference to parent bar window for tooltips
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
        title: "My Custom Widget"
        description: "Click to do something awesome!"
        shortcuts: [
            { action: "Trigger Action", key: "Left Click" },
            { action: "Secondary Action", key: "Right Click" }
        ]
    }

    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "" // Nerd Font icon
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

    // Optional: Run CLI commands on action
    Process {
        id: cmdProc
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                // Execute a command or toggle a popup
                cmdProc.exec(["notify-send", "Custom Plugin", "Left clicked!"]);
            } else if (mouse.button === Qt.RightButton) {
                cmdProc.exec(["kitty", "-e", "htop"]);
            }
        }
    }
}
```

---

## 📍 2. Placing Your Widget in the Topbar (`shell.qml`)

Open `~/.config/quickshell/shell.qml`:

1. **Import your custom plugin directory** at the top:
   ```qml
   import "custom_plugins/my_widget"
   ```

2. **Add it into your preferred group in the topbar**:
   The topbar has three alignment sections:

   ### A. Left Section (`leftGroup`):
   Ideal for launchers, workspace indicators, window title, music player.
   ```qml
   // Left Modules
   Row {
       id: leftGroup
       anchors.left: parent.left
       anchors.leftMargin: 6
       anchors.verticalCenter: parent.verticalCenter
       spacing: 6

       LauncherButton { barWindow: barWindow }
       Workspaces { barWindow: barWindow }
       ActiveWindow { barWindow: barWindow }
       MprisModule { barWindow: barWindow }

       // ⭐ YOUR CUSTOM WIDGET HERE (Left aligned)
       MyWidget { barWindow: barWindow }
   }
   ```

   ### B. Center Section (`centerGroup`):
   Ideal for clocks, calendars, weather tickers, active indicators.
   ```qml
   // Center Modules
   Row {
       id: centerGroup
       anchors.centerIn: parent
       spacing: 6

       ClockModule { barWindow: barWindow }
       LanguageModule { barWindow: barWindow }

       // ⭐ YOUR CUSTOM WIDGET HERE (Center aligned)
       MyWidget { barWindow: barWindow }
   }
   ```

   ### C. Right Section (`rightGroup`):
   Ideal for system stats, volume, battery, system tray, quick actions.
   ```qml
   // Right Modules
   Row {
       id: rightGroup
       anchors.right: parent.right
       anchors.rightMargin: 6
       anchors.verticalCenter: parent.verticalCenter
       spacing: 6

       // ⭐ YOUR CUSTOM WIDGET HERE (Right aligned, before status pills)
       MyWidget { barWindow: barWindow }

       RecordingModule { barWindow: barWindow }
       TrayNotifGroup { barWindow: barWindow }
       StatusGroup { ... }
       StatsModule { barWindow: barWindow }
       PowerModule { barWindow: barWindow }
   }
   ```

---

## 🪟 3. Creating a Full Popup Panel / Window Plugin

If you want a floating modal popup (similar to App Menu, Volume Mixer, Quick Calc, Emoji Picker):

### 1. Define your Popup Window (`MyPopupWindow.qml`)
```qml
import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: popupWindow

    // Bind visibility to PluginManager property or custom boolean
    visible: PluginManager.myPluginVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:myplugin"
    WlrLayershell.keyboardFocus: PluginManager.myPluginVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    // Backdrop click-outside-to-dismiss
    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        // Main card popup
        Rectangle {
            anchors.centerIn: parent
            implicitWidth: 400
            implicitHeight: 300
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
                text: "Hello from Custom Popup Plugin!"
                color: Theme.text
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
            }
        }
    }
}
```

### 2. Register State in `PluginManager.qml`
1. Add visibility property:
   ```qml
   property bool myPluginVisible: false
   ```
2. Reset it in `closeAll()`:
   ```qml
   myPluginVisible = false;
   ```
3. Add toggle case in `toggle(name)`:
   ```qml
   case "myplugin":
       current = myPluginVisible;
       closeAll();
       myPluginVisible = !current;
       break;
   ```

### 3. Instantiate Window in `shell.qml`
At the bottom of `shell.qml`:
```qml
MyPopupWindow {}
```

---

## ⌨️ 4. Triggering via Keybinds & Hyprland

You can trigger your custom plugin from anywhere via terminal, Hyprland keybinds, or scripts:

### Using the toggle script:
```bash
bash ~/.config/quickshell/scripts/toggle_plugin.sh myplugin
```

### Adding a Hyprland Shortcut:
In `~/.config/hypr/modules/keybinds.lua`:
```lua
hl.bind("SUPER + ALT + P", hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh myplugin"))
```

---

## 🎨 Useful Theme Tokens (`Theme.qml`)

Always use `Theme` properties for consistent styling across dynamic light/dark/Nord themes:

| Property | Description | Example Usage |
| :--- | :--- | :--- |
| `Theme.barBg` | Main glassmorphic background | `color: Theme.barBg` |
| `Theme.moduleBg` | Default pill/capsule background | `color: Theme.moduleBg` |
| `Theme.moduleHoverBg` | Hovered pill/capsule background | `color: Theme.moduleHoverBg` |
| `Theme.accent` | Active dynamic accent color | `color: Theme.accent` |
| `Theme.text` | Primary foreground text color | `color: Theme.text` |
| `Theme.subtext0` / `1` | Secondary muted text | `color: Theme.subtext0` |
| `Theme.barHeight` | Bar height metric (default: 38) | `implicitHeight: Theme.barHeight - 8` |
| `Theme.capsuleRadius` | Radius for capsules (default: 12) | `radius: Theme.capsuleRadius` |
| `Theme.fontFamily` | Configured Nerd Font family | `font.family: Theme.fontFamily` |
| `Theme.blue`, `Theme.mauve`, `Theme.green`, etc. | Palette accent colors | `color: Theme.peach` |

---

## 🔄 Live Reloading Quickshell

To test your changes, restart quickshell:
```bash
bash ~/.config/quickshell/scripts/launch_quickshell.sh --restart
```
Or check errors with:
```bash
quickshell -p ~/.config/quickshell
```
