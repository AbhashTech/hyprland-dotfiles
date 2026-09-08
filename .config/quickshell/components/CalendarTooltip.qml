import QtQuick
import Quickshell
import ".."

PopupWindow {
    id: calPop

    property var barWindow: null
    property var targetItem: parent
    property bool isHovered: false
    property int showDelay: 200
    property int hideDelay: 150

    anchor.window: calPop.barWindow
    anchor.item: calPop.targetItem
    anchor.edges: Edges.Bottom
    anchor.gravity: Edges.Bottom
    anchor.margins.top: 8

    implicitWidth: calCard.implicitWidth
    implicitHeight: calCard.implicitHeight

    color: "transparent"
    visible: calCard.opacity > 0

    Timer {
        id: showTimer
        interval: calPop.showDelay
        repeat: false
        onTriggered: {
            if (calPop.isHovered || popMa.containsMouse) {
                calCard.opacity = 1;
            }
        }
    }

    Timer {
        id: hideTimer
        interval: calPop.hideDelay
        repeat: false
        onTriggered: {
            if (!calPop.isHovered && !popMa.containsMouse) {
                calCard.opacity = 0;
                // Reset calendar view to current month when closed
                calCard.resetToday();
            }
        }
    }

    onIsHoveredChanged: {
        if (isHovered) {
            hideTimer.stop();
            showTimer.start();
        } else {
            showTimer.stop();
            hideTimer.start();
        }
    }

    Rectangle {
        id: calCard
        radius: 14
        color: Theme.tooltipBg
        border.color: Theme.tooltipBorder
        border.width: 1

        opacity: 0
        Behavior on opacity {
            NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
        }

        implicitWidth: 350
        implicitHeight: mainCol.implicitHeight + 28

        property var now: new Date()
        property int viewYear: now.getFullYear()
        property int viewMonth: now.getMonth() // 0 - 11

        property string liveTimeStr: ""
        property string liveDateStr: ""

        readonly property var monthNames: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        readonly property var dayNames: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

        function updateClock() {
            var d = new Date();
            calCard.now = d;
            var h = d.getHours();
            var m = d.getMinutes();
            var s = d.getSeconds();
            var ampm = h >= 12 ? "PM" : "AM";
            h = h % 12;
            h = h ? h : 12;
            var hStr = h < 10 ? "0" + h : h;
            var mStr = m < 10 ? "0" + m : m;
            var sStr = s < 10 ? "0" + s : s;
            calCard.liveTimeStr = hStr + ":" + mStr + ":" + sStr + " " + ampm;

            var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
            calCard.liveDateStr = days[d.getDay()] + ", " + calCard.monthNames[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
        }

        Component.onCompleted: updateClock()

        Timer {
            interval: 1000
            running: calPop.visible && calCard.opacity > 0
            repeat: true
            onTriggered: calCard.updateClock()
        }

        function prevMonth() {
            if (viewMonth === 0) {
                viewMonth = 11;
                viewYear--;
            } else {
                viewMonth--;
            }
        }

        function nextMonth() {
            if (viewMonth === 11) {
                viewMonth = 0;
                viewYear++;
            } else {
                viewMonth++;
            }
        }

        function resetToday() {
            var d = new Date();
            viewYear = d.getFullYear();
            viewMonth = d.getMonth();
        }

        function getDaysArray(year, month) {
            var firstDay = new Date(year, month, 1).getDay(); // 0 = Sun
            var totalDays = new Date(year, month + 1, 0).getDate();
            var prevMonthTotalDays = new Date(year, month, 0).getDate();
            var curDate = calCard.now.getDate();
            var curMonth = calCard.now.getMonth();
            var curYear = calCard.now.getFullYear();

            var days = [];
            // Previous month trailing days
            for (var i = firstDay - 1; i >= 0; i--) {
                days.push({
                    day: prevMonthTotalDays - i,
                    isCurrentMonth: false,
                    isToday: false
                });
            }
            // Current month days
            for (var d = 1; d <= totalDays; d++) {
                var isToday = (d === curDate && month === curMonth && year === curYear);
                days.push({
                    day: d,
                    isCurrentMonth: true,
                    isToday: isToday
                });
            }
            // Next month leading days to complete grid (42 cells = 6 rows)
            var remaining = 42 - days.length;
            for (var n = 1; n <= remaining; n++) {
                days.push({
                    day: n,
                    isCurrentMonth: false,
                    isToday: false
                });
            }
            return days;
        }

        MouseArea {
            id: popMa
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            onContainsMouseChanged: {
                if (!containsMouse && !calPop.isHovered) {
                    hideTimer.start();
                }
            }
        }

        Column {
            id: mainCol
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 14
            width: calCard.width - 28
            spacing: 11

            // Header: Live Clock and Date
            Column {
                width: parent.width
                spacing: 3

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: calCard.liveTimeStr
                    font.family: Theme.fontFamily
                    font.pixelSize: 20
                    font.bold: true
                    color: Theme.accent
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: calCard.liveDateStr
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                }
            }

            // Divider
            Rectangle {
                width: parent.width
                height: 1
                color: Theme.surface1
            }

            // Month Navigation Row
            Row {
                width: parent.width

                Rectangle {
                    width: 32
                    height: 30
                    radius: 6
                    color: prevMa.containsMouse ? Theme.moduleActiveBg : "transparent"
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        anchors.centerIn: parent
                        text: "󰅁"
                        font.family: Theme.fontFamily
                        font.pixelSize: 18
                        font.bold: true
                        color: prevMa.containsMouse ? Theme.accent : Theme.subtext0
                    }

                    MouseArea {
                        id: prevMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: calCard.prevMonth()
                    }
                }

                Item {
                    width: parent.width - 64
                    height: 30
                    anchors.verticalCenter: parent.verticalCenter

                    Row {
                        anchors.centerIn: parent
                        spacing: 8

                        Text {
                            text: calCard.monthNames[calCard.viewMonth] + " " + calCard.viewYear
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeLarge
                            font.bold: true
                            color: (calCard.viewMonth === calCard.now.getMonth() && calCard.viewYear === calCard.now.getFullYear()) ? Theme.text : Theme.accent
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        // Return to today button if viewing another month
                        Rectangle {
                            visible: !(calCard.viewMonth === calCard.now.getMonth() && calCard.viewYear === calCard.now.getFullYear())
                            radius: 4
                            color: todayMa.containsMouse ? Theme.accent : Theme.surface0
                            border.color: Theme.surface2
                            border.width: 1
                            implicitWidth: todayTxt.implicitWidth + 10
                            implicitHeight: 20
                            anchors.verticalCenter: parent.verticalCenter

                            Text {
                                id: todayTxt
                                anchors.centerIn: parent
                                text: "Today"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: true
                                color: todayMa.containsMouse ? Theme.crust : Theme.text
                            }

                            MouseArea {
                                id: todayMa
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: calCard.resetToday()
                            }
                        }
                    }
                }

                Rectangle {
                    width: 32
                    height: 30
                    radius: 6
                    color: nextMa.containsMouse ? Theme.moduleActiveBg : "transparent"
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        anchors.centerIn: parent
                        text: "󰅂"
                        font.family: Theme.fontFamily
                        font.pixelSize: 18
                        font.bold: true
                        color: nextMa.containsMouse ? Theme.accent : Theme.subtext0
                    }

                    MouseArea {
                        id: nextMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: calCard.nextMonth()
                    }
                }
            }

            // Weekday Headers
            Grid {
                columns: 7
                columnSpacing: 4
                rowSpacing: 4
                anchors.horizontalCenter: parent.horizontalCenter

                Repeater {
                    model: calCard.dayNames

                    Item {
                        width: 38
                        height: 24

                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: Theme.blue
                        }
                    }
                }
            }

            // Days Grid
            Grid {
                columns: 7
                columnSpacing: 4
                rowSpacing: 4
                anchors.horizontalCenter: parent.horizontalCenter

                Repeater {
                    model: calCard.getDaysArray(calCard.viewYear, calCard.viewMonth)

                    Rectangle {
                        id: dayCell
                        width: 38
                        height: 28
                        radius: 6

                        color: modelData.isToday ? Theme.accent : (dayMa.containsMouse ? Theme.moduleActiveBg : "transparent")
                        border.color: modelData.isToday ? Theme.accent : (dayMa.containsMouse ? Theme.surface2 : "transparent")
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: modelData.day.toString()
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: modelData.isToday || (modelData.isCurrentMonth && dayMa.containsMouse)
                            color: modelData.isToday ? Theme.crust : (modelData.isCurrentMonth ? Theme.text : Theme.overlay0)
                        }

                        MouseArea {
                            id: dayMa
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                        }
                    }
                }
            }

            // Divider
            Rectangle {
                width: parent.width
                height: 1
                color: Theme.surface1
            }

            // Shortcuts footer
            Column {
                width: parent.width
                spacing: 5

                Row {
                    width: parent.width
                    spacing: 6

                    Text {
                        text: "Left-Click"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        font.bold: true
                        color: Theme.subtext0
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "• Toggle Date / Time format"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        color: Theme.overlay1
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Row {
                    width: parent.width
                    spacing: 6

                    Text {
                        text: "Right-Click"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        font.bold: true
                        color: Theme.subtext0
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "• Open terminal calendar (cal -3)"
                        font.family: Theme.fontFamily
                        font.pixelSize: 11
                        color: Theme.overlay1
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }
}
