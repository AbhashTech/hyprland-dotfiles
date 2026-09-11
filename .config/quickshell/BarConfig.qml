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

    // ── Reactive in-memory state ──────────────────────────────────────────────
    property string position: "top"
    readonly property bool isTop: position === "top"
    readonly property bool isBottom: position === "bottom"
    property bool floating: true
    property int barHeight: 38
    property int barRadius: 16
    property int capsuleRadius: 12
    property int spacing: 6
    property int marginTop: 8
    property int marginBottom: 8
    property int marginLeft: 12
    property int marginRight: 12
    property bool compactMode: false

    property var leftModules: ["launcher", "workspaces", "activewindow", "custom_left"]
    property var centerModules: ["mpris", "custom_center", "language"]
    property var rightModules: ["custom_right", "recording", "traynotif", "status", "stats", "power", "clock"]
    property var hiddenModules: []

    // ── Master Catalog ────────────────────────────────────────────────────────
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

    // ── Initial load & file watcher ───────────────────────────────────────────
    property var configFile: FileView {
        path: Quickshell.env("HOME") + "/.config/quickshell/bar_config.json"
        printErrors: false
        onLoaded: {
            root.loadFromText(configFile.text());
        }
    }

    function loadFromText(rawText) {
        if (!rawText || rawText.trim().length === 0) return;
        try {
            var data = JSON.parse(rawText);
            if (!data) return;
            if (data.position) root.position = data.position;
            if (data.floating !== undefined) root.floating = data.floating;
            if (data.barHeight) root.barHeight = data.barHeight;
            if (data.barRadius) root.barRadius = data.barRadius;
            if (data.capsuleRadius) root.capsuleRadius = data.capsuleRadius;
            if (data.spacing !== undefined) root.spacing = data.spacing;
            if (data.marginTop !== undefined) root.marginTop = data.marginTop;
            if (data.marginBottom !== undefined) root.marginBottom = data.marginBottom;
            if (data.marginLeft !== undefined) root.marginLeft = data.marginLeft;
            if (data.marginRight !== undefined) root.marginRight = data.marginRight;
            if (data.compactMode !== undefined) root.compactMode = data.compactMode;
            if (Array.isArray(data.leftModules)) root.leftModules = data.leftModules.slice();
            if (Array.isArray(data.centerModules)) root.centerModules = data.centerModules.slice();
            if (Array.isArray(data.rightModules)) root.rightModules = data.rightModules.slice();
            if (Array.isArray(data.hiddenModules)) root.hiddenModules = data.hiddenModules.slice();
            root.version++;
        } catch (e) {}
    }

    // ── Background Persistence Process ────────────────────────────────────────
    property var saveProc: Process {
        id: saveProc
    }

    function persist() {
        var cfg = {
            "version": 1,
            "position": root.position,
            "floating": root.floating,
            "barHeight": root.barHeight,
            "barRadius": root.barRadius,
            "capsuleRadius": root.capsuleRadius,
            "spacing": root.spacing,
            "marginTop": root.marginTop,
            "marginBottom": root.marginBottom,
            "marginLeft": root.marginLeft,
            "marginRight": root.marginRight,
            "compactMode": root.compactMode,
            "leftModules": root.leftModules,
            "centerModules": root.centerModules,
            "rightModules": root.rightModules,
            "hiddenModules": root.hiddenModules
        };

        if (saveProc.running) saveProc.running = false;
        saveProc.command = [
            "python3",
            Quickshell.env("HOME") + "/.config/quickshell/scripts/bar_config_helper.py",
            "save",
            "--json-data",
            JSON.stringify(cfg)
        ];
        saveProc.running = true;
    }

    // ── Helper Queries ────────────────────────────────────────────────────────
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

    // ── Public Mutators (Instant In-Memory + Disk Sync) ────────────────────────
    function toggleEditMode() {
        root.editMode = !root.editMode;
        if (!root.editMode) {
            root.selectedModule = "";
            root.draggedModule = "";
        }
    }

    function setBarPosition(pos) {
        root.position = pos;
        root.persist();
    }

    function setMetric(key, val) {
        if (key === "barHeight") root.barHeight = val;
        else if (key === "barRadius") root.barRadius = val;
        else if (key === "capsuleRadius") root.capsuleRadius = val;
        else if (key === "spacing") root.spacing = val;
        else if (key === "marginLeft") { root.marginLeft = val; root.marginRight = val; }
        else if (key === "compactMode") root.compactMode = val;
        root.persist();
    }

    function moveModule(moduleId, targetSection, targetIndex) {
        if (!moduleId || !targetSection) return;

        var left = root.leftModules.slice();
        var center = root.centerModules.slice();
        var right = root.rightModules.slice();
        var hidden = root.hiddenModules.slice();

        // Remove from current section
        var lIdx = left.indexOf(moduleId);
        if (lIdx !== -1) left.splice(lIdx, 1);
        var cIdx = center.indexOf(moduleId);
        if (cIdx !== -1) center.splice(cIdx, 1);
        var rIdx = right.indexOf(moduleId);
        if (rIdx !== -1) right.splice(rIdx, 1);
        var hIdx = hidden.indexOf(moduleId);
        if (hIdx !== -1) hidden.splice(hIdx, 1);

        // Insert into target section
        var targetArr = (targetSection === "left") ? left : (targetSection === "center" ? center : (targetSection === "right" ? right : hidden));
        if (targetIndex !== undefined && targetIndex >= 0 && targetIndex <= targetArr.length) {
            targetArr.splice(targetIndex, 0, moduleId);
        } else {
            targetArr.push(moduleId);
        }

        root.leftModules = left;
        root.centerModules = center;
        root.rightModules = right;
        root.hiddenModules = hidden;
        root.version++;
        root.persist();
    }

    function reorderModule(fromSection, fromIndex, toSection, toIndex) {
        var left = root.leftModules.slice();
        var center = root.centerModules.slice();
        var right = root.rightModules.slice();

        var srcArr = (fromSection === "left") ? left : (fromSection === "center" ? center : right);
        var dstArr = (toSection === "left") ? left : (toSection === "center" ? center : right);

        if (fromIndex < 0 || fromIndex >= srcArr.length) return;
        var item = srcArr.splice(fromIndex, 1)[0];

        if (toIndex >= 0 && toIndex <= dstArr.length) {
            dstArr.splice(toIndex, 0, item);
        } else {
            dstArr.push(item);
        }

        root.leftModules = left;
        root.centerModules = center;
        root.rightModules = right;
        root.version++;
        root.persist();
    }

    function moveStep(moduleId, direction) {
        var curSec = getSectionForModule(moduleId);
        if (curSec === "hidden") return;

        var list = (curSec === "left") ? root.leftModules.slice() : (curSec === "center" ? root.centerModules.slice() : root.rightModules.slice());
        var idx = list.indexOf(moduleId);
        if (idx === -1) return;

        if (direction === "left" || direction === "up") {
            if (idx > 0) {
                reorderModule(curSec, idx, curSec, idx - 1);
            } else {
                if (curSec === "right") moveModule(moduleId, "center", -1);
                else if (curSec === "center") moveModule(moduleId, "left", -1);
            }
        } else if (direction === "right" || direction === "down") {
            if (idx < list.length - 1) {
                reorderModule(curSec, idx, curSec, idx + 1);
            } else {
                if (curSec === "left") moveModule(moduleId, "center", 0);
                else if (curSec === "center") moveModule(moduleId, "right", 0);
            }
        }
    }

    function toggleVisibility(moduleId) {
        var isHidden = root.hiddenModules.indexOf(moduleId) !== -1;
        if (isHidden) {
            var hidden = root.hiddenModules.slice();
            var hIdx = hidden.indexOf(moduleId);
            if (hIdx !== -1) hidden.splice(hIdx, 1);
            root.hiddenModules = hidden;

            var meta = getModuleMeta(moduleId);
            var defSec = (meta && meta.defaultSection) ? meta.defaultSection : "center";
            moveModule(moduleId, defSec, -1);
        } else {
            moveModule(moduleId, "hidden", -1);
        }
    }

    function applyPreset(presetName) {
        var name = (presetName || "default").toLowerCase();
        if (name === "minimal") {
            root.position = "top";
            root.barHeight = 36;
            root.barRadius = 14;
            root.capsuleRadius = 10;
            root.spacing = 6;
            root.compactMode = true;
            root.leftModules = ["launcher", "workspaces"];
            root.centerModules = ["activewindow"];
            root.rightModules = ["status", "clock"];
            root.hiddenModules = ["mpris", "language", "recording", "traynotif", "stats", "power"];
        } else if (name === "poweruser") {
            root.position = "top";
            root.barHeight = 40;
            root.barRadius = 16;
            root.capsuleRadius = 12;
            root.spacing = 6;
            root.compactMode = false;
            root.leftModules = ["launcher", "workspaces", "activewindow", "custom_left"];
            root.centerModules = ["mpris", "custom_center"];
            root.rightModules = ["custom_right", "recording", "traynotif", "status", "stats", "language", "power", "clock"];
            root.hiddenModules = [];
        } else if (name === "dock") {
            root.position = "bottom";
            root.barHeight = 44;
            root.barRadius = 22;
            root.capsuleRadius = 14;
            root.spacing = 8;
            root.compactMode = false;
            root.leftModules = ["launcher", "workspaces"];
            root.centerModules = ["activewindow", "mpris"];
            root.rightModules = ["traynotif", "status", "clock", "power"];
            root.hiddenModules = ["stats", "recording", "language"];
        } else if (name === "split") {
            root.position = "top";
            root.barHeight = 38;
            root.barRadius = 16;
            root.capsuleRadius = 12;
            root.spacing = 6;
            root.compactMode = false;
            root.leftModules = ["launcher", "workspaces", "activewindow"];
            root.centerModules = ["clock"];
            root.rightModules = ["mpris", "traynotif", "status", "power"];
            root.hiddenModules = ["stats", "recording", "language"];
        } else {
            // default
            root.position = "top";
            root.barHeight = 38;
            root.barRadius = 16;
            root.capsuleRadius = 12;
            root.spacing = 6;
            root.compactMode = false;
            root.leftModules = ["launcher", "workspaces", "activewindow", "custom_left"];
            root.centerModules = ["mpris", "custom_center", "language"];
            root.rightModules = ["custom_right", "recording", "traynotif", "status", "stats", "power", "clock"];
            root.hiddenModules = [];
        }
        root.version++;
        root.persist();
    }

    function resetToDefaults() {
        applyPreset("default");
    }
}
