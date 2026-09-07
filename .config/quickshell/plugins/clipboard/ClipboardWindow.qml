import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: clipboardWindow

    visible: PluginManager.clipboardVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:clipboard"
    WlrLayershell.keyboardFocus: PluginManager.clipboardVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        ClipboardMenu {
            id: clipboardMenuItem
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

    Connections {
        target: PluginManager
        function onClipboardVisibleChanged() {
            if (PluginManager.clipboardVisible) {
                clipboardMenuItem.grabFocus();
            }
        }
    }
}
