import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 860
    implicitHeight: 580
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

    function copyShortcut(item) {
        if (!item) return;
        PluginManager.closeAll();
        copyProc.exec([
            "bash", "-c",
            "wl-copy -- \"$1\" && (command -v notify-send >/dev/null 2>&1 && notify-send -a 'Shortcut Helper' -i preferences-desktop-keyboard-shortcuts \"⌨️ $1\" \"$2\n(Shortcut copied to clipboard)\" || true)",
            "_", item.key, item.desc
        ]);
    }

    Process {
        id: copyProc
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
        anchors.margins: 18
        spacing: 14

        // Header & Search
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 46
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
                        text: "󰌌"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeIcon + 2
                        color: Theme.accent
                    }

                    TextInput {
                        id: searchInput
                        Layout.fillWidth: true
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.text
                        selectByMouse: true

                        Text {
                            text: "Search shortcuts by key, action, or category..."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: Theme.overlay0
                            visible: !searchInput.text && !searchInput.activeFocus
                        }

                        onTextChanged: root.filterBinds()
                        Keys.onEscapePressed: PluginManager.closeAll()
                        Keys.onReturnPressed: {
                            if (root.filteredBinds.length > 0 && root.selectedIndex >= 0 && root.selectedIndex < root.filteredBinds.length) {
                                root.copyShortcut(root.filteredBinds[root.selectedIndex]);
                            }
                        }
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

                    // Clear button
                    Rectangle {
                        visible: searchInput.text.length > 0
                        implicitWidth: 22
                        implicitHeight: 22
                        radius: 11
                        color: clearMouse.containsMouse ? Theme.surface1 : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: "󰅖"
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            color: clearMouse.containsMouse ? Theme.red : Theme.overlay0
                        }

                        MouseArea {
                            id: clearMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                searchInput.text = "";
                                searchInput.forceActiveFocus();
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
            spacing: 5

            ScrollBar.vertical: ScrollBar {
                id: vbar
                active: true
                policy: ScrollBar.AsNeeded
                contentItem: Rectangle {
                    implicitWidth: 4
                    radius: 2
                    color: vbar.pressed ? Theme.accent : (vbar.hovered ? Theme.overlay0 : Qt.rgba(Theme.overlay0.r, Theme.overlay0.g, Theme.overlay0.b, 0.35))
                }
            }

            delegate: Rectangle {
                id: rowDelegate
                required property var modelData
                required property int index

                width: bindListView.width - (vbar.visible ? 8 : 0)
                implicitHeight: 46
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : "transparent"
                border.color: root.selectedIndex === index ? Theme.accent : "transparent"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 12

                    // Key combo pill badges
                    Row {
                        spacing: 4
                        Layout.alignment: Qt.AlignVCenter

                        Repeater {
                            model: {
                                var rawKey = rowDelegate.modelData.key || "";
                                var keys = rawKey.split("+");
                                var result = [];
                                for (var k = 0; k < keys.length; k++) {
                                    var trimmed = keys[k].trim();
                                    if (trimmed.length > 0) {
                                        result.push(trimmed);
                                    }
                                }
                                return result;
                            }

                            Rectangle {
                                required property var modelData
                                required property int index

                                implicitWidth: keyTxt.implicitWidth + 12
                                implicitHeight: 26
                                radius: 6
                                color: root.selectedIndex === rowDelegate.index ? Theme.surface1 : Theme.surface0
                                border.color: root.selectedIndex === rowDelegate.index ? Theme.accent : Theme.surface2
                                border.width: 1

                                Text {
                                    id: keyTxt
                                    anchors.centerIn: parent
                                    text: parent.modelData
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: root.selectedIndex === rowDelegate.index ? Theme.accent : Theme.text
                                }
                            }
                        }
                    }

                    Text {
                        text: "➜"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: root.selectedIndex === index ? Theme.accent : Theme.overlay0
                    }

                    // Description
                    Text {
                        Layout.fillWidth: true
                        text: modelData.desc
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        font.weight: root.selectedIndex === index ? Font.DemiBold : Font.Normal
                        color: root.selectedIndex === index ? Theme.text : Theme.subtext1
                        elide: Text.ElideRight
                    }

                    // Category Tag Badge
                    Rectangle {
                        implicitWidth: Math.min(220, catTxt.implicitWidth + 16)
                        implicitHeight: 22
                        radius: 6
                        color: root.selectedIndex === index ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.16) : Qt.rgba(Theme.surface0.r, Theme.surface0.g, Theme.surface0.b, 0.6)
                        border.color: root.selectedIndex === index ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.35) : Theme.surface1
                        border.width: 1

                        Text {
                            id: catTxt
                            anchors.centerIn: parent
                            width: parent.width - 12
                            text: modelData.category.replace(/^[^\w\s]+/, '').trim()
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            color: root.selectedIndex === index ? Theme.accent : Theme.subtext0
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onEntered: root.selectedIndex = index
                    onClicked: root.copyShortcut(modelData)
                }
            }
        }

        // Status Row
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            RowLayout {
                spacing: 6
                Text {
                    text: "󰌌"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.accent
                }
                Text {
                    text: root.filteredBinds.length + (root.filteredBinds.length === 1 ? " shortcut configured" : " shortcuts configured")
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.subtext0
                }
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "↑↓ Navigate  •  ↵ Copy  •  Esc Close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }
    }
}
