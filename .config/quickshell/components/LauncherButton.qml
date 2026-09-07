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
    border.color: isHovered ? Theme.mauve : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    Text {
        anchors.centerIn: parent
        text: "󰣇"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: root.isHovered ? "#ffffff" : Theme.mauve
    }

    Process {
        id: launcherProc
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                launcherProc.exec(["bash", Quickshell.env("HOME") + "/.config/hypr/scripts/fuzzel_launcher.sh"]);
            } else if (mouse.button === Qt.RightButton) {
                launcherProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/power-menu.sh"]);
            }
        }
    }
}
