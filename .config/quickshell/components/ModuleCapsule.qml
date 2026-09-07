import QtQuick
import Quickshell
import ".."

Rectangle {
    id: capsule

    default property alias content: innerContainer.data
    property alias horizontalAlignment: innerContainer.alignment
    property alias layoutSpacing: innerContainer.spacing
    property bool hoverable: true
    readonly property bool isHovered: hoverable && mouseArea.containsMouse

    implicitHeight: Theme.barHeight - 8
    implicitWidth: innerContainer.implicitWidth + 16

    radius: Theme.capsuleRadius
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: 200 } }
    Behavior on border.color { ColorAnimation { duration: 200 } }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: capsule.hoverable
        acceptedButtons: Qt.NoButton
    }

    Row {
        id: innerContainer
        anchors.centerIn: parent
        spacing: 6
        property int alignment: Qt.AlignVCenter
    }
}
