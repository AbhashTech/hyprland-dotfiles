import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: clipboardWindow

    visible: PluginManager.clipboardVisible

    anchors {
        top: true
        right: true
    }

    margins {
        top: Theme.barHeight + 16
        right: 16
    }

    implicitWidth: 540
    implicitHeight: 480
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:clipboard"
    WlrLayershell.keyboardFocus: PluginManager.clipboardVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    ClipboardMenu {
        anchors.fill: parent
    }
}
