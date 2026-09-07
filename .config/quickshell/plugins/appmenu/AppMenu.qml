import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 640
    implicitHeight: 520
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property var allApps: []
    property var filteredApps: []
    property string activeCategory: "All"
    property int selectedIndex: 0

    readonly property var categories: ["All", "Internet", "Development", "Multimedia", "Graphics", "Office", "System", "Utilities"]

    function categoryIcon(cat) {
        switch (cat) {
            case "All": return "󰀻";
            case "Internet": return "󰖟";
            case "Development": return "󰅩";
            case "Multimedia": return "󰕼";
            case "Graphics": return "󰹉";
            case "Office": return "󰈙";
            case "System": return "󰒋";
            case "Utilities": return "󰋜";
            default: return "󰀻";
        }
    }

    function filterApps() {
        var q = searchInput.text.toLowerCase().trim();
        var cat = root.activeCategory;
        var list = [];

        for (var i = 0; i < root.allApps.length; i++) {
            var app = root.allApps[i];
            if (cat !== "All" && app.category !== cat) {
                continue;
            }
            if (q.length > 0) {
                var nameMatch = app.name.toLowerCase().indexOf(q) !== -1;
                var commentMatch = app.comment && app.comment.toLowerCase().indexOf(q) !== -1;
                var execMatch = app.exec && app.exec.toLowerCase().indexOf(q) !== -1;
                if (!nameMatch && !commentMatch && !execMatch) {
                    continue;
                }
            }
            list.push(app);
        }
        root.filteredApps = list;
        root.selectedIndex = 0;
    }

    function launchSelected() {
        if (root.filteredApps.length > 0 && root.selectedIndex >= 0 && root.selectedIndex < root.filteredApps.length) {
            var app = root.filteredApps[root.selectedIndex];
            launchApp(app);
        }
    }

    function launchApp(app) {
        if (!app) return;
        var cmd = app.exec;
        if (app.terminal) {
            cmd = "kitty -e " + cmd;
        }
        launcherProc.exec(["bash", "-c", cmd + " &"]);
        PluginManager.closeAll();
    }

    Process {
        id: launcherProc
    }

    Process {
        id: scannerProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/appmenu/app_scanner.py"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (Array.isArray(parsed)) {
                        root.allApps = parsed;
                        root.filterApps();
                    }
                } catch (e) {}
            }
        }
    }

    Component.onCompleted: {
        scannerProc.running = true;
        searchInput.forceActiveFocus();
    }

    Connections {
        target: PluginManager
        function onAppMenuVisibleChanged() {
            if (PluginManager.appMenuVisible) {
                searchInput.text = "";
                root.activeCategory = "All";
                root.filterApps();
                searchInput.forceActiveFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Search Input Header
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 44
            radius: Theme.pillRadius
            color: Theme.moduleBg
            border.color: searchInput.activeFocus ? Theme.accent : Theme.moduleBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 10

                Text {
                    text: ""
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon
                    font.bold: true
                    color: searchInput.activeFocus ? Theme.accent : Theme.subtext0
                }

                TextInput {
                    id: searchInput
                    Layout.fillWidth: true
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge
                    color: Theme.text
                    clip: true
                    selectByMouse: true
                    selectionColor: Theme.surface2
                    selectedTextColor: Theme.text

                    Text {
                        text: "Search applications, utilities..."
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge
                        color: Theme.overlay0
                        visible: !searchInput.text && !searchInput.activeFocus
                    }

                    onTextChanged: root.filterApps()

                    Keys.onEscapePressed: PluginManager.closeAll()
                    Keys.onReturnPressed: root.launchSelected()
                    Keys.onDownPressed: {
                        if (root.selectedIndex < root.filteredApps.length - 1) {
                            root.selectedIndex++;
                            appsListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                        }
                    }
                    Keys.onUpPressed: {
                        if (root.selectedIndex > 0) {
                            root.selectedIndex--;
                            appsListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                        }
                    }
                }

                // Clear button
                Text {
                    visible: searchInput.text.length > 0
                    text: "󰅖"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon
                    color: Theme.subtext0
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            searchInput.text = "";
                            searchInput.forceActiveFocus();
                        }
                    }
                }
            }
        }

        // Category Pills Row
        ScrollView {
            Layout.fillWidth: true
            implicitHeight: 34
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOff

            Row {
                spacing: 6

                Repeater {
                    model: root.categories

                    Rectangle {
                        required property string modelData
                        implicitWidth: catRow.implicitWidth + 16
                        implicitHeight: 30
                        radius: Theme.pillRadius
                        color: root.activeCategory === modelData ? Theme.accent : Theme.moduleBg
                        border.color: root.activeCategory === modelData ? Theme.accent : Theme.moduleBorder
                        border.width: 1

                        Row {
                            id: catRow
                            anchors.centerIn: parent
                            spacing: 5

                            Text {
                                text: root.categoryIcon(modelData)
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: root.activeCategory === modelData ? Theme.crust : Theme.subtext0
                            }

                            Text {
                                text: modelData
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: root.activeCategory === modelData
                                color: root.activeCategory === modelData ? Theme.crust : Theme.text
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.activeCategory = modelData;
                                root.filterApps();
                                searchInput.forceActiveFocus();
                            }
                        }
                    }
                }
            }
        }

        // Applications List
        ListView {
            id: appsListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.filteredApps
            spacing: 4

            delegate: Rectangle {
                id: itemDelegate
                required property var modelData
                required property int index

                width: appsListView.width
                implicitHeight: 46
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : "transparent"
                border.color: root.selectedIndex === index ? Theme.accent : "transparent"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 12

                    // Icon / Fallback Icon
                    Rectangle {
                        implicitWidth: 32
                        implicitHeight: 32
                        radius: 6
                        color: Theme.moduleBg
                        border.color: Theme.moduleBorder
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: "󰣆"
                            font.family: Theme.fontFamily
                            font.pixelSize: 18
                            color: Theme.accent
                        }
                    }

                    // App Title & Comment
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            text: modelData.name
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                            color: root.selectedIndex === index ? Theme.accent : Theme.text
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Text {
                            text: modelData.comment ? modelData.comment : modelData.category
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.overlay0
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    // Category Tag
                    Rectangle {
                        implicitWidth: tagText.implicitWidth + 10
                        implicitHeight: 20
                        radius: 4
                        color: Theme.surface0

                        Text {
                            id: tagText
                            anchors.centerIn: parent
                            text: modelData.category
                            font.family: Theme.fontFamily
                            font.pixelSize: 10
                            color: Theme.subtext0
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onEntered: root.selectedIndex = index
                    onClicked: root.launchApp(modelData)
                }
            }

            // Empty state placeholder
            Text {
                anchors.centerIn: parent
                visible: root.filteredApps.length === 0
                text: "No applications found"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                color: Theme.overlay0
            }
        }

        // Bottom status bar / hints
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            Text {
                text: root.filteredApps.length + " Applications"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }

            Item { Layout.fillWidth: true }

            Row {
                spacing: 12

                Row {
                    spacing: 4
                    Text { text: "󰌌"; font.family: Theme.fontFamily; color: Theme.accent; font.pixelSize: Theme.fontSizeSmall }
                    Text { text: "Navigate: ↑ ↓"; font.family: Theme.fontFamily; color: Theme.overlay0; font.pixelSize: Theme.fontSizeSmall }
                }
                Row {
                    spacing: 4
                    Text { text: "󰌑"; font.family: Theme.fontFamily; color: Theme.accent; font.pixelSize: Theme.fontSizeSmall }
                    Text { text: "Launch: Enter"; font.family: Theme.fontFamily; color: Theme.overlay0; font.pixelSize: Theme.fontSizeSmall }
                }
                Row {
                    spacing: 4
                    Text { text: "󱊷"; font.family: Theme.fontFamily; color: Theme.accent; font.pixelSize: Theme.fontSizeSmall }
                    Text { text: "Close: Esc"; font.family: Theme.fontFamily; color: Theme.overlay0; font.pixelSize: Theme.fontSizeSmall }
                }
            }
        }
    }
}
