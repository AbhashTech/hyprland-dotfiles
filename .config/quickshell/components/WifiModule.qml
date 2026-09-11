import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    readonly property bool isHovered: netArea.containsMouse
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

    Text {
        anchors.centerIn: parent
        text: StatusService.wifiText
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: StatusService.wifiConnected ? Theme.teal : (StatusService.wifiPowered ? Theme.subtext0 : Theme.red)
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: StatusService.wifiText
        iconColor: StatusService.wifiConnected ? Theme.teal : (StatusService.wifiPowered ? Theme.subtext0 : Theme.red)
        title: StatusService.wifiConnected ? StatusService.wifiSsid : (StatusService.wifiPowered ? "Wi-Fi Disconnected" : "Wi-Fi Disabled")
        description: StatusService.wifiConnected ? ("Signal: " + StatusService.wifiSignal + "% • IP: " + (StatusService.wifiIp || "N/A")) : "Click to manage wireless networks"
        shortcuts: [
            { action: "Wi-Fi Control Center", key: "Left Click" },
            { action: "Toggle Wi-Fi Radio", key: "Right Click" }
        ]
    }

    MouseArea {
        id: netArea
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
                    BarConfig.startDrag("wifi", root.barSection, root.barIndex);
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
                PluginManager.toggle("wifi");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/connectivity/wireless_ctl.py", "wifi-toggle"]);
            }
        }
    }
}
