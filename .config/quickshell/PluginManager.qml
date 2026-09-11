pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    // Active state for each plugin
    property bool appMenuVisible: false
    property bool powerMenuVisible: false
    property bool clipboardVisible: false
    property bool calcVisible: false
    property bool emojiVisible: false
    property bool keybindsVisible: false
    property bool volumeVisible: false
    property bool brightnessVisible: false
    property bool sysinfoVisible: false
    property bool batteryVisible: false
    property bool notificationVisible: false
    property bool workspaceViewerVisible: false
    property string powerProfile: "balanced"
    property bool connectivityVisible: false
    property string connectivityTab: "wifi"
    property bool clipboardPromptClear: false

    // ── Dynamic Custom Plugins State ──────────────────────────────────────────
    property var customPluginStates: ({})
    property int customPluginVersion: 0

    function isPluginVisible(pluginId) {
        var v = customPluginVersion;
        if (!pluginId) return false;
        if (customPluginStates[pluginId] === true) return true;
        var alt1 = pluginId.replace(/-/g, "_");
        if (customPluginStates[alt1] === true) return true;
        var alt2 = pluginId.replace(/_/g, "-");
        if (customPluginStates[alt2] === true) return true;
        return false;
    }

    function setPluginVisible(pluginId, isVis) {
        if (!pluginId) return;
        var copy = Object.assign({}, customPluginStates);
        copy[pluginId] = isVis;
        copy[pluginId.replace(/-/g, "_")] = isVis;
        copy[pluginId.replace(/_/g, "-")] = isVis;
        customPluginStates = copy;
        customPluginVersion++;
    }

    // ── File Picker plugin ────────────────────────────────────────────────────
    property bool   filePickerVisible:    false
    property string filePickerMode:       "open"
    property string filePickerTitle:      "Open File"
    property string filePickerMimeFilter: "all"
    property string filePickerAppId:      ""
    property bool   filePickerMultiSelect: false

    function setPowerProfile(profile) {
        powerProfile = profile;
    }

    // Close all open plugins
    function closeAll() {
        appMenuVisible = false;
        powerMenuVisible = false;
        clipboardVisible = false;
        clipboardPromptClear = false;
        calcVisible = false;
        emojiVisible = false;
        keybindsVisible = false;
        volumeVisible = false;
        brightnessVisible = false;
        sysinfoVisible = false;
        batteryVisible = false;
        notificationVisible = false;
        workspaceViewerVisible = false;
        connectivityVisible = false;
        filePickerVisible = false;
        customPluginStates = ({});
        customPluginVersion++;
    }

    // Toggle a plugin by name
    function toggle(name) {
        var current = false;
        switch (name) {
            case "appmenu":
            case "menu":
            case "launcher":
                current = appMenuVisible;
                closeAll();
                appMenuVisible = !current;
                break;
            case "powermenu":
            case "power":
            case "session":
                current = powerMenuVisible;
                closeAll();
                powerMenuVisible = !current;
                break;
            case "clipboard":
            case "clip":
                current = clipboardVisible && !clipboardPromptClear;
                closeAll();
                clipboardVisible = !current;
                break;
            case "clipboard-clear":
            case "clip-clear":
            case "clipclear":
                current = clipboardVisible && clipboardPromptClear;
                closeAll();
                if (!current) {
                    clipboardPromptClear = true;
                    clipboardVisible = true;
                }
                break;
            case "calc":
            case "calculator":
                current = calcVisible;
                closeAll();
                calcVisible = !current;
                break;
            case "emoji":
                current = emojiVisible;
                closeAll();
                emojiVisible = !current;
                break;
            case "keybinds":
            case "shortcuts":
                current = keybindsVisible;
                closeAll();
                keybindsVisible = !current;
                break;
            case "volume":
            case "volumemenu":
            case "audio":
            case "sound":
            case "mixer":
                current = volumeVisible;
                closeAll();
                volumeVisible = !current;
                break;
            case "brightness":
            case "brightnessmenu":
            case "light":
                current = brightnessVisible;
                closeAll();
                brightnessVisible = !current;
                break;
            case "sysinfo":
            case "system":
            case "stats":
            case "resources":
                current = sysinfoVisible;
                closeAll();
                sysinfoVisible = !current;
                break;
            case "battery":
            case "powerprofile":
            case "powerprofiles":
            case "power":
                current = batteryVisible;
                closeAll();
                batteryVisible = !current;
                break;
            case "wifi":
            case "wifimenu":
            case "network":
            case "wlan":
                if (root.connectivityVisible && root.connectivityTab === "wifi") {
                    root.closeAll();
                } else {
                    root.closeAll();
                    root.connectivityTab = "wifi";
                    root.connectivityVisible = true;
                }
                break;
            case "bluetooth":
            case "bt":
            case "bluetoothmenu":
                if (root.connectivityVisible && root.connectivityTab === "bluetooth") {
                    root.closeAll();
                } else {
                    root.closeAll();
                    root.connectivityTab = "bluetooth";
                    root.connectivityVisible = true;
                }
                break;
            case "connectivity":
            case "wireless":
                current = root.connectivityVisible;
                root.closeAll();
                root.connectivityVisible = !current;
                break;
            case "notifications":
            case "notification":
            case "notif":
                current = root.notificationVisible;
                root.closeAll();
                root.notificationVisible = !current;
                break;
            case "workspaces":
            case "workspace":
            case "workspaceviewer":
            case "workspace_viewer":
            case "ws":
            case "overview":
                current = root.workspaceViewerVisible;
                root.closeAll();
                root.workspaceViewerVisible = !current;
                break;
            case "filepicker":
            case "picker":
            case "files":
            case "upload":
            case "file-picker":
                current = filePickerVisible;
                closeAll();
                filePickerVisible = !current;
                break;
            case "filepicker-portal":
            case "portal-open":
                // Always open (never toggle) — used by the XDG portal backend
                closeAll();
                filePickerVisible = true;
                break;
            case "filepicker-image":
            case "picker-image":
                closeAll();
                filePickerMimeFilter = "image";
                filePickerVisible = true;
                break;
            case "plugin_manager":
            case "plugin-manager":
            case "pluginmanager":
            case "plugins":
            case "pm":
                current = root.isPluginVisible("plugin_manager");
                root.closeAll();
                root.setPluginVisible("plugin_manager", !current);
                break;
            case "close":
            case "hide":
                closeAll();
                break;
            default:
                // Dynamically toggle any custom plugin by ID
                if (name && name.length > 0) {
                    var vis = root.isPluginVisible(name);
                    root.closeAll();
                    root.setPluginVisible(name, !vis);
                }
                break;
        }
    }

    // File watcher for external IPC trigger (~/.cache/quickshell_plugin_trigger)
    property bool triggerInitialized: false
    property var triggerFile: FileView {
        path: Quickshell.env("HOME") + "/.cache/quickshell_plugin_trigger"
        printErrors: false
        onLoaded: {
            if (!root.triggerInitialized) {
                root.triggerInitialized = true;
                return;
            }
            try {
                var content = triggerFile.text();
                if (content && content.trim().length > 0) {
                    var parts = content.trim().split(/\s+/);
                    if (parts.length > 0) {
                        root.toggle(parts[0]);
                    }
                }
            } catch (e) {}
        }
    }
}
