import QtQuick
import Quickshell
import Quickshell.Wayland
import "../.."

PanelWindow {
    id: wsViewerWindow

    visible: PluginManager.workspaceViewerVisible

    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }

    color: "transparent"

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell:workspace_viewer"
    WlrLayershell.keyboardFocus: PluginManager.workspaceViewerVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    MouseArea {
        anchors.fill: parent
        onClicked: PluginManager.closeAll()

        WorkspaceViewerMenu {
            id: wsViewerMenuItem
            anchors.centerIn: parent

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
            }
        }
    }

    Connections {
        target: PluginManager
        function onWorkspaceViewerVisibleChanged() {
            if (PluginManager.workspaceViewerVisible) {
                wsViewerMenuItem.grabFocus();
            }
        }
    }
}
