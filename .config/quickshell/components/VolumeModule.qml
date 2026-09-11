import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: volContent.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: volArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property var barWindow: null

    Process {
        id: ctlProc
    }

    Row {
        id: volContent
        anchors.centerIn: parent
        spacing: 4

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
        isHovered: root.isHovered
        icon: StatusService.muted ? "󰝟" : (StatusService.volume > 50 ? "󰕾" : "󰖀")
        iconColor: StatusService.muted ? Theme.red : Theme.blue
        title: "Audio & Sound"
        description: "Output: " + StatusService.sinkName + " • " + (StatusService.muted ? "Muted" : (StatusService.volume + "%"))
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
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
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
