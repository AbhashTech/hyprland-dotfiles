import QtQuick
import Quickshell
import Quickshell.Io
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

    property var barWindow: null
    property string screenName: ""
    property int volume: 50
    property bool muted: false
    property string sinkName: "Speakers"
    property int micVolume: 100
    property bool micMuted: false
    property string micName: "Microphone"
    property int brightness: 50
    property string wifiText: "󰤨"
    property bool wifiPowered: true
    property bool wifiConnected: false
    property string wifiSsid: ""
    property int wifiSignal: 0
    property string wifiRssi: ""
    property string wifiIp: ""
    property string wifiSec: ""
    property string wifiFreq: ""
    property string wifiIface: "wlan0"
    property string btText: "󰂯"
    property bool btPowered: true
    property bool btConnected: false
    property int btConnectedCount: 0
    property int btPairedCount: 0
    property var btDevices: []
    property string batIcon: "󰁹"
    property string batPercent: "100%"
    property string batProfile: PluginManager.powerProfile
    property string batStatus: "Full"
    property double batPowerW: 0.0
    property double batHealth: 100.0
    property string batTimeStr: ""

    // Dynamic color based on power profile
    readonly property color batColor: {
        if (batProfile === "power-saver") return Theme.green;
        if (batProfile === "performance") return Theme.peach;
        return Theme.blue; // balanced
    }

    Process {
        id: statusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/scripts/status_helper.py", "--screen", root.screenName]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data.trim());
                    if (!obj) return;

                    // 1. Audio
                    if (obj.audio) {
                        if (obj.audio.vol !== undefined) root.volume = obj.audio.vol;
                        if (obj.audio.muted !== undefined) root.muted = obj.audio.muted;
                        if (obj.audio.sink) root.sinkName = obj.audio.sink;
                        if (obj.audio.mic_vol !== undefined) root.micVolume = obj.audio.mic_vol;
                        if (obj.audio.mic_muted !== undefined) root.micMuted = obj.audio.mic_muted;
                        if (obj.audio.mic) root.micName = obj.audio.mic;
                    }

                    // 2. Brightness
                    if (obj.bright && obj.bright.brightness !== undefined) {
                        root.brightness = obj.bright.brightness;
                    }

                    // 3. Wi-Fi
                    if (obj.wifi) {
                        root.wifiPowered = obj.wifi.powered !== undefined ? obj.wifi.powered : true;
                        root.wifiConnected = !!obj.wifi.connected;
                        root.wifiSsid = obj.wifi.ssid || "";
                        root.wifiSignal = parseInt(obj.wifi.sig || "0", 10);
                        root.wifiRssi = obj.wifi.rssi || "";
                        root.wifiIp = obj.wifi.ip || "";
                        root.wifiSec = obj.wifi.sec || "";
                        root.wifiFreq = obj.wifi.freq || "";
                        root.wifiIface = obj.wifi.iface || "wlan0";

                        if (!root.wifiPowered) {
                            root.wifiText = "󰤮";
                        } else if (root.wifiConnected) {
                            if (root.wifiSignal >= 75) root.wifiText = "󰤨";
                            else if (root.wifiSignal >= 50) root.wifiText = "󰤥";
                            else if (root.wifiSignal >= 25) root.wifiText = "󰤢";
                            else root.wifiText = "󰤟";
                        } else {
                            root.wifiText = "󰤭";
                        }
                    }

                    // 4. Bluetooth
                    if (obj.bt) {
                        root.btPowered = obj.bt.powered !== undefined ? obj.bt.powered : true;
                        root.btConnected = !!obj.bt.connected;
                        root.btConnectedCount = parseInt(obj.bt.connected_count || "0", 10);
                        root.btPairedCount = parseInt(obj.bt.paired_count || "0", 10);
                        root.btDevices = obj.bt.devices || [];

                        if (!root.btPowered) {
                            root.btText = "󰂲";
                        } else if (root.btConnected) {
                            root.btText = "󰂱";
                        } else {
                            root.btText = "󰂯";
                        }
                    }

                    // 5. Battery
                    if (obj.bat) {
                        var cap = obj.bat.cap !== undefined ? obj.bat.cap : 100;
                        var chg = obj.bat.status === "Charging";
                        var icon = "󰁹";
                        if (cap <= 10) icon = chg ? "󰢜" : "󰂃";
                        else if (cap <= 20) icon = chg ? "󰂆" : "󰁺";
                        else if (cap <= 30) icon = chg ? "󰂇" : "󰁻";
                        else if (cap <= 40) icon = chg ? "󰂈" : "󰁼";
                        else if (cap <= 50) icon = chg ? "󰢝" : "󰁽";
                        else if (cap <= 60) icon = chg ? "󰂉" : "󰁾";
                        else if (cap <= 70) icon = chg ? "󰢞" : "󰁿";
                        else if (cap <= 80) icon = chg ? "󰂊" : "󰂀";
                        else if (cap <= 90) icon = chg ? "󰂋" : "󰂁";
                        else icon = chg ? "󰂅" : "󰁹";
                        root.batIcon = icon;
                        root.batPercent = cap + "%";
                        if (obj.bat.status) root.batStatus = obj.bat.status;
                        if (obj.bat.power_w !== undefined) root.batPowerW = obj.bat.power_w;
                        if (obj.bat.health !== undefined) root.batHealth = obj.bat.health;
                        if (obj.bat.time_str !== undefined) root.batTimeStr = obj.bat.time_str;
                        if (obj.bat.profile) {
                            root.batProfile = obj.bat.profile;
                            PluginManager.setPowerProfile(obj.bat.profile);
                        }
                    }
                } catch (e) {}
            }
        }
    }

    Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!statusProc.running) statusProc.running = true;
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
        spacing: 6

        // Volume Item
        Item {
            id: volItem
            implicitWidth: volContent.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: volContent
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.muted ? "󰝟" : (root.volume > 50 ? "󰕾" : "󰖀")
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: root.muted ? Theme.red : Theme.blue
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.volume + "%"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: volItem
                isHovered: volArea.containsMouse
                icon: root.muted ? "󰝟" : (root.volume > 50 ? "󰕾" : "󰖀")
                iconColor: root.muted ? Theme.red : Theme.blue
                title: "Audio & Sound"
                description: "PipeWire / WirePlumber audio server"
                details: [
                    {
                        icon: root.muted ? "󰝟" : "󰕾",
                        iconColor: root.muted ? Theme.red : Theme.blue,
                        label: "Output (" + root.sinkName + ")",
                        value: root.muted ? "Muted" : (root.volume + "%"),
                        valueColor: root.muted ? Theme.red : Theme.text
                    },
                    {
                        icon: root.micMuted ? "󰍭" : "󰍬",
                        iconColor: root.micMuted ? Theme.red : Theme.mauve,
                        label: "Input (" + root.micName + ")",
                        value: root.micMuted ? "Muted" : (root.micVolume + "%"),
                        valueColor: root.micMuted ? Theme.red : Theme.text
                    },
                    {
                        icon: "󰓃",
                        iconColor: Theme.sapphire,
                        label: "Audio Server",
                        value: "PipeWire",
                        valueColor: Theme.subtext0
                    }
                ]
                shortcuts: [
                    { action: "Toggle Mute", key: "Left Click" },
                    { action: "Audio Mixer Menu", key: "Right Click" },
                    { action: "Volume Up / Down", key: "Scroll" }
                ]
            }

            MouseArea {
                id: volArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "mute"]);
                    } else if (mouse.button === Qt.RightButton) {
                        PluginManager.toggle("volume");
                    }
                }

                onWheel: wheel => {
                    if (wheel.angleDelta.y > 0) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "up", "5"]);
                    } else if (wheel.angleDelta.y < 0) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "down", "5"]);
                    }
                }
            }
        }

        // Brightness Item
        Item {
            id: brightItem
            implicitWidth: brightContent.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: brightContent
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: "󰃠"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.yellow
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.brightness + "%"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: brightItem
                isHovered: brightArea.containsMouse
                icon: "󰃠"
                iconColor: Theme.yellow
                title: "Screen Brightness"
                description: "Display backlight & color temperature"
                details: [
                    {
                        icon: "󰃠",
                        iconColor: Theme.yellow,
                        label: "Current Level",
                        value: root.brightness + "%",
                        valueColor: Theme.yellow
                    },
                    {
                        icon: "󰃟",
                        iconColor: Theme.peach,
                        label: "Backlight Control",
                        value: "Hardware / DDC",
                        valueColor: Theme.subtext0
                    },
                    {
                        icon: "󰖔",
                        iconColor: Theme.mauve,
                        label: "Night Light Filter",
                        value: "Hyprsunset (Toggleable)",
                        valueColor: Theme.mauve
                    }
                ]
                shortcuts: [
                    { action: "Brightness Center", key: "SUPER + SHIFT + B" },
                    { action: "Night Light Filter", key: "SUPER + ALT + N" },
                    { action: "Brightness Up / Down", key: "Scroll" }
                ]
            }

            MouseArea {
                id: brightArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("brightness");
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/sunset_idle_manager.py", "--sunset-toggle"]);
                    }
                }

                onWheel: wheel => {
                    var act = wheel.angleDelta.y > 0 ? (root.screenName !== "" ? "screen-up" : "active-up") : (root.screenName !== "" ? "screen-down" : "active-down");
                    var args = root.screenName !== ""
                        ? ["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/brightness_control.py", act, root.screenName, "5"]
                        : ["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/brightness_control.py", act, "5"];
                    ctlProc.exec(args);
                    if (wheel.angleDelta.y > 0) {
                        root.brightness = Math.min(100, root.brightness + 5);
                    } else if (wheel.angleDelta.y < 0) {
                        root.brightness = Math.max(0, root.brightness - 5);
                    }
                }
            }
        }

        // Network Item
        Item {
            id: netItem
            implicitWidth: netText.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Text {
                id: netText
                anchors.verticalCenter: parent.verticalCenter
                text: root.wifiText
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.teal
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: netItem
                isHovered: netArea.containsMouse
                icon: root.wifiText
                iconColor: root.wifiConnected ? Theme.teal : (root.wifiPowered ? Theme.subtext0 : Theme.red)
                title: root.wifiConnected ? root.wifiSsid : (root.wifiPowered ? "Wi-Fi Disconnected" : "Wi-Fi Disabled")
                description: root.wifiConnected ? ("Connected via " + root.wifiIface) : (root.wifiPowered ? "Adapter active, not connected to any network" : "Wireless adapter radio is turned off")
                details: root.wifiConnected ? [
                    {
                        icon: "󰤨",
                        iconColor: Theme.teal,
                        label: "Network (SSID)",
                        value: root.wifiSsid,
                        valueColor: Theme.teal
                    },
                    {
                        icon: "󰤢",
                        iconColor: Theme.green,
                        label: "Signal Strength",
                        value: root.wifiSignal + "%" + (root.wifiRssi !== "" ? " (" + root.wifiRssi + ")" : ""),
                        valueColor: Theme.green
                    },
                    {
                        icon: "󰩟",
                        iconColor: Theme.blue,
                        label: "IPv4 Address",
                        value: root.wifiIp !== "" ? root.wifiIp : "Assigning IP...",
                        valueColor: Theme.text
                    },
                    {
                        icon: "󰌾",
                        iconColor: Theme.yellow,
                        label: "Security & Band",
                        value: (root.wifiSec !== "" ? root.wifiSec : "Open") + (root.wifiFreq !== "" ? " • " + root.wifiFreq : ""),
                        valueColor: Theme.subtext0
                    },
                    {
                        icon: "󰈀",
                        iconColor: Theme.sapphire,
                        label: "Interface",
                        value: root.wifiIface,
                        valueColor: Theme.subtext0
                    }
                ] : [
                    {
                        icon: root.wifiPowered ? "󰤭" : "󰤮",
                        iconColor: root.wifiPowered ? Theme.yellow : Theme.red,
                        label: "Radio State",
                        value: root.wifiPowered ? "Enabled (Disconnected)" : "Disabled (Radio Off)",
                        valueColor: root.wifiPowered ? Theme.yellow : Theme.red
                    },
                    {
                        icon: "󰈀",
                        iconColor: Theme.sapphire,
                        label: "Interface",
                        value: root.wifiIface,
                        valueColor: Theme.subtext0
                    }
                ]
                shortcuts: [
                    { action: "Wi-Fi Control Center", key: "Left Click" },
                    { action: "Toggle Wi-Fi Radio", key: "Right Click" }
                ]
            }

            MouseArea {
                id: netArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("wifi");
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/connectivity/wireless_ctl.py", "wifi-toggle"]);
                    }
                }
            }
        }

        // Bluetooth Item
        Item {
            id: btItem
            implicitWidth: btText.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Text {
                id: btText
                anchors.verticalCenter: parent.verticalCenter
                text: root.btText
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.blue
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: btItem
                isHovered: btArea.containsMouse
                icon: root.btText
                iconColor: root.btConnected ? Theme.green : (root.btPowered ? Theme.blue : Theme.red)
                title: root.btConnected ? (root.btConnectedCount + (root.btConnectedCount === 1 ? " Device Connected" : " Devices Connected")) : (root.btPowered ? "Bluetooth On" : "Bluetooth Off")
                description: root.btConnected ? "Active connected bluetooth peripherals" : (root.btPowered ? (root.btPairedCount + " paired devices in memory") : "Bluetooth adapter radio is disabled")
                details: {
                    var list = [];
                    if (root.btConnected && root.btDevices && root.btDevices.length > 0) {
                        for (var i = 0; i < root.btDevices.length; i++) {
                            var dev = root.btDevices[i];
                            var batStr = (dev.battery !== undefined && dev.battery >= 0) ? (dev.battery + "%") : "Connected";
                            list.push({
                                icon: dev.icon || "󰂱",
                                iconColor: Theme.green,
                                label: dev.name || "Device",
                                value: batStr,
                                valueColor: (dev.battery !== undefined && dev.battery >= 0 && dev.battery <= 20) ? Theme.red : Theme.green
                            });
                        }
                    }
                    list.push({
                        icon: root.btPowered ? "󰂯" : "󰂲",
                        iconColor: root.btPowered ? Theme.blue : Theme.red,
                        label: "Controller Radio",
                        value: root.btPowered ? "Powered On" : "Powered Off",
                        valueColor: root.btPowered ? Theme.green : Theme.red
                    });
                    list.push({
                        icon: "󰂯",
                        iconColor: Theme.sapphire,
                        label: "Paired Devices",
                        value: root.btPairedCount + " paired",
                        valueColor: Theme.subtext0
                    });
                    return list;
                }
                shortcuts: [
                    { action: "Bluetooth Control Center", key: "Left Click" },
                    { action: "Toggle Bluetooth Radio", key: "Right Click" }
                ]
            }

            MouseArea {
                id: btArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("bluetooth");
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/connectivity/wireless_ctl.py", "bt-toggle"]);
                    }
                }
            }
        }

        // Battery Item
        Item {
            id: batItem
            implicitWidth: batContent.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: batContent
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.batIcon
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: root.batColor

                    Behavior on color { ColorAnimation { duration: 200 } }
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.batPercent
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: batItem
                isHovered: batArea.containsMouse
                icon: root.batIcon
                iconColor: root.batColor
                title: "Battery & Power (" + root.batPercent + ")"
                description: root.batStatus + (root.batTimeStr !== "" ? " • " + root.batTimeStr : "")
                details: [
                    {
                        icon: root.batIcon,
                        iconColor: root.batColor,
                        label: "State & Charge",
                        value: root.batStatus + " (" + root.batPercent + ")",
                        valueColor: root.batColor
                    },
                    {
                        icon: root.batProfile === "power-saver" ? "󰾆" : (root.batProfile === "performance" ? "󰓅" : "󰾅"),
                        iconColor: root.batColor,
                        label: "Power Profile",
                        value: root.batProfile.charAt(0).toUpperCase() + root.batProfile.slice(1),
                        valueColor: root.batColor
                    },
                    {
                        icon: "󱐋",
                        iconColor: Theme.peach,
                        label: "Power Draw",
                        value: (root.batPowerW > 0 ? (root.batPowerW + " W") : "On AC Power"),
                        valueColor: Theme.peach
                    },
                    {
                        icon: "󰁹",
                        iconColor: root.batHealth >= 80 ? Theme.green : (root.batHealth >= 60 ? Theme.yellow : Theme.red),
                        label: "Battery Health",
                        value: root.batHealth + "%",
                        valueColor: root.batHealth >= 80 ? Theme.green : Theme.yellow
                    },
                    {
                        icon: "󱎫",
                        iconColor: Theme.sapphire,
                        label: "Runtime Estimate",
                        value: root.batTimeStr !== "" ? root.batTimeStr : (root.batStatus === "Full" ? "Fully Charged" : "Calculating..."),
                        valueColor: Theme.text
                    }
                ]
                shortcuts: [
                    { action: "Power Profiles Menu", key: "Left Click" },
                    { action: "Task Manager (btop)", key: "Right Click" }
                ]
            }

            MouseArea {
                id: batArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("battery");
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
                    }
                }
            }
        }
    }
}
