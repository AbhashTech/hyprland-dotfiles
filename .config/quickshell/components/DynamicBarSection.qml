import QtQuick
import QtQuick.Layouts
import Quickshell
import ".."
import "../generated"

Row {
    id: root

    property var barWindow: null
    property string section: "left" // "left" | "center" | "right"
    readonly property var moduleList: (section === "left") ? BarConfig.leftModules : (section === "center" ? BarConfig.centerModules : BarConfig.rightModules)
    spacing: BarConfig.spacing

    // Empty section placeholder in edit mode
    Rectangle {
        id: emptyPlaceholder
        visible: BarConfig.editMode && root.moduleList.length === 0
        implicitHeight: Theme.barHeight - 10
        implicitWidth: 130
        radius: Theme.capsuleRadius
        color: Theme.moduleBg
        border.color: Theme.mauve
        border.width: 1

        Row {
            anchors.centerIn: parent
            spacing: 6
            Text {
                text: "󰐕"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.mauve
            }
            Text {
                text: section.toUpperCase() + " (Empty)"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: Theme.subtext0
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: {
                if (BarConfig.selectedModule !== "") {
                    BarConfig.moveModule(BarConfig.selectedModule, root.section, -1);
                }
            }
        }
    }

    Repeater {
        id: repeater
        model: root.moduleList

        Item {
            id: moduleWrapper
            required property var modelData
            required property int index

            readonly property string moduleId: modelData
            readonly property var moduleMeta: BarConfig.getModuleMeta(moduleId)
            readonly property bool isSelected: BarConfig.selectedModule === moduleId
            readonly property bool isDragged: BarConfig.draggedModule === moduleId

            implicitWidth: (moduleLoader.item ? moduleLoader.item.implicitWidth : 38) + (BarConfig.editMode ? 32 : 0)
            implicitHeight: Theme.barHeight - 8

            Behavior on implicitWidth { NumberAnimation { duration: 150 } }

            // Normal & Edit container
            Rectangle {
                id: editContainer
                anchors.fill: parent
                radius: Theme.capsuleRadius
                color: BarConfig.editMode ? (isSelected ? Theme.moduleActiveBg : Qt.rgba(Theme.mantle.r, Theme.mantle.g, Theme.mantle.b, 0.6)) : "transparent"
                border.color: BarConfig.editMode ? (isSelected ? Theme.accent : Theme.mauve) : "transparent"
                border.width: BarConfig.editMode ? 1 : 0

                Behavior on border.color { ColorAnimation { duration: 150 } }

                // The Actual Widget
                Loader {
                    id: moduleLoader
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: BarConfig.editMode ? 28 : 0
                    sourceComponent: root.getComponentForId(moduleId)
                    asynchronous: false

                    onLoaded: {
                        if (item && item.hasOwnProperty("barWindow")) {
                            item.barWindow = root.barWindow;
                        }
                    }
                }

                // Edit Overlay & Controls
                Item {
                    id: editControlsOverlay
                    anchors.fill: parent
                    visible: BarConfig.editMode
                    z: 5

                    // Drag & Select Handle on Left
                    Rectangle {
                        id: dragHandle
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 26
                        radius: Theme.capsuleRadius
                        color: dragHandleArea.containsMouse || isSelected ? Theme.mauve : Qt.rgba(Theme.surface0.r, Theme.surface0.g, Theme.surface0.b, 0.7)

                        Behavior on color { ColorAnimation { duration: 150 } }

                        Text {
                            anchors.centerIn: parent
                            text: "󰁝"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: dragHandleArea.containsMouse || isSelected ? "#ffffff" : Theme.subtext0
                        }

                        MouseArea {
                            id: dragHandleArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.SizeAllCursor
                            drag.target: null

                            property real startX: 0

                            onPressed: mouse => {
                                startX = mouse.x;
                                BarConfig.selectedModule = moduleId;
                            }

                            onPositionChanged: mouse => {
                                if (pressed) {
                                    var diff = mouse.x - startX;
                                    if (diff > 40) {
                                        BarConfig.moveStep(moduleId, "right");
                                        startX = mouse.x;
                                    } else if (diff < -40) {
                                        BarConfig.moveStep(moduleId, "left");
                                        startX = mouse.x;
                                    }
                                }
                            }

                            onClicked: {
                                BarConfig.selectedModule = (BarConfig.selectedModule === moduleId) ? "" : moduleId;
                            }
                        }
                    }

                    // Quick Action Menu on Hover / Selected
                    Row {
                        anchors.right: parent.right
                        anchors.rightMargin: 4
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 3
                        visible: moduleWrapperHoverArea.containsMouse || isSelected

                        // Move Left Button
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: leftBtnArea.containsMouse ? Theme.blue : Qt.rgba(0, 0, 0, 0.6)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅁"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: leftBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: BarConfig.moveStep(moduleId, "left")
                            }
                        }

                        // Move Right Button
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: rightBtnArea.containsMouse ? Theme.blue : Qt.rgba(0, 0, 0, 0.6)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅂"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: rightBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: BarConfig.moveStep(moduleId, "right")
                            }
                        }

                        // Cycle Section Button (Left -> Center -> Right -> Left)
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: secBtnArea.containsMouse ? Theme.teal : Qt.rgba(0, 0, 0, 0.6)
                            Text {
                                anchors.centerIn: parent
                                text: root.section === "left" ? "C" : (root.section === "center" ? "R" : "L")
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
                                font.bold: true
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: secBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var nextSec = root.section === "left" ? "center" : (root.section === "center" ? "right" : "left");
                                    BarConfig.moveModule(moduleId, nextSec, -1);
                                }
                            }
                        }

                        // Hide / Remove from Bar Button
                        Rectangle {
                            width: 20
                            height: 20
                            radius: 10
                            color: hideBtnArea.containsMouse ? Theme.red : Qt.rgba(0, 0, 0, 0.6)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅙"
                                font.family: Theme.fontFamily
                                font.pixelSize: 11
                                color: "#ffffff"
                            }
                            MouseArea {
                                id: hideBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: BarConfig.toggleVisibility(moduleId)
                            }
                        }
                    }

                    MouseArea {
                        id: moduleWrapperHoverArea
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: mouse => {
                            if (mouse.button === Qt.LeftButton) {
                                BarConfig.selectedModule = (BarConfig.selectedModule === moduleId) ? "" : moduleId;
                            }
                        }
                    }
                }
            }
        }
    }

    // Component Registry Resolver
    function getComponentForId(id) {
        switch (id) {
            case "launcher":
                return launcherComp;
            case "workspaces":
                return workspacesComp;
            case "activewindow":
                return activeWindowComp;
            case "mpris":
                return mprisComp;
            case "language":
                return languageComp;
            case "recording":
                return recordingComp;
            case "traynotif":
                return trayNotifComp;
            case "status":
                return statusGroupComp;
            case "stats":
                return statsComp;
            case "power":
                return powerComp;
            case "clock":
                return clockComp;
            case "custom_left":
                return customLeftComp;
            case "custom_center":
                return customCenterComp;
            case "custom_right":
                return customRightComp;
            default:
                if (id && id.startsWith("plugin_")) {
                    return customCenterComp;
                }
                return null;
        }
    }

    Component { id: launcherComp; LauncherButton { barWindow: root.barWindow } }
    Component { id: workspacesComp; Workspaces { barWindow: root.barWindow } }
    Component { id: activeWindowComp; ActiveWindow { barWindow: root.barWindow } }
    Component { id: mprisComp; MprisModule { barWindow: root.barWindow } }
    Component { id: languageComp; LanguageModule { barWindow: root.barWindow } }
    Component { id: recordingComp; RecordingModule { barWindow: root.barWindow } }
    Component { id: trayNotifComp; TrayNotifGroup { barWindow: root.barWindow } }
    Component {
        id: statusGroupComp
        StatusGroup {
            barWindow: root.barWindow
            screenName: (root.barWindow && root.barWindow.screen && root.barWindow.screen.name) ? root.barWindow.screen.name : ""
        }
    }
    Component { id: statsComp; StatsModule { barWindow: root.barWindow } }
    Component { id: powerComp; PowerModule { barWindow: root.barWindow } }
    Component { id: clockComp; ClockModule { barWindow: root.barWindow } }
    Component { id: customLeftComp; CustomWidgetsLeft { barWindow: root.barWindow } }
    Component { id: customCenterComp; CustomWidgetsCenter { barWindow: root.barWindow } }
    Component { id: customRightComp; CustomWidgetsRight { barWindow: root.barWindow } }
}
