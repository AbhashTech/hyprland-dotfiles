import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: batContent.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: batArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property var barWindow: null

    Process {
        id: ctlProc
    }

    Row {
        id: batContent
        anchors.centerIn: parent
        spacing: 4

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.batIcon
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: StatusService.batColor

            Behavior on color { ColorAnimation { duration: 200 } }
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.batPercent
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
        icon: StatusService.batIcon
        iconColor: StatusService.batColor
        title: "Battery & Power (" + StatusService.batPercent + ")"
        description: StatusService.batStatus + (StatusService.batTimeStr !== "" ? " • " + StatusService.batTimeStr : "")
        shortcuts: [
            { action: "Power Profiles Menu", key: "Left Click" },
            { action: "Task Manager (btop)", key: "Right Click" }
        ]
    }

    MouseArea {
        id: batArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("battery");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
            }
        }
    }
}
