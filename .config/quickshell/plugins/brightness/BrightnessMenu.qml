import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 440
    implicitHeight: Math.min(720, contentCol.implicitHeight + 36)
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property int internalBrightness: 50
    property string internalLabel: "Laptop Screen"
    property bool internalAvailable: true
    property var externalMonitors: []
    property bool nightLightEnabled: false

    function refreshBrightness(rescan) {
        if (!brightProc.running) {
            brightProc.command = ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", rescan ? "rescan" : "get-all"];
            brightProc.running = true;
        }
    }

    function setInternalBrightness(val) {
        root.internalBrightness = val;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "set-internal", val.toString()]);
    }

    function setExtBrightness(bus, val) {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "set-ext-brightness", bus.toString(), val.toString()]);
    }

    function setExtContrast(bus, val) {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "set-ext-contrast", bus.toString(), val.toString()]);
    }

    function toggleNightLight() {
        root.nightLightEnabled = !root.nightLightEnabled;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "toggle-nightlight"]);
    }

    Process {
        id: ctlProc
    }

    Process {
        id: brightProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "get-all"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    var obj = JSON.parse(data);
                    if (obj.internal) {
                        root.internalAvailable = obj.internal.available;
                        root.internalBrightness = obj.internal.brightness;
                        root.internalLabel = obj.internal.label;
                    }
                    root.externalMonitors = obj.external || [];
                    root.nightLightEnabled = obj.night_light || false;
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
        root.refreshBrightness(false);
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onBrightnessVisibleChanged() {
            if (PluginManager.brightnessVisible) {
                root.grabFocus();
            }
        }
    }

    Timer {
        interval: 3000
        running: PluginManager.brightnessVisible
        repeat: true
        onTriggered: root.refreshBrightness(false)
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
                text: "󰃠"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge + 2
                color: Theme.yellow
            }

            Text {
                text: "Display & Brightness"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            // Rescan DDC Monitors button
            Rectangle {
                implicitWidth: 30
                implicitHeight: 30
                radius: 6
                color: rescanArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰑐"
                    font.family: Theme.fontFamily
                    font.pixelSize: 14
                    color: rescanArea.containsMouse ? Theme.yellow : Theme.subtext0
                }

                MouseArea {
                    id: rescanArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.refreshBrightness(true)
                }
            }

            Text {
                text: "Esc"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }

        // ==========================================
        // INTERNAL DISPLAY CARD
        // ==========================================
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 112
            radius: 10
            color: Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1
            visible: root.internalAvailable

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
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
                        text: root.internalLabel
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: true
                        color: Theme.text
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: root.internalBrightness + "%"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: true
                        color: Theme.yellow
                    }
                }

                Slider {
                    Layout.fillWidth: true
                    from: 1
                    to: 100
                    value: root.internalBrightness
                    onMoved: root.setInternalBrightness(Math.round(value))
                }

                // Presets Row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Repeater {
                        model: [25, 50, 75, 100]
                        delegate: Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 22
                            radius: 4
                            color: presetMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface1
                            border.color: root.internalBrightness === modelData ? Theme.yellow : Theme.moduleBorder
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: modelData + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: root.internalBrightness === modelData
                                color: root.internalBrightness === modelData ? Theme.yellow : Theme.text
                            }

                            MouseArea {
                                id: presetMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.setInternalBrightness(modelData)
                            }
                        }
                    }
                }
            }
        }

        // ==========================================
        // EXTERNAL MONITORS (DDC/CI)
        // ==========================================
        Repeater {
            model: root.externalMonitors
            delegate: Rectangle {
                id: extCard
                Layout.fillWidth: true
                implicitHeight: extCol.implicitHeight + 24
                radius: 10
                color: Theme.surface0
                border.color: Theme.blue
                border.width: 1

                property int monitorBus: modelData.bus
                property int liveBrightness: modelData.brightness
                property int liveContrast: modelData.contrast

                ColumnLayout {
                    id: extCol
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    // Monitor Header
                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: "󰡁"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeIcon
                            color: Theme.blue
                        }

                        Text {
                            text: modelData.model + " (DDC/CI)"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.text
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            implicitWidth: 62
                            implicitHeight: 20
                            radius: 4
                            color: Theme.moduleActiveBg
                            Text {
                                anchors.centerIn: parent
                                text: "I2C Bus " + extCard.monitorBus
                                font.family: Theme.fontFamily
                                font.pixelSize: 9
                                color: Theme.accent
                            }
                        }
                    }

                    // Brightness Slider & Presets Row
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "󰃟 Brightness"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: Theme.subtext0
                            }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: extCard.liveBrightness + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: Theme.yellow
                            }
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: extCard.liveBrightness
                            onMoved: {
                                extCard.liveBrightness = Math.round(value);
                                root.setExtBrightness(extCard.monitorBus, Math.round(value));
                            }
                        }

                        // External Brightness Presets
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Repeater {
                                model: [25, 50, 75, 100]
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 22
                                    radius: 4
                                    color: extBPresetMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface1
                                    border.color: extCard.liveBrightness === modelData ? Theme.yellow : Theme.moduleBorder
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData + "%"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        font.bold: extCard.liveBrightness === modelData
                                        color: extCard.liveBrightness === modelData ? Theme.yellow : Theme.text
                                    }

                                    MouseArea {
                                        id: extBPresetMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            extCard.liveBrightness = modelData;
                                            root.setExtBrightness(extCard.monitorBus, modelData);
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Contrast Slider & Presets Row
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: "󰹑 Contrast"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: Theme.subtext0
                            }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: extCard.liveContrast + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: Theme.teal
                            }
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: extCard.liveContrast
                            onMoved: {
                                extCard.liveContrast = Math.round(value);
                                root.setExtContrast(extCard.monitorBus, Math.round(value));
                            }
                        }

                        // External Contrast Presets
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Repeater {
                                model: [25, 50, 75, 100]
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 22
                                    radius: 4
                                    color: extCPresetMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface1
                                    border.color: extCard.liveContrast === modelData ? Theme.teal : Theme.moduleBorder
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData + "%"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        font.bold: extCard.liveContrast === modelData
                                        color: extCard.liveContrast === modelData ? Theme.teal : Theme.text
                                    }

                                    MouseArea {
                                        id: extCPresetMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            extCard.liveContrast = modelData;
                                            root.setExtContrast(extCard.monitorBus, modelData);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Placeholder if no external monitor detected
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 46
            radius: 8
            color: Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1
            visible: root.externalMonitors.length === 0

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Text {
                    text: "󰍹"
                    font.family: Theme.fontFamily
                    font.pixelSize: 16
                    color: Theme.overlay0
                }

                Text {
                    text: "No external DDC/CI monitor detected"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.subtext0
                    Layout.fillWidth: true
                }

                Rectangle {
                    implicitWidth: 64
                    implicitHeight: 22
                    radius: 4
                    color: Theme.surface1
                    border.color: Theme.moduleBorder
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "Rescan"
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        color: Theme.text
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.refreshBrightness(true)
                    }
                }
            }
        }

        // ==========================================
        // NIGHT LIGHT (WARM FILTER)
        // ==========================================
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 38
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
                    text: root.nightLightEnabled ? "Warm Night Light (Active)" : "Toggle Warm Night Light"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
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
