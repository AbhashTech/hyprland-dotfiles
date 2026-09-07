import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: brightnessWindow

    visible: PluginManager.brightnessVisible

    anchors {
        top: true
        right: true
    }

    margins {
        top: Theme.barHeight + 16
        right: 80
    }

    implicitWidth: 380
    implicitHeight: 220
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:brightness"
    WlrLayershell.keyboardFocus: PluginManager.brightnessVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    BrightnessMenu {
        anchors.fill: parent
    }
}
