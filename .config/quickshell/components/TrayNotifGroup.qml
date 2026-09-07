import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.SystemTray
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: row.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property string notifIcon: "󰂚"
    property string notifText: ""
    property string clipIcon: "󰅌"

    Process {
        id: notifProc
        command: ["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/notifications.py", "--status"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj && obj.text) {
                        root.notifText = obj.text;
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: ctlProc
    }

    Timer {
        interval: 3000
        running: true
        repeat: true
        onTriggered: {
            if (!notifProc.running) notifProc.running = true;
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 8

        // System Tray Icons
        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            Repeater {
                model: SystemTray.items
                Item {
                    required property var modelData
                    width: 16
                    height: 16
                    anchors.verticalCenter: parent.verticalCenter

                    Image {
                        anchors.fill: parent
                        source: modelData.icon || ""
                        fillMode: Image.PreserveAspectFit
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: mouse => {
                            if (mouse.button === Qt.LeftButton) {
                                modelData.activate();
                            } else if (mouse.button === Qt.RightButton && modelData.hasMenu) {
                                modelData.menu.open();
                            }
                        }
                    }
                }
            }
        }

        // Clipboard Manager Button
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: 20
            implicitHeight: 20
            radius: 4
            color: clipArea.containsMouse ? Theme.moduleActiveBg : "transparent"

            Text {
                anchors.centerIn: parent
                text: "󰅌"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.lavender
            }

            MouseArea {
                id: clipArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/clipboard_manager.py", "--menu"]);
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/clipboard_manager.py", "--delete"]);
                    } else if (mouse.button === Qt.MiddleButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/clipboard_manager.py", "--toggle-pause"]);
                    }
                }
            }
        }

        // Notifications Button
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: notifRow.implicitWidth + 4
            implicitHeight: 20
            radius: 4
            color: notifArea.containsMouse ? Theme.moduleActiveBg : "transparent"

            Row {
                id: notifRow
                anchors.centerIn: parent
                spacing: 3

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.notifText ? root.notifText : "󰂚"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.accent
                }
            }

            MouseArea {
                id: notifArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/notifications.py"]);
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/notifications.py", "--toggle-dnd"]);
                    } else if (mouse.button === Qt.MiddleButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/notifications.py", "--clear"]);
                    }
                }
            }
        }
    }
}
