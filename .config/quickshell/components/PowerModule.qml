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
    color: isHovered ? Theme.red : Theme.moduleBg
    border.color: isHovered ? Theme.red : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    Text {
        anchors.centerIn: parent
        text: "󰐥"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: root.isHovered ? "#ffffff" : Theme.red
    }

    Process {
        id: ctlProc
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/power-menu.sh"]);
        }
    }
}
