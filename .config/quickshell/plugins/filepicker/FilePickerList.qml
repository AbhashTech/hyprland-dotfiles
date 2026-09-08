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

    // ── Signals ───────────────────────────────────────────────────────────────
    signal entryClicked(var entry)
    signal entryDoubleClicked(var entry)
    signal selectionToggled(string path)
    signal itemFocusChanged(int index)

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
            anchors.leftMargin:  40
            anchors.rightMargin: 12
            spacing: 0

            Text {
                Layout.fillWidth: true
                text:           "Name"
                font.family:    Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold:      true
                color:          Theme.overlay0
            }
            Text {
                Layout.preferredWidth: 72
                text:           "Size"
                font.family:    Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold:      true
                color:          Theme.overlay0
                horizontalAlignment: Text.AlignRight
            }
            Text {
                Layout.preferredWidth: 130
                text:           "Modified"
                font.family:    Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold:      true
                color:          Theme.overlay0
                horizontalAlignment: Text.AlignRight
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

                // Multi-select checkbox / icon
                Rectangle {
                    implicitWidth:  22
                    implicitHeight: 22
                    radius:         multiSelect ? 5 : 11
                    color:          isSelected
                                        ? Theme.accent
                                        : (multiSelect ? Theme.moduleBg : "transparent")
                    border.color:   multiSelect ? (isSelected ? Theme.accent : Theme.moduleBorder) : "transparent"
                    border.width:   1

                    Text {
                        anchors.centerIn: parent
                        text:           multiSelect
                                            ? (isSelected ? "" : "")
                                            : modelData.icon
                        font.family:    Theme.fontFamily
                        font.pixelSize: multiSelect ? 11 : 14
                        color:          multiSelect
                                            ? (isSelected ? Theme.crust : Theme.overlay0)
                                            : (isSelected ? Theme.accent : (modelData.isDir ? Theme.blue : Theme.subtext0))
                    }

                    // Non-multiselect: show thumbnail for images
                    Image {
                        anchors.fill:  parent
                        visible:       !multiSelect && modelData.thumbnail !== "" && modelData.thumbnail !== undefined
                        source:        (modelData.thumbnail && modelData.thumbnail !== "") ? ("file://" + modelData.thumbnail) : ""
                        fillMode:      Image.PreserveAspectCrop
                        asynchronous:  true
                        smooth:        true
                        layer.enabled: true
                        layer.effect: null
                        // Rounded clip
                        Rectangle {
                            anchors.fill: parent
                            radius:       11
                            color:        "transparent"
                        }
                    }
                }

                // File name
                Text {
                    Layout.fillWidth: true
                    text:           modelData.name
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold:      isSelected || (modelData.isDir && isFocused)
                    color:          isSelected
                                        ? Theme.accent
                                        : (modelData.isDir ? Theme.blue : Theme.text)
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

                // Size
                Text {
                    Layout.preferredWidth: 72
                    text:            modelData.sizeStr
                    font.family:     Theme.fontFamily
                    font.pixelSize:  Theme.fontSizeSmall
                    color:           Theme.overlay0
                    horizontalAlignment: Text.AlignRight
                    visible:         !modelData.isDir
                }
                Item { Layout.preferredWidth: 72; visible: modelData.isDir }

                // Modified date
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

                onEntered:    listRoot.focusIndex = index

                onClicked: (mouse) => {
                    listRoot.focusIndex = index
                    if (listRoot.multiSelect) {
                        listRoot.selectionToggled(modelData.path)
                    } else {
                        listRoot.entryClicked(modelData)
                    }
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
