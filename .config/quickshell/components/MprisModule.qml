import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property string playerStatus: ""
    property string mediaText: ""
    property string fullMediaText: ""
    property bool isPlaying: playerStatus === "Playing"
    property bool hasMedia: mediaText.length > 0

    visible: hasMedia
    implicitHeight: Theme.barHeight - 8
    implicitWidth: visible ? Math.min(row.implicitWidth + 20, 240) : 0
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on implicitWidth { NumberAnimation { duration: 150 } }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: root.isPlaying ? "󰐊" : "󰏤"
        iconColor: root.isPlaying ? Theme.green : Theme.subtext0
        title: root.fullMediaText !== "" ? root.fullMediaText : "Media Player"
        description: root.isPlaying ? "Currently Playing" : "Playback Paused"
        shortcuts: [
            { action: "Play / Pause", key: "Left Click" },
            { action: "Next Track", key: "Scroll Up" },
            { action: "Previous Track", key: "Scroll Down" }
        ]
    }

    Process {
        id: mprisStatusProc
        command: ["playerctl", "status"]
        stdout: SplitParser {
            onRead: data => {
                root.playerStatus = data.trim();
            }
        }
    }

    Process {
        id: mprisMetaProc
        command: ["playerctl", "metadata", "--format", "{{artist}} - {{title}}"]
        stdout: SplitParser {
            onRead: data => {
                var raw = data.trim();
                root.fullMediaText = raw;
                var txt = raw;
                if (txt.length > 26) {
                    txt = txt.substring(0, 23) + "...";
                }
                root.mediaText = txt;
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
            if (!mprisStatusProc.running) mprisStatusProc.running = true;
            if (!mprisMetaProc.running) mprisMetaProc.running = true;
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.isPlaying ? "󰐊" : "󰏤"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: root.isPlaying ? Theme.green : Theme.subtext0
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.mediaText
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            font.italic: !root.isPlaying
            color: Theme.text
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            ctlProc.exec(["playerctl", "play-pause"]);
        }

        onWheel: wheel => {
            if (wheel.angleDelta.y > 0) {
                ctlProc.exec(["playerctl", "next"]);
            } else if (wheel.angleDelta.y < 0) {
                ctlProc.exec(["playerctl", "previous"]);
            }
        }
    }
}
