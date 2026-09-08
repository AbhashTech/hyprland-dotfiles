import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: calcWindow

    visible: PluginManager.calcVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:calc"
    WlrLayershell.keyboardFocus: PluginManager.calcVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        QuickCalc {
            id: quickCalcItem
            anchors.centerIn: parent

            // Prevent clicks inside popup from dismissing
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onCalcVisibleChanged() {
            if (PluginManager.calcVisible) {
                quickCalcItem.grabFocus();
            }
        }
    }
}
