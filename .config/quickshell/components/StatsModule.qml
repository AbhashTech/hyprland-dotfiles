import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    Text {
        anchors.centerIn: parent
        text: "󰍛"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: root.isHovered ? Theme.accent : Theme.text
    }

    Process {
        id: ctlProc
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/system-stats.py"]);
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
            }
        }
    }
}
