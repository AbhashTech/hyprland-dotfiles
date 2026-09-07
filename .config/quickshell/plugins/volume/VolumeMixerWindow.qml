import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: volumeWindow

    visible: PluginManager.volumeVisible

    anchors {
        top: true
        right: true
    }

    margins {
        top: Theme.barHeight + 16
        right: 120
    }

    implicitWidth: 420
    implicitHeight: 280
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:volume"
    WlrLayershell.keyboardFocus: PluginManager.volumeVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    VolumeMixer {
        anchors.fill: parent
    }
}
