import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

// Left sidebar: quick links, custom bookmarks, recent directories
Rectangle {
    id: sidebar

    implicitWidth:  175
    implicitHeight: 500
    color:          "transparent"

    // Signals emitted when user clicks a location
    signal navigateTo(string path)

    // ── Data properties (populated by FilePickerModal) ──────────────────────
    property var quickLinks:  []
    property var bookmarks:   []
    property var recentDirs:  []

    property string currentPath: ""

    // ── Helper ───────────────────────────────────────────────────────────────
    function isActive(path) {
        return currentPath === path
    }

    // ── Layout ───────────────────────────────────────────────────────────────
    ColumnLayout {
        anchors.fill:    parent
        anchors.margins: 0
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
            visible:           sidebar.bookmarks.length > 0
        }

        Text {
            Layout.fillWidth:  true
            Layout.leftMargin: 12
            Layout.topMargin:  8
            Layout.bottomMargin: 4
            text:      "BOOKMARKS"
            font.family:    Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall
            font.bold:      true
            font.letterSpacing: 1.2
            color:     Theme.overlay0
            visible:   sidebar.bookmarks.length > 0
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
            model: sidebar.recentDirs.slice(0, 6)

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

        Item { Layout.fillHeight: true }
    }

    // ── Inline: Sidebar row delegate ─────────────────────────────────────────
    component SidebarEntry: Item {
        property string entryName:  ""
        property string entryPath:  ""
        property string entryIcon:  "󰉋"
        property bool   active:     false
        property bool   showRemove: false

        signal clicked()
        signal remove()

        implicitHeight: 30

        Rectangle {
            anchors.fill:   parent
            anchors.leftMargin:  4
            anchors.rightMargin: 4
            radius:  6
            color:   active
                         ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.18)
                         : (rowMouse.containsMouse ? Theme.moduleHoverBg : "transparent")
            border.color: active ? Theme.accent : "transparent"
            border.width: 1

            RowLayout {
                anchors.fill:        parent
                anchors.leftMargin:  8
                anchors.rightMargin: 6
                spacing: 6

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

                // Remove bookmark button
                Text {
                    visible:        showRemove && rowMouse.containsMouse
                    text:           "󰅖"
                    font.family:    Theme.fontFamily
                    font.pixelSize: 11
                    color:          Theme.red

                    MouseArea {
                        anchors.fill:  parent
                        cursorShape:   Qt.PointingHandCursor
                        onClicked: (mouse) => {
                            mouse.accepted = true
                            remove()
                        }
                    }
                }
            }

            MouseArea {
                id:          rowMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape:  Qt.PointingHandCursor
                onClicked:    clicked()
            }
        }
    }

    // ── External functions (called by FilePickerModal) ────────────────────────
    signal removeBookmark(string path)
}
