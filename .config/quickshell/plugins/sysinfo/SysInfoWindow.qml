import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: sysinfoWindow

    visible: PluginManager.sysinfoVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:sysinfo"
    WlrLayershell.keyboardFocus: PluginManager.sysinfoVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        SystemStats {
            id: systemStatsItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.right: parent.right
            anchors.rightMargin: 40

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onSysinfoVisibleChanged() {
            if (PluginManager.sysinfoVisible) {
                systemStatsItem.grabFocus();
            }
        }
    }
}
