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

    color: isHovered || PluginManager.appMenuVisible ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered || PluginManager.appMenuVisible ? Theme.mauve : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    Text {
        anchors.centerIn: parent
        text: "󰣇"
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: root.isHovered || PluginManager.appMenuVisible ? "#ffffff" : Theme.mauve
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: "󰣇"
        iconColor: Theme.mauve
        title: "Application Launcher"
        description: "Search and launch installed applications"
        shortcuts: [
            { action: "Open App Menu", key: "SUPER + Space" },
            { action: "Quick Menu", key: "SUPER + R" },
            { action: "Power Menu", key: "Right Click" }
        ]
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("appmenu");
            } else if (mouse.button === Qt.RightButton) {
                PluginManager.toggle("powermenu");
            }
        }
    }
}
