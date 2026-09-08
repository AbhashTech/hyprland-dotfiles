import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: notificationWindow

    visible: PluginManager.notificationVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:notifications"
    WlrLayershell.keyboardFocus: PluginManager.notificationVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        NotificationMenu {
            id: notificationMenuItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.right: parent.right
            anchors.rightMargin: 16

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }
}
