import QtQuick
import Quickshell
import Quickshell.Widgets
import Quickshell.Io
import Quickshell.Services.SystemTray
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: row.implicitWidth + 16
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property var barWindow: null
    property string notifIcon: "󰂚"
    property int notifCount: 0
    property bool dndActive: false
    property bool clipDndActive: false

    Process {
        id: ctlProc
    }

    Process {
        id: notifStatusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "status"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data.trim());
                    if (obj) {
                        root.notifCount = obj.count !== undefined ? obj.count : 0;
                        root.dndActive = !!obj.dnd;
                    }
                } catch (e) {
                    try {
                        root.notifCount = parseInt(data.trim(), 10) || 0;
                    } catch (e2) {
                        root.notifCount = 0;
                    }
                }
            }
        }
    }

    Process {
        id: clipStatusProc
        command: ["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "status"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    var obj = JSON.parse(data.trim());
                    if (obj) {
                        root.clipDndActive = !!obj.dnd;
                    }
                } catch (e) {
                    root.clipDndActive = false;
                }
            }
        }
    }

    Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!notifStatusProc.running) notifStatusProc.running = true;
            if (!clipStatusProc.running) clipStatusProc.running = true;
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 8

        // System Tray Icons
        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            Repeater {
                model: SystemTray.items
                Item {
                    id: trayItemWrapper
                    required property var modelData
                    width: 18
                    height: 18
                    anchors.verticalCenter: parent.verticalCenter

                    QsMenuAnchor {
                        id: menuAnchor
                        menu: trayItemWrapper.modelData.menu
                        anchor.window: root.barWindow
                        anchor.item: trayItemWrapper
                    }

                    Image {
                        anchors.fill: parent
                        source: modelData.icon || ""
                        fillMode: Image.PreserveAspectFit
                    }

                    MouseArea {
                        id: trayMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                        onClicked: mouse => {
                            try {
                                if (mouse.button === Qt.LeftButton) {
                                    modelData.activate();
                                } else if (mouse.button === Qt.RightButton) {
                                    if (modelData.hasMenu && modelData.menu) {
                                        menuAnchor.open();
                                    } else if (modelData.hasMenu) {
                                        menuAnchor.open();
                                    } else if (typeof modelData.secondaryActivate === "function") {
                                        modelData.secondaryActivate();
                                    } else {
                                        modelData.activate();
                                    }
                                } else if (mouse.button === Qt.MiddleButton) {
                                    if (typeof modelData.secondaryActivate === "function") {
                                        modelData.secondaryActivate();
                                    }
                                }
                            } catch (e) {
                                console.log("Tray action error: " + e);
                            }
                        }
                    }

                    BarTooltip {
                        barWindow: root.barWindow
                        targetItem: trayItemWrapper
                        isHovered: trayMa.containsMouse
                        icon: "󰍜"
                        title: (modelData.title && modelData.title.length > 0) ? modelData.title : (modelData.id ? modelData.id : "System Tray Application")
                        description: "Background status indicator"
                        shortcuts: [
                            { action: "Activate", key: "Left Click" },
                            { action: "Menu", key: "Right Click" }
                        ]
                    }
                }
            }
        }

        // Clipboard Manager Button (Quickshell Plugin)
        Rectangle {
            id: clipBtn
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: 20
            implicitHeight: 20
            radius: 4
            color: clipArea.containsMouse || PluginManager.clipboardVisible ? Theme.moduleActiveBg : "transparent"

            Text {
                anchors.centerIn: parent
                text: root.clipDndActive ? "󰈉" : "󰅌"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: root.clipDndActive ? Theme.peach : Theme.lavender
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: clipBtn
                isHovered: clipArea.containsMouse
                icon: root.clipDndActive ? "󰈉" : "󰅌"
                iconColor: root.clipDndActive ? Theme.peach : Theme.lavender
                title: "Clipboard History"
                description: root.clipDndActive ? "Private Mode (Recording Paused)" : "Search and paste history entries"
                shortcuts: [
                    { action: "Open Clipboard", key: "SUPER + SHIFT + V" },
                    { action: "Alternate Shortcut", key: "SUPER + ALT + V" },
                    { action: "Wipe History", key: "Right Click" },
                    { action: "Toggle Private Mode", key: "Middle Click" }
                ]
            }

            MouseArea {
                id: clipArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("clipboard");
                        if (!clipStatusProc.running) clipStatusProc.running = true;
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "wipe"]);
                    } else if (mouse.button === Qt.MiddleButton) {
                        root.clipDndActive = !root.clipDndActive;
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/clipboard/clip_helper.py", "toggle-private"]);
                    }
                }
            }
        }

        // Notifications / Mako Button
        Rectangle {
            id: notifBtn
            anchors.verticalCenter: parent.verticalCenter
            implicitWidth: notifRow.implicitWidth + 8
            implicitHeight: 22
            radius: 4
            color: notifArea.containsMouse || PluginManager.notificationVisible ? Theme.moduleActiveBg : "transparent"

            Row {
                id: notifRow
                anchors.centerIn: parent
                spacing: 4

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.dndActive ? "󰂛" : (root.notifCount > 0 ? "󱅫" : "󰂚")
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: root.dndActive ? Theme.peach : (root.notifCount > 0 ? Theme.peach : Theme.accent)
                }

                Text {
                    visible: root.notifCount > 0
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.notifCount.toString()
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    color: Theme.peach
                }
            }

            BarTooltip {
                barWindow: root.barWindow
                targetItem: notifBtn
                isHovered: notifArea.containsMouse
                icon: root.dndActive ? "󰂛" : (root.notifCount > 0 ? "󱅫" : "󰂚")
                iconColor: root.dndActive ? Theme.peach : Theme.accent
                title: "Notification Center"
                description: root.dndActive ? "Do-Not-Disturb is ON" : (root.notifCount > 0 ? (root.notifCount + " Unread Notification" + (root.notifCount > 1 ? "s" : "")) : "No unread notifications")
                shortcuts: [
                    { action: "Open Notifications", key: "SUPER + N" },
                    { action: "Dismiss All", key: "Right Click" },
                    { action: "Toggle DND", key: "Middle Click" }
                ]
            }

            MouseArea {
                id: notifArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                onClicked: mouse => {
                    if (mouse.button === Qt.LeftButton) {
                        PluginManager.toggle("notifications");
                        if (!notifStatusProc.running) notifStatusProc.running = true;
                    } else if (mouse.button === Qt.RightButton) {
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "dismiss-all"]);
                        root.notifCount = 0;
                    } else if (mouse.button === Qt.MiddleButton) {
                        root.dndActive = !root.dndActive;
                        ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/notifications/notification_helper.py", "toggle-dnd"]);
                    }
                }
            }
        }
    }
}
