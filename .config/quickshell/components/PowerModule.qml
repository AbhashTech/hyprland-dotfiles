import QtQuick
import Quickshell
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    property var barWindow: null
    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered || PluginManager.powerMenuVisible ? Theme.red : Theme.moduleBg
    border.color: isHovered || PluginManager.powerMenuVisible ? Theme.red : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    Text {
        anchors.centerIn: parent
        text: "󰐥"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: root.isHovered || PluginManager.powerMenuVisible ? "#ffffff" : Theme.red
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: "󰐥"
        iconColor: Theme.red
        title: "Power & Session"
        description: "Shutdown, restart, lock, or sleep"
        shortcuts: [
            { action: "Power Menu", key: "SUPER + Escape" },
            { action: "Quick Power", key: "SUPER + M" },
            { action: "Lock Screen", key: "SUPER + L" }
        ]
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            PluginManager.toggle("powermenu");
        }
    }
}
