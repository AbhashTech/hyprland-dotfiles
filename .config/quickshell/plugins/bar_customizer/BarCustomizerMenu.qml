import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import "../.."
import "../../components"

Rectangle {
    id: root

    implicitWidth: 860
    implicitHeight: 660
    width: implicitWidth
    height: implicitHeight
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property string currentTab: "layout" // "layout" | "appearance" | "presets" | "catalog"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                width: 38
                height: 38
                radius: Theme.capsuleRadius
                color: Theme.moduleActiveBg
                Text {
                    anchors.centerIn: parent
                    text: "󰏖"
                    font.family: Theme.fontFamily
                    font.pixelSize: 20
                    color: Theme.mauve
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Status Bar Customizer"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    color: Theme.text
                }
                Text {
                    text: "Move widgets dynamically across sections, customize geometry, and switch presets"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.subtext0
                }
            }

            Item { Layout.fillWidth: true }

            // Live Edit Mode Button
            Rectangle {
                implicitHeight: 32
                implicitWidth: liveRow.implicitWidth + 20
                radius: 16
                color: BarConfig.editMode ? Theme.teal : (liveArea.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg)
                border.color: BarConfig.editMode ? Theme.teal : Theme.moduleBorder
                border.width: 1

                Row {
                    id: liveRow
                    anchors.centerIn: parent
                    spacing: 6
                    Text {
                        text: BarConfig.editMode ? "✓" : "✏"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        font.bold: true
                        color: BarConfig.editMode ? "#ffffff" : Theme.teal
                    }
                    Text {
                        text: BarConfig.editMode ? "Exit Live Edit" : "Live Bar Edit Mode"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        font.bold: true
                        color: BarConfig.editMode ? "#ffffff" : Theme.text
                    }
                }

                MouseArea {
                    id: liveArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: BarConfig.toggleEditMode()
                }
            }

            // Close Button
            Rectangle {
                width: 32
                height: 32
                radius: 16
                color: closeArea.containsMouse ? Theme.red : Theme.moduleBg
                border.color: Theme.moduleBorder
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    font.bold: true
                    color: closeArea.containsMouse ? "#ffffff" : Theme.subtext0
                }

                MouseArea {
                    id: closeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManager.toggle("bar_customizer")
                }
            }
        }

        // Tab Navigation Bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            TabButton {
                tabId: "layout"
                tabIcon: "󰆊"
                tabTitle: "Layout & Arrangement"
                isActive: root.currentTab === "layout"
                onClicked: root.currentTab = "layout"
            }

            TabButton {
                tabId: "appearance"
                tabIcon: "󰔎"
                tabTitle: "Appearance & Geometry"
                isActive: root.currentTab === "appearance"
                onClicked: root.currentTab = "appearance"
            }

            TabButton {
                tabId: "presets"
                tabIcon: "󰓅"
                tabTitle: "Layout Presets"
                isActive: root.currentTab === "presets"
                onClicked: root.currentTab = "presets"
            }

            TabButton {
                tabId: "catalog"
                tabIcon: "󰄲"
                tabTitle: "All Modules (" + BarConfig.moduleCatalog.length + ")"
                isActive: root.currentTab === "catalog"
                onClicked: root.currentTab = "catalog"
            }

            Item { Layout.fillWidth: true }
        }

        // Main Tab Content Area
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.capsuleRadius
            color: Theme.crust
            border.color: Theme.moduleBorder
            border.width: 1
            clip: true

            // ── Tab 1: Layout & Arrangement ──────────────────────────────────────────
            Item {
                anchors.fill: parent
                anchors.margins: 12
                visible: root.currentTab === "layout"

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10

                    // 3 Sections Row
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 10

                        // Left Section Column
                        SectionColumn {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            sectionTitle: "LEFT SECTION"
                            sectionName: "left"
                            accentColor: Theme.mauve
                            modules: BarConfig.leftModules
                        }

                        // Center Section Column
                        SectionColumn {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            sectionTitle: "CENTER SECTION"
                            sectionName: "center"
                            accentColor: Theme.teal
                            modules: BarConfig.centerModules
                        }

                        // Right Section Column
                        SectionColumn {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            sectionTitle: "RIGHT SECTION"
                            sectionName: "right"
                            accentColor: Theme.blue
                            modules: BarConfig.rightModules
                        }
                    }

                    // Hidden / Inactive Tray
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 46
                        radius: Theme.capsuleRadius
                        color: Theme.moduleBg
                        border.color: Theme.moduleBorder
                        border.width: 1
                        visible: BarConfig.hiddenModules.length > 0

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 8

                            Text {
                                text: "󰅙 Inactive:"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: Theme.subtext0
                            }

                            Row {
                                spacing: 6
                                Repeater {
                                    model: BarConfig.hiddenModules

                                    Rectangle {
                                        required property var modelData
                                        readonly property var meta: BarConfig.getModuleMeta(modelData)
                                        implicitHeight: 28
                                        implicitWidth: hidRow.implicitWidth + 12
                                        radius: 14
                                        color: hidArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
                                        border.color: Theme.moduleBorder
                                        border.width: 1

                                        Row {
                                            id: hidRow
                                            anchors.centerIn: parent
                                            spacing: 4
                                            Text {
                                                text: "+ " + meta.name
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 10
                                                font.bold: true
                                                color: Theme.green
                                            }
                                        }

                                        MouseArea {
                                            id: hidArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: BarConfig.toggleVisibility(modelData)
                                        }
                                    }
                                }
                            }

                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }

            // ── Tab 2: Appearance & Geometry ────────────────────────────────────────
            ScrollView {
                anchors.fill: parent
                anchors.margins: 16
                visible: root.currentTab === "appearance"
                contentWidth: width

                ColumnLayout {
                    width: parent.width - 20
                    spacing: 16

                    // Position Selector
                    GroupBoxCard {
                        title: "Bar Screen Position"
                        icon: "󰘔"

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            OptionCard {
                                Layout.fillWidth: true
                                icon: "󰘔"
                                title: "Top of Screen"
                                description: "Standard status bar anchored to the top of the monitor"
                                isSelected: BarConfig.isTop
                                onClicked: BarConfig.setBarPosition("top")
                            }

                            OptionCard {
                                Layout.fillWidth: true
                                icon: "󰘓"
                                title: "Bottom of Screen"
                                description: "Dock-style status bar anchored to the bottom edge"
                                isSelected: BarConfig.isBottom
                                onClicked: BarConfig.setBarPosition("bottom")
                            }
                        }
                    }

                    // Geometry Metrics
                    GroupBoxCard {
                        title: "Dimensions & Spacing"
                        icon: "󰔎"

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            MetricSlider {
                                label: "Bar Height"
                                metricKey: "barHeight"
                                minVal: 30
                                maxVal: 54
                                curVal: BarConfig.barHeight
                                unit: "px"
                            }

                            MetricSlider {
                                label: "Bar Corner Radius"
                                metricKey: "barRadius"
                                minVal: 0
                                maxVal: 28
                                curVal: BarConfig.barRadius
                                unit: "px"
                            }

                            MetricSlider {
                                label: "Module Capsule Radius"
                                metricKey: "capsuleRadius"
                                minVal: 0
                                maxVal: 20
                                curVal: BarConfig.capsuleRadius
                                unit: "px"
                            }

                            MetricSlider {
                                label: "Module Spacing"
                                metricKey: "spacing"
                                minVal: 2
                                maxVal: 16
                                curVal: BarConfig.spacing
                                unit: "px"
                            }

                            MetricSlider {
                                label: "Horizontal Margins"
                                metricKey: "marginLeft"
                                minVal: 0
                                maxVal: 48
                                curVal: BarConfig.marginLeft
                                unit: "px"
                                onValueChanged: val => {
                                    BarConfig.setMetric("marginLeft", val);
                                }
                            }
                        }
                    }

                    // Display Style Options
                    GroupBoxCard {
                        title: "Style & Behavior"
                        icon: "󰒓"

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            ToggleOption {
                                title: "Compact Status Indicators"
                                description: "Display icon-only indicators without textual percentages for a minimalist look"
                                checked: BarConfig.compactMode
                                onToggled: BarConfig.setMetric("compactMode", !BarConfig.compactMode)
                            }
                        }
                    }
                }
            }

            // ── Tab 3: Presets Library ──────────────────────────────────────────────
            ScrollView {
                anchors.fill: parent
                anchors.margins: 16
                visible: root.currentTab === "presets"
                contentWidth: width

                ColumnLayout {
                    width: parent.width - 20
                    spacing: 12

                    Text {
                        text: "Select a curated layout preset to instantly configure your status bar:"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.subtext0
                    }

                    PresetCard {
                        presetId: "default"
                        presetIcon: "💎"
                        presetName: "Modern Glass (Default)"
                        presetDesc: "Balanced 3-group floating layout with launcher, workspaces, media player, status hub, and clock."
                        tags: ["Balanced", "Top Bar", "All Modules"]
                    }

                    PresetCard {
                        presetId: "minimal"
                        presetIcon: "⚡"
                        presetName: "Clean Minimalist"
                        presetDesc: "Clean ultra-compact bar with workspace numbers, active window title, essential status, and time."
                        tags: ["Lightweight", "Distraction Free", "Compact"]
                    }

                    PresetCard {
                        presetId: "poweruser"
                        presetIcon: "🚀"
                        presetName: "Power User Dashboard"
                        presetDesc: "Complete workstation bar with system stats, recording monitor, notifications, audio mixer, and tray."
                        tags: ["System Stats", "Tray", "Hardware Monitors"]
                    }

                    PresetCard {
                        presetId: "dock"
                        presetIcon: "⚓"
                        presetName: "Centered Floating Dock"
                        presetDesc: "Bottom anchored dock with larger rounded capsules, centered media controls, and quick launchers."
                        tags: ["Bottom Bar", "Rounded Dock", "Large Icons"]
                    }

                    PresetCard {
                        presetId: "split"
                        presetIcon: "🔀"
                        presetName: "Split Clock Focus"
                        presetDesc: "Clean split design highlighting a prominent center clock, navigation on left, and quick settings on right."
                        tags: ["Centered Time", "Split Layout"]
                    }
                }
            }

            // ── Tab 4: All Modules Catalog ──────────────────────────────────────────
            ScrollView {
                anchors.fill: parent
                anchors.margins: 16
                visible: root.currentTab === "catalog"
                contentWidth: width

                ColumnLayout {
                    width: parent.width - 20
                    spacing: 8

                    Repeater {
                        model: BarConfig.moduleCatalog

                        Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: 52
                            radius: Theme.capsuleRadius
                            color: Theme.moduleBg
                            border.color: Theme.moduleBorder
                            border.width: 1

                            readonly property bool isVisible: BarConfig.isModuleVisible(modelData.id)
                            readonly property string currentSec: BarConfig.getSectionForModule(modelData.id)

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 10

                                Text {
                                    text: modelData.icon
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 18
                                    color: Theme.accent
                                }

                                ColumnLayout {
                                    spacing: 2
                                    Text {
                                        text: modelData.name
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSize
                                        font.bold: true
                                        color: Theme.text
                                    }
                                    Text {
                                        text: modelData.description
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        color: Theme.subtext0
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                // Section Tag if active
                                Rectangle {
                                    visible: isVisible
                                    implicitHeight: 22
                                    implicitWidth: secText.implicitWidth + 12
                                    radius: 11
                                    color: currentSec === "left" ? Theme.mauve : (currentSec === "center" ? Theme.teal : Theme.blue)
                                    Text {
                                        id: secText
                                        anchors.centerIn: parent
                                        text: currentSec.toUpperCase()
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 9
                                        font.bold: true
                                        color: "#ffffff"
                                    }
                                }

                                // Toggle Visibility Button
                                Rectangle {
                                    implicitHeight: 26
                                    implicitWidth: 80
                                    radius: 13
                                    color: isVisible ? Theme.red : Theme.green

                                    Text {
                                        anchors.centerIn: parent
                                        text: isVisible ? "Hide" : "Enable"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: "#ffffff"
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: BarConfig.toggleVisibility(modelData.id)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Footer Actions Bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            // Reset Defaults Button
            Rectangle {
                implicitHeight: 32
                implicitWidth: resetRow.implicitWidth + 16
                radius: 16
                color: resetArea.containsMouse ? Theme.red : Theme.moduleBg
                border.color: Theme.moduleBorder
                border.width: 1

                Row {
                    id: resetRow
                    anchors.centerIn: parent
                    spacing: 6
                    Text {
                        text: "󰕑"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        color: resetArea.containsMouse ? "#ffffff" : Theme.yellow
                    }
                    Text {
                        text: "Reset Defaults"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        font.bold: true
                        color: resetArea.containsMouse ? "#ffffff" : Theme.text
                    }
                }

                MouseArea {
                    id: resetArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: BarConfig.resetToDefaults()
                }
            }

            Item { Layout.fillWidth: true }

            // Apply & Close Button
            Rectangle {
                implicitHeight: 32
                implicitWidth: applyRow.implicitWidth + 24
                radius: 16
                color: applyArea.containsMouse ? Theme.teal : Theme.blue

                Row {
                    id: applyRow
                    anchors.centerIn: parent
                    spacing: 6
                    Text {
                        text: "✓"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        font.bold: true
                        color: "#ffffff"
                    }
                    Text {
                        text: "Done"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        font.bold: true
                        color: "#ffffff"
                    }
                }

                MouseArea {
                    id: applyArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManager.toggle("bar_customizer")
                }
            }
        }
    }

    // ── Components ─────────────────────────────────────────────────────────────
    component TabButton: Rectangle {
        id: tabRoot
        property string tabId: ""
        property string tabIcon: ""
        property string tabTitle: ""
        property bool isActive: false
        signal clicked()

        implicitHeight: 32
        implicitWidth: tabRow.implicitWidth + 20
        radius: 16
        color: tabRoot.isActive ? Theme.accent : (tabArea.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg)
        border.color: tabRoot.isActive ? Theme.accent : Theme.moduleBorder
        border.width: 1

        Behavior on color { ColorAnimation { duration: 150 } }

        Row {
            id: tabRow
            anchors.centerIn: parent
            spacing: 6

            Text {
                text: tabRoot.tabIcon
                font.family: Theme.fontFamily
                font.pixelSize: 13
                color: tabRoot.isActive ? Theme.crust : Theme.accent
            }

            Text {
                text: tabRoot.tabTitle
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: tabRoot.isActive ? Theme.crust : Theme.text
            }
        }

        MouseArea {
            id: tabArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: tabRoot.clicked()
        }
    }

    component SectionColumn: Rectangle {
        id: secCol
        property string sectionTitle: ""
        property string sectionName: "left"
        property color accentColor: Theme.accent
        property var modules: []

        radius: Theme.capsuleRadius
        color: Theme.moduleBg
        border.color: Theme.moduleBorder
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            // Section Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: secCol.accentColor
                }

                Text {
                    text: secCol.sectionTitle
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.bold: true
                    color: secCol.accentColor
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: secCol.modules.length + " items"
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: Theme.subtext0
                }
            }

            // Modules List
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: secCol.modules

                delegate: Rectangle {
                    required property var modelData
                    required property int index

                    readonly property var meta: BarConfig.getModuleMeta(modelData)

                    width: ListView.view ? ListView.view.width : 200
                    height: 44
                    radius: Theme.pillRadius
                    color: itemMa.containsMouse ? Theme.moduleHoverBg : Theme.surface0
                    border.color: Theme.moduleBorder
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 6

                        Text {
                            text: meta.icon
                            font.family: Theme.fontFamily
                            font.pixelSize: 14
                            color: secCol.accentColor
                        }

                        Text {
                            Layout.fillWidth: true
                            text: meta.name
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: Theme.text
                            elide: Text.ElideRight
                        }

                        // Move Up / Left
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: upArea.containsMouse ? Theme.blue : Qt.rgba(0, 0, 0, 0.3)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅁"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: upArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: BarConfig.moveStep(modelData, "left")
                            }
                        }

                        // Move Down / Right
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: downArea.containsMouse ? Theme.blue : Qt.rgba(0, 0, 0, 0.3)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅂"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: downArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: BarConfig.moveStep(modelData, "right")
                            }
                        }

                        // Move to other sections
                        Row {
                            spacing: 2
                            // Target 1
                            Rectangle {
                                readonly property string targetSec: (secCol.sectionName === "left") ? "center" : (secCol.sectionName === "center" ? "left" : "left")
                                width: 18
                                height: 18
                                radius: 4
                                color: t1Area.containsMouse ? Theme.teal : Qt.rgba(0, 0, 0, 0.3)
                                Text {
                                    anchors.centerIn: parent
                                    text: targetSec.charAt(0).toUpperCase()
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: "#ffffff"
                                }
                                MouseArea {
                                    id: t1Area
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: BarConfig.moveModule(modelData, targetSec, -1)
                                }
                            }
                            // Target 2
                            Rectangle {
                                readonly property string targetSec: (secCol.sectionName === "right") ? "center" : "right"
                                width: 18
                                height: 18
                                radius: 4
                                color: t2Area.containsMouse ? Theme.teal : Qt.rgba(0, 0, 0, 0.3)
                                Text {
                                    anchors.centerIn: parent
                                    text: targetSec.charAt(0).toUpperCase()
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: "#ffffff"
                                }
                                MouseArea {
                                    id: t2Area
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: BarConfig.moveModule(modelData, targetSec, -1)
                                }
                            }
                        }

                        // Hide Button
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: delArea.containsMouse ? Theme.red : Qt.rgba(0, 0, 0, 0.3)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅙"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: delArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: BarConfig.toggleVisibility(modelData)
                            }
                        }
                    }

                    MouseArea {
                        id: itemMa
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton
                    }
                }
            }
        }
    }

    component GroupBoxCard: Rectangle {
        id: groupCard
        property string title: ""
        property string icon: ""
        default property alias content: innerCardCol.data

        Layout.fillWidth: true
        implicitHeight: cardLayout.implicitHeight + 24
        radius: Theme.capsuleRadius
        color: Theme.moduleBg
        border.color: Theme.moduleBorder
        border.width: 1

        ColumnLayout {
            id: cardLayout
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            RowLayout {
                spacing: 6
                Text {
                    text: groupCard.icon
                    font.family: Theme.fontFamily
                    font.pixelSize: 14
                    color: Theme.accent
                }
                Text {
                    text: groupCard.title
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }
            }

            ColumnLayout {
                id: innerCardCol
                Layout.fillWidth: true
                spacing: 10
            }
        }
    }

    component OptionCard: Rectangle {
        id: optCard
        property string icon: ""
        property string title: ""
        property string description: ""
        property bool isSelected: false
        signal clicked()

        implicitHeight: 64
        radius: Theme.pillRadius
        color: optCard.isSelected ? Theme.moduleActiveBg : (optMa.containsMouse ? Theme.surface0 : "transparent")
        border.color: optCard.isSelected ? Theme.accent : Theme.moduleBorder
        border.width: optCard.isSelected ? 2 : 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Text {
                text: optCard.icon
                font.family: Theme.fontFamily
                font.pixelSize: 22
                color: optCard.isSelected ? Theme.accent : Theme.subtext0
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: optCard.title
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: optCard.isSelected ? Theme.text : Theme.subtext0
                }
                Text {
                    Layout.fillWidth: true
                    text: optCard.description
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: Theme.subtext0
                    elide: Text.ElideRight
                }
            }
        }

        MouseArea {
            id: optMa
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: optCard.clicked()
        }
    }

    component MetricSlider: RowLayout {
        id: sliderRoot
        property string label: ""
        property string metricKey: ""
        property int minVal: 0
        property int maxVal: 100
        property int curVal: 50
        property string unit: ""
        signal valueChanged(int val)

        Layout.fillWidth: true
        spacing: 12

        Text {
            Layout.preferredWidth: 160
            text: sliderRoot.label
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall
            font.bold: true
            color: Theme.text
        }

        Slider {
            Layout.fillWidth: true
            from: sliderRoot.minVal
            to: sliderRoot.maxVal
            stepSize: 1
            value: sliderRoot.curVal
            onMoved: {
                if (sliderRoot.metricKey !== "") {
                    BarConfig.setMetric(sliderRoot.metricKey, Math.round(value));
                }
                sliderRoot.valueChanged(Math.round(value));
            }
        }

        Rectangle {
            implicitWidth: 50
            implicitHeight: 24
            radius: 6
            color: Theme.surface0
            Text {
                anchors.centerIn: parent
                text: Math.round(sliderRoot.curVal) + sliderRoot.unit
                font.family: Theme.fontFamily
                font.pixelSize: 11
                font.bold: true
                color: Theme.accent
            }
        }
    }

    component ToggleOption: RowLayout {
        id: togRoot
        property string title: ""
        property string description: ""
        property bool checked: false
        signal toggled()

        Layout.fillWidth: true
        spacing: 12

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: togRoot.title
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.text
            }
            Text {
                text: togRoot.description
                font.family: Theme.fontFamily
                font.pixelSize: 10
                color: Theme.subtext0
            }
        }

        Rectangle {
            width: 44
            height: 24
            radius: 12
            color: togRoot.checked ? Theme.teal : Theme.surface0

            Rectangle {
                width: 18
                height: 18
                radius: 9
                x: togRoot.checked ? 23 : 3
                anchors.verticalCenter: parent.verticalCenter
                color: "#ffffff"
                Behavior on x { NumberAnimation { duration: 150 } }
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: togRoot.toggled()
            }
        }
    }

    component PresetCard: Rectangle {
        id: preCard
        property string presetId: ""
        property string presetIcon: ""
        property string presetName: ""
        property string presetDesc: ""
        property var tags: []

        Layout.fillWidth: true
        implicitHeight: 72
        radius: Theme.capsuleRadius
        color: preMa.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg
        border.color: Theme.moduleBorder
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Text {
                text: preCard.presetIcon
                font.family: Theme.fontFamily
                font.pixelSize: 24
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: preCard.presetName
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }
                Text {
                    Layout.fillWidth: true
                    text: preCard.presetDesc
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: Theme.subtext0
                    wrapMode: Text.WordWrap
                }
            }

            // Tags
            Row {
                spacing: 4
                Repeater {
                    model: preCard.tags
                    Rectangle {
                        implicitHeight: 20
                        implicitWidth: tagT.implicitWidth + 10
                        radius: 10
                        color: Theme.surface0
                        Text {
                            id: tagT
                            anchors.centerIn: parent
                            text: modelData
                            font.family: Theme.fontFamily
                            font.pixelSize: 9
                            color: Theme.accent
                        }
                    }
                }
            }

            // Apply Button
            Rectangle {
                implicitHeight: 28
                implicitWidth: 64
                radius: 14
                color: Theme.accent

                Text {
                    anchors.centerIn: parent
                    text: "Apply"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.bold: true
                    color: Theme.crust
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: BarConfig.applyPreset(preCard.presetId)
                }
            }
        }

        MouseArea {
            id: preMa
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
        }
    }
}
