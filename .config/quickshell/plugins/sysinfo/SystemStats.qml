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
        command: ["python3", "-c", "import os, json\ncpu = 0; mem_pct = 0; mem_txt = ''; disk_pct = 0; disk_txt = ''\ntry:\n    import psutil\n    cpu = int(psutil.cpu_percent())\n    mem = psutil.virtual_memory()\n    mem_pct = int(mem.percent)\n    mem_txt = f'{mem.used/(1024**3):.1f}/{mem.total/(1024**3):.1f} GB'\n    disk = psutil.disk_usage('/')\n    disk_pct = int(disk.percent)\n    disk_txt = f'{disk.used/(1024**3):.0f}/{disk.total/(1024**3):.0f} GB'\nexcept Exception:\n    try:\n        # Fallback to /proc & os.statvfs\n        vfs = os.statvfs('/')\n        total_d = vfs.f_blocks * vfs.f_frsize\n        free_d = vfs.f_bavail * vfs.f_frsize\n        used_d = total_d - free_d\n        disk_pct = int((used_d / total_d) * 100) if total_d else 0\n        disk_txt = f'{used_d/(1024**3):.0f}/{total_d/(1024**3):.0f} GB'\n        meminfo = {}\n        for line in open('/proc/meminfo'):\n            parts = line.split(':')\n            if len(parts) == 2:\n                meminfo[parts[0].strip()] = int(parts[1].split()[0]) * 1024\n        total_m = meminfo.get('MemTotal', 1)\n        avail_m = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))\n        used_m = total_m - avail_m\n        mem_pct = int((used_m / total_m) * 100)\n        mem_txt = f'{used_m/(1024**3):.1f}/{total_m/(1024**3):.1f} GB'\n    except Exception:\n        pass\nprint(json.dumps({'cpu': cpu, 'mem_pct': mem_pct, 'mem_txt': mem_txt, 'disk_pct': disk_pct, 'disk_txt': disk_txt}))"]
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
