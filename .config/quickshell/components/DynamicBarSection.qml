import QtQuick
import QtQuick.Layouts
import Quickshell
import ".."
import "../generated"

Row {
    id: root

    property var barWindow: null
    property var barContainer: null
    property string section: "left" // "left" | "center" | "right"
    readonly property var moduleList: (section === "left") ? BarConfig.leftModules : (section === "center") ? BarConfig.centerModules : BarConfig.rightModules
    spacing: BarConfig.spacing

    // Drop slot if empty section is targeted
    Rectangle {
        id: emptyDropSlot
        visible: BarConfig.isDragging && root.moduleList.length === 0 && BarConfig.targetSection === root.section
        implicitHeight: Theme.barHeight - 8
        implicitWidth: 44
        radius: Theme.capsuleRadius
        color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.25)
        border.color: Theme.accent
        border.width: 1

        Text {
            anchors.centerIn: parent
            text: "󰐕"
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontSize
            color: Theme.accent
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
            readonly property bool isDraggedThis: BarConfig.isDragging && BarConfig.draggedModule === moduleId
            readonly property bool isTargetHere: BarConfig.isDragging && BarConfig.targetSection === root.section && BarConfig.targetIndex === index

            implicitWidth: (isTargetHere && !isDraggedThis ? 48 : 0) + (moduleLoader.item ? moduleLoader.item.implicitWidth : 38)
            implicitHeight: Theme.barHeight - 8

            Behavior on implicitWidth { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

            // Drop indicator gap / glow
            Rectangle {
                id: dropGap
                visible: isTargetHere && !isDraggedThis
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: 40
                height: parent.height
                radius: Theme.capsuleRadius
                color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.25)
                border.color: Theme.accent
                border.width: 1
                z: 10

                Text {
                    anchors.centerIn: parent
                    text: "󰐕"
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    color: Theme.accent
                }
            }

            // Container for module
            Rectangle {
                id: capsuleContainer
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: moduleLoader.item ? moduleLoader.item.implicitWidth : 38
                radius: Theme.capsuleRadius
                color: "transparent"
                opacity: isDraggedThis ? 0.35 : 1.0

                Behavior on opacity { NumberAnimation { duration: 150 } }

                Loader {
                    id: moduleLoader
                    anchors.centerIn: parent
                    sourceComponent: root.getComponentForId(moduleId)
                    asynchronous: false

                    onLoaded: {
                        if (item && item.hasOwnProperty("barWindow")) {
                            item.barWindow = root.barWindow;
                        }
                    }
                }

                // Interactive Drag & Move Handler
                MouseArea {
                    id: dragMa
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton
                    cursorShape: isDraggedThis ? Qt.ClosedHandCursor : (dragMa.containsMouse ? Qt.PointingHandCursor : Qt.ArrowCursor)

                    property real startPressX: 0
                    property real startPressY: 0
                    property bool movingActive: false

                    onPressed: mouse => {
                        startPressX = mouse.x;
                        startPressY = mouse.y;
                        movingActive = false;
                    }

                    onPositionChanged: mouse => {
                        if (pressed) {
                            var dx = mouse.x - startPressX;
                            var dy = mouse.y - startPressY;
                            if (!movingActive && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
                                movingActive = true;
                                BarConfig.isDragging = true;
                                BarConfig.draggedModule = moduleId;
                                BarConfig.dragSourceSection = root.section;
                                BarConfig.dragSourceIndex = index;
                            }
                            if (movingActive && root.barContainer) {
                                var pt = mapToItem(root.barContainer, mouse.x, mouse.y);
                                BarConfig.dragX = pt.x;
                                BarConfig.dragY = pt.y;
                                BarConfig.updateDropTarget(pt.x, root.barContainer.width);
                            }
                        }
                    }

                    onReleased: mouse => {
                        if (movingActive && BarConfig.isDragging) {
                            if (BarConfig.targetSection !== "") {
                                BarConfig.moveModule(BarConfig.draggedModule, BarConfig.targetSection, BarConfig.targetIndex);
                            }
                            BarConfig.isDragging = false;
                            BarConfig.draggedModule = "";
                            BarConfig.targetSection = "";
                            BarConfig.targetIndex = -1;
                            movingActive = false;
                        } else {
                            // Click pass-through: if user just clicked without dragging, trigger module default action
                            root.handleModuleClick(moduleId);
                        }
                    }
                }
            }
        }
    }

    // Default primary click action for each module when clicked
    function handleModuleClick(id) {
        switch (id) {
            case "launcher":
                PluginManager.toggle("appmenu");
                break;
            case "power":
                PluginManager.toggle("powermenu");
                break;
            case "clock":
                // handled by clock's own logic or toggle
                break;
            case "status":
                PluginManager.toggle("volume");
                break;
            case "traynotif":
                PluginManager.toggle("notifications");
                break;
            case "workspaces":
                PluginManager.toggle("workspaces");
                break;
            case "mpris":
                break;
            default:
                if (id.startsWith("plugin_")) {
                    PluginManager.toggle(id.replace("plugin_", ""));
                }
                break;
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
