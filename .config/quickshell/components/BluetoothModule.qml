import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    readonly property bool isHovered: btArea.containsMouse
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
        text: StatusService.btText
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: StatusService.btConnected ? Theme.green : (StatusService.btPowered ? Theme.blue : Theme.red)
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: StatusService.btText
        iconColor: StatusService.btConnected ? Theme.green : (StatusService.btPowered ? Theme.blue : Theme.red)
        title: StatusService.btConnected ? (StatusService.btConnectedCount + " Devices Connected") : (StatusService.btPowered ? "Bluetooth On" : "Bluetooth Off")
        description: StatusService.btConnected ? "Active Bluetooth peripherals" : "Click to scan and connect devices"
        shortcuts: [
            { action: "Bluetooth Control Center", key: "Left Click" },
            { action: "Toggle Bluetooth Radio", key: "Right Click" }
        ]
    }

    MouseArea {
        id: btArea
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
                    BarConfig.startDrag("bluetooth", root.barSection, root.barIndex);
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
                PluginManager.toggle("bluetooth");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/connectivity/wireless_ctl.py", "bt-toggle"]);
            }
        }
    }
}
