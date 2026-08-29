import QtQuick
import QtQuick.Controls

Item {
    id: dropdownRoot

    property var sessionModel: null
    property int currentIndex: 0
    property string currentSessionName: (sessionModel && sessionModel.count > 0 && currentIndex >= 0 && currentIndex < sessionModel.count) ? sessionModel.data(sessionModel.index(currentIndex, 0), Qt.UserRole + 2) || sessionModel.data(sessionModel.index(currentIndex, 0), Qt.DisplayRole) || "Session" : "Hyprland"
    property color accentColor: "#cba6f7"
    property color textColor: "#cdd6f4"
    property color bgColor: "#181825"
    property bool isOpen: false

    signal sessionSelected(int index)

    implicitWidth: 160
    implicitHeight: 36

    // Dropdown Button
    Rectangle {
        id: buttonRect
        anchors.fill: parent
        radius: 10
        color: btnMouse.containsMouse || dropdownRoot.isOpen ? "#313244" : Qt.rgba(49/255, 50/255, 68/255, 0.4)
        border.color: dropdownRoot.isOpen ? dropdownRoot.accentColor : Qt.rgba(69/255, 71/255, 90/255, 0.5)
        border.width: 1

        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }

        Row {
            anchors.centerIn: parent
            spacing: 8

            Image {
                width: 14
                height: 14
                source: "../assets/icons/session.svg"
                fillMode: Image.PreserveAspectFit
                anchors.verticalCenter: parent.verticalCenter
                opacity: 0.85
            }

            Text {
                id: currentLabel
                text: dropdownRoot.currentSessionName
                color: dropdownRoot.textColor
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 12
                font.bold: true
                elide: Text.ElideRight
                anchors.verticalCenter: parent.verticalCenter
            }

            Image {
                width: 12
                height: 12
                source: "../assets/icons/chevron-down.svg"
                fillMode: Image.PreserveAspectFit
                anchors.verticalCenter: parent.verticalCenter
                rotation: dropdownRoot.isOpen ? 180 : 0
                opacity: 0.7

                Behavior on rotation { NumberAnimation { duration: 200 } }
            }
        }

        MouseArea {
            id: btnMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: dropdownRoot.isOpen = !dropdownRoot.isOpen
        }
    }

    // Dropdown Popup List
    Rectangle {
        id: popupList
        visible: dropdownRoot.isOpen
        z: 999
        anchors.top: buttonRect.bottom
        anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.max(parent.width, 180)
        height: Math.min(220, (sessionModel ? sessionModel.count * 36 : 36) + 12)
        radius: 12
        color: dropdownRoot.bgColor
        border.color: dropdownRoot.accentColor
        border.width: 1
        clip: true

        ListView {
            id: listView
            anchors.fill: parent
            anchors.margins: 6
            model: dropdownRoot.sessionModel
            spacing: 2
            clip: true

            delegate: Rectangle {
                id: itemRect
                width: listView.width
                height: 32
                radius: 8
                color: itemMouse.containsMouse ? "#313244" : (index === dropdownRoot.currentIndex ? Qt.rgba(203/255, 166/255, 247/255, 0.15) : "transparent")

                Behavior on color { ColorAnimation { duration: 100 } }

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 8

                    Image {
                        width: 12
                        height: 12
                        source: "../assets/icons/session.svg"
                        fillMode: Image.PreserveAspectFit
                        anchors.verticalCenter: parent.verticalCenter
                        opacity: index === dropdownRoot.currentIndex ? 1.0 : 0.5
                    }

                    Text {
                        text: {
                            try {
                                return model.name || model.display || model.nameRole || "Session " + (index + 1)
                            } catch(e) {
                                return "Session " + (index + 1)
                            }
                        }
                        color: index === dropdownRoot.currentIndex ? dropdownRoot.accentColor : dropdownRoot.textColor
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 12
                        font.bold: index === dropdownRoot.currentIndex
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: itemMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        dropdownRoot.currentIndex = index
                        dropdownRoot.sessionSelected(index)
                        dropdownRoot.isOpen = false
                    }
                }
            }
        }
    }
}
