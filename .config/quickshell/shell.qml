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
import "plugins/plugin-manager"
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

    // Dynamic Modular Status Bar across all connected displays
    Variants {
        model: Quickshell.screens

        delegate: Component {
            PanelWindow {
                id: barWindow
                required property var modelData
                screen: modelData

                // Dynamic Top / Bottom positioning & margins from BarConfig
                anchors {
                    top: BarConfig.isTop
                    bottom: BarConfig.isBottom
                    left: true
                    right: true
                }

                margins {
                    top: BarConfig.isTop ? BarConfig.marginTop : 0
                    bottom: BarConfig.isBottom ? BarConfig.marginBottom : 0
                    left: BarConfig.marginLeft
                    right: BarConfig.marginRight
                }

                implicitHeight: BarConfig.barHeight
                color: "transparent"

                WlrLayershell.layer: WlrLayer.Top
                WlrLayershell.namespace: "quickshell"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
                exclusiveZone: BarConfig.barHeight + (BarConfig.isTop ? BarConfig.marginTop : BarConfig.marginBottom)

                // Main glassmorphic container
                Rectangle {
                    id: barContainer
                    anchors.fill: parent
                    radius: BarConfig.barRadius
                    color: Theme.barBg
                    border.color: BarConfig.isDragging ? Theme.accent : Theme.barBorder
                    border.width: 1

                    Behavior on radius { NumberAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    // Left Modules Section
                    DynamicBarSection {
                        id: leftGroup
                        section: "left"
                        barWindow: barWindow
                        barContainer: barContainer
                        anchors.left: parent.left
                        anchors.leftMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    // Center Modules Section
                    DynamicBarSection {
                        id: centerGroup
                        section: "center"
                        barWindow: barWindow
                        barContainer: barContainer
                        anchors.centerIn: parent
                    }

                    // Right Modules Section
                    DynamicBarSection {
                        id: rightGroup
                        section: "right"
                        barWindow: barWindow
                        barContainer: barContainer
                        anchors.right: parent.right
                        anchors.rightMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    // Floating Live Drag Ghost (follows cursor anywhere across the bar)
                    Rectangle {
                        id: dragGhost
                        visible: BarConfig.isDragging && BarConfig.draggedModule !== ""
                        x: BarConfig.dragX - width / 2
                        y: 4
                        height: parent.height - 8
                        width: ghostRow.implicitWidth + 24
                        radius: BarConfig.capsuleRadius
                        color: Theme.moduleActiveBg
                        border.color: Theme.accent
                        border.width: 2
                        z: 999
                        scale: 1.06

                        readonly property var ghostMeta: BarConfig.getModuleMeta(BarConfig.draggedModule)

                        Row {
                            id: ghostRow
                            anchors.centerIn: parent
                            spacing: 6

                            Text {
                                text: dragGhost.ghostMeta ? dragGhost.ghostMeta.icon : "󰏖"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeIcon
                                color: Theme.accent
                            }

                            Text {
                                text: dragGhost.ghostMeta ? dragGhost.ghostMeta.name : BarConfig.draggedModule
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: "#ffffff"
                            }
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
    LazyWindow { trigger: PluginManager.pluginManagerVisible; source: "plugins/plugin-manager/PluginManagerWindow.qml" }
    CustomWindows {}
}
