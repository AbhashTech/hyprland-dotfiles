import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: batteryWindow

    visible: PluginManager.batteryVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:battery"
    WlrLayershell.keyboardFocus: PluginManager.batteryVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        BatteryMenu {
            id: batteryMenuItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.right: parent.right
            anchors.rightMargin: 70

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onBatteryVisibleChanged() {
            if (PluginManager.batteryVisible) {
                batteryMenuItem.grabFocus();
            }
        }
    }
}
