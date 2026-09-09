import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 820
    implicitHeight: 520
    radius: 16
    color: Theme.base
    border.color: Theme.surface1
    border.width: 1

    property var allWorkspaces: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    property var activeIds: [1]
    property int activeWorkspaceId: 1
    property var allClients: [] // Array of all clients from hyprctl clients -j
    property var monitorsList: []
    property string searchQuery: ""

    function cleanAddress(addr) {
        if (!addr) return "none";
        return addr.toString().replace(/^0x/, "");
    }

    function getMonitorForClient(client) {
        if (!root.monitorsList || root.monitorsList.length === 0) {
            return { x: 0, y: 0, width: 1920, height: 1080 };
        }
        if (client.monitor !== undefined) {
            for (var i = 0; i < root.monitorsList.length; i++) {
                var m = root.monitorsList[i];
                if (m.id === client.monitor || m.name === client.monitor) {
                    return m;
                }
            }
        }
        var rawX = (client.at && client.at.length > 0) ? client.at[0] : 0;
        for (var j = 0; j < root.monitorsList.length; j++) {
            var mon = root.monitorsList[j];
            if (rawX >= mon.x && rawX < (mon.x + (mon.width || 1920))) {
                return mon;
            }
        }
        return root.monitorsList[0] || { x: 0, y: 0, width: 1920, height: 1080 };
    }

    function grabFocus() {
        if (!hyprMonitorsProc.running) hyprMonitorsProc.running = true;
        captureProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/workspace_viewer/window_preview_capture.py", "capture-now"]);
        searchInput.forceActiveFocus();
    }

    function getAppIcon(appClass, appTitle) {
        var c = (appClass || "").toLowerCase();
        var t = (appTitle || "").toLowerCase();

        if (c.indexOf("firefox") !== -1 || c.indexOf("zen") !== -1 || c.indexOf("librewolf") !== -1 || c.indexOf("waterfox") !== -1) return "󰈹";
        if (c.indexOf("chrome") !== -1 || c.indexOf("chromium") !== -1 || c.indexOf("brave") !== -1 || c.indexOf("edge") !== -1) return "󰊯";
        if (c.indexOf("kitty") !== -1 || c.indexOf("alacritty") !== -1 || c.indexOf("foot") !== -1 || c.indexOf("wezterm") !== -1 || c.indexOf("terminal") !== -1 || c.indexOf("konsole") !== -1) return "󰄛";
        if (c.indexOf("dolphin") !== -1 || c.indexOf("nautilus") !== -1 || c.indexOf("thunar") !== -1 || c.indexOf("nemo") !== -1 || c.indexOf("yazi") !== -1) return "󰉋";
        if (c.indexOf("code") !== -1 || c.indexOf("vscodium") !== -1 || c.indexOf("cursor") !== -1 || c.indexOf("nvim") !== -1 || c.indexOf("kate") !== -1 || c.indexOf("kwrite") !== -1) return "󰨞";
        if (c.indexOf("discord") !== -1 || c.indexOf("vesktop") !== -1 || c.indexOf("webcord") !== -1) return "󰙯";
        if (c.indexOf("telegram") !== -1) return "󰈰";
        if (c.indexOf("spotify") !== -1) return "󰓇";
        if (c.indexOf("obsidian") !== -1) return "󰎚";
        if (c.indexOf("slack") !== -1) return "󰒱";
        if (c.indexOf("steam") !== -1) return "󰓓";
        if (c.indexOf("gimp") !== -1 || c.indexOf("inkscape") !== -1 || c.indexOf("krita") !== -1 || c.indexOf("blender") !== -1) return "󰽉";
        if (c.indexOf("mpv") !== -1 || c.indexOf("vlc") !== -1 || c.indexOf("celluloid") !== -1) return "󰕼";
        if (c.indexOf("btop") !== -1 || c.indexOf("htop") !== -1) return "󰍛";
        if (c.indexOf("swappy") !== -1) return "󰹑";
        if (c.indexOf("lazygit") !== -1) return "󰊢";
        if (c.indexOf("lazydocker") !== -1) return "󰡨";
        if (c.indexOf("zathura") !== -1 || c.indexOf("evince") !== -1 || c.indexOf("okular") !== -1) return "󰈦";
        if (c.indexOf("libreoffice") !== -1) return "󰏫";

        return "󰖲";
    }

    function getAppColor(appClass) {
        var c = (appClass || "").toLowerCase();
        if (c.indexOf("firefox") !== -1) return Theme.peach;
        if (c.indexOf("chrome") !== -1 || c.indexOf("brave") !== -1) return Theme.yellow;
        if (c.indexOf("kitty") !== -1 || c.indexOf("terminal") !== -1) return Theme.green;
        if (c.indexOf("dolphin") !== -1 || c.indexOf("nautilus") !== -1) return Theme.blue;
        if (c.indexOf("code") !== -1 || c.indexOf("vscodium") !== -1) return Theme.sapphire;
        if (c.indexOf("discord") !== -1) return Theme.lavender;
        if (c.indexOf("spotify") !== -1) return Theme.green;
        if (c.indexOf("telegram") !== -1) return Theme.teal;
        if (c.indexOf("obsidian") !== -1) return Theme.mauve;
        return Theme.accent;
    }

    function getClientsForWs(wsId) {
        var list = [];
        for (var i = 0; i < root.allClients.length; i++) {
            var c = root.allClients[i];
            if (c.workspace && c.workspace.id === wsId) {
                if (root.searchQuery.trim() === "") {
                    list.push(c);
                } else {
                    var q = root.searchQuery.toLowerCase();
                    var titleMatch = c.title && c.title.toLowerCase().indexOf(q) !== -1;
                    var classMatch = c.class && c.class.toLowerCase().indexOf(q) !== -1;
                    if (titleMatch || classMatch) {
                        list.push(c);
                    }
                }
            }
        }
        return list;
    }

    // Hyprland Processes
    Process {
        id: hyprWsProc
        command: ["hyprctl", "workspaces", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => { hyprWsProc.buffer += data; }
        }
        onExited: {
            try {
                var wsList = JSON.parse(buffer);
                var ids = [];
                var maxId = 4;
                for (var i = 0; i < wsList.length; i++) {
                    ids.push(wsList[i].id);
                    if (wsList[i].id > maxId) maxId = wsList[i].id;
                }
                root.activeIds = ids;
                var all = [];
                for (var n = 1; n <= Math.max(maxId, 6); n++) {
                    all.push(n);
                }
                root.allWorkspaces = all;
            } catch (e) {}
            buffer = "";
        }
    }

    Process {
        id: hyprActiveWsProc
        command: ["hyprctl", "activeworkspace", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => { hyprActiveWsProc.buffer += data; }
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
            onRead: data => { hyprClientsProc.buffer += data; }
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

    Process {
        id: captureProc
    }

    Process {
        id: hyprMonitorsProc
        command: ["hyprctl", "monitors", "-j"]
        property string buffer: ""
        stdout: SplitParser {
            onRead: data => { hyprMonitorsProc.buffer += data; }
        }
        onExited: {
            try {
                root.monitorsList = JSON.parse(buffer) || [];
            } catch (e) {}
            buffer = "";
        }
    }

    Timer {
        interval: 250
        running: PluginManager.workspaceViewerVisible
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!hyprWsProc.running) hyprWsProc.running = true;
            if (!hyprActiveWsProc.running) hyprActiveWsProc.running = true;
            if (!hyprClientsProc.running) hyprClientsProc.running = true;
            if (!hyprMonitorsProc.running) hyprMonitorsProc.running = true;
        }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14

        // Top Navigation Bar
        Row {
            width: parent.width
            spacing: 12

            // Icon + Title
            Row {
                spacing: 8
                anchors.verticalCenter: parent.verticalCenter

                Text {
                    text: "󰮯"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge + 3
                    color: Theme.blue
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: "Workspace Overview"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    color: Theme.text
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Search Bar
            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 320
                height: 36
                radius: 10
                color: Theme.surface0
                border.color: searchInput.activeFocus ? Theme.blue : Theme.surface1
                border.width: 1

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 8

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "󰍉"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.subtext0
                    }

                    TextInput {
                        id: searchInput
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width - 30
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        clip: true
                        onTextChanged: {
                            root.searchQuery = text;
                        }
                        Keys.onEscapePressed: {
                            PluginManager.closeAll();
                        }
                    }
                }

                Text {
                    visible: searchInput.text.length === 0
                    anchors.left: parent.left
                    anchors.leftMargin: 32
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Search open windows across workspaces..."
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.overlay0
                }
            }

            Item {
                width: 1
                height: 1
                // spacer
            }

            // Close button
            Rectangle {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                implicitWidth: 32
                implicitHeight: 32
                radius: 8
                color: closeMa.containsMouse ? Theme.surface1 : Theme.surface0
                border.color: Theme.surface1
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰅖"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    color: closeMa.containsMouse ? Theme.red : Theme.subtext0
                }

                MouseArea {
                    id: closeMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManager.closeAll()
                }
            }
        }

        // Divider
        Rectangle {
            width: parent.width
            height: 1
            color: Theme.surface1
        }

        // Workspaces Grid
        Flickable {
            width: parent.width
            height: parent.height - 80
            contentHeight: wsGrid.implicitHeight + 16
            clip: true

            Grid {
                id: wsGrid
                width: parent.width
                columns: 3
                spacing: 12

                Repeater {
                    model: root.allWorkspaces

                    Rectangle {
                        id: wsCard
                        readonly property int wsId: modelData
                        readonly property bool isActive: root.activeWorkspaceId === wsId
                        readonly property var clients: root.getClientsForWs(wsId)

                        width: (wsGrid.width - 24) / 3
                        implicitHeight: 180
                        radius: 12
                        color: cardMa.containsMouse ? Theme.surface0 : Theme.mantle
                        border.color: isActive ? Theme.blue : (cardMa.containsMouse ? Theme.surface2 : Theme.surface1)
                        border.width: isActive ? 2 : 1

                        Behavior on color { ColorAnimation { duration: 120 } }
                        Behavior on border.color { ColorAnimation { duration: 120 } }

                        Column {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            // Header inside Card
                            Row {
                                width: parent.width
                                spacing: 6

                                Rectangle {
                                    implicitWidth: 22
                                    implicitHeight: 22
                                    radius: 6
                                    color: isActive ? Theme.blue : Theme.surface1
                                    anchors.verticalCenter: parent.verticalCenter

                                    Text {
                                        anchors.centerIn: parent
                                        text: wsId.toString()
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: true
                                        color: isActive ? "#ffffff" : Theme.text
                                    }
                                }

                                Text {
                                    text: "Workspace " + wsId
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.text
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Item {
                                    width: 1
                                    height: 1
                                }

                                Rectangle {
                                    visible: isActive
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    implicitWidth: activeLabel.implicitWidth + 8
                                    implicitHeight: 18
                                    radius: 9
                                    color: Qt.rgba(Theme.blue.r, Theme.blue.g, Theme.blue.b, 0.2)
                                    border.color: Theme.blue
                                    border.width: 1

                                    Text {
                                        id: activeLabel
                                        anchors.centerIn: parent
                                        text: "Active"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 9
                                        font.bold: true
                                        color: Theme.blue
                                    }
                                }
                            }

                            // Layout Wireframe Thumbnail
                            Rectangle {
                                id: cardWireframe
                                width: parent.width
                                height: 75
                                radius: 6
                                color: Theme.crust
                                border.color: Theme.surface1
                                border.width: 1
                                clip: true

                                Text {
                                    visible: clients.length === 0
                                    anchors.centerIn: parent
                                    text: "Empty"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    color: Theme.overlay0
                                }

                                Repeater {
                                    model: clients

                                    Rectangle {
                                        readonly property var client: modelData
                                        readonly property var mon: root.getMonitorForClient(client)
                                        readonly property real monX: (mon && mon.x !== undefined) ? mon.x : 0
                                        readonly property real monY: (mon && mon.y !== undefined) ? mon.y : 0
                                        readonly property real monW: (mon && mon.width && mon.width > 0) ? mon.width : 1920.0
                                        readonly property real monH: (mon && mon.height && mon.height > 0) ? mon.height : 1080.0
                                        readonly property real p: 4

                                        readonly property real canvasW: Math.max(10, cardWireframe.width - 2 * p)
                                        readonly property real canvasH: Math.max(10, cardWireframe.height - 2 * p)

                                        readonly property real rawX: (client.at && client.at.length > 0) ? client.at[0] : 0
                                        readonly property real rawY: (client.at && client.at.length > 1) ? client.at[1] : 0
                                        readonly property real rawW: (client.size && client.size.length > 0) ? client.size[0] : monW
                                        readonly property real rawH: (client.size && client.size.length > 1) ? client.size[1] : (monH - 50)

                                        readonly property real relX: Math.max(0, rawX - monX)
                                        readonly property real relY: Math.max(0, rawY - monY)

                                        readonly property real normX: Math.max(0.0, Math.min(0.92, relX / monW))
                                        readonly property real normY: Math.max(0.0, Math.min(0.92, relY / monH))
                                        readonly property real normW: Math.max(0.06, Math.min(1.0 - normX, rawW / monW))
                                        readonly property real normH: Math.max(0.06, Math.min(1.0 - normY, rawH / monH))

                                        x: p + Math.round(normX * canvasW)
                                        y: p + Math.round(normY * canvasH)
                                        width: Math.max(16, Math.min(canvasW - (x - p), Math.round(normW * canvasW)))
                                        height: Math.max(14, Math.min(canvasH - (y - p), Math.round(normH * canvasH)))
                                        radius: 3

                                        color: Theme.mantle
                                        border.color: root.getAppColor(client.class)
                                        border.width: 1
                                        clip: true

                                        // Actual application screenshot image
                                        Image {
                                            id: snapImg
                                            anchors.fill: parent
                                            anchors.margins: 1
                                            source: "file://" + Quickshell.env("HOME") + "/.cache/quickshell/window_previews/" + root.cleanAddress(client.address) + ".png"
                                            sourceSize: Qt.size(240, 135)
                                            fillMode: Image.PreserveAspectCrop
                                            smooth: true
                                            asynchronous: true
                                            visible: status === Image.Ready
                                            opacity: 0.92
                                        }

                                        // Simulated interface when image is loading
                                        Item {
                                            anchors.fill: parent
                                            visible: snapImg.status !== Image.Ready

                                            Column {
                                                anchors.fill: parent

                                                Rectangle {
                                                    width: parent.width
                                                    height: Math.max(5, Math.min(10, parent.height * 0.2))
                                                    color: Qt.rgba(root.getAppColor(client.class).r, root.getAppColor(client.class).g, root.getAppColor(client.class).b, 0.3)
                                                }

                                                Rectangle {
                                                    width: parent.width
                                                    height: parent.height - Math.max(5, Math.min(10, parent.height * 0.2))
                                                    color: Theme.surface0

                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: root.getAppIcon(client.class, client.title)
                                                        font.family: Theme.fontFamily
                                                        font.pixelSize: 8
                                                        color: root.getAppColor(client.class)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            // Running App Badges Row
                            Row {
                                width: parent.width
                                spacing: 4
                                clip: true

                                Repeater {
                                    model: clients.slice(0, 5)

                                    Rectangle {
                                        implicitWidth: 24
                                        implicitHeight: 24
                                        radius: 5
                                        color: Theme.surface1
                                        border.color: Theme.surface2
                                        border.width: 1

                                        Text {
                                            anchors.centerIn: parent
                                            text: root.getAppIcon(modelData.class, modelData.title)
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            color: root.getAppColor(modelData.class)
                                        }
                                    }
                                }

                                Text {
                                    visible: clients.length > 5
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "+" + (clients.length - 5)
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    color: Theme.subtext0
                                }
                            }
                        }

                        MouseArea {
                            id: cardMa
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                dispatchProc.exec(["bash", "-c", "hyprctl dispatch workspace " + wsId + " 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({workspace = " + wsId + "})' 2>/dev/null || hyprctl dispatch focusworkspaceoncurrentmonitor " + wsId]);
                                PluginManager.closeAll();
                            }
                        }
                    }
                }
            }
        }
    }
}
