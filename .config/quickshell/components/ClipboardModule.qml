import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    readonly property bool isHovered: clipArea.containsMouse
    color: isHovered || PluginManager.clipboardVisible ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered || PluginManager.clipboardVisible ? Theme.lavender : Theme.moduleBorder
    border.width: 1

    property var barWindow: null

    Process {
        id: ctlProc
    }

    Text {
        anchors.centerIn: parent
        text: StatusService.clipDndActive ? "󰈉" : "󰅌"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: StatusService.clipDndActive ? Theme.peach : Theme.lavender
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: StatusService.clipDndActive ? "󰈉" : "󰅌"
        iconColor: StatusService.clipDndActive ? Theme.peach : Theme.lavender
        title: "Clipboard History"
        description: StatusService.clipDndActive ? "Private Mode (Recording Paused)" : "Search and paste history entries"
        shortcuts: [
            { action: "Open Clipboard", key: "Left / Right Click" },
            { action: "Toggle Private Mode", key: "Middle Click" },
            { action: "Shortcut", key: "SUPER + SHIFT + V" }
        ]
    }

    MouseArea {
        id: clipArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton || mouse.button === Qt.RightButton) {
                PluginManager.toggle("clipboard");
            } else if (mouse.button === Qt.MiddleButton) {
                StatusService.clipDndActive = !StatusService.clipDndActive;
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "toggle-private"]);
            }
        }
    }
}
