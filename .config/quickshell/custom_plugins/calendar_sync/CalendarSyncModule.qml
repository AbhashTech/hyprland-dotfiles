import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.." // Theme
import "."

Rectangle {
    id: root

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null
    property bool showDate: false
    property bool is24Hour: false
    property string timeStr: ""
    property string dateStr: ""

    implicitHeight: Theme.barHeight - 8
    implicitWidth: row.implicitWidth + 14
    radius: Theme.capsuleRadius

    readonly property bool isHovered: mouseArea.containsMouse
    color: isHovered ? Theme.moduleHoverBg : Theme.moduleBg
    border.color: isHovered ? Theme.moduleHoverBorder : Theme.moduleBorder
    border.width: 1

    property alias hoverCard: hoverCard

    CalendarHoverCard {
        id: hoverCard
        barWindow: root.barWindow
        targetItem: root
        barSection: root.barSection
        isHovered: root.isHovered && !BarConfig.isDragging
        is24Hour: root.is24Hour
    }

    function updateTime() {
        var now = new Date();
        var hours = now.getHours();
        var minutes = now.getMinutes();
        var seconds = now.getSeconds();
        var mStr = minutes < 10 ? "0" + minutes : minutes;
        var sStr = seconds < 10 ? "0" + seconds : seconds;

        if (root.is24Hour) {
            var h24Str = hours < 10 ? "0" + hours : hours;
            root.timeStr = h24Str + ":" + mStr;
        } else {
            var ampm = hours >= 12 ? "PM" : "AM";
            hours = hours % 12;
            hours = hours ? hours : 12;
            var hStr = hours < 10 ? "0" + hours : hours;
            root.timeStr = hStr + ":" + mStr + " " + ampm;
        }

        var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        root.dateStr = days[now.getDay()] + ", " + now.getDate() + " " + months[now.getMonth()] + " " + now.getFullYear();
    }

    Component.onCompleted: {
        updateTime();
    }

    onVisibleChanged: {
        if (visible) updateTime();
    }

    Timer {
        id: timer
        interval: 1000
        running: root.visible
        repeat: true
        onTriggered: {
            root.updateTime();
        }
    }

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 5

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

        // Event indicator dot on topbar capsule if there are events today
        Rectangle {
            visible: (CalendarSyncService.eventsData.today_events && CalendarSyncService.eventsData.today_events.length > 0)
            anchors.verticalCenter: parent.verticalCenter
            width: 6
            height: 6
            radius: 3
            color: Theme.green
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
                    var section = root.barSection || BarConfig.getSectionForModule("clock");
                    var idx = (root.barIndex >= 0) ? root.barIndex : (section === "left" ? BarConfig.leftModules.indexOf("clock") : (section === "center" ? BarConfig.centerModules.indexOf("clock") : BarConfig.rightModules.indexOf("clock")));
                    BarConfig.startDrag("clock", section, idx);
                }
                if (didDrag) {
                    var container = root.barContainer;
                    if (!container) {
                        var p = root.parent;
                        while (p && !container) {
                            if (p.hasOwnProperty("barContainer") && p.barContainer) container = p.barContainer;
                            p = p.parent;
                        }
                    }
                    if (container) {
                        var pt = mapToItem(container, mouse.x, mouse.y);
                        BarConfig.updateDragPos(pt.x, container.width);
                    }
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
                root.is24Hour = !root.is24Hour;
                root.updateTime();
            }
        }
    }
}
