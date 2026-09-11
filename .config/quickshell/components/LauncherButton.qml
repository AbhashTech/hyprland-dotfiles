import QtQuick
import Quickshell
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 32
    radius: Theme.capsuleRadius

    property var barWindow: null
    property string barSection: "left"
    property int barIndex: -1
    property var barContainer: null
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
        isHovered: root.isHovered && !BarConfig.isDragging
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
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor

        property real pressX: 0
        property real pressY: 0
        property bool didDrag: false

        onPressed: mouse => {
            pressX = mouse.x;
            pressY = mouse.y;
            didDrag = false;
        }

        onPositionChanged: mouse => {
            if (pressed && mouse.buttons === Qt.LeftButton) {
                var dx = mouse.x - pressX;
                var dy = mouse.y - pressY;
                if (!didDrag && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
                    didDrag = true;
                    BarConfig.startDrag("launcher", root.barSection, root.barIndex);
                }
                if (didDrag && root.barContainer) {
                    var pt = mapToItem(root.barContainer, mouse.x, mouse.y);
                    BarConfig.updateDragPos(pt.x, root.barContainer.width);
                }
            }
        }

        onReleased: mouse => {
            if (didDrag) {
                BarConfig.endDrag();
                didDrag = false;
            } else if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("appmenu");
            } else if (mouse.button === Qt.RightButton) {
                PluginManager.toggle("powermenu");
            }
        }
    }
}
