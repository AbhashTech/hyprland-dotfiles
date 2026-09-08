import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: emojiWindow

    visible: PluginManager.emojiVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:emoji"
    WlrLayershell.keyboardFocus: PluginManager.emojiVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        EmojiPicker {
            id: emojiPickerItem
            anchors.centerIn: parent

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onEmojiVisibleChanged() {
            if (PluginManager.emojiVisible) {
                emojiPickerItem.grabFocus();
            }
        }
    }
}
