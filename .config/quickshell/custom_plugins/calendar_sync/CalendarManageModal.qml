import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.." // Theme
import "."

Rectangle {
    id: modal

    property bool isOpen: false
    signal closed()

    implicitWidth: 540
    implicitHeight: 520
    width: implicitWidth
    height: implicitHeight
    radius: 16
    color: Theme.base
    border.color: Theme.accent
    border.width: 1

    opacity: isOpen ? 1 : 0
    visible: isOpen || opacity > 0
    Behavior on opacity {
        NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
    }

    onIsOpenChanged: {
        if (isOpen) {
            CalendarSyncService.loadSources();
        }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        // Header
        RowLayout {
            width: parent.width
            spacing: 10

            Text {
                text: ""
                font.family: Theme.fontFamily
                font.pixelSize: 22
                color: Theme.accent
                Layout.alignment: Qt.AlignVCenter
            }

            ColumnLayout {
                spacing: 2
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                Text {
                    text: "Calendar Feeds & Sources"
                    font.family: Theme.fontFamily
                    font.pixelSize: 15
                    font.bold: true
                    color: Theme.text
                }
                Text {
                    text: "Import .ics calendars from URL (Google, Apple, Nextcloud) or disk"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.overlay1
                }
            }

            Rectangle {
                width: 30
                height: 30
                radius: 15
                color: closeMa.containsMouse ? Theme.surface2 : Theme.surface0
                border.color: closeMa.containsMouse ? Theme.red : Theme.surface1
                border.width: 1
                Layout.alignment: Qt.AlignVCenter

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    font.family: Theme.fontFamily
                    font.pixelSize: 15
                    font.bold: true
                    color: closeMa.containsMouse ? Theme.red : Theme.text
                }

                MouseArea {
                    id: closeMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        modal.isOpen = false;
                        modal.closed();
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 1
            color: Theme.surface0
        }

        // Input Section: Add new source
        Rectangle {
            width: parent.width
            height: addCol.implicitHeight + 20
            radius: 10
            color: Theme.mantle
            border.color: Theme.surface1
            border.width: 1

            Column {
                id: addCol
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                property string selectedColor: "#88c0d0"

                RowLayout {
                    width: parent.width
                    spacing: 8

                    // Mode toggle: URL vs Disk
                    Rectangle {
                        id: urlTab
                        width: 96
                        height: 26
                        radius: 6
                        color: newSrcType === "url" ? Theme.accent : Theme.surface0
                        property string newSrcType: "url"

                        Text {
                            anchors.centerIn: parent
                            text: "󰖟 From URL"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: urlTab.newSrcType === "url" ? Theme.crust : Theme.text
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: urlTab.newSrcType = "url"
                        }
                    }

                    Rectangle {
                        id: diskTab
                        width: 96
                        height: 26
                        radius: 6
                        color: urlTab.newSrcType === "file" ? Theme.accent : Theme.surface0

                        Text {
                            anchors.centerIn: parent
                            text: "󰉋 From Disk"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: urlTab.newSrcType === "file" ? Theme.crust : Theme.text
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: urlTab.newSrcType = "file"
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                        height: 1
                    }

                    // Color picker dots
                    Row {
                        spacing: 5
                        Layout.alignment: Qt.AlignVCenter
                        Repeater {
                            model: ["#88c0d0", "#a3be8c", "#ebcb8b", "#b48ead", "#bf616a", "#81a1c1"]
                            Rectangle {
                                width: 18
                                height: 18
                                radius: 9
                                color: modelData
                                border.color: addCol.selectedColor === modelData ? Theme.text : "transparent"
                                border.width: 2

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: addCol.selectedColor = modelData
                                }
                            }
                        }
                    }
                }

                // Input fields
                RowLayout {
                    width: parent.width
                    spacing: 8

                    Rectangle {
                        width: 130
                        height: 32
                        radius: 6
                        color: Theme.crust
                        border.color: nameInput.activeFocus ? Theme.accent : Theme.surface1
                        border.width: 1

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.IBeamCursor
                            onClicked: nameInput.forceActiveFocus()
                        }

                        TextInput {
                            id: nameInput
                            anchors.fill: parent
                            anchors.margins: 6
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            color: Theme.text
                            selectByMouse: true
                            activeFocusOnPress: true
                            clip: true

                            Text {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                visible: !nameInput.text && !nameInput.activeFocus
                                text: "Calendar Name..."
                                color: Theme.overlay0
                                font.pixelSize: 11
                                font.family: Theme.fontFamily
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 32
                        radius: 6
                        color: Theme.crust
                        border.color: pathInput.activeFocus ? Theme.accent : Theme.surface1
                        border.width: 1

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.IBeamCursor
                            onClicked: pathInput.forceActiveFocus()
                        }

                        TextInput {
                            id: pathInput
                            anchors.fill: parent
                            anchors.margins: 6
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            color: Theme.text
                            selectByMouse: true
                            activeFocusOnPress: true
                            clip: true

                            Text {
                                anchors.fill: parent
                                verticalAlignment: Text.AlignVCenter
                                visible: !pathInput.text && !pathInput.activeFocus
                                text: urlTab.newSrcType === "url" ? "https://example.com/calendar.ics" : "/path/to/calendar.ics"
                                color: Theme.overlay0
                                font.pixelSize: 11
                                font.family: Theme.fontFamily
                            }
                        }
                    }

                    // Browse button (if disk file)
                    Rectangle {
                        visible: urlTab.newSrcType === "file"
                        width: 68
                        height: 32
                        radius: 6
                        color: browseMa.containsMouse ? Theme.surface1 : Theme.surface0
                        border.color: Theme.surface2
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: "Browse"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: Theme.subtext0
                        }

                        MouseArea {
                            id: browseMa
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: zenityProc.exec(["python3", CalendarSyncService.helperPath, "pick-file"])
                        }
                    }

                    // Add button
                    Rectangle {
                        width: 74
                        height: 32
                        radius: 6
                        color: addMa.containsMouse ? Qt.lighter(Theme.accent, 1.1) : Theme.accent

                        Text {
                            anchors.centerIn: parent
                            text: "+ Add"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: Theme.crust
                        }

                        MouseArea {
                            id: addMa
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (!pathInput.text.trim()) return;
                                var calName = nameInput.text.trim() || (urlTab.newSrcType === "url" ? "Web Calendar" : "Local Calendar");
                                if (urlTab.newSrcType === "url") {
                                    CalendarSyncService.addUrlSource(calName, pathInput.text.trim(), addCol.selectedColor);
                                } else {
                                    CalendarSyncService.addFileSource(calName, pathInput.text.trim(), addCol.selectedColor);
                                }
                                pathInput.text = "";
                                nameInput.text = "";
                            }
                        }
                    }
                }
            }
        }

        // Sources List Header
        RowLayout {
            width: parent.width
            spacing: 8

            Text {
                text: "Configured Calendars (" + (CalendarSyncService.sourcesData.sources ? CalendarSyncService.sourcesData.sources.length : 0) + ")"
                font.family: Theme.fontFamily
                font.pixelSize: 13
                font.bold: true
                color: Theme.text
                Layout.alignment: Qt.AlignVCenter
            }

            Item {
                Layout.fillWidth: true
                height: 1
            }

            Rectangle {
                width: 76
                height: 24
                radius: 4
                color: syncBtnMa.containsMouse ? Theme.surface1 : Theme.surface0
                border.color: Theme.surface2
                border.width: 1
                Layout.alignment: Qt.AlignVCenter

                Row {
                    anchors.centerIn: parent
                    spacing: 4
                    Text {
                        text: ""
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        color: Theme.subtext0
                    }
                    Text {
                        text: CalendarSyncService.isSyncing ? "Syncing" : "Sync All"
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        color: Theme.subtext0
                    }
                }

                MouseArea {
                    id: syncBtnMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: CalendarSyncService.syncNow()
                }
            }
        }

        // Sources ListView
        ScrollView {
            width: parent.width
            height: 190
            clip: true

            ListView {
                width: parent.width
                spacing: 6
                model: CalendarSyncService.sourcesData.sources || []

                delegate: Rectangle {
                    width: parent ? parent.width : 480
                    height: 48
                    radius: 8
                    color: Theme.mantle
                    border.color: Theme.surface1
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        // Color dot
                        Rectangle {
                            width: 12
                            height: 12
                            radius: 6
                            color: modelData.color || Theme.accent
                            Layout.alignment: Qt.AlignVCenter
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 2

                            Row {
                                spacing: 6
                                Text {
                                    text: modelData.name || "Calendar"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: modelData.enabled ? Theme.text : Theme.overlay1
                                }
                                Text {
                                    text: (modelData.type === "url" ? "[URL]" : "[DISK]")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
                                    color: Theme.subtext0
                                }
                            }

                            Text {
                                text: modelData.path || ""
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                color: Theme.overlay0
                                elide: Text.ElideMiddle
                                Layout.fillWidth: true
                            }
                        }

                        // Toggle button
                        Rectangle {
                            width: 28
                            height: 28
                            radius: 4
                            color: toggleMa.containsMouse ? Theme.surface1 : "transparent"
                            Layout.alignment: Qt.AlignVCenter

                            Text {
                                anchors.centerIn: parent
                                text: modelData.enabled ? "󰄲" : "󰄱"
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
                                color: modelData.enabled ? Theme.green : Theme.overlay0
                            }

                            MouseArea {
                                id: toggleMa
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: CalendarSyncService.toggleSource(modelData.id)
                            }
                        }

                        // Delete button
                        Rectangle {
                            width: 28
                            height: 28
                            radius: 4
                            color: delMa.containsMouse ? Qt.rgba(Theme.red.r, Theme.red.g, Theme.red.b, 0.2) : "transparent"
                            Layout.alignment: Qt.AlignVCenter

                            Text {
                                anchors.centerIn: parent
                                text: "󰆴"
                                font.family: Theme.fontFamily
                                font.pixelSize: 14
                                color: delMa.containsMouse ? Theme.red : Theme.overlay1
                            }

                            MouseArea {
                                id: delMa
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: CalendarSyncService.removeSource(modelData.id)
                            }
                        }
                    }
                }
            }
        }

        // Footer info
        RowLayout {
            width: parent.width
            spacing: 8

            Text {
                text: "Last synchronized: " + (CalendarSyncService.lastSyncTime || "Never")
                font.family: Theme.fontFamily
                font.pixelSize: 11
                color: Theme.overlay1
                Layout.alignment: Qt.AlignVCenter
                Layout.fillWidth: true
            }

            Rectangle {
                id: bottomCloseBtn
                implicitWidth: 80
                height: 28
                radius: 6
                color: bottomCloseMa.containsMouse ? Theme.surface2 : Theme.surface0
                border.color: bottomCloseMa.containsMouse ? Theme.accent : Theme.surface1
                border.width: 1

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 4

                    Text {
                        text: "󰅖"
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        color: Theme.text
                    }

                    Text {
                        text: "Close"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        font.bold: true
                        color: Theme.text
                    }
                }

                MouseArea {
                    id: bottomCloseMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        modal.isOpen = false;
                        modal.closed();
                    }
                }
            }
        }
    }

    Process {
        id: zenityProc
        stdout: SplitParser {
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (parsed && parsed.status === "ok" && parsed.path) {
                        pathInput.text = parsed.path;
                        if (!nameInput.text) {
                            var parts = parsed.path.split("/");
                            nameInput.text = parts[parts.length - 1].replace(".ics", "");
                        }
                    }
                } catch (e) {}
            }
        }
    }
}
