pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: root

    property string helperPath: Quickshell.env("HOME") + "/.config/quickshell/custom_plugins/calendar_sync/calendar_helper.py"

    property var eventsData: ({
        "last_sync": "",
        "today_str": "",
        "today_events": [],
        "future_events": [],
        "events_by_date": {}
    })

    property var sourcesData: ({ "sources": [] })
    property bool isSyncing: false
    property string lastSyncTime: ""
    property int syncVersion: 0

    function queryEvents() {
        if (!queryProc.running) {
            queryProc.exec(["python3", helperPath, "query"]);
        }
    }

    function syncNow() {
        if (!syncProc.running) {
            root.isSyncing = true;
            syncProc.exec(["python3", helperPath, "sync"]);
        }
    }

    function loadSources() {
        if (!sourcesProc.running) {
            sourcesProc.exec(["python3", helperPath, "list-sources"]);
        }
    }

    function addFileSource(name, path, color) {
        var p = Qt.createQmlObject('import Quickshell.Io; Process {}', root, "dynamicProc");
        p.onExited.connect(function() {
            root.loadSources();
            root.queryEvents();
            p.destroy();
        });
        p.exec(["python3", helperPath, "add-file", name || "", path, color || "#88c0d0"]);
    }

    function addUrlSource(name, url, color) {
        var p = Qt.createQmlObject('import Quickshell.Io; Process {}', root, "dynamicProc");
        p.onExited.connect(function() {
            root.loadSources();
            root.queryEvents();
            p.destroy();
        });
        p.exec(["python3", helperPath, "add-url", name || "", url, color || "#a3be8c"]);
    }

    function removeSource(id) {
        var p = Qt.createQmlObject('import Quickshell.Io; Process {}', root, "dynamicProc");
        p.onExited.connect(function() {
            root.loadSources();
            root.queryEvents();
            p.destroy();
        });
        p.exec(["python3", helperPath, "remove-source", id]);
    }

    function toggleSource(id) {
        var p = Qt.createQmlObject('import Quickshell.Io; Process {}', root, "dynamicProc");
        p.onExited.connect(function() {
            root.loadSources();
            root.queryEvents();
            p.destroy();
        });
        p.exec(["python3", helperPath, "toggle-source", id]);
    }

    function getEventCountForDate(dateStr) {
        var v = root.syncVersion;
        if (root.eventsData && root.eventsData.events_by_date && root.eventsData.events_by_date[dateStr]) {
            return root.eventsData.events_by_date[dateStr];
        }
        return 0;
    }

    function getEventsListForDate(dateStr) {
        var v = root.syncVersion;
        if (root.eventsData && root.eventsData.events_map && root.eventsData.events_map[dateStr]) {
            return root.eventsData.events_map[dateStr];
        }
        return [];
    }

    // Process for fast query
    property var queryProc: Process {
        id: queryProc
        stdout: SplitParser {
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (parsed && parsed.today_str) {
                        root.eventsData = parsed;
                        root.lastSyncTime = parsed.last_sync || "";
                        root.syncVersion++;
                    }
                } catch (e) {}
            }
        }
    }

    // Process for background sync
    property var syncProc: Process {
        id: syncProc
        stdout: SplitParser {
            onRead: data => {
                root.isSyncing = false;
                try {
                    var parsed = JSON.parse(data);
                    if (parsed && parsed.today_str) {
                        root.eventsData = parsed;
                        root.lastSyncTime = parsed.last_sync || "";
                        root.syncVersion++;
                    }
                } catch (e) {}
            }
        }
        onExited: {
            root.isSyncing = false;
        }
    }

    // Process for sources list
    property var sourcesProc: Process {
        id: sourcesProc
        stdout: SplitParser {
            onRead: data => {
                try {
                    var parsed = JSON.parse(data);
                    if (parsed && parsed.sources) {
                        root.sourcesData = parsed;
                    }
                } catch (e) {}
            }
        }
    }

    // Auto-sync timer (every 15 minutes)
    property var syncTimer: Timer {
        interval: 15 * 60 * 1000
        running: true
        repeat: true
        onTriggered: root.syncNow()
    }

    // Initial query on startup
    property var initTimer: Timer {
        interval: 800
        running: true
        repeat: false
        onTriggered: {
            root.queryEvents();
            root.loadSources();
        }
    }
}
