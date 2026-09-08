#!/usr/bin/env python3
"""
Quickshell File Picker - XDG Desktop Portal Backend
Registers as: org.freedesktop.impl.portal.desktop.quickshell
Implements: org.freedesktop.impl.portal.FileChooser

This service intercepts file open/save dialogs from XDG-portal-aware
applications (browsers, IDEs, Electron apps) and routes them to the
Quickshell floating file picker UI.
"""

import sys
import os
import json
import time
import threading
import signal

try:
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib
except ImportError:
    print(
        "[portal] ERROR: python-dbus / pygobject not installed.\n"
        "Install: sudo pacman -S python-dbus python-gobject\n"
        "      or: pip install dbus-python PyGObject",
        file=sys.stderr,
    )
    sys.exit(1)

HOME          = os.path.expanduser("~")
CACHE_DIR     = os.path.join(HOME, ".cache", "qs_filepicker")
REQUEST_F     = os.path.join(CACHE_DIR, "request.json")
RESPONSE_F    = os.path.join(CACHE_DIR, "response.json")
TRIGGER_F     = os.path.join(HOME, ".cache", "quickshell_plugin_trigger")
PORTAL_TIMEOUT = 300  # 5 minutes

os.makedirs(CACHE_DIR, exist_ok=True)

BUS_NAME  = "org.freedesktop.impl.portal.desktop.quickshell"
OBJ_PATH  = "/org/freedesktop/portal/desktop"
IFACE     = "org.freedesktop.impl.portal.FileChooser"


def trigger_quickshell(plugin: str) -> None:
    """Write plugin name to the Quickshell IPC trigger file."""
    try:
        with open(TRIGGER_F, "w") as f:
            f.write(plugin)
        os.utime(TRIGGER_F, None)  # touch to fire FileView watcher
    except Exception as e:
        print(f"[portal] Failed to trigger quickshell: {e}", file=sys.stderr)


def wait_for_response(timeout: int = PORTAL_TIMEOUT):
    """Block until response.json appears or timeout. Returns (code, results)."""
    # Clear old response
    try:
        os.remove(RESPONSE_F)
    except FileNotFoundError:
        pass

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(RESPONSE_F):
            try:
                with open(RESPONSE_F) as f:
                    result = json.load(f)
                if result.get("cancelled"):
                    return 1, {}  # 1 = user cancelled
                uris = result.get("uris", [])
                return 0, {
                    "uris": dbus.Array(
                        [dbus.String(u) for u in uris],
                        signature="s"
                    )
                }
            except Exception as e:
                print(f"[portal] Error reading response: {e}", file=sys.stderr)
        time.sleep(0.1)

    print("[portal] Timed out waiting for file picker response.", file=sys.stderr)
    return 2, {}  # 2 = error / timeout


def parse_mime_filter(options) -> str:
    """Extract primary MIME category hint from portal options."""
    filters = options.get("filters", [])
    for f in filters:
        try:
            patterns = f[1] if len(f) > 1 else []
            for ptype, pattern in patterns:
                if int(ptype) == 1:  # MIME type filter
                    top = str(pattern).split("/")[0]
                    if top in ("image", "video", "audio"):
                        return top
        except Exception:
            continue
    return "all"


class FileChooserBackend(dbus.service.Object):
    _lock = threading.Lock()

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)

    def _dispatch(self, app_id, title, options, mode):
        """Common handler: write request, trigger Quickshell, wait for response."""
        with self._lock:
            multiple    = bool(options.get("multiple", False))
            mime_filter = parse_mime_filter(options)

            request = {
                "mode":        mode,
                "app_id":      str(app_id),
                "title":       str(title),
                "multiple":    multiple,
                "mime_filter": mime_filter,
                "timestamp":   time.time(),
            }

            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(REQUEST_F, "w") as f:
                json.dump(request, f, indent=2)

            print(f"[portal] Request from {app_id!r}: {mode} / {mime_filter}", file=sys.stderr)
            trigger_quickshell("filepicker")

            code, results = wait_for_response()
            print(f"[portal] Response: code={code}, uris={results.get('uris', [])}", file=sys.stderr)
            return dbus.UInt32(code), results

    @dbus.service.method(IFACE, in_signature="osssa{sv}", out_signature="ua{sv}")
    def OpenFile(self, handle, app_id, parent_window, title, options):
        return self._dispatch(app_id, title, options, "open")

    @dbus.service.method(IFACE, in_signature="osssa{sv}", out_signature="ua{sv}")
    def SaveFile(self, handle, app_id, parent_window, title, options):
        return self._dispatch(app_id, title, options, "save")

    @dbus.service.method(IFACE, in_signature="osssa{sv}", out_signature="ua{sv}")
    def SaveFiles(self, handle, app_id, parent_window, title, options):
        return self._dispatch(app_id, title, options, "save-multiple")


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus  = dbus.SessionBus()
    name = dbus.service.BusName(BUS_NAME, bus=bus)
    _    = FileChooserBackend(bus, OBJ_PATH)

    loop = GLib.MainLoop()
    signal.signal(signal.SIGINT,  lambda *_: loop.quit())
    signal.signal(signal.SIGTERM, lambda *_: loop.quit())

    print(f"[portal] Quickshell FileChooser portal backend listening as {BUS_NAME}", file=sys.stderr)
    loop.run()


if __name__ == "__main__":
    main()
