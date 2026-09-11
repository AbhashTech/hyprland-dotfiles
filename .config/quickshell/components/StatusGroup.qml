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
    property string batIcon: "󰁹"
    property string batPercent: "100%"
    property string batProfile: PluginManager.powerProfile

    // Dynamic color based on power profile
    readonly property color batColor: {
        if (batProfile === "power-saver") return Theme.green;
        if (batProfile === "performance") return Theme.peach;
        return Theme.blue; // balanced
    }

    Process {
        id: volProc
        command: ["python3", "-c", "import subprocess, json, re\ndef clean_audio_name(desc, is_mic=False):\n    if not desc: return 'Digital Mic' if is_mic else 'Speakers'\n    desc = re.sub(r'\\s+', ' ', desc).strip()\n    if 'Speaker' in desc or 'speaker' in desc: return 'Speakers'\n    if 'Headphone' in desc or 'Headset' in desc: return 'Headphones'\n    if 'Digital Microphone' in desc or 'Mic' in desc: return 'Microphone'\n    parts = desc.split(')')\n    if len(parts) > 1 and parts[-1].strip(): return parts[-1].strip()[:24]\n    desc = re.sub(r'\\(HD Audio\\)', '', desc).strip()\n    return desc[:24]\nvol = 50; muted = False; s_desc = 'Speakers'\ntry:\n    res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], capture_output=True, text=True, timeout=2).stdout.strip()\n    parts = res.split()\n    vol = int(round(float(parts[1])*100)) if len(parts) > 1 else 50\n    muted = '[MUTED]' in res\n    s_name = subprocess.run(['pactl', 'get-default-sink'], capture_output=True, text=True, timeout=2).stdout.strip()\n    sinks_json = json.loads(subprocess.run(['pactl', '-f', 'json', 'list', 'sinks'], capture_output=True, text=True, timeout=2).stdout)\n    for s in sinks_json:\n        if s.get('name') == s_name:\n            s_desc = clean_audio_name(s.get('description', ''))\n            break\nexcept Exception: pass\nm_vol = 100; m_muted = False; m_desc = 'Microphone'\ntry:\n    m_res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SOURCE@'], capture_output=True, text=True, timeout=2).stdout.strip()\n    m_parts = m_res.split()\n    m_vol = int(round(float(m_parts[1])*100)) if len(m_parts) > 1 else 100\n    m_muted = '[MUTED]' in m_res\n    m_name = subprocess.run(['pactl', 'get-default-source'], capture_output=True, text=True, timeout=2).stdout.strip()\n    srcs_json = json.loads(subprocess.run(['pactl', '-f', 'json', 'list', 'sources'], capture_output=True, text=True, timeout=2).stdout)\n    for s in srcs_json:\n        if s.get('name') == m_name:\n            m_desc = clean_audio_name(s.get('description', ''), is_mic=True)\n            break\nexcept Exception: pass\nprint(json.dumps({'vol': vol, 'muted': muted, 'sink': s_desc, 'mic_vol': m_vol, 'mic_muted': m_muted, 'mic': m_desc}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.volume = obj.vol;
                    root.muted = obj.muted;
                    if (obj.sink) root.sinkName = obj.sink;
                    if (obj.mic_vol !== undefined) root.micVolume = obj.mic_vol;
                    if (obj.mic_muted !== undefined) root.micMuted = obj.mic_muted;
                    if (obj.mic) root.micName = obj.mic;
                } catch (e) {}
            }
        }
    }

    Process {
        id: brightProc
        command: root.screenName !== ""
            ? ["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/brightness_control.py", "get-screen", root.screenName]
            : ["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/brightness_control.py", "get-active"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj && obj.brightness !== undefined) {
                        root.brightness = obj.brightness;
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: netProc
        command: ["python3", "-c", "import subprocess, json, os, re\ndef get_wifi_info():\n    iface = 'wlan0'\n    try:\n        for net_if in os.listdir('/sys/class/net'):\n            if net_if.startswith(('wl', 'wlan', 'wifi')):\n                iface = net_if; break\n    except Exception: pass\n    powered = True\n    try:\n        rf = subprocess.run(['rfkill', 'list', 'wifi'], capture_output=True, text=True, timeout=2).stdout\n        if 'Soft blocked: yes' in rf or 'Hard blocked: yes' in rf: powered = False\n    except Exception: pass\n    ssid = ''; sig = 0; rssi = ''; ip = ''; sec = ''; freq = ''; connected = False\n    try:\n        res = subprocess.run(['iwctl', 'station', iface, 'show'], capture_output=True, text=True, timeout=2).stdout\n        for l in res.splitlines():\n            if 'Connected network' in l:\n                ssid = l.split('Connected network')[-1].strip(); connected = bool(ssid)\n            elif 'IPv4 address' in l: ip = l.split('IPv4 address')[-1].strip()\n            elif 'Security' in l: sec = l.split('Security')[-1].strip()\n            elif 'Frequency' in l:\n                f_val = l.split('Frequency')[-1].strip()\n                try: freq = '5 GHz' if int(f_val.split()[0]) > 3000 else '2.4 GHz'\n                except: freq = f_val\n            elif 'RSSI' in l and not sig:\n                try:\n                    r_str = l.split('RSSI')[-1].strip(); rssi = r_str\n                    val = int(r_str.split()[0]); sig = max(0, min(100, int(2 * (val + 100))))\n                except: pass\n    except Exception: pass\n    if not ssid:\n        try:\n            res = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL,SECURITY,FREQ,DEVICE', 'dev', 'wifi'], capture_output=True, text=True, timeout=2).stdout\n            for l in res.splitlines():\n                if l.startswith('yes:'):\n                    p = l.split(':')\n                    if len(p) >= 3:\n                        ssid = p[1]; connected = True; sig = int(p[2] or 0)\n                        if len(p) >= 4: sec = p[3]\n                        if len(p) >= 5: freq = p[4]\n                        if len(p) >= 6: iface = p[5]\n        except Exception: pass\n    if not ip and connected:\n        try:\n            ip_out = subprocess.run(['ip', '-brief', 'address', 'show', iface], capture_output=True, text=True, timeout=2).stdout\n            parts = ip_out.split()\n            if len(parts) >= 3: ip = parts[2].split('/')[0]\n        except Exception: pass\n    return {'powered': powered, 'connected': connected, 'ssid': ssid, 'sig': sig, 'rssi': rssi, 'ip': ip, 'sec': sec, 'freq': freq, 'iface': iface}\nprint(json.dumps(get_wifi_info()))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.wifiPowered = obj.powered !== undefined ? obj.powered : true;
                    root.wifiConnected = !!obj.connected;
                    root.wifiSsid = obj.ssid || "";
                    root.wifiSignal = parseInt(obj.sig || "0", 10);
                    root.wifiRssi = obj.rssi || "";
                    root.wifiIp = obj.ip || "";
                    root.wifiSec = obj.sec || "";
                    root.wifiFreq = obj.freq || "";
                    root.wifiIface = obj.iface || "wlan0";

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
                } catch (e) {
                    root.wifiText = "󰤨";
                }
            }
        }
    }

    Process {
        id: btProc
        command: ["python3", "-c", "import subprocess, json; res = subprocess.run(['bluetoothctl', 'show'], capture_output=True, text=True).stdout; powered = 'Powered: yes' in res; dev_res = subprocess.run(['bluetoothctl', 'devices', 'Connected'], capture_output=True, text=True).stdout.strip(); print(json.dumps({'powered': powered, 'connected': bool(dev_res)}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (!obj.powered) {
                        root.btText = "󰂲";
                    } else if (obj.connected) {
                        root.btText = "󰂱";
                    } else {
                        root.btText = "󰂯";
                    }
                } catch (e) {
                    root.btText = "󰂯";
                }
            }
        }
    }

    Process {
        id: batProc
        command: ["python3", "-c", "import glob, subprocess, json\nbats = glob.glob('/sys/class/power_supply/BAT*')\ncap = 100; status = 'Full'\nif bats:\n    b = bats[0]\n    try: cap = int(open(b + '/capacity').read().strip())\n    except: pass\n    try: status = open(b + '/status').read().strip()\n    except: pass\nprof = 'balanced'\ntry:\n    res = subprocess.run(['powerprofilesctl', 'get'], capture_output=True, text=True, timeout=1)\n    if res.returncode == 0 and res.stdout.strip():\n        prof = res.stdout.strip()\nexcept: pass\nprint(json.dumps({'cap': cap, 'status': status, 'profile': prof}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    var cap = obj.cap;
                    var chg = obj.status === "Charging";
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
                    if (obj.profile) {
                        root.batProfile = obj.profile;
                        PluginManager.setPowerProfile(obj.profile);
                    }
                } catch (e) {
                    root.batIcon = "󰁹";
                    root.batPercent = "100%";
                }
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
            if (!volProc.running) volProc.running = true;
            if (!brightProc.running) brightProc.running = true;
            if (!netProc.running) netProc.running = true;
            if (!btProc.running) btProc.running = true;
            if (!batProc.running) batProc.running = true;
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
                description: "Display brightness: " + root.brightness + "%"
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
                iconColor: Theme.blue
                title: "Bluetooth Manager"
                description: "Paired devices & bluetooth settings"
                shortcuts: [
                    { action: "Bluetooth Control Center", key: "SUPER + CTRL + B" },
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
                description: "Power Profile: " + root.batProfile.charAt(0).toUpperCase() + root.batProfile.slice(1)
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
