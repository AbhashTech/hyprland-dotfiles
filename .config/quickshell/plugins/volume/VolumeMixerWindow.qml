import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: volumeWindow

    visible: PluginManager.volumeVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:volume"
    WlrLayershell.keyboardFocus: PluginManager.volumeVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        VolumeMixer {
            id: volumeMixerItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.right: parent.right
            anchors.rightMargin: 120

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onVolumeVisibleChanged() {
            if (PluginManager.volumeVisible) {
                volumeMixerItem.grabFocus();
            }
        }
    }
}
