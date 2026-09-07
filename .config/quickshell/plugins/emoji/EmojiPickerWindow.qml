import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: emojiWindow

    visible: PluginManager.emojiVisible

    anchors {
        top: true
    }

    margins {
        top: Theme.barHeight + 30
    }

    implicitWidth: 560
    implicitHeight: 460
    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:emoji"
    WlrLayershell.keyboardFocus: PluginManager.emojiVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    EmojiPicker {
        anchors.fill: parent
    }
}
