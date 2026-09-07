import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: appMenuWindow

    visible: PluginManager.appMenuVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:appmenu"
    WlrLayershell.keyboardFocus: PluginManager.appMenuVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        AppMenu {
            id: appMenuItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.left: parent.left
            anchors.leftMargin: 16

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onAppMenuVisibleChanged() {
            if (PluginManager.appMenuVisible) {
                appMenuItem.grabFocus();
            }
        }
    }
}
