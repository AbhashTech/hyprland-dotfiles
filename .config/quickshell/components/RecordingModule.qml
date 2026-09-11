import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null
    property bool isRecording: false
    property string displayText: ""

    visible: isRecording
    implicitHeight: Theme.barHeight - 8
    implicitWidth: visible ? row.implicitWidth + 18 : 0
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: Theme.moduleBg
    border.color: Theme.red
    border.width: 1

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: "󰻃"
        iconColor: Theme.red
        title: "Screen Recording"
        description: root.displayText !== "" ? ("Status: " + root.displayText) : "Active Screen Recording"
        shortcuts: [
            { action: "Stop Recording", key: "SUPER + CTRL + R" },
            { action: "Recording Hub", key: "SUPER + Print" },
            { action: "Toggle Indicator", key: "Right Click" }
        ]
    }

    Process {
        id: statusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "--status"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj && obj.text) {
                        root.displayText = obj.text;
                        root.isRecording = obj.text.indexOf("REC") !== -1 || obj.alt === "recording";
                    } else {
                        root.isRecording = false;
                    }
                } catch (e) {
                    root.isRecording = false;
                }
            }
        }
    }

    Process {
        id: ctlProc
    }

    Timer {
        interval: root.isRecording ? 1000 : 3000
        running: true
        repeat: true
        onTriggered: {
            if (!statusProc.running) statusProc.running = true;
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "󰻃"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.red
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.displayText
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor

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
                    BarConfig.startDrag("recording", root.barSection, root.barIndex);
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
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "stop"]);
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "--toggle-indicator"]);
            } else if (mouse.button === Qt.MiddleButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "menu"]);
            }
        }
    }
}
