import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: volContent.implicitWidth + 12
    radius: Theme.capsuleRadius

    readonly property bool isHovered: volArea.containsMouse
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
        id: volContent
        anchors.centerIn: parent
        spacing: 3

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.muted ? "󰝟" : (StatusService.volume > 50 ? "󰕾" : "󰖀")
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: StatusService.muted ? Theme.red : Theme.blue
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.volume + "%"
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
        icon: StatusService.muted ? "󰝟" : (StatusService.volume > 50 ? "󰕾" : "󰖀")
        iconColor: StatusService.muted ? Theme.red : Theme.blue
        title: "Audio & Sound"
        description: "PipeWire / WirePlumber audio server"
        details: [
            {
                icon: StatusService.muted ? "󰝟" : "󰕾",
                iconColor: StatusService.muted ? Theme.red : Theme.blue,
                label: "Output (" + StatusService.sinkName + ")",
                value: StatusService.muted ? "Muted" : (StatusService.volume + "%"),
                valueColor: StatusService.muted ? Theme.red : Theme.text
            },
            {
                icon: StatusService.micMuted ? "󰍭" : "󰍬",
                iconColor: StatusService.micMuted ? Theme.red : Theme.mauve,
                label: "Input (" + StatusService.micName + ")",
                value: StatusService.micMuted ? "Muted" : (StatusService.micVolume + "%"),
                valueColor: StatusService.micMuted ? Theme.red : Theme.text
            },
            {
                icon: "󰓃",
                iconColor: Theme.sapphire,
                label: "Audio Server",
                value: "PipeWire",
                valueColor: Theme.subtext0
            }
        ]
        shortcuts: [
            { action: "Toggle Mute", key: "Left Click" },
            { action: "Audio Mixer Menu", key: "Right Click" },
            { action: "Volume Up / Down", key: "Scroll" }
        ]
    }

    MouseArea {
        id: volArea
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
                    BarConfig.startDrag("volume", root.barSection, root.barIndex);
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
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "mute"]);
            } else if (mouse.button === Qt.RightButton) {
                PluginManager.toggle("volume");
            }
        }

        onWheel: wheel => {
            if (wheel.angleDelta.y > 0) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "up", "5"]);
            } else if (wheel.angleDelta.y < 0) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "down", "5"]);
            }
        }
    }
}
