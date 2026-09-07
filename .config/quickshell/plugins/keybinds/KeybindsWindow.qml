import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: keybindsWindow

    visible: PluginManager.keybindsVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:keybinds"
    WlrLayershell.keyboardFocus: PluginManager.keybindsVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        KeybindsViewer {
            id: keybindsViewerItem
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 20
            anchors.horizontalCenter: parent.horizontalCenter

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onKeybindsVisibleChanged() {
            if (PluginManager.keybindsVisible) {
                keybindsViewerItem.grabFocus();
            }
        }
    }
}
