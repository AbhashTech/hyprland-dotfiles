import QtQuick
import QtQuick.Controls

Item {
    id: powerMenuRoot

    property bool canPowerOff: true
    property bool canReboot: true
    property bool canSuspend: true
    property string fontFamily: "JetBrainsMono Nerd Font"
    property color textColor: "#a6adc8"
    property color hoverColor: "#ffffff"

    signal powerOffClicked()
    signal rebootClicked()
    signal suspendClicked()

    implicitWidth: powerRow.implicitWidth
    implicitHeight: powerRow.implicitHeight

    Row {
        id: powerRow
        spacing: 28
        anchors.centerIn: parent

        // Suspend
        Item {
            width: 64
            height: 52
            visible: powerMenuRoot.canSuspend

            Column {
                anchors.centerIn: parent
                spacing: 6

                Image {
                    width: 20
                    height: 20
                    anchors.horizontalCenter: parent.horizontalCenter
                    source: "../assets/icons/suspend.svg"
                    fillMode: Image.PreserveAspectFit
                    opacity: suspendArea.containsMouse ? 1.0 : 0.65
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                }

                Text {
                    text: "Suspend"
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: suspendArea.containsMouse ? powerMenuRoot.hoverColor : powerMenuRoot.textColor
                    font.family: powerMenuRoot.fontFamily
                    font.pixelSize: 11
                    Behavior on color { ColorAnimation { duration: 150 } }
                }

                Rectangle {
                    width: 36
                    height: 1
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: suspendArea.containsMouse ? powerMenuRoot.hoverColor : Qt.rgba(166/255, 173/255, 200/255, 0.4)
                }
            }

            MouseArea {
                id: suspendArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: powerMenuRoot.suspendClicked()
            }
        }

        // Reboot
        Item {
            width: 64
            height: 52
            visible: powerMenuRoot.canReboot

            Column {
                anchors.centerIn: parent
                spacing: 6

                Image {
                    width: 20
                    height: 20
                    anchors.horizontalCenter: parent.horizontalCenter
                    source: "../assets/icons/reboot.svg"
                    fillMode: Image.PreserveAspectFit
                    opacity: rebootArea.containsMouse ? 1.0 : 0.65
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                }

                Text {
                    text: "Reboot"
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: rebootArea.containsMouse ? powerMenuRoot.hoverColor : powerMenuRoot.textColor
                    font.family: powerMenuRoot.fontFamily
                    font.pixelSize: 11
                    Behavior on color { ColorAnimation { duration: 150 } }
                }

                Rectangle {
                    width: 36
                    height: 1
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: rebootArea.containsMouse ? powerMenuRoot.hoverColor : Qt.rgba(166/255, 173/255, 200/255, 0.4)
                }
            }

            MouseArea {
                id: rebootArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: powerMenuRoot.rebootClicked()
            }
        }

        // Shutdown
        Item {
            width: 64
            height: 52
            visible: powerMenuRoot.canPowerOff

            Column {
                anchors.centerIn: parent
                spacing: 6

                Image {
                    width: 20
                    height: 20
                    anchors.horizontalCenter: parent.horizontalCenter
                    source: "../assets/icons/power.svg"
                    fillMode: Image.PreserveAspectFit
                    opacity: shutdownArea.containsMouse ? 1.0 : 0.65
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                }

                Text {
                    text: "Shutdown"
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: shutdownArea.containsMouse ? powerMenuRoot.hoverColor : powerMenuRoot.textColor
                    font.family: powerMenuRoot.fontFamily
                    font.pixelSize: 11
                    Behavior on color { ColorAnimation { duration: 150 } }
                }

                Rectangle {
                    width: 36
                    height: 1
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: shutdownArea.containsMouse ? powerMenuRoot.hoverColor : Qt.rgba(166/255, 173/255, 200/255, 0.4)
                }
            }

            MouseArea {
                id: shutdownArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: powerMenuRoot.powerOffClicked()
            }
        }
    }
}

