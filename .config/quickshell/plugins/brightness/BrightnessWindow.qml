import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: brightnessWindow

    visible: PluginManager.brightnessVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:brightness"
    WlrLayershell.keyboardFocus: PluginManager.brightnessVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        BrightnessMenu {
            id: brightnessMenuItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.right: parent.right
            anchors.rightMargin: 80

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onBrightnessVisibleChanged() {
            if (PluginManager.brightnessVisible) {
                brightnessMenuItem.grabFocus();
            }
        }
    }
}
