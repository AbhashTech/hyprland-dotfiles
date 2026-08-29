import QtQuick
import QtQuick.Controls

Item {
    id: dialogRoot

    property string title: "Confirm Action"
    property string message: "Are you sure you want to proceed?"
    property string confirmText: "Confirm"
    property string cancelText: "Cancel"
    property color accentColor: "#f38ba8"
    property bool isDestructive: true

    signal confirmed()
    signal cancelled()

    anchors.fill: parent
    visible: opacity > 0
    opacity: 0

    Behavior on opacity { NumberAnimation { duration: 180 } }

    function open() {
        opacity = 1
    }

    function close() {
        opacity = 0
        cancelled()
    }

    // Backdrop
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(17/255, 17/255, 27/255, 0.7)

        MouseArea {
            anchors.fill: parent
            onClicked: dialogRoot.close()
        }
    }

    // Modal Card
    Rectangle {
        id: modalCard
        anchors.centerIn: parent
        width: 360
        height: 200
        radius: 20
        color: "#181825"
        border.color: dialogRoot.accentColor
        border.width: 1

        Column {
            anchors.centerIn: parent
            spacing: 16
            width: parent.width - 48

            // Title
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8

                Image {
                    width: 20
                    height: 20
                    source: "../assets/icons/warning.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: dialogRoot.title
                    color: "#cdd6f4"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 18
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Message
            Text {
                width: parent.width
                text: dialogRoot.message
                color: "#a6adc8"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 13
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            // Action Buttons
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 14

                // Cancel Button
                Rectangle {
                    width: 120
                    height: 38
                    radius: 10
                    color: cancelMouse.containsMouse ? "#45475a" : "#313244"
                    border.color: "#45475a"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: dialogRoot.cancelText
                        color: "#cdd6f4"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 13
                        font.bold: true
                    }

                    MouseArea {
                        id: cancelMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: dialogRoot.close()
                    }
                }

                // Confirm Button
                Rectangle {
                    width: 120
                    height: 38
                    radius: 10
                    color: confirmMouse.containsMouse ? "#eba0ac" : dialogRoot.accentColor

                    Text {
                        anchors.centerIn: parent
                        text: dialogRoot.confirmText
                        color: "#11111b"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 13
                        font.bold: true
                    }

                    MouseArea {
                        id: confirmMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            dialogRoot.opacity = 0
                            dialogRoot.confirmed()
                        }
                    }
                }
            }
        }
    }
}
