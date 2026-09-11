pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    property int version: 0
    property bool editMode: false
    property string selectedModule: ""
    property string draggedModule: ""
    property string dragSourceSection: ""
    property int dragSourceIndex: -1
    property string activeDropTargetSection: ""
    property int activeDropTargetIndex: -1

    // File watcher for dynamic config reloading
    property var configFile: FileView {
        path: Quickshell.env("HOME") + "/.config/quickshell/bar_config.json"
        printErrors: false
        onLoaded: {
            root.version++;
        }
    }

    readonly property var rawConfig: {
        var v = root.version;
        try {
            var raw = configFile.text();
            if (raw && raw.trim().length > 0) {
                return JSON.parse(raw);
            }
        } catch (e) {
            // fallback
        }
        return {
            "position": "top",
            "floating": true,
            "barHeight": 38,
            "barRadius": 16,
            "capsuleRadius": 12,
            "spacing": 6,
            "marginTop": 8,
            "marginBottom": 8,
            "marginLeft": 12,
            "marginRight": 12,
            "compactMode": false,
            "leftModules": ["launcher", "workspaces", "activewindow", "custom_left"],
            "centerModules": ["mpris", "custom_center", "language"],
            "rightModules": ["custom_right", "recording", "traynotif", "status", "stats", "power", "clock"],
            "hiddenModules": []
        };
    }

    // Geometry and appearance
    readonly property string position: rawConfig.position || "top"
    readonly property bool isTop: position === "top"
    readonly property bool isBottom: position === "bottom"
    readonly property bool floating: rawConfig.floating !== undefined ? rawConfig.floating : true
    readonly property int barHeight: rawConfig.barHeight || 38
    readonly property int barRadius: rawConfig.barRadius || 16
    readonly property int capsuleRadius: rawConfig.capsuleRadius || 12
    readonly property int spacing: rawConfig.spacing !== undefined ? rawConfig.spacing : 6
    readonly property int marginTop: rawConfig.marginTop !== undefined ? rawConfig.marginTop : 8
    readonly property int marginBottom: rawConfig.marginBottom !== undefined ? rawConfig.marginBottom : 8
    readonly property int marginLeft: rawConfig.marginLeft !== undefined ? rawConfig.marginLeft : 12
    readonly property int marginRight: rawConfig.marginRight !== undefined ? rawConfig.marginRight : 12
    readonly property bool compactMode: !!rawConfig.compactMode

    // Modules per section
    readonly property var leftModules: rawConfig.leftModules || ["launcher", "workspaces", "activewindow", "custom_left"]
    readonly property var centerModules: rawConfig.centerModules || ["mpris", "custom_center", "language"]
    readonly property var rightModules: rawConfig.rightModules || ["custom_right", "recording", "traynotif", "status", "stats", "power", "clock"]
    readonly property var hiddenModules: rawConfig.hiddenModules || []

    // Master Catalog
    readonly property var moduleCatalog: [
        {
            id: "launcher",
            name: "App Launcher",
            icon: "󰣇",
            description: "Application menu search and quick power launcher",
            category: "Navigation",
            defaultSection: "left"
        },
        {
            id: "workspaces",
            name: "Workspaces",
            icon: "󰨇",
            description: "Active virtual workspaces with preview popups and scroll navigation",
            category: "Navigation",
            defaultSection: "left"
        },
        {
            id: "activewindow",
            name: "Active Window",
            icon: "󰘔",
            description: "Current focused window title and application icon",
            category: "Information",
            defaultSection: "left"
        },
        {
            id: "mpris",
            name: "Media Player (MPRIS)",
            icon: "󰎈",
            description: "Now-playing music info, playback controls, and track details",
            category: "Media",
            defaultSection: "center"
        },
        {
            id: "language",
            name: "Keyboard Layout",
            icon: "󰌌",
            description: "Current keyboard layout indicator and switcher",
            category: "System",
            defaultSection: "center"
        },
        {
            id: "recording",
            name: "Recording Indicator",
            icon: "󰑋",
            description: "Screen capture and audio recording active status capsule",
            category: "System",
            defaultSection: "right"
        },
        {
            id: "traynotif",
            name: "Tray & Notification Hub",
            icon: "󰂚",
            description: "System tray apps, clipboard history button, and unread notifications",
            category: "System",
            defaultSection: "right"
        },
        {
            id: "status",
            name: "Quick Status Controls",
            icon: "󰤨",
            description: "Volume mixer, brightness, Wi-Fi, Bluetooth, and battery gauges",
            category: "Hardware",
            defaultSection: "right"
        },
        {
            id: "stats",
            name: "Hardware Resource Stats",
            icon: "󰍛",
            description: "Live CPU load, memory utilization, and hardware graphs",
            category: "Hardware",
            defaultSection: "right"
        },
        {
            id: "power",
            name: "Power Menu",
            icon: "",
            description: "Power options: lock screen, suspend, reboot, and power off",
            category: "System",
            defaultSection: "right"
        },
        {
            id: "clock",
            name: "Clock & Calendar",
            icon: "",
            description: "Live clock, date view, and interactive calendar popup",
            category: "Time",
            defaultSection: "right"
        },
        {
            id: "custom_left",
            name: "Left Custom Plugins",
            icon: "󰏖",
            description: "User plugins configured to appear on the left section",
            category: "Custom Plugins",
            defaultSection: "left"
        },
        {
            id: "custom_center",
            name: "Center Custom Plugins",
            icon: "󰏖",
            description: "User plugins configured to appear in the center section",
            category: "Custom Plugins",
            defaultSection: "center"
        },
        {
            id: "custom_right",
            name: "Right Custom Plugins",
            icon: "󰏖",
            description: "User plugins configured to appear on the right section",
            category: "Custom Plugins",
            defaultSection: "right"
        }
    ]

    function getModuleMeta(moduleId) {
        if (!moduleId) return null;
        for (var i = 0; i < moduleCatalog.length; i++) {
            if (moduleCatalog[i].id === moduleId) {
                return moduleCatalog[i];
            }
        }
        return {
            id: moduleId,
            name: moduleId.replace(/_/g, " ").replace(/-/g, " "),
            icon: "󰏖",
            description: "Module " + moduleId,
            category: "Custom",
            defaultSection: "center"
        };
    }

    function isModuleVisible(moduleId) {
        if (hiddenModules.indexOf(moduleId) !== -1) return false;
        if (leftModules.indexOf(moduleId) !== -1) return true;
        if (centerModules.indexOf(moduleId) !== -1) return true;
        if (rightModules.indexOf(moduleId) !== -1) return true;
        return false;
    }

    function getSectionForModule(moduleId) {
        if (leftModules.indexOf(moduleId) !== -1) return "left";
        if (centerModules.indexOf(moduleId) !== -1) return "center";
        if (rightModules.indexOf(moduleId) !== -1) return "right";
        if (hiddenModules.indexOf(moduleId) !== -1) return "hidden";
        return "hidden";
    }

    function getSectionModules(section) {
        if (section === "left") return leftModules;
        if (section === "center") return centerModules;
        if (section === "right") return rightModules;
        if (section === "hidden") return hiddenModules;
        return [];
    }

    property var execProc: Process {
        id: execProc
    }

    function runHelper(args) {
        var cmd = ["python3", Quickshell.env("HOME") + "/.config/quickshell/scripts/bar_config_helper.py"].concat(args);
        execProc.exec(cmd);
    }

    function saveFullConfig(configObj) {
        runHelper(["save", "--json-data", JSON.stringify(configObj)]);
    }

    function setBarPosition(pos) {
        runHelper(["set-position", "--position", pos]);
    }

    function setMetric(key, val) {
        runHelper(["set-metric", "--key", key, "--value", val.toString()]);
    }

    function toggleEditMode() {
        root.editMode = !root.editMode;
        if (!root.editMode) {
            root.selectedModule = "";
            root.draggedModule = "";
        }
    }

    function moveModule(moduleId, targetSection, targetIndex) {
        if (!moduleId || !targetSection) return;
        var idx = targetIndex !== undefined ? targetIndex.toString() : "-1";
        runHelper(["move", "--module-id", moduleId, "--target-section", targetSection, "--target-index", idx]);
    }

    function reorderModule(fromSection, fromIndex, toSection, toIndex) {
        runHelper([
            "reorder",
            "--from-section", fromSection,
            "--from-index", fromIndex.toString(),
            "--to-section", toSection,
            "--to-index", toIndex.toString()
        ]);
    }

    function moveStep(moduleId, direction) {
        var curSec = getSectionForModule(moduleId);
        if (curSec === "hidden") return;

        var list = getSectionModules(curSec);
        var idx = list.indexOf(moduleId);
        if (idx === -1) return;

        if (direction === "left" || direction === "up") {
            if (idx > 0) {
                reorderModule(curSec, idx, curSec, idx - 1);
            } else {
                // Move to preceding section
                if (curSec === "right") moveModule(moduleId, "center", -1);
                else if (curSec === "center") moveModule(moduleId, "left", -1);
            }
        } else if (direction === "right" || direction === "down") {
            if (idx < list.length - 1) {
                reorderModule(curSec, idx, curSec, idx + 1);
            } else {
                // Move to next section
                if (curSec === "left") moveModule(moduleId, "center", 0);
                else if (curSec === "center") moveModule(moduleId, "right", 0);
            }
        }
    }

    function toggleVisibility(moduleId) {
        runHelper(["toggle", "--module-id", moduleId]);
    }

    function applyPreset(presetName) {
        runHelper(["preset", "--preset-name", presetName]);
    }

    function resetToDefaults() {
        runHelper(["reset"]);
    }
}
