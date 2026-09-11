import QtQuick
import QtQuick.Layouts
import Quickshell
import ".."
import "../generated"

Row {
    id: root

    property var barWindow: null
    property string section: "left" // "left" | "center" | "right"
    readonly property var moduleList: BarConfig.getSectionModules(section)
    spacing: BarConfig.spacing

    // Empty section placeholder in edit mode
    Rectangle {
        id: emptyPlaceholder
        visible: BarConfig.editMode && root.moduleList.length === 0
        implicitHeight: Theme.barHeight - 10
        implicitWidth: 140
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
                text: section.toUpperCase() + " Empty"
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fontSizeSmall
                font.bold: true
                color: Theme.subtext0
            }
        }

        DropArea {
            anchors.fill: parent
            onEntered: {
                BarConfig.activeDropTargetSection = root.section;
                BarConfig.activeDropTargetIndex = 0;
            }
            onExited: {
                if (BarConfig.activeDropTargetSection === root.section) {
                    BarConfig.activeDropTargetSection = "";
                }
            }
            onDropped: drop => {
                if (BarConfig.draggedModule !== "") {
                    BarConfig.moveModule(BarConfig.draggedModule, root.section, 0);
                    BarConfig.draggedModule = "";
                    BarConfig.activeDropTargetSection = "";
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
            readonly property bool isDropTargetHere: BarConfig.activeDropTargetSection === root.section && BarConfig.activeDropTargetIndex === index

            implicitWidth: (moduleLoader.item ? moduleLoader.item.implicitWidth : 38) + (BarConfig.editMode ? 32 : 0)
            implicitHeight: Theme.barHeight - 8

            Behavior on implicitWidth { NumberAnimation { duration: 150 } }

            // Drop indicator line before item
            Rectangle {
                id: dropIndicator
                visible: BarConfig.editMode && isDropTargetHere && !isDragged
                anchors.left: parent.left
                anchors.leftMargin: -3
                anchors.verticalCenter: parent.verticalCenter
                width: 4
                height: parent.height
                radius: 2
                color: Theme.accent
                z: 10
            }

            // Normal & Edit container
            Rectangle {
                id: editContainer
                anchors.fill: parent
                radius: Theme.capsuleRadius
                color: BarConfig.editMode ? (isSelected ? Theme.moduleActiveBg : Qt.rgba(Theme.mantle.r, Theme.mantle.g, Theme.mantle.b, 0.5)) : "transparent"
                border.color: BarConfig.editMode ? (isSelected ? Theme.accent : Theme.mauve) : "transparent"
                border.width: BarConfig.editMode ? 1 : 0
                opacity: isDragged ? 0.3 : 1.0

                Behavior on border.color { ColorAnimation { duration: 150 } }
                Behavior on opacity { NumberAnimation { duration: 150 } }

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

                    // Drag Handle on Left
                    Rectangle {
                        id: dragHandle
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 26
                        radius: Theme.capsuleRadius
                        color: dragHandleArea.containsMouse || isDragged ? Theme.mauve : Qt.rgba(Theme.surface0.r, Theme.surface0.g, Theme.surface0.b, 0.6)

                        Behavior on color { ColorAnimation { duration: 150 } }

                        Text {
                            anchors.centerIn: parent
                            text: "󰁝"
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fontSize
                            color: dragHandleArea.containsMouse || isDragged ? "#ffffff" : Theme.subtext0
                        }

                        MouseArea {
                            id: dragHandleArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.SizeAllCursor
                            drag.target: dragGhost
                            drag.axis: Drag.XAxis

                            onPressed: {
                                BarConfig.draggedModule = moduleId;
                                BarConfig.dragSourceSection = root.section;
                                BarConfig.dragSourceIndex = index;
                                BarConfig.selectedModule = moduleId;
                            }

                            onReleased: {
                                if (BarConfig.activeDropTargetSection !== "" && BarConfig.activeDropTargetIndex >= 0) {
                                    BarConfig.reorderModule(
                                        BarConfig.dragSourceSection,
                                        BarConfig.dragSourceIndex,
                                        BarConfig.activeDropTargetSection,
                                        BarConfig.activeDropTargetIndex
                                    );
                                }
                                BarConfig.draggedModule = "";
                                BarConfig.activeDropTargetSection = "";
                                BarConfig.activeDropTargetIndex = -1;
                            }
                        }
                    }

                    // Quick Action Menu on Right (Move Left, Move Right, Cycle Section, Hide)
                    Row {
                        anchors.right: parent.right
                        anchors.rightMargin: 4
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2
                        visible: moduleWrapperHoverArea.containsMouse || isSelected

                        // Move Left Button
                        Rectangle {
                            width: 18
                            height: 18
                            radius: 9
                            color: leftBtnArea.containsMouse ? Theme.blue : Qt.rgba(0, 0, 0, 0.4)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅁"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
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
                            width: 18
                            height: 18
                            radius: 9
                            color: rightBtnArea.containsMouse ? Theme.blue : Qt.rgba(0, 0, 0, 0.4)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅂"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
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

                        // Cycle Section Button (Left -> Center -> Right)
                        Rectangle {
                            width: 18
                            height: 18
                            radius: 9
                            color: secBtnArea.containsMouse ? Theme.teal : Qt.rgba(0, 0, 0, 0.4)
                            Text {
                                anchors.centerIn: parent
                                text: "󰆊"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
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
                            width: 18
                            height: 18
                            radius: 9
                            color: hideBtnArea.containsMouse ? Theme.red : Qt.rgba(0, 0, 0, 0.4)
                            Text {
                                anchors.centerIn: parent
                                text: "󰅙"
                                font.family: Theme.fontFamily
                                font.pixelSize: 10
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

                    // Drop Area for item reordering
                    DropArea {
                        anchors.fill: parent
                        onEntered: {
                            if (BarConfig.draggedModule !== "" && BarConfig.draggedModule !== moduleId) {
                                BarConfig.activeDropTargetSection = root.section;
                                BarConfig.activeDropTargetIndex = index;
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

            // Item Ghost for visual drag
            Item {
                id: dragGhost
                Drag.active: dragHandleArea.drag.active
                Drag.source: moduleWrapper
                Drag.hotSpot.x: 14
                Drag.hotSpot.y: 14
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
