//@ pragma UseQApplication
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "components"
import "plugins/appmenu"
import "plugins/powermenu"
import "plugins/clipboard"
import "plugins/calc"
import "plugins/emoji"
import "plugins/keybinds"
import "plugins/volume"
import "plugins/brightness"
import "plugins/sysinfo"
import "plugins/connectivity"
import "plugins/battery"
import "plugins/notifications"
import "plugins/filepicker"
import "plugins/workspace_viewer"
import "generated"

ShellRoot {
    id: root

    IpcHandler {
        target: "pluginManager"
        function toggle(name: string) {
            PluginManager.toggle(name);
        }
        function closeAll() {
            PluginManager.closeAll();
        }
    }

    // Top Status Bar across screens
    Variants {
        model: Quickshell.screens

        delegate: Component {
            PanelWindow {
                id: barWindow
                required property var modelData
                screen: modelData

                // Match waybar margins and positioning
                anchors {
                    top: true
                    left: true
                    right: true
                }

                margins {
                    top: 8
                    left: 12
                    right: 12
                    bottom: 0
                }

                implicitHeight: Theme.barHeight
                color: "transparent"

                WlrLayershell.layer: WlrLayer.Top
                WlrLayershell.namespace: "quickshell"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
                exclusiveZone: Theme.barHeight + 8

                // Main glassmorphic background container
                Rectangle {
                    anchors.fill: parent
                    radius: Theme.barRadius
                    color: Theme.barBg
                    border.color: Theme.barBorder
                    border.width: 1

                    // Left Modules
                    Row {
                        id: leftGroup
                        anchors.left: parent.left
                        anchors.leftMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 6

                        LauncherButton {
                            barWindow: barWindow
                        }
                        Workspaces {
                            barWindow: barWindow
                        }
                        ActiveWindow {
                            barWindow: barWindow
                        }
                        CustomWidgetsLeft {
                            barWindow: barWindow
                        }
                    }

                    // Center Modules
                    Row {
                        id: centerGroup
                        anchors.centerIn: parent
                        spacing: 6

                        MprisModule {
                            barWindow: barWindow
                        }
                        CustomWidgetsCenter {
                            barWindow: barWindow
                        }
                        LanguageModule {
                            barWindow: barWindow
                        }
                    }

                    // Right Modules
                    Row {
                        id: rightGroup
                        anchors.right: parent.right
                        anchors.rightMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 6

                        CustomWidgetsRight {
                            barWindow: barWindow
                        }
                        RecordingModule {
                            barWindow: barWindow
                        }
                        TrayNotifGroup {
                            barWindow: barWindow
                        }
                        StatusGroup {
                            barWindow: barWindow
                            screenName: (barWindow && barWindow.screen && barWindow.screen.name) ? barWindow.screen.name : (modelData && modelData.name ? modelData.name : "")
                        }
                        StatsModule {
                            barWindow: barWindow
                        }
                        PowerModule {
                            barWindow: barWindow
                        }
                        ClockModule {
                            barWindow: barWindow
                        }
                    }
                }
            }
        }
    }

    component LazyWindow: Loader {
        property bool trigger: false
        property bool _cached: false
        active: trigger || _cached
        onLoaded: _cached = true
    }

    // Modular Quickshell Plugin Windows (Lazy-loaded on first access for instant shell startup)
    LazyWindow { trigger: PluginManager.appMenuVisible; source: "plugins/appmenu/AppMenuWindow.qml" }
    LazyWindow { trigger: PluginManager.powerMenuVisible; source: "plugins/powermenu/PowerMenuWindow.qml" }
    LazyWindow { trigger: PluginManager.clipboardVisible; source: "plugins/clipboard/ClipboardWindow.qml" }
    LazyWindow { trigger: PluginManager.calcVisible; source: "plugins/calc/QuickCalcWindow.qml" }
    LazyWindow { trigger: PluginManager.emojiVisible; source: "plugins/emoji/EmojiPickerWindow.qml" }
    LazyWindow { trigger: PluginManager.keybindsVisible; source: "plugins/keybinds/KeybindsWindow.qml" }
    LazyWindow { trigger: PluginManager.volumeVisible; source: "plugins/volume/VolumeMixerWindow.qml" }
    LazyWindow { trigger: PluginManager.brightnessVisible; source: "plugins/brightness/BrightnessWindow.qml" }
    LazyWindow { trigger: PluginManager.sysinfoVisible; source: "plugins/sysinfo/SysInfoWindow.qml" }
    LazyWindow { trigger: PluginManager.connectivityVisible; source: "plugins/connectivity/ConnectivityWindow.qml" }
    LazyWindow { trigger: PluginManager.batteryVisible; source: "plugins/battery/BatteryWindow.qml" }
    LazyWindow { trigger: PluginManager.notificationVisible; source: "plugins/notifications/NotificationWindow.qml" }
    LazyWindow { trigger: PluginManager.filePickerVisible; source: "plugins/filepicker/FilePickerWindow.qml" }
    LazyWindow { trigger: PluginManager.workspaceViewerVisible; source: "plugins/workspace_viewer/WorkspaceViewerWindow.qml" }
    CustomWindows {}
}
