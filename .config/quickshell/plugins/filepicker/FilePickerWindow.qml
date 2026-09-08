import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

// Fullscreen overlay window — same pattern as EmojiPickerWindow / ClipboardWindow
PanelWindow {
    id: filePickerWindow

    visible: PluginManager.filePickerVisible

    anchors {
        top:    true
        left:   true
        right:  true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer:         WlrLayer.Overlay
    WlrLayershell.namespace:     "quickshell:filepicker"
    WlrLayershell.keyboardFocus: PluginManager.filePickerVisible
                                     ? WlrKeyboardFocus.Exclusive
                                     : WlrKeyboardFocus.None

    // Clicking the backdrop closes the picker (same as clipboard/emoji)
    MouseArea {
        anchors.fill: parent
        onClicked: {
            filePickerModal.cancelAndClose()
        }

        FilePickerModal {
            id: filePickerModal
            anchors.centerIn: parent

            // Prevent backdrop click from propagating through the modal
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onFilePickerVisibleChanged() {
            if (PluginManager.filePickerVisible) {
                filePickerModal.grabFocus()
            }
        }
    }
}
