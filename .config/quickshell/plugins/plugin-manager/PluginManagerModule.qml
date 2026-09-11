import QtQuick
import Quickshell
import Quickshell.Io
import "../../components"
import "../.."
import "."

Rectangle {
    id: root

    property var barWindow: null

    readonly property int totalCount: PluginManagerService.stats.totalCustom || 0
    readonly property int activeCount: PluginManagerService.stats.activeCustom || 0
    readonly property bool isHovered: mouseArea.containsMouse
    readonly property bool isOpen: PluginManager.pluginManagerVisible

    implicitHeight: Theme.barHeight - 8
    implicitWidth: contentRow.implicitWidth + 20
    height: implicitHeight
    width: implicitWidth
    radius: Theme.capsuleRadius

    color: isOpen ? Theme.moduleActiveBg : (isHovered ? Theme.moduleHoverBg : Theme.moduleBg)
    border.color: isOpen ? Theme.accent : (isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder)
    border.width: 1

    Behavior on color { ColorAnimation { duration: 180 } }
    Behavior on border.color { ColorAnimation { duration: 180 } }

    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: 6

        // Puzzle / Plugin Icon
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "󰏓"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeIcon
            color: root.isOpen ? Theme.accent : (root.isHovered ? Theme.yellow : Theme.accent)
        }

        // Active Count
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.activeCount + "/" + root.totalCount
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall + 1
            font.bold: true
            color: Theme.text
        }

        // Status indicator dot
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 6
            height: 6
            radius: 3
            color: root.activeCount > 0 ? Theme.green : Theme.surface2
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        cursorShape: Qt.PointingHandCursor

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("plugin_manager");
            } else if (mouse.button === Qt.RightButton) {
                PluginManagerService.reloadShell();
            } else if (mouse.button === Qt.MiddleButton) {
                PluginManagerService.refresh();
            }
        }
    }
}
