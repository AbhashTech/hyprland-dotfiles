import QtQuick
import QtQuick.Controls

Item {
    id: usernameRoot

    property alias text: usernameInput.text
    property string placeholder: "Username"
    property color textColor: "#ffffff"
    property color placeholderColor: "#a6adc8"
    property color accentColor: "#cba6f7"
    property color bgBaseColor: Qt.rgba(20/255, 20/255, 30/255, 0.45)
    property color bgFocusColor: Qt.rgba(35/255, 35/255, 50/255, 0.7)
    property bool isMultipleUsers: false
    property bool readOnly: false

    signal submitted()
    signal userSelectClicked()

    implicitWidth: 320
    implicitHeight: 46

    function focusInput() {
        usernameInput.forceActiveFocus()
    }

    Rectangle {
        id: container
        anchors.fill: parent
        radius: 23
        color: usernameInput.activeFocus ? usernameRoot.bgFocusColor : usernameRoot.bgBaseColor
        border.color: usernameInput.activeFocus ? usernameRoot.accentColor : Qt.rgba(255/255, 255/255, 255/255, 0.5)
        border.width: usernameInput.activeFocus ? 2 : 1.2

        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }

        Row {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 12
            spacing: 10

            // Left black pill badge with user icon
            Rectangle {
                id: iconBadge
                width: 60
                height: 34
                radius: 17
                anchors.verticalCenter: parent.verticalCenter
                color: "#11111b"
                border.color: Qt.rgba(255/255, 255/255, 255/255, 0.2)
                border.width: 1

                Image {
                    anchors.centerIn: parent
                    width: 15
                    height: 15
                    source: "../assets/icons/user.svg"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: badgeMouse
                    anchors.fill: parent
                    cursorShape: usernameRoot.isMultipleUsers ? Qt.PointingHandCursor : Qt.ArrowCursor
                    hoverEnabled: true
                    onClicked: {
                        if (usernameRoot.isMultipleUsers) {
                            usernameRoot.userSelectClicked()
                        }
                    }
                }
            }

            // Username text input
            TextInput {
                id: usernameInput
                width: parent.width - iconBadge.width - (dropdownIcon.visible ? 24 : 0) - 26
                height: parent.height
                anchors.verticalCenter: parent.verticalCenter
                verticalAlignment: TextInput.AlignVCenter
                color: usernameRoot.textColor
                selectionColor: usernameRoot.accentColor
                selectedTextColor: "#11111b"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 14
                clip: true
                readOnly: usernameRoot.readOnly
                activeFocusOnTab: true

                onAccepted: {
                    usernameRoot.submitted()
                }

                Text {
                    id: placeholderText
                    text: usernameRoot.placeholder
                    color: usernameRoot.placeholderColor
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 13
                    anchors.verticalCenter: parent.verticalCenter
                    visible: !usernameInput.text && !usernameInput.inputMethodComposing
                    opacity: 0.65
                }
            }

            // Optional Dropdown Arrow
            Image {
                id: dropdownIcon
                visible: usernameRoot.isMultipleUsers
                width: 14
                height: 14
                anchors.verticalCenter: parent.verticalCenter
                source: "../assets/icons/chevron-down.svg"
                fillMode: Image.PreserveAspectFit
                opacity: 0.7

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: usernameRoot.userSelectClicked()
                }
            }
        }
    }
}
