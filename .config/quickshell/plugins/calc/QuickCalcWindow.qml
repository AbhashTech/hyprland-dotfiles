import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: calcWindow

    visible: PluginManager.calcVisible

    anchors {
        top: true
    }

    margins {
        top: Theme.barHeight + 40
    }

    implicitWidth: 440
    implicitHeight: 200
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:calc"
    WlrLayershell.keyboardFocus: PluginManager.calcVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    QuickCalc {
        anchors.fill: parent
    }
}
