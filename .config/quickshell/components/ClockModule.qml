import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null
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
        isHovered: root.isHovered && !BarConfig.isDragging
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

    function scheduleNextMinute() {
        var now = new Date();
        var msToNextMinute = (60 - now.getSeconds()) * 1000 - now.getMilliseconds() + 50;
        if (msToNextMinute < 500) msToNextMinute = 60000;
        timer.interval = msToNextMinute;
        timer.restart();
    }

    Component.onCompleted: {
        updateTime();
        scheduleNextMinute();
    }

    Timer {
        id: timer
        interval: 60000
        running: root.visible
        repeat: false
        onTriggered: {
            root.updateTime();
            root.scheduleNextMinute();
        }
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
        cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        property real pressX: 0
        property real pressY: 0
        property bool didDrag: false

        onPressed: mouse => {
            pressX = mouse.x;
            pressY = mouse.y;
            didDrag = false;
        }

        onPositionChanged: mouse => {
            if (pressed && mouse.buttons === Qt.LeftButton) {
                var dx = mouse.x - pressX;
                var dy = mouse.y - pressY;
                if (!didDrag && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
                    didDrag = true;
                    BarConfig.startDrag("clock", root.barSection, root.barIndex);
                }
                if (didDrag && root.barContainer) {
                    var pt = mapToItem(root.barContainer, mouse.x, mouse.y);
                    BarConfig.updateDragPos(pt.x, root.barContainer.width);
                }
            }
        }

        onReleased: mouse => {
            if (didDrag) {
                BarConfig.endDrag();
                didDrag = false;
            } else if (mouse.button === Qt.LeftButton) {
                root.showDate = !root.showDate;
            } else if (mouse.button === Qt.RightButton) {
                ctlProc.exec(["kitty", "--class", "calendar-floating", "-T", "Calendar", "-e", "bash", "-c", "cal -3; read -n 1 -s -r -p 'Press any key to close...'"]);
            }
        }
    }
}
