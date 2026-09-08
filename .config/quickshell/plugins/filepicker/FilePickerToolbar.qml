import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import "../.."

// Top toolbar: back/forward/up + breadcrumb (Ctrl+L → editable) + search + view/sort controls
Rectangle {
    id: toolbar

    implicitHeight: 44
    color:          "transparent"

    // ── In-props ─────────────────────────────────────────────────────────────
    property string currentPath:   ""
    property bool   canGoBack:     false
    property bool   canGoForward:  false
    property bool   showHidden:    false
    property string viewMode:      "list"   // "list" | "grid"
    property string sortBy:        "name"   // "name" | "size" | "date"
    property bool   sortAsc:       true
    property string searchText:    ""

    // ── Signals ───────────────────────────────────────────────────────────────
    signal goBack()
    signal goForward()
    signal goUp()
    signal navigateTo(string path)
    signal toggleHidden()
    signal toggleViewMode()
    signal setSortBy(string by, bool asc)
    signal searchChanged(string text)

    // ── Internal ─────────────────────────────────────────────────────────────
    property bool editingPath:   false
    property bool sortMenuOpen:  false

    function breadcrumbs() {
        var p = currentPath
        if (!p) return []
        var parts = p.split("/").filter(function(s) { return s.length > 0 })
        var result = [{ label: "/", path: "/" }]
        var acc = ""
        for (var i = 0; i < parts.length; i++) {
            acc += "/" + parts[i]
            result.push({ label: parts[i], path: acc })
        }
        return result
    }

    RowLayout {
        anchors.fill:    parent
        anchors.margins: 0
        spacing:         4

        // ── Nav buttons ───────────────────────────────────────────────────────
        NavButton {
            icon:     "󰒮"
            tooltip:  "Back"
            enabled2: toolbar.canGoBack
            onClicked: toolbar.goBack()
        }
        NavButton {
            icon:     "󰒭"
            tooltip:  "Forward"
            enabled2: toolbar.canGoForward
            onClicked: toolbar.goForward()
        }
        NavButton {
            icon:     "󰁞"
            tooltip:  "Up"
            enabled2: toolbar.currentPath !== "/"
            onClicked: toolbar.goUp()
        }

        // ── Path breadcrumb / edit field ──────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            implicitHeight:   34
            radius:           Theme.pillRadius
            color:            Theme.moduleBg
            border.color:     pathInput.activeFocus ? Theme.accent : Theme.moduleBorder
            border.width:     1

            // Click background to enter edit mode
            MouseArea {
                anchors.fill: parent
                visible:      !toolbar.editingPath
                onClicked:    {
                    toolbar.editingPath = true
                    pathInput.forceActiveFocus()
                }
            }

            // Breadcrumb (click to navigate segment, Ctrl+L / click blank to edit)
            Row {
                id:            breadcrumbRow
                anchors.fill:  parent
                anchors.leftMargin:  10
                anchors.rightMargin: 10
                spacing:       0
                visible:       !toolbar.editingPath
                clip:          true

                Repeater {
                    model: toolbar.breadcrumbs()

                    delegate: Row {
                        required property var modelData
                        required property int index

                        Text {
                            visible:        index > 0
                            text:           " / "
                            font.family:    Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color:          Theme.overlay0
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text:           modelData.label
                            font.family:    Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold:      index === toolbar.breadcrumbs().length - 1
                            color:          (index === toolbar.breadcrumbs().length - 1)
                                                ? Theme.text
                                                : (crumbMouse.containsMouse ? Theme.accent : Theme.subtext0)
                            anchors.verticalCenter: parent.verticalCenter

                            MouseArea {
                                id:          crumbMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape:  Qt.PointingHandCursor
                                onClicked:    toolbar.navigateTo(modelData.path)
                            }
                        }
                    }
                }
            }

            // Editable path input
            TextInput {
                id:            pathInput
                anchors.fill:  parent
                anchors.leftMargin:  10
                anchors.rightMargin: 10
                visible:       toolbar.editingPath
                verticalAlignment: TextInput.AlignVCenter
                font.family:   Theme.fontFamily
                font.pixelSize: Theme.fontSize
                color:         Theme.text
                text:          toolbar.currentPath
                clip:          true
                selectByMouse: true

                onActiveFocusChanged: {
                    if (activeFocus) {
                        selectAll()
                    }
                }

                Keys.onReturnPressed: {
                    toolbar.navigateTo(text)
                    toolbar.editingPath = false
                }
                Keys.onEscapePressed: {
                    toolbar.editingPath = false
                }
            }

            Keys.onPressed: (event) => {
                if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_L) {
                    toolbar.editingPath = true
                    pathInput.forceActiveFocus()
                    event.accepted = true
                }
            }
        }

        // ── Search ────────────────────────────────────────────────────────────
        Rectangle {
            implicitWidth:  180
            implicitHeight: 34
            radius:         Theme.pillRadius
            color:          Theme.moduleBg
            border.color:   searchInput.activeFocus ? Theme.accent : Theme.moduleBorder
            border.width:   1

            RowLayout {
                anchors.fill:        parent
                anchors.leftMargin:  8
                anchors.rightMargin: 8
                spacing: 6

                Text {
                    text:           "󰍉"
                    font.family:    Theme.fontFamily
                    font.pixelSize: 14
                    color:          searchInput.activeFocus ? Theme.accent : Theme.subtext0
                }

                TextInput {
                    id:             searchInput
                    Layout.fillWidth: true
                    font.family:    Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    color:          Theme.text
                    clip:           true

                    Text {
                        text:           "Search files…"
                        font.family:    Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color:          Theme.overlay0
                        visible:        !searchInput.text && !searchInput.activeFocus
                    }

                    onTextChanged: toolbar.searchChanged(text)
                    Keys.onEscapePressed: {
                        if (text.length > 0) { text = "" }
                        else { toolbar.searchChanged("") }
                    }
                }

                // Clear button
                Text {
                    visible:        searchInput.text.length > 0
                    text:           "󰅖"
                    font.family:    Theme.fontFamily
                    font.pixelSize: 11
                    color:          Theme.overlay0

                    MouseArea {
                        anchors.fill: parent
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    searchInput.text = ""
                    }
                }
            }
        }

        // ── Hidden files toggle ───────────────────────────────────────────────
        ToolIconButton {
            icon:    toolbar.showHidden ? "󰗹" : "󱈴"
            tooltip: toolbar.showHidden ? "Hide dotfiles (Ctrl+H)" : "Show dotfiles (Ctrl+H)"
            active:  toolbar.showHidden
            onClicked: toolbar.toggleHidden()
        }

        // ── View mode toggle ──────────────────────────────────────────────────
        ToolIconButton {
            icon:    toolbar.viewMode === "list" ? "󰙀" : "󰈚"
            tooltip: toolbar.viewMode === "list" ? "Grid view" : "List view"
            onClicked: toolbar.toggleViewMode()
        }

        // ── Sort button ───────────────────────────────────────────────────────
        ToolIconButton {
            id:      sortBtn
            icon:    "󰒺"
            tooltip: "Sort"
            onClicked: toolbar.sortMenuOpen = !toolbar.sortMenuOpen

            // Sort dropdown popup
            Rectangle {
                id:      sortMenu
                visible: toolbar.sortMenuOpen
                z:       200
                width:   140
                implicitHeight: sortCol.implicitHeight + 12
                anchors.top:    parent.bottom
                anchors.right:  parent.right
                anchors.topMargin: 4
                radius:       Theme.pillRadius
                color:        Theme.tooltipBg
                border.color: Theme.tooltipBorder
                border.width: 1

                ColumnLayout {
                    id:             sortCol
                    anchors.left:   parent.left
                    anchors.right:  parent.right
                    anchors.top:    parent.top
                    anchors.margins: 6
                    spacing:        2

                    Repeater {
                        model: [
                            { id: "name", label: "Name",         icon: "󰊓" },
                            { id: "size", label: "Size",         icon: "󰙖" },
                            { id: "date", label: "Date Modified", icon: "󰃰" },
                        ]

                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: 28
                            radius: 6
                            color: sortItemMouse.containsMouse ? Theme.moduleHoverBg : "transparent"

                            RowLayout {
                                anchors.fill:        parent
                                anchors.leftMargin:  8
                                anchors.rightMargin: 8
                                spacing: 6

                                Text {
                                    text:           modelData.icon
                                    font.family:    Theme.fontFamily
                                    font.pixelSize: 12
                                    color:          toolbar.sortBy === modelData.id
                                                        ? Theme.accent : Theme.subtext0
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text:           modelData.label
                                    font.family:    Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold:      toolbar.sortBy === modelData.id
                                    color:          toolbar.sortBy === modelData.id
                                                        ? Theme.accent : Theme.text
                                }
                                Text {
                                    visible:        toolbar.sortBy === modelData.id
                                    text:           toolbar.sortAsc ? "↑" : "↓"
                                    font.family:    Theme.fontFamily
                                    font.pixelSize: 11
                                    color:          Theme.accent
                                }
                            }

                            MouseArea {
                                id:          sortItemMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape:  Qt.PointingHandCursor
                                onClicked: {
                                    var newAsc = (toolbar.sortBy === modelData.id) ? !toolbar.sortAsc : true
                                    toolbar.setSortBy(modelData.id, newAsc)
                                    toolbar.sortMenuOpen = false
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Close sort menu when clicking elsewhere
    MouseArea {
        anchors.fill: parent
        z: -1
        visible: toolbar.sortMenuOpen
        onClicked: toolbar.sortMenuOpen = false
    }

    // ── Inline components ─────────────────────────────────────────────────────
    component NavButton: Rectangle {
        property string icon:     ""
        property string tooltip:  ""
        property bool   enabled2: true  // renamed to avoid clash with Item.enabled

        signal clicked()

        implicitWidth:  30
        implicitHeight: 30
        radius:         8
        color:          !enabled2 ? "transparent" : (navMouse.containsMouse ? Theme.moduleHoverBg : "transparent")
        opacity:        enabled2 ? 1.0 : 0.35

        Text {
            anchors.centerIn: parent
            text:           icon
            font.family:    Theme.fontFamily
            font.pixelSize: 15
            color:          navMouse.containsMouse ? Theme.accent : Theme.subtext0
        }

        MouseArea {
            id:          navMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape:  enabled2 ? Qt.PointingHandCursor : Qt.ArrowCursor
            enabled:      enabled2
            onClicked:    parent.clicked()
        }

        ToolTip.visible: navMouse.containsMouse && tooltip.length > 0
        ToolTip.text:    tooltip
        ToolTip.delay:   400
    }

    component ToolIconButton: Rectangle {
        property string icon:    ""
        property string tooltip: ""
        property bool   active:  false

        signal clicked()

        implicitWidth:  30
        implicitHeight: 30
        radius:         8
        color:          active
                            ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.18)
                            : (toolMouse.containsMouse ? Theme.moduleHoverBg : "transparent")
        border.color:   active ? Theme.accent : "transparent"
        border.width:   1

        Text {
            anchors.centerIn: parent
            text:           icon
            font.family:    Theme.fontFamily
            font.pixelSize: 15
            color:          active ? Theme.accent : (toolMouse.containsMouse ? Theme.accent : Theme.subtext0)
        }

        MouseArea {
            id:          toolMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape:  Qt.PointingHandCursor
            onClicked:    parent.clicked()
        }

        ToolTip.visible: toolMouse.containsMouse && tooltip.length > 0
        ToolTip.text:    tooltip
        ToolTip.delay:   400
    }
}
