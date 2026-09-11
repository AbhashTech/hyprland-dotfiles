import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: Math.min(row.implicitWidth + 20, 260)
    radius: Theme.capsuleRadius

    property var barWindow: null
    property string barSection: "left"
    property int barIndex: -1
    property var barContainer: null
    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property string windowTitle: "󰖲 Desktop"
    property string fullTitle: "Desktop"
    property string iconText: "󰖲"

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered && !BarConfig.isDragging
        icon: root.iconText
        iconColor: Theme.accent
        title: root.fullTitle
        description: "Active window controls"
        shortcuts: [
            { action: "Toggle Float", key: "SUPER + V" },
            { action: "Close Window", key: "SUPER + C" },
            { action: "Toggle Fullscreen", key: "SUPER + F" }
        ]
    }

    Process {
        id: titleProc
        command: ["hyprctl", "activewindow", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => {
                titleProc.buffer += data;
            }
        }
        onExited: {
            try {
                var win = JSON.parse(buffer);
                var title = win && win.title ? win.title.trim() : "";
                if (!title) {
                    root.windowTitle = "Desktop";
                    root.fullTitle = "Desktop";
                    root.iconText = "󰖲";
                    buffer = "";
                    return;
                }

                if (title.indexOf("Mozilla Firefox") !== -1) {
                    root.iconText = "󰈹";
                    title = title.replace(" — Mozilla Firefox", "").replace(" - Mozilla Firefox", "");
                } else if (title.indexOf("Kitty") !== -1 || win.class === "kitty") {
                    root.iconText = "󰞷";
                    title = title.replace(" - Kitty", "");
                } else if (title.indexOf("Dolphin") !== -1 || win.class === "dolphin") {
                    root.iconText = "󰉋";
                    title = title.replace(" - Dolphin", "");
                } else if (title.indexOf("Visual Studio Code") !== -1 || win.class === "Code") {
                    root.iconText = "󰨞";
                    title = title.replace(" - Visual Studio Code", "");
                } else {
                    root.iconText = "󰖲";
                }

                root.fullTitle = title;
                if (title.length > 28) {
                    title = title.substring(0, 25) + "...";
                }
                root.windowTitle = title;
            } catch (e) {}
            buffer = "";
        }
    }

    Timer {
        interval: 600
        running: true
        repeat: true
        onTriggered: {
            if (!titleProc.running) titleProc.running = true;
        }
    }

    Process {
        id: ctlProc
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

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
                    BarConfig.startDrag("activewindow", root.barSection, root.barIndex);
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
                ctlProc.exec(["hyprctl", "dispatch hl.dsp.window.float({action = 'toggle'})"]);
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["hyprctl", "dispatch hl.dsp.window.close()"]);
            } else if (mouse.button === Qt.MiddleButton) {
                ctlProc.exec(["hyprctl", "dispatch hl.dsp.window.fullscreen()"]);
            }
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.iconText
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.accent
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.windowTitle
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
            elide: Text.ElideRight
        }
    }
}
