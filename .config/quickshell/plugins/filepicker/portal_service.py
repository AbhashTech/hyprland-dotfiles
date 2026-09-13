#!/usr/bin/env python3
"""
Quickshell File Picker - XDG Desktop Portal Backend
Registers as: org.freedesktop.impl.portal.desktop.quickshell
Implements: org.freedesktop.impl.portal.FileChooser

This service intercepts file open/save dialogs from XDG-portal-aware
applications (browsers, IDEs, Electron apps) and routes them to the
Quickshell floating file picker UI.

Key design: D-Bus method calls are dispatched on the GLib main thread.
We use async_callbacks to avoid blocking the mainloop — each request
is handled on a background thread, and the D-Bus reply is sent when done.
"""

import sys
import os
import json
import time
import subprocess
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

# Serialise concurrent portal calls (one file picker at a time)
_request_lock = threading.Lock()


def trigger_quickshell(plugin: str) -> None:
    """Trigger Quickshell via native IPC or atomic trigger file write."""
    try:
        # Try quickshell native IPC first
        res = subprocess.run(
            ["quickshell", "ipc", "call", "pluginManager", "toggle", plugin],
            capture_output=True,
            timeout=1
        )
        if res.returncode == 0:
            return
    except Exception:
        pass

    try:
        tmp_f = TRIGGER_F + ".tmp"
        with open(tmp_f, "w") as f:
            f.write(f"{plugin} {time.time_ns()}\n")
        os.replace(tmp_f, TRIGGER_F)
    except Exception as e:
        print(f"[portal] Failed to trigger quickshell: {e}", file=sys.stderr)


def wait_for_response(timeout: int = PORTAL_TIMEOUT):
    """Block (on background thread) until response.json appears or timeout."""
    # Clear old response first
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


def parse_current_folder(options) -> str:
    """Extract suggested folder path from portal options if provided."""
    cf = options.get("current_folder")
    if not cf:
        return ""
    if isinstance(cf, (bytes, bytearray)):
        return cf.decode("utf-8", errors="replace").rstrip("\x00")
    if isinstance(cf, (list, tuple, dbus.Array)):
        try:
            return bytes(cf).decode("utf-8", errors="replace").rstrip("\x00")
        except Exception:
            return ""
    return str(cf).rstrip("\x00")


class FileChooserBackend(dbus.service.Object):

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)

    def _dispatch_async(self, app_id, title, options, mode, return_cb, error_cb):
        """Run in a background thread: write request, trigger QS, wait, reply."""
        with _request_lock:
            multiple    = bool(options.get("multiple", False))
            directory   = bool(options.get("directory", False))
            if not directory:
                title_lower = str(title).lower()
                if any(k in title_lower for k in ("workspace", "folder", "directory")):
                    directory = True

            mime_filter    = parse_mime_filter(options)
            current_folder = parse_current_folder(options)
            accept_label   = str(options.get("accept_label", ""))

            request = {
                "mode":           mode,
                "directory":      directory,
                "app_id":         str(app_id),
                "title":          str(title),
                "accept_label":   accept_label,
                "multiple":       multiple,
                "mime_filter":    mime_filter,
                "current_name":   str(options.get("current_name", "")),
                "current_folder": current_folder,
                "timestamp":      time.time(),
            }

            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(REQUEST_F, "w") as f:
                json.dump(request, f, indent=2)

            print(f"[portal] Request from {app_id!r}: {mode} / dir={directory} / {mime_filter}", file=sys.stderr)
            trigger_quickshell("filepicker-portal")

            code, results = wait_for_response()
            print(f"[portal] Response: code={code}, uris={results.get('uris', [])}", file=sys.stderr)

            # Schedule the D-Bus reply back on the main GLib loop (thread-safe)
            GLib.idle_add(return_cb, dbus.UInt32(code), results)

    @dbus.service.method(
        IFACE,
        in_signature="osssa{sv}",
        out_signature="ua{sv}",
        async_callbacks=("return_cb", "error_cb"),
    )
    def OpenFile(self, handle, app_id, parent_window, title, options,
                 return_cb=None, error_cb=None):
        t = threading.Thread(
            target=self._dispatch_async,
            args=(app_id, title, options, "open", return_cb, error_cb),
            daemon=True,
        )
        t.start()

    @dbus.service.method(
        IFACE,
        in_signature="osssa{sv}",
        out_signature="ua{sv}",
        async_callbacks=("return_cb", "error_cb"),
    )
    def SaveFile(self, handle, app_id, parent_window, title, options,
                 return_cb=None, error_cb=None):
        t = threading.Thread(
            target=self._dispatch_async,
            args=(app_id, title, options, "save", return_cb, error_cb),
            daemon=True,
        )
        t.start()

    @dbus.service.method(
        IFACE,
        in_signature="osssa{sv}",
        out_signature="ua{sv}",
        async_callbacks=("return_cb", "error_cb"),
    )
    def SaveFiles(self, handle, app_id, parent_window, title, options,
                  return_cb=None, error_cb=None):
        t = threading.Thread(
            target=self._dispatch_async,
            args=(app_id, title, options, "save-multiple", return_cb, error_cb),
            daemon=True,
        )
        t.start()


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    if hasattr(GLib, "threads_init"):
        try:
            GLib.threads_init()
        except Exception:
            pass

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
