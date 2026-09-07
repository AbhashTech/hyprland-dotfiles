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
        command: ["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/brightness-active.py"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj && obj.percentage !== undefined) {
                        root.brightness = obj.percentage;
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: netProc
        command: ["python3", "-c", "import subprocess, json; res = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL,DEVICE,TYPE', 'dev', 'wifi'], capture_output=True, text=True).stdout; lines = [l for l in res.splitlines() if l.startswith('yes:')]; print(json.dumps({'ssid': lines[0].split(':')[1] if lines else '', 'sig': lines[0].split(':')[2] if lines else '0'}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj.ssid) {
                        root.wifiText = "󰤨 " + obj.sig + "%";
                    } else {
                        root.wifiText = "󰤭";
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: btProc
        command: ["python3", "-c", "import subprocess, json; res = subprocess.run(['bluetoothctl', 'show'], capture_output=True, text=True).stdout; on = 'Powered: yes' in res; res2 = subprocess.run(['bluetoothctl', 'devices', 'Connected'], capture_output=True, text=True).stdout.strip(); count = len(res2.splitlines()) if res2 else 0; print(json.dumps({'on': on, 'count': count}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (!obj.on) {
                        root.btText = "󰂲";
                    } else if (obj.count > 0) {
                        root.btText = "󰂱 " + obj.count;
                    } else {
                        root.btText = "󰂯";
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: batProc
        command: ["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/battery-status.py"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj && obj.text) {
                        var cleaned = obj.text.replace(/<[^>]*>/g, "");
                        root.batText = cleaned;
                    }
                } catch (e) {}
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

        // Audio Item
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
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/volume_control.py", "mute"]);
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/sound-menu.sh"]);
                    } else if (mouse.button === Qt.MiddleButton) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/sound-menu.sh", "--tui"]);
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
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/brightness-menu.sh"]);
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/brightness-menu.sh", "--nightlight"]);
                    } else if (mouse.button === Qt.MiddleButton) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/brightness-menu.sh", "--tui"]);
                    }
                }

                onWheel: wheel => {
                    if (wheel.angleDelta.y > 0) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/brightness-menu.sh", "--up", "5"]);
                    } else if (wheel.angleDelta.y < 0) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/brightness-menu.sh", "--down", "5"]);
                    }
                }
            }
        }

        // Network Item
        Item {
            implicitWidth: netContent.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: netContent
                anchors.verticalCenter: parent.verticalCenter
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
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/network-menu.sh"]);
                }
            }
        }

        // Bluetooth Item
        Item {
            implicitWidth: btContent.implicitWidth
            implicitHeight: root.implicitHeight
            anchors.verticalCenter: parent.verticalCenter

            Row {
                id: btContent
                anchors.verticalCenter: parent.verticalCenter
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
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        ctlProc.exec(["bash", Quickshell.env("HOME") + "/.config/waybar/scripts/bluetooth-menu.sh"]);
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["rfkill", "toggle", "bluetooth"]);
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
                    ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/waybar/scripts/power-profile.py"]);
                }
            }
        }
    }
}
