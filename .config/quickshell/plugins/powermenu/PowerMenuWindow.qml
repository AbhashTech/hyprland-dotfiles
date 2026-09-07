import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: powerMenuWindow

    visible: PluginManager.powerMenuVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:powermenu"
    WlrLayershell.keyboardFocus: PluginManager.powerMenuVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    // Dim background overlay
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.45)

        MouseArea {
            anchors.fill: parent
            onClicked: PluginManager.closeAll()
        }

        PowerMenu {
            id: powerMenu
            anchors.centerIn: parent

            Component.onCompleted: {
                if (powerMenuWindow.visible) {
                    powerMenu.forceActiveFocus();
                }
            }
        }
    }

    Connections {
        target: PluginManager
        function onPowerMenuVisibleChanged() {
            if (PluginManager.powerMenuVisible) {
                powerMenu.forceActiveFocus();
            }
        }
    }
}
