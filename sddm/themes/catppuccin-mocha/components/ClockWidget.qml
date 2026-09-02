import QtQuick
import QtQuick.Controls

Item {
    id: clockRoot

    property string greetingText: "Welcome!"
    property string timeFormat: "HH:mm"
    property string dateFormat: "dddd, d 'of' MMMM"
    property string fontFamily: "JetBrainsMono Nerd Font"
    property color greetingColor: "#ffffff"
    property color timeColor: "#ffffff"
    property color dateColor: "#cdd6f4"
    property bool showGreeting: true

    implicitWidth: clockColumn.implicitWidth
    implicitHeight: clockColumn.implicitHeight

    Timer {
        id: timer
        interval: 1000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: {
            var date = new Date()
            timeLabel.text = Qt.formatTime(date, clockRoot.timeFormat)
            dateLabel.text = Qt.formatDate(date, clockRoot.dateFormat)
        }
    }

    Column {
        id: clockColumn
        anchors.centerIn: parent
        spacing: 6

        // Welcome Header
        Text {
            id: greetingLabel
            visible: clockRoot.showGreeting
            anchors.horizontalCenter: parent.horizontalCenter
            text: clockRoot.greetingText
            color: clockRoot.greetingColor
            font.family: clockRoot.fontFamily
            font.pixelSize: 30
            font.weight: Font.DemiBold
            renderType: Text.NativeRendering
        }

        // Live Clock
        Text {
            id: timeLabel
            anchors.horizontalCenter: parent.horizontalCenter
            color: clockRoot.timeColor
            font.family: clockRoot.fontFamily
            font.pixelSize: 56
            font.bold: true
            renderType: Text.NativeRendering
        }

        // Full Date
        Text {
            id: dateLabel
            anchors.horizontalCenter: parent.horizontalCenter
            color: clockRoot.dateColor
            font.family: clockRoot.fontFamily
            font.pixelSize: 15
            font.weight: Font.Normal
            opacity: 0.85
            renderType: Text.NativeRendering
        }
    }
}

