import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 470
    implicitHeight: 560
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    readonly property string scriptPath: Quickshell.env("HOME") + "/.config/quickshell/plugins/connectivity/wireless_ctl.py"

    // Active tab: "wifi" or "bluetooth"
    property string activeTab: PluginManager.connectivityTab || "wifi"

    // WiFi State
    property bool wifiPowered: true
    property bool wifiConnected: false
    property string wifiSsid: ""
    property int wifiSignal: 0
    property string wifiIp: ""
    property string wifiSecurity: ""
    property var wifiNetworks: []
    property bool wifiScanning: false
    property string selectedWifiSsid: ""
    property string wifiPasswordInput: ""
    property bool showWifiPassword: false
    property string wifiSearchText: ""

    // Bluetooth State
    property bool btPowered: false
    property bool btDiscovering: false
    property int btConnectedCount: 0
    property var btDevices: []
    property var btDiscovered: []

    // Refresh timers & functions
    function refreshWifi() {
        if (!wifiProc.running) wifiProc.running = true;
    }

    function refreshBluetooth() {
        if (!btProc.running) btProc.running = true;
    }

    function refreshAll() {
        refreshWifi();
        refreshBluetooth();
    }

    function triggerWifiScan() {
        root.wifiScanning = true;
        wifiScanProc.running = true;
    }

    function toggleWifiPower() {
        ctlProc.exec(["python3", root.scriptPath, "wifi-toggle"]);
        scanDelayTimer.restart();
    }

    function connectWifi(ssid, password) {
        var pwd = password ? password : "NONE";
        ctlProc.exec(["python3", root.scriptPath, "wifi-connect", ssid, pwd]);
        root.selectedWifiSsid = "";
        root.wifiPasswordInput = "";
        scanDelayTimer.restart();
    }

    function disconnectWifi() {
        ctlProc.exec(["python3", root.scriptPath, "wifi-disconnect"]);
        scanDelayTimer.restart();
    }

    function forgetWifi(ssid) {
        ctlProc.exec(["python3", root.scriptPath, "wifi-forget", ssid]);
        scanDelayTimer.restart();
    }

    function toggleBtPower() {
        ctlProc.exec(["python3", root.scriptPath, "bt-toggle"]);
        scanDelayTimer.restart();
    }

    function toggleBtScan() {
        ctlProc.exec(["python3", root.scriptPath, "bt-scan-toggle"]);
        scanDelayTimer.restart();
    }

    function connectBt(mac) {
        ctlProc.exec(["python3", root.scriptPath, "bt-connect", mac]);
        scanDelayTimer.restart();
    }

    function disconnectBt(mac) {
        ctlProc.exec(["python3", root.scriptPath, "bt-disconnect", mac]);
        scanDelayTimer.restart();
    }

    function pairBt(mac) {
        ctlProc.exec(["python3", root.scriptPath, "bt-pair", mac]);
        scanDelayTimer.restart();
    }

    function removeBt(mac) {
        ctlProc.exec(["python3", root.scriptPath, "bt-remove", mac]);
        scanDelayTimer.restart();
    }

    Timer {
        id: scanDelayTimer
        interval: 800
        repeat: false
        onTriggered: root.refreshAll()
    }

    Timer {
        id: pollTimer
        interval: 3500
        running: PluginManager.connectivityVisible
        repeat: true
        onTriggered: {
            if (root.activeTab === "wifi") {
                root.refreshWifi();
            } else {
                root.refreshBluetooth();
            }
        }
    }

    Process {
        id: ctlProc
    }

    Process {
        id: wifiScanProc
        command: ["python3", root.scriptPath, "wifi-scan"]
        stdout: SplitParser {
            onRead: data => {
                root.wifiScanning = false;
                try {
                    var obj = JSON.parse(data);
                    root.updateWifiData(obj);
                } catch (e) {}
            }
        }
    }

    Process {
        id: wifiProc
        command: ["python3", root.scriptPath, "status-wifi"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.updateWifiData(obj);
                } catch (e) {}
            }
        }
    }

    function updateWifiData(obj) {
        if (!obj) return;
        root.wifiPowered = obj.powered;
        root.wifiConnected = obj.connected;
        root.wifiSsid = obj.ssid || "";
        root.wifiSignal = obj.signal || 0;
        root.wifiIp = obj.ip || "";
        root.wifiSecurity = obj.security || "";
        root.wifiNetworks = obj.networks || [];
    }

    Process {
        id: btProc
        command: ["python3", root.scriptPath, "status-bt"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.btPowered = obj.powered;
                    root.btDiscovering = obj.discovering;
                    root.btConnectedCount = obj.connected_count || 0;
                    root.btDevices = obj.devices || [];
                    root.btDiscovered = obj.discovered || [];
                } catch (e) {}
            }
        }
    }

    focus: true
    Keys.onEscapePressed: event => {
        PluginManager.closeAll();
        event.accepted = true;
    }

    function grabFocus() {
        root.forceActiveFocus();
        root.activeTab = PluginManager.connectivityTab || "wifi";
        root.refreshAll();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onConnectivityVisibleChanged() {
            if (PluginManager.connectivityVisible) {
                root.grabFocus();
            }
        }
        function onConnectivityTabChanged() {
            root.activeTab = PluginManager.connectivityTab;
            if (root.activeTab === "wifi") root.refreshWifi();
            else root.refreshBluetooth();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Top Header
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "󰢮 Wireless & Connectivity"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            // Close button
            Rectangle {
                implicitWidth: 26
                implicitHeight: 26
                radius: 13
                color: closeHover.containsMouse ? Theme.red : Theme.surface0

                Text {
                    anchors.centerIn: parent
                    text: "󰅖"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: closeHover.containsMouse ? "#ffffff" : Theme.text
                }

                MouseArea {
                    id: closeHover
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManager.closeAll()
                }
            }
        }

        // Segmented Tab Switcher: [ Wi-Fi ]  [ Bluetooth ]
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 38
            radius: Theme.pillRadius
            color: Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 3
                spacing: 4

                // WiFi Tab Button
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: Theme.pillRadius - 2
                    color: root.activeTab === "wifi" ? Theme.accent : (wifiTabHover.containsMouse ? Theme.surface1 : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Text {
                            text: root.wifiConnected ? "󰤨" : (root.wifiPowered ? "󰤟" : "󰤭")
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: root.activeTab === "wifi" ? Theme.mantle : Theme.text
                            font.bold: true
                        }

                        Text {
                            text: "Wi-Fi" + (root.wifiConnected ? " (" + root.wifiSsid + ")" : "")
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: root.activeTab === "wifi"
                            color: root.activeTab === "wifi" ? Theme.mantle : Theme.text
                            elide: Text.ElideRight
                            Layout.maximumWidth: 160
                        }
                    }

                    MouseArea {
                        id: wifiTabHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeTab = "wifi";
                            PluginManager.connectivityTab = "wifi";
                            root.refreshWifi();
                        }
                    }
                }

                // Bluetooth Tab Button
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: Theme.pillRadius - 2
                    color: root.activeTab === "bluetooth" ? Theme.accent : (btTabHover.containsMouse ? Theme.surface1 : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Text {
                            text: root.btConnectedCount > 0 ? "󰂱" : (root.btPowered ? "󰂯" : "󰂲")
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: root.activeTab === "bluetooth" ? Theme.mantle : Theme.text
                            font.bold: true
                        }

                        Text {
                            text: "Bluetooth" + (root.btConnectedCount > 0 ? " (" + root.btConnectedCount + ")" : "")
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: root.activeTab === "bluetooth"
                            color: root.activeTab === "bluetooth" ? Theme.mantle : Theme.text
                            elide: Text.ElideRight
                            Layout.maximumWidth: 160
                        }
                    }

                    MouseArea {
                        id: btTabHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeTab = "bluetooth";
                            PluginManager.connectivityTab = "bluetooth";
                            root.refreshBluetooth();
                        }
                    }
                }
            }
        }

        // ==========================================
        // WI-FI VIEW
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.activeTab === "wifi"
            spacing: 10

            // Subheader: Power Switch & Scan Button
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                // Power Toggle Pill
                Rectangle {
                    implicitWidth: 130
                    implicitHeight: 34
                    radius: Theme.pillRadius
                    color: root.wifiPowered ? Theme.surface1 : Theme.surface0
                    border.color: root.wifiPowered ? Theme.teal : Theme.moduleBorder
                    border.width: 1

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: root.wifiPowered ? "󰤨" : "󰤭"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: root.wifiPowered ? Theme.teal : Theme.overlay0
                        }

                        Text {
                            text: root.wifiPowered ? "Wi-Fi On" : "Wi-Fi Off"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: root.wifiPowered ? Theme.text : Theme.overlay0
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleWifiPower()
                    }
                }

                Item { Layout.fillWidth: true }

                // Rescan Button
                Rectangle {
                    implicitWidth: 110
                    implicitHeight: 34
                    radius: Theme.pillRadius
                    color: scanArea.containsMouse ? Theme.surface1 : Theme.surface0
                    border.color: Theme.moduleBorder
                    border.width: 1
                    visible: root.wifiPowered

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: "󰑐"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: root.wifiScanning ? Theme.accent : Theme.text

                            RotationAnimator on rotation {
                                running: root.wifiScanning
                                from: 0
                                to: 360
                                loops: Animation.Infinite
                                duration: 800
                            }
                        }

                        Text {
                            text: root.wifiScanning ? "Scanning..." : "Rescan"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.text
                        }
                    }

                    MouseArea {
                        id: scanArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.triggerWifiScan()
                    }
                }
            }

            // If WiFi is disabled
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.pillRadius
                color: Theme.surface0
                visible: !root.wifiPowered

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 12

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "󰤭"
                        font.family: Theme.fontFamily
                        font.pixelSize: 48
                        color: Theme.overlay0
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Wi-Fi is turned off"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        color: Theme.text
                    }

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 140
                        implicitHeight: 36
                        radius: Theme.pillRadius
                        color: Theme.accent

                        Text {
                            anchors.centerIn: parent
                            text: "Turn On Wi-Fi"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                            color: Theme.mantle
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.toggleWifiPower()
                        }
                    }
                }
            }

            // If WiFi is enabled: Active connection banner + Network list
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.wifiPowered
                spacing: 10

                // Connected Network Card
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: root.wifiConnected ? 70 : 0
                    visible: root.wifiConnected
                    radius: Theme.pillRadius
                    color: Theme.surface0
                    border.color: Theme.teal
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 12

                        // Signal Icon
                        Rectangle {
                            implicitWidth: 42
                            implicitHeight: 42
                            radius: 21
                            color: Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.15)

                            Text {
                                anchors.centerIn: parent
                                text: "󰤨"
                                font.family: Theme.fontFamily
                                font.pixelSize: 22
                                color: Theme.teal
                            }
                        }

                        // Info
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            RowLayout {
                                spacing: 8
                                Text {
                                    text: root.wifiSsid
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeLarge
                                    font.bold: true
                                    color: Theme.text
                                    elide: Text.ElideRight
                                    Layout.maximumWidth: 200
                                }

                                Rectangle {
                                    implicitWidth: 64
                                    implicitHeight: 18
                                    radius: 9
                                    color: Qt.rgba(Theme.green.r, Theme.green.g, Theme.green.b, 0.2)

                                    Text {
                                        anchors.centerIn: parent
                                        text: "Connected"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        font.bold: true
                                        color: Theme.green
                                    }
                                }
                            }

                            Text {
                                text: (root.wifiIp ? root.wifiIp + " • " : "") + (root.wifiSecurity ? root.wifiSecurity + " • " : "") + root.wifiSignal + "% Signal"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.overlay0
                            }
                        }

                        // Actions: Disconnect & Forget
                        RowLayout {
                            spacing: 6

                            // Disconnect Button
                            Rectangle {
                                implicitWidth: 78
                                implicitHeight: 30
                                radius: Theme.pillRadius
                                color: disconnHover.containsMouse ? Theme.red : Theme.surface1
                                border.color: Theme.moduleBorder
                                border.width: 1

                                Text {
                                    anchors.centerIn: parent
                                    text: "Disconnect"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 11
                                    font.bold: true
                                    color: disconnHover.containsMouse ? "#ffffff" : Theme.red
                                }

                                MouseArea {
                                    id: disconnHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.disconnectWifi()
                                }
                            }

                            // Forget Button
                            Rectangle {
                                implicitWidth: 72
                                implicitHeight: 30
                                radius: Theme.pillRadius
                                color: forgetActiveHover.containsMouse ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.2) : Theme.surface1
                                border.color: forgetActiveHover.containsMouse ? Theme.red : Theme.moduleBorder
                                border.width: 1

                                RowLayout {
                                    anchors.centerIn: parent
                                    spacing: 4

                                    Text {
                                        text: "󰆴"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        color: forgetActiveHover.containsMouse ? Theme.red : Theme.overlay0
                                    }

                                    Text {
                                        text: "Forget"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: forgetActiveHover.containsMouse ? Theme.red : Theme.subtext0
                                    }
                                }

                                MouseArea {
                                    id: forgetActiveHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.forgetWifi(root.wifiSsid)
                                }
                            }
                        }
                    }
                }

                // Search Bar
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 34
                    radius: Theme.pillRadius
                    color: Theme.surface0
                    border.color: wifiSearchInput.activeFocus ? Theme.accent : Theme.moduleBorder
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 6

                        Text {
                            text: "󰍉"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.overlay0
                        }

                        TextInput {
                            id: wifiSearchInput
                            Layout.fillWidth: true
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.text
                            clip: true

                            Text {
                                text: "Search networks..."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.overlay0
                                visible: !wifiSearchInput.text && !wifiSearchInput.activeFocus
                            }

                            onTextChanged: root.wifiSearchText = text.toLowerCase().trim()
                        }
                    }
                }

                // Networks List
                ListView {
                    id: wifiListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4

                    model: {
                        var list = [];
                        for (var i = 0; i < root.wifiNetworks.length; i++) {
                            var it = root.wifiNetworks[i];
                            if (!root.wifiSearchText || it.ssid.toLowerCase().indexOf(root.wifiSearchText) !== -1) {
                                list.push(it);
                            }
                        }
                        return list;
                    }

                    delegate: Rectangle {
                        id: netItemRect
                        required property var modelData
                        required property int index

                        width: wifiListView.width
                        implicitHeight: isPasswordOpen ? 90 : 46
                        radius: Theme.pillRadius
                        color: netHover.containsMouse ? Theme.surface1 : Theme.surface0
                        border.color: modelData.connected ? Theme.teal : (netHover.containsMouse ? Theme.moduleHoverBorder : Theme.moduleBorder)
                        border.width: 1

                        readonly property bool isPasswordOpen: root.selectedWifiSsid === modelData.ssid

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 6

                            // Main row
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                // Signal Icon
                                Text {
                                    text: {
                                        if (modelData.in_range === false) return "󰤭";
                                        var sig = modelData.signal || 0;
                                        if (sig >= 75) return "󰤨";
                                        if (sig >= 50) return "󰤥";
                                        if (sig >= 25) return "󰤢";
                                        return "󰤟";
                                    }
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    color: modelData.connected ? Theme.teal : (modelData.in_range === false ? Theme.overlay0 : Theme.accent)
                                }

                                // SSID & Badges
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    RowLayout {
                                        spacing: 6

                                        Text {
                                            text: modelData.ssid
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            font.bold: modelData.connected || modelData.known
                                            color: modelData.connected ? Theme.teal : (modelData.in_range === false ? Theme.overlay0 : Theme.text)
                                            elide: Text.ElideRight
                                            Layout.maximumWidth: 190
                                        }

                                        // Lock badge
                                        Text {
                                            text: modelData.security && modelData.security.toLowerCase() !== "open" ? "󰌾" : ""
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: Theme.overlay0
                                            visible: text.length > 0 && modelData.in_range !== false
                                        }

                                        // Saved badge
                                        Rectangle {
                                            implicitWidth: (modelData.in_range === false) ? 105 : 42
                                            implicitHeight: 16
                                            radius: 4
                                            color: Theme.surface2
                                            visible: modelData.known && !modelData.connected

                                            Text {
                                                anchors.centerIn: parent
                                                text: (modelData.in_range === false) ? "Saved • Out of range" : "Saved"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                color: Theme.subtext0
                                            }
                                        }
                                    }
                                }

                                // Signal %
                                Text {
                                    text: (modelData.in_range === false) ? "" : ((modelData.signal || 0) + "%")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Theme.overlay0
                                    visible: modelData.in_range !== false
                                }

                                // Action Button
                                Rectangle {
                                    implicitWidth: (modelData.in_range === false) ? 60 : (modelData.connected ? 70 : 64)
                                    implicitHeight: 28
                                    radius: 6
                                    color: (modelData.in_range === false) ? (connBtnArea.containsMouse ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.2) : Theme.surface2) : (modelData.connected ? Qt.rgba(Theme.teal.r, Theme.teal.g, Theme.teal.b, 0.2) : (connBtnArea.containsMouse ? Theme.accent : Theme.surface2))

                                    Text {
                                        anchors.centerIn: parent
                                        text: (modelData.in_range === false) ? "Forget" : (modelData.connected ? "Active" : (modelData.known ? "Connect" : "Join"))
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: (modelData.in_range === false) ? (connBtnArea.containsMouse ? Theme.red : Theme.subtext0) : (modelData.connected ? Theme.teal : (connBtnArea.containsMouse ? Theme.mantle : Theme.text))
                                    }

                                    MouseArea {
                                        id: connBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (modelData.in_range === false) {
                                                root.forgetWifi(modelData.ssid);
                                            } else if (modelData.connected) {
                                                root.disconnectWifi();
                                            } else if (modelData.known || (modelData.security && modelData.security.toLowerCase() === "open")) {
                                                root.connectWifi(modelData.ssid);
                                            } else {
                                                root.selectedWifiSsid = (root.selectedWifiSsid === modelData.ssid) ? "" : modelData.ssid;
                                                root.wifiPasswordInput = "";
                                            }
                                        }
                                    }
                                }

                                // Forget Button (Icon) for in-range saved/known networks
                                Rectangle {
                                    implicitWidth: 28
                                    implicitHeight: 28
                                    radius: 6
                                    color: forgetNetArea.containsMouse ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.2) : "transparent"
                                    border.color: forgetNetArea.containsMouse ? Theme.red : "transparent"
                                    border.width: 1
                                    visible: modelData.known && modelData.in_range !== false

                                    Text {
                                        anchors.centerIn: parent
                                        text: "󰆴"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 12
                                        color: forgetNetArea.containsMouse ? Theme.red : Theme.overlay0
                                    }

                                    MouseArea {
                                        id: forgetNetArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.forgetWifi(modelData.ssid)
                                    }
                                }
                            }

                            // Inline Password Input row when expanding
                            RowLayout {
                                Layout.fillWidth: true
                                visible: isPasswordOpen
                                spacing: 8

                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 30
                                    radius: 4
                                    color: Theme.base
                                    border.color: pwdInput.activeFocus ? Theme.accent : Theme.moduleBorder
                                    border.width: 1

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        spacing: 6

                                        TextInput {
                                            id: pwdInput
                                            Layout.fillWidth: true
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            color: Theme.text
                                            echoMode: root.showWifiPassword ? TextInput.Normal : TextInput.Password
                                            clip: true

                                            Text {
                                                text: "Enter Wi-Fi password..."
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSizeSmall
                                                color: Theme.overlay0
                                                visible: !pwdInput.text && !pwdInput.activeFocus
                                            }

                                            onTextChanged: root.wifiPasswordInput = text
                                            Keys.onReturnPressed: {
                                                if (pwdInput.text.length > 0) {
                                                    root.connectWifi(modelData.ssid, pwdInput.text);
                                                }
                                            }
                                        }

                                        // Eye icon to toggle visibility
                                        Text {
                                            text: root.showWifiPassword ? "󰈈" : "󰈉"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            color: Theme.overlay0

                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.showWifiPassword = !root.showWifiPassword
                                            }
                                        }
                                    }
                                }

                                // Connect with Password button
                                Rectangle {
                                    implicitWidth: 60
                                    implicitHeight: 30
                                    radius: 4
                                    color: pwdConnArea.containsMouse ? Theme.teal : Theme.accent

                                    Text {
                                        anchors.centerIn: parent
                                        text: "Join"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: Theme.mantle
                                    }

                                    MouseArea {
                                        id: pwdConnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (pwdInput.text.length > 0) {
                                                root.connectWifi(modelData.ssid, pwdInput.text);
                                            }
                                        }
                                    }
                                }

                                // Cancel button
                                Rectangle {
                                    implicitWidth: 50
                                    implicitHeight: 30
                                    radius: 4
                                    color: Theme.surface2

                                    Text {
                                        anchors.centerIn: parent
                                        text: "Cancel"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        color: Theme.text
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.selectedWifiSsid = ""
                                    }
                                }
                            }
                        }

                        MouseArea {
                            id: netHover
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: wifiListView.count === 0 && !root.wifiScanning
                        text: "No Wi-Fi networks found"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.overlay0
                    }
                }
            }
        }

        // ==========================================
        // BLUETOOTH VIEW
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.activeTab === "bluetooth"
            spacing: 10

            // Subheader: Power Switch & Discovery Scan Button
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                // Power Toggle Pill
                Rectangle {
                    implicitWidth: 140
                    implicitHeight: 34
                    radius: Theme.pillRadius
                    color: root.btPowered ? Theme.surface1 : Theme.surface0
                    border.color: root.btPowered ? Theme.blue : Theme.moduleBorder
                    border.width: 1

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: root.btPowered ? "󰂯" : "󰂲"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: root.btPowered ? Theme.blue : Theme.overlay0
                        }

                        Text {
                            text: root.btPowered ? "Bluetooth On" : "Bluetooth Off"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: root.btPowered ? Theme.text : Theme.overlay0
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleBtPower()
                    }
                }

                Item { Layout.fillWidth: true }

                // Scan / Discovery Toggle
                Rectangle {
                    implicitWidth: 120
                    implicitHeight: 34
                    radius: Theme.pillRadius
                    color: root.btDiscovering ? Qt.rgba(Theme.blue.r, Theme.blue.g, Theme.blue.b, 0.2) : (btScanArea.containsMouse ? Theme.surface1 : Theme.surface0)
                    border.color: root.btDiscovering ? Theme.blue : Theme.moduleBorder
                    border.width: 1
                    visible: root.btPowered

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: "󰍉"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: root.btDiscovering ? Theme.blue : Theme.text

                            RotationAnimator on rotation {
                                running: root.btDiscovering
                                from: 0
                                to: 360
                                loops: Animation.Infinite
                                duration: 1200
                            }
                        }

                        Text {
                            text: root.btDiscovering ? "Scanning..." : "Pair Device"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: root.btDiscovering ? Theme.blue : Theme.text
                        }
                    }

                    MouseArea {
                        id: btScanArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleBtScan()
                    }
                }
            }

            // If Bluetooth is disabled
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.pillRadius
                color: Theme.surface0
                visible: !root.btPowered

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 12

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "󰂲"
                        font.family: Theme.fontFamily
                        font.pixelSize: 48
                        color: Theme.overlay0
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Bluetooth is turned off"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        color: Theme.text
                    }

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 150
                        implicitHeight: 36
                        radius: Theme.pillRadius
                        color: Theme.accent

                        Text {
                            anchors.centerIn: parent
                            text: "Turn On Bluetooth"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                            color: Theme.mantle
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.toggleBtPower()
                        }
                    }
                }
            }

            // If Bluetooth is enabled: Paired Devices List & Discovered Devices
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.btPowered
                spacing: 8

                Text {
                    text: "Paired Devices (" + root.btDevices.length + ")"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: Theme.overlay0
                }

                ListView {
                    id: btListView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: root.btDevices

                    delegate: Rectangle {
                        required property var modelData
                        required property int index

                        width: btListView.width
                        implicitHeight: 48
                        radius: Theme.pillRadius
                        color: btDevHover.containsMouse ? Theme.surface1 : Theme.surface0
                        border.color: modelData.connected ? Theme.blue : (btDevHover.containsMouse ? Theme.moduleHoverBorder : Theme.moduleBorder)
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 10

                            // Device Icon
                            Rectangle {
                                implicitWidth: 32
                                implicitHeight: 32
                                radius: 16
                                color: modelData.connected ? Qt.rgba(Theme.blue.r, Theme.blue.g, Theme.blue.b, 0.18) : Theme.surface2

                                Text {
                                    anchors.centerIn: parent
                                    text: {
                                        var ic = modelData.icon || "";
                                        if (ic === "audio-headset") return "󰋋";
                                        if (ic === "input-mouse") return "󰍽";
                                        if (ic === "input-keyboard") return "󰌌";
                                        if (ic === "phone") return "󰏲";
                                        return "󰂯";
                                    }
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    color: modelData.connected ? Theme.blue : Theme.text
                                }
                            }

                            // Device Details
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                RowLayout {
                                    spacing: 6

                                    Text {
                                        text: modelData.name || modelData.mac
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSize
                                        font.bold: modelData.connected
                                        color: modelData.connected ? Theme.blue : Theme.text
                                        elide: Text.ElideRight
                                        Layout.maximumWidth: 170
                                    }

                                    // Battery level if available
                                    Rectangle {
                                        implicitWidth: 42
                                        implicitHeight: 16
                                        radius: 4
                                        color: Qt.rgba(Theme.green.r, Theme.green.g, Theme.green.b, 0.2)
                                        visible: modelData.battery >= 0

                                        Text {
                                            anchors.centerIn: parent
                                            text: "󰁹 " + modelData.battery + "%"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 9
                                            color: Theme.green
                                        }
                                    }
                                }

                                Text {
                                    text: modelData.connected ? "Connected" : modelData.mac
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    color: modelData.connected ? Theme.green : Theme.overlay0
                                }
                            }

                            // Connect / Disconnect button
                            Rectangle {
                                implicitWidth: modelData.connected ? 74 : 64
                                implicitHeight: 28
                                radius: 6
                                color: modelData.connected ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.2) : (btConnHover.containsMouse ? Theme.accent : Theme.surface2)

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.connected ? "Disconnect" : "Connect"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    font.bold: true
                                    color: modelData.connected ? Theme.red : (btConnHover.containsMouse ? Theme.mantle : Theme.text)
                                }

                                MouseArea {
                                    id: btConnHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (modelData.connected) {
                                            root.disconnectBt(modelData.mac);
                                        } else {
                                            root.connectBt(modelData.mac);
                                        }
                                    }
                                }
                            }

                            // Forget / Remove device icon
                            Rectangle {
                                implicitWidth: 26
                                implicitHeight: 26
                                radius: 4
                                color: rmArea.containsMouse ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.2) : "transparent"

                                Text {
                                    anchors.centerIn: parent
                                    text: "󰆴"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 12
                                    color: rmArea.containsMouse ? Theme.red : Theme.overlay0
                                }

                                MouseArea {
                                    id: rmArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.removeBt(modelData.mac)
                                }
                            }
                        }

                        MouseArea {
                            id: btDevHover
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: root.btDevices.length === 0
                        text: "No paired Bluetooth devices"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.overlay0
                    }
                }

                // Discovered Devices Section (if scanning)
                ColumnLayout {
                    Layout.fillWidth: true
                    visible: root.btDiscovering
                    spacing: 6

                    Text {
                        text: "Nearby Devices Found (" + root.btDiscovered.length + ")"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: true
                        color: Theme.blue
                    }

                    ListView {
                        id: discListView
                        Layout.fillWidth: true
                        implicitHeight: Math.min(110, count * 40)
                        clip: true
                        spacing: 4
                        model: root.btDiscovered

                        delegate: Rectangle {
                            required property var modelData
                            width: discListView.width
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.moduleBorder
                            border.width: 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 8

                                Text {
                                    text: "󰂯"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    color: Theme.blue
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Theme.text
                                    elide: Text.ElideRight
                                }

                                Rectangle {
                                    implicitWidth: 50
                                    implicitHeight: 24
                                    radius: 4
                                    color: Theme.accent

                                    Text {
                                        anchors.centerIn: parent
                                        text: "Pair"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        font.bold: true
                                        color: Theme.mantle
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.pairBt(modelData.mac)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Bottom status row
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: root.activeTab === "wifi" ? (root.wifiNetworks.length + " networks available") : (root.btDevices.length + " paired • " + root.btConnectedCount + " connected")
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }
    }
}
