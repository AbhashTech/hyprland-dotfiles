import QtQuick
import QtQuick.Controls

Item {
    id: clockRoot

    property string timeFormat: "HH:mm"
    property string dateFormat: "dddd, MMMM d, yyyy"
    property string fontFamily: "JetBrainsMono Nerd Font"
    property color timeColor: "#cdd6f4"
    property color dateColor: "#b4befe"
    property color greetingColor: "#a6adc8"
    property string currentUserName: ""
    property bool showGreeting: true

    implicitWidth: clockColumn.implicitWidth
    implicitHeight: clockColumn.implicitHeight

    function getGreeting() {
        var hour = new Date().getHours()
        if (hour >= 5 && hour < 12) return "Good morning"
        if (hour >= 12 && hour < 17) return "Good afternoon"
        if (hour >= 17 && hour < 22) return "Good evening"
        return "Good night"
    }

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
            if (clockRoot.showGreeting) {
                var greet = clockRoot.getGreeting()
                if (clockRoot.currentUserName.length > 0) {
                    greetingLabel.text = greet + ", " + clockRoot.currentUserName
                } else {
                    greetingLabel.text = greet
                }
            }
        }
    }

    Column {
        id: clockColumn
        anchors.centerIn: parent
        spacing: 4

        // Greeting
        Text {
            id: greetingLabel
            visible: clockRoot.showGreeting
            anchors.horizontalCenter: parent.horizontalCenter
            color: clockRoot.greetingColor
            font.family: clockRoot.fontFamily
            font.pixelSize: 15
            font.bold: false
        }

        // Live Clock
        Text {
            id: timeLabel
            anchors.horizontalCenter: parent.horizontalCenter
            color: clockRoot.timeColor
            font.family: clockRoot.fontFamily
            font.pixelSize: 64
            font.bold: true
        }

        // Full Date
        Text {
            id: dateLabel
            anchors.horizontalCenter: parent.horizontalCenter
            color: clockRoot.dateColor
            font.family: clockRoot.fontFamily
            font.pixelSize: 14
            font.bold: false
        }
    }
}
