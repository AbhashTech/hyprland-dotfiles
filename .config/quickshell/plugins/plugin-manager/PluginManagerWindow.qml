import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."
import "../../components"
import "."

PanelWindow {
    id: pluginManagerWindow

    visible: PluginManager.pluginManagerVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:plugin_manager"
    WlrLayershell.keyboardFocus: PluginManager.pluginManagerVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    // Backdrop
    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        PluginManagerMenu {
            id: menuContainer
            width: 780
            height: 680
            anchors.top: parent.top
            anchors.topMargin: Theme.barHeight + 16
            anchors.horizontalCenter: parent.horizontalCenter

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    onVisibleChanged: {
        if (visible) {
            PluginManagerService.refresh();
            if (menuContainer.focusSearch) {
                menuContainer.focusSearch();
            }
        }
    }

    Connections {
        target: PluginManager
        function onPluginManagerVisibleChanged() {
            if (PluginManager.pluginManagerVisible) {
                PluginManagerService.refresh();
                if (menuContainer.focusSearch) {
                    menuContainer.focusSearch();
                }
            }
        }
    }
}
