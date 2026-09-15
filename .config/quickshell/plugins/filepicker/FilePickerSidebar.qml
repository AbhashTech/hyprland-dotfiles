import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import "../.."

// Left sidebar: quick links, custom bookmarks, recent directories
Rectangle {
    id: sidebar

    implicitWidth:  175
    implicitHeight: 500
    color:          "transparent"

    // Signals emitted when user clicks a location or manages bookmarks
    signal navigateTo(string path)
    signal addBookmarkRequested(string path)
    signal removeBookmark(string path)

    // ── Data properties (populated by FilePickerModal) ──────────────────────
    property var quickLinks:  []
    property var bookmarks:   []
    property var recentDirs:  []

    property string currentPath: ""

    // ── Helper ───────────────────────────────────────────────────────────────
    function isActive(path) {
        return currentPath === path
    }

    // ── Scrollable Sidebar Container ──────────────────────────────────────────
    Flickable {
        anchors.fill:    parent
        contentWidth:    width
        contentHeight:   sideCol.implicitHeight
        clip:            true
        boundsBehavior:  Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
            width:  4
        }

        ColumnLayout {
            id:              sideCol
            width:           parent.width
            spacing:         0

            // ── Quick Links ──────────────────────────────────────────────────────
            Text {
                Layout.fillWidth:  true
                Layout.leftMargin: 12
                Layout.topMargin:  12
                Layout.bottomMargin: 4
                text:      "PLACES"
                font.family:    Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold:      true
                font.letterSpacing: 1.2
                color:     Theme.overlay0
            }

            Repeater {
                model: sidebar.quickLinks

                delegate: SidebarEntry {
                    required property var modelData
                    Layout.fillWidth: true
                    entryName:   modelData.name
                    entryPath:   modelData.path
                    entryIcon:   modelData.icon
                    active:      sidebar.isActive(modelData.path)
                    onClicked:   sidebar.navigateTo(modelData.path)
                }
            }

            // ── Bookmarks ────────────────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth:  true
                Layout.topMargin:  8
                Layout.bottomMargin: 0
                implicitHeight:    1
                color:             Theme.barBorder
                opacity:           0.5
                visible:           sidebar.bookmarks.length > 0 || sidebar.currentPath !== ""
            }

            RowLayout {
                Layout.fillWidth:    true
                Layout.leftMargin:   12
                Layout.rightMargin:  8
                Layout.topMargin:    8
                Layout.bottomMargin: 4
                visible:             sidebar.bookmarks.length > 0 || sidebar.currentPath !== ""

                Text {
                    Layout.fillWidth: true
                    text:             "BOOKMARKS"
                    font.family:      Theme.fontFamily
                    font.pixelSize:   Theme.fontSizeSmall
                    font.bold:        true
                    font.letterSpacing: 1.2
                    color:            Theme.overlay0
                }

                Rectangle {
                    implicitWidth:  20
                    implicitHeight: 20
                    radius:         4
                    color:          addBmMouse.containsMouse ? Theme.moduleHoverBg : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text:           "+"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 14
                        font.bold:      true
                        color:          addBmMouse.containsMouse ? Theme.accent : Theme.overlay0
                    }

                    MouseArea {
                        id:          addBmMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    sidebar.addBookmarkRequested(sidebar.currentPath)
                    }

                    ToolTip.visible: addBmMouse.containsMouse
                    ToolTip.text:    "Bookmark current folder (Ctrl+D)"
                    ToolTip.delay:   300
                }
            }

            Repeater {
                model: sidebar.bookmarks

                delegate: SidebarEntry {
                    required property var modelData
                    Layout.fillWidth: true
                    entryName:   modelData.name
                    entryPath:   modelData.path
                    entryIcon:   modelData.icon || "󰉋"
                    active:      sidebar.isActive(modelData.path)
                    showRemove:  true
                    onClicked:   sidebar.navigateTo(modelData.path)
                    onRemove:    sidebar.removeBookmark(modelData.path)
                }
            }

            // ── Recent Dirs ──────────────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth:  true
                Layout.topMargin:  8
                Layout.bottomMargin: 0
                implicitHeight:    1
                color:             Theme.barBorder
                opacity:           0.5
                visible:           sidebar.recentDirs.length > 0
            }

            Text {
                Layout.fillWidth:  true
                Layout.leftMargin: 12
                Layout.topMargin:  8
                Layout.bottomMargin: 4
                text:      "RECENT"
                font.family:    Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold:      true
                font.letterSpacing: 1.2
                color:     Theme.overlay0
                visible:   sidebar.recentDirs.length > 0
            }

            Repeater {
                model: sidebar.recentDirs.slice(0, 5)

                delegate: SidebarEntry {
                    required property var modelData
                    Layout.fillWidth: true
                    entryName:   modelData.name
                    entryPath:   modelData.path
                    entryIcon:   "󰉋"
                    active:      sidebar.isActive(modelData.path)
                    onClicked:   sidebar.navigateTo(modelData.path)
                }
            }

            Item { Layout.fillHeight: true; implicitHeight: 12 }
        }
    }

    // ── Inline: Sidebar row delegate ─────────────────────────────────────────
    component SidebarEntry: Item {
        id: entryRoot
        property string entryName:  ""
        property string entryPath:  ""
        property string entryIcon:  "󰉋"
        property bool   active:     false
        property bool   showRemove: false

        signal clicked()
        signal remove()

        implicitHeight: 30

        Rectangle {
            id:             rowBg
            anchors.fill:   parent
            anchors.leftMargin:  4
            anchors.rightMargin: 4
            radius:         6
            color:          active
                                ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.18)
                                : (itemClickMouse.containsMouse ? Theme.moduleHoverBg : "transparent")
            border.color:   active ? Theme.accent : "transparent"
            border.width:   1

            RowLayout {
                anchors.fill:        parent
                anchors.leftMargin:  8
                anchors.rightMargin: 6
                spacing: 6

                // Clickable area for navigating to the folder
                Item {
                    Layout.fillWidth:  true
                    Layout.fillHeight: true

                    RowLayout {
                        anchors.fill: parent
                        spacing:      6

                        Text {
                            text:           entryIcon
                            font.family:    Theme.fontFamily
                            font.pixelSize: 13
                            color:          active ? Theme.accent : Theme.subtext0
                        }

                        Text {
                            Layout.fillWidth: true
                            text:           entryName
                            font.family:    Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold:      active
                            color:          active ? Theme.accent : Theme.text
                            elide:          Text.ElideRight
                        }
                    }

                    MouseArea {
                        id:          itemClickMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    entryRoot.clicked()
                    }
                }

                // Remove bookmark button (separate non-overlapping click target)
                Rectangle {
                    visible:        showRemove
                    implicitWidth:  18
                    implicitHeight: 18
                    radius:         4
                    color:          removeMouse.containsMouse ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.20) : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text:           "󰅖"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 11
                        color:          removeMouse.containsMouse ? Theme.red : Theme.subtext0
                    }

                    MouseArea {
                        id:          removeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    entryRoot.remove()
                    }

                    ToolTip.visible: removeMouse.containsMouse
                    ToolTip.text:    "Remove bookmark"
                    ToolTip.delay:   300
                }
            }
        }
    }
}
