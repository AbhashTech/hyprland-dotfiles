import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 420
    implicitHeight: 280
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property int speakerVolume: 50
    property bool speakerMuted: false
    property int micVolume: 50
    property bool micMuted: false

    function refreshAudio() {
        if (!statusProc.running) statusProc.running = true;
    }

    function setSinkVolume(val) {
        root.speakerVolume = val;
        ctlProc.exec(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", (val / 100).toFixed(2)]);
    }

    function toggleSinkMute() {
        ctlProc.exec(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]);
        root.refreshAudio();
    }

    function setSourceVolume(val) {
        root.micVolume = val;
        ctlProc.exec(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", (val / 100).toFixed(2)]);
    }

    function toggleSourceMute() {
        ctlProc.exec(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"]);
        root.refreshAudio();
    }

    Process {
        id: ctlProc
    }

    Process {
        id: statusProc
        command: ["python3", "-c", "import subprocess, json; s_vol = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], capture_output=True, text=True).stdout; m_vol = subprocess.run(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SOURCE@'], capture_output=True, text=True).stdout; sp = s_vol.split(); sv = int(float(sp[1])*100) if len(sp)>1 else 0; sm = '[MUTED]' in s_vol; mp = m_vol.split(); mv = int(float(mp[1])*100) if len(mp)>1 else 0; mm = '[MUTED]' in m_vol; print(json.dumps({'sv': sv, 'sm': sm, 'mv': mv, 'mm': mm}))"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    root.speakerVolume = obj.sv;
                    root.speakerMuted = obj.sm;
                    root.micVolume = obj.mv;
                    root.micMuted = obj.mm;
                } catch (e) {}
            }
        }
    }

    Component.onCompleted: root.refreshAudio()

    Connections {
        target: PluginManager
        function onVolumeVisibleChanged() {
            if (PluginManager.volumeVisible) {
                root.refreshAudio();
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
                text: " Volume & Audio Mixer"
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

        // Speaker Row
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: root.speakerMuted ? "󰝟" : (root.speakerVolume > 50 ? "󰕾" : "󰖀")
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon
                    color: root.speakerMuted ? Theme.red : Theme.blue
                }

                Text {
                    text: "Speaker Output"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.speakerMuted ? "MUTED" : root.speakerVolume + "%"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: root.speakerMuted ? Theme.red : Theme.accent
                }

                // Mute toggle button
                Rectangle {
                    implicitWidth: 54
                    implicitHeight: 22
                    radius: 4
                    color: root.speakerMuted ? Theme.red : Theme.surface0

                    Text {
                        anchors.centerIn: parent
                        text: root.speakerMuted ? "Unmute" : "Mute"
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        color: root.speakerMuted ? "#ffffff" : Theme.text
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleSinkMute()
                    }
                }
            }

            Slider {
                Layout.fillWidth: true
                from: 0
                to: 100
                value: root.speakerVolume
                onMoved: root.setSinkVolume(Math.round(value))
            }
        }

        // Microphone Row
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: root.micMuted ? "󰍭" : "󰍬"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon
                    color: root.micMuted ? Theme.red : Theme.green
                }

                Text {
                    text: "Microphone Input"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.micMuted ? "MUTED" : root.micVolume + "%"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: root.micMuted ? Theme.red : Theme.green
                }

                Rectangle {
                    implicitWidth: 54
                    implicitHeight: 22
                    radius: 4
                    color: root.micMuted ? Theme.red : Theme.surface0

                    Text {
                        anchors.centerIn: parent
                        text: root.micMuted ? "Unmute" : "Mute"
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        color: root.micMuted ? "#ffffff" : Theme.text
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleSourceMute()
                    }
                }
            }

            Slider {
                Layout.fillWidth: true
                from: 0
                to: 100
                value: root.micVolume
                onMoved: root.setSourceVolume(Math.round(value))
            }
        }

        // Audio Settings shortcut
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 32
            radius: Theme.pillRadius
            color: pavuArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.centerIn: parent
                spacing: 6
                Text { text: "󰓃"; font.family: Theme.fontFamily; color: Theme.accent }
                Text { text: "Open Advanced Mixer (pavucontrol)"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSizeSmall; color: Theme.text }
            }

            MouseArea {
                id: pavuArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    PluginManager.closeAll();
                    ctlProc.exec(["pavucontrol"]);
                }
            }
        }
    }
}
