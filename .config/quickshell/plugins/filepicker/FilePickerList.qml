import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import "../.."

// File list view: icon | name | size | date — keyboard navigable, multi-select aware
Rectangle {
    id: listRoot

    color: "transparent"

    // ── In-props ─────────────────────────────────────────────────────────────
    property var    entries:       []
    property var    selectedPaths: []
    property bool   multiSelect:   false
    property int    focusIndex:    0
    property string sortBy:        "name"
    property bool   sortAsc:       true

    // ── Signals ───────────────────────────────────────────────────────────────
    signal entryClicked(var entry)
    signal entryDoubleClicked(var entry)
    signal selectionToggled(string path)
    signal itemFocusChanged(int index)
    signal sortRequested(string by)

    // ── Computed ──────────────────────────────────────────────────────────────
    function isSelected(path) {
        return selectedPaths.indexOf(path) !== -1
    }

    function moveFocus(delta) {
        var next = Math.max(0, Math.min(listView.count - 1, focusIndex + delta))
        focusIndex = next
        listView.positionViewAtIndex(next, ListView.Contain)
        itemFocusChanged(next)
    }

    function activateFocused() {
        if (focusIndex >= 0 && focusIndex < entries.length) {
            entryDoubleClicked(entries[focusIndex])
        }
    }

    function getItemIcon(entry) {
        if (!entry) return "󰈚"
        if (entry.isDir) return "󰉋"
        var ext = (entry.name || "").toLowerCase()
        if (ext.endsWith(".pdf")) return "󰈦"
        if (ext.endsWith(".zip") || ext.endsWith(".tar") || ext.endsWith(".tar.gz") || ext.endsWith(".tar.xz") || ext.endsWith(".7z") || ext.endsWith(".gz") || ext.endsWith(".bz2")) return "󰛫"
        if (entry.category === "image") return "󰈟"
        if (entry.category === "video") return "󰕧"
        if (entry.category === "audio") return "󰎆"
        if (entry.category === "document") return "󰈦"
        if (entry.category === "code") return "󰅩"
        if (entry.category === "archive") return "󰛫"
        if (entry.category === "text") return "󰈙"
        return "󰈚"
    }

    function getItemColor(entry) {
        if (!entry) return Theme.subtext0
        if (entry.isDir) return Theme.peach
        var ext = (entry.name || "").toLowerCase()
        if (ext.endsWith(".pdf")) return Theme.red
        if (entry.category === "image") return Theme.teal
        if (entry.category === "video") return Theme.peach
        if (entry.category === "audio") return Theme.mauve
        if (entry.category === "document") return Theme.blue
        if (entry.category === "code") return Theme.green
        if (entry.category === "archive") return Theme.yellow
        if (entry.category === "text") return Theme.subtext0
        return Theme.subtext0
    }

    function getFileTypeStr(entry) {
        if (!entry) return ""
        if (entry.isDir) return "Folder"
        var name = entry.name || ""
        var dot = name.lastIndexOf(".")
        if (dot > 0 && dot < name.length - 1) {
            var ext = name.substring(dot + 1).toUpperCase()
            if (ext.length <= 6) return ext
        }
        return "File"
    }

    // ── Column headers ────────────────────────────────────────────────────────
    Rectangle {
        id:             header
        anchors.top:    parent.top
        anchors.left:   parent.left
        anchors.right:  parent.right
        implicitHeight: 26
        color:          Qt.rgba(Theme.crust.r, Theme.crust.g, Theme.crust.b, 0.5)
        radius:         Theme.pillRadius

        RowLayout {
            anchors.fill:        parent
            anchors.leftMargin:  listRoot.multiSelect ? 68 : 42
            anchors.rightMargin: 12
            spacing: 0

            // Name column
            Rectangle {
                Layout.fillWidth: true
                implicitHeight:   24
                color:            "transparent"

                RowLayout {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text:           "Name"
                        font.family:    Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold:      true
                        color:          listRoot.sortBy === "name" ? Theme.accent : Theme.overlay0
                    }
                    Text {
                        visible:        listRoot.sortBy === "name"
                        text:           listRoot.sortAsc ? "↑" : "↓"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 11
                        color:          Theme.accent
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape:  Qt.PointingHandCursor
                    onClicked:    listRoot.sortRequested("name")
                }
            }

            // Type column
            Rectangle {
                Layout.preferredWidth: 68
                implicitHeight:        24
                color:                 "transparent"

                RowLayout {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text:           "Type"
                        font.family:    Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold:      true
                        color:          (listRoot.sortBy === "type" || listRoot.sortBy === "category") ? Theme.accent : Theme.overlay0
                    }
                    Text {
                        visible:        listRoot.sortBy === "type" || listRoot.sortBy === "category"
                        text:           listRoot.sortAsc ? "↑" : "↓"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 11
                        color:          Theme.accent
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape:  Qt.PointingHandCursor
                    onClicked:    listRoot.sortRequested("type")
                }
            }

            // Size column
            Rectangle {
                Layout.preferredWidth: 72
                implicitHeight:        24
                color:                 "transparent"

                RowLayout {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text:           "Size"
                        font.family:    Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold:      true
                        color:          listRoot.sortBy === "size" ? Theme.accent : Theme.overlay0
                    }
                    Text {
                        visible:        listRoot.sortBy === "size"
                        text:           listRoot.sortAsc ? "↑" : "↓"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 11
                        color:          Theme.accent
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape:  Qt.PointingHandCursor
                    onClicked:    listRoot.sortRequested("size")
                }
            }

            // Modified column
            Rectangle {
                Layout.preferredWidth: 130
                implicitHeight:        24
                color:                 "transparent"

                RowLayout {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text:           "Modified"
                        font.family:    Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold:      true
                        color:          (listRoot.sortBy === "date" || listRoot.sortBy === "modified") ? Theme.accent : Theme.overlay0
                    }
                    Text {
                        visible:        listRoot.sortBy === "date" || listRoot.sortBy === "modified"
                        text:           listRoot.sortAsc ? "↑" : "↓"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 11
                        color:          Theme.accent
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape:  Qt.PointingHandCursor
                    onClicked:    listRoot.sortRequested("date")
                }
            }
        }
    }

    // ── File list ─────────────────────────────────────────────────────────────
    ListView {
        id:            listView
        anchors.top:   header.bottom
        anchors.left:  parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: 4
        clip:          true
        model:         listRoot.entries
        spacing:       2

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            width:  6
        }

        delegate: Rectangle {
            id:              fileRow
            required property var modelData
            required property int index

            width:           listView.width - 6
            implicitHeight:  38
            radius:          Theme.pillRadius

            readonly property bool isFocused:  listRoot.focusIndex === index
            readonly property bool isSelected: listRoot.isSelected(modelData.path)

            color: isSelected
                       ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.22)
                       : isFocused
                           ? Theme.moduleHoverBg
                           : (rowHover.containsMouse ? Qt.rgba(Theme.surface0.r, Theme.surface0.g, Theme.surface0.b, 0.5) : "transparent")

            border.color: isSelected ? Theme.accent : (isFocused ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.5) : "transparent")
            border.width: 1

            RowLayout {
                anchors.fill:        parent
                anchors.leftMargin:  8
                anchors.rightMargin: 12
                spacing: 8

                // 1. Separate Multi-select checkbox
                Rectangle {
                    visible:        listRoot.multiSelect
                    implicitWidth:  18
                    implicitHeight: 18
                    radius:         4
                    color:          isSelected ? Theme.accent : Theme.moduleBg
                    border.color:   isSelected ? Theme.accent : Theme.moduleBorder
                    border.width:   1

                    Text {
                        anchors.centerIn: parent
                        visible:        isSelected
                        text:           "✓"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 11
                        font.bold:      true
                        color:          Theme.crust
                    }
                }

                // 2. Folder / File Icon container (ALWAYS VISIBLE!)
                Rectangle {
                    implicitWidth:  26
                    implicitHeight: 26
                    radius:         6
                    readonly property color itemCol: listRoot.getItemColor(modelData)
                    color:          Qt.rgba(itemCol.r, itemCol.g, itemCol.b, 0.16)
                    border.color:   Qt.rgba(itemCol.r, itemCol.g, itemCol.b, 0.35)
                    border.width:   1

                    Text {
                        anchors.centerIn: parent
                        visible:        !(modelData.category === "image" && modelData.thumbnail && modelData.thumbnail !== "")
                        text:           listRoot.getItemIcon(modelData)
                        font.family:    Theme.fontFamily
                        font.pixelSize: modelData.isDir ? 16 : 14
                        color:          parent.itemCol
                    }

                    // Thumbnail for images if available
                    Image {
                        anchors.fill:    parent
                        anchors.margins: 1
                        visible:         modelData.category === "image" && modelData.thumbnail !== "" && modelData.thumbnail !== undefined
                        source:          (modelData.thumbnail && modelData.thumbnail !== "") ? ("file://" + modelData.thumbnail) : ""
                        fillMode:        Image.PreserveAspectCrop
                        asynchronous:    true
                        smooth:          true
                    }
                }

                // 3. File / Folder name
                Text {
                    Layout.fillWidth: true
                    text:           modelData.name
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold:      modelData.isDir || isSelected
                    color:          isSelected
                                        ? Theme.accent
                                        : (modelData.isDir ? Theme.peach : Theme.text)
                    elide:          Text.ElideMiddle

                    // Symlink badge
                    Text {
                        anchors.right:  parent.right
                        anchors.top:    parent.top
                        visible:        modelData.isSymlink
                        text:           "󰁔"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 9
                        color:          Theme.overlay0
                    }
                }

                // 4. Type / Extension column
                Text {
                    Layout.preferredWidth: 68
                    text:            listRoot.getFileTypeStr(modelData)
                    font.family:     Theme.fontFamily
                    font.pixelSize:  Theme.fontSizeSmall
                    font.bold:       modelData.isDir
                    color:           modelData.isDir ? Theme.peach : Theme.overlay0
                    horizontalAlignment: Text.AlignRight
                    elide:           Text.ElideRight
                }

                // 5. Size column
                Text {
                    Layout.preferredWidth: 72
                    text:            modelData.sizeStr
                    font.family:     Theme.fontFamily
                    font.pixelSize:  Theme.fontSizeSmall
                    color:           Theme.overlay0
                    horizontalAlignment: Text.AlignRight
                }

                // 6. Modified date column
                Text {
                    Layout.preferredWidth: 130
                    text:            modelData.modifiedStr
                    font.family:     Theme.fontFamily
                    font.pixelSize:  Theme.fontSizeSmall
                    color:           Theme.overlay0
                    horizontalAlignment: Text.AlignRight
                }
            }

            MouseArea {
                id:          rowHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape:  Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onClicked: (mouse) => {
                    listRoot.focusIndex = index
                    listRoot.entryClicked(modelData)
                }

                onDoubleClicked: (mouse) => {
                    listRoot.entryDoubleClicked(modelData)
                }
            }
        }

        Text {
            anchors.centerIn: parent
            visible:          listRoot.entries.length === 0
            text:             "No files found"
            font.family:      Theme.fontFamily
            font.pixelSize:   Theme.fontSizeLarge
            color:            Theme.overlay0
        }
    }
}
