import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    property var barWindow: null
    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered || PluginManager.sysinfoVisible ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered || PluginManager.sysinfoVisible ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    Text {
        anchors.centerIn: parent
        text: "󰍛"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: root.isHovered || PluginManager.sysinfoVisible ? Theme.accent : Theme.text
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: "󰍛"
        iconColor: Theme.accent
        title: "System Resources"
        description: "CPU, RAM, Disk & Hardware Monitor"
        shortcuts: [
            { action: "System Info Center", key: "Left Click" },
            { action: "Task Manager (btop)", key: "Right Click" }
        ]
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
                PluginManager.toggle("sysinfo");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
            }
        }
    }
}
