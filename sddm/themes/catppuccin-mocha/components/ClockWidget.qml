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

    function updateTime() {
        var date = new Date()
        timeLabel.text = Qt.formatTime(date, clockRoot.timeFormat)
        dateLabel.text = Qt.formatDate(date, clockRoot.dateFormat)
    }

    function scheduleNextMinute() {
        var now = new Date()
        var msToNextMinute = (60 - now.getSeconds()) * 1000 - now.getMilliseconds() + 50
        if (msToNextMinute < 500) msToNextMinute = 60000
        timer.interval = msToNextMinute
        timer.restart()
    }

    Component.onCompleted: {
        updateTime()
        scheduleNextMinute()
    }

    Timer {
        id: timer
        interval: 60000
        repeat: false
        running: clockRoot.visible
        onTriggered: {
            clockRoot.updateTime()
            clockRoot.scheduleNextMinute()
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

