import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 700
    implicitHeight: 520
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property var allBinds: []
    property var filteredBinds: []
    property int selectedIndex: 0

    function refreshKeybinds() {
        if (!keybindProc.running) {
            keybindProc.running = true;
        }
    }

    function filterBinds() {
        var q = searchInput.text.toLowerCase().trim();
        var list = [];
        for (var i = 0; i < root.allBinds.length; i++) {
            var b = root.allBinds[i];
            if (q.length === 0 || b.key.toLowerCase().indexOf(q) !== -1 || b.desc.toLowerCase().indexOf(q) !== -1 || b.category.toLowerCase().indexOf(q) !== -1) {
                list.push(b);
            }
        }
        root.filteredBinds = list;
        root.selectedIndex = 0;
    }

    Process {
        id: keybindProc
        command: ["python3", Quickshell.env("HOME") + "/.config/hypr/scripts/keybinds_viewer.py", "--json"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (Array.isArray(parsed)) {
                        root.allBinds = parsed;
                        root.filterBinds();
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
        searchInput.text = "";
        root.refreshKeybinds();
        searchInput.forceActiveFocus();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onKeybindsVisibleChanged() {
            if (PluginManager.keybindsVisible) {
                root.grabFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header & Search
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 42
                radius: Theme.pillRadius
                color: Theme.moduleBg
                border.color: searchInput.activeFocus ? Theme.accent : Theme.moduleBorder
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8

                    Text {
                        text: "󰌌"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeIcon
                        color: Theme.accent
                    }

                    TextInput {
                        id: searchInput
                        Layout.fillWidth: true
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.text

                        Text {
                            text: "Search shortcuts by key or description..."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: Theme.overlay0
                            visible: !searchInput.text && !searchInput.activeFocus
                        }

                        onTextChanged: root.filterBinds()
                        Keys.onEscapePressed: PluginManager.closeAll()
                        Keys.onDownPressed: {
                            if (root.selectedIndex < root.filteredBinds.length - 1) {
                                root.selectedIndex++;
                                bindListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                            }
                        }
                        Keys.onUpPressed: {
                            if (root.selectedIndex > 0) {
                                root.selectedIndex--;
                                bindListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                            }
                        }
                    }
                }
            }
        }

        // Keybinds List
        ListView {
            id: bindListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.filteredBinds
            spacing: 4

            delegate: Rectangle {
                required property var modelData
                required property int index

                width: bindListView.width
                implicitHeight: 42
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : "transparent"
                border.color: root.selectedIndex === index ? Theme.accent : "transparent"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 12

                    // Key combo pill
                    Rectangle {
                        implicitWidth: keyTxt.implicitWidth + 14
                        implicitHeight: 26
                        radius: 6
                        color: Theme.surface0
                        border.color: Theme.surface1
                        border.width: 1

                        Text {
                            id: keyTxt
                            anchors.centerIn: parent
                            text: modelData.key
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.accent
                        }
                    }

                    Text {
                        text: "➜"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.overlay0
                    }

                    // Description
                    Text {
                        Layout.fillWidth: true
                        text: modelData.desc
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.text
                        elide: Text.ElideRight
                    }

                    // Category Tag
                    Rectangle {
                        implicitWidth: catTxt.implicitWidth + 8
                        implicitHeight: 18
                        radius: 4
                        color: Theme.surface0

                        Text {
                            id: catTxt
                            anchors.centerIn: parent
                            text: modelData.category.replace(/^[^\w\s]+/, '').trim()
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
                }
            }
        }

        // Status Row
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: root.filteredBinds.length + " Shortcuts configured"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }
    }
}
