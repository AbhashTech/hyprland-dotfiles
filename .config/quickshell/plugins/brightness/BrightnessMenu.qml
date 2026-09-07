import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 380
    implicitHeight: 220
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property int brightnessLevel: 50
    property bool nightLightEnabled: false

    function refreshBrightness() {
        if (!brightProc.running) brightProc.running = true;
    }

    function setBrightness(val) {
        root.brightnessLevel = val;
        ctlProc.exec(["brightnessctl", "set", val + "%"]);
    }

    function toggleNightLight() {
        root.nightLightEnabled = !root.nightLightEnabled;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/sunset_idle_manager.py", "--sunset-toggle"]);
    }

    Process {
        id: ctlProc
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
                            root.brightnessLevel = parseInt(parts[3].replace("%", ""), 10);
                        }
                    }
                } catch (e) {}
            }
        }
    }

    Component.onCompleted: root.refreshBrightness()

    Connections {
        target: PluginManager
        function onBrightnessVisibleChanged() {
            if (PluginManager.brightnessVisible) {
                root.refreshBrightness();
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
                text: "󰃠 Display & Brightness"
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

        // Slider Row
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: "󰃟"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon
                    color: Theme.yellow
                }

                Text {
                    text: "Screen Brightness"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.brightnessLevel + "%"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: Theme.yellow
                }
            }

            Slider {
                Layout.fillWidth: true
                from: 5
                to: 100
                value: root.brightnessLevel
                onMoved: root.setBrightness(Math.round(value))
            }
        }

        // Night Light Button
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 36
            radius: Theme.pillRadius
            color: nightArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
            border.color: root.nightLightEnabled ? Theme.peach : Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    text: "󰖔"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    color: root.nightLightEnabled ? Theme.peach : Theme.subtext0
                }

                Text {
                    text: "Toggle Warm Night Light"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: root.nightLightEnabled
                    color: root.nightLightEnabled ? Theme.peach : Theme.text
                }
            }

            MouseArea {
                id: nightArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.toggleNightLight()
            }
        }
    }
}
