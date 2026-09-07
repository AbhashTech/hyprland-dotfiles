import QtQuick
import Quickshell
import Quickshell.Wayland
import "components"

ShellRoot {
    id: root

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

                        LauncherButton {}
                        Workspaces {}
                        ActiveWindow {}
                        MprisModule {}
                    }

                    // Center Modules
                    Row {
                        id: centerGroup
                        anchors.centerIn: parent
                        spacing: 6

                        ClockModule {}
                        LanguageModule {}
                    }

                    // Right Modules
                    Row {
                        id: rightGroup
                        anchors.right: parent.right
                        anchors.rightMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 6

                        RecordingModule {}
                        TrayNotifGroup {}
                        StatusGroup {}
                        StatsModule {}
                        PowerModule {}
                    }
                }
            }
        }
    }
}
