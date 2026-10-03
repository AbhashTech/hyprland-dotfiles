import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 460
    implicitHeight: Math.min(740, contentCol.implicitHeight + 36)
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property string activeTab: PluginManager.brightnessTab || "brightness"

    // Brightness state
    property int internalBrightness: 50
    property string internalLabel: "Laptop Screen"
    property bool internalAvailable: true
    property var externalMonitors: []
    property bool nightLightEnabled: false
    property string activeScreenName: ""
    property bool activeIsInternal: true

    // Resolution & Scaling state
    property var displayMonitors: []
    property int selectedMonitorIndex: 0
    property string saveStatusMsg: ""

    readonly property var currentMonitor: (displayMonitors && displayMonitors.length > selectedMonitorIndex) ? displayMonitors[selectedMonitorIndex] : (displayMonitors && displayMonitors.length > 0 ? displayMonitors[0] : null)

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

    function applyResolution(mode, scale) {
        if (!root.currentMonitor) return;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "set-resolution", root.currentMonitor.name, mode, scale.toString()]);
        refreshBrightness(false);
    }

    function applyScale(scale) {
        if (!root.currentMonitor) return;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "set-scale", root.currentMonitor.name, scale.toString()]);
        refreshBrightness(false);
    }

    function saveDisplayAsDefault() {
        if (!root.currentMonitor) return;
        var mon = root.currentMonitor;
        var currMode = mon.width + "x" + mon.height + "@" + mon.refreshRate;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/brightness/brightness_helper.py", "save-display", mon.name, currMode, mon.scale.toString()]);
        root.saveStatusMsg = "Saved default for " + mon.name + "!";
        saveTimer.restart();
    }

    function getAvailableModesModel() {
        if (!root.currentMonitor) return [];
        var modes = [];
        var currentModeStr = root.currentMonitor.width + "x" + root.currentMonitor.height;
        var currentRr = root.currentMonitor.refreshRate;

        // Auto preferred
        modes.push({
            mode: "preferred",
            label: "Auto Preferred (Hyprland Auto-detect)",
            isCurrent: false
        });

        // Current mode
        var currentFull = currentModeStr + "@" + currentRr.toFixed(2);
        modes.push({
            mode: currentFull,
            label: currentModeStr + " @ " + currentRr.toFixed(0) + "Hz (Current)",
            isCurrent: true
        });

        var rawModes = root.currentMonitor.availableModes || [];
        var added = {};
        added[currentFull] = true;
        added["preferred"] = true;

        for (var i = 0; i < rawModes.length; i++) {
            var m = rawModes[i];
            // Format: 1920x1080@60.00Hz
            var cleanMode = m.replace(/Hz$/i, "");
            if (!added[cleanMode] && modes.length < 10) {
                added[cleanMode] = true;
                modes.push({
                    mode: cleanMode,
                    label: m.replace("@", " @ "),
                    isCurrent: false
                });
            }
        }

        // Standard fallbacks if needed
        var standardResolutions = ["1920x1080@60", "1600x900@60", "1366x768@60", "1280x720@60"];
        for (var j = 0; j < standardResolutions.length; j++) {
            var sm = standardResolutions[j];
            if (!added[sm] && modes.length < 9) {
                added[sm] = true;
                modes.push({
                    mode: sm,
                    label: sm.replace("@", " @ ") + "Hz",
                    isCurrent: false
                });
            }
        }

        return modes;
    }

    Timer {
        id: saveTimer
        interval: 3500
        onTriggered: root.saveStatusMsg = ""
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
                    if (obj.active) {
                        root.activeScreenName = obj.active.name || "";
                        root.activeIsInternal = obj.active.is_internal !== undefined ? obj.active.is_internal : true;
                    }
                    if (obj.monitors && obj.monitors.length > 0) {
                        root.displayMonitors = obj.monitors;
                        // Select focused monitor if index is 0
                        if (root.selectedMonitorIndex >= obj.monitors.length) {
                            root.selectedMonitorIndex = 0;
                        }
                    }
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
        root.activeTab = PluginManager.brightnessTab || "brightness";
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
        function onBrightnessTabChanged() {
            root.activeTab = PluginManager.brightnessTab || "brightness";
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
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: root.activeTab === "brightness" ? "󰃠" : "󰍹"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge + 2
                color: Theme.yellow
            }

            Text {
                text: root.activeTab === "brightness" ? "Display & Brightness" : "Display Resolution & Scaling"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            // Rescan Monitors button
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
        // TAB SWITCHER (BRIGHTNESS / RESOLUTION & SCALING)
        // ==========================================
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 36
            radius: Theme.pillRadius
            color: Theme.surface0
            border.color: Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 3
                spacing: 4

                // Tab 1: Brightness
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: Theme.pillRadius - 2
                    color: root.activeTab === "brightness" ? Theme.accent : (brightTabHover.containsMouse ? Theme.surface1 : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: "󰃠"
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            color: root.activeTab === "brightness" ? Theme.mantle : Theme.text
                        }

                        Text {
                            text: "Brightness"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: root.activeTab === "brightness"
                            color: root.activeTab === "brightness" ? Theme.mantle : Theme.text
                        }
                    }

                    MouseArea {
                        id: brightTabHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeTab = "brightness";
                            PluginManager.brightnessTab = "brightness";
                        }
                    }
                }

                // Tab 2: Display Resolution & Scaling
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: Theme.pillRadius - 2
                    color: root.activeTab === "resolution" ? Theme.accent : (resTabHover.containsMouse ? Theme.surface1 : "transparent")

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 6

                        Text {
                            text: "󰍹"
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            color: root.activeTab === "resolution" ? Theme.mantle : Theme.text
                        }

                        Text {
                            text: "Resolution & Scaling"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: root.activeTab === "resolution"
                            color: root.activeTab === "resolution" ? Theme.mantle : Theme.text
                        }
                    }

                    MouseArea {
                        id: resTabHover
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeTab = "resolution";
                            PluginManager.brightnessTab = "resolution";
                        }
                    }
                }
            }
        }

        // ==========================================
        // TAB 1 CONTENT: BRIGHTNESS & DISPLAY
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: root.activeTab === "brightness"

            // INTERNAL DISPLAY CARD
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 112
                radius: 10
                color: Theme.surface0
                border.color: root.activeIsInternal ? Theme.yellow : Theme.moduleBorder
                border.width: root.activeIsInternal ? 2 : 1
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

                        Rectangle {
                            visible: root.activeIsInternal
                            implicitWidth: 84
                            implicitHeight: 20
                            radius: 4
                            color: Qt.rgba(Theme.yellow.r, Theme.yellow.g, Theme.yellow.b, 0.2)
                            border.color: Theme.yellow
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: "★ Active Screen"
                                font.family: Theme.fontFamily
                                font.pixelSize: 9
                                font.bold: true
                                color: Theme.yellow
                            }
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
                        id: intSlider
                        Layout.fillWidth: true
                        from: 1
                        to: 100
                        value: root.internalBrightness
                        onMoved: root.setInternalBrightness(Math.round(value))

                        background: Rectangle {
                            x: intSlider.leftPadding
                            y: intSlider.topPadding + intSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 6
                            width: intSlider.availableWidth
                            height: implicitHeight
                            radius: 3
                            color: Theme.surface2

                            Rectangle {
                                width: intSlider.visualPosition * parent.width
                                height: parent.height
                                color: Theme.yellow
                                radius: 3
                            }
                        }

                        handle: Rectangle {
                            x: intSlider.leftPadding + intSlider.visualPosition * (intSlider.availableWidth - width)
                            y: intSlider.topPadding + intSlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: intSlider.pressed ? Theme.text : Theme.yellow
                            border.color: Theme.crust
                            border.width: 2
                        }
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

            // EXTERNAL MONITORS
            Repeater {
                model: root.externalMonitors
                delegate: Rectangle {
                    id: extCard
                    Layout.fillWidth: true
                    implicitHeight: 176
                    radius: 10
                    color: Theme.surface0
                    border.color: (!root.activeIsInternal && root.activeScreenName === modelData.name) ? Theme.yellow : Theme.moduleBorder
                    border.width: (!root.activeIsInternal && root.activeScreenName === modelData.name) ? 2 : 1

                    property int extBrightness: modelData.brightness
                    property int extContrast: modelData.contrast

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                text: "󰍹"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeIcon
                                color: Theme.accent
                            }

                            Text {
                                text: modelData.model || ("External (" + modelData.name + ")")
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: Theme.text
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Rectangle {
                                visible: !root.activeIsInternal && root.activeScreenName === modelData.name
                                implicitWidth: 84
                                implicitHeight: 20
                                radius: 4
                                color: Qt.rgba(Theme.yellow.r, Theme.yellow.g, Theme.yellow.b, 0.2)
                                border.color: Theme.yellow
                                border.width: 1

                                Text {
                                    anchors.centerIn: parent
                                    text: "★ Active Screen"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: Theme.yellow
                                }
                            }

                            Text {
                                text: extCard.extBrightness + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: Theme.accent
                            }
                        }

                        // Brightness Slider
                        Slider {
                            id: extBrightSlider
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: extCard.extBrightness
                            onMoved: {
                                extCard.extBrightness = Math.round(value);
                                root.setExtBrightness(modelData.bus, Math.round(value));
                            }

                            background: Rectangle {
                                x: extBrightSlider.leftPadding
                                y: extBrightSlider.topPadding + extBrightSlider.availableHeight / 2 - height / 2
                                implicitWidth: 200
                                implicitHeight: 6
                                width: extBrightSlider.availableWidth
                                height: implicitHeight
                                radius: 3
                                color: Theme.surface2

                                Rectangle {
                                    width: extBrightSlider.visualPosition * parent.width
                                    height: parent.height
                                    color: Theme.accent
                                    radius: 3
                                }
                            }

                            handle: Rectangle {
                                x: extBrightSlider.leftPadding + extBrightSlider.visualPosition * (extBrightSlider.availableWidth - width)
                                y: extBrightSlider.topPadding + extBrightSlider.availableHeight / 2 - height / 2
                                implicitWidth: 16
                                implicitHeight: 16
                                radius: 8
                                color: extBrightSlider.pressed ? Theme.text : Theme.accent
                                border.color: Theme.crust
                                border.width: 2
                            }
                        }

                        // Contrast Row & Slider
                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                text: "󰃠 Contrast"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.subtext0
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                text: extCard.extContrast + "%"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                                color: Theme.subtext0
                            }
                        }

                        Slider {
                            id: extContrastSlider
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            value: extCard.extContrast
                            onMoved: {
                                extCard.extContrast = Math.round(value);
                                root.setExtContrast(modelData.bus, Math.round(value));
                            }

                            background: Rectangle {
                                x: extContrastSlider.leftPadding
                                y: extContrastSlider.topPadding + extContrastSlider.availableHeight / 2 - height / 2
                                implicitWidth: 200
                                implicitHeight: 6
                                width: extContrastSlider.availableWidth
                                height: implicitHeight
                                radius: 3
                                color: Theme.surface2

                                Rectangle {
                                    width: extContrastSlider.visualPosition * parent.width
                                    height: parent.height
                                    color: Theme.subtext0
                                    radius: 3
                                }
                            }

                            handle: Rectangle {
                                x: extContrastSlider.leftPadding + extContrastSlider.visualPosition * (extContrastSlider.availableWidth - width)
                                y: extContrastSlider.topPadding + extContrastSlider.availableHeight / 2 - height / 2
                                implicitWidth: 16
                                implicitHeight: 16
                                radius: 8
                                color: extContrastSlider.pressed ? Theme.text : Theme.subtext0
                                border.color: Theme.crust
                                border.width: 2
                            }
                        }
                    }
                }
            }

            // Fallback when no external monitor detected
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

            // NIGHT LIGHT TOGGLE
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

        // ==========================================
        // TAB 2 CONTENT: DISPLAY RESOLUTION & SCALING
        // ==========================================
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 12
            visible: root.activeTab === "resolution"

            // Monitor Selector (Multi-monitor pills)
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                visible: root.displayMonitors && root.displayMonitors.length > 1

                Repeater {
                    model: root.displayMonitors
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 32
                        radius: 6
                        color: root.selectedMonitorIndex === index ? Theme.accent : (monHover.containsMouse ? Theme.surface1 : Theme.surface0)
                        border.color: root.selectedMonitorIndex === index ? Theme.accent : Theme.moduleBorder
                        border.width: 1

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 6

                            Text {
                                text: modelData.is_internal ? "󰃟" : "󰍹"
                                font.family: Theme.fontFamily
                                font.pixelSize: 12
                                color: root.selectedMonitorIndex === index ? Theme.mantle : Theme.text
                            }

                            Text {
                                text: modelData.name + (modelData.focused ? " ★" : "")
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: root.selectedMonitorIndex === index
                                color: root.selectedMonitorIndex === index ? Theme.mantle : Theme.text
                            }
                        }

                        MouseArea {
                            id: monHover
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.selectedMonitorIndex = index
                        }
                    }
                }
            }

            // Monitor Status Card
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 64
                radius: 10
                color: Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    Rectangle {
                        implicitWidth: 40
                        implicitHeight: 40
                        radius: 8
                        color: Theme.surface1

                        Text {
                            anchors.centerIn: parent
                            text: (root.currentMonitor && root.currentMonitor.is_internal) ? "󰃟" : "󰍹"
                            font.family: Theme.fontFamily
                            font.pixelSize: 20
                            color: Theme.accent
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            text: root.currentMonitor ? (root.currentMonitor.model || root.currentMonitor.description || root.currentMonitor.name) : "Display"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.text
                            elide: Text.ElideRight
                        }

                        Text {
                            text: root.currentMonitor ? (root.currentMonitor.name + " • " + root.currentMonitor.width + "×" + root.currentMonitor.height + " @" + root.currentMonitor.refreshRate + "Hz") : ""
                            font.family: Theme.fontFamily
                            font.pixelSize: 10
                            color: Theme.subtext0
                        }
                    }

                    Rectangle {
                        implicitHeight: 24
                        implicitWidth: scaleBadgeText.implicitWidth + 14
                        radius: 4
                        color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.15)
                        border.color: Theme.accent
                        border.width: 1

                        Text {
                            id: scaleBadgeText
                            anchors.centerIn: parent
                            text: root.currentMonitor ? (Math.round(root.currentMonitor.scale * 100) + "% Scale") : "100% Scale"
                            font.family: Theme.fontFamily
                            font.pixelSize: 10
                            font.bold: true
                            color: Theme.accent
                        }
                    }
                }
            }

            // UI Scaling Card
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 114
                radius: 10
                color: Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: "󰁌"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeIcon
                            color: Theme.accent
                        }

                        Text {
                            text: "Display UI Scaling"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.text
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: root.currentMonitor ? (root.currentMonitor.scale.toFixed(2) + "x (" + Math.round(root.currentMonitor.scale * 100) + "%)") : "1.00x"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.accent
                        }
                    }

                    Slider {
                        id: scaleSlider
                        Layout.fillWidth: true
                        from: 0.5
                        to: 2.5
                        stepSize: 0.05
                        value: root.currentMonitor ? root.currentMonitor.scale : 1.0
                        onMoved: root.applyScale(Number(value.toFixed(2)))

                        background: Rectangle {
                            x: scaleSlider.leftPadding
                            y: scaleSlider.topPadding + scaleSlider.availableHeight / 2 - height / 2
                            implicitWidth: 200
                            implicitHeight: 6
                            width: scaleSlider.availableWidth
                            height: implicitHeight
                            radius: 3
                            color: Theme.surface2

                            Rectangle {
                                width: scaleSlider.visualPosition * parent.width
                                height: parent.height
                                color: Theme.accent
                                radius: 3
                            }
                        }

                        handle: Rectangle {
                            x: scaleSlider.leftPadding + scaleSlider.visualPosition * (scaleSlider.availableWidth - width)
                            y: scaleSlider.topPadding + scaleSlider.availableHeight / 2 - height / 2
                            implicitWidth: 16
                            implicitHeight: 16
                            radius: 8
                            color: scaleSlider.pressed ? Theme.text : Theme.accent
                            border.color: Theme.crust
                            border.width: 2
                        }
                    }

                    // Presets Row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Repeater {
                            model: [
                                { label: "1.00x", val: 1.0 },
                                { label: "1.25x", val: 1.25 },
                                { label: "1.50x", val: 1.50 },
                                { label: "1.75x", val: 1.75 },
                                { label: "2.00x", val: 2.00 }
                            ]
                            delegate: Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: 22
                                radius: 4
                                property bool isCurrent: root.currentMonitor && Math.abs(root.currentMonitor.scale - modelData.val) < 0.02
                                color: scalePresetMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface1
                                border.color: isCurrent ? Theme.accent : Theme.moduleBorder
                                border.width: isCurrent ? 2 : 1

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.label
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    font.bold: isCurrent
                                    color: isCurrent ? Theme.accent : Theme.text
                                }

                                MouseArea {
                                    id: scalePresetMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.applyScale(modelData.val)
                                }
                            }
                        }
                    }
                }
            }

            // Screen Resolution Card
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 175
                radius: 10
                color: Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: "🖥️"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                        }

                        Text {
                            text: "Resolution & Refresh Rate"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.text
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: "Click to apply"
                            font.family: Theme.fontFamily
                            font.pixelSize: 10
                            color: Theme.overlay0
                        }
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 4

                            Repeater {
                                model: root.getAvailableModesModel()
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 28
                                    radius: 5
                                    property bool isCurrent: modelData.isCurrent
                                    color: modeMouse.containsMouse ? Theme.moduleHoverBg : (isCurrent ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.12) : Theme.surface1)
                                    border.color: isCurrent ? Theme.accent : Theme.moduleBorder
                                    border.width: isCurrent ? 1.5 : 1

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        spacing: 8

                                        Text {
                                            text: isCurrent ? "●" : "○"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            color: isCurrent ? Theme.accent : Theme.overlay0
                                        }

                                        Text {
                                            text: modelData.label
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            font.bold: isCurrent
                                            color: isCurrent ? Theme.accent : Theme.text
                                            Layout.fillWidth: true
                                        }

                                        Rectangle {
                                            visible: isCurrent
                                            implicitWidth: 46
                                            implicitHeight: 16
                                            radius: 3
                                            color: Theme.accent

                                            Text {
                                                anchors.centerIn: parent
                                                text: "Active"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                font.bold: true
                                                color: Theme.mantle
                                            }
                                        }
                                    }

                                    MouseArea {
                                        id: modeMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.applyResolution(modelData.mode, root.currentMonitor ? root.currentMonitor.scale : 1.0)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Save Actions Card
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 38
                radius: Theme.pillRadius
                color: saveMouse.containsMouse ? Theme.moduleHoverBg : Theme.surface0
                border.color: Theme.moduleBorder
                border.width: 1

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    Text {
                        text: "💾"
                        font.family: Theme.fontFamily
                        font.pixelSize: 13
                    }

                    Text {
                        text: root.saveStatusMsg !== "" ? root.saveStatusMsg : "Save Configuration as Default (monitors.lua)"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: root.saveStatusMsg !== ""
                        color: root.saveStatusMsg !== "" ? Theme.green : Theme.text
                    }
                }

                MouseArea {
                    id: saveMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.saveDisplayAsDefault()
                }
            }
        }
    }
}
