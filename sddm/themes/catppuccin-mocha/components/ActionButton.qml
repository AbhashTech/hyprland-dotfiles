import QtQuick
import QtQuick.Controls

Item {
    id: buttonRoot

    property string iconSource: ""
    property string text: ""
    property string tooltip: ""
    property color iconColor: "#cdd6f4"
    property color hoverColor: "#cba6f7"
    property color activeColor: "#b4befe"
    property color bgBaseColor: "#313244"
    property color bgHoverColor: "#45475a"
    property real iconSize: 20
    property real buttonRadius: 12
    property bool showText: text.length > 0
    property bool isDestructive: false

    signal clicked()

    implicitWidth: showText ? (iconSize + labelText.implicitWidth + 28) : 42
    implicitHeight: 42

    Rectangle {
        id: bg
        anchors.fill: parent
        radius: buttonRoot.buttonRadius
        color: mouseArea.pressed ? (buttonRoot.isDestructive ? "#e78284" : buttonRoot.bgHoverColor)
                                 : (mouseArea.containsMouse ? (buttonRoot.isDestructive ? "#45222d" : buttonRoot.bgHoverColor)
                                                            : Qt.rgba(49/255, 50/255, 68/255, 0.5))
        border.color: mouseArea.containsMouse ? (buttonRoot.isDestructive ? "#f38ba8" : buttonRoot.hoverColor)
                                              : Qt.rgba(69/255, 71/255, 90/255, 0.4)
        border.width: 1

        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }

        Row {
            anchors.centerIn: parent
            spacing: 8

            Image {
                id: btnIcon
                width: buttonRoot.iconSize
                height: buttonRoot.iconSize
                source: buttonRoot.iconSource
                fillMode: Image.PreserveAspectFit
                anchors.verticalCenter: parent.verticalCenter
                opacity: mouseArea.containsMouse ? 1.0 : 0.85

                Behavior on opacity { NumberAnimation { duration: 150 } }
            }

            Text {
                id: labelText
                visible: buttonRoot.showText
                text: buttonRoot.text
                color: mouseArea.containsMouse ? (buttonRoot.isDestructive ? "#f38ba8" : buttonRoot.hoverColor)
                                               : buttonRoot.iconColor
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 13
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter

                Behavior on color { ColorAnimation { duration: 150 } }
            }
        }
    }

    // Tooltip
    Rectangle {
        id: tipBox
        visible: mouseArea.containsMouse && buttonRoot.tooltip.length > 0
        z: 100
        anchors.bottom: parent.top
        anchors.bottomMargin: 8
        anchors.horizontalCenter: parent.horizontalCenter
        width: tipText.implicitWidth + 16
        height: tipText.implicitHeight + 8
        radius: 6
        color: "#11111b"
        border.color: "#313244"
        border.width: 1

        Text {
            id: tipText
            anchors.centerIn: parent
            text: buttonRoot.tooltip
            color: "#cdd6f4"
            font.family: "JetBrainsMono Nerd Font"
            font.pixelSize: 11
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: buttonRoot.clicked()
    }
}
