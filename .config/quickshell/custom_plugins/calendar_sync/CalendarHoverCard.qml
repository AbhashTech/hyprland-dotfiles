import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.." // Theme
import "."

PopupWindow {
    id: calPop

    property var barWindow: null
    property var targetItem: parent
    property string barSection: "right"
    property bool isHovered: false
    property bool is24Hour: false
    property int showDelay: 200
    property int hideDelay: 300

    anchor.window: calPop.barWindow
    anchor.edges: (barSection === "right") ? (Edges.Bottom | Edges.Right) : (barSection === "left" ? (Edges.Bottom | Edges.Left) : Edges.Bottom)
    anchor.gravity: (barSection === "right") ? (Edges.Bottom | Edges.Left) : (barSection === "left" ? (Edges.Bottom | Edges.Right) : Edges.Bottom)
    anchor.margins.top: 8

    function updateAnchorRect() {
        if (!calPop.targetItem || !calPop.barWindow) return;
        var pt = calPop.targetItem.mapToItem(null, 0, 0);
        calPop.anchor.rect.x = Math.round(pt.x);
        calPop.anchor.rect.y = Math.round(pt.y);
        calPop.anchor.rect.width = Math.round(calPop.targetItem.width);
        calPop.anchor.rect.height = Math.round(calPop.targetItem.height);
    }

    onBarWindowChanged: updateAnchorRect()
    onTargetItemChanged: updateAnchorRect()

    Connections {
        target: calPop.targetItem
        function onXChanged() { calPop.updateAnchorRect(); }
        function onYChanged() { calPop.updateAnchorRect(); }
        function onWidthChanged() { calPop.updateAnchorRect(); }
    }

    Connections {
        target: BarConfig
        function onIsDraggingChanged() {
            if (BarConfig.isDragging) {
                calCard.opacity = 0;
                showTimer.stop();
                hideTimer.stop();
                if (manageModal) manageModal.isOpen = false;
            }
        }
    }

    implicitWidth: calCard.implicitWidth
    implicitHeight: calCard.implicitHeight

    color: "transparent"
    visible: calCard.opacity > 0

    readonly property bool cardHovered: cardHover.hovered || cardMa.containsMouse || (manageModal && manageModal.isOpen)
    readonly property bool shouldBeOpen: ((calPop.isHovered || cardHovered) && !BarConfig.isDragging) || (manageModal && manageModal.isOpen && !BarConfig.isDragging)

    onVisibleChanged: {
        if (visible) {
            updateAnchorRect();
            calCard.updateClock();
            CalendarSyncService.queryEvents();
        }
    }

    onIsHoveredChanged: {
        if (isHovered) {
            updateAnchorRect();
            calCard.updateClock();
            CalendarSyncService.queryEvents();
        }
    }

    onIs24HourChanged: {
        calCard.updateClock();
    }

    Timer {
        id: showTimer
        interval: calPop.showDelay
        repeat: false
        onTriggered: {
            if (calPop.shouldBeOpen) {
                updateAnchorRect();
                calCard.updateClock();
                CalendarSyncService.queryEvents();
                calCard.opacity = 1;
            }
        }
    }

    Timer {
        id: hideTimer
        interval: calPop.hideDelay
        repeat: false
        onTriggered: {
            if (!calPop.shouldBeOpen) {
                calCard.opacity = 0;
                calCard.resetToday();
            }
        }
    }

    onShouldBeOpenChanged: {
        if (shouldBeOpen) {
            updateAnchorRect();
            hideTimer.stop();
            calCard.updateClock();
            if (calCard.opacity > 0) {
                calCard.opacity = 1;
            } else {
                showTimer.restart();
            }
        } else {
            showTimer.stop();
            hideTimer.restart();
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

        implicitWidth: 640
        implicitHeight: mainCol.implicitHeight + 28

        property var now: new Date()
        property int viewYear: now.getFullYear()
        property int viewMonth: now.getMonth() // 0 - 11
        property string selectedDateStr: ""

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
            var mStr = m < 10 ? "0" + m : m;
            var sStr = s < 10 ? "0" + s : s;

            if (calPop.is24Hour) {
                var h24Str = h < 10 ? "0" + h : h;
                calCard.liveTimeStr = h24Str + ":" + mStr + ":" + sStr;
            } else {
                var ampm = h >= 12 ? "PM" : "AM";
                h = h % 12;
                h = h ? h : 12;
                var hStr = h < 10 ? "0" + h : h;
                calCard.liveTimeStr = hStr + ":" + mStr + ":" + sStr + " " + ampm;
            }

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
            calCard.now = d;
            viewYear = d.getFullYear();
            viewMonth = d.getMonth();
        }

        function getDaysArray(year, month) {
            var firstDay = new Date(year, month, 1).getDay();
            var totalDays = new Date(year, month + 1, 0).getDate();
            var prevMonthTotalDays = new Date(year, month, 0).getDate();
            var curDate = calCard.now.getDate();
            var curMonth = calCard.now.getMonth();
            var curYear = calCard.now.getFullYear();

            var days = [];
            // Previous month trailing days
            for (var i = firstDay - 1; i >= 0; i--) {
                var pDay = prevMonthTotalDays - i;
                var pMonth = month === 0 ? 11 : month - 1;
                var pYear = month === 0 ? year - 1 : year;
                var pDateStr = pYear + "-" + (pMonth < 9 ? "0" + (pMonth + 1) : (pMonth + 1)) + "-" + (pDay < 10 ? "0" + pDay : pDay);
                days.push({
                    day: pDay,
                    dateStr: pDateStr,
                    isCurrentMonth: false,
                    isToday: false,
                    eventCount: CalendarSyncService.getEventCountForDate(pDateStr)
                });
            }
            // Current month days
            for (var d = 1; d <= totalDays; d++) {
                var isToday = (d === curDate && month === curMonth && year === curYear);
                var cDateStr = year + "-" + (month < 9 ? "0" + (month + 1) : (month + 1)) + "-" + (d < 10 ? "0" + d : d);
                days.push({
                    day: d,
                    dateStr: cDateStr,
                    isCurrentMonth: true,
                    isToday: isToday,
                    eventCount: CalendarSyncService.getEventCountForDate(cDateStr)
                });
            }
            // Next month leading days to complete grid (42 cells = 6 rows)
            var remaining = 42 - days.length;
            for (var n = 1; n <= remaining; n++) {
                var nMonth = month === 11 ? 0 : month + 1;
                var nYear = month === 11 ? year + 1 : year;
                var nDateStr = nYear + "-" + (nMonth < 9 ? "0" + (nMonth + 1) : (nMonth + 1)) + "-" + (n < 10 ? "0" + n : n);
                days.push({
                    day: n,
                    dateStr: nDateStr,
                    isCurrentMonth: false,
                    isToday: false,
                    eventCount: CalendarSyncService.getEventCountForDate(nDateStr)
                });
            }
            return days;
        }

        HoverHandler {
            id: cardHover
        }

        MouseArea {
            id: cardMa
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onPressed: mouse => mouse.accepted = true
            onReleased: mouse => mouse.accepted = true
            onClicked: mouse => mouse.accepted = true
        }

        Column {
            id: mainCol
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 14
            width: calCard.width - 28
            spacing: 12

            // Top Header: Live Time, Date & Manage / Sync Buttons
            RowLayout {
                width: parent.width

                ColumnLayout {
                    spacing: 2
                    Layout.alignment: Qt.AlignVCenter

                    Text {
                        text: calCard.liveTimeStr
                        font.family: Theme.fontFamily
                        font.pixelSize: 20
                        font.bold: true
                        color: Theme.accent
                    }
                    Text {
                        text: calCard.liveDateStr
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        color: Theme.text
                    }
                }

                Item {
                    Layout.fillWidth: true
                    height: 1
                }

                RowLayout {
                    spacing: 8
                    Layout.alignment: Qt.AlignVCenter

                    // Sync button
                    Rectangle {
                        width: 32
                        height: 30
                        radius: 6
                        color: syncMa.containsMouse ? Theme.moduleActiveBg : Theme.surface0
                        border.color: Theme.surface2
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: ""
                            font.family: Theme.fontFamily
                            font.pixelSize: 14
                            color: CalendarSyncService.isSyncing ? Theme.accent : (syncMa.containsMouse ? Theme.accent : Theme.subtext0)
                        }

                        MouseArea {
                            id: syncMa
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: CalendarSyncService.syncNow()
                        }
                    }

                    // Manage Sources button
                    Rectangle {
                        height: 30
                        radius: 6
                        color: manageMa.containsMouse ? Theme.accent : Theme.surface0
                        border.color: manageMa.containsMouse ? Theme.accent : Theme.surface2
                        border.width: 1
                        implicitWidth: manageRow.implicitWidth + 14

                        Row {
                            id: manageRow
                            anchors.centerIn: parent
                            spacing: 6
                            Text {
                                text: "󰢻"
                                font.family: Theme.fontFamily
                                font.pixelSize: 14
                                color: manageMa.containsMouse ? Theme.crust : Theme.accent
                            }
                            Text {
                                text: "Import / Feeds"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: manageMa.containsMouse ? Theme.crust : Theme.text
                            }
                        }

                        MouseArea {
                            id: manageMa
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                manageModal.isOpen = !manageModal.isOpen;
                            }
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

            // Main Body: 2 Columns (Left: Calendar Grid, Right: Today's & Future Events)
            RowLayout {
                width: parent.width
                spacing: 16

                // LEFT: Calendar Grid
                Column {
                    width: 310
                    spacing: 8

                    // Month Navigation Row
                    RowLayout {
                        width: parent.width

                        Rectangle {
                            width: 28
                            height: 28
                            radius: 6
                            color: prevMa.containsMouse ? Theme.moduleActiveBg : "transparent"
                            Layout.alignment: Qt.AlignVCenter

                            Text {
                                anchors.centerIn: parent
                                text: "󰅁"
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
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
                            Layout.fillWidth: true
                            height: 28

                            Row {
                                anchors.centerIn: parent
                                spacing: 6

                                Text {
                                    text: calCard.monthNames[calCard.viewMonth] + " " + calCard.viewYear
                                    font.family: Theme.fontFamily
                                    font.pixelSize: Theme.fontSize
                                    font.bold: true
                                    color: (calCard.viewMonth === calCard.now.getMonth() && calCard.viewYear === calCard.now.getFullYear()) ? Theme.text : Theme.accent
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Rectangle {
                                    visible: !(calCard.viewMonth === calCard.now.getMonth() && calCard.viewYear === calCard.now.getFullYear())
                                    radius: 4
                                    color: todayMa.containsMouse ? Theme.accent : Theme.surface0
                                    border.color: Theme.surface2
                                    border.width: 1
                                    implicitWidth: todayTxt.implicitWidth + 8
                                    implicitHeight: 18
                                    anchors.verticalCenter: parent.verticalCenter

                                    Text {
                                        id: todayTxt
                                        anchors.centerIn: parent
                                        text: "Today"
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 9
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
                            width: 28
                            height: 28
                            radius: 6
                            color: nextMa.containsMouse ? Theme.moduleActiveBg : "transparent"
                            Layout.alignment: Qt.AlignVCenter

                            Text {
                                anchors.centerIn: parent
                                text: "󰅂"
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
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
                                height: 20
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 10
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

                                readonly property bool isSelected: calCard.selectedDateStr === modelData.dateStr

                                color: modelData.isToday ? Theme.accent : 
                                       (isSelected ? Theme.moduleActiveBg : 
                                       (dayMa.containsMouse ? Theme.surface0 : "transparent"))
                                border.color: modelData.isToday ? Theme.accent : 
                                              (isSelected ? Theme.accent : 
                                              (dayMa.containsMouse ? Theme.surface2 : "transparent"))
                                border.width: 1

                                Column {
                                    anchors.centerIn: parent
                                    spacing: 1

                                    Text {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: modelData.day.toString()
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 11
                                        font.bold: modelData.isToday || isSelected || (modelData.isCurrentMonth && dayMa.containsMouse)
                                        color: modelData.isToday ? Theme.crust : 
                                               (isSelected ? Theme.accent : 
                                               (modelData.isCurrentMonth ? Theme.text : Theme.overlay0))
                                    }

                                    // Event indicator dot
                                    Rectangle {
                                        visible: modelData.eventCount > 0
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        width: 4
                                        height: 4
                                        radius: 2
                                        color: modelData.isToday ? Theme.crust : Theme.green
                                    }
                                }

                                MouseArea {
                                    id: dayMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        calCard.selectedDateStr = modelData.dateStr;
                                        eventsListCol.activeEventTab = "selected";
                                    }
                                }
                            }
                        }
                    }
                }

                // Divider between columns
                Rectangle {
                    width: 1
                    height: 240
                    color: Theme.surface1
                    Layout.alignment: Qt.AlignVCenter
                }

                // RIGHT: Today's and Future Events List
                ColumnLayout {
                    id: eventsListCol
                    property string activeEventTab: "today"
                    Layout.fillWidth: true
                    spacing: 8

                    // Section Tabs / Header
                    RowLayout {
                        id: tabsRow
                        width: parent.width
                        spacing: 6

                        // Selected Date Tab (shows when a date is selected)
                        Rectangle {
                            id: selectedTab
                            visible: Boolean(calCard.selectedDateStr)
                            height: 24
                            radius: 4
                            color: eventsListCol.activeEventTab === "selected" ? Theme.moduleActiveBg : "transparent"
                            border.color: eventsListCol.activeEventTab === "selected" ? Theme.accent : "transparent"
                            border.width: 1
                            implicitWidth: selectedTabTxt.implicitWidth + 12

                            Text {
                                id: selectedTabTxt
                                anchors.centerIn: parent
                                text: {
                                    var count = CalendarSyncService.getEventsListForDate(calCard.selectedDateStr).length;
                                    var parts = calCard.selectedDateStr ? calCard.selectedDateStr.split("-") : [];
                                    var dDisplay = parts.length === 3 ? (parts[1] + "/" + parts[2]) : "Selected";
                                    return dDisplay + " (" + count + ")";
                                }
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: eventsListCol.activeEventTab === "selected" ? Theme.accent : Theme.subtext0
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: eventsListCol.activeEventTab = "selected"
                            }
                        }

                        Rectangle {
                            id: todayTab
                            height: 24
                            radius: 4
                            color: eventsListCol.activeEventTab === "today" ? Theme.moduleActiveBg : "transparent"
                            border.color: eventsListCol.activeEventTab === "today" ? Theme.accent : "transparent"
                            border.width: 1
                            implicitWidth: todayTabTxt.implicitWidth + 12

                            Text {
                                id: todayTabTxt
                                anchors.centerIn: parent
                                text: "Today (" + (CalendarSyncService.eventsData.today_events ? CalendarSyncService.eventsData.today_events.length : 0) + ")"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: eventsListCol.activeEventTab === "today" ? Theme.accent : Theme.subtext0
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: eventsListCol.activeEventTab = "today"
                            }
                        }

                        Rectangle {
                            id: futureTab
                            height: 24
                            radius: 4
                            color: eventsListCol.activeEventTab === "future" ? Theme.moduleActiveBg : "transparent"
                            border.color: eventsListCol.activeEventTab === "future" ? Theme.accent : "transparent"
                            border.width: 1
                            implicitWidth: futureTabTxt.implicitWidth + 12

                            Text {
                                id: futureTabTxt
                                anchors.centerIn: parent
                                text: "Upcoming (" + (CalendarSyncService.eventsData.future_events ? CalendarSyncService.eventsData.future_events.length : 0) + ")"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                font.bold: true
                                color: eventsListCol.activeEventTab === "future" ? Theme.accent : Theme.subtext0
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: eventsListCol.activeEventTab = "future"
                            }
                        }
                    }

                    // Events Scroll List
                    ScrollView {
                        Layout.fillWidth: true
                        height: 200
                        clip: true

                        ListView {
                            width: parent.width
                            spacing: 6
                            model: (eventsListCol.activeEventTab === "selected") ?
                                   CalendarSyncService.getEventsListForDate(calCard.selectedDateStr) :
                                   ((eventsListCol.activeEventTab === "today") ? 
                                    (CalendarSyncService.eventsData.today_events || []) : 
                                    (CalendarSyncService.eventsData.future_events || []))

                            // Empty State
                            Text {
                                visible: parent.count === 0
                                anchors.centerIn: parent
                                text: eventsListCol.activeEventTab === "selected" ? 
                                      ("No events on " + (calCard.selectedDateStr || "this date")) :
                                      (eventsListCol.activeEventTab === "today" ? "No events scheduled for today" : "No upcoming events")
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: Theme.overlay0
                            }

                            delegate: Rectangle {
                                width: parent ? parent.width : 260
                                implicitHeight: evCol.implicitHeight + 14
                                radius: 8
                                color: evMa.containsMouse ? Theme.surface0 : Theme.mantle
                                border.color: evMa.containsMouse ? Theme.surface2 : Theme.surface1
                                border.width: 1

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 7
                                    spacing: 8

                                    // Color stripe / indicator
                                    Rectangle {
                                        width: 3
                                        Layout.fillHeight: true
                                        radius: 1.5
                                        color: modelData.color || Theme.accent
                                    }

                                    ColumnLayout {
                                        id: evCol
                                        Layout.fillWidth: true
                                        spacing: 2

                                        // Time & Date
                                        RowLayout {
                                            width: parent.width
                                            spacing: 6

                                            Text {
                                                text: modelData.timeStr || "All Day"
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 10
                                                font.bold: true
                                                color: Theme.accent
                                            }

                                            Text {
                                                visible: eventsListCol.activeEventTab === "future" && Boolean(modelData.dateLabel)
                                                text: "• " + (modelData.dateLabel || "")
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 10
                                                color: Theme.subtext0
                                            }

                                            Item {
                                                Layout.fillWidth: true
                                                height: 1
                                            }

                                            Text {
                                                visible: eventsListCol.activeEventTab === "future" && modelData.daysUntil !== undefined
                                                text: modelData.daysUntil === 1 ? "Tomorrow" : ("in " + modelData.daysUntil + "d")
                                                font.family: Theme.fontFamily
                                                font.pixelSize: 9
                                                color: Theme.overlay1
                                            }
                                        }

                                        // Summary / Title
                                        Text {
                                            text: modelData.summary || "Event"
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 11
                                            font.bold: true
                                            color: Theme.text
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }

                                        // Location / Description
                                        Text {
                                            visible: Boolean(modelData.location)
                                            text: " " + (modelData.location || "")
                                            font.family: Theme.fontFamily
                                            font.pixelSize: 9
                                            color: Theme.overlay0
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                MouseArea {
                                    id: evMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }
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
            RowLayout {
                width: parent.width
                spacing: 16

                Text {
                    text: "Left-Click: Toggle Date/Time"
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: Theme.overlay1
                }
                Text {
                    text: "Right-Click: Toggle 12h/24h"
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: Theme.overlay1
                }
                Item {
                    Layout.fillWidth: true
                    height: 1
                }
                Text {
                    text: CalendarSyncService.lastSyncTime ? ("Synced: " + CalendarSyncService.lastSyncTime) : "Ready"
                    font.family: Theme.fontFamily
                    font.pixelSize: 10
                    color: Theme.overlay0
                }
            }
        }

        // In-card modal for managing calendar feeds & .ics files
        CalendarManageModal {
            id: manageModal
            anchors.fill: parent
            anchors.margins: 4
            isOpen: false
            z: 99
            onClosed: {
                isOpen = false;
            }
        }
    }
}
