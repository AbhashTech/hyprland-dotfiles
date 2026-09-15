import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import "../.."

// Collapsible right-side preview panel
// Supports: images, text/code, generic file info
Rectangle {
    id: preview

    implicitWidth:  240
    color:          Qt.rgba(Theme.crust.r, Theme.crust.g, Theme.crust.b, 0.55)
    radius:         Theme.barRadius

    // ── In-props ─────────────────────────────────────────────────────────────
    property var    entry:   null   // current file entry object
    property string content: ""    // text content (loaded externally)
    property var    dirData: null   // directory preview summary
    property bool   isDirectoryMode: false

    // ── States ────────────────────────────────────────────────────────────────
    readonly property bool hasEntry:   preview.entry !== null && preview.entry !== undefined
    readonly property bool isImage:    preview.hasEntry && (preview.entry.category === "image" || (preview.entry.thumbnail !== "" && preview.entry.thumbnail !== undefined))
    readonly property bool isDir:      preview.hasEntry && !!preview.entry.isDir
    readonly property bool isText:     preview.hasEntry && !preview.isImage && !preview.isDir && (
        preview.entry.category === "text" ||
        preview.entry.category === "code" ||
        (preview.entry.mime && preview.entry.mime.indexOf("text/") === 0) ||
        (preview.entry.mime && (preview.entry.mime === "application/json" ||
                                preview.entry.mime === "application/xml" ||
                                preview.entry.mime === "application/javascript" ||
                                preview.entry.mime === "application/x-sh" ||
                                preview.entry.mime === "application/x-yaml" ||
                                preview.entry.mime === "application/toml"))
    )

    ColumnLayout {
        anchors.fill:    parent
        anchors.margins: 12
        spacing:         10

        // ── No selection placeholder ──────────────────────────────────────────
        Item {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            visible: !preview.hasEntry

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text:           preview.isDirectoryMode ? "󰉋" : "󰈔"
                    font.family:    Theme.fontFamily
                    font.pixelSize: 48
                    color:          Theme.overlay0
                    opacity:        0.4
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text:           preview.isDirectoryMode ? "Select a folder\nto preview" : "Select a file\nto preview"
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color:          Theme.overlay0
                    horizontalAlignment: Text.AlignHCenter
                    opacity:        0.6
                }
            }
        }

        // ── Image preview ─────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth:  true
            implicitHeight:    180
            visible:           preview.hasEntry && preview.isImage
            radius:            Theme.pillRadius
            color:             Theme.moduleBg
            clip:              true

            Image {
                anchors.fill:  parent
                source:        preview.isImage
                                   ? ("file://" + ((preview.entry.thumbnail && preview.entry.thumbnail !== "") ? preview.entry.thumbnail : preview.entry.path))
                                   : ""
                fillMode:      Image.PreserveAspectFit
                asynchronous:  true
                smooth:        true
                cache:         true
            }
        }

        // ── Directory icon ────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth:  true
            implicitHeight:    80
            visible:           preview.hasEntry && preview.isDir
            radius:            Theme.pillRadius
            color:             Theme.moduleBg

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 4

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text:           "󰉋"
                    font.family:    Theme.fontFamily
                    font.pixelSize: 36
                    color:          Theme.blue
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text:           preview.hasEntry && preview.isDir && preview.entry.itemCount !== undefined && preview.entry.itemCount >= 0
                                        ? (preview.entry.itemCount + (preview.entry.itemCount === 1 ? " item" : " items"))
                                        : "Directory"
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color:          Theme.subtext0
                }
            }
        }

        // ── Generic icon for non-image/non-dir files ──────────────────────────
        Rectangle {
            Layout.fillWidth:  true
            implicitHeight:    70
            visible:           preview.hasEntry && !preview.isImage && !preview.isDir
            radius:            Theme.pillRadius
            color:             Theme.moduleBg

            Text {
                anchors.centerIn: parent
                text:            preview.hasEntry ? (preview.entry.icon || "󰈔") : ""
                font.family:     Theme.fontFamily
                font.pixelSize:  36
                color:           Theme.subtext0
            }
        }

        // ── File metadata ─────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            implicitHeight:   metaCol.implicitHeight + 16
            visible:          preview.hasEntry
            radius:           Theme.pillRadius
            color:            Theme.moduleBg

            ColumnLayout {
                id:              metaCol
                anchors.left:    parent.left
                anchors.right:   parent.right
                anchors.top:     parent.top
                anchors.margins: 10
                spacing:         6

                // Name
                Text {
                    Layout.fillWidth: true
                    text:           preview.hasEntry ? preview.entry.name : ""
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold:      true
                    color:          Theme.text
                    wrapMode:       Text.WrapAnywhere
                }

                // MIME type
                MetaRow {
                    label: "Type"
                    value: preview.hasEntry ? (preview.entry.mime || "unknown") : ""
                }

                // Size (files only)
                MetaRow {
                    visible: preview.hasEntry && !preview.isDir
                    label:   "Size"
                    value:   preview.hasEntry ? (preview.entry.sizeStr || "—") : ""
                }

                // Contains (directories only)
                MetaRow {
                    visible: preview.hasEntry && preview.isDir
                    label:   "Contains"
                    value:   preview.hasEntry && preview.entry.sizeStr ? preview.entry.sizeStr : "—"
                }

                // Modified
                MetaRow {
                    label: "Modified"
                    value: preview.hasEntry ? (preview.entry.modifiedStr || "—") : ""
                }

                // Symlink badge
                Rectangle {
                    visible:      preview.hasEntry && preview.entry.isSymlink
                    Layout.fillWidth: true
                    implicitHeight: 20
                    radius:        10
                    color:         Qt.rgba(Theme.yellow.r, Theme.yellow.g, Theme.yellow.b, 0.18)

                    Text {
                        anchors.centerIn: parent
                        text:           "󰁔  Symbolic Link"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 10
                        color:          Theme.yellow
                    }
                }
            }
        }

        // ── Directory contents preview ────────────────────────────────────────
        Rectangle {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            visible:           preview.hasEntry && preview.isDir
            radius:            Theme.pillRadius
            color:             Theme.moduleBg
            clip:              true

            ColumnLayout {
                anchors.fill:    parent
                anchors.margins: 10
                spacing:         6

                Text {
                    Layout.fillWidth: true
                    text:           "Contents:"
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold:      true
                    color:          Theme.subtext0
                }

                ListView {
                    Layout.fillWidth:  true
                    Layout.fillHeight: true
                    clip:              true
                    model:             preview.dirData && preview.dirData.items ? preview.dirData.items : []

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                        width:  4
                    }

                    delegate: Item {
                        width:  ListView.view.width
                        height: 20

                        RowLayout {
                            anchors.fill: parent
                            spacing:      6

                            Text {
                                text:           modelData.icon || (modelData.isDir ? "󰉋" : "󰈔")
                                font.family:    Theme.fontFamily
                                font.pixelSize: 11
                                color:          modelData.isDir ? Theme.blue : Theme.subtext0
                            }

                            Text {
                                Layout.fillWidth: true
                                text:           modelData.name
                                font.family:    Theme.fontFamily
                                font.pixelSize: 11
                                color:          modelData.isDir ? Theme.blue : Theme.text
                                elide:          Text.ElideRight
                            }
                        }
                    }
                }

                Text {
                    visible:        preview.dirData && preview.dirData.items && preview.dirData.items.length === 0
                    Layout.alignment: Qt.AlignHCenter
                    text:           "Empty folder"
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color:          Theme.overlay0
                    opacity:        0.7
                }
            }
        }

        // ── Text/code preview ─────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            visible:           preview.hasEntry && preview.isText
            radius:            Theme.pillRadius
            color:             Theme.moduleBg
            clip:              true

            Flickable {
                anchors.fill:    parent
                anchors.margins: 8
                contentHeight:   codeText.implicitHeight
                clip:            true

                Text {
                    id:              codeText
                    width:           parent.width
                    text:            preview.content.length > 0 ? preview.content : "Loading preview..."
                    font.family:     Theme.fontFamily
                    font.pixelSize:  10
                    color:           preview.content.length > 0 ? Theme.subtext0 : Theme.overlay0
                    wrapMode:        Text.WrapAnywhere
                }
            }
        }

        Item { Layout.fillHeight: true }
    }

    // ── Inline: metadata row helper ───────────────────────────────────────────
    component MetaRow: RowLayout {
        property string label: ""
        property string value: ""
        Layout.fillWidth: true

        Text {
            text:           label + ":"
            font.family:    Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall
            color:          Theme.overlay0
            Layout.preferredWidth: 54
        }
        Text {
            Layout.fillWidth: true
            text:           value
            font.family:    Theme.fontFamily
            font.pixelSize: Theme.fontSizeSmall
            color:          Theme.text
            elide:          Text.ElideRight
        }
    }
}
