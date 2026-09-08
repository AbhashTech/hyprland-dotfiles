import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import "../.."

// Thumbnail grid view — auto-used when MIME filter = image/video, or user toggles
Rectangle {
    id: gridRoot

    color: "transparent"

    property var    entries:       []
    property var    selectedPaths: []
    property bool   multiSelect:   false
    property int    focusIndex:    0

    signal entryClicked(var entry)
    signal entryDoubleClicked(var entry)
    signal selectionToggled(string path)
    signal itemFocusChanged(int index)

    readonly property int cellSize:   120
    readonly property int cellSpacing: 8

    function isSelected(path) {
        return selectedPaths.indexOf(path) !== -1
    }

    function moveFocus(delta) {
        var cols  = Math.floor(gridView.width / (cellSize + cellSpacing)) || 1
        var next  = Math.max(0, Math.min(gridView.count - 1, focusIndex + delta))
        focusIndex = next
        gridView.positionViewAtIndex(next, GridView.Contain)
        itemFocusChanged(next)
    }

    function activateFocused() {
        if (focusIndex >= 0 && focusIndex < entries.length) {
            entryDoubleClicked(entries[focusIndex])
        }
    }

    GridView {
        id:              gridView
        anchors.fill:    parent
        clip:            true
        model:           gridRoot.entries
        cellWidth:       gridRoot.cellSize + gridRoot.cellSpacing
        cellHeight:      gridRoot.cellSize + gridRoot.cellSpacing + 24
        leftMargin:      4
        topMargin:       4

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            width:  6
        }

        delegate: Rectangle {
            id:       gridCell
            required property var modelData
            required property int index

            width:   gridRoot.cellSize
            height:  gridRoot.cellSize + 24
            radius:  Theme.pillRadius

            readonly property bool isFocused:  gridRoot.focusIndex === index
            readonly property bool isSelected: gridRoot.isSelected(modelData.path)

            color:  isSelected
                        ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.22)
                        : isFocused
                            ? Theme.moduleHoverBg
                            : (cellHover.containsMouse ? Qt.rgba(Theme.surface0.r, Theme.surface0.g, Theme.surface0.b, 0.5) : "transparent")
            border.color: isSelected ? Theme.accent : (isFocused ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.5) : "transparent")
            border.width: 1

            ColumnLayout {
                anchors.fill:    parent
                anchors.margins: 6
                spacing:         4

                // Thumbnail / Icon area
                Rectangle {
                    Layout.fillWidth:  true
                    Layout.fillHeight: true
                    radius:            8
                    color:             Theme.moduleBg
                    clip:              true

                    // Image thumbnail
                    Image {
                        anchors.fill:  parent
                        visible:       modelData.thumbnail !== "" && modelData.thumbnail !== undefined
                        source:        (modelData.thumbnail && modelData.thumbnail !== "")
                                           ? ("file://" + modelData.thumbnail) : ""
                        fillMode:      Image.PreserveAspectCrop
                        asynchronous:  true
                        smooth:        true
                    }

                    // MIME icon fallback
                    Text {
                        anchors.centerIn: parent
                        visible:         !modelData.thumbnail
                        text:            modelData.isDir ? "󰉋" : (modelData.icon || "󰈔")
                        font.family:     Theme.fontFamily
                        font.pixelSize:  32
                        color:           modelData.isDir
                                             ? Theme.blue
                                             : (isSelected ? Theme.accent : Theme.subtext0)
                    }

                    // Selection checkmark badge
                    Rectangle {
                        visible:      isSelected
                        anchors.top:  parent.top
                        anchors.right: parent.right
                        anchors.margins: 4
                        width:  20
                        height: 20
                        radius: 10
                        color:  Theme.accent

                        Text {
                            anchors.centerIn: parent
                            text:           ""
                            font.family:    Theme.fontFamily
                            font.pixelSize: 10
                            color:          Theme.crust
                        }
                    }

                    // Directory badge
                    Rectangle {
                        visible:      modelData.isDir
                        anchors.bottom:  parent.bottom
                        anchors.left:    parent.left
                        anchors.margins: 4
                        implicitWidth:  dirCountText.implicitWidth + 8
                        implicitHeight: 16
                        radius:         8
                        color:          Qt.rgba(Theme.crust.r, Theme.crust.g, Theme.crust.b, 0.75)

                        Text {
                            id:             dirCountText
                            anchors.centerIn: parent
                            text:           "Folder"
                            font.family:    Theme.fontFamily
                            font.pixelSize: 9
                            color:          Theme.blue
                        }
                    }
                }

                // File name label
                Text {
                    Layout.fillWidth: true
                    text:            modelData.name
                    font.family:     Theme.fontFamily
                    font.pixelSize:  Theme.fontSizeSmall
                    font.bold:       isSelected
                    color:           isSelected ? Theme.accent : (modelData.isDir ? Theme.blue : Theme.text)
                    elide:           Text.ElideRight
                    horizontalAlignment: Text.AlignHCenter
                }
            }

            MouseArea {
                id:          cellHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape:  Qt.PointingHandCursor

                onEntered:       gridRoot.focusIndex = index
                onClicked:  (mouse) => {
                    gridRoot.focusIndex = index
                    if (gridRoot.multiSelect) {
                        gridRoot.selectionToggled(modelData.path)
                    } else {
                        gridRoot.entryClicked(modelData)
                    }
                }
                onDoubleClicked: (mouse) => {
                    gridRoot.entryDoubleClicked(modelData)
                }
            }
        }

        Text {
            anchors.centerIn: parent
            visible:          gridRoot.entries.length === 0
            text:             "No files found"
            font.family:      Theme.fontFamily
            font.pixelSize:   Theme.fontSizeLarge
            color:            Theme.overlay0
        }
    }
}
