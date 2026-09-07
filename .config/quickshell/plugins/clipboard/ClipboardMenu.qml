import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 540
    implicitHeight: 480
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property var allItems: []
    property var filteredItems: []
    property int selectedIndex: 0

    function refreshClipboard() {
        if (!clipListProc.running) {
            clipListProc.running = true;
        }
    }

    function filterItems() {
        var q = searchInput.text.toLowerCase().trim();
        var list = [];
        for (var i = 0; i < root.allItems.length; i++) {
            var item = root.allItems[i];
            if (q.length === 0 || item.text.toLowerCase().indexOf(q) !== -1) {
                list.push(item);
            }
        }
        root.filteredItems = list;
        root.selectedIndex = 0;
    }

    function copyItem(item) {
        if (!item) return;
        PluginManager.closeAll();
        decodeProc.exec(["bash", "-c", "echo '" + item.raw + "' | cliphist decode | wl-copy && (command -v wtype >/dev/null 2>&1 && wtype -M ctrl -k v -m ctrl || true)"]);
    }

    function deleteItem(item) {
        if (!item) return;
        decodeProc.exec(["bash", "-c", "echo '" + item.raw + "' | cliphist delete"]);
        root.allItems = root.allItems.filter(it => it.id !== item.id);
        root.filterItems();
    }

    function clearAll() {
        decodeProc.exec(["cliphist", "wipe"]);
        root.allItems = [];
        root.filteredItems = [];
        PluginManager.closeAll();
    }

    Process {
        id: decodeProc
    }

    Process {
        id: clipListProc
        command: ["cliphist", "list"]
        stdout: SplitParser {
            onRead: data => {
                var lines = data.trim().split("\n");
                var items = [];
                for (var i = 0; i < lines.length; i++) {
                    var l = lines[i];
                    if (!l || l.trim().length === 0) continue;
                    var parts = l.split("\t");
                    var id = parts[0];
                    var txt = parts.slice(1).join("\t").trim();
                    items.push({
                        id: id,
                        text: txt,
                        raw: l
                    });
                }
                root.allItems = items;
                root.filterItems();
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
        root.refreshClipboard();
        searchInput.forceActiveFocus();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onClipboardVisibleChanged() {
            if (PluginManager.clipboardVisible) {
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
                implicitHeight: 40
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
                        text: "󰅍"
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
                        clip: true

                        Text {
                            text: "Search clipboard history..."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: Theme.overlay0
                            visible: !searchInput.text && !searchInput.activeFocus
                        }

                        onTextChanged: root.filterItems()
                        Keys.onEscapePressed: PluginManager.closeAll()
                        Keys.onReturnPressed: {
                            if (root.filteredItems.length > 0 && root.selectedIndex >= 0) {
                                root.copyItem(root.filteredItems[root.selectedIndex]);
                            }
                        }
                        Keys.onDownPressed: {
                            if (root.selectedIndex < root.filteredItems.length - 1) {
                                root.selectedIndex++;
                                clipListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                            }
                        }
                        Keys.onUpPressed: {
                            if (root.selectedIndex > 0) {
                                root.selectedIndex--;
                                clipListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                            }
                        }
                    }
                }
            }

            // Wipe button
            Rectangle {
                implicitWidth: 38
                implicitHeight: 40
                radius: Theme.pillRadius
                color: wipeArea.containsMouse ? Theme.red : Theme.moduleBg
                border.color: Theme.moduleBorder
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰆴"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon
                    color: wipeArea.containsMouse ? "#ffffff" : Theme.red
                }

                MouseArea {
                    id: wipeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.clearAll()
                }
            }
        }

        // Clipboard List
        ListView {
            id: clipListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.filteredItems
            spacing: 4

            delegate: Rectangle {
                id: itemRect
                required property var modelData
                required property int index

                width: clipListView.width
                implicitHeight: 44
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : "transparent"
                border.color: root.selectedIndex === index ? Theme.accent : "transparent"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 10

                    Text {
                        text: "󰅌"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.subtext0
                    }

                    Text {
                        Layout.fillWidth: true
                        text: modelData.text
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: root.selectedIndex === index ? Theme.accent : Theme.text
                        elide: Text.ElideRight
                    }

                    // Delete single item icon
                    Text {
                        text: "󰅖"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: delItemArea.containsMouse ? Theme.red : Theme.overlay0

                        MouseArea {
                            id: delItemArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.deleteItem(modelData)
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onEntered: root.selectedIndex = index
                    onClicked: root.copyItem(modelData)
                }
            }

            Text {
                anchors.centerIn: parent
                visible: root.filteredItems.length === 0
                text: "Clipboard history is empty"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                color: Theme.overlay0
            }
        }

        // Status row
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: root.filteredItems.length + " Items cached"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Enter to Paste • Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }
    }
}
