pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    // Central plugins data
    property var customPlugins: []
    property var builtinPlugins: []
    property var stats: ({
        totalCustom: 0,
        activeCustom: 0,
        disabledCustom: 0,
        totalBuiltin: 0
    })

    // Store / Catalog data
    property var catalog: []
    property bool isCatalogLoading: false

    // Git inspection data
    property var gitLogs: []
    property string gitLogPluginName: ""
    property string gitLogPluginId: ""
    property bool isGitLogsLoading: false

    // Diagnostics / System Logs Buffer
    property var diagnosticsLogs: []

    // Keybinding state
    property string activeKeybind: "SUPER + ALT + M"
    property bool isKeybindConflict: false
    property string keybindConflictDesc: ""
    property string keybindStatusMessage: ""
    property var recommendedKeybinds: []
    property string keybindTargetPlugin: "plugin_manager"

    // UI state
    property bool isLoading: false
    property string searchQuery: ""
    property string currentFilter: "all" // "all", "active", "disabled", "custom", "builtin"
    property string actionInProgress: ""

    // Toast notification state
    property string toastMessage: ""
    property string toastType: "info" // "info", "success", "error"
    property bool toastVisible: false

    readonly property string helperPath: Quickshell.env("HOME") + "/.config/quickshell/plugins/plugin-manager/plugin_helper.py"

    // Toast timer
    property var toastTimer: Timer {
        interval: 3500
        repeat: false
        onTriggered: {
            root.toastVisible = false;
        }
    }

    function showToast(msg, type) {
        root.toastMessage = msg;
        root.toastType = type || "info";
        root.toastVisible = true;
        root.appendLog(msg, type);
        toastTimer.restart();
    }

    function appendLog(msg, type) {
        var d = new Date();
        var timeStr = d.toTimeString().split(" ")[0];
        var copy = Array.from(root.diagnosticsLogs);
        copy.unshift({
            time: timeStr,
            message: msg,
            type: type || "info"
        });
        if (copy.length > 100) copy = copy.slice(0, 100);
        root.diagnosticsLogs = copy;
    }

    function clearLogs() {
        root.diagnosticsLogs = [];
    }

    // ── Processes with Full Output Accumulator ───────────────────────────────

    // 1. List Plugins Process
    property var listProc: Process {
        id: listProc
        property string buffer: ""
        command: ["python3", root.helperPath, "list"]
        onStarted: {
            buffer = "";
            root.isLoading = true;
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                listProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.isLoading = false;
            if (exitCode === 0 && listProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(listProc.buffer.trim());
                    if (res && res.success) {
                        root.customPlugins = res.customPlugins || [];
                        root.builtinPlugins = res.builtinPlugins || [];
                        root.stats = res.stats || root.stats;
                        root.appendLog("Loaded " + (res.customPlugins ? res.customPlugins.length : 0) + " custom plugins (" + (res.stats ? res.stats.activeCustom : 0) + " active)", "success");
                    }
                } catch (e) {
                    console.error("PluginManagerService list JSON parse error:", e);
                    root.appendLog("List parse error: " + e, "error");
                }
            }
            listProc.buffer = "";
        }
    }

    // 2. Catalog Fetch Process
    property var catalogProc: Process {
        id: catalogProc
        property string buffer: ""
        command: ["python3", root.helperPath, "catalog"]
        onStarted: {
            buffer = "";
            root.isCatalogLoading = true;
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                catalogProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.isCatalogLoading = false;
            if (exitCode === 0 && catalogProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(catalogProc.buffer.trim());
                    if (res && res.success) {
                        root.catalog = res.catalog || [];
                        root.appendLog("Loaded " + (res.catalog ? res.catalog.length : 0) + " discover store items", "info");
                    }
                } catch (e) {
                    console.error("Catalog parse error:", e);
                }
            }
            catalogProc.buffer = "";
        }
    }

    // 3. Toggle Plugin Process
    property var toggleProc: Process {
        id: toggleProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                toggleProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && toggleProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(toggleProc.buffer.trim());
                    if (res && res.success) {
                        var stateStr = res.enabled ? "enabled" : "disabled";
                        root.showToast("Plugin '" + (res.pluginId || res.folderName) + "' " + stateStr + "!", "success");
                        root.refresh();
                    } else if (res && res.error) {
                        root.showToast("Error: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Toggle proc error:", e);
                }
            }
            toggleProc.buffer = "";
        }
    }

    // 4. Update Manifest (Position/Metadata) Process
    property var manifestProc: Process {
        id: manifestProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                manifestProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && manifestProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(manifestProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Updated manifest for '" + res.pluginId + "'!", "success");
                        root.refresh();
                    } else if (res && res.error) {
                        root.showToast("Manifest update failed: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Manifest update error:", e);
                }
            }
            manifestProc.buffer = "";
        }
    }

    // 5. Delete Plugin Process
    property var deleteProc: Process {
        id: deleteProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                deleteProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && deleteProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(deleteProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Plugin '" + res.deletedFolder + "' deleted!", "success");
                        root.refresh();
                        root.loadCatalog();
                    } else if (res && res.error) {
                        root.showToast("Delete failed: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Delete proc error:", e);
                }
            }
            deleteProc.buffer = "";
        }
    }

    // 6. Create Plugin Process
    property var createProc: Process {
        id: createProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                createProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && createProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(createProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Created plugin '" + res.pluginId + "' successfully!", "success");
                        root.refresh();
                        root.loadCatalog();
                    } else if (res && res.error) {
                        root.showToast("Create failed: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Create proc error:", e);
                }
            }
            createProc.buffer = "";
        }
    }

    // 7. Git Clone Process
    property var gitProc: Process {
        id: gitProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                gitProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && gitProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(gitProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Installed plugin '" + res.folderName + "' from Git!", "success");
                        root.refresh();
                    } else if (res && res.error) {
                        root.showToast("Git clone failed: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Git proc error:", e);
                }
            }
            gitProc.buffer = "";
        }
    }

    // 8. Git Pull Process
    property var gitPullProc: Process {
        id: gitPullProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                gitPullProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && gitPullProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(gitPullProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Git pull complete: " + (res.message || "Up to date"), "success");
                        root.refresh();
                    } else if (res && res.error) {
                        root.showToast("Git pull error: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Git pull error:", e);
                }
            }
            gitPullProc.buffer = "";
        }
    }

    // 9. Git Log Process
    property var gitLogProc: Process {
        id: gitLogProc
        property string buffer: ""
        onStarted: {
            buffer = "";
            root.isGitLogsLoading = true;
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                gitLogProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.isGitLogsLoading = false;
            if (exitCode === 0 && gitLogProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(gitLogProc.buffer.trim());
                    if (res && res.success) {
                        root.gitLogs = res.commits || [];
                    } else {
                        root.gitLogs = [];
                    }
                } catch (e) {
                    console.error("Git log parse error:", e);
                }
            }
            gitLogProc.buffer = "";
        }
    }

    // 10. Export Plugin Process
    property var exportProc: Process {
        id: exportProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                exportProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && exportProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(exportProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Exported to " + res.archiveName + " (" + res.sizeFormatted + ")", "success");
                    } else if (res && res.error) {
                        root.showToast("Export failed: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Export error:", e);
                }
            }
            exportProc.buffer = "";
        }
    }

    // 11. Import Plugin Process
    property var importProc: Process {
        id: importProc
        property string buffer: ""
        onStarted: {
            buffer = "";
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                importProc.buffer += data;
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.actionInProgress = "";
            if (exitCode === 0 && importProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(importProc.buffer.trim());
                    if (res && res.success) {
                        root.showToast("Plugin imported successfully!", "success");
                        root.refresh();
                    } else if (res && res.error) {
                        root.showToast("Import error: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Import error:", e);
                }
            }
            importProc.buffer = "";
        }
    }

    // 12. Reload Shell Process
    property var reloadProc: Process {
        id: reloadProc
        command: ["python3", root.helperPath, "reload"]
        stdout: SplitParser {
            onRead: data => {
                root.showToast("Quickshell hot-reloaded!", "success");
            }
        }
    }

    property var openProc: Process {
        id: openProc
    }

    // ── Public API Methods ───────────────────────────────────────────────────

    function refresh() {
        if (listProc.running) {
            listProc.running = false;
        }
        listProc.command = ["python3", root.helperPath, "list"];
        listProc.running = true;
    }

    function loadCatalog() {
        if (catalogProc.running) {
            catalogProc.running = false;
        }
        catalogProc.command = ["python3", root.helperPath, "catalog"];
        catalogProc.running = true;
    }

    function launchPluginUI(pluginId) {
        if (!pluginId) return;
        try {
            PluginManager.toggle(pluginId);
        } catch (e) {
            console.error("PluginManager toggle error:", e);
        }
        openProc.exec(["bash", Quickshell.env("HOME") + "/.config/quickshell/scripts/toggle_plugin.sh", pluginId]);
        root.appendLog("Launched UI for " + pluginId, "info");
    }

    function togglePlugin(pluginId, targetEnabled) {
        root.actionInProgress = "toggle:" + pluginId;
        toggleProc.exec(["python3", root.helperPath, "toggle", pluginId, targetEnabled ? "true" : "false"]);
    }

    function updateManifest(pluginId, updatesObj) {
        root.actionInProgress = "manifest:" + pluginId;
        manifestProc.exec(["python3", root.helperPath, "update-manifest", pluginId, JSON.stringify(updatesObj)]);
    }

    function setPluginPosition(pluginId, newPos) {
        root.updateManifest(pluginId, { position: newPos });
    }

    function deletePlugin(pluginId) {
        root.actionInProgress = "delete:" + pluginId;
        deleteProc.exec(["python3", root.helperPath, "delete", pluginId]);
    }

    function createPlugin(configObj) {
        root.actionInProgress = "create";
        createProc.exec(["python3", root.helperPath, "create", JSON.stringify(configObj)]);
    }

    function installFromCatalog(catalogItem) {
        root.createPlugin({
            id: catalogItem.id,
            name: catalogItem.name,
            author: catalogItem.author,
            description: catalogItem.description,
            position: catalogItem.position || "center",
            hasWidget: catalogItem.hasWidget !== false,
            hasWindow: catalogItem.hasWindow !== false,
            hasService: catalogItem.hasService === true,
            dependencies: catalogItem.dependencies || [],
            initGit: true
        });
    }

    function installGit(repoUrl, folderName) {
        root.actionInProgress = "git";
        if (folderName && folderName.trim().length > 0) {
            gitProc.exec(["python3", root.helperPath, "install-git", repoUrl.trim(), folderName.trim()]);
        } else {
            gitProc.exec(["python3", root.helperPath, "install-git", repoUrl.trim()]);
        }
    }

    function gitPull(pluginId) {
        root.actionInProgress = "pull:" + pluginId;
        gitPullProc.exec(["python3", root.helperPath, "git-pull", pluginId]);
    }

    function fetchGitLog(pluginId, pluginName) {
        root.gitLogPluginId = pluginId;
        root.gitLogPluginName = pluginName || pluginId;
        root.isGitLogsLoading = true;
        gitLogProc.exec(["python3", root.helperPath, "git-log", pluginId]);
    }

    function exportPlugin(pluginId) {
        root.actionInProgress = "export:" + pluginId;
        exportProc.exec(["python3", root.helperPath, "export", pluginId]);
    }

    function importPlugin(archivePath) {
        root.actionInProgress = "import";
        importProc.exec(["python3", root.helperPath, "import", archivePath.trim()]);
    }

    function reloadShell() {
        reloadProc.exec(["python3", root.helperPath, "reload"]);
    }

    // 13. Get Keybind Process
    property var getKeybindProc: Process {
        id: getKeybindProc
        property string buffer: ""
        onStarted: { buffer = ""; }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => { getKeybindProc.buffer += data; }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode === 0 && getKeybindProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(getKeybindProc.buffer.trim());
                    if (res && res.success && res.keybind) {
                        root.activeKeybind = res.keybind;
                    }
                } catch (e) {
                    console.error("Get keybind parse error:", e);
                }
            }
            getKeybindProc.buffer = "";
        }
    }

    // 14. Check Keybind Process
    property var checkKeybindProc: Process {
        id: checkKeybindProc
        property string buffer: ""
        onStarted: { buffer = ""; }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => { checkKeybindProc.buffer += data; }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode === 0 && checkKeybindProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(checkKeybindProc.buffer.trim());
                    root.isKeybindConflict = !!res.hasConflict;
                    root.keybindConflictDesc = res.conflictDesc || "";
                    root.keybindStatusMessage = res.message || "";
                    root.recommendedKeybinds = res.recommended || [];
                } catch (e) {
                    console.error("Check keybind parse error:", e);
                }
            }
            checkKeybindProc.buffer = "";
        }
    }

    // 15. Save Keybind Process
    property var saveKeybindProc: Process {
        id: saveKeybindProc
        property string buffer: ""
        onStarted: { buffer = ""; }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => { saveKeybindProc.buffer += data; }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode === 0 && saveKeybindProc.buffer.trim().length > 0) {
                try {
                    var res = JSON.parse(saveKeybindProc.buffer.trim());
                    if (res && res.success) {
                        root.activeKeybind = res.keybind || "";
                        root.isKeybindConflict = false;
                        root.showToast("Keybinding saved to '" + res.keybind + "'!", "success");
                    } else if (res && res.error) {
                        root.showToast("Keybinding error: " + res.error, "error");
                    }
                } catch (e) {
                    console.error("Save keybind error:", e);
                }
            }
            saveKeybindProc.buffer = "";
        }
    }

    function loadKeybind(pluginId) {
        var pid = pluginId || root.keybindTargetPlugin || "plugin_manager";
        root.keybindTargetPlugin = pid;
        getKeybindProc.exec(["python3", root.helperPath, "get-keybind", pid]);
    }

    function checkKeybind(combo, pluginId) {
        if (!combo || combo.trim().length === 0) return;
        var pid = pluginId || root.keybindTargetPlugin || "plugin_manager";
        checkKeybindProc.exec(["python3", root.helperPath, "check-keybind", combo.trim(), pid]);
    }

    function saveKeybind(combo, pluginId) {
        if (!combo || combo.trim().length === 0) return;
        var pid = pluginId || root.keybindTargetPlugin || "plugin_manager";
        saveKeybindProc.exec(["python3", root.helperPath, "set-keybind", combo.trim(), pid]);
    }

    // Auto-fetch data on initialization
    Component.onCompleted: {
        root.refresh();
        root.loadCatalog();
        root.loadKeybind("plugin_manager");
        root.appendLog("Plugin Manager service ready", "info");
    }
}
