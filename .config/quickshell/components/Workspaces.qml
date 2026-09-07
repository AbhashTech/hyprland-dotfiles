import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: row.implicitWidth + 8
    radius: Theme.capsuleRadius

    color: Theme.moduleBg
    border.color: Theme.moduleBorder
    border.width: 1

    property int activeWorkspaceId: 1
    property var activeIds: [1]

    Process {
        id: hyprWsProc
        command: ["hyprctl", "workspaces", "-j"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var wsList = JSON.parse(data);
                    var ids = [];
                    for (var i = 0; i < wsList.length; i++) {
                        ids.push(wsList[i].id);
                    }
                    root.activeIds = ids;
                } catch (e) {}
            }
        }
    }

    Process {
        id: hyprActiveWsProc
        command: ["hyprctl", "activeworkspace", "-j"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var ws = JSON.parse(data);
                    if (ws && ws.id) {
                        root.activeWorkspaceId = ws.id;
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: dispatchProc
    }

    Timer {
        interval: 200
        running: true
        repeat: true
        onTriggered: {
            if (!hyprWsProc.running) hyprWsProc.running = true;
            if (!hyprActiveWsProc.running) hyprActiveWsProc.running = true;
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 4

        Repeater {
            model: [1, 2, 3, 4]

            Rectangle {
                id: wsBtn
                readonly property int wsNum: modelData
                readonly property bool isActive: root.activeWorkspaceId === wsNum
                readonly property bool isOccupied: root.activeIds.indexOf(wsNum) !== -1

                implicitHeight: Theme.barHeight - 16
                implicitWidth: isActive ? 28 : 24
                radius: Theme.pillRadius

                color: isActive ? Theme.blue : (btnArea.containsMouse ? Theme.moduleActiveBg : "transparent")
                border.color: "transparent"
                border.width: 1

                Behavior on implicitWidth { NumberAnimation { duration: 150 } }
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: wsNum.toString()
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: isActive ? "#ffffff" : (btnArea.containsMouse ? Theme.text : (isOccupied ? Theme.text : Theme.subtext0))
                }

                MouseArea {
                    id: btnArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        dispatchProc.exec(["hyprctl", "dispatch", "hl.dsp.focus", "{ workspace = " + wsNum + " }"]);
                        root.activeWorkspaceId = wsNum;
                    }
                }
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onWheel: wheel => {
            if (wheel.angleDelta.y > 0) {
                dispatchProc.exec(["hyprctl", "dispatch", "hl.dsp.focus", "{ workspace = \"e-1\" }"]);
            } else if (wheel.angleDelta.y < 0) {
                dispatchProc.exec(["hyprctl", "dispatch", "hl.dsp.focus", "{ workspace = \"e+1\" }"]);
            }
        }
    }
}
