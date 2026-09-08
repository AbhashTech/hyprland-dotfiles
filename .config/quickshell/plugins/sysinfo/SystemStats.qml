import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 440
    implicitHeight: 340
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property int cpuUsage: 0
    property int memUsage: 0
    property string memText: ""
    property int diskUsage: 0
    property string diskText: ""
    property string tempText: "45°C"

    function refreshStats() {
        if (!statsProc.running) statsProc.running = true;
    }

    Process {
        id: ctlProc
    }

    Process {
        id: statsProc
        command: ["python3", "-c", "import os, time, json\ncpu = 0\ntry:\n    with open('/proc/stat') as f:\n        fields = [float(x) for x in f.readline().strip().split()[1:]]\n    idle1, total1 = fields[3], sum(fields)\n    time.sleep(0.05)\n    with open('/proc/stat') as f:\n        fields2 = [float(x) for x in f.readline().strip().split()[1:]]\n    idle2, total2 = fields2[3], sum(fields2)\n    idle_d, total_d = idle2 - idle1, total2 - total1\n    cpu = int(max(0, min(100, (1.0 - idle_d / total_d) * 100))) if total_d else 0\nexcept Exception:\n    pass\n\nmem_pct = 0\nmem_txt = ''\ntry:\n    meminfo = {}\n    with open('/proc/meminfo') as f:\n        for line in f:\n            parts = line.split(':')\n            if len(parts) == 2:\n                meminfo[parts[0].strip()] = int(parts[1].split()[0]) * 1024\n    total_m = meminfo.get('MemTotal', 1)\n    avail_m = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))\n    used_m = max(0, total_m - avail_m)\n    mem_pct = int((used_m / total_m) * 100)\n    mem_txt = f'{used_m/(1024**3):.1f}/{total_m/(1024**3):.1f} GB'\nexcept Exception:\n    pass\n\ndisk_pct = 0\ndisk_txt = ''\ntry:\n    vfs = os.statvfs('/')\n    total_d = vfs.f_blocks * vfs.f_frsize\n    free_d = vfs.f_bavail * vfs.f_frsize\n    used_d = max(0, total_d - free_d)\n    disk_pct = int((used_d / total_d) * 100) if total_d else 0\n    disk_txt = f'{used_d/(1024**3):.0f}/{total_d/(1024**3):.0f} GB'\nexcept Exception:\n    pass\n\nprint(json.dumps({'cpu': cpu, 'mem_pct': mem_pct, 'mem_txt': mem_txt, 'disk_pct': disk_pct, 'disk_txt': disk_txt}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.cpuUsage = obj.cpu;
                    root.memUsage = obj.mem_pct;
                    root.memText = obj.mem_txt;
                    root.diskUsage = obj.disk_pct;
                    root.diskText = obj.disk_txt;
                } catch (e) {}
            }
        }
    }

    Timer {
        interval: 2000
        running: PluginManager.sysinfoVisible
        repeat: true
        onTriggered: root.refreshStats()
    }

    focus: true
    Keys.onEscapePressed: event => {
        PluginManager.closeAll();
        event.accepted = true;
    }

    function grabFocus() {
        root.forceActiveFocus();
        root.refreshStats();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onSysinfoVisibleChanged() {
            if (PluginManager.sysinfoVisible) {
                root.grabFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 16

        // Header
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "󰍛 System Resources"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }

        // Metrics Rows
        // CPU
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4

            RowLayout {
                Layout.fillWidth: true
                Text { text: "󰘚 CPU Usage"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSize; color: Theme.text }
                Item { Layout.fillWidth: true }
                Text { text: root.cpuUsage + "%"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSizeSmall; font.bold: true; color: root.cpuUsage > 80 ? Theme.red : Theme.blue }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 8
                radius: 4
                color: Theme.surface0
                Rectangle {
                    width: parent.width * (root.cpuUsage / 100)
                    height: parent.height
                    radius: 4
                    color: root.cpuUsage > 80 ? Theme.red : Theme.blue

                    Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutQuad } }
                    Behavior on color { ColorAnimation { duration: 250 } }
                }
            }
        }

        // Memory
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4

            RowLayout {
                Layout.fillWidth: true
                Text { text: "󰍛 Memory (RAM)"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSize; color: Theme.text }
                Item { Layout.fillWidth: true }
                Text { text: root.memText + " (" + root.memUsage + "%)"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSizeSmall; font.bold: true; color: root.memUsage > 85 ? Theme.red : Theme.mauve }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 8
                radius: 4
                color: Theme.surface0
                Rectangle {
                    width: parent.width * (root.memUsage / 100)
                    height: parent.height
                    radius: 4
                    color: root.memUsage > 85 ? Theme.red : Theme.mauve

                    Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutQuad } }
                    Behavior on color { ColorAnimation { duration: 250 } }
                }
            }
        }

        // Disk
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4

            RowLayout {
                Layout.fillWidth: true
                Text { text: "󰋊 Root Storage"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSize; color: Theme.text }
                Item { Layout.fillWidth: true }
                Text { text: root.diskText + " (" + root.diskUsage + "%)"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSizeSmall; font.bold: true; color: root.diskUsage > 90 ? Theme.red : Theme.green }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 8
                radius: 4
                color: Theme.surface0
                Rectangle {
                    width: parent.width * (root.diskUsage / 100)
                    height: parent.height
                    radius: 4
                    color: root.diskUsage > 90 ? Theme.red : Theme.green

                    Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutQuad } }
                    Behavior on color { ColorAnimation { duration: 250 } }
                }
            }
        }

        // Btop Launcher Button
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 38
            radius: Theme.pillRadius
            color: btopArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.centerIn: parent
                spacing: 8
                Text { text: "󰢮"; font.family: Theme.fontFamily; color: Theme.accent }
                Text { text: "Open Btop System Monitor (TUI)"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSize; color: Theme.text }
            }

            MouseArea {
                id: btopArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    PluginManager.closeAll();
                    ctlProc.exec(["kitty", "--class", "btop", "-e", "btop"]);
                }
            }
        }
    }
}
