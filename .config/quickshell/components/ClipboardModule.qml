import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 32
    radius: Theme.capsuleRadius

    readonly property bool isHovered: clipArea.containsMouse
    color: isHovered || PluginManager.clipboardVisible ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered || PluginManager.clipboardVisible ? Theme.lavender : Theme.moduleBorder
    border.width: 1

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null

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
        isHovered: root.isHovered && !BarConfig.isDragging
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
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

        property real pressX: 0
        property real pressY: 0
        property bool didDrag: false

        onPressed: mouse => {
            pressX = mouse.x;
            pressY = mouse.y;
            didDrag = false;
        }

        onPositionChanged: mouse => {
            if (pressed && mouse.buttons === Qt.LeftButton) {
                var dx = mouse.x - pressX;
                var dy = mouse.y - pressY;
                if (!didDrag && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
                    didDrag = true;
                    BarConfig.startDrag("clipboard", root.barSection, root.barIndex);
                }
                if (didDrag && root.barContainer) {
                    var pt = mapToItem(root.barContainer, mouse.x, mouse.y);
                    BarConfig.updateDragPos(pt.x, root.barContainer.width);
                }
            }
        }

        onReleased: mouse => {
            if (didDrag) {
                BarConfig.endDrag();
                didDrag = false;
            } else if (mouse.button === Qt.LeftButton || mouse.button === Qt.RightButton) {
                PluginManager.toggle("clipboard");
            } else if (mouse.button === Qt.MiddleButton) {
                StatusService.clipDndActive = !StatusService.clipDndActive;
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "toggle-private"]);
            }
        }
    }
}
