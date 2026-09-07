import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."

Rectangle {
    id: root

    implicitWidth: 620
    implicitHeight: 220
    radius: Theme.barRadius
    color: Theme.barBg
    border.color: Theme.barBorder
    border.width: 1

    property int selectedIndex: 0

    readonly property var actions: [
        { id: "lock", label: "Lock", icon: "󰌾", key: "L", desc: "hyprlock" },
        { id: "suspend", label: "Suspend", icon: "󰒲", key: "U", desc: "systemctl suspend" },
        { id: "logout", label: "Logout", icon: "󰍃", key: "E", desc: "hyprctl dispatch exit" },
        { id: "reboot", label: "Reboot", icon: "󰑐", key: "R", desc: "systemctl reboot" },
        { id: "shutdown", label: "Shutdown", icon: "󰐥", key: "S", desc: "systemctl poweroff" }
    ]

    Process {
        id: execProc
    }

    function triggerAction(actionId) {
        PluginManager.closeAll();
        switch (actionId) {
            case "lock":
                execProc.exec(["bash", "-c", "hyprlock &"]);
                break;
            case "suspend":
                execProc.exec(["systemctl", "suspend"]);
                break;
            case "logout":
                execProc.exec(["bash", "-c", "hyprctl eval 'return hl.dsp.exit()' || loginctl terminate-session ${XDG_SESSION_ID}"]);
                break;
            case "reboot":
                execProc.exec(["systemctl", "reboot"]);
                break;
            case "shutdown":
                execProc.exec(["systemctl", "poweroff"]);
                break;
        }
    }

    focus: true
    Keys.onEscapePressed: event => {
        PluginManager.closeAll();
        event.accepted = true;
    }

    function grabFocus() {
        root.selectedIndex = 0;
        root.forceActiveFocus();
    }
    Keys.onReturnPressed: {
        if (root.selectedIndex >= 0 && root.selectedIndex < root.actions.length) {
            root.triggerAction(root.actions[root.selectedIndex].id);
        }
    }
    Keys.onLeftPressed: {
        if (root.selectedIndex > 0) root.selectedIndex--;
    }
    Keys.onRightPressed: {
        if (root.selectedIndex < root.actions.length - 1) root.selectedIndex++;
    }

    // Direct hotkeys
    Keys.onPressed: event => {
        var k = event.text.toLowerCase();
        if (k === "l") { root.triggerAction("lock"); event.accepted = true; }
        else if (k === "u") { root.triggerAction("suspend"); event.accepted = true; }
        else if (k === "e") { root.triggerAction("logout"); event.accepted = true; }
        else if (k === "r") { root.triggerAction("reboot"); event.accepted = true; }
        else if (k === "s") { root.triggerAction("shutdown"); event.accepted = true; }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // Title Row
        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "󰐥 Session & Power Menu"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.accent
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "Esc to close"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.overlay0
            }
        }

        // Action Buttons Row
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            Repeater {
                model: root.actions

                Rectangle {
                    id: btnRect
                    required property var modelData
                    required property int index

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: Theme.pillRadius

                    readonly property bool isSelected: root.selectedIndex === index
                    readonly property bool isHovered: btnMouseArea.containsMouse

                    color: isSelected || isHovered ? Theme.moduleHoverBg : Theme.moduleBg
                    border.color: isSelected || isHovered ? (modelData.id === "shutdown" ? Theme.red : Theme.accent) : Theme.moduleBorder
                    border.width: isSelected ? 2 : 1

                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on border.color { ColorAnimation { duration: 150 } }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: modelData.icon
                            font.family: Theme.fontFamily
                            font.pixelSize: 32
                            font.bold: true
                            color: modelData.id === "shutdown" ? Theme.red : (modelData.id === "reboot" ? Theme.yellow : Theme.accent)
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: modelData.label
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                            color: Theme.text
                        }

                        // Hotkey tag
                        Rectangle {
                            Layout.alignment: Qt.AlignHCenter
                            implicitWidth: 20
                            implicitHeight: 18
                            radius: 4
                            color: Theme.surface0

                            Text {
                                anchors.centerIn: parent
                                text: modelData.key
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: true
                                color: Theme.subtext0
                            }
                        }
                    }

                    MouseArea {
                        id: btnMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: root.selectedIndex = index
                        onClicked: root.triggerAction(modelData.id)
                    }
                }
            }
        }
    }
}
