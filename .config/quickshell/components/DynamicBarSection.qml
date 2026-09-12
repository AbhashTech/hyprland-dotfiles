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

            visible: isTargetHere || isDraggedThis || (moduleLoader.item ? (moduleLoader.item.visible || moduleWrapper.implicitWidth > 0) : true)
            implicitWidth: (isTargetHere && !isDraggedThis ? 36 : 0) + (moduleLoader.item ? moduleLoader.item.implicitWidth : 32)
            implicitHeight: Theme.barHeight - 8

            Behavior on implicitWidth { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

            // Drop indicator gap / glow
            Rectangle {
                id: dropGap
                visible: isTargetHere && !isDraggedThis
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: 32
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
                    font.pixelSize: 12
                    color: Theme.accent
                }
            }

            // Container for module (Zero blocking overlay: child receives all hovers and clicks)
            Rectangle {
                id: capsuleContainer
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: moduleLoader.item ? moduleLoader.item.implicitWidth : 32
                radius: Theme.capsuleRadius
                color: "transparent"
                opacity: isDraggedThis ? 0.30 : 1.0

                Behavior on opacity { NumberAnimation { duration: 150 } }

                Loader {
                    id: moduleLoader
                    anchors.centerIn: parent
                    sourceComponent: root.getComponentForId(moduleId)
                    asynchronous: false

                    Binding {
                        target: moduleLoader.item
                        property: "barWindow"
                        value: root.barWindow
                        when: moduleLoader.item !== null && moduleLoader.item.hasOwnProperty("barWindow")
                    }
                    Binding {
                        target: moduleLoader.item
                        property: "barSection"
                        value: root.section
                        when: moduleLoader.item !== null && moduleLoader.item.hasOwnProperty("barSection")
                    }
                    Binding {
                        target: moduleLoader.item
                        property: "barIndex"
                        value: moduleWrapper.index
                        when: moduleLoader.item !== null && moduleLoader.item.hasOwnProperty("barIndex")
                    }
                    Binding {
                        target: moduleLoader.item
                        property: "barContainer"
                        value: root.barContainer
                        when: moduleLoader.item !== null && moduleLoader.item.hasOwnProperty("barContainer")
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
            case "volume":
                return volumeComp;
            case "brightness":
                return brightnessComp;
            case "wifi":
            case "network":
                return wifiComp;
            case "bluetooth":
                return bluetoothComp;
            case "battery":
                return batteryComp;
            case "tray":
                return trayComp;
            case "clipboard":
                return clipboardComp;
            case "notifications":
            case "notification":
                return notificationComp;
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
    Component { id: volumeComp; VolumeModule { barWindow: root.barWindow } }
    Component { id: brightnessComp; BrightnessModule { barWindow: root.barWindow } }
    Component { id: wifiComp; WifiModule { barWindow: root.barWindow } }
    Component { id: bluetoothComp; BluetoothModule { barWindow: root.barWindow } }
    Component { id: batteryComp; BatteryModule { barWindow: root.barWindow } }
    Component { id: trayComp; TrayModule { barWindow: root.barWindow } }
    Component { id: clipboardComp; ClipboardModule { barWindow: root.barWindow } }
    Component { id: notificationComp; NotificationModule { barWindow: root.barWindow } }
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
