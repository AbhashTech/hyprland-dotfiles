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
    property int brightness: 50
    property string wifiText: "󰤨"
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
        command: ["python3", "-c", "import subprocess, json; res = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], capture_output=True, text=True).stdout.strip(); parts = res.split(); vol = int(float(parts[1])*100) if len(parts) > 1 else 0; muted = '[MUTED]' in res; print(json.dumps({'vol': vol, 'muted': muted}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.volume = obj.vol;
                    root.muted = obj.muted;
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
        command: ["python3", "-c", "import subprocess, json\nssid = ''\nsig = 0\ntry:\n    # Try nmcli first\n    res = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL', 'dev', 'wifi'], capture_output=True, text=True).stdout\n    lines = [l for l in res.splitlines() if l.startswith('yes:')]\n    if lines:\n        ssid = lines[0].split(':')[1]\n        sig = int(lines[0].split(':')[2] or 0)\nexcept Exception:\n    pass\nif not ssid:\n    try:\n        # Fallback to iwctl / iwd\n        res = subprocess.run(['iwctl', 'station', 'wlan0', 'show'], capture_output=True, text=True).stdout\n        for l in res.splitlines():\n            if 'Connected network' in l:\n                ssid = l.split('Connected network')[-1].strip()\n            if 'RSSI' in l and not sig:\n                try:\n                    rssi_val = int(l.split('RSSI')[-1].strip().split()[0])\n                    # Convert dBm to approx percentage (e.g. -50 dBm -> ~80%)\n                    sig = max(0, min(100, int(2 * (rssi_val + 100))))\n                except Exception:\n                    sig = 75\n    except Exception:\n        pass\nprint(json.dumps({'ssid': ssid, 'sig': sig}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj && obj.ssid) {
                        var sig = parseInt(obj.sig || "0", 10);
                        if (sig >= 75) root.wifiText = "󰤨";
                        else if (sig >= 50) root.wifiText = "󰤥";
                        else if (sig >= 25) root.wifiText = "󰤢";
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
                title: "Audio Volume"
                description: root.muted ? "Audio is currently Muted" : ("Level: " + root.volume + "%")
                shortcuts: [
                    { action: "Toggle Mute", key: "Left Click" },
                    { action: "Audio Mixer Menu", key: "SUPER + SHIFT + A" },
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
                iconColor: Theme.teal
                title: "Wireless Network"
                description: "Wi-Fi connections & network manager"
                shortcuts: [
                    { action: "Wi-Fi Control Center", key: "SUPER + CTRL + W" },
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
