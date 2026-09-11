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
        id: volProc
        command: ["python3", "-c", "import subprocess, json\ndef clean_audio_name(desc, is_mic=False):\n    if not desc: return 'Digital Mic' if is_mic else 'Speakers'\n    desc = ' '.join(desc.split()).strip()\n    if 'Speaker' in desc or 'speaker' in desc: return 'Speakers'\n    if 'Headphone' in desc or 'Headset' in desc: return 'Headphones'\n    if 'Digital Microphone' in desc or 'Mic' in desc: return 'Microphone'\n    parts = desc.split(')')\n    if len(parts) > 1 and parts[-1].strip(): return parts[-1].strip()[:24]\n    desc = desc.replace('(HD Audio)', '').strip()\n    return desc[:24]\nvol = 50; muted = False; s_desc = 'Speakers'\ntry:\n    res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], capture_output=True, text=True, timeout=2).stdout.strip()\n    parts = res.split()\n    vol = int(round(float(parts[1])*100)) if len(parts) > 1 else 50\n    muted = '[MUTED]' in res\n    s_name = subprocess.run(['pactl', 'get-default-sink'], capture_output=True, text=True, timeout=2).stdout.strip()\n    sinks_json = json.loads(subprocess.run(['pactl', '-f', 'json', 'list', 'sinks'], capture_output=True, text=True, timeout=2).stdout)\n    for s in sinks_json:\n        if s.get('name') == s_name:\n            s_desc = clean_audio_name(s.get('description', ''))\n            break\nexcept Exception: pass\nm_vol = 100; m_muted = False; m_desc = 'Microphone'\ntry:\n    m_res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SOURCE@'], capture_output=True, text=True, timeout=2).stdout.strip()\n    m_parts = m_res.split()\n    m_vol = int(round(float(m_parts[1])*100)) if len(m_parts) > 1 else 100\n    m_muted = '[MUTED]' in m_res\n    m_name = subprocess.run(['pactl', 'get-default-source'], capture_output=True, text=True, timeout=2).stdout.strip()\n    srcs_json = json.loads(subprocess.run(['pactl', '-f', 'json', 'list', 'sources'], capture_output=True, text=True, timeout=2).stdout)\n    for s in srcs_json:\n        if s.get('name') == m_name:\n            m_desc = clean_audio_name(s.get('description', ''), is_mic=True)\n            break\nexcept Exception: pass\nprint(json.dumps({'vol': vol, 'muted': muted, 'sink': s_desc, 'mic_vol': m_vol, 'mic_muted': m_muted, 'mic': m_desc}))"]
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
        command: ["python3", "-c", "import subprocess, json\ndef get_bt_info():\n    show_out = subprocess.run(['bluetoothctl', 'show'], capture_output=True, text=True, timeout=2).stdout\n    powered = 'Powered: yes' in show_out\n    paired_out = subprocess.run(['bluetoothctl', 'devices', 'Paired'], capture_output=True, text=True, timeout=2).stdout\n    if not paired_out: paired_out = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True, timeout=2).stdout\n    paired_count = len([l for l in paired_out.splitlines() if l.strip().startswith('Device')])\n    conn_out = subprocess.run(['bluetoothctl', 'devices', 'Connected'], capture_output=True, text=True, timeout=2).stdout\n    conn_lines = [l for l in conn_out.splitlines() if l.strip().startswith('Device')]\n    connected_count = len(conn_lines)\n    connected = connected_count > 0\n    devices = []\n    for l in conn_lines:\n        parts = l.strip().split()\n        if len(parts) >= 3:\n            mac = parts[1]; name = ' '.join(parts[2:])\n            info_out = subprocess.run(['bluetoothctl', 'info', mac], capture_output=True, text=True, timeout=2).stdout\n            bat = -1; icon_type = '󰂱'\n            for il in info_out.splitlines():\n                if 'Battery Percentage:' in il:\n                    try:\n                        if '(' in il and ')' in il: bat = int(il.split('(')[-1].split(')')[0].strip())\n                        else: bat = int(il.split('Battery Percentage:')[-1].strip().replace('%', ''))\n                    except: pass\n                elif 'Icon:' in il:\n                    ic = il.lower()\n                    if 'audio' in ic or 'headset' in ic or 'headphone' in ic: icon_type = '󰋋'\n                    elif 'mouse' in ic: icon_type = '󰍽'\n                    elif 'keyboard' in ic: icon_type = '󰌌'\n                    elif 'phone' in ic: icon_type = '󰄜'\n            devices.append({'name': name, 'mac': mac, 'battery': bat, 'icon': icon_type})\n    return {'powered': powered, 'connected': connected, 'connected_count': connected_count, 'paired_count': paired_count, 'devices': devices}\nprint(json.dumps(get_bt_info()))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.btPowered = obj.powered !== undefined ? obj.powered : true;
                    root.btConnected = !!obj.connected;
                    root.btConnectedCount = parseInt(obj.connected_count || "0", 10);
                    root.btPairedCount = parseInt(obj.paired_count || "0", 10);
                    root.btDevices = obj.devices || [];

                    if (!root.btPowered) {
                        root.btText = "󰂲";
                    } else if (root.btConnected) {
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
        command: ["python3", "-c", "import glob, subprocess, json, os\ndef get_bat():\n    bats = glob.glob('/sys/class/power_supply/BAT*')\n    cap = 100; status = 'Full'; power_w = 0.0; health = 100.0; time_str = ''\n    if bats:\n        b = bats[0]\n        try: cap = int(open(os.path.join(b, 'capacity')).read().strip())\n        except: pass\n        try: status = open(os.path.join(b, 'status')).read().strip()\n        except: pass\n        try:\n            p_now = int(open(os.path.join(b, 'power_now')).read().strip())\n            power_w = p_now / 1000000.0\n        except:\n            try:\n                c_now = int(open(os.path.join(b, 'current_now')).read().strip())\n                v_now = int(open(os.path.join(b, 'voltage_now')).read().strip())\n                power_w = (c_now * v_now) / 1e12\n            except: pass\n        try:\n            efull = int(open(os.path.join(b, 'energy_full')).read().strip())\n            edes = int(open(os.path.join(b, 'energy_full_design')).read().strip())\n            health = round((efull / edes) * 100, 1)\n        except:\n            try:\n                cfull = int(open(os.path.join(b, 'charge_full')).read().strip())\n                cdes = int(open(os.path.join(b, 'charge_full_design')).read().strip())\n                health = round((cfull / cdes) * 100, 1)\n            except: pass\n        if power_w > 0.5:\n            try:\n                enow = 0; efull = 0\n                if os.path.exists(os.path.join(b, 'energy_now')):\n                    enow = int(open(os.path.join(b, 'energy_now')).read().strip()) / 1000000.0\n                    efull = int(open(os.path.join(b, 'energy_full')).read().strip()) / 1000000.0\n                elif os.path.exists(os.path.join(b, 'charge_now')):\n                    v_now = int(open(os.path.join(b, 'voltage_now')).read().strip()) / 1000000.0\n                    enow = (int(open(os.path.join(b, 'charge_now')).read().strip()) / 1000000.0) * v_now\n                    efull = (int(open(os.path.join(b, 'charge_full')).read().strip()) / 1000000.0) * v_now\n                if status.lower() == 'discharging' and enow > 0:\n                    hours = enow / power_w; h = int(hours); m = int((hours - h) * 60)\n                    time_str = f'{h}h {m}m left' if h > 0 else f'{m}m left'\n                elif status.lower() == 'charging' and efull > enow:\n                    hours = (efull - enow) / power_w; h = int(hours); m = int((hours - h) * 60)\n                    time_str = f'{h}h {m}m to full' if h > 0 else f'{m}m to full'\n            except: pass\n    prof = 'balanced'\n    try:\n        res = subprocess.run(['powerprofilesctl', 'get'], capture_output=True, text=True, timeout=1)\n        if res.returncode == 0 and res.stdout.strip(): prof = res.stdout.strip()\n    except: pass\n    return {'cap': cap, 'status': status, 'profile': prof, 'power_w': round(power_w, 1), 'health': health, 'time_str': time_str}\nprint(json.dumps(get_bat()))"]
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
                    if (obj.status) root.batStatus = obj.status;
                    if (obj.power_w !== undefined) root.batPowerW = obj.power_w;
                    if (obj.health !== undefined) root.batHealth = obj.health;
                    if (obj.time_str !== undefined) root.batTimeStr = obj.time_str;
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
