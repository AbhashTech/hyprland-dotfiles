import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 540
    implicitHeight: 500
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property var allItems: []
    property var filteredItems: []
    property int selectedIndex: 0
    property string activeCategory: "all"

    function refreshClipboard() {
        if (!clipListProc.running) {
            clipListProc.running = true;
        }
    }

    function filterItems() {
        var q = searchInput.text.toLowerCase().trim();
        var cat = root.activeCategory;
        var list = [];
        for (var i = 0; i < root.allItems.length; i++) {
            var item = root.allItems[i];
            if (cat !== "all" && item.category !== cat) {
                continue;
            }
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
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "copy", item.id, item.raw]);
    }

    function deleteItem(item) {
        if (!item) return;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "delete", item.id, item.raw]);
        root.allItems = root.allItems.filter(it => it.id !== item.id);
        root.filterItems();
    }

    function clearAll() {
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "wipe"]);
        root.allItems = [];
        root.filteredItems = [];
        PluginManager.closeAll();
    }

    Process {
        id: ctlProc
    }

    Process {
        id: clipListProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "list"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (Array.isArray(parsed)) {
                        root.allItems = parsed;
                        root.filterItems();
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
        root.activeCategory = "all";
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
        spacing: 10

        // Search Header
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
                            if (root.filteredItems.length > 0 && root.selectedIndex >= 0 && root.selectedIndex < root.filteredItems.length) {
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

        // Category Filter Tabs
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: [
                    { id: "all", label: "All", icon: "󰅍" },
                    { id: "image", label: "Images", icon: "󰋩" },
                    { id: "code", label: "Code", icon: "󰅪" },
                    { id: "url", label: "Links", icon: "󰖟" },
                    { id: "text", label: "Text", icon: "󰉿" }
                ]

                Rectangle {
                    required property var modelData
                    implicitHeight: 26
                    implicitWidth: catLabelRow.implicitWidth + 16
                    radius: 13
                    color: root.activeCategory === modelData.id ? Theme.accent : (catMouse.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg)
                    border.color: root.activeCategory === modelData.id ? Theme.accent : Theme.moduleBorder
                    border.width: 1

                    RowLayout {
                        id: catLabelRow
                        anchors.centerIn: parent
                        spacing: 4

                        Text {
                            text: modelData.icon
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            color: root.activeCategory === modelData.id ? Theme.crust : Theme.subtext0
                        }

                        Text {
                            text: modelData.label
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: root.activeCategory === modelData.id
                            color: root.activeCategory === modelData.id ? Theme.crust : Theme.text
                        }
                    }

                    MouseArea {
                        id: catMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeCategory = modelData.id;
                            root.filterItems();
                        }
                    }
                }
            }

            Item { Layout.fillWidth: true }
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
                implicitHeight: modelData.isImage && modelData.thumbnail ? 56 : 44
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : "transparent"
                border.color: root.selectedIndex === index ? Theme.accent : "transparent"
                border.width: 1

                // Row content
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 10

                    // Thumbnail image or Category icon
                    Item {
                        implicitWidth: 28
                        implicitHeight: 28
                        Layout.alignment: Qt.AlignVCenter

                        Image {
                            visible: modelData.isImage && modelData.thumbnail !== ""
                            anchors.fill: parent
                            source: modelData.thumbnail ? "file://" + modelData.thumbnail : ""
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                        }

                        Text {
                            visible: !modelData.isImage || !modelData.thumbnail
                            anchors.centerIn: parent
                            text: modelData.icon || "󰅍"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: root.selectedIndex === index ? Theme.accent : (modelData.isImage ? Theme.peach : Theme.subtext0)
                        }
                    }

                    // Text Content (Clickable)
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ColumnLayout {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2

                            Text {
                                Layout.fillWidth: true
                                text: modelData.text
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold: root.selectedIndex === index
                                color: root.selectedIndex === index ? Theme.accent : Theme.text
                                elide: Text.ElideRight
                            }

                            Text {
                                visible: modelData.category !== "text"
                                text: modelData.category.toUpperCase()
                                font.family: Theme.fontFamily
                                font.pixelSize: 9
                                font.bold: true
                                color: Theme.overlay0
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

                    // Delete single item icon
                    Rectangle {
                        implicitWidth: 26
                        implicitHeight: 26
                        radius: 13
                        color: delItemArea.containsMouse ? Theme.red : "transparent"
                        z: 10

                        Text {
                            anchors.centerIn: parent
                            text: "󰅖"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: delItemArea.containsMouse ? "#ffffff" : Theme.overlay0
                        }

                        MouseArea {
                            id: delItemArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.deleteItem(modelData)
                        }
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: root.filteredItems.length === 0
                text: "No clipboard items found"
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
