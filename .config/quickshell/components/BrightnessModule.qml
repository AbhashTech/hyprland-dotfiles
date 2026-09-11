import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: brightContent.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: brightArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property var barWindow: null

    Process {
        id: ctlProc
    }

    Row {
        id: brightContent
        anchors.centerIn: parent
        spacing: 4

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "󰃠"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.yellow
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: StatusService.brightness + "%"
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
        icon: "󰃠"
        iconColor: Theme.yellow
        title: "Screen Brightness"
        description: "Display brightness: " + StatusService.brightness + "%"
        shortcuts: [
            { action: "Brightness Center", key: "Left Click" },
            { action: "Night Light Filter", key: "Right Click" },
            { action: "Brightness Up / Down", key: "Scroll" }
        ]
    }

    MouseArea {
        id: brightArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("brightness");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/sunset_idle_manager.py", "--sunset-toggle"]);
            }
        }

        onWheel: wheel => {
            var act = wheel.angleDelta.y > 0 ? "active-up" : "active-down";
            ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/brightness_control.py", act, "5"]);
            if (wheel.angleDelta.y > 0) {
                StatusService.brightness = Math.min(100, StatusService.brightness + 5);
            } else if (wheel.angleDelta.y < 0) {
                StatusService.brightness = Math.max(0, StatusService.brightness - 5);
            }
        }
    }
}
