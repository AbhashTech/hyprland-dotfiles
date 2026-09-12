pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    // Audio State
    property int volume: 50
    property bool muted: false
    property string sinkName: "Speakers"
    property int micVolume: 100
    property bool micMuted: false
    property string micName: "Microphone"

    // Brightness State
    property int brightness: 50
    property string brightScreen: ""
    property string brightLabel: "Display"
    property bool brightIsInternal: true

    // Wi-Fi State
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

    // Bluetooth State
    property string btText: "󰂯"
    property bool btPowered: true
    property bool btConnected: false
    property int btConnectedCount: 0
    property int btPairedCount: 0
    property var btDevices: []

    // Battery State
    property string batIcon: "󰁹"
    property string batPercent: "100%"
    property string batProfile: PluginManager.powerProfile
    property string batStatus: "Full"
    property double batPowerW: 0.0
    property double batHealth: 100.0
    property string batTimeStr: ""

    readonly property color batColor: {
        if (batProfile === "power-saver") return Theme.green;
        if (batProfile === "performance") return Theme.peach;
        return Theme.blue;
    }

    // Notifications & Clipboard
    property int notifCount: 0
    property bool dndActive: false
    property bool clipDndActive: false

    property var statusProc: Process {
        id: statusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/scripts/status_helper.py"]
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
                        if (obj.bright.name) root.brightScreen = obj.bright.name;
                        if (obj.bright.label) root.brightLabel = obj.bright.label;
                        if (obj.bright.is_internal !== undefined) root.brightIsInternal = obj.bright.is_internal;
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

    property var notifStatusProc: Process {
        id: notifStatusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "status"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data.trim());
                    if (obj) {
                        root.notifCount = obj.count !== undefined ? obj.count : 0;
                        root.dndActive = !!obj.dnd;
                    }
                } catch (e) {
                    try {
                        root.notifCount = parseInt(data.trim(), 10) || 0;
                    } catch (e2) {
                        root.notifCount = 0;
                    }
                }
            }
        }
    }

    property var clipStatusProc: Process {
        id: clipStatusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "status"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data.trim());
                    if (obj) {
                        root.clipDndActive = !!obj.dnd;
                    }
                } catch (e) {
                    root.clipDndActive = false;
                }
            }
        }
    }

    property var pollTimer: Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!statusProc.running) statusProc.running = true;
            if (!notifStatusProc.running) notifStatusProc.running = true;
            if (!clipStatusProc.running) clipStatusProc.running = true;
        }
    }
}
