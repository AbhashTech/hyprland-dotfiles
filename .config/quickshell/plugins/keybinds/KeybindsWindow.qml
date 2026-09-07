import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: keybindsWindow

    visible: PluginManager.keybindsVisible

    anchors {
        top: true
    }

    margins {
        top: Theme.barHeight + 20
    }

    implicitWidth: 700
    implicitHeight: 520
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:keybinds"
    WlrLayershell.keyboardFocus: PluginManager.keybindsVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    KeybindsViewer {
        anchors.fill: parent
    }
}
