import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 460
    implicitHeight: Math.min(640, contentCol.implicitHeight + 36)
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property int speakerVolume: 50
    property bool speakerMuted: false
    property string activeSinkName: "Speaker"
    
    property int micVolume: 50
    property bool micMuted: false
    property string activeSourceName: "Microphone"

    property var sinksList: []
    property var sourcesList: []
    property var appsList: []
    property string currentTab: "master" // "master", "devices", "apps"

    function refreshAudio() {
        if (!statusProc.running) statusProc.running = true;
    }

    function setSinkVolume(val) {
        root.speakerVolume = val;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "set-sink-vol", val.toString()]);
    }

    function toggleSinkMute() {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "toggle-sink-mute"]);
        root.refreshAudio();
    }

    function setSourceVolume(val) {
        root.micVolume = val;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "set-source-vol", val.toString()]);
    }

    function toggleSourceMute() {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "toggle-source-mute"]);
        root.refreshAudio();
    }

    function setDefaultSink(nameOrId) {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "set-default-sink", nameOrId.toString()]);
        refreshTimer.restart();
    }

    function setDefaultSource(nameOrId) {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "set-default-source", nameOrId.toString()]);
        refreshTimer.restart();
    }

    function setAppVolume(streamId, val) {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "set-app-vol", streamId.toString(), val.toString()]);
    }

    function toggleAppMute(streamId) {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "toggle-app-mute", streamId.toString()]);
        refreshTimer.restart();
    }

    function restartAudioServer() {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "restart"]);
        refreshTimer.restart();
    }

    Timer {
        id: refreshTimer
        interval: 300
        repeat: false
        onTriggered: root.refreshAudio()
    }

    Process {
        id: ctlProc
    }

    Process {
        id: statusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/volume/audio_helper.py", "get-all"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj.master_sink) {
                        root.speakerVolume = obj.master_sink.volume;
                        root.speakerMuted = obj.master_sink.muted;
                        root.activeSinkName = obj.master_sink.description;
                    }
                    if (obj.master_source) {
                        root.micVolume = obj.master_source.volume;
                        root.micMuted = obj.master_source.muted;
                        root.activeSourceName = obj.master_source.description;
                    }
                    root.sinksList = obj.sinks || [];
                    root.sourcesList = obj.sources || [];
                    root.appsList = obj.apps || [];
                } catch (e) {}
            }
        }
    }

    focus: true
    Keys.onEscapePressed: event => {
        PluginManager.closeAll();
        event.accepted = true;
    }

    function grabFocus() {
        root.forceActiveFocus();
        root.refreshAudio();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onVolumeVisibleChanged() {
            if (PluginManager.volumeVisible) {
                root.grabFocus();
            }
        }
    }

    Timer {
        interval: 2000
        running: PluginManager.volumeVisible
        repeat: true
        onTriggered: root.refreshAudio()
    }

    ColumnLayout {
        id: contentCol
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: "󰓃"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge + 2
                color: Theme.accent
            }

            Text {
                text: "Audio Control & Mixer"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            // Restart Audio Stack button in Header
            Rectangle {
                implicitWidth: 30
                implicitHeight: 30
                radius: 6
                color: restartHeaderArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰑐"
                    font.family: Theme.fontFamily
                    font.pixelSize: 14
                    color: restartHeaderArea.containsMouse ? Theme.peach : Theme.subtext0
                }

                MouseArea {
                    id: restartHeaderArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.restartAudioServer()
                }
            }

            Text {
                text: "Esc"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }

        // Navigation Tabs (Master / Devices / Apps)
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 36
            radius: 8
            color: Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 3
                spacing: 4

                // Tab 1: Master
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: root.currentTab === "master" ? Theme.accent : (tab1Area.containsMouse ? Theme.moduleHoverBg : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        Text {
                            text: "󰕾"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: root.currentTab === "master" ? Theme.barBg : Theme.text
                        }
                        Text {
                            text: "Master"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: root.currentTab === "master"
                            color: root.currentTab === "master" ? Theme.barBg : Theme.text
                        }
                    }

                    MouseArea {
                        id: tab1Area
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentTab = "master"
                    }
                }

                // Tab 2: Devices (Output & Input Switcher)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: root.currentTab === "devices" ? Theme.accent : (tab2Area.containsMouse ? Theme.moduleHoverBg : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        Text {
                            text: "󰡁"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: root.currentTab === "devices" ? Theme.barBg : Theme.text
                        }
                        Text {
                            text: "Devices (" + (root.sinksList.length + root.sourcesList.length) + ")"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: root.currentTab === "devices"
                            color: root.currentTab === "devices" ? Theme.barBg : Theme.text
                        }
                    }

                    MouseArea {
                        id: tab2Area
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentTab = "devices"
                    }
                }

                // Tab 3: Applications
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: root.currentTab === "apps" ? Theme.accent : (tab3Area.containsMouse ? Theme.moduleHoverBg : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        Text {
                            text: "󰓃"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: root.currentTab === "apps" ? Theme.barBg : Theme.text
                        }
                        Text {
                            text: "Apps (" + root.appsList.length + ")"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: root.currentTab === "apps"
                            color: root.currentTab === "apps" ? Theme.barBg : Theme.text
                        }
                    }

                    MouseArea {
                        id: tab3Area
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.currentTab = "apps"
                    }
                }
            }
        }

        // ==========================================
        // TAB 1: MASTER CONTROLS
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: root.currentTab === "master"

            // Speaker Output Card
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 88
                radius: 10
                color: Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: root.speakerMuted ? "󰝟" : (root.speakerVolume > 50 ? "󰕾" : "󰖀")
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeIcon
                            color: root.speakerMuted ? Theme.red : Theme.blue
                        }

                        ColumnLayout {
                            spacing: 1
                            Text {
                                text: "Speaker / Output"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: Theme.text
                            }
                            Text {
                                text: root.activeSinkName
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: Theme.subtext0
                                elide: Text.ElideRight
                                Layout.maximumWidth: 220
                            }
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: root.speakerMuted ? "MUTED" : root.speakerVolume + "%"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: root.speakerMuted ? Theme.red : Theme.accent
                        }

                        Rectangle {
                            implicitWidth: 58
                            implicitHeight: 24
                            radius: 4
                            color: root.speakerMuted ? Theme.red : (spkMuteArea.containsMouse ? Theme.moduleHoverBg : Theme.surface1)
                            border.color: Theme.moduleBorder
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: root.speakerMuted ? "Unmute" : "Mute"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: true
                                color: root.speakerMuted ? "#ffffff" : Theme.text
                            }

                            MouseArea {
                                id: spkMuteArea
                                anchors.fill: parent
                                hoverEnabled: true
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
            }

            // Microphone Input Card
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 88
                radius: 10
                color: Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: root.micMuted ? "󰍭" : "󰍬"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeIcon
                            color: root.micMuted ? Theme.red : Theme.green
                        }

                        ColumnLayout {
                            spacing: 1
                            Text {
                                text: "Microphone / Input"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: Theme.text
                            }
                            Text {
                                text: root.activeSourceName
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: Theme.subtext0
                                elide: Text.ElideRight
                                Layout.maximumWidth: 220
                            }
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
                            implicitWidth: 58
                            implicitHeight: 24
                            radius: 4
                            color: root.micMuted ? Theme.red : (micMuteArea.containsMouse ? Theme.moduleHoverBg : Theme.surface1)
                            border.color: Theme.moduleBorder
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: root.micMuted ? "Unmute" : "Mute"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: true
                                color: root.micMuted ? "#ffffff" : Theme.text
                            }

                            MouseArea {
                                id: micMuteArea
                                anchors.fill: parent
                                hoverEnabled: true
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
            }
        }

        // ==========================================
        // TAB 2: DEVICE SWITCHER (SINKS & SOURCES)
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: root.currentTab === "devices"

            Text {
                text: "󰕾 Output Devices (Select Active Sink)"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: Theme.accent
            }

            // Output Devices List
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: root.sinksList
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 38
                        radius: 8
                        color: modelData.is_default ? Theme.moduleActiveBg : (sinkMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface0)
                        border.color: modelData.is_default ? Theme.accent : Theme.moduleBorder
                        border.width: modelData.is_default ? 1.5 : 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 10

                            Text {
                                text: modelData.icon || "󰕾"
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
                                color: modelData.is_default ? Theme.accent : Theme.text
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.description
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: modelData.is_default
                                color: Theme.text
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.volume + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: Theme.subtext0
                            }

                            Text {
                                text: modelData.is_default ? "󰄬 Active" : "Select"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: modelData.is_default
                                color: modelData.is_default ? Theme.green : Theme.overlay0
                            }
                        }

                        MouseArea {
                            id: sinkMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.setDefaultSink(modelData.name || modelData.id)
                        }
                    }
                }
            }

            Text {
                Layout.topMargin: 6
                text: "󰍬 Input Devices (Select Active Microphone)"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: Theme.green
            }

            // Input Sources List
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: root.sourcesList
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 38
                        radius: 8
                        color: modelData.is_default ? Theme.moduleActiveBg : (srcMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface0)
                        border.color: modelData.is_default ? Theme.green : Theme.moduleBorder
                        border.width: modelData.is_default ? 1.5 : 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 10

                            Text {
                                text: modelData.icon || "󰍬"
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
                                color: modelData.is_default ? Theme.green : Theme.text
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.description
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: modelData.is_default
                                color: Theme.text
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.is_default ? "󰄬 Active" : "Select"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: modelData.is_default
                                color: modelData.is_default ? Theme.green : Theme.overlay0
                            }
                        }

                        MouseArea {
                            id: srcMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.setDefaultSource(modelData.name || modelData.id)
                        }
                    }
                }
            }
        }

        // ==========================================
        // TAB 3: APPLICATION STREAMS (PER-APP VOLUME)
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.currentTab === "apps"

            // Empty state if no apps
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 90
                radius: 8
                color: Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1
                visible: root.appsList.length === 0

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 6
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "󰓄"
                        font.family: Theme.fontFamily
                        font.pixelSize: 24
                        color: Theme.overlay0
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "No active audio streams playing"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.subtext0
                    }
                }
            }

            // List of per-app volume sliders
            Repeater {
                model: root.appsList
                delegate: Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 74
                    radius: 8
                    color: Theme.surface0
                    border.color: Theme.moduleBorder
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                text: modelData.icon || "󰓃"
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
                                color: Theme.accent
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: Theme.text
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.muted ? "MUTED" : modelData.volume + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: modelData.muted ? Theme.red : Theme.accent
                            }

                            Rectangle {
                                implicitWidth: 50
                                implicitHeight: 20
                                radius: 4
                                color: modelData.muted ? Theme.red : Theme.surface1
                                border.color: Theme.moduleBorder
                                border.width: 1

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.muted ? "Unmute" : "Mute"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: modelData.muted ? "#ffffff" : Theme.text
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.toggleAppMute(modelData.id)
                                }
                            }
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: modelData.volume
                            onMoved: root.setAppVolume(modelData.id, Math.round(value))
                        }
                    }
                }
            }
        }

        // ==========================================
        // FOOTER ACTIONS
        // ==========================================
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 34
            radius: Theme.pillRadius
            color: restartArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.centerIn: parent
                spacing: 6
                Text { text: "󰑐"; font.family: Theme.fontFamily; color: Theme.peach }
                Text { text: "Restart Audio Server (PipeWire)"; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSizeSmall; color: Theme.text }
            }

            MouseArea {
                id: restartArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.restartAudioServer()
            }
        }
    }
}
