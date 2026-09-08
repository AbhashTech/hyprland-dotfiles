import QtQuick
import Quickshell
import Quickshell.Io
import ".."

PopupWindow {
    id: previewPop

    property var barWindow: null
    property var targetItem: parent
    property bool isHovered: false
    property int workspaceId: 1
    property bool isActiveWs: false
    property var clientsList: [] // Array of { address, class, title, at, size, floating, fullscreen }
    property int showDelay: 150
    property int hideDelay: 120
    property int previewVersion: 0

    anchor.window: previewPop.barWindow
    anchor.item: previewPop.targetItem
    anchor.edges: Edges.Bottom
    anchor.gravity: Edges.Bottom
    anchor.margins.top: 8

    implicitWidth: previewContainer.implicitWidth
    implicitHeight: previewContainer.implicitHeight

    color: "transparent"
    visible: previewContainer.opacity > 0

    function cleanAddress(addr) {
        if (!addr) return "none";
        return addr.toString().replace(/^0x/, "");
    }

    function getAppIcon(appClass, appTitle) {
        var c = (appClass || "").toLowerCase();
        var t = (appTitle || "").toLowerCase();

        if (c.indexOf("firefox") !== -1 || c.indexOf("zen") !== -1 || c.indexOf("librewolf") !== -1 || c.indexOf("waterfox") !== -1) return "󰈹";
        if (c.indexOf("chrome") !== -1 || c.indexOf("chromium") !== -1 || c.indexOf("brave") !== -1 || c.indexOf("edge") !== -1) return "󰊯";
        if (c.indexOf("kitty") !== -1 || c.indexOf("alacritty") !== -1 || c.indexOf("foot") !== -1 || c.indexOf("wezterm") !== -1 || c.indexOf("terminal") !== -1 || c.indexOf("konsole") !== -1) return "󰄛";
        if (c.indexOf("dolphin") !== -1 || c.indexOf("nautilus") !== -1 || c.indexOf("thunar") !== -1 || c.indexOf("nemo") !== -1 || c.indexOf("yazi") !== -1) return "󰉋";
        if (c.indexOf("code") !== -1 || c.indexOf("vscodium") !== -1 || c.indexOf("cursor") !== -1 || c.indexOf("nvim") !== -1 || c.indexOf("kate") !== -1 || c.indexOf("kwrite") !== -1) return "󰨞";
        if (c.indexOf("discord") !== -1 || c.indexOf("vesktop") !== -1 || c.indexOf("webcord") !== -1) return "󰙯";
        if (c.indexOf("telegram") !== -1) return "󰈰";
        if (c.indexOf("spotify") !== -1) return "󰓇";
        if (c.indexOf("obsidian") !== -1) return "󰎚";
        if (c.indexOf("slack") !== -1) return "󰒱";
        if (c.indexOf("steam") !== -1) return "󰓓";
        if (c.indexOf("gimp") !== -1 || c.indexOf("inkscape") !== -1 || c.indexOf("krita") !== -1 || c.indexOf("blender") !== -1) return "󰽉";
        if (c.indexOf("mpv") !== -1 || c.indexOf("vlc") !== -1 || c.indexOf("celluloid") !== -1) return "󰕼";
        if (c.indexOf("btop") !== -1 || c.indexOf("htop") !== -1) return "󰍛";
        if (c.indexOf("swappy") !== -1) return "󰹑";
        if (c.indexOf("lazygit") !== -1) return "󰊢";
        if (c.indexOf("lazydocker") !== -1) return "󰡨";
        if (c.indexOf("zathura") !== -1 || c.indexOf("evince") !== -1 || c.indexOf("okular") !== -1) return "󰈦";
        if (c.indexOf("libreoffice") !== -1) return "󰏫";

        return "󰖲";
    }

    function getAppColor(appClass) {
        var c = (appClass || "").toLowerCase();
        if (c.indexOf("firefox") !== -1) return Theme.peach;
        if (c.indexOf("chrome") !== -1 || c.indexOf("brave") !== -1) return Theme.yellow;
        if (c.indexOf("kitty") !== -1 || c.indexOf("terminal") !== -1) return Theme.green;
        if (c.indexOf("dolphin") !== -1 || c.indexOf("nautilus") !== -1) return Theme.blue;
        if (c.indexOf("code") !== -1 || c.indexOf("vscodium") !== -1) return Theme.sapphire;
        if (c.indexOf("discord") !== -1) return Theme.lavender;
        if (c.indexOf("spotify") !== -1) return Theme.green;
        if (c.indexOf("telegram") !== -1) return Theme.teal;
        if (c.indexOf("obsidian") !== -1) return Theme.mauve;
        return Theme.accent;
    }

    Timer {
        id: showTimer
        interval: previewPop.showDelay
        repeat: false
        onTriggered: {
            if (previewPop.isHovered || popMa.containsMouse) {
                previewPop.previewVersion++;
                captureProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/workspace_viewer/window_preview_capture.py", "capture-now"]);
                previewContainer.opacity = 1;
            }
        }
    }

    Timer {
        id: hideTimer
        interval: previewPop.hideDelay
        repeat: false
        onTriggered: {
            if (!previewPop.isHovered && !popMa.containsMouse) {
                previewContainer.opacity = 0;
            }
        }
    }

    onIsHoveredChanged: {
        if (isHovered) {
            hideTimer.stop();
            showTimer.start();
        } else {
            showTimer.stop();
            hideTimer.start();
        }
    }

    Rectangle {
        id: previewContainer
        radius: 14
        color: Theme.tooltipBg
        border.color: previewPop.isActiveWs ? Theme.blue : Theme.tooltipBorder
        border.width: 1

        opacity: 0
        Behavior on opacity {
            NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
        }

        implicitWidth: 350
        implicitHeight: contentCol.implicitHeight + 24

        MouseArea {
            id: popMa
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            onContainsMouseChanged: {
                if (!containsMouse && !previewPop.isHovered) {
                    hideTimer.start();
                }
            }
        }

        Column {
            id: contentCol
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 12
            spacing: 10
            width: previewContainer.width - 24

            // Header: Workspace ID + Active Badge + App Count
            Row {
                width: parent.width
                spacing: 8

                Rectangle {
                    implicitWidth: 26
                    implicitHeight: 26
                    radius: 7
                    color: previewPop.isActiveWs ? Theme.blue : Theme.surface1
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        anchors.centerIn: parent
                        text: previewPop.workspaceId.toString()
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        color: previewPop.isActiveWs ? "#ffffff" : Theme.text
                    }
                }

                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2
                    width: parent.width - 120

                    Text {
                        text: "Workspace " + previewPop.workspaceId
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        color: Theme.text
                    }

                    Text {
                        text: previewPop.clientsList.length > 0 
                              ? (previewPop.clientsList.length + (previewPop.clientsList.length === 1 ? " application open" : " applications open"))
                              : "No open applications"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall - 1
                        color: Theme.subtext0
                    }
                }

                // Active status pill
                Rectangle {
                    visible: previewPop.isActiveWs
                    anchors.verticalCenter: parent.verticalCenter
                    implicitWidth: activeStatusText.implicitWidth + 12
                    implicitHeight: 20
                    radius: 10
                    color: Qt.rgba(Theme.blue.r, Theme.blue.g, Theme.blue.b, 0.25)
                    border.color: Theme.blue
                    border.width: 1

                    Text {
                        id: activeStatusText
                        anchors.centerIn: parent
                        text: "󰄬 Active"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall - 2
                        font.bold: true
                        color: Theme.blue
                    }
                }
            }

            // Divider
            Rectangle {
                width: parent.width
                height: 1
                color: Theme.surface1
            }

            // Section Label for Layout Blueprint
            Row {
                visible: previewPop.clientsList.length > 0
                width: parent.width
                spacing: 6

                Text {
                    text: "󰮯"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.accent
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: "SCREEN LAYOUT & LIVE INTERFACES"
                    font.family: Theme.fontFamily
                    font.pixelSize: 9
                    font.bold: true
                    color: Theme.subtext0
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Mini Screen Wireframe Layout (if clients exist)
            Rectangle {
                id: wireframeBox
                visible: previewPop.clientsList.length > 0
                width: parent.width
                height: 115
                radius: 8
                color: Theme.crust
                border.color: Theme.surface1
                border.width: 1
                clip: true

                // Calculate bounding box bounds
                Repeater {
                    model: previewPop.clientsList

                    Rectangle {
                        id: clientRect
                        readonly property var client: modelData
                        readonly property real refW: 1920.0
                        readonly property real refH: 1080.0
                        readonly property real padding: 5

                        readonly property real rawX: (client.at && client.at.length > 0) ? client.at[0] : 0
                        readonly property real rawY: (client.at && client.at.length > 1) ? client.at[1] : 0
                        readonly property real rawW: (client.size && client.size.length > 0) ? client.size[0] : (refW / Math.max(1, previewPop.clientsList.length))
                        readonly property real rawH: (client.size && client.size.length > 1) ? client.size[1] : (refH - 40)

                        // Mapped to wireframe canvas
                        x: padding + Math.max(0, Math.min(wireframeBox.width - 2 * padding, (rawX / refW) * (wireframeBox.width - 2 * padding)))
                        y: padding + Math.max(0, Math.min(wireframeBox.height - 2 * padding, (rawY / refH) * (wireframeBox.height - 2 * padding)))
                        width: Math.max(24, Math.min(wireframeBox.width - x - padding, (rawW / refW) * (wireframeBox.width - 2 * padding)))
                        height: Math.max(22, Math.min(wireframeBox.height - y - padding, (rawH / refH) * (wireframeBox.height - 2 * padding)))
                        radius: 5
                        clip: true

                        color: Theme.mantle
                        border.color: previewPop.getAppColor(client.class)
                        border.width: 1

                        // Actual application screenshot image
                        Image {
                            id: snapImg
                            anchors.fill: parent
                            anchors.margins: 1
                            source: "file://" + Quickshell.env("HOME") + "/.cache/quickshell/window_previews/" + previewPop.cleanAddress(client.address) + ".png"
                            sourceSize: Qt.size(240, 135)
                            fillMode: Image.PreserveAspectCrop
                            smooth: true
                            asynchronous: true
                            visible: status === Image.Ready
                            opacity: 0.92
                        }

                        // Simulated application interface UI when image is not loaded
                        Item {
                            anchors.fill: parent
                            visible: snapImg.status !== Image.Ready

                            Column {
                                anchors.fill: parent

                                // Simulated window title bar
                                Rectangle {
                                    width: parent.width
                                    height: Math.max(7, Math.min(13, parent.height * 0.2))
                                    color: Qt.rgba(previewPop.getAppColor(client.class).r, previewPop.getAppColor(client.class).g, previewPop.getAppColor(client.class).b, 0.3)

                                    Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 3
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 2
                                        visible: clientRect.width > 40

                                        Rectangle { width: 3; height: 3; radius: 1.5; color: "#f38ba8" }
                                        Rectangle { width: 3; height: 3; radius: 1.5; color: "#f9e2af" }
                                        Rectangle { width: 3; height: 3; radius: 1.5; color: "#a6e3a1" }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: client.class || ""
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 6
                                        font.bold: true
                                        color: Theme.text
                                        elide: Text.ElideRight
                                        width: parent.width - 24
                                        visible: clientRect.width > 60
                                    }
                                }

                                // Simulated application content body
                                Rectangle {
                                    width: parent.width
                                    height: parent.height - Math.max(7, Math.min(13, parent.height * 0.2))
                                    color: (client.class && (client.class.toLowerCase().indexOf("kitty") !== -1 || client.class.toLowerCase().indexOf("terminal") !== -1)) ? "#11111b" : Theme.surface0

                                    // App Icon & Lines
                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 3

                                        Text {
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: previewPop.getAppIcon(client.class, client.title)
                                            font.family: Theme.fontFamily
                                            font.pixelSize: Math.max(8, Math.min(14, clientRect.height * 0.35))
                                            color: previewPop.getAppColor(client.class)
                                        }

                                        Column {
                                            anchors.verticalCenter: parent.verticalCenter
                                            spacing: 2
                                            visible: clientRect.width > 55

                                            Rectangle { width: Math.min(45, clientRect.width - 26); height: 2; radius: 1; color: Theme.surface2 }
                                            Rectangle { width: Math.min(30, clientRect.width - 34); height: 2; radius: 1; color: Theme.surface1 }
                                        }
                                    }
                                }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (client.address) {
                                    dispatchProc.exec(["bash", "-c", "hyprctl dispatch focuswindow address:" + client.address + " 2>/dev/null; hyprctl dispatch workspace " + previewPop.workspaceId + " 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({workspace = " + previewPop.workspaceId + "})' 2>/dev/null"]);
                                    previewContainer.opacity = 0;
                                }
                            }
                        }
                    }
                }
            }

            // List of Open Windows / Apps
            Column {
                width: parent.width
                spacing: 6
                visible: previewPop.clientsList.length > 0

                Repeater {
                    model: previewPop.clientsList

                    Rectangle {
                        id: appCard
                        readonly property var client: modelData
                        width: parent.width
                        implicitHeight: 44
                        radius: 8
                        color: cardArea.containsMouse ? Theme.surface1 : Theme.surface0
                        border.color: cardArea.containsMouse ? previewPop.getAppColor(client.class) : Theme.surface2
                        border.width: 1

                        Behavior on color { ColorAnimation { duration: 120 } }
                        Behavior on border.color { ColorAnimation { duration: 120 } }

                        Row {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 8

                            // App Snapshot / Icon Box
                            Rectangle {
                                implicitWidth: 32
                                implicitHeight: 32
                                radius: 6
                                color: Qt.rgba(previewPop.getAppColor(client.class).r, previewPop.getAppColor(client.class).g, previewPop.getAppColor(client.class).b, 0.2)
                                anchors.verticalCenter: parent.verticalCenter
                                clip: true

                                Image {
                                    id: cardThumb
                                    anchors.fill: parent
                                    source: "file://" + Quickshell.env("HOME") + "/.cache/quickshell/window_previews/" + previewPop.cleanAddress(client.address) + ".png"
                                    sourceSize: Qt.size(48, 48)
                                    fillMode: Image.PreserveAspectCrop
                                    smooth: true
                                    asynchronous: true
                                    visible: status === Image.Ready
                                }

                                Text {
                                    anchors.centerIn: parent
                                    visible: cardThumb.status !== Image.Ready
                                    text: previewPop.getAppIcon(client.class, client.title)
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeLarge
                                    color: previewPop.getAppColor(client.class)
                                }
                            }

                            // App Title & Class
                            Column {
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 100
                                spacing: 1

                                Text {
                                    text: (client.title && client.title.length > 0) ? client.title : (client.class || "Application")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    color: Theme.text
                                    elide: Text.ElideRight
                                    width: parent.width
                                }

                                Text {
                                    text: client.class || "Unknown"
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSizeSmall - 2
                                    color: Theme.subtext0
                                    elide: Text.ElideRight
                                    width: parent.width
                                }
                            }

                            // Layout tag (Floating / Fullscreen)
                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                implicitWidth: tagText.implicitWidth + 8
                                implicitHeight: 16
                                radius: 4
                                color: client.floating ? Qt.rgba(Theme.peach.r, Theme.peach.g, Theme.peach.b, 0.2) : Qt.rgba(Theme.surface2.r, Theme.surface2.g, Theme.surface2.b, 0.4)
                                border.color: client.floating ? Theme.peach : Theme.surface2
                                border.width: 1

                                Text {
                                    id: tagText
                                    anchors.centerIn: parent
                                    text: client.fullscreen ? "Full" : (client.floating ? "Float" : "Tile")
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 9
                                    font.bold: true
                                    color: client.floating ? Theme.peach : Theme.subtext0
                                }
                            }
                        }

                        MouseArea {
                            id: cardArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (client.address) {
                                    dispatchProc.exec(["bash", "-c", "hyprctl dispatch focuswindow address:" + client.address + " 2>/dev/null; hyprctl dispatch workspace " + previewPop.workspaceId + " 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({workspace = " + previewPop.workspaceId + "})' 2>/dev/null"]);
                                    previewContainer.opacity = 0;
                                }
                            }
                        }
                    }
                }
            }

            // Empty State
            Rectangle {
                visible: previewPop.clientsList.length === 0
                width: parent.width
                implicitHeight: 60
                radius: 8
                color: Theme.surface0
                border.color: Theme.surface1
                border.width: 1

                Row {
                    anchors.centerIn: parent
                    spacing: 8

                    Text {
                        text: "󰖲"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeLarge + 2
                        color: Theme.overlay0
                    }

                    Text {
                        text: "Empty Workspace"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.subtext0
                    }
                }
            }

            // Footer action bar
            Rectangle {
                width: parent.width
                implicitHeight: 28
                radius: 6
                color: footerMa.containsMouse ? Theme.surface1 : "transparent"

                Row {
                    anchors.centerIn: parent
                    spacing: 6

                    Text {
                        text: "󰍹"
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.accent
                    }

                    Text {
                        text: "Click to switch to Workspace " + previewPop.workspaceId
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSizeSmall - 1
                        color: Theme.subtext0
                    }
                }

                MouseArea {
                    id: footerMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        dispatchProc.exec(["bash", "-c", "hyprctl dispatch workspace " + previewPop.workspaceId + " 2>/dev/null || hyprctl dispatch 'hl.dsp.focus({workspace = " + previewPop.workspaceId + "})' 2>/dev/null || hyprctl dispatch focusworkspaceoncurrentmonitor " + previewPop.workspaceId]);
                        previewContainer.opacity = 0;
                    }
                }
            }
        }
    }

    Process {
        id: dispatchProc
    }

    Process {
        id: captureProc
    }
}
