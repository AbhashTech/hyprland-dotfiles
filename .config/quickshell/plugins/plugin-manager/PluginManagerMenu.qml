import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import "../.."
import "../../components"
import "."

Rectangle {
    id: root

    implicitWidth: 780
    implicitHeight: 680
    width: implicitWidth
    height: implicitHeight
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    // Main views: "list", "store", "add", "logs", "edit_manifest", "git_logs", "delete_confirm"
    property string activeView: "list"
    property var pluginToDelete: null
    property var pluginToEdit: null

    // Edit Manifest state
    property string editName: ""
    property string editAuthor: ""
    property string editDesc: ""
    property string editPosition: "center"

    // Add Form State
    property string addMode: "template" // "template", "git", "import"
    property string newId: ""
    property string newName: ""
    property string newAuthor: "Kunal Gautam"
    property string newDescription: ""
    property string newPosition: "center"
    property bool newHasWidget: true
    property bool newHasWindow: true
    property bool newHasService: false
    property bool newInitGit: true

    // Git Form State
    property string gitRepoUrl: ""
    property string gitFolderName: ""
    property string importArchivePath: ""

    // Keybinding Builder State
    property bool kbSuper: true
    property bool kbCtrl: false
    property bool kbAlt: true
    property bool kbShift: false
    property string kbCustomKey: "M"

    function setKbCombo(comboStr) {
        if (!comboStr) return;
        var parts = comboStr.split(" + ");
        root.kbSuper = parts.indexOf("SUPER") !== -1;
        root.kbCtrl = parts.indexOf("CTRL") !== -1;
        root.kbAlt = parts.indexOf("ALT") !== -1;
        root.kbShift = parts.indexOf("SHIFT") !== -1;
        var key = parts[parts.length - 1];
        if (["SUPER", "CTRL", "ALT", "SHIFT"].indexOf(key) === -1) {
            root.kbCustomKey = key;
        }
    }

    readonly property string kbPreviewCombo: {
        var mods = [];
        if (kbSuper) mods.push("SUPER");
        if (kbCtrl) mods.push("CTRL");
        if (kbAlt) mods.push("ALT");
        if (kbShift) mods.push("SHIFT");
        var k = kbCustomKey.trim();
        if (k.length > 0) mods.push(k);
        return mods.join(" + ");
    }

    onKbPreviewComboChanged: {
        if (root.activeView === "keybinds") {
            PluginManagerService.checkKeybind(kbPreviewCombo, PluginManagerService.keybindTargetPlugin);
        }
    }

    function focusSearch() {
        if (searchInput) searchInput.forceActiveFocus();
    }

    function resetAddForm() {
        newId = "";
        newName = "";
        newAuthor = "Kunal Gautam";
        newDescription = "";
        newPosition = "center";
        newHasWidget = true;
        newHasWindow = true;
        newHasService = false;
        newInitGit = true;
        gitRepoUrl = "";
        gitFolderName = "";
        importArchivePath = "";
    }

    function openEditManifest(pluginData) {
        root.pluginToEdit = pluginData;
        root.editName = pluginData.name || "";
        root.editAuthor = pluginData.author || "";
        root.editDesc = pluginData.description || "";
        root.editPosition = (pluginData.position || "center").toLowerCase();
        root.activeView = "edit_manifest";
    }

    Component.onCompleted: {
        PluginManagerService.refresh();
        PluginManagerService.loadCatalog();
    }

    // Filter plugins list based on search and selected category filter
    readonly property var filteredList: {
        var query = PluginManagerService.searchQuery.toLowerCase().trim();
        var filter = PluginManagerService.currentFilter;
        var list = [];

        var customs = PluginManagerService.customPlugins || [];
        var builtins = PluginManagerService.builtinPlugins || [];

        if (filter === "builtin") {
            list = builtins;
        } else if (filter === "custom") {
            list = customs;
        } else if (filter === "active") {
            list = customs.filter(p => p.enabled);
        } else if (filter === "disabled") {
            list = customs.filter(p => !p.enabled);
        } else {
            // "all"
            list = customs.concat(builtins);
        }

        if (query.length > 0) {
            list = list.filter(p => {
                var nameMatch = (p.name || "").toLowerCase().includes(query);
                var idMatch = (p.id || "").toLowerCase().includes(query);
                var descMatch = (p.description || "").toLowerCase().includes(query);
                var authorMatch = (p.author || "").toLowerCase().includes(query);
                return nameMatch || idMatch || descMatch || authorMatch;
            });
        }

        return list;
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        // ── 1. Top Header Bar ────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            // Icon
            Rectangle {
                implicitWidth: 38
                implicitHeight: 38
                radius: 10
                color: Theme.surface0
                border.color: Theme.accent
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰏓"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon + 4
                    color: Theme.accent
                }
            }

            // Title & Counts
            ColumnLayout {
                spacing: 2
                Layout.fillWidth: true

                RowLayout {
                    spacing: 8
                    Text {
                        text: "Quickshell Plugin Manager"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge + 1
                        font.bold: true
                        color: Theme.text
                    }

                    Rectangle {
                        implicitWidth: statsText.implicitWidth + 12
                        implicitHeight: 20
                        radius: 10
                        color: Theme.surface1

                        Text {
                            id: statsText
                            anchors.centerIn: parent
                            text: PluginManagerService.stats.activeCustom + "/" + PluginManagerService.stats.totalCustom + " Active Custom"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall - 1
                            font.bold: true
                            color: Theme.accent
                        }
                    }
                }

                Text {
                    text: "Add, Discover, Delete, Enable, Disable, and Configure Custom Plugins"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.subtext0
                }
            }

            // Quick Shell Reload Button
            Rectangle {
                implicitWidth: 34
                implicitHeight: 34
                radius: Theme.capsuleRadius
                color: reloadMouse.containsMouse ? Theme.surface1 : Theme.surface0
                border.color: Theme.surface2
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰑐"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    color: Theme.yellow
                }

                MouseArea {
                    id: reloadMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManagerService.reloadShell()
                }
            }

            // Close Button
            Rectangle {
                implicitWidth: 34
                implicitHeight: 34
                radius: Theme.capsuleRadius
                color: closeMouse.containsMouse ? Theme.red : Theme.surface0
                border.color: Theme.surface2
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    color: closeMouse.containsMouse ? Theme.crust : Theme.subtext0
                }

                MouseArea {
                    id: closeMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: PluginManager.closeAll()
                }
            }
        }

        // ── 2. Navigation Tabs (Plugins, Store, Add, Logs) ───────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { id: "list", label: "Installed (" + (PluginManagerService.stats.totalCustom || 0) + ")", icon: "󰏓" },
                    { id: "store", label: "Discover / Store (" + (PluginManagerService.catalog ? PluginManagerService.catalog.length : 5) + ")", icon: "󰄧" },
                    { id: "add", label: "Add & Scaffold", icon: "󰐕" },
                    { id: "keybinds", label: "Keybinds", icon: "󰌌" },
                    { id: "logs", label: "Diagnostics & Logs", icon: "󰞌" }
                ]

                delegate: Rectangle {
                    required property var modelData
                    implicitWidth: navRow.implicitWidth + 20
                    implicitHeight: 32
                    radius: Theme.pillRadius
                    color: root.activeView === modelData.id ? Theme.accent : (navMouse.containsMouse ? Theme.surface1 : Theme.surface0)
                    border.color: root.activeView === modelData.id ? Theme.accent : Theme.surface1
                    border.width: 1

                    Row {
                        id: navRow
                        anchors.centerIn: parent
                        spacing: 6
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.icon
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: root.activeView === modelData.id ? Theme.crust : (navMouse.containsMouse ? Theme.accent : Theme.subtext0)
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.label
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall + 1
                            font.bold: root.activeView === modelData.id
                            color: root.activeView === modelData.id ? Theme.crust : (navMouse.containsMouse ? Theme.text : Theme.subtext0)
                        }
                    }

                    MouseArea {
                        id: navMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (modelData.id === "store") {
                                PluginManagerService.loadCatalog();
                            } else if (modelData.id === "list") {
                                PluginManagerService.refresh();
                            } else if (modelData.id === "keybinds") {
                                PluginManagerService.loadKeybind(PluginManagerService.keybindTargetPlugin);
                                PluginManagerService.checkKeybind(root.kbPreviewCombo, PluginManagerService.keybindTargetPlugin);
                            }
                            root.activeView = modelData.id;
                        }
                    }
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.surface0
        }

        // ── 3. Search and Category Filter Bar (Only in 'list' view) ──────────
        ColumnLayout {
            Layout.fillWidth: true
            visible: root.activeView === "list"
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                // Search Input Field
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 36
                    radius: Theme.capsuleRadius
                    color: Theme.surface0
                    border.color: searchInput.activeFocus ? Theme.accent : Theme.surface1
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 10
                        spacing: 8

                        Text {
                            text: "󰍉"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: searchInput.activeFocus ? Theme.accent : Theme.subtext0
                        }

                        TextInput {
                            id: searchInput
                            Layout.fillWidth: true
                            text: PluginManagerService.searchQuery
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: Theme.text
                            clip: true
                            onTextChanged: PluginManagerService.searchQuery = text

                            Text {
                                text: "Search plugins by name, ID, author, or description..."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: Theme.overlay0
                                visible: !searchInput.text && !searchInput.activeFocus
                            }
                        }

                        // Clear search button
                        Rectangle {
                            implicitWidth: 20
                            implicitHeight: 20
                            radius: 10
                            color: "transparent"
                            visible: searchInput.text.length > 0

                            Text {
                                anchors.centerIn: parent
                                text: "✕"
                                font.pixelSize: 11
                                color: Theme.subtext0
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    searchInput.text = "";
                                    PluginManagerService.searchQuery = "";
                                }
                            }
                        }
                    }
                }

                // Quick Refresh Button
                Rectangle {
                    implicitWidth: 36
                    implicitHeight: 36
                    radius: Theme.capsuleRadius
                    color: refreshListMouse.containsMouse ? Theme.surface1 : Theme.surface0
                    border.color: Theme.surface2
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "󰦗"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge
                        color: PluginManagerService.isLoading ? Theme.accent : Theme.subtext0
                    }

                    MouseArea {
                        id: refreshListMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: PluginManagerService.refresh()
                    }
                }
            }

            // Category Filter Pills
            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: [
                        { key: "all", label: "All (" + ((PluginManagerService.stats.totalCustom || 0) + (PluginManagerService.stats.totalBuiltin || 0)) + ")" },
                        { key: "active", label: "Active Custom (" + (PluginManagerService.stats.activeCustom || 0) + ")" },
                        { key: "disabled", label: "Disabled (" + (PluginManagerService.stats.disabledCustom || 0) + ")" },
                        { key: "custom", label: "Custom Only (" + (PluginManagerService.stats.totalCustom || 0) + ")" },
                        { key: "builtin", label: "Core Built-in (" + (PluginManagerService.stats.totalBuiltin || 0) + ")" }
                    ]

                    delegate: Rectangle {
                        required property var modelData
                        implicitWidth: filterText.implicitWidth + 14
                        implicitHeight: 26
                        radius: Theme.pillRadius
                        color: PluginManagerService.currentFilter === modelData.key ? Theme.accent : (filterMouse.containsMouse ? Theme.surface1 : Theme.surface0)
                        border.color: PluginManagerService.currentFilter === modelData.key ? Theme.accent : Theme.surface1
                        border.width: 1

                        Text {
                            id: filterText
                            anchors.centerIn: parent
                            text: modelData.label
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall - 1
                            font.bold: PluginManagerService.currentFilter === modelData.key
                            color: PluginManagerService.currentFilter === modelData.key ? Theme.crust : (filterMouse.containsMouse ? Theme.text : Theme.subtext0)
                        }

                        MouseArea {
                            id: filterMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: PluginManagerService.currentFilter = modelData.key
                        }
                    }
                }
            }
        }

        // ── 4. Main Views Container ──────────────────────────────────────────
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // ═════════════════════════════════════════════════════════════════
            // VIEW 1: Installed Plugins List
            // ═════════════════════════════════════════════════════════════════
            Item {
                anchors.fill: parent
                visible: root.activeView === "list"

                ListView {
                    id: pluginsListView
                    anchors.fill: parent
                    clip: true
                    spacing: 10
                    model: root.filteredList

                    // Empty state
                    Text {
                        anchors.centerIn: parent
                        visible: pluginsListView.count === 0
                        text: PluginManagerService.isLoading ? "Loading plugins..." : "No plugins found matching your search or filter."
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.subtext0
                    }

                    delegate: Rectangle {
                        id: cardRoot
                        required property var modelData
                        width: pluginsListView.width
                        implicitHeight: cardCol.implicitHeight + 22
                        radius: Theme.capsuleRadius
                        color: cardMouse.containsMouse ? Theme.surface0 : Theme.mantle
                        border.color: modelData.enabled ? (cardMouse.containsMouse ? Theme.accent : Theme.surface1) : Theme.surface0
                        border.width: 1

                        Behavior on color { ColorAnimation { duration: 150 } }
                        Behavior on border.color { ColorAnimation { duration: 150 } }

                        MouseArea {
                            id: cardMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                        }

                        ColumnLayout {
                            id: cardCol
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            // Top Row: Icon + Name + ID + Badges + Enable Switch
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                // Kind Icon
                                Rectangle {
                                    implicitWidth: 32
                                    implicitHeight: 32
                                    radius: 8
                                    color: modelData.enabled ? (modelData.isCustom ? Theme.accentGlow : Theme.surface1) : Theme.surface1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.isCustom ? (modelData.kinds && modelData.kinds.includes("service") ? "󰒋" : "󰏓") : "󰘳"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeIcon
                                        color: modelData.enabled ? (modelData.isCustom ? Theme.accent : Theme.subtext1) : Theme.subtext0
                                    }
                                }

                                // Name & ID
                                ColumnLayout {
                                    spacing: 2
                                    Layout.fillWidth: true

                                    RowLayout {
                                        spacing: 8
                                        Text {
                                            text: modelData.name || modelData.id
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeLarge
                                            font.bold: true
                                            color: modelData.enabled ? Theme.text : Theme.subtext0
                                        }

                                        // ID Badge
                                        Rectangle {
                                            implicitWidth: idText.implicitWidth + 8
                                            implicitHeight: 18
                                            radius: 4
                                            color: Theme.surface1

                                            Text {
                                                id: idText
                                                anchors.centerIn: parent
                                                text: modelData.id
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSizeSmall - 2
                                                color: Theme.subtext0
                                            }
                                        }

                                        // Version
                                        Text {
                                            text: "v" + (modelData.version || "1.0")
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall - 1
                                            color: Theme.subtext0
                                        }
                                    }

                                    // Status & Meta Badges Row
                                    RowLayout {
                                        spacing: 6

                                        // Status badge
                                        Rectangle {
                                            implicitWidth: statusBadgeText.implicitWidth + 8
                                            implicitHeight: 16
                                            radius: 8
                                            color: modelData.enabled ? Qt.rgba(163/255, 190/255, 140/255, 0.2) : Qt.rgba(76/255, 86/255, 106/255, 0.3)

                                            Text {
                                                id: statusBadgeText
                                                anchors.centerIn: parent
                                                text: modelData.enabled ? "ACTIVE" : "DISABLED"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                font.bold: true
                                                color: modelData.enabled ? Theme.green : Theme.subtext0
                                            }
                                        }

                                        // Dependency Health Badge
                                        Rectangle {
                                            visible: modelData.dependencies && modelData.dependencies.length > 0
                                            implicitWidth: depText.implicitWidth + 8
                                            implicitHeight: 16
                                            radius: 8
                                            color: (modelData.dependencyStatus && modelData.dependencyStatus.allSatisfied) ? Qt.rgba(163/255, 190/255, 140/255, 0.2) : Qt.rgba(191/255, 97/255, 106/255, 0.25)

                                            Text {
                                                id: depText
                                                anchors.centerIn: parent
                                                text: (modelData.dependencyStatus && modelData.dependencyStatus.allSatisfied) ? "󰄬 DEPS OK" : "⚠ MISSING DEPS"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                font.bold: true
                                                color: (modelData.dependencyStatus && modelData.dependencyStatus.allSatisfied) ? Theme.green : Theme.red
                                            }
                                        }

                                        // Git badge
                                        Rectangle {
                                            visible: modelData.hasGit === true
                                            implicitWidth: gitBadgeText.implicitWidth + 8
                                            implicitHeight: 16
                                            radius: 8
                                            color: Qt.rgba(235/255, 203/255, 139/255, 0.2)

                                            Text {
                                                id: gitBadgeText
                                                anchors.centerIn: parent
                                                text: "󰊢 " + (modelData.gitBranch || "git") + " (" + (modelData.gitCommits || 1) + " commits)"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                font.bold: true
                                                color: Theme.yellow
                                            }
                                        }
                                    }
                                }

                                // ── Live Topbar Position Switcher Chips (Custom plugins) ──
                                RowLayout {
                                    visible: modelData.isCustom
                                    spacing: 4

                                    Repeater {
                                        model: [
                                            { key: "left", label: "Left" },
                                            { key: "center", label: "Center" },
                                            { key: "right", label: "Right" }
                                        ]
                                        delegate: Rectangle {
                                            required property var modelData
                                            implicitWidth: 50
                                            implicitHeight: 22
                                            radius: 11
                                            color: cardRoot.modelData.position === modelData.key ? Theme.blue : (posChipMouse.containsMouse ? Theme.surface1 : Theme.surface0)
                                            border.color: cardRoot.modelData.position === modelData.key ? Theme.blue : Theme.surface2
                                            border.width: 1

                                            Text {
                                                anchors.centerIn: parent
                                                text: modelData.label
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 10
                                                font.bold: cardRoot.modelData.position === modelData.key
                                                color: cardRoot.modelData.position === modelData.key ? Theme.crust : (posChipMouse.containsMouse ? Theme.text : Theme.subtext0)
                                            }

                                            MouseArea {
                                                id: posChipMouse
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    if (cardRoot.modelData.position !== modelData.key) {
                                                        PluginManagerService.setPluginPosition(cardRoot.modelData.id, modelData.key);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                // ── Enable / Disable Switch Toggle ─────────────
                                Rectangle {
                                    visible: modelData.isCustom
                                    implicitWidth: 46
                                    implicitHeight: 24
                                    radius: 12
                                    color: modelData.enabled ? Theme.green : Theme.surface1
                                    border.color: Theme.surface2
                                    border.width: 1

                                    Behavior on color { ColorAnimation { duration: 180 } }

                                    // Switch thumb knob
                                    Rectangle {
                                        width: 18
                                        height: 18
                                        radius: 9
                                        color: Theme.crust
                                        anchors.verticalCenter: parent.verticalCenter
                                        x: modelData.enabled ? parent.width - width - 3 : 3

                                        Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            PluginManagerService.togglePlugin(modelData.id, !modelData.enabled);
                                        }
                                    }
                                }
                            }

                            // Description
                            Text {
                                text: modelData.description || "No description provided."
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.subtext0
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            // Bottom Meta & Action Bar
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                // Meta details (Author, Size, Files)
                                RowLayout {
                                    spacing: 8
                                    Layout.fillWidth: true

                                    Text {
                                        visible: modelData.author && modelData.author.length > 0
                                        text: "By " + modelData.author
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall - 2
                                        color: Theme.overlay0
                                    }

                                    Text {
                                        visible: modelData.sizeFormatted && modelData.sizeFormatted.length > 0
                                        text: "· " + modelData.sizeFormatted + " (" + modelData.filesCount + " files)"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall - 2
                                        color: Theme.overlay0
                                    }
                                }

                                // ── Action Buttons ─────────────────────────
                                // 1. Test Window Toggle
                                Rectangle {
                                    visible: modelData.enabled && (modelData.kinds && modelData.kinds.includes("window") || modelData.entryPoints && modelData.entryPoints.windows)
                                    implicitWidth: testRow.implicitWidth + 12
                                    implicitHeight: 24
                                    radius: Theme.pillRadius
                                    color: testMouse.containsMouse ? Theme.surface1 : Theme.surface0
                                    border.color: Theme.surface2

                                    Row {
                                        id: testRow
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "󰍹"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: Theme.accent
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Test UI"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            color: Theme.text
                                        }
                                    }

                                    MouseArea {
                                        id: testMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            PluginManagerService.launchPluginUI(modelData.id);
                                        }
                                    }
                                }

                                // 2. Git Pull & History (If Git repo)
                                Rectangle {
                                    visible: modelData.hasGit === true
                                    implicitWidth: gitRow.implicitWidth + 12
                                    implicitHeight: 24
                                    radius: Theme.pillRadius
                                    color: gitBtnMouse.containsMouse ? Theme.surface1 : Theme.surface0
                                    border.color: Theme.surface2

                                    Row {
                                        id: gitRow
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "󰊢"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: Theme.yellow
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Git Log"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            color: Theme.text
                                        }
                                    }

                                    MouseArea {
                                        id: gitBtnMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            PluginManagerService.fetchGitLog(modelData.id, modelData.name);
                                            root.activeView = "git_logs";
                                        }
                                    }
                                }

                                // 3. Edit Manifest Properties (Custom plugins)
                                Rectangle {
                                    visible: modelData.isCustom
                                    implicitWidth: editRow.implicitWidth + 12
                                    implicitHeight: 24
                                    radius: Theme.pillRadius
                                    color: editBtnMouse.containsMouse ? Theme.surface1 : Theme.surface0
                                    border.color: Theme.surface2

                                    Row {
                                        id: editRow
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "󰏫"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: Theme.blue
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Edit"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            color: Theme.text
                                        }
                                    }

                                    MouseArea {
                                        id: editBtnMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.openEditManifest(modelData)
                                    }
                                }

                                // 4. Export Archive Button (Custom plugins)
                                Rectangle {
                                    visible: modelData.isCustom
                                    implicitWidth: expRow.implicitWidth + 12
                                    implicitHeight: 24
                                    radius: Theme.pillRadius
                                    color: expMouse.containsMouse ? Theme.surface1 : Theme.surface0
                                    border.color: Theme.surface2

                                    Row {
                                        id: expRow
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "󰛫"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: Theme.mauve
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Export"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            color: Theme.text
                                        }
                                    }

                                    MouseArea {
                                        id: expMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: PluginManagerService.exportPlugin(modelData.id)
                                    }
                                }

                                // 5. Open Directory
                                Rectangle {
                                    implicitWidth: openRow.implicitWidth + 12
                                    implicitHeight: 24
                                    radius: Theme.pillRadius
                                    color: openMouse.containsMouse ? Theme.surface1 : Theme.surface0
                                    border.color: Theme.surface2

                                    Row {
                                        id: openRow
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "󰉋"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: Theme.yellow
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Folder"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            color: Theme.text
                                        }
                                    }

                                    MouseArea {
                                        id: openMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: PluginManagerService.openFolder(modelData.path)
                                    }
                                }

                                // 6. Delete Plugin Button
                                Rectangle {
                                    visible: modelData.isCustom && modelData.id !== "plugin_manager" && modelData.folderName !== "plugin-manager"
                                    implicitWidth: delRow.implicitWidth + 12
                                    implicitHeight: 24
                                    radius: Theme.pillRadius
                                    color: delMouse.containsMouse ? Theme.red : Theme.surface0
                                    border.color: delMouse.containsMouse ? Theme.red : Theme.surface2

                                    Row {
                                        id: delRow
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "󰆴"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            color: delMouse.containsMouse ? Theme.crust : Theme.red
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: "Delete"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 10
                                            font.bold: delMouse.containsMouse
                                            color: delMouse.containsMouse ? Theme.crust : Theme.subtext0
                                        }
                                    }

                                    MouseArea {
                                        id: delMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            root.pluginToDelete = modelData;
                                            root.activeView = "delete_confirm";
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ═════════════════════════════════════════════════════════════════
            // VIEW 2: Discover / Store Catalog
            // ═════════════════════════════════════════════════════════════════
            Item {
                anchors.fill: parent
                visible: root.activeView === "store"

                ListView {
                    id: storeListView
                    anchors.fill: parent
                    clip: true
                    spacing: 12
                    model: PluginManagerService.catalog

                    header: ColumnLayout {
                        width: storeListView.width
                        spacing: 4
                        Layout.bottomMargin: 10

                        Text {
                            text: "🌟 Community Curated Plugins & Widgets"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeLarge
                            font.bold: true
                            color: Theme.text
                        }

                        Text {
                            text: "One-click install pre-configured custom widgets with instant live reload."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext0
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 8
                            color: "transparent"
                        }
                    }

                    delegate: Rectangle {
                        required property var modelData
                        width: storeListView.width
                        implicitHeight: storeCardCol.implicitHeight + 20
                        radius: Theme.capsuleRadius
                        color: Theme.mantle
                        border.color: Theme.surface1
                        border.width: 1

                        ColumnLayout {
                            id: storeCardCol
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                // Icon Box
                                Rectangle {
                                    implicitWidth: 36
                                    implicitHeight: 36
                                    radius: 8
                                    color: Theme.surface0
                                    border.color: Theme.accent
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.icon || "󰏓"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeIcon + 2
                                        color: Theme.accent
                                    }
                                }

                                ColumnLayout {
                                    spacing: 2
                                    Layout.fillWidth: true

                                    RowLayout {
                                        spacing: 8
                                        Text {
                                            text: modelData.name
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeLarge
                                            font.bold: true
                                            color: Theme.text
                                        }

                                        Rectangle {
                                            implicitWidth: catText.implicitWidth + 8
                                            implicitHeight: 18
                                            radius: 4
                                            color: Theme.surface1

                                            Text {
                                                id: catText
                                                anchors.centerIn: parent
                                                text: modelData.category
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                font.bold: true
                                                color: Theme.yellow
                                            }
                                        }

                                        Text {
                                            text: "v" + modelData.version
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall - 1
                                            color: Theme.subtext0
                                        }
                                    }

                                    // Tags & Dependency Info
                                    RowLayout {
                                        spacing: 6
                                        Repeater {
                                            model: modelData.tags || []
                                            delegate: Rectangle {
                                                required property var modelData
                                                implicitWidth: tagTxt.implicitWidth + 8
                                                implicitHeight: 16
                                                radius: 4
                                                color: Theme.surface0

                                                Text {
                                                    id: tagTxt
                                                    anchors.centerIn: parent
                                                    text: "#" + modelData
                                                    font.family: Theme.fontFamily
                                                    font.pixelSize: 8
                                                    color: Theme.subtext0
                                                }
                                            }
                                        }
                                    }
                                }

                                // Install / Installed Status Button
                                Rectangle {
                                    implicitWidth: 120
                                    implicitHeight: 32
                                    radius: Theme.pillRadius
                                    color: modelData.isInstalled ? Theme.surface1 : (installMouse.containsMouse ? Theme.green : Theme.accent)
                                    border.color: modelData.isInstalled ? Theme.surface2 : Theme.accent

                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 4
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.isInstalled ? "✓" : "📥"
                                            font.pixelSize: 11
                                            color: modelData.isInstalled ? Theme.green : Theme.crust
                                        }
                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.isInstalled ? "Installed" : "Install 1-Click"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            font.bold: true
                                            color: modelData.isInstalled ? Theme.subtext0 : Theme.crust
                                        }
                                    }

                                    MouseArea {
                                        id: installMouse
                                        anchors.fill: parent
                                        enabled: !modelData.isInstalled
                                        hoverEnabled: true
                                        cursorShape: modelData.isInstalled ? Qt.ArrowCursor : Qt.PointingHandCursor
                                        onClicked: {
                                            PluginManagerService.installFromCatalog(modelData);
                                            root.activeView = "list";
                                        }
                                    }
                                }
                            }

                            Text {
                                text: modelData.description
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.subtext0
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }

            // ═════════════════════════════════════════════════════════════════
            // VIEW 3: Add & Scaffold Plugin Form
            // ═════════════════════════════════════════════════════════════════
            Rectangle {
                anchors.fill: parent
                visible: root.activeView === "add"
                radius: Theme.capsuleRadius
                color: Theme.mantle
                border.color: Theme.surface1
                border.width: 1

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 18
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    ColumnLayout {
                        width: parent.width
                        spacing: 16

                        // Sub Mode Switcher (Template, Git, Archive Import)
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Repeater {
                                model: [
                                    { id: "template", label: "Scaffold Template", icon: "󰅴" },
                                    { id: "git", label: "Git Clone", icon: "󰊢" },
                                    { id: "import", label: "Import Archive (.tar.gz/.zip)", icon: "󰛫" }
                                ]
                                delegate: Rectangle {
                                    required property var modelData
                                    implicitWidth: addTabRow.implicitWidth + 20
                                    implicitHeight: 32
                                    radius: Theme.pillRadius
                                    color: root.addMode === modelData.id ? Theme.accent : (addTabMouse.containsMouse ? Theme.surface1 : Theme.surface0)

                                    Row {
                                        id: addTabRow
                                        anchors.centerIn: parent
                                        spacing: 6
                                        Text {
                                            text: modelData.icon
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: root.addMode === modelData.id ? Theme.crust : Theme.accent
                                        }
                                        Text {
                                            text: modelData.label
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall + 1
                                            font.bold: true
                                            color: root.addMode === modelData.id ? Theme.crust : Theme.text
                                        }
                                    }

                                    MouseArea {
                                        id: addTabMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.addMode = modelData.id
                                    }
                                }
                            }
                        }

                        // ── Mode A: Scaffold Template Form ───────────────────
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: root.addMode === "template"
                            spacing: 12

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: "Plugin ID (folder & IPC key):"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: true
                                        color: Theme.subtext1
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        implicitHeight: 36
                                        radius: Theme.pillRadius
                                        color: Theme.surface0
                                        border.color: idInput.activeFocus ? Theme.accent : Theme.surface1

                                        TextInput {
                                            id: idInput
                                            anchors.fill: parent
                                            anchors.margins: 8
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.text
                                            text: root.newId
                                            onTextChanged: root.newId = text
                                            Text {
                                                text: "e.g. system_monitor"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSize
                                                color: Theme.overlay0
                                                visible: !idInput.text
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: "Display Name:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: true
                                        color: Theme.subtext1
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        implicitHeight: 36
                                        radius: Theme.pillRadius
                                        color: Theme.surface0
                                        border.color: nameInput.activeFocus ? Theme.accent : Theme.surface1

                                        TextInput {
                                            id: nameInput
                                            anchors.fill: parent
                                            anchors.margins: 8
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.text
                                            text: root.newName
                                            onTextChanged: root.newName = text
                                            Text {
                                                text: "e.g. System Monitor"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSize
                                                color: Theme.overlay0
                                                visible: !nameInput.text
                                            }
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: "Author:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: true
                                        color: Theme.subtext1
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        implicitHeight: 36
                                        radius: Theme.pillRadius
                                        color: Theme.surface0
                                        border.color: authorInput.activeFocus ? Theme.accent : Theme.surface1

                                        TextInput {
                                            id: authorInput
                                            anchors.fill: parent
                                            anchors.margins: 8
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.text
                                            text: root.newAuthor
                                            onTextChanged: root.newAuthor = text
                                        }
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: "Description:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: true
                                        color: Theme.subtext1
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        implicitHeight: 36
                                        radius: Theme.pillRadius
                                        color: Theme.surface0
                                        border.color: descInput.activeFocus ? Theme.accent : Theme.surface1

                                        TextInput {
                                            id: descInput
                                            anchors.fill: parent
                                            anchors.margins: 8
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.text
                                            text: root.newDescription
                                            onTextChanged: root.newDescription = text
                                            Text {
                                                text: "Brief summary of features"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSize
                                                color: Theme.overlay0
                                                visible: !descInput.text
                                            }
                                        }
                                    }
                                }
                            }

                            // Topbar Position
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                Text {
                                    text: "Topbar Capsule Position:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.subtext1
                                }

                                RowLayout {
                                    spacing: 8
                                    Repeater {
                                        model: [
                                            { key: "left", label: "Left Group" },
                                            { key: "center", label: "Center Group" },
                                            { key: "right", label: "Right Group" }
                                        ]
                                        delegate: Rectangle {
                                            required property var modelData
                                            implicitWidth: 120
                                            implicitHeight: 32
                                            radius: Theme.pillRadius
                                            color: root.newPosition === modelData.key ? Theme.accent : (posMouse.containsMouse ? Theme.surface1 : Theme.surface0)
                                            border.color: root.newPosition === modelData.key ? Theme.accent : Theme.surface1

                                            Text {
                                                anchors.centerIn: parent
                                                text: modelData.label
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSizeSmall
                                                font.bold: root.newPosition === modelData.key
                                                color: root.newPosition === modelData.key ? Theme.crust : Theme.text
                                            }

                                            MouseArea {
                                                id: posMouse
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.newPosition = modelData.key
                                            }
                                        }
                                    }
                                }
                            }

                            // Component Checkboxes
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text {
                                    text: "Components to Scaffold:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.subtext1
                                }

                                RowLayout {
                                    spacing: 16

                                    RowLayout {
                                        spacing: 6
                                        Rectangle {
                                            implicitWidth: 20
                                            implicitHeight: 20
                                            radius: 4
                                            color: root.newHasWidget ? Theme.accent : Theme.surface0
                                            border.color: Theme.surface2
                                            Text {
                                                anchors.centerIn: parent
                                                text: "✓"
                                                visible: root.newHasWidget
                                                font.pixelSize: 12
                                                color: Theme.crust
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.newHasWidget = !root.newHasWidget
                                            }
                                        }
                                        Text {
                                            text: "Topbar Widget (Module.qml)"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            color: Theme.text
                                        }
                                    }

                                    RowLayout {
                                        spacing: 6
                                        Rectangle {
                                            implicitWidth: 20
                                            implicitHeight: 20
                                            radius: 4
                                            color: root.newHasWindow ? Theme.accent : Theme.surface0
                                            border.color: Theme.surface2
                                            Text {
                                                anchors.centerIn: parent
                                                text: "✓"
                                                visible: root.newHasWindow
                                                font.pixelSize: 12
                                                color: Theme.crust
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.newHasWindow = !root.newHasWindow
                                            }
                                        }
                                        Text {
                                            text: "Popup Modal (Window.qml)"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            color: Theme.text
                                        }
                                    }

                                    RowLayout {
                                        spacing: 6
                                        Rectangle {
                                            implicitWidth: 20
                                            implicitHeight: 20
                                            radius: 4
                                            color: root.newHasService ? Theme.accent : Theme.surface0
                                            border.color: Theme.surface2
                                            Text {
                                                anchors.centerIn: parent
                                                text: "✓"
                                                visible: root.newHasService
                                                font.pixelSize: 12
                                                color: Theme.crust
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.newHasService = !root.newHasService
                                            }
                                        }
                                        Text {
                                            text: "Background Service (Service.qml)"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            color: Theme.text
                                        }
                                    }
                                }

                                RowLayout {
                                    spacing: 6
                                    Rectangle {
                                        implicitWidth: 20
                                        implicitHeight: 20
                                        radius: 4
                                        color: root.newInitGit ? Theme.accent : Theme.surface0
                                        border.color: Theme.surface2
                                        Text {
                                            anchors.centerIn: parent
                                            text: "✓"
                                            visible: root.newInitGit
                                            font.pixelSize: 12
                                            color: Theme.crust
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: root.newInitGit = !root.newInitGit
                                        }
                                    }
                                    Text {
                                        text: "Initialize as a Standalone Git Repository (git init + initial commit)"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        color: Theme.subtext1
                                    }
                                }
                            }

                            // Submit Scaffold Button
                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: 40
                                radius: Theme.capsuleRadius
                                color: submitTemplateMouse.containsMouse ? Theme.green : Theme.accent
                                border.color: Theme.surface2

                                Text {
                                    anchors.centerIn: parent
                                    text: "🚀 Scaffold & Activate Plugin"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold: true
                                    color: Theme.crust
                                }

                                MouseArea {
                                    id: submitTemplateMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (!root.newId.trim()) {
                                            PluginManagerService.showToast("Please provide a Plugin ID", "error");
                                            return;
                                        }
                                        PluginManagerService.createPlugin({
                                            id: root.newId,
                                            name: root.newName,
                                            author: root.newAuthor,
                                            description: root.newDescription,
                                            position: root.newPosition,
                                            hasWidget: root.newHasWidget,
                                            hasWindow: root.newHasWindow,
                                            hasService: root.newHasService,
                                            initGit: root.newInitGit
                                        });
                                        root.activeView = "list";
                                    }
                                }
                            }
                        }

                        // ── Mode B: Git Clone Form ───────────────────────────
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: root.addMode === "git"
                            spacing: 12

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text {
                                    text: "Git Repository URL:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.subtext1
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 36
                                    radius: Theme.pillRadius
                                    color: Theme.surface0
                                    border.color: gitUrlInput.activeFocus ? Theme.accent : Theme.surface1

                                    TextInput {
                                        id: gitUrlInput
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSize
                                        color: Theme.text
                                        text: root.gitRepoUrl
                                        onTextChanged: root.gitRepoUrl = text
                                        Text {
                                            text: "https://github.com/username/quickshell-plugin.git"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.overlay0
                                            visible: !gitUrlInput.text
                                        }
                                    }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text {
                                    text: "Custom Folder Name (Optional):"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.subtext1
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 36
                                    radius: Theme.pillRadius
                                    color: Theme.surface0
                                    border.color: gitFolderInput.activeFocus ? Theme.accent : Theme.surface1

                                    TextInput {
                                        id: gitFolderInput
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSize
                                        color: Theme.text
                                        text: root.gitFolderName
                                        onTextChanged: root.gitFolderName = text
                                        Text {
                                            text: "Leave empty to use repository name"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.overlay0
                                            visible: !gitFolderInput.text
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: 40
                                radius: Theme.capsuleRadius
                                color: submitGitMouse.containsMouse ? Theme.green : Theme.accent
                                border.color: Theme.surface2

                                Text {
                                    anchors.centerIn: parent
                                    text: "📥 Clone & Install Plugin"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold: true
                                    color: Theme.crust
                                }

                                MouseArea {
                                    id: submitGitMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (!root.gitRepoUrl.trim()) {
                                            PluginManagerService.showToast("Please enter a Git repository URL", "error");
                                            return;
                                        }
                                        PluginManagerService.installGit(root.gitRepoUrl, root.gitFolderName);
                                        root.activeView = "list";
                                    }
                                }
                            }
                        }

                        // ── Mode C: Archive Import Form ──────────────────────
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: root.addMode === "import"
                            spacing: 12

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text {
                                    text: "Archive File Path (.tar.gz or .zip):"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.subtext1
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 36
                                    radius: Theme.pillRadius
                                    color: Theme.surface0
                                    border.color: importInput.activeFocus ? Theme.accent : Theme.surface1

                                    TextInput {
                                        id: importInput
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSize
                                        color: Theme.text
                                        text: root.importArchivePath
                                        onTextChanged: root.importArchivePath = text
                                        Text {
                                            text: "~/.cache/quickshell_backups/my-plugin.tar.gz"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            color: Theme.overlay0
                                            visible: !importInput.text
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: 40
                                radius: Theme.capsuleRadius
                                color: submitImportMouse.containsMouse ? Theme.green : Theme.accent
                                border.color: Theme.surface2

                                Text {
                                    anchors.centerIn: parent
                                    text: "📦 Extract & Install Archive"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold: true
                                    color: Theme.crust
                                }

                                MouseArea {
                                    id: submitImportMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (!root.importArchivePath.trim()) {
                                            PluginManagerService.showToast("Please enter an archive path", "error");
                                            return;
                                        }
                                        PluginManagerService.importPlugin(root.importArchivePath);
                                        root.activeView = "list";
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ═════════════════════════════════════════════════════════════════
            // VIEW 4: Diagnostics & Logs Console
            // ═════════════════════════════════════════════════════════════════
            Rectangle {
                anchors.fill: parent
                visible: root.activeView === "logs"
                radius: Theme.capsuleRadius
                color: Theme.crust
                border.color: Theme.surface1
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "📜 Real-Time Diagnostics & Process Traces"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                            color: Theme.text
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            implicitWidth: 80
                            implicitHeight: 26
                            radius: Theme.pillRadius
                            color: Theme.surface0

                            Text {
                                anchors.centerIn: parent
                                text: "Clear Logs"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: Theme.subtext0
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: PluginManagerService.clearLogs()
                            }
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 4
                        model: PluginManagerService.diagnosticsLogs

                        delegate: RowLayout {
                            required property var modelData
                            width: parent.width
                            spacing: 8

                            Text {
                                text: "[" + modelData.time + "]"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: Theme.overlay0
                            }

                            Text {
                                text: modelData.message
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: modelData.type === "error" ? Theme.red : (modelData.type === "success" ? Theme.green : Theme.subtext1)
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }

            // ═════════════════════════════════════════════════════════════════
            // VIEW: Keybindings Manager
            // ═════════════════════════════════════════════════════════════════
            Rectangle {
                anchors.fill: parent
                visible: root.activeView === "keybinds"
                radius: Theme.capsuleRadius
                color: Theme.crust
                border.color: Theme.surface1
                border.width: 1

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 16
                    contentWidth: width
                    clip: true

                    ColumnLayout {
                        width: parent.width - 10
                        spacing: 12

                        // Header & Description
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: "󰌌"
                                font.family: Theme.fontFamily
                                font.pixelSize: 20
                                color: Theme.accent
                            }
                            Text {
                                text: "Custom Plugin Shortcuts & Keybindings"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeLarge
                                font.bold: true
                                color: Theme.text
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "Configure dynamic global shortcuts in Hyprland with automatic system conflict checking against active compositor bindings."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext0
                            wrapMode: Text.Wrap
                        }

                        // Target Plugin Selector
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: targetCol.implicitHeight + 16
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface1
                            border.width: 1

                            ColumnLayout {
                                id: targetCol
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Text {
                                    text: "Target Plugin Component:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.text
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Repeater {
                                        model: [
                                            { id: "plugin_manager", name: "Plugin Manager" },
                                            { id: "scratchpad_notes", name: "Scratchpad Notes" },
                                            { id: "wikidict", name: "Wiktionary" },
                                            { id: "alarm", name: "Alarm" }
                                        ]
                                        delegate: Rectangle {
                                            required property var modelData
                                            height: 28
                                            width: targetTxt.implicitWidth + 16
                                            radius: Theme.pillRadius
                                            color: PluginManagerService.keybindTargetPlugin === modelData.id ? Theme.accent : (targetMa.containsMouse ? Theme.surface2 : Theme.surface1)
                                            border.color: PluginManagerService.keybindTargetPlugin === modelData.id ? Theme.accent : Theme.surface2
                                            border.width: 1

                                            Text {
                                                id: targetTxt
                                                anchors.centerIn: parent
                                                text: modelData.name
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 10
                                                font.bold: PluginManagerService.keybindTargetPlugin === modelData.id
                                                color: PluginManagerService.keybindTargetPlugin === modelData.id ? Theme.crust : Theme.text
                                            }

                                            MouseArea {
                                                id: targetMa
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    PluginManagerService.loadKeybind(modelData.id);
                                                    PluginManagerService.checkKeybind(root.kbPreviewCombo, modelData.id);
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Active Keybind Display
                        Rectangle {
                            Layout.fillWidth: true
                            height: 44
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface1
                            border.width: 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                spacing: 10

                                Text {
                                    text: "Currently Active Keybind:"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold: true
                                    color: Theme.text
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    height: 26
                                    width: activeKbPillRow.implicitWidth + 16
                                    radius: Theme.pillRadius
                                    color: Theme.surface1
                                    border.color: Theme.accent
                                    border.width: 1

                                    Row {
                                        id: activeKbPillRow
                                        anchors.centerIn: parent
                                        spacing: 6
                                        Rectangle {
                                            width: 8
                                            height: 8
                                            radius: 4
                                            color: Theme.green
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        Text {
                                            text: PluginManagerService.activeKeybind
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSizeSmall
                                            font.bold: true
                                            color: Theme.accent
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }
                                }
                            }
                        }

                        // Shortcut Builder Card
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: kbBuilderCol.implicitHeight + 20
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface1
                            border.width: 1

                            ColumnLayout {
                                id: kbBuilderCol
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 10

                                Text {
                                    text: "Configure Shortcut Combination"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold: true
                                    color: Theme.text
                                }

                                // Modifiers
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Repeater {
                                        model: [
                                            { name: "SUPER", prop: "kbSuper", label: "󰘳 SUPER (Win)" },
                                            { name: "CTRL", prop: "kbCtrl", label: "CTRL" },
                                            { name: "ALT", prop: "kbAlt", label: "ALT" },
                                            { name: "SHIFT", prop: "kbShift", label: "SHIFT" }
                                        ]
                                        delegate: Rectangle {
                                            required property var modelData
                                            property bool isChecked: root[modelData.prop]
                                            height: 30
                                            width: kbModTxt.implicitWidth + 20
                                            radius: Theme.pillRadius
                                            color: isChecked ? Theme.accent : (kbModMa.containsMouse ? Theme.surface1 : Theme.surface0)
                                            border.color: isChecked ? Theme.accent : Theme.surface2
                                            border.width: 1

                                            Text {
                                                id: kbModTxt
                                                anchors.centerIn: parent
                                                text: modelData.label
                                                font.family: Theme.fontFamily
                                                font.pixelSize: Theme.fontSizeSmall
                                                font.bold: isChecked
                                                color: isChecked ? Theme.crust : Theme.text
                                            }

                                            MouseArea {
                                                id: kbModMa
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root[modelData.prop] = !isChecked
                                            }
                                        }
                                    }
                                }

                                // Key Input & Presets
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    Text {
                                        text: "+ Key:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSize
                                        color: Theme.subtext0
                                    }

                                    Rectangle {
                                        width: 100
                                        height: 30
                                        radius: Theme.pillRadius
                                        color: Theme.surface1
                                        border.color: kbKeyInput.activeFocus ? Theme.accent : Theme.surface2
                                        border.width: 1

                                        TextInput {
                                            id: kbKeyInput
                                            anchors.fill: parent
                                            anchors.leftMargin: 10
                                            anchors.rightMargin: 10
                                            verticalAlignment: TextInput.AlignVCenter
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Theme.fontSize
                                            font.bold: true
                                            color: Theme.text
                                            text: root.kbCustomKey
                                            onTextChanged: root.kbCustomKey = text.trim()
                                        }
                                    }

                                    Text {
                                        text: "Quick Presets:"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        color: Theme.subtext0
                                    }

                                    Repeater {
                                        model: ["M", "P", "J", "Return", "Space"]
                                        delegate: Rectangle {
                                            required property var modelData
                                            height: 24
                                            width: preKbText.implicitWidth + 12
                                            radius: 4
                                            color: root.kbCustomKey.toUpperCase() === modelData.toUpperCase() ? Theme.surface2 : (preKbMa.containsMouse ? Theme.surface1 : "transparent")
                                            border.color: root.kbCustomKey.toUpperCase() === modelData.toUpperCase() ? Theme.accent : Theme.surface2
                                            border.width: 1

                                            Text {
                                                id: preKbText
                                                anchors.centerIn: parent
                                                text: modelData
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 10
                                                color: Theme.text
                                            }

                                            MouseArea {
                                                id: preKbMa
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: root.kbCustomKey = modelData
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Conflict Detection Banner
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: kbStatusCol.implicitHeight + 16
                            radius: Theme.pillRadius
                            color: PluginManagerService.isKeybindConflict ? Qt.rgba(243/255, 139/255, 168/255, 0.15) : Qt.rgba(166/255, 227/255, 161/255, 0.15)
                            border.color: PluginManagerService.isKeybindConflict ? Theme.red : Theme.green
                            border.width: 1

                            ColumnLayout {
                                id: kbStatusCol
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Text {
                                        text: PluginManagerService.isKeybindConflict ? "⚠️" : "✓"
                                        font.pixelSize: 13
                                    }
                                    Text {
                                        text: PluginManagerService.isKeybindConflict ? "Keybinding Conflict Warning" : "Keybinding Available"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall + 1
                                        font.bold: true
                                        color: PluginManagerService.isKeybindConflict ? Theme.red : Theme.green
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: PluginManagerService.keybindStatusMessage.length > 0 ? PluginManagerService.keybindStatusMessage : (root.kbPreviewCombo + " is ready to bind.")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Theme.text
                                    wrapMode: Text.Wrap
                                }

                                // Recommended Alternatives
                                ColumnLayout {
                                    visible: PluginManagerService.isKeybindConflict && PluginManagerService.recommendedKeybinds && PluginManagerService.recommendedKeybinds.length > 0
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Text {
                                        text: "Recommended Free Alternatives (Click to Select):"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        font.bold: true
                                        color: Theme.peach
                                    }

                                    Row {
                                        spacing: 6
                                        Repeater {
                                            model: PluginManagerService.recommendedKeybinds
                                            delegate: Rectangle {
                                                required property var modelData
                                                height: 24
                                                width: recKbTxt.implicitWidth + 14
                                                radius: Theme.pillRadius
                                                color: recKbMa.containsMouse ? Theme.surface2 : Theme.surface1
                                                border.color: Theme.accent
                                                border.width: 1

                                                Row {
                                                    anchors.centerIn: parent
                                                    spacing: 4
                                                    Text {
                                                        text: "⚡"
                                                        font.pixelSize: 9
                                                    }
                                                    Text {
                                                        id: recKbTxt
                                                        text: modelData
                                                        font.family: Theme.fontFamily
                                                        font.pixelSize: 10
                                                        font.bold: true
                                                        color: Theme.accent
                                                    }
                                                }

                                                MouseArea {
                                                    id: recKbMa
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    cursorShape: Qt.PointingHandCursor
                                                    onClicked: root.setKbCombo(modelData)
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Action Buttons
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: Theme.pillRadius
                                color: saveKbMa.containsMouse ? Qt.darker(Theme.accent, 1.15) : Theme.accent

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 6
                                    Text {
                                        text: "󰄬"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 13
                                        font.bold: true
                                        color: Theme.crust
                                    }
                                    Text {
                                        text: "Save & Apply Dynamic Shortcut"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: true
                                        color: Theme.crust
                                    }
                                }

                                MouseArea {
                                    id: saveKbMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: PluginManagerService.saveKeybind(root.kbPreviewCombo, PluginManagerService.keybindTargetPlugin)
                                }
                            }
                        }
                    }
                }
            }
            Rectangle {
                anchors.fill: parent
                visible: root.activeView === "edit_manifest"
                radius: Theme.capsuleRadius
                color: Theme.mantle
                border.color: Theme.accent
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12

                    Text {
                        text: "⚙️ Edit Plugin Manifest (" + (root.pluginToEdit ? root.pluginToEdit.id : "") + ")"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        color: Theme.text
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "Display Name:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext1
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface1

                            TextInput {
                                anchors.fill: parent
                                anchors.margins: 8
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: Theme.text
                                text: root.editName
                                onTextChanged: root.editName = text
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "Author:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext1
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface1

                            TextInput {
                                anchors.fill: parent
                                anchors.margins: 8
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: Theme.text
                                text: root.editAuthor
                                onTextChanged: root.editAuthor = text
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "Description:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext1
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface1

                            TextInput {
                                anchors.fill: parent
                                anchors.margins: 8
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: Theme.text
                                text: root.editDesc
                                onTextChanged: root.editDesc = text
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "Topbar Capsule Position:"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext1
                        }

                        RowLayout {
                            spacing: 8
                            Repeater {
                                model: [
                                    { key: "left", label: "Left Group" },
                                    { key: "center", label: "Center Group" },
                                    { key: "right", label: "Right Group" }
                                ]
                                delegate: Rectangle {
                                    required property var modelData
                                    implicitWidth: 120
                                    implicitHeight: 32
                                    radius: Theme.pillRadius
                                    color: root.editPosition === modelData.key ? Theme.accent : Theme.surface0
                                    border.color: Theme.surface1

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.label
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall
                                        font.bold: root.editPosition === modelData.key
                                        color: root.editPosition === modelData.key ? Theme.crust : Theme.text
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: root.editPosition = modelData.key
                                    }
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    RowLayout {
                        Layout.alignment: Qt.AlignRight
                        spacing: 12

                        Rectangle {
                            implicitWidth: 100
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: Theme.surface0
                            border.color: Theme.surface2

                            Text {
                                anchors.centerIn: parent
                                text: "Cancel"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: Theme.text
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.activeView = "list"
                            }
                        }

                        Rectangle {
                            implicitWidth: 140
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: Theme.accent

                            Text {
                                anchors.centerIn: parent
                                text: "💾 Save Changes"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold: true
                                color: Theme.crust
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.pluginToEdit) {
                                        PluginManagerService.updateManifest(root.pluginToEdit.id, {
                                            name: root.editName,
                                            author: root.editAuthor,
                                            description: root.editDesc,
                                            position: root.editPosition
                                        });
                                    }
                                    root.activeView = "list";
                                }
                            }
                        }
                    }
                }
            }

            // ═════════════════════════════════════════════════════════════════
            // VIEW 6: Git Commit History Modal
            // ═════════════════════════════════════════════════════════════════
            Rectangle {
                anchors.fill: parent
                visible: root.activeView === "git_logs"
                radius: Theme.capsuleRadius
                color: Theme.mantle
                border.color: Theme.yellow
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "󰊢 Git History: " + PluginManagerService.gitLogPluginName
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeLarge
                            font.bold: true
                            color: Theme.text
                            Layout.fillWidth: true
                        }

                        // Pull Latest button
                        Rectangle {
                            implicitWidth: 100
                            implicitHeight: 28
                            radius: Theme.pillRadius
                            color: Theme.yellow

                            Row {
                                anchors.centerIn: parent
                                spacing: 4
                                Text {
                                    text: "󰑐"
                                    color: Theme.crust
                                    font.pixelSize: 11
                                }
                                Text {
                                    text: "Git Pull"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    font.bold: true
                                    color: Theme.crust
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: PluginManagerService.gitPull(PluginManagerService.gitLogPluginId)
                            }
                        }

                        // Close Log button
                        Rectangle {
                            implicitWidth: 28
                            implicitHeight: 28
                            radius: 14
                            color: Theme.surface0

                            Text {
                                anchors.centerIn: parent
                                text: "✕"
                                color: Theme.subtext0
                                font.pixelSize: 12
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.activeView = "list"
                            }
                        }
                    }

                    // Commits List
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 8
                        model: PluginManagerService.gitLogs

                        delegate: Rectangle {
                            required property var modelData
                            width: parent.width
                            implicitHeight: commitCol.implicitHeight + 16
                            radius: 8
                            color: Theme.surface0
                            border.color: Theme.surface1

                            ColumnLayout {
                                id: commitCol
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: modelData.hash
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        font.bold: true
                                        color: Theme.yellow
                                    }
                                    Text {
                                        text: "· " + modelData.author
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        color: Theme.subtext0
                                    }
                                    Text {
                                        text: "· " + modelData.date
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        color: Theme.overlay0
                                        Layout.fillWidth: true
                                    }
                                }

                                Text {
                                    text: modelData.message
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Theme.text
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }

            // ═════════════════════════════════════════════════════════════════
            // VIEW 7: Delete Confirmation Modal
            // ═════════════════════════════════════════════════════════════════
            Rectangle {
                anchors.fill: parent
                visible: root.activeView === "delete_confirm"
                radius: Theme.capsuleRadius
                color: Qt.rgba(30/255, 34/255, 42/255, 0.95)
                border.color: Theme.red
                border.width: 1

                ColumnLayout {
                    anchors.centerIn: parent
                    width: parent.width - 80
                    spacing: 16

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 48
                        implicitHeight: 48
                        radius: 24
                        color: Qt.rgba(191/255, 97/255, 106/255, 0.2)
                        border.color: Theme.red
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: "󰆴"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeIcon + 6
                            color: Theme.red
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Delete Plugin Confirmation"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge + 2
                        font.bold: true
                        color: Theme.text
                    }

                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        text: "Are you sure you want to permanently delete '" + (root.pluginToDelete ? root.pluginToDelete.name : "") + "'?\nThis will remove all files from " + (root.pluginToDelete ? root.pluginToDelete.path : "") + "."
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.subtext0
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 16

                        Rectangle {
                            implicitWidth: 120
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: cancelDelMouse.containsMouse ? Theme.surface1 : Theme.surface0
                            border.color: Theme.surface2

                            Text {
                                anchors.centerIn: parent
                                text: "Cancel"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: Theme.text
                            }

                            MouseArea {
                                id: cancelDelMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.pluginToDelete = null;
                                    root.activeView = "list";
                                }
                            }
                        }

                        Rectangle {
                            implicitWidth: 140
                            implicitHeight: 36
                            radius: Theme.pillRadius
                            color: confirmDelMouse.containsMouse ? Qt.darker(Theme.red, 1.2) : Theme.red

                            Text {
                                anchors.centerIn: parent
                                text: "Confirm Delete"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold: true
                                color: Theme.crust
                            }

                            MouseArea {
                                id: confirmDelMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (root.pluginToDelete) {
                                        PluginManagerService.deletePlugin(root.pluginToDelete.id);
                                    }
                                    root.pluginToDelete = null;
                                    root.activeView = "list";
                                }
                            }
                        }
                    }
                }
            }
        }

        // ── 5. Toast Notification Pill ───────────────────────────────────────
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            visible: PluginManagerService.toastVisible
            implicitWidth: toastRow.implicitWidth + 24
            implicitHeight: 32
            radius: 16
            color: Theme.crust
            border.color: PluginManagerService.toastType === "success" ? Theme.green : (PluginManagerService.toastType === "error" ? Theme.red : Theme.accent)
            border.width: 1

            Row {
                id: toastRow
                anchors.centerIn: parent
                spacing: 8

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: PluginManagerService.toastType === "success" ? "✓" : (PluginManagerService.toastType === "error" ? "⚠" : "ℹ")
                    font.pixelSize: 13
                    font.bold: true
                    color: PluginManagerService.toastType === "success" ? Theme.green : (PluginManagerService.toastType === "error" ? Theme.red : Theme.accent)
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: PluginManagerService.toastMessage
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: Theme.text
                }
            }
        }
    }
}
