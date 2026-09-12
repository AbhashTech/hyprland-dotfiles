import QtQuick
import Quickshell
import Quickshell.Widgets
import Quickshell.Io
import Quickshell.Services.SystemTray
import ".."

Rectangle {
    id: root

    property var barWindow: null
    property string barSection: "right"
    property int barIndex: -1
    property var barContainer: null

    readonly property int validItemCount: {
        const list = SystemTray.items ? SystemTray.items.values : null;
        if (!list || list.length === 0) return 0;
        let c = 0;
        for (let i = 0; i < list.length; i++) {
            const it = list[i];
            if (it && it.icon && it.icon.length > 0) {
                c++;
            }
        }
        return c;
    }

    readonly property bool hasItems: validItemCount > 0

    visible: hasItems || (BarConfig.isDragging && BarConfig.draggedModule === "tray")
    implicitHeight: visible ? Theme.barHeight - 8 : 0
    implicitWidth: hasItems ? (trayRow.implicitWidth + 8) : (visible ? 28 : 0)
    radius: Theme.capsuleRadius

    color: Theme.moduleBg
    border.color: Theme.moduleBorder
    border.width: visible && hasItems ? 1 : (visible ? 1 : 0)

    Row {
        id: trayRow
        anchors.centerIn: parent
        spacing: 4

        Repeater {
            id: trayRepeater
            model: SystemTray.items

            Item {
                id: trayItemWrapper
                required property var modelData
                readonly property bool hasIcon: !!(modelData && modelData.icon && modelData.icon.length > 0)
                visible: hasIcon
                width: hasIcon ? 18 : 0
                height: hasIcon ? 18 : 0
                anchors.verticalCenter: parent.verticalCenter

                QsMenuAnchor {
                    id: menuAnchor
                    menu: trayItemWrapper.modelData.menu
                    anchor.window: root.barWindow
                    anchor.item: trayItemWrapper
                }

                Image {
                    anchors.fill: parent
                    source: modelData.icon || ""
                    sourceSize: Qt.size(24, 24)
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: trayMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: BarConfig.isDragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
                    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

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
                                BarConfig.startDrag("tray", root.barSection, root.barIndex);
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
                            return;
                        }
                        try {
                            if (mouse.button === Qt.LeftButton) {
                                modelData.activate();
                            } else if (mouse.button === Qt.RightButton) {
                                if (modelData.hasMenu && modelData.menu) {
                                    menuAnchor.open();
                                } else if (modelData.hasMenu) {
                                    menuAnchor.open();
                                } else if (typeof modelData.secondaryActivate === "function") {
                                    modelData.secondaryActivate();
                                } else {
                                    modelData.activate();
                                }
                            } else if (mouse.button === Qt.MiddleButton) {
                                if (typeof modelData.secondaryActivate === "function") {
                                    modelData.secondaryActivate();
                                }
                            }
                        } catch (e) {}
                    }
                }

                BarTooltip {
                    barWindow: root.barWindow
                    targetItem: trayItemWrapper
                    isHovered: trayMa.containsMouse && !BarConfig.isDragging
                    icon: "󰍜"
                    title: (modelData.title && modelData.title.length > 0) ? modelData.title : (modelData.id ? modelData.id : "System Tray App")
                    description: "Background system tray indicator"
                    shortcuts: [
                        { action: "Activate", key: "Left Click" },
                        { action: "Menu", key: "Right Click" }
                    ]
                }
            }
        }
    }
}
