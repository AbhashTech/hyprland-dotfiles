import QtQuick
import QtQuick.Controls

Rectangle {
    id: card

    property color cardColor: "#cc181825"
    property color borderColor: "#313244"
    property real borderWidth: 1
    property real cardRadius: 20

    color: cardColor
    radius: cardRadius
    border.color: borderColor
    border.width: borderWidth

    // Inner subtle glow border
    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Math.max(0, card.cardRadius - 1)
        color: "transparent"
        border.color: Qt.rgba(203/255, 166/255, 247/255, 0.08)
        border.width: 1
    }
}
