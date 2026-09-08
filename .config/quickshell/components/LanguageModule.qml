import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property string layoutName: "US"

    implicitHeight: Theme.barHeight - 8
    implicitWidth: row.implicitWidth + 18
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: "󰌌"
        iconColor: Theme.accent
        title: "Keyboard Layout"
        description: "Active Layout: " + root.layoutName
        shortcuts: [
            { action: "Cycle Next Layout", key: "SUPER + ALT + Space" },
            { action: "Layout Switcher Menu", key: "SUPER + SHIFT + K" },
            { action: "Add Regional Layout", key: "SUPER + ALT + K" }
        ]
    }

    Process {
        id: langProc
        command: ["hyprctl", "devices", "-j"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var devs = JSON.parse(data);
                    if (devs && devs.keyboards) {
                        for (var i = 0; i < devs.keyboards.length; i++) {
                            var kb = devs.keyboards[i];
                            if (kb.main) {
                                var act = kb.active_keymap || "";
                                if (act.toLowerCase().indexOf("english") !== -1) {
                                    root.layoutName = "US";
                                } else {
                                    root.layoutName = act.substring(0, 2).toUpperCase();
                                }
                                break;
                            }
                        }
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: ctlProc
    }

    Timer {
        interval: 2000
        running: true
        repeat: true
        onTriggered: {
            if (!langProc.running) langProc.running = true;
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "󰌌"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.accent
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.layoutName
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
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
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/keyboard_layout.py", "--next"]);
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/keyboard_layout.py", "--menu"]);
            } else if (mouse.button === Qt.MiddleButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/keyboard_layout.py", "--add-menu"]);
            }
        }
    }
}
