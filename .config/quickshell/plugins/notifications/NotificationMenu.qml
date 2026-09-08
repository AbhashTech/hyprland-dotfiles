import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 460
    implicitHeight: 520
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property var allNotifications: []
    property var filteredNotifications: []
    property int selectedIndex: 0
    property bool dndActive: false

    property bool confirmingClear: false

    function refreshNotifications() {
        if (!notifProc.running) {
            notifProc.running = true;
        }
    }

    function filterNotifications() {
        var q = searchInput.text.toLowerCase().trim();
        var list = [];
        for (var i = 0; i < root.allNotifications.length; i++) {
            var item = root.allNotifications[i];
            if (q.length === 0 ||
                (item.summary && item.summary.toLowerCase().indexOf(q) !== -1) ||
                (item.body && item.body.toLowerCase().indexOf(q) !== -1) ||
                (item.appName && item.appName.toLowerCase().indexOf(q) !== -1)) {
                list.push(item);
            }
        }
        root.filteredNotifications = list;
        root.selectedIndex = 0;
    }

    function dismissItem(item) {
        if (!item) return;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "dismiss", item.id.toString()]);
        root.allNotifications = root.allNotifications.filter(it => it.id !== item.id);
        root.filterNotifications();
    }

    function invokeItem(item) {
        if (!item) return;
        PluginManager.closeAll();
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "invoke", item.id.toString()]);
    }

    function requestClearAll() {
        if (root.allNotifications.length === 0) return;
        root.confirmingClear = true;
    }

    function confirmClearAll() {
        root.confirmingClear = false;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "dismiss-all"]);
        root.allNotifications = [];
        root.filteredNotifications = [];
        PluginManager.closeAll();
    }

    function cancelClearAll() {
        root.confirmingClear = false;
        searchInput.forceActiveFocus();
    }

    function toggleDnd() {
        root.dndActive = !root.dndActive;
        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "toggle-dnd"]);
    }

    Process {
        id: ctlProc
    }

    Process {
        id: notifProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "list"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (parsed && Array.isArray(parsed.notifications)) {
                        root.allNotifications = parsed.notifications;
                        root.dndActive = !!parsed.dnd;
                        root.filterNotifications();
                    }
                } catch (e) {}
            }
        }
    }

    focus: true
    Keys.onEscapePressed: event => {
        if (root.confirmingClear) {
            root.cancelClearAll();
            event.accepted = true;
            return;
        }
        PluginManager.closeAll();
        event.accepted = true;
    }

    function grabFocus() {
        root.confirmingClear = false;
        searchInput.text = "";
        root.refreshNotifications();
        searchInput.forceActiveFocus();
    }

    Component.onCompleted: root.grabFocus()

    Connections {
        target: PluginManager
        function onNotificationVisibleChanged() {
            if (PluginManager.notificationVisible) {
                root.grabFocus();
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            // Notification Title
            RowLayout {
                spacing: 8

                Text {
                    text: root.dndActive ? "󰂛" : "󰂚"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeIcon + 2
                    color: root.dndActive ? Theme.peach : Theme.accent
                }

                Text {
                    text: "Notifications"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    color: Theme.text
                }

                Rectangle {
                    implicitWidth: countText.implicitWidth + 12
                    implicitHeight: 20
                    radius: 10
                    color: root.allNotifications.length > 0 ? Theme.accent : Theme.moduleBg

                    Text {
                        id: countText
                        anchors.centerIn: parent
                        text: root.allNotifications.length.toString()
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        font.bold: true
                        color: root.allNotifications.length > 0 ? Theme.crust : Theme.subtext0
                    }
                }
            }

            Item { Layout.fillWidth: true }

            // DND Toggle Button
            Rectangle {
                implicitWidth: dndRow.implicitWidth + 16
                implicitHeight: 32
                radius: Theme.pillRadius
                color: root.dndActive ? Theme.peach : (dndArea.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg)
                border.color: root.dndActive ? Theme.peach : Theme.moduleBorder
                border.width: 1

                RowLayout {
                    id: dndRow
                    anchors.centerIn: parent
                    spacing: 6

                    Text {
                        text: root.dndActive ? "󰂛" : "󰂚"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        color: root.dndActive ? Theme.crust : Theme.text
                    }

                    Text {
                        text: root.dndActive ? "DND On" : "DND"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: true
                        color: root.dndActive ? Theme.crust : Theme.text
                    }
                }

                MouseArea {
                    id: dndArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.toggleDnd()
                }
            }

            // Clear All Button
            Rectangle {
                implicitWidth: 34
                implicitHeight: 32
                radius: Theme.pillRadius
                color: clearArea.containsMouse ? Theme.red : Theme.moduleBg
                border.color: Theme.moduleBorder
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰆴"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    color: clearArea.containsMouse ? "#ffffff" : Theme.red
                }

                MouseArea {
                    id: clearArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.requestClearAll()
                }
            }
        }

        // Search Input Bar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 38
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
                    text: "󰍉"
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
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
                        text: "Filter notifications..."
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        color: Theme.overlay0
                        visible: !searchInput.text && !searchInput.activeFocus
                    }

                    onTextChanged: root.filterNotifications()
                    Keys.onEscapePressed: PluginManager.closeAll()
                    Keys.onReturnPressed: {
                        if (root.filteredNotifications.length > 0 && root.selectedIndex >= 0 && root.selectedIndex < root.filteredNotifications.length) {
                            root.invokeItem(root.filteredNotifications[root.selectedIndex]);
                        }
                    }
                    Keys.onDownPressed: {
                        if (root.selectedIndex < root.filteredNotifications.length - 1) {
                            root.selectedIndex++;
                            notifListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                        }
                    }
                    Keys.onUpPressed: {
                        if (root.selectedIndex > 0) {
                            root.selectedIndex--;
                            notifListView.positionViewAtIndex(root.selectedIndex, ListView.Contain);
                        }
                    }
                }
            }
        }

        // Notification List
        ListView {
            id: notifListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.filteredNotifications
            spacing: 6

            delegate: Rectangle {
                id: notifCard
                required property var modelData
                required property int index

                width: notifListView.width
                implicitHeight: cardContent.implicitHeight + 20
                radius: Theme.pillRadius
                color: root.selectedIndex === index ? Theme.moduleHoverBg : Theme.moduleBg
                border.color: root.selectedIndex === index ? Theme.accent : (modelData.urgency === "critical" ? Theme.red : Theme.moduleBorder)
                border.width: 1

                ColumnLayout {
                    id: cardContent
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 4

                    // App Name & Live Tag & Dismiss
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        // Urgency / App indicator
                        Rectangle {
                            implicitWidth: 8
                            implicitHeight: 8
                            radius: 4
                            color: modelData.urgency === "critical" ? Theme.red : (modelData.urgency === "low" ? Theme.subtext0 : Theme.accent)
                        }

                        Text {
                            text: modelData.appName || "Notification"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: Theme.accent
                        }

                        // Live badge
                        Rectangle {
                            visible: !!modelData.isLive
                            implicitWidth: 38
                            implicitHeight: 16
                            radius: 8
                            color: Theme.green

                            Text {
                                anchors.centerIn: parent
                                text: "LIVE"
                                font.family: Theme.fontFamily
                                font.pixelSize: 9
                                font.bold: true
                                color: Theme.crust
                            }
                        }

                        Item { Layout.fillWidth: true }

                        // Single dismiss button
                        Rectangle {
                            implicitWidth: 24
                            implicitHeight: 24
                            radius: 12
                            color: delMouse.containsMouse ? Theme.red : "transparent"
                            z: 10

                            Text {
                                anchors.centerIn: parent
                                text: "󰅖"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: delMouse.containsMouse ? "#ffffff" : Theme.overlay0
                            }

                            MouseArea {
                                id: delMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.dismissItem(modelData)
                            }
                        }
                    }

                    // Content Area (Clickable to invoke action)
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: textColumn.implicitHeight

                        ColumnLayout {
                            id: textColumn
                            anchors.fill: parent
                            spacing: 2

                            // Summary / Title
                            Text {
                                visible: modelData.summary && modelData.summary.length > 0
                                Layout.fillWidth: true
                                text: modelData.summary || ""
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold: true
                                color: Theme.text
                                wrapMode: Text.Wrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }

                            // Body
                            Text {
                                visible: modelData.body && modelData.body.length > 0
                                Layout.fillWidth: true
                                text: modelData.body || ""
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.subtext0
                                wrapMode: Text.Wrap
                                maximumLineCount: 3
                                elide: Text.ElideRight
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: root.selectedIndex = index
                            onClicked: root.invokeItem(modelData)
                        }
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: root.filteredNotifications.length === 0
                text: "No notifications"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                color: Theme.overlay0
            }
        }

        // Status row
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: root.filteredNotifications.length + " Notifications"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Click to View • Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }
    }

    // Confirmation Overlay Dialog
    Rectangle {
        id: confirmOverlay
        anchors.fill: parent
        radius: Theme.barRadius
        color: Qt.rgba(Theme.crust.r, Theme.crust.g, Theme.crust.b, 0.94)
        visible: root.confirmingClear
        z: 100

        MouseArea {
            anchors.fill: parent
            onClicked: root.cancelClearAll()
        }

        Rectangle {
            anchors.centerIn: parent
            width: parent.width - 48
            implicitHeight: confirmCol.implicitHeight + 36
            radius: Theme.pillRadius
            color: Theme.moduleBg
            border.color: Theme.red
            border.width: 1

            MouseArea {
                anchors.fill: parent
            }

            ColumnLayout {
                id: confirmCol
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Rectangle {
                        implicitWidth: 38
                        implicitHeight: 38
                        radius: 19
                        color: Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.18)

                        Text {
                            anchors.centerIn: parent
                            text: "󰆴"
                            font.family: Theme.fontFamily
                            font.pixelSize: 18
                            color: Theme.red
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            text: "Clear All Notifications?"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeLarge
                            font.bold: true
                            color: Theme.text
                        }

                        Text {
                            text: "This will permanently remove all active and historical notifications."
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext0
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    // Cancel Button
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 36
                        radius: Theme.pillRadius
                        color: cancelArea.containsMouse ? Theme.moduleHoverBg : Theme.surface0
                        border.color: Theme.moduleBorder
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: "Cancel"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                            color: Theme.text
                        }

                        MouseArea {
                            id: cancelArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.cancelClearAll()
                        }
                    }

                    // Confirm Clear Button
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 36
                        radius: Theme.pillRadius
                        color: confirmBtnArea.containsMouse ? Qt.darker(Theme.red, 1.15) : Theme.red

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 6

                            Text {
                                text: "󰆴"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                color: "#ffffff"
                            }

                            Text {
                                text: "Clear All"
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSize
                                font.bold: true
                                color: "#ffffff"
                            }
                        }

                        MouseArea {
                            id: confirmBtnArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.confirmClearAll()
                        }
                    }
                }
            }
        }
    }
}
