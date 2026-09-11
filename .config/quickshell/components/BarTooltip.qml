import QtQuick
import Quickshell
import ".."

PopupWindow {
    id: tooltipPop

    property var barWindow: null
    property var targetItem: parent
    property bool isHovered: false
    property string title: ""
    property string description: ""
    property string icon: ""
    property color iconColor: Theme.accent
    property var shortcuts: [] // Array of { action: "...", key: "..." }
    property var details: [] // Array of { label: "...", value: "...", icon?: "...", iconColor?: "...", valueColor?: "..." }
    property int showDelay: 200
    property int hideDelay: 100

    anchor.window: tooltipPop.barWindow
    anchor.item: tooltipPop.targetItem
    anchor.edges: Edges.Bottom
    anchor.gravity: Edges.Bottom
    anchor.margins.top: 8

    implicitWidth: tooltipContainer.implicitWidth
    implicitHeight: tooltipContainer.implicitHeight

    color: "transparent"
    visible: tooltipContainer.opacity > 0

    Timer {
        id: showTimer
        interval: tooltipPop.showDelay
        repeat: false
        onTriggered: {
            if (tooltipPop.isHovered || popMa.containsMouse) {
                tooltipContainer.opacity = 1;
            }
        }
    }

    Timer {
        id: hideTimer
        interval: tooltipPop.hideDelay
        repeat: false
        onTriggered: {
            if (!tooltipPop.isHovered && !popMa.containsMouse) {
                tooltipContainer.opacity = 0;
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
        id: tooltipContainer
        radius: 12
        color: Theme.tooltipBg
        border.color: Theme.tooltipBorder
        border.width: 1

        opacity: 0
        Behavior on opacity {
            NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
        }

        // Dynamic width calculation with comfortable minimum & padding
        readonly property int calculatedWidth: {
            var w = 220;
            if (headerRow.implicitWidth > w) w = headerRow.implicitWidth;
            if (descText.implicitWidth > w) w = descText.implicitWidth;
            if (detailsCol.implicitWidth > w) w = detailsCol.implicitWidth;
            if (shortcutsCol.implicitWidth > w) w = shortcutsCol.implicitWidth;
            return Math.min(Math.max(w + 36, 260), 480);
        }

        implicitWidth: calculatedWidth
        implicitHeight: contentCol.implicitHeight + 24

        MouseArea {
            id: popMa
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            onContainsMouseChanged: {
                if (!containsMouse && !tooltipPop.isHovered) {
                    hideTimer.start();
                }
            }
        }

        Column {
            id: contentCol
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 12
            spacing: 8
            width: tooltipContainer.width - 24

            // Header: Icon + Title
            Row {
                id: headerRow
                spacing: 8
                width: parent.width

                Text {
                    visible: tooltipPop.icon !== ""
                    text: tooltipPop.icon
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSizeLarge + 1
                    font.bold: true
                    color: tooltipPop.iconColor
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: tooltipPop.title
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.text
                    elide: Text.ElideRight
                    width: tooltipPop.icon !== "" ? parent.width - 30 : parent.width
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Description
            Text {
                id: descText
                visible: tooltipPop.description !== ""
                text: tooltipPop.description
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.subtext0
                wrapMode: Text.WordWrap
                width: parent.width
            }

            // Divider if details exist
            Rectangle {
                visible: tooltipPop.details && tooltipPop.details.length > 0
                width: parent.width
                height: 1
                color: Theme.surface1
            }

            // Structured details list
            Column {
                id: detailsCol
                visible: tooltipPop.details && tooltipPop.details.length > 0
                spacing: 5
                width: parent.width

                Repeater {
                    model: tooltipPop.details

                    Item {
                        width: detailsCol.width
                        implicitWidth: leftRow.implicitWidth + valLabel.implicitWidth + 24
                        implicitHeight: Math.max(leftRow.implicitHeight, valLabel.implicitHeight)

                        Row {
                            id: leftRow
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 6

                            Text {
                                visible: modelData.icon !== undefined && modelData.icon !== ""
                                text: modelData.icon || ""
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: modelData.iconColor !== undefined ? modelData.iconColor : Theme.subtext0
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: modelData.label || ""
                                font.family: Theme.fontFamily
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.subtext0
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        Text {
                            id: valLabel
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.value || ""
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            font.bold: true
                            color: modelData.valueColor !== undefined ? modelData.valueColor : Theme.text
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            width: Math.min(implicitWidth, parent.width - leftRow.implicitWidth - 12)
                        }
                    }
                }
            }

            // Divider if shortcuts exist
            Rectangle {
                visible: tooltipPop.shortcuts && tooltipPop.shortcuts.length > 0
                width: parent.width
                height: 1
                color: Theme.surface1
            }

            // Shortcuts list
            Column {
                id: shortcutsCol
                visible: tooltipPop.shortcuts && tooltipPop.shortcuts.length > 0
                spacing: 7
                width: parent.width

                Repeater {
                    model: tooltipPop.shortcuts

                    Item {
                        width: shortcutsCol.width
                        implicitWidth: actLabel.implicitWidth + keyRow.implicitWidth + 24
                        implicitHeight: Math.max(actLabel.implicitHeight, keyRow.implicitHeight)

                        Text {
                            id: actLabel
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.action
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.subtext0
                        }

                        Row {
                            id: keyRow
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 4

                            Repeater {
                                model: modelData.key ? modelData.key.split(" + ") : []

                                Rectangle {
                                    radius: 4
                                    color: Theme.surface0
                                    border.color: Theme.surface2
                                    border.width: 1
                                    implicitWidth: keyLabel.implicitWidth + 10
                                    implicitHeight: keyLabel.implicitHeight + 6

                                    Text {
                                        id: keyLabel
                                        anchors.centerIn: parent
                                        text: modelData
                                        font.family: Theme.fontFamily
                                        font.pixelSize: Theme.fontSizeSmall - 1
                                        font.bold: true
                                        color: Theme.accent
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
