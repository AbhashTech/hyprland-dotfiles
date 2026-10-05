import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.." // Theme
import "."

PanelWindow {
    id: manageWindow

    visible: PluginManager.isPluginVisible("calendar_sync")

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:calendar_sync"
    WlrLayershell.keyboardFocus: visible ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None

    // Dimmed background backdrop with click-outside to close
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.5)
        opacity: manageWindow.visible ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 150 } }

        MouseArea {
            anchors.fill: parent
            onClicked: PluginManager.setPluginVisible("calendar_sync", false)
        }
    }

    CalendarManageModal {
        id: modalContent
        anchors.centerIn: parent
        isOpen: manageWindow.visible
        onClosed: {
            PluginManager.setPluginVisible("calendar_sync", false);
        }
    }
}
