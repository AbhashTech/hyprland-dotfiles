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
    property var allClients: []
    readonly property bool isHovered: wheelMa.containsMouse

    function getClientsForWs(wsId) {
        var list = [];
        for (var i = 0; i < root.allClients.length; i++) {
            var c = root.allClients[i];
            if (c.workspace && c.workspace.id === wsId) {
                list.push(c);
            }
        }
        return list;
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
        id: hyprClientsProc
        command: ["hyprctl", "clients", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => {
                hyprClientsProc.buffer += data;
            }
        }
        onExited: {
            try {
                var list = JSON.parse(buffer);
                root.allClients = list || [];
            } catch (e) {}
            buffer = "";
        }
    }

    Process {
        id: dispatchProc
    }

    function focusWorkspace(wsId) {
        root.activeWorkspaceId = wsId;
        dispatchProc.exec(["bash", "-c", "hyprctl dispatch workspace " + wsId + " 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({workspace = " + wsId + "})' 2>/dev/null || hyprctl dispatch focusworkspaceoncurrentmonitor " + wsId]);
    }

    function scrollWorkspace(delta) {
        var arg = delta > 0 ? "e-1" : "e+1";
        var luaArg = delta > 0 ? "'e-1'" : "'e+1'";
        dispatchProc.exec(["bash", "-c", "hyprctl dispatch workspace " + arg + " 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({workspace = " + luaArg + "})' 2>/dev/null"]);
    }

    Timer {
        interval: 200
        running: true
        repeat: true
        onTriggered: {
            if (!hyprWsProc.running) hyprWsProc.running = true;
            if (!hyprActiveWsProc.running) hyprActiveWsProc.running = true;
            if (!hyprClientsProc.running) hyprClientsProc.running = true;
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

                WorkspacePreviewPopup {
                    barWindow: root.barWindow
                    targetItem: wsBtn
                    isHovered: btnArea.containsMouse
                    workspaceId: wsBtn.wsNum
                    isActiveWs: wsBtn.isActive
                    clientsList: root.getClientsForWs(wsBtn.wsNum)
                }

                MouseArea {
                    id: btnArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: mouse => {
                        if (mouse.button === Qt.LeftButton) {
                            root.focusWorkspace(wsNum);
                        } else if (mouse.button === Qt.RightButton) {
                            PluginManager.toggle("workspaces");
                        }
                    }
                }
            }
        }
    }
}
