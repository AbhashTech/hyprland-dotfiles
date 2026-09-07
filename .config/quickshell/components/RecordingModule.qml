import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    property bool isRecording: false
    property string displayText: ""

    visible: isRecording
    implicitHeight: Theme.barHeight - 8
    implicitWidth: visible ? row.implicitWidth + 18 : 0
    radius: Theme.capsuleRadius

    color: Theme.moduleBg
    border.color: Theme.red
    border.width: 1

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
        interval: 1000
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
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        cursorShape: Qt.PointingHandCursor
        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "stop"]);
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "--toggle-indicator"]);
            } else if (mouse.button === Qt.MiddleButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/screen_capture.py", "menu"]);
            }
        }
    }
}
