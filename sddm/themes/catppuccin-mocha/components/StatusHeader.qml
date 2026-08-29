import QtQuick
import QtQuick.Controls

Item {
    id: statusRoot

    property string hostName: ""
    property var sessionModel: null
    property int currentSessionIndex: 0
    property bool showHost: true
    property bool showBattery: true
    property bool showSessions: true
    property bool showPower: true

    signal sessionChanged(int index)
    signal powerOff()
    signal reboot()
    signal suspend()
    signal hibernate()

    implicitWidth: parent ? parent.width : 800
    implicitHeight: 48

    // Left Corner: Host Badge
    Rectangle {
        id: hostBadge
        visible: statusRoot.showHost
        anchors.left: parent.left
        anchors.leftMargin: 24
        anchors.verticalCenter: parent.verticalCenter
        height: 36
        width: hostRow.implicitWidth + 24
        radius: 18
        color: Qt.rgba(24/255, 24/255, 37/255, 0.7)
        border.color: Qt.rgba(49/255, 50/255, 68/255, 0.8)
        border.width: 1

        Row {
            id: hostRow
            anchors.centerIn: parent
            spacing: 8

            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: "#a6e3a1" // Green online status indicator
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: statusRoot.hostName !== "" ? statusRoot.hostName : "Hyprland Desktop"
                color: "#cdd6f4"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 12
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    // Right Corner: Session Selector + Power Menu
    Row {
        anchors.right: parent.right
        anchors.rightMargin: 24
        anchors.verticalCenter: parent.verticalCenter
        spacing: 12

        // Session Dropdown
        SessionDropdown {
            id: sessionDropdown
            visible: statusRoot.showSessions
            sessionModel: statusRoot.sessionModel
            currentIndex: statusRoot.currentSessionIndex
            anchors.verticalCenter: parent.verticalCenter
            onSessionSelected: function(idx) {
                statusRoot.sessionChanged(idx)
            }
        }

        // Power Buttons
        PowerMenu {
            id: powerMenu
            visible: statusRoot.showPower
            anchors.verticalCenter: parent.verticalCenter
            onPowerOffClicked: statusRoot.powerOff()
            onRebootClicked: statusRoot.reboot()
            onSuspendClicked: statusRoot.suspend()
            onHibernateClicked: statusRoot.hibernate()
        }
    }
}
