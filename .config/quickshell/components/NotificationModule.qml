import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: notifRow.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: notifArea.containsMouse
    color: isHovered || PluginManager.notificationVisible ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered || PluginManager.notificationVisible ? Theme.peach : Theme.moduleBorder
    border.width: 1

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null

    Process {
        id: ctlProc
    }

    Row {
        id: notifRow
        anchors.centerIn: parent
        spacing: 4

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.dndActive ? "󰂛" : (StatusService.notifCount > 0 ? "󱅫" : "󰂚")
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: StatusService.dndActive ? Theme.peach : (StatusService.notifCount > 0 ? Theme.peach : Theme.accent)
        }

        Text {
            visible: StatusService.notifCount > 0
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.notifCount.toString()
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall
            font.bold: true
            color: Theme.peach
        }
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: StatusService.dndActive ? "󰂛" : (StatusService.notifCount > 0 ? "󱅫" : "󰂚")
        iconColor: StatusService.dndActive ? Theme.peach : Theme.accent
        title: "Notification Center"
        description: StatusService.dndActive ? "Do-Not-Disturb is ON" : (StatusService.notifCount > 0 ? (StatusService.notifCount + " Unread Notification" + (StatusService.notifCount > 1 ? "s" : "")) : "No unread notifications")
        shortcuts: [
            { action: "Open Notifications", key: "Left / Right Click" },
            { action: "Toggle DND", key: "Middle Click" },
            { action: "Shortcut", key: "SUPER + N" }
        ]
    }

    MouseArea {
        id: notifArea
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
                    BarConfig.startDrag("notifications", root.barSection, root.barIndex);
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
                PluginManager.toggle("notifications");
            } else if (mouse.button === Qt.MiddleButton) {
                StatusService.dndActive = !StatusService.dndActive;
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "toggle-dnd"]);
            }
        }
    }
}
