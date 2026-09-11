import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Item {
    id: root

    property bool isOpen: false
    property real menuX: 0
    property real menuY: 0

    function showAt(targetX, targetY) {
        menuX = Math.min(Math.max(10, targetX), (parent ? parent.width - menuBox.width - 10 : targetX));
        menuY = targetY;
        isOpen = true;
    }

    function close() {
        isOpen = false;
    }

    // Dismiss backdrop
    MouseArea {
        anchors.fill: parent
        enabled: root.isOpen
        z: 99
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: root.close()
    }

    Rectangle {
        id: menuBox
        visible: root.isOpen
        x: root.menuX
        y: root.menuY + 6
        z: 100
        width: 220
        height: menuCol.implicitHeight + 16
        radius: Theme.barRadius
        color: Theme.tooltipBg
        border.color: Theme.accent
        border.width: 1

        scale: root.isOpen ? 1.0 : 0.85
        opacity: root.isOpen ? 1.0 : 0.0

        Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutQuad } }
        Behavior on opacity { NumberAnimation { duration: 120 } }

        Column {
            id: menuCol
            anchors.centerIn: parent
            width: parent.width - 12
            spacing: 3

            // Header
            Text {
                text: "BAR CONTROLS"
                font.family: Theme.fontFamily
                font.pixelSize: 10
                font.bold: true
                color: Theme.subtext0
                leftPadding: 8
                topPadding: 4
                bottomPadding: 2
            }

            // Customize Bar
            MenuItem {
                icon: "󰏖"
                iconColor: Theme.mauve
                title: "Customize Layout..."
                shortcut: "SUPER + ALT + B"
                onTriggered: {
                    root.close();
                    PluginManager.toggle("bar_customizer");
                }
            }

            // Toggle Edit Mode
            MenuItem {
                icon: BarConfig.editMode ? "󰅙" : "✏"
                iconColor: BarConfig.editMode ? Theme.red : Theme.teal
                title: BarConfig.editMode ? "Exit Edit Mode" : "Interactive Edit Mode"
                shortcut: "Live Drag"
                onTriggered: {
                    root.close();
                    BarConfig.toggleEditMode();
                }
            }

            // Separator
            Rectangle {
                width: parent.width - 16
                height: 1
                color: Theme.surface0
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Bar Position Toggle
            MenuItem {
                icon: "󰆊"
                iconColor: Theme.blue
                title: BarConfig.isTop ? "Position: Move to Bottom" : "Position: Move to Top"
                onTriggered: {
                    root.close();
                    BarConfig.setBarPosition(BarConfig.isTop ? "bottom" : "top");
                }
            }

            // Reset Defaults
            MenuItem {
                icon: "󰕑"
                iconColor: Theme.yellow
                title: "Reset Layout Defaults"
                onTriggered: {
                    root.close();
                    BarConfig.resetToDefaults();
                }
            }

            // Reload Quickshell
            MenuItem {
                icon: "󰑓"
                iconColor: Theme.green
                title: "Reload Shell"
                onTriggered: {
                    root.close();
                    reloadProc.exec(["bash", "-c", Quickshell.env("HOME") + "/.config/quickshell/scripts/launch_quickshell.sh --restart"]);
                }
            }
        }
    }

    Process {
        id: reloadProc
    }

    component MenuItem: Rectangle {
        id: itemRoot
        property string icon: ""
        property color iconColor: Theme.accent
        property string title: ""
        property string shortcut: ""
        signal triggered()

        width: parent ? parent.width : 200
        height: 28
        radius: Theme.pillRadius
        color: itemArea.containsMouse ? Theme.moduleHoverBg : "transparent"

        Row {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 8
            spacing: 8

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: itemRoot.icon
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: itemRoot.iconColor
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: itemRoot.title
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: Theme.text
            }
        }

        Text {
            visible: itemRoot.shortcut !== ""
            anchors.right: parent.right
            anchors.rightMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            text: itemRoot.shortcut
            font.family: Theme.fontFamily
            font.pixelSize: 9
            color: Theme.subtext0
        }

        MouseArea {
            id: itemArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: itemRoot.triggered()
        }
    }
}
