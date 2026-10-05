import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.." // Theme
import "."

Rectangle {
    id: pickerRoot

    signal fileSelected(string path, string name)
    signal cancelled()

    radius: 16
    color: Theme.base
    border.color: Theme.accent
    border.width: 1
    clip: true

    property string currentPath: ""
    property string parentPath: ""
    property var subDirs: []
    property var currentIcsFiles: []
    property var quickIcsFiles: []
    property bool isLoading: false

    function open(initialPath) {
        pickerRoot.visible = true;
        var p = initialPath || (Quickshell.env("HOME") + "/Downloads");
        loadDir(p);
        findQuickIcs();
    }

    function close() {
        pickerRoot.visible = false;
        pickerRoot.cancelled();
    }

    function loadDir(dirPath) {
        isLoading = true;
        listProc.exec(["python3", CalendarSyncService.helperPath, "list-dir", dirPath || ""]);
    }

    function findQuickIcs() {
        findProc.exec(["python3", CalendarSyncService.helperPath, "find-ics"]);
    }

    Process {
        id: listProc
        stdout: SplitParser {
            onRead: data => {
                pickerRoot.isLoading = false;
                try {
                    var res = JSON.parse(data);
                    if (res && res.status === "ok") {
                        pickerRoot.currentPath = res.current || "";
                        pickerRoot.parentPath = res.parent || "";
                        pickerRoot.subDirs = res.dirs || [];
                        pickerRoot.currentIcsFiles = res.icsFiles || [];
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: findProc
        stdout: SplitParser {
            onRead: data => {
                try {
                    var res = JSON.parse(data);
                    if (res && res.status === "ok") {
                        pickerRoot.quickIcsFiles = res.files || [];
                    }
                } catch (e) {}
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
            spacing: 10

            Rectangle {
                width: 32
                height: 32
                radius: 8
                color: backMa.containsMouse ? Theme.surface2 : Theme.surface0
                border.color: Theme.surface1
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "󰁞"
                    font.family: Theme.fontFamily
                    font.pixelSize: 16
                    color: Theme.accent
                }

                MouseArea {
                    id: backMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: pickerRoot.close()
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1

                Text {
                    text: "Select iCalendar (.ics) File"
                    font.family: Theme.fontFamily
                    font.pixelSize: 15
                    font.bold: true
                    color: Theme.text
                }

                Text {
                    text: "Native file browser — click any .ics file or navigate directories"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.overlay1
                }
            }

            Rectangle {
                width: 30
                height: 30
                radius: 15
                color: closeBtnMa.containsMouse ? Theme.surface2 : Theme.surface0
                border.color: closeBtnMa.containsMouse ? Theme.red : Theme.surface1
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    font.family: Theme.fontFamily
                    font.pixelSize: 14
                    font.bold: true
                    color: closeBtnMa.containsMouse ? Theme.red : Theme.text
                }

                MouseArea {
                    id: closeBtnMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: pickerRoot.close()
                }
            }
        }

        // Quick Locations Row
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Text {
                text: "Quick:"
                font.family: Theme.fontFamily
                font.pixelSize: 11
                font.bold: true
                color: Theme.subtext0
            }

            Repeater {
                model: [
                    { label: "󰉍 Downloads", path: Quickshell.env("HOME") + "/Downloads" },
                    { label: "󰋜 Home", path: Quickshell.env("HOME") },
                    { label: "󰈙 Documents", path: Quickshell.env("HOME") + "/Documents" },
                    { label: "󰉋 Calendar Data", path: Quickshell.env("HOME") + "/.config/quickshell/calendar_data" }
                ]

                Rectangle {
                    height: 24
                    implicitWidth: qTxt.implicitWidth + 14
                    radius: 6
                    color: pickerRoot.currentPath === modelData.path
                           ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.2)
                           : (qMa.containsMouse ? Theme.surface2 : Theme.surface0)
                    border.color: pickerRoot.currentPath === modelData.path ? Theme.accent : Theme.surface1
                    border.width: 1

                    Text {
                        id: qTxt
                        anchors.centerIn: parent
                        text: modelData.label
                        font.family: Theme.fontFamily
                        font.pixelSize: 10
                        font.bold: true
                        color: pickerRoot.currentPath === modelData.path ? Theme.accent : Theme.text
                    }

                    MouseArea {
                        id: qMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: pickerRoot.loadDir(modelData.path)
                    }
                }
            }

            Item { Layout.fillWidth: true }
        }

        // Current Path / Up Navigation Bar
        Rectangle {
            Layout.fillWidth: true
            height: 34
            radius: 8
            color: Theme.surface0
            border.color: Theme.surface1
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8

                // Up Button
                Rectangle {
                    width: 26
                    height: 24
                    radius: 5
                    color: upMa.containsMouse && pickerRoot.parentPath ? Theme.surface2 : Theme.surface1
                    opacity: pickerRoot.parentPath ? 1.0 : 0.4

                    Text {
                        anchors.centerIn: parent
                        text: "󰁞"
                        font.family: Theme.fontFamily
                        font.pixelSize: 14
                        font.bold: true
                        color: Theme.text
                    }

                    MouseArea {
                        id: upMa
                        anchors.fill: parent
                        enabled: !!pickerRoot.parentPath
                        hoverEnabled: true
                        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: {
                            if (pickerRoot.parentPath) pickerRoot.loadDir(pickerRoot.parentPath);
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: pickerRoot.currentPath.replace(Quickshell.env("HOME"), "~")
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.text
                    elide: Text.ElideMiddle
                }

                Text {
                    text: pickerRoot.isLoading ? "Loading..." : (pickerRoot.currentIcsFiles.length + " .ics files")
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: pickerRoot.currentIcsFiles.length > 0 ? Theme.accent : Theme.overlay1
                }
            }
        }

        // Main Scrollable Area
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 12

                // 1. Detected .ics files in Current Directory
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    visible: pickerRoot.currentIcsFiles.length > 0

                    RowLayout {
                        spacing: 6
                        Text {
                            text: "󰸗"
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            color: Theme.accent
                        }
                        Text {
                            text: "iCalendar Files in This Folder (" + pickerRoot.currentIcsFiles.length + "):"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: Theme.accent
                        }
                    }

                    Repeater {
                        model: pickerRoot.currentIcsFiles

                        Rectangle {
                            Layout.fillWidth: true
                            height: 44
                            radius: 8
                            color: curIcsMa.containsMouse ? Theme.surface2 : Theme.mantle
                            border.color: curIcsMa.containsMouse ? Theme.accent : Theme.surface1
                            border.width: curIcsMa.containsMouse ? 2 : 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 10

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: 6
                                    color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.2)

                                    Text {
                                        anchors.centerIn: parent
                                        text: "󰸗"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 15
                                        color: Theme.accent
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1

                                    Text {
                                        text: modelData.name
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: Theme.text
                                        elide: Text.ElideRight
                                    }

                                    Text {
                                        text: modelData.sizeStr + " • Modified: " + modelData.modifiedStr
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        color: Theme.overlay1
                                    }
                                }

                                Rectangle {
                                    width: 60
                                    height: 26
                                    radius: 5
                                    color: Theme.accent

                                    Text {
                                        anchors.centerIn: parent
                                        text: "Select"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: Theme.crust
                                    }
                                }
                            }

                            MouseArea {
                                id: curIcsMa
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var baseName = modelData.name.replace(/\.ics$/i, "");
                                    pickerRoot.fileSelected(modelData.path, baseName);
                                    pickerRoot.visible = false;
                                }
                            }
                        }
                    }
                }

                // 2. Detected .ics files across System (Quick Suggestions)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    visible: pickerRoot.quickIcsFiles.length > 0 && pickerRoot.currentIcsFiles.length === 0

                    RowLayout {
                        spacing: 6
                        Text {
                            text: "󰁥"
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            color: Theme.yellow
                        }
                        Text {
                            text: "Suggested .ics Files Found on System:"
                            font.family: Theme.fontFamily
                            font.pixelSize: 11
                            font.bold: true
                            color: Theme.yellow
                        }
                    }

                    Repeater {
                        model: pickerRoot.quickIcsFiles

                        Rectangle {
                            Layout.fillWidth: true
                            height: 44
                            radius: 8
                            color: qkIcsMa.containsMouse ? Theme.surface2 : Theme.mantle
                            border.color: qkIcsMa.containsMouse ? Theme.accent : Theme.surface1
                            border.width: qkIcsMa.containsMouse ? 2 : 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 10

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: 6
                                    color: Qt.rgba(Theme.yellow.r, Theme.yellow.g, Theme.yellow.b, 0.2)

                                    Text {
                                        anchors.centerIn: parent
                                        text: "󰸗"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 15
                                        color: Theme.yellow
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1

                                    Text {
                                        text: modelData.name
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: Theme.text
                                        elide: Text.ElideRight
                                    }

                                    Text {
                                        text: modelData.dir.replace(Quickshell.env("HOME"), "~") + " • " + modelData.sizeStr
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 10
                                        color: Theme.overlay1
                                        elide: Text.ElideMiddle
                                    }
                                }

                                Rectangle {
                                    width: 60
                                    height: 26
                                    radius: 5
                                    color: Theme.accent

                                    Text {
                                        anchors.centerIn: parent
                                        text: "Select"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: Theme.crust
                                    }
                                }
                            }

                            MouseArea {
                                id: qkIcsMa
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var baseName = modelData.name.replace(/\.ics$/i, "");
                                    pickerRoot.fileSelected(modelData.path, baseName);
                                    pickerRoot.visible = false;
                                }
                            }
                        }
                    }
                }

                // 3. Subdirectories Browser
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Text {
                        text: "Folders (" + pickerRoot.subDirs.length + "):"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        font.bold: true
                        color: Theme.subtext0
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 6

                        Repeater {
                            model: pickerRoot.subDirs

                            Rectangle {
                                height: 30
                                implicitWidth: Math.min(folderTxt.implicitWidth + 34, 240)
                                radius: 6
                                color: folderMa.containsMouse ? Theme.surface2 : Theme.surface0
                                border.color: folderMa.containsMouse ? Theme.accent : Theme.surface1
                                border.width: 1

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8
                                    spacing: 6

                                    Text {
                                        text: "󰉋"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 13
                                        color: Theme.blue
                                    }

                                    Text {
                                        id: folderTxt
                                        Layout.fillWidth: true
                                        text: modelData.name
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        color: Theme.text
                                        elide: Text.ElideRight
                                    }
                                }

                                MouseArea {
                                    id: folderMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: pickerRoot.loadDir(modelData.path)
                                }
                            }
                        }
                    }

                    Text {
                        visible: pickerRoot.subDirs.length === 0 && !pickerRoot.isLoading
                        text: "No subfolders"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        color: Theme.overlay0
                    }
                }
            }
        }

        // Footer Action
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Item { Layout.fillWidth: true }

            Rectangle {
                width: 90
                height: 30
                radius: 6
                color: cancelMa.containsMouse ? Theme.surface2 : Theme.surface0
                border.color: Theme.surface1
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "Cancel"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.bold: true
                    color: Theme.text
                }

                MouseArea {
                    id: cancelMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: pickerRoot.close()
                }
            }
        }
    }
}
