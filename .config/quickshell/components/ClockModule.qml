import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property bool showDate: false
    property string timeStr: ""
    property string dateStr: ""

    implicitHeight: Theme.barHeight - 8
    implicitWidth: row.implicitWidth + 20
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    CalendarTooltip {
        barWindow: root.barWindow
        targetItem: root
        isHovered: root.isHovered
    }

    function updateTime() {
        var now = new Date();
        var hours = now.getHours();
        var minutes = now.getMinutes();
        var seconds = now.getSeconds();
        var ampm = hours >= 12 ? "PM" : "AM";
        hours = hours % 12;
        hours = hours ? hours : 12;
        var hStr = hours < 10 ? "0" + hours : hours;
        var mStr = minutes < 10 ? "0" + minutes : minutes;
        var sStr = seconds < 10 ? "0" + seconds : seconds;

        root.timeStr = hStr + ":" + mStr + " " + ampm;

        var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        root.dateStr = days[now.getDay()] + ", " + now.getDate() + " " + months[now.getMonth()] + " " + now.getFullYear();
    }

    Component.onCompleted: updateTime()

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.updateTime()
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.showDate ? "󰃭" : ""
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.accent
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.showDate ? root.dateStr : root.timeStr
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.text
        }
    }

    Process {
        id: ctlProc
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: mouse => {
            if (mouse.button === Qt.LeftButton) {
                root.showDate = !root.showDate;
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["kitty", "--class", "calendar-floating", "-T", "Calendar", "-e", "bash", "-c", "cal -3; read -n 1 -s -r -p 'Press any key to close...'"]);
            }
        }
    }
}
