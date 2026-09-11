import QtQuick
import Quickshell
import ".."

Rectangle {
    id: root

    visible: BarConfig.editMode
    implicitHeight: 34
    implicitWidth: contentRow.implicitWidth + 24
    radius: 17

    color: Theme.crust
    border.color: Theme.accent
    border.width: 1

    opacity: BarConfig.editMode ? 1.0 : 0.0
    scale: BarConfig.editMode ? 1.0 : 0.9

    Behavior on opacity { NumberAnimation { duration: 180 } }
    Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }

    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: 12

        // Live Pulsing Indicator
        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6
            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: Theme.accent
                anchors.verticalCenter: parent.verticalCenter

                SequentialAnimation on opacity {
                    loops: Animation.Infinite
                    running: BarConfig.editMode
                    NumberAnimation { from: 0.3; to: 1.0; duration: 600 }
                    NumberAnimation { from: 1.0; to: 0.3; duration: 600 }
                }
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "Bar Edit Mode"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: Theme.accent
            }
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "Drag icons to move • Use 󰅁 󰅂 to step"
            font.family: Theme.fontFamily
            font.pixelSize: 11
            color: Theme.subtext0
        }

        // Open Customizer Button
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            implicitHeight: 24
            implicitWidth: customRow.implicitWidth + 12
            radius: 12
            color: customArea.containsMouse ? Theme.moduleHoverBg : Theme.moduleBg
            border.color: Theme.moduleBorder
            border.width: 1

            Row {
                id: customRow
                anchors.centerIn: parent
                spacing: 4
                Text {
                    text: "󰏖"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    color: Theme.mauve
                }
                Text {
                    text: "Settings"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.bold: true
                    color: Theme.text
                }
            }

            MouseArea {
                id: customArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: PluginManager.toggle("bar_customizer")
            }
        }

        // Done Editing Button
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            implicitHeight: 24
            implicitWidth: doneRow.implicitWidth + 14
            radius: 12
            color: doneArea.containsMouse ? Theme.teal : Theme.blue

            Row {
                id: doneRow
                anchors.centerIn: parent
                spacing: 4
                Text {
                    text: "✓"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.bold: true
                    color: "#ffffff"
                }
                Text {
                    text: "Done"
                    font.family: Theme.fontFamily
                    font.pixelSize: 11
                    font.bold: true
                    color: "#ffffff"
                }
            }

            MouseArea {
                id: doneArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: BarConfig.toggleEditMode()
            }
        }
    }
}
