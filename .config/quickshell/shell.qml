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
                        MprisModule {
                            barWindow: barWindow
                        }
                    }

                    // Center Modules
                    Row {
                        id: centerGroup
                        anchors.centerIn: parent
                        spacing: 6

                        ClockModule {
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
                    }
                }
            }
        }
    }

    // Modular Quickshell Plugin Windows
    AppMenuWindow {}
    PowerMenuWindow {}
    ClipboardWindow {}
    QuickCalcWindow {}
    EmojiPickerWindow {}
    KeybindsWindow {}
    VolumeMixerWindow {}
    BrightnessWindow {}
    SysInfoWindow {}
    ConnectivityWindow {}
    BatteryWindow {}
    NotificationWindow {}
}
