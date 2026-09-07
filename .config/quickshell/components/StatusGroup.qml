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

    property int volume: 50
    property bool muted: false
    property int brightness: 50
    property string wifiText: "󰤨"
    property string btText: "󰂯"
    property string batText: "󰁹 100%"

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
        command: ["brightnessctl", "-m"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var lines = data.trim().split("\n");
                    if (lines.length > 0) {
                        var parts = lines[0].split(",");
                        if (parts.length >= 4) {
                            root.brightness = parseInt(parts[3].replace("%", ""), 10);
                        }
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
        command: ["python3", "-c", "import glob, os, json; bats = glob.glob('/sys/class/power_supply/BAT*'); cap = 100; status = 'Full';\nif bats:\n    b = bats[0]\n    try:\n        cap = int(open(b + '/capacity').read().strip())\n        status = open(b + '/status').read().strip()\n    except: pass\nprint(json.dumps({'cap': cap, 'status': status}))"]
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
                    root.batText = icon + " " + cap + "%";
                } catch (e) {
                    root.batText = "󰁹 100%";
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
        spacing: 12

        // Volume Item
        Item {
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

            MouseArea {
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

            MouseArea {
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
                    if (wheel.angleDelta.y > 0) {
                        ctlProc.exec(["brightnessctl", "set", "+5%"]);
                    } else if (wheel.angleDelta.y < 0) {
                        ctlProc.exec(["brightnessctl", "set", "5%-"]);
                    }
                }
            }
        }

        // Network Item
        Rectangle {
            implicitWidth: Math.max(22, netContent.implicitWidth + 8)
            implicitHeight: root.implicitHeight
            radius: 4
            color: netArea.containsMouse ? Theme.moduleActiveBg : "transparent"
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: netContent
                anchors.centerIn: parent
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.wifiText
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.teal
                }
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
        Rectangle {
            implicitWidth: Math.max(22, btContent.implicitWidth + 8)
            implicitHeight: root.implicitHeight
            radius: 4
            color: btArea.containsMouse ? Theme.moduleActiveBg : "transparent"
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: btContent
                anchors.centerIn: parent
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.btText
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.blue
                }
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
            implicitWidth: batContent.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: batContent
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.batText
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.green
                }
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
                }
            }
        }
    }
}
