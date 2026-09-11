import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: brightContent.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: brightArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null

    Process {
        id: ctlProc
    }

    Row {
        id: brightContent
        anchors.centerIn: parent
        spacing: 4

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "󰃠"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.yellow
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.brightness + "%"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
        }
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: "󰃠"
        iconColor: Theme.yellow
        title: "Screen Brightness"
        description: "Display brightness: " + StatusService.brightness + "%"
        shortcuts: [
            { action: "Brightness Center", key: "Left Click" },
            { action: "Night Light Filter", key: "Right Click" },
            { action: "Brightness Up / Down", key: "Scroll" }
        ]
    }

    MouseArea {
        id: brightArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

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
                    BarConfig.startDrag("brightness", root.barSection, root.barIndex);
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
            } else if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("brightness");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/sunset_idle_manager.py", "--sunset-toggle"]);
            }
        }

        onWheel: wheel => {
            var act = wheel.angleDelta.y > 0 ? "active-up" : "active-down";
            ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/brightness_control.py", act, "5"]);
            if (wheel.angleDelta.y > 0) {
                StatusService.brightness = Math.min(100, StatusService.brightness + 5);
            } else if (wheel.angleDelta.y < 0) {
                StatusService.brightness = Math.max(0, StatusService.brightness - 5);
            }
        }
    }
}
