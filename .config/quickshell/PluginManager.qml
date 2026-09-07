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

    // Close all open plugins
    function closeAll() {
        appMenuVisible = false;
        powerMenuVisible = false;
        clipboardVisible = false;
        calcVisible = false;
        emojiVisible = false;
        keybindsVisible = false;
        volumeVisible = false;
        brightnessVisible = false;
        sysinfoVisible = false;
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
                current = clipboardVisible;
                closeAll();
                clipboardVisible = !current;
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
            case "audio":
            case "sound":
                current = volumeVisible;
                closeAll();
                volumeVisible = !current;
                break;
            case "brightness":
                current = brightnessVisible;
                closeAll();
                brightnessVisible = !current;
                break;
            case "sysinfo":
            case "stats":
                current = sysinfoVisible;
                closeAll();
                sysinfoVisible = !current;
                break;
            case "close":
            case "hide":
                closeAll();
                break;
            default:
                break;
        }
    }

    // File watcher for external IPC trigger (~/.cache/quickshell_plugin_trigger)
    property var triggerFile: FileView {
        path: Quickshell.env("HOME") + "/.cache/quickshell_plugin_trigger"
        printErrors: false
        onLoaded: {
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
