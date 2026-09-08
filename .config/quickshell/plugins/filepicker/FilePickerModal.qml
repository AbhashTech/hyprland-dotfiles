import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import "../.."

// ─────────────────────────────────────────────────────────────────────────────
// FilePickerModal — Main floating file picker/selector modal
//
// Layout:  [Sidebar 175px] | [divider] | [Toolbar + FilterTabs + Content] | [divider] | [Preview 240px collapsible]
//          Bottom: status info + action buttons
//
// Integrates with file_picker_helper.py (list, bookmarks, recents, confirm, cancel, request)
// Portal mode: reads request from ~/.cache/qs_filepicker/request.json on open
// ─────────────────────────────────────────────────────────────────────────────
Rectangle {
    id: modal

    implicitWidth:  960
    implicitHeight: 620
    radius:         Theme.barRadius
    color:          Theme.barBg
    border.color:   Theme.barBorder
    border.width:   1

    // ── Helper path ───────────────────────────────────────────────────────────
    readonly property string helper: Quickshell.env("HOME") +
        "/.config/quickshell/plugins/filepicker/file_picker_helper.py"

    // ── Navigation state ──────────────────────────────────────────────────────
    property string  currentPath:    Quickshell.env("HOME")
    property var     history:        []
    property int     historyIdx:     -1

    property var     allEntries:     []
    property var     filteredEntries: []
    property string  searchText:     ""
    property string  mimeFilter:     "all"
    property bool    showHidden:     false
    property string  viewMode:       "list"
    property string  sortBy:         "name"
    property bool    sortAsc:        true
    property int     focusIndex:     0

    // ── Selection state ───────────────────────────────────────────────────────
    property var     selectedPaths:  []
    property bool    multiSelect:    false

    // ── Preview state ─────────────────────────────────────────────────────────
    property bool    previewVisible: true
    property var     previewEntry:   null
    property string  previewContent: ""

    // ── Portal request metadata (filled from request.json) ────────────────────
    property string  requestMode:    "open"    // "open" | "save" | "open-multiple"
    property string  requestTitle:   "Open File"
    property string  requestAppId:   ""
    property string  requestMime:    "all"

    // ── Computed ──────────────────────────────────────────────────────────────
    property bool    canGoBack:    historyIdx > 0
    property bool    canGoForward: historyIdx < history.length - 1

    readonly property var mimeFilterTabs: [
        { id: "all",      label: "All",       icon: "󰈔" },
        { id: "image",    label: "Images",    icon: "󰋩" },
        { id: "video",    label: "Videos",    icon: "󰕧" },
        { id: "audio",    label: "Audio",     icon: "󰓃" },
        { id: "code",     label: "Code",      icon: "" },
        { id: "document", label: "Docs",      icon: "󰈦" },
        { id: "text",     label: "Text",      icon: "󰈙" },
        { id: "archive",  label: "Archives",  icon: "󰛫" },
    ]

    // ── Navigation ────────────────────────────────────────────────────────────
    function navigate(path) {
        if (path === currentPath) return
        // Push to history
        if (historyIdx < history.length - 1) {
            history = history.slice(0, historyIdx + 1)
        }
        history.push(path)
        historyIdx = history.length - 1
        currentPath = path
        selectedPaths = []
        focusIndex = 0
        refreshListing()
    }

    function navigateBack() {
        if (!canGoBack) return
        historyIdx--
        currentPath = history[historyIdx]
        selectedPaths = []
        focusIndex = 0
        refreshListing()
    }

    function navigateForward() {
        if (!canGoForward) return
        historyIdx++
        currentPath = history[historyIdx]
        selectedPaths = []
        focusIndex = 0
        refreshListing()
    }

    function navigateUp() {
        var parts = currentPath.split("/").filter(function(s) { return s.length > 0 })
        if (parts.length === 0) return
        parts.pop()
        navigate(parts.length === 0 ? "/" : "/" + parts.join("/"))
    }

    // ── Listing ───────────────────────────────────────────────────────────────
    function refreshListing() {
        var args = ["python3", helper, "list", currentPath]
        if (showHidden)              args.push("--hidden")
        if (mimeFilter !== "all")    { args.push("--mime"); args.push(mimeFilter) }
        if (sortBy !== "name")       { args.push("--sort"); args.push(sortBy) }
        if (!sortAsc)                args.push("--desc")
        listProc.command = args
        if (!listProc.running) listProc.running = true
    }

    function applySearch() {
        var q = searchText.toLowerCase().trim()
        if (q.length === 0) {
            filteredEntries = allEntries
        } else {
            filteredEntries = allEntries.filter(function(e) {
                return e.name.toLowerCase().indexOf(q) !== -1
            })
        }
        focusIndex = 0
    }

    // ── Selection ─────────────────────────────────────────────────────────────
    function toggleSelection(path) {
        var idx = selectedPaths.indexOf(path)
        if (idx === -1) {
            if (multiSelect) {
                selectedPaths.push(path)
            } else {
                selectedPaths = [path]
            }
        } else {
            selectedPaths.splice(idx, 1)
        }
        selectedPaths = selectedPaths.slice()  // trigger binding
    }

    function handleEntryClick(entry) {
        if (entry.isDir) {
            navigate(entry.path)
        } else {
            if (multiSelect) {
                toggleSelection(entry.path)
            } else {
                selectedPaths = [entry.path]
                loadPreview(entry)
            }
        }
    }

    function handleEntryDoubleClick(entry) {
        if (entry.isDir) {
            navigate(entry.path)
        } else {
            selectedPaths = [entry.path]
            confirmSelection()
        }
    }

    // ── Preview ───────────────────────────────────────────────────────────────
    function loadPreview(entry) {
        previewEntry = entry
        previewContent = ""
        if (entry && !entry.isDir && entry.category === "text" || entry.category === "code") {
            previewProc.command = ["head", "-c", "4000", entry.path]
            if (!previewProc.running) previewProc.running = true
        }
    }

    // ── Confirm / Cancel ──────────────────────────────────────────────────────
    function confirmSelection() {
        if (selectedPaths.length === 0) {
            // Confirm currently focused entry
            if (focusIndex >= 0 && focusIndex < filteredEntries.length) {
                var e = filteredEntries[focusIndex]
                if (!e.isDir) {
                    selectedPaths = [e.path]
                } else {
                    navigate(e.path)
                    return
                }
            } else {
                return
            }
        }
        var args = ["python3", helper, "confirm"].concat(selectedPaths)
        ctlProc.command = args
        if (!ctlProc.running) ctlProc.running = true
        PluginManager.closeAll()
    }

    function cancelAndClose() {
        ctlProc.command = ["python3", helper, "cancel"]
        if (!ctlProc.running) ctlProc.running = true
        PluginManager.closeAll()
    }

    // ── Bookmarks ─────────────────────────────────────────────────────────────
    function refreshBookmarks() {
        bmProc.command = ["python3", helper, "bookmarks"]
        if (!bmProc.running) bmProc.running = true
    }

    function addBookmark(path) {
        ctlProc.command = ["python3", helper, "add-bookmark", path]
        if (!ctlProc.running) ctlProc.running = true
        Qt.callLater(refreshBookmarks)
    }

    function removeBookmark(path) {
        ctlProc.command = ["python3", helper, "remove-bookmark", path]
        if (!ctlProc.running) ctlProc.running = true
        Qt.callLater(refreshBookmarks)
    }

    // ── Init ──────────────────────────────────────────────────────────────────
    property var    sidebarQuick:   []
    property var    sidebarBookmarks: []
    property var    sidebarRecents:  []

    function grabFocus() {
        // Read portal request if available
        requestProc.command = ["python3", helper, "request"]
        if (!requestProc.running) requestProc.running = true
        // Reset state
        selectedPaths  = []
        searchText     = ""
        mimeFilter     = "all"
        focusIndex     = 0
        previewEntry   = null
        previewContent = ""
        // Set starting path
        var startPath  = Quickshell.env("HOME")
        // If portal specified a MIME, auto-set filter
        if (requestMime && requestMime !== "all") {
            mimeFilter = requestMime
            // Auto-grid for images
            if (requestMime === "image") viewMode = "grid"
        }
        if (history.length === 0) {
            history    = [startPath]
            historyIdx = 0
            currentPath = startPath
        }
        refreshListing()
        refreshBookmarks()
        modal.forceActiveFocus()
    }

    Component.onCompleted: grabFocus()

    // ── Process: directory listing ────────────────────────────────────────────
    Process {
        id: listProc
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var parsed = JSON.parse(data)
                    if (Array.isArray(parsed)) {
                        allEntries = parsed
                        modal.applySearch()
                    }
                } catch(e) {}
            }
        }
    }

    // ── Process: bookmarks + recents ──────────────────────────────────────────
    Process {
        id: bmProc
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data)
                    if (obj.quick)  modal.sidebarQuick    = obj.quick
                    if (obj.custom) modal.sidebarBookmarks = obj.custom
                } catch(e) {}
            }
        }
    }

    Process {
        id: recentsProc
        command: ["python3", helper, "recents"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var arr = JSON.parse(data)
                    if (Array.isArray(arr)) modal.sidebarRecents = arr
                } catch(e) {}
            }
        }
    }

    // ── Process: portal request reader ────────────────────────────────────────
    Process {
        id: requestProc
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data)
                    if (obj && obj.mode) {
                        modal.requestMode   = obj.mode   || "open"
                        modal.requestTitle  = obj.title  || "Open File"
                        modal.requestAppId  = obj.app_id || ""
                        modal.requestMime   = obj.mime_filter || "all"
                        modal.multiSelect   = !!obj.multiple
                        if (modal.requestMime !== "all") {
                            modal.mimeFilter = modal.requestMime
                        }
                    }
                } catch(e) {}
            }
        }
    }

    // ── Process: text preview reader ──────────────────────────────────────────
    Process {
        id: previewProc
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => { modal.previewContent = data }
        }
    }

    // ── Process: control (confirm/cancel/bookmark ops) ────────────────────────
    Process { id: ctlProc }

    // ── Keyboard handling ─────────────────────────────────────────────────────
    focus: true
    Keys.onEscapePressed: event => {
        modal.cancelAndClose()
        event.accepted = true
    }
    Keys.onReturnPressed:  event => { modal.confirmSelection(); event.accepted = true }
    Keys.onEnterPressed:   event => { modal.confirmSelection(); event.accepted = true }

    Keys.onUpPressed:   event => {
        if (viewMode === "list") fileList.moveFocus(-1)
        else                     fileGrid.moveFocus(-4)
        event.accepted = true
    }
    Keys.onDownPressed: event => {
        if (viewMode === "list") fileList.moveFocus(1)
        else                     fileGrid.moveFocus(4)
        event.accepted = true
    }
    Keys.onLeftPressed:  event => {
        if (viewMode === "grid") fileGrid.moveFocus(-1)
        event.accepted = true
    }
    Keys.onRightPressed: event => {
        if (viewMode === "grid") fileGrid.moveFocus(1)
        event.accepted = true
    }

    Keys.onPressed: event => {
        if (event.key === Qt.Key_Backspace && !(searchText.length > 0)) {
            modal.navigateUp()
            event.accepted = true
        }
        if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_H) {
            modal.showHidden = !modal.showHidden
            modal.refreshListing()
            event.accepted = true
        }
        if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_P) {
            modal.previewVisible = !modal.previewVisible
            event.accepted = true
        }
        if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_D) {
            if (modal.currentPath) modal.addBookmark(modal.currentPath)
            event.accepted = true
        }
    }

    // ── Watchers ──────────────────────────────────────────────────────────────
    onCurrentPathChanged:  { refreshListing(); recentsProc.running = true }
    onShowHiddenChanged:   refreshListing()
    onMimeFilterChanged:   refreshListing()
    onSortByChanged:       refreshListing()
    onSortAscChanged:      refreshListing()
    onSearchTextChanged:   applySearch()

    Connections {
        target: PluginManager
        function onFilePickerVisibleChanged() {
            if (PluginManager.filePickerVisible) {
                modal.grabFocus()
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // ── UI Layout ─────────────────────────────────────────────────────────────
    // ─────────────────────────────────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        spacing:      0

        // ── Title bar ─────────────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            implicitHeight:   42
            color:            Qt.rgba(Theme.crust.r, Theme.crust.g, Theme.crust.b, 0.6)
            radius:           Theme.barRadius

            // Bottom straight edge
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left:   parent.left
                anchors.right:  parent.right
                height:         Theme.barRadius
                color:          parent.color
            }

            RowLayout {
                anchors.fill:        parent
                anchors.leftMargin:  16
                anchors.rightMargin: 12
                spacing: 10

                // App ID badge (portal mode)
                Rectangle {
                    visible:       modal.requestAppId.length > 0
                    implicitHeight: 24
                    implicitWidth:  appIdRow.implicitWidth + 16
                    radius:        12
                    color:         Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.15)
                    border.color:  Theme.accent
                    border.width:  1

                    RowLayout {
                        id:              appIdRow
                        anchors.centerIn: parent
                        spacing:         5

                        Text {
                            text:           "󰿎"
                            font.family:    Theme.fontFamily
                            font.pixelSize: 11
                            color:          Theme.accent
                        }
                        Text {
                            text:           modal.requestAppId
                            font.family:    Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color:          Theme.accent
                            font.bold:      true
                        }
                    }
                }

                // Title
                Text {
                    Layout.fillWidth:  true
                    text:             modal.requestTitle.length > 0
                                          ? modal.requestTitle
                                          : (modal.requestMode === "save" ? "Save File" : "Open File")
                    font.family:      Theme.fontFamily
                    font.pixelSize:   Theme.fontSizeLarge
                    font.bold:        true
                    color:            Theme.text
                    elide:            Text.ElideRight
                }

                // Multi-select badge
                Rectangle {
                    visible:       modal.multiSelect
                    implicitHeight: 22
                    implicitWidth:  multiSelRow.implicitWidth + 12
                    radius:        11
                    color:         Qt.rgba(Theme.green.r, Theme.green.g, Theme.green.b, 0.18)
                    border.color:  Theme.green
                    border.width:  1

                    RowLayout {
                        id:              multiSelRow
                        anchors.centerIn: parent
                        spacing:         4

                        Text { text: ""; font.family: Theme.fontFamily; font.pixelSize: 10; color: Theme.green }
                        Text {
                            text:           "Multi-select"
                            font.family:    Theme.fontFamily
                            font.pixelSize: 10
                            color:          Theme.green
                            font.bold:      true
                        }
                    }
                }

                // Preview toggle button (Ctrl+P)
                Rectangle {
                    implicitWidth:  28
                    implicitHeight: 28
                    radius:         8
                    color:          previewToggleMouse.containsMouse
                                        ? Theme.moduleHoverBg
                                        : (modal.previewVisible ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.15) : "transparent")
                    border.color:   modal.previewVisible ? Theme.accent : "transparent"
                    border.width:   1

                    Text {
                        anchors.centerIn: parent
                        text:           modal.previewVisible ? "󰈿" : "󰈾"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 14
                        color:          modal.previewVisible ? Theme.accent : Theme.subtext0
                    }

                    MouseArea {
                        id:          previewToggleMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    modal.previewVisible = !modal.previewVisible
                    }

                    ToolTip.visible: previewToggleMouse.containsMouse
                    ToolTip.text:    "Toggle preview (Ctrl+P)"
                    ToolTip.delay:   400
                }

                // Bookmark current dir (Ctrl+D)
                Rectangle {
                    implicitWidth:  28
                    implicitHeight: 28
                    radius:         8
                    color:          bmToggleMouse.containsMouse ? Theme.moduleHoverBg : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text:           "󰃃"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 14
                        color:          bmToggleMouse.containsMouse ? Theme.yellow : Theme.subtext0
                    }

                    MouseArea {
                        id:          bmToggleMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    modal.addBookmark(modal.currentPath)
                    }

                    ToolTip.visible: bmToggleMouse.containsMouse
                    ToolTip.text:    "Bookmark current folder (Ctrl+D)"
                    ToolTip.delay:   400
                }

                // Close button
                Rectangle {
                    implicitWidth:  28
                    implicitHeight: 28
                    radius:         14
                    color:          closeBtnMouse.containsMouse ? Theme.red : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text:           "󰅖"
                        font.family:    Theme.fontFamily
                        font.pixelSize: 13
                        color:          closeBtnMouse.containsMouse ? "#ffffff" : Theme.subtext0
                    }

                    MouseArea {
                        id:          closeBtnMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape:  Qt.PointingHandCursor
                        onClicked:    modal.cancelAndClose()
                    }
                }
            }
        }

        // ── Main content row (sidebar | content | preview) ────────────────────
        RowLayout {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            spacing:           0

            // ── Left sidebar ──────────────────────────────────────────────────
            FilePickerSidebar {
                id:            sidebar
                Layout.fillHeight: true
                Layout.topMargin:  8
                Layout.bottomMargin: 8

                quickLinks:  modal.sidebarQuick
                bookmarks:   modal.sidebarBookmarks
                recentDirs:  modal.sidebarRecents
                currentPath: modal.currentPath

                onNavigateTo:    (path) => modal.navigate(path)
                onRemoveBookmark: (path) => modal.removeBookmark(path)
            }

            // Vertical divider
            Rectangle {
                Layout.fillHeight: true
                implicitWidth:     1
                color:             Theme.barBorder
                opacity:           0.5
            }

            // ── Center: toolbar + filter tabs + file list/grid ────────────────
            ColumnLayout {
                Layout.fillWidth:  true
                Layout.fillHeight: true
                spacing:           0

                // Toolbar
                FilePickerToolbar {
                    id:              toolbar
                    Layout.fillWidth: true
                    Layout.margins:  8
                    Layout.bottomMargin: 4

                    currentPath:   modal.currentPath
                    canGoBack:     modal.canGoBack
                    canGoForward:  modal.canGoForward
                    showHidden:    modal.showHidden
                    viewMode:      modal.viewMode
                    sortBy:        modal.sortBy
                    sortAsc:       modal.sortAsc
                    searchText:    modal.searchText

                    onGoBack:          modal.navigateBack()
                    onGoForward:       modal.navigateForward()
                    onGoUp:            modal.navigateUp()
                    onNavigateTo:      (path) => modal.navigate(path)
                    onToggleHidden:    { modal.showHidden = !modal.showHidden }
                    onToggleViewMode:  { modal.viewMode = (modal.viewMode === "list" ? "grid" : "list") }
                    onSetSortBy:       (by, asc) => { modal.sortBy = by; modal.sortAsc = asc }
                    onSearchChanged:   (text) => { modal.searchText = text }
                }

                // MIME filter tabs
                Rectangle {
                    Layout.fillWidth:   true
                    Layout.leftMargin:  8
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 6
                    implicitHeight:     32
                    color:              "transparent"

                    Row {
                        anchors.fill: parent
                        spacing:      4

                        Repeater {
                            model: modal.mimeFilterTabs

                            delegate: Rectangle {
                                required property var modelData
                                implicitHeight: 26
                                implicitWidth:  filterRow.implicitWidth + 14
                                radius:         13
                                color:          modal.mimeFilter === modelData.id
                                                    ? Theme.accent
                                                    : (filterMouse.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg)
                                border.color:   modal.mimeFilter === modelData.id
                                                    ? Theme.accent : Theme.moduleBorder
                                border.width:   1

                                RowLayout {
                                    id:              filterRow
                                    anchors.centerIn: parent
                                    spacing:         4

                                    Text {
                                        text:           modelData.icon
                                        font.family:    Theme.fontFamily
                                        font.pixelSize: 11
                                        color:          modal.mimeFilter === modelData.id ? Theme.crust : Theme.subtext0
                                    }
                                    Text {
                                        text:           modelData.label
                                        font.family:    Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold:      modal.mimeFilter === modelData.id
                                        color:          modal.mimeFilter === modelData.id ? Theme.crust : Theme.text
                                    }
                                }

                                MouseArea {
                                    id:          filterMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape:  Qt.PointingHandCursor
                                    onClicked: {
                                        modal.mimeFilter = modelData.id
                                        // Auto-switch view mode for images
                                        if (modelData.id === "image" || modelData.id === "video") {
                                            modal.viewMode = "grid"
                                        } else if (modelData.id !== "all") {
                                            modal.viewMode = "list"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Horizontal divider
                Rectangle {
                    Layout.fillWidth:    true
                    Layout.leftMargin:   8
                    Layout.rightMargin:  8
                    Layout.bottomMargin: 4
                    implicitHeight:      1
                    color:               Theme.barBorder
                    opacity:             0.5
                }

                // File content: list or grid
                Item {
                    Layout.fillWidth:   true
                    Layout.fillHeight:  true
                    Layout.leftMargin:  8
                    Layout.rightMargin: 8

                    // List view
                    FilePickerList {
                        id:          fileList
                        anchors.fill: parent
                        visible:     modal.viewMode === "list"

                        entries:       modal.filteredEntries
                        selectedPaths: modal.selectedPaths
                        multiSelect:   modal.multiSelect
                        focusIndex:    modal.focusIndex

                        onEntryClicked:       (entry) => modal.handleEntryClick(entry)
                        onEntryDoubleClicked: (entry) => modal.handleEntryDoubleClick(entry)
                        onSelectionToggled:   (path) => modal.toggleSelection(path)
                        onItemFocusChanged:   (idx) => {
                            modal.focusIndex = idx
                            if (idx >= 0 && idx < modal.filteredEntries.length) {
                                modal.loadPreview(modal.filteredEntries[idx])
                            }
                        }
                    }

                    // Grid view
                    FilePickerGrid {
                        id:          fileGrid
                        anchors.fill: parent
                        visible:     modal.viewMode === "grid"

                        entries:       modal.filteredEntries
                        selectedPaths: modal.selectedPaths
                        multiSelect:   modal.multiSelect
                        focusIndex:    modal.focusIndex

                        onEntryClicked:       (entry) => modal.handleEntryClick(entry)
                        onEntryDoubleClicked: (entry) => modal.handleEntryDoubleClick(entry)
                        onSelectionToggled:   (path) => modal.toggleSelection(path)
                        onItemFocusChanged:   (idx) => {
                            modal.focusIndex = idx
                            if (idx >= 0 && idx < modal.filteredEntries.length) {
                                modal.loadPreview(modal.filteredEntries[idx])
                            }
                        }
                    }
                }

                // Bottom status + action bar
                Rectangle {
                    Layout.fillWidth:  true
                    implicitHeight:    52
                    color:             Qt.rgba(Theme.crust.r, Theme.crust.g, Theme.crust.b, 0.5)
                    radius:            Theme.barRadius

                    // Top straight edge
                    Rectangle {
                        anchors.top:   parent.top
                        anchors.left:  parent.left
                        anchors.right: parent.right
                        height:        Theme.barRadius
                        color:         parent.color
                    }

                    RowLayout {
                        anchors.fill:        parent
                        anchors.leftMargin:  14
                        anchors.rightMargin: 14
                        spacing: 10

                        // Status info
                        Text {
                            text: modal.filteredEntries.length + " items"
                                + (modal.selectedPaths.length > 0
                                    ? "  •  " + modal.selectedPaths.length + " selected"
                                    : "")
                            font.family:    Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color:          Theme.overlay0
                        }

                        // Search active indicator
                        Rectangle {
                            visible:       modal.searchText.length > 0
                            implicitHeight: 20
                            implicitWidth:  searchBadgeText.implicitWidth + 14
                            radius:        10
                            color:         Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.15)
                            border.color:  Theme.accent
                            border.width:  1

                            Text {
                                id:              searchBadgeText
                                anchors.centerIn: parent
                                text:            "󰍉  Filtering: \"" + modal.searchText + "\""
                                font.family:     Theme.fontFamily
                                font.pixelSize:  10
                                color:           Theme.accent
                            }
                        }

                        // Keyboard shortcuts hint
                        Text {
                            visible:        modal.selectedPaths.length === 0
                            text:           "↑↓ Navigate  •  Enter to open  •  Ctrl+H dotfiles  •  Ctrl+P preview"
                            font.family:    Theme.fontFamily
                            font.pixelSize: 10
                            color:          Theme.overlay0
                            opacity:        0.7
                        }

                        Item { Layout.fillWidth: true }

                        // Cancel button
                        Rectangle {
                            implicitWidth:  80
                            implicitHeight: 32
                            radius:         Theme.pillRadius
                            color:          cancelMouse.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg
                            border.color:   Theme.moduleBorder
                            border.width:   1

                            Text {
                                anchors.centerIn: parent
                                text:           "Cancel"
                                font.family:    Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold:      true
                                color:          cancelMouse.containsMouse ? Theme.text : Theme.subtext0
                            }

                            MouseArea {
                                id:          cancelMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape:  Qt.PointingHandCursor
                                onClicked:    modal.cancelAndClose()
                            }
                        }

                        // Open / Save button
                        Rectangle {
                            implicitWidth:  openBtnRow.implicitWidth + 24
                            implicitHeight: 32
                            radius:         Theme.pillRadius
                            color:          openMouse.containsMouse
                                                ? Qt.darker(Theme.accent, 1.12)
                                                : (modal.selectedPaths.length > 0 ? Theme.accent : Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.6))

                            RowLayout {
                                id:              openBtnRow
                                anchors.centerIn: parent
                                spacing:         6

                                Text {
                                    text:           modal.requestMode === "save" ? "󰆓" : "󰂑"
                                    font.family:    Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    color:          Theme.crust
                                }
                                Text {
                                    text: modal.requestMode === "save"
                                              ? "Save"
                                              : (modal.selectedPaths.length > 1
                                                     ? "Open " + modal.selectedPaths.length + " files"
                                                     : "Open")
                                    font.family:    Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold:      true
                                    color:          Theme.crust
                                }
                            }

                            MouseArea {
                                id:          openMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape:  Qt.PointingHandCursor
                                onClicked:    modal.confirmSelection()
                            }
                        }
                    }
                }
            }

            // Vertical divider (before preview)
            Rectangle {
                Layout.fillHeight: true
                implicitWidth:     1
                color:             Theme.barBorder
                opacity:           0.5
                visible:           modal.previewVisible
            }

            // ── Right: collapsible preview panel ──────────────────────────────
            FilePickerPreview {
                id:      previewPanel
                Layout.fillHeight: true
                Layout.topMargin:    8
                Layout.rightMargin:  8
                Layout.bottomMargin: 8
                visible: modal.previewVisible

                entry:   modal.previewEntry
                content: modal.previewContent

                Behavior on visible {
                    NumberAnimation { duration: 180; easing.type: Easing.InOutCubic }
                }
            }
        }
    }
}
