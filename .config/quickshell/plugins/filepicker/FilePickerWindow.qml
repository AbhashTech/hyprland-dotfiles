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
        anchors.centerIn: parent
        focus: true

        // Absorb clicks within the modal area so backdrop is never triggered
        MouseArea {
            anchors.fill: parent
            z: -1
            preventStealing: true
        }
    }

    // Capture OS close keyboard shortcuts (Super+C, Alt+F4, Super+Q, Super+W, Escape)
    Keys.onPressed: (event) => {
        var isSuper = (event.modifiers & Qt.MetaModifier);
        var isAlt   = (event.modifiers & Qt.AltModifier);
        if (event.key === Qt.Key_Escape ||
            (isSuper && (event.key === Qt.Key_C || event.key === Qt.Key_Q || event.key === Qt.Key_W)) ||
            (isAlt && event.key === Qt.Key_F4)) {
            filePickerModal.cancelAndClose();
            event.accepted = true;
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
