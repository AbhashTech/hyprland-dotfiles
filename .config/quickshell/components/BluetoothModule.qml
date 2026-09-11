import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    implicitHeight: Theme.barHeight - 8
    implicitWidth: 38
    radius: Theme.capsuleRadius

    readonly property bool isHovered: btArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property var barWindow: null

    Process {
        id: ctlProc
    }

    Text {
        anchors.centerIn: parent
        text: StatusService.btText
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fontSizeIcon
        font.bold: true
        color: StatusService.btConnected ? Theme.green : (StatusService.btPowered ? Theme.blue : Theme.red)
    }

    BarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
        icon: StatusService.btText
        iconColor: StatusService.btConnected ? Theme.green : (StatusService.btPowered ? Theme.blue : Theme.red)
        title: StatusService.btConnected ? (StatusService.btConnectedCount + " Devices Connected") : (StatusService.btPowered ? "Bluetooth On" : "Bluetooth Off")
        description: StatusService.btConnected ? "Active Bluetooth peripherals" : "Click to scan and connect devices"
        shortcuts: [
            { action: "Bluetooth Control Center", key: "Left Click" },
            { action: "Toggle Bluetooth Radio", key: "Right Click" }
        ]
    }

    MouseArea {
        id: btArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                PluginManager.toggle("bluetooth");
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["python3", Quickshell.env("HOME") + "/.config/quickshell/plugins/connectivity/wireless_ctl.py", "bt-toggle"]);
            }
        }
    }
}
