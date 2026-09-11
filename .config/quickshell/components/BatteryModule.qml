import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: batContent.implicitWidth + 12
    radius: Theme.capsuleRadius

    readonly property bool isHovered: batArea.containsMouse
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
        id: batContent
        anchors.centerIn: parent
        spacing: 3

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.batIcon
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: StatusService.batColor

            Behavior on color { ColorAnimation { duration: 200 } }
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.batPercent
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
        icon: StatusService.batIcon
        iconColor: StatusService.batColor
        title: "Battery & Power (" + StatusService.batPercent + ")"
        description: StatusService.batStatus + (StatusService.batTimeStr !== "" ? " • " + StatusService.batTimeStr : "")
        details: [
            {
                icon: StatusService.batIcon,
                iconColor: StatusService.batColor,
                label: "State & Charge",
                value: StatusService.batStatus + " (" + StatusService.batPercent + ")",
                valueColor: StatusService.batColor
            },
            {
                icon: StatusService.batProfile === "power-saver" ? "󰾆" : (StatusService.batProfile === "performance" ? "󰓅" : "󰾅"),
                iconColor: StatusService.batColor,
                label: "Power Profile",
                value: StatusService.batProfile ? (StatusService.batProfile.charAt(0).toUpperCase() + StatusService.batProfile.slice(1)) : "Balanced",
                valueColor: StatusService.batColor
            },
            {
                icon: "󱐋",
                iconColor: Theme.peach,
                label: "Power Draw",
                value: (StatusService.batPowerW > 0 ? (StatusService.batPowerW + " W") : "On AC Power"),
                valueColor: Theme.peach
            },
            {
                icon: "󰁹",
                iconColor: StatusService.batHealth >= 80 ? Theme.green : (StatusService.batHealth >= 60 ? Theme.yellow : Theme.red),
                label: "Battery Health",
                value: StatusService.batHealth + "%",
                valueColor: StatusService.batHealth >= 80 ? Theme.green : Theme.yellow
            },
            {
                icon: "󱎫",
                iconColor: Theme.sapphire,
                label: "Runtime Estimate",
                value: StatusService.batTimeStr !== "" ? StatusService.batTimeStr : (StatusService.batStatus === "Full" ? "Fully Charged" : "Calculating..."),
                valueColor: Theme.text
            }
        ]
        shortcuts: [
            { action: "Power Profiles Menu", key: "Left Click" },
            { action: "Task Manager (btop)", key: "Right Click" }
        ]
    }

    MouseArea {
        id: batArea
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
                    BarConfig.startDrag("battery", root.barSection, root.barIndex);
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
                PluginManager.toggle("battery");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
            }
        }
    }
}
