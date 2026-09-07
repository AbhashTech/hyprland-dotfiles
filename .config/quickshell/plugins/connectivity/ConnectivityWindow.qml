import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: connectivityWindow

    visible: PluginManager.connectivityVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:connectivity"
    WlrLayershell.keyboardFocus: PluginManager.connectivityVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        ConnectivityMenu {
            id: connectivityMenuItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.right: parent.right
            anchors.rightMargin: 65

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onConnectivityVisibleChanged() {
            if (PluginManager.connectivityVisible) {
                connectivityMenuItem.grabFocus();
            }
        }
    }
}
