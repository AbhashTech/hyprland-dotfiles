import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."
import "."

PanelWindow {
    id: root

    visible: PluginManager.barCustomizerVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: Qt.rgba(0, 0, 0, 0.45)

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:bar_customizer"
    WlrLayershell.keyboardFocus: PluginManager.barCustomizerVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.toggle("bar_customizer")

        BarCustomizerMenu {
            id: menuContent
            anchors.centerIn: parent

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Item {
        focus: true
        Keys.onEscapePressed: PluginManager.toggle("bar_customizer")
    }
}
