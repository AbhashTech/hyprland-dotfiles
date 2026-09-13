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

    // Backdrop: modal background overlay that absorbs clicks from passing to background windows,
    // but does NOT close the plugin manager when clicked outside
    MouseArea {
        anchors.fill: parent
        hoverEnabled: false
        preventStealing: true
        // Intentionally no onClicked - do not close when clicked outside
    }

    PluginManagerMenu {
        id: menuContainer
        width: 780
        height: 680
        anchors.top: parent.top
        anchors.topMargin: Theme.barHeight + 16
        anchors.horizontalCenter: parent.horizontalCenter
        focus: true
    }

    // Capture OS close keyboard shortcuts (Super+C, Alt+F4, Super+Q, Super+W, Escape)
    Keys.onPressed: (event) => {
        var isSuper = (event.modifiers & Qt.MetaModifier);
        var isAlt = (event.modifiers & Qt.AltModifier);
        if (event.key === Qt.Key_Escape ||
            (isSuper && (event.key === Qt.Key_C || event.key === Qt.Key_Q || event.key === Qt.Key_W)) ||
            (isAlt && event.key === Qt.Key_F4)) {
            PluginManager.pluginManagerVisible = false;
            PluginManager.closeAll();
            event.accepted = true;
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
