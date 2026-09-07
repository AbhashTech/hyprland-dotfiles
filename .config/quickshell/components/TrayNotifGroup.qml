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
    property int notifCount: 0

    Process {
        id: ctlProc
    }

    Process {
        id: notifCountProc
        command: ["python3", "-c", "import subprocess, json; res = subprocess.run(['makoctl', 'history'], capture_output=True, text=True).stdout; \ntry:\n    data = json.loads(res)\n    count = len(data.get('data', [[]])[0]) if 'data' in data else 0\nexcept Exception:\n    count = 0\nprint(count)"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    root.notifCount = parseInt(data.trim(), 10) || 0;
                } catch (e) {
                    root.notifCount = 0;
                }
            }
        }
    }

    Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!notifCountProc.running) notifCountProc.running = true;
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
                    id: trayItemWrapper
                    required property var modelData
                    width: 18
                    height: 18
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
                        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                        onClicked: mouse => {
                            if (mouse.button === Qt.LeftButton) {
                                modelData.activate();
                            } else if (mouse.button === Qt.RightButton) {
                                if (modelData.hasMenu && modelData.menu) {
                                    modelData.menu.open(trayItemWrapper);
                                } else if (typeof modelData.secondaryActivate === "function") {
                                    modelData.secondaryActivate();
                                }
                            } else if (mouse.button === Qt.MiddleButton && typeof modelData.secondaryActivate === "function") {
                                modelData.secondaryActivate();
                            }
                        }
                    }
                }
            }
        }

        // Clipboard Manager Button (Quickshell Plugin)
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: 20
            implicitHeight: 20
            radius: 4
            color: clipArea.containsMouse || PluginManager.clipboardVisible ? Theme.moduleActiveBg : "transparent"

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
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("clipboard");
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["cliphist", "wipe"]);
                    }
                }
            }
        }

        // Notifications / Mako Button
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: notifRow.implicitWidth + 8
            implicitHeight: 22
            radius: 4
            color: notifArea.containsMouse ? Theme.moduleActiveBg : "transparent"

            Row {
                id: notifRow
                anchors.centerIn: parent
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.notifCount > 0 ? "󱅫" : "󰂚"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: root.notifCount > 0 ? Theme.peach : Theme.accent
                }

                Text {
                    visible: root.notifCount > 0
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.notifCount.toString()
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: Theme.peach
                }
            }

            MouseArea {
                id: notifArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["makoctl", "restore"]);
                        if (!notifCountProc.running) notifCountProc.running = true;
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["makoctl", "dismiss", "-a"]);
                        root.notifCount = 0;
                    }
                }
            }
        }
    }
}
