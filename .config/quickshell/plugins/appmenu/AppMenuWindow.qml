import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: appMenuWindow

    visible: PluginManager.appMenuVisible

    anchors {
        top: true
        left: true
    }

    margins {
        top: Theme.barHeight + 16
        left: 16
    }

    implicitWidth: 640
    implicitHeight: 520
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:appmenu"
    WlrLayershell.keyboardFocus: PluginManager.appMenuVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    AppMenu {
        anchors.fill: parent
    }
}
