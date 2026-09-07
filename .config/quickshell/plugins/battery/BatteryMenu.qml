import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 380
    implicitHeight: 320
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property string currentProfile: PluginManager.powerProfile
    property int batteryCap: 100
    property string batteryStatus: "Full"
    property double powerWatt: 0.0
    property double batteryHealth: 100.0

    readonly property var profiles: [
        {
            id: "power-saver",
            name: "Powersave",
            icon: "󰾆",
            color: Theme.green,
            desc: "Reduces power, quieter fan & cooler temps"
        },
        {
            id: "balanced",
            name: "Balanced",
            icon: "󰾅",
            color: Theme.blue,
            desc: "Standard dynamic scaling & power balance"
        },
        {
            id: "performance",
            name: "Performance",
            icon: "󰓅",
            color: Theme.peach,
            desc: "Max CPU performance, faster responsiveness"
        }
    ]

    function refreshProfile() {
        if (!profileProc.running) profileProc.running = true;
        if (!batDetailsProc.running) batDetailsProc.running = true;
    }

    function setProfile(profileId) {
        root.currentProfile = profileId;
        PluginManager.setPowerProfile(profileId);
        ctlProc.exec(["powerprofilesctl", "set", profileId]);
        refreshTimer.restart();
    }

    Timer {
        id: refreshTimer
        interval: 300
        repeat: false
        onTriggered: root.refreshProfile()
    }

    Process {
        id: ctlProc
    }

    Process {
        id: profileProc
        command: ["powerprofilesctl", "get"]
        stdout: SplitParser {
            onRead: data => {
                var p = data.trim();
                if (p.length > 0) {
                    root.currentProfile = p;
                    PluginManager.setPowerProfile(p);
                }
            }
        }
    }

    Process {
        id: batDetailsProc
        command: ["python3", "-c", "import glob, json\nbats = glob.glob('/sys/class/power_supply/BAT*')\ncap = 100; status = 'Unknown'; power_w = 0.0; health = 100.0\nif bats:\n    b = bats[0]\n    try: cap = int(open(b + '/capacity').read().strip())\n    except: pass\n    try: status = open(b + '/status').read().strip()\n    except: pass\n    try:\n        power_now = int(open(b + '/power_now').read().strip())\n        power_w = power_now / 1000000.0\n    except:\n        try:\n            current_now = int(open(b + '/current_now').read().strip())\n            voltage_now = int(open(b + '/voltage_now').read().strip())\n            power_w = (current_now * voltage_now) / 1e12\n        except: pass\n    try:\n        efull = int(open(b + '/energy_full').read().strip())\n        edes = int(open(b + '/energy_full_design').read().strip())\n        health = round((efull / edes) * 100, 1)\n    except:\n        try:\n            cfull = int(open(b + '/charge_full').read().strip())\n            cdes = int(open(b + '/charge_full_design').read().strip())\n            health = round((cfull / cdes) * 100, 1)\n        except: pass\nprint(json.dumps({'cap': cap, 'status': status, 'power_w': round(power_w, 1), 'health': health}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.batteryCap = obj.cap;
                    root.batteryStatus = obj.status;
                    root.powerWatt = obj.power_w;
                    root.batteryHealth = obj.health;
                } catch (e) {}
            }
        }
    }

    Timer {
        interval: 3000
        running: PluginManager.batteryVisible
        repeat: true
        onTriggered: root.refreshProfile()
    }

    focus: true
    Keys.onEscapePressed: event => {
        PluginManager.closeAll();
        event.accepted = true;
    }

    Keys.onDigit1Pressed: root.setProfile("power-saver")
    Keys.onDigit2Pressed: root.setProfile("balanced")
    Keys.onDigit3Pressed: root.setProfile("performance")

    function grabFocus() {
        root.forceActiveFocus();
        root.refreshProfile();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onBatteryVisibleChanged() {
            if (PluginManager.batteryVisible) {
                root.grabFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14

        // Header
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "󰁹 Battery & Power"
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

        // Battery Status Info Capsule
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 46
            radius: Theme.pillRadius
            color: Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 12

                // State & percentage
                Row {
                    spacing: 6
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.batteryStatus === "Charging" ? "󰂄" : "󰁹"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeIcon
                        color: root.batteryStatus === "Charging" ? Theme.yellow : Theme.green
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.batteryCap + "% (" + root.batteryStatus + ")"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        color: Theme.text
                    }
                }

                Item { Layout.fillWidth: true }

                // Stats: Health & Wattage
                Row {
                    spacing: 10
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "󰚥 " + root.batteryHealth + "%"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.subtext0
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: root.powerWatt > 0
                        text: "󱐋 " + root.powerWatt + "W"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.peach
                    }
                }
            }
        }

        // Section Label
        Text {
            text: "Power Profile"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall
            font.bold: true
            color: Theme.subtext0
        }

        // Profile Cards List
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: root.profiles

                Rectangle {
                    id: profileCard
                    required property var modelData
                    required property int index

                    Layout.fillWidth: true
                    implicitHeight: 44
                    radius: Theme.pillRadius

                    readonly property bool isActive: root.currentProfile === modelData.id
                    readonly property bool isHovered: cardMouseArea.containsMouse

                    color: isActive ? Theme.moduleActiveBg : (isHovered ? Theme.moduleHoverBg : Theme.surface0)
                    border.color: isActive ? modelData.color : (isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder)
                    border.width: isActive ? 2 : 1

                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 12

                        // Profile Icon
                        Text {
                            text: modelData.icon
                            font.family: Theme.fontFamily
                            font.pixelSize: 20
                            color: profileCard.isActive ? modelData.color : Theme.subtext0
                        }

                        // Profile details
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                text: modelData.name
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold: true
                                color: profileCard.isActive ? Theme.text : Theme.subtext1
                            }

                            Text {
                                text: modelData.desc
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: Theme.overlay1
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }

                        // Active badge / check
                        Rectangle {
                            implicitWidth: 18
                            implicitHeight: 18
                            radius: 9
                            color: profileCard.isActive ? modelData.color : "transparent"
                            border.color: profileCard.isActive ? modelData.color : Theme.surface2
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                visible: profileCard.isActive
                                text: "✓"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: Theme.crust
                            }
                        }
                    }

                    MouseArea {
                        id: cardMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.setProfile(modelData.id)
                    }
                }
            }
        }
    }
}
