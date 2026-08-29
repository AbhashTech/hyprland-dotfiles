import QtQuick
import QtQuick.Controls

Item {
    id: avatarRoot

    property string avatarSource: ""
    property string fallbackSource: "../assets/default-avatar.svg"
    property string username: ""
    property string realName: ""
    property color accentColor: "#cba6f7"
    property color textColor: "#cdd6f4"
    property color subtextColor: "#a6adc8"
    property real avatarSize: 96
    property bool isMultipleUsers: false

    signal userClicked()

    implicitWidth: Math.max(avatarContainer.width, nameColumn.implicitWidth)
    implicitHeight: avatarContainer.height + (nameColumn.visible ? nameColumn.implicitHeight + 12 : 0)

    Column {
        anchors.centerIn: parent
        spacing: 12

        // Circular Avatar with Glowing Border
        Rectangle {
            id: avatarContainer
            anchors.horizontalCenter: parent.horizontalCenter
            width: avatarRoot.avatarSize
            height: avatarRoot.avatarSize
            radius: avatarRoot.avatarSize / 2
            color: "#181825"
            border.color: avatarMouseArea.containsMouse ? avatarRoot.accentColor : Qt.rgba(203/255, 166/255, 247/255, 0.4)
            border.width: 3

            Behavior on border.color { ColorAnimation { duration: 200 } }

            // Inner Avatar Image
            Image {
                id: avatarImg
                anchors.fill: parent
                anchors.margins: 4
                source: (avatarRoot.avatarSource !== "" && avatarRoot.avatarSource !== undefined) ? avatarRoot.avatarSource : avatarRoot.fallbackSource
                fillMode: Image.PreserveAspectCrop
                smooth: true
                asynchronous: true
                onStatusChanged: {
                    if (status === Image.Error && source !== avatarRoot.fallbackSource) {
                        source = avatarRoot.fallbackSource
                    }
                }
            }

            // Glow overlay when hovered
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                color: Qt.rgba(203/255, 166/255, 247/255, avatarMouseArea.containsMouse ? 0.12 : 0.0)
                Behavior on color { ColorAnimation { duration: 150 } }
            }

            MouseArea {
                id: avatarMouseArea
                anchors.fill: parent
                cursorShape: avatarRoot.isMultipleUsers ? Qt.PointingHandCursor : Qt.ArrowCursor
                hoverEnabled: true
                onClicked: {
                    if (avatarRoot.isMultipleUsers) {
                        avatarRoot.userClicked()
                    }
                }
            }
        }

        // User Names
        Column {
            id: nameColumn
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 2

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 6

                Text {
                    id: primaryName
                    text: (avatarRoot.realName !== "" && avatarRoot.realName !== undefined) ? avatarRoot.realName : (avatarRoot.username !== "" ? avatarRoot.username : "User")
                    color: avatarRoot.textColor
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 18
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                }

                Image {
                    id: userSelectIcon
                    visible: avatarRoot.isMultipleUsers
                    width: 14
                    height: 14
                    source: "../assets/icons/chevron-down.svg"
                    fillMode: Image.PreserveAspectFit
                    anchors.verticalCenter: parent.verticalCenter
                    opacity: 0.7
                }
            }

            Text {
                id: secondaryName
                visible: avatarRoot.realName !== "" && avatarRoot.realName !== undefined && avatarRoot.realName !== avatarRoot.username && avatarRoot.username !== ""
                anchors.horizontalCenter: parent.horizontalCenter
                text: "@" + avatarRoot.username
                color: avatarRoot.subtextColor
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 12
            }
        }
    }
}
