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

    // Backdrop overlay: intercepts clicks outside the modal
    MouseArea {
        anchors.fill: parent
        hoverEnabled: false
        preventStealing: true
        onClicked: filePickerModal.cancelAndClose()
    }

    FilePickerModal {
        id: filePickerModal
        width: implicitWidth
        height: implicitHeight
        anchors.centerIn: parent
        focus: true

        // Absorb clicks within the modal area so backdrop is never triggered
        MouseArea {
            anchors.fill: parent
            z: -1
            preventStealing: true
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
