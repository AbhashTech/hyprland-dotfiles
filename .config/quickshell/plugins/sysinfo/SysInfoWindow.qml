import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: sysinfoWindow

    visible: PluginManager.sysinfoVisible

    anchors {
        top: true
        right: true
    }

    margins {
        top: Theme.barHeight + 16
        right: 40
    }

    implicitWidth: 440
    implicitHeight: 340
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:sysinfo"
    WlrLayershell.keyboardFocus: PluginManager.sysinfoVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    SystemStats {
        anchors.fill: parent
    }
}
