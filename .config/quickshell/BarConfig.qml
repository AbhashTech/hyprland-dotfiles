pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    property int version: 0

    // ── Drag and Drop Live State ──────────────────────────────────────────────
    property bool isDragging: false
    property string draggedModule: ""
    property string dragSourceSection: ""
    property int dragSourceIndex: -1
    property real dragX: 0
    property real dragY: 0
    property string targetSection: ""
    property int targetIndex: -1

    // ── Reactive in-memory state ──────────────────────────────────────────────
    property string position: "top"
    readonly property bool isTop: position === "top"
    readonly property bool isBottom: position === "bottom"
    property bool floating: true
    property int barHeight: 38
    property int barRadius: 16
    property int capsuleRadius: 12
    property int spacing: 3
    property int marginTop: 6
    property int marginBottom: 6
    property int marginLeft: 8
    property int marginRight: 8
    property bool compactMode: false

    property var leftModules: ["launcher", "workspaces", "activewindow", "custom_left"]
    property var centerModules: ["mpris", "custom_center", "language"]
    property var rightModules: ["tray", "clipboard", "notifications", "volume", "brightness", "wifi", "bluetooth", "battery", "stats", "power", "clock"]
    property var hiddenModules: []

    // ── Master Catalog ────────────────────────────────────────────────────────
    readonly property var moduleCatalog: [
        { id: "launcher", name: "App Launcher", icon: "󰣇", description: "Application menu search and quick power launcher", category: "Navigation", defaultSection: "left" },
        { id: "workspaces", name: "Workspaces", icon: "󰨇", description: "Active virtual workspaces with preview popups and scroll navigation", category: "Navigation", defaultSection: "left" },
        { id: "activewindow", name: "Active Window", icon: "󰘔", description: "Current focused window title and application icon", category: "Information", defaultSection: "left" },
        { id: "mpris", name: "Media Player (MPRIS)", icon: "󰎈", description: "Now-playing music info, playback controls, and track details", category: "Media", defaultSection: "center" },
        { id: "language", name: "Keyboard Layout", icon: "󰌌", description: "Current keyboard layout indicator and switcher", category: "System", defaultSection: "center" },
        { id: "recording", name: "Recording Indicator", icon: "󰑋", description: "Screen capture and audio recording active status capsule", category: "System", defaultSection: "right" },
        { id: "tray", name: "System Tray", icon: "󰍜", description: "System background application tray icons", category: "System", defaultSection: "right" },
        { id: "clipboard", name: "Clipboard History", icon: "󰅌", description: "Clipboard manager button with search and private mode toggle", category: "System", defaultSection: "right" },
        { id: "notifications", name: "Notification Hub", icon: "󰂚", description: "Notification center and DND toggle", category: "System", defaultSection: "right" },
        { id: "volume", name: "Audio Volume", icon: "󰕾", description: "Volume output level and mute toggle", category: "Hardware", defaultSection: "right" },
        { id: "brightness", name: "Screen Brightness", icon: "󰃠", description: "Display backlight brightness level and control", category: "Hardware", defaultSection: "right" },
        { id: "wifi", name: "Wi-Fi Network", icon: "󰤨", description: "Wireless network status and control center", category: "Hardware", defaultSection: "right" },
        { id: "bluetooth", name: "Bluetooth Peripherals", icon: "󰂯", description: "Bluetooth connectivity and paired devices", category: "Hardware", defaultSection: "right" },
        { id: "battery", name: "Battery & Power", icon: "󰁹", description: "Battery charge indicator and power profiles", category: "Hardware", defaultSection: "right" },
        { id: "stats", name: "Hardware Resource Stats", icon: "󰍛", description: "Live CPU load, memory utilization, and hardware graphs", category: "Hardware", defaultSection: "right" },
        { id: "power", name: "Power Menu", icon: "", description: "Power options: lock screen, suspend, reboot, and power off", category: "System", defaultSection: "right" },
        { id: "clock", name: "Clock & Calendar", icon: "", description: "Live clock, date view, and interactive calendar popup", category: "Time", defaultSection: "right" },
        { id: "custom_left", name: "Left Custom Plugins", icon: "󰏖", description: "User plugins configured to appear on the left section", category: "Custom Plugins", defaultSection: "left" },
        { id: "custom_center", name: "Center Custom Plugins", icon: "󰏖", description: "User plugins configured to appear in the center section", category: "Custom Plugins", defaultSection: "center" },
        { id: "custom_right", name: "Right Custom Plugins", icon: "󰏖", description: "User plugins configured to appear on the right section", category: "Custom Plugins", defaultSection: "right" }
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

    function getSectionForModule(moduleId) {
        if (leftModules.indexOf(moduleId) !== -1) return "left";
        if (centerModules.indexOf(moduleId) !== -1) return "center";
        if (rightModules.indexOf(moduleId) !== -1) return "right";
        return "hidden";
    }

    function startDrag(moduleId, fromSection, fromIndex) {
        root.isDragging = true;
        root.draggedModule = moduleId;
        root.dragSourceSection = fromSection;
        root.dragSourceIndex = fromIndex;
    }

    function updateDragPos(globalX, barWidth) {
        root.dragX = globalX;
        root.updateDropTarget(globalX, barWidth);
    }

    function endDrag() {
        if (root.isDragging && root.draggedModule !== "") {
            if (root.targetSection !== "") {
                root.moveModule(root.draggedModule, root.targetSection, root.targetIndex);
            }
            root.isDragging = false;
            root.draggedModule = "";
            root.targetSection = "";
            root.targetIndex = -1;
        }
    }

    function updateDropTarget(globalX, barWidth) {
        var leftBound = barWidth * 0.35;
        var rightBound = barWidth * 0.65;

        if (globalX < leftBound) {
            root.targetSection = "left";
            var leftCount = root.leftModules.length;
            var ratio = Math.max(0, Math.min(1, globalX / leftBound));
            root.targetIndex = Math.floor(ratio * (leftCount + 1));
        } else if (globalX > rightBound) {
            root.targetSection = "right";
            var rightCount = root.rightModules.length;
            var ratio = Math.max(0, Math.min(1, (globalX - rightBound) / (barWidth - rightBound)));
            root.targetIndex = Math.floor(ratio * (rightCount + 1));
        } else {
            root.targetSection = "center";
            var centerCount = root.centerModules.length;
            var ratio = Math.max(0, Math.min(1, (globalX - leftBound) / (rightBound - leftBound)));
            root.targetIndex = Math.floor(ratio * (centerCount + 1));
        }
    }

    function moveModule(moduleId, targetSection, targetIndex) {
        if (!moduleId || !targetSection) return;

        var left = root.leftModules.slice();
        var center = root.centerModules.slice();
        var right = root.rightModules.slice();
        var hidden = root.hiddenModules.slice();

        // Remove from current list
        var lIdx = left.indexOf(moduleId);
        if (lIdx !== -1) left.splice(lIdx, 1);
        var cIdx = center.indexOf(moduleId);
        if (cIdx !== -1) center.splice(cIdx, 1);
        var rIdx = right.indexOf(moduleId);
        if (rIdx !== -1) right.splice(rIdx, 1);
        var hIdx = hidden.indexOf(moduleId);
        if (hIdx !== -1) hidden.splice(hIdx, 1);

        // Target list insertion
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
}
