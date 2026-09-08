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

    property var barWindow: null
    property int activeWorkspaceId: 1
    property var activeIds: [1]
    readonly property bool isHovered: wheelMa.containsMouse

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: "󰮯"
        iconColor: Theme.blue
        title: "Workspaces"
        description: "Hyprland virtual workspaces"
        shortcuts: [
            { action: "Switch Workspace", key: "SUPER + 1..0" },
            { action: "Move Window", key: "SUPER + SHIFT + 1..0" },
            { action: "Cycle Workspaces", key: "SUPER + Scroll" }
        ]
    }

    readonly property var workspaceList: {
        var defaultCount = 4;
        var maxId = defaultCount;
        if (root.activeWorkspaceId > maxId) {
            maxId = root.activeWorkspaceId;
        }
        for (var i = 0; i < root.activeIds.length; i++) {
            if (root.activeIds[i] > maxId) {
                maxId = root.activeIds[i];
            }
        }
        var list = [];
        for (var n = 1; n <= maxId; n++) {
            list.push(n);
        }
        return list;
    }

    Process {
        id: hyprWsProc
        command: ["hyprctl", "workspaces", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => {
                hyprWsProc.buffer += data;
            }
        }
        onExited: {
            try {
                var wsList = JSON.parse(buffer);
                var ids = [];
                for (var i = 0; i < wsList.length; i++) {
                    ids.push(wsList[i].id);
                }
                root.activeIds = ids;
            } catch (e) {}
            buffer = "";
        }
    }

    Process {
        id: hyprActiveWsProc
        command: ["hyprctl", "activeworkspace", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => {
                hyprActiveWsProc.buffer += data;
            }
        }
        onExited: {
            try {
                var ws = JSON.parse(buffer);
                if (ws && ws.id) {
                    root.activeWorkspaceId = ws.id;
                }
            } catch (e) {}
            buffer = "";
        }
    }

    Process {
        id: dispatchProc
    }

    function focusWorkspace(wsId) {
        root.activeWorkspaceId = wsId;
        dispatchProc.exec(["hyprctl", "dispatch hl.dsp.focus({workspace = " + wsId + "})"]);
    }

    function scrollWorkspace(delta) {
        var arg = delta > 0 ? "'e-1'" : "'e+1'";
        dispatchProc.exec(["hyprctl", "dispatch hl.dsp.focus({workspace = " + arg + "})"]);
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

    // Wheel area underneath the row
    MouseArea {
        id: wheelMa
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onWheel: wheel => {
            root.scrollWorkspace(wheel.angleDelta.y);
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 4

        Repeater {
            model: root.workspaceList

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
                        root.focusWorkspace(wsNum);
                    }
                }
            }
        }
    }
}
