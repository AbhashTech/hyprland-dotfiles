#!/usr/bin/env python3
"""
Wofi Launcher with Outside Click Dismissal
Launches Wofi alongside a transparent fullscreen backdrop layer on Wayland/Hyprland.
Clicking outside Wofi's window dismisses Wofi immediately, while hovering or focus shifts do not.
"""

import os
import sys
import subprocess
import signal
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

try:
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell
    HAS_LAYER_SHELL = True
except Exception:
    HAS_LAYER_SHELL = False


class WofiDismissBackdrop:
    def __init__(self, wofi_args):
        self.wofi_proc = None
        self.wofi_args = wofi_args
        self.closed = False

        # If wofi is already running, toggle (kill) and exit
        if self._is_wofi_running():
            self._kill_wofi()
            sys.exit(0)

        self._create_window()
        self._launch_wofi()

    def _is_wofi_running(self):
        try:
            res = subprocess.run(["pgrep", "-x", "wofi"], capture_output=True)
            return res.returncode == 0
        except Exception:
            return False

    def _kill_wofi(self):
        try:
            subprocess.run(["pkill", "-x", "wofi"])
        except Exception:
            pass

    def _create_window(self):
        self.window = Gtk.Window()
        self.window.set_title("wofi-backdrop")
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)

        # Transparent RGBA visual
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)

        if HAS_LAYER_SHELL:
            GtkLayerShell.init_for_window(self.window)
            GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.TOP)
            GtkLayerShell.set_namespace(self.window, "wofi-backdrop")
            GtkLayerShell.set_exclusive_zone(self.window, -1)
            GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.NONE)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.BOTTOM, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.LEFT, True)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, True)
        else:
            self.window.fullscreen()

        self.window.connect("draw", self._on_draw)
        self.window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.window.connect("button-press-event", self._on_click)

        self.window.show_all()

    def _on_draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0.001)
        cr.paint()
        return False

    def _on_click(self, widget, event):
        # Click received on backdrop (outside wofi) -> dismiss
        self._cleanup()
        return True

    def _launch_wofi(self):
        cmd = ["wofi"] + (self.wofi_args if self.wofi_args else ["--show", "drun"])
        try:
            self.wofi_proc = subprocess.Popen(cmd)
            # Monitor wofi process exit
            GLib.child_watch_add(self.wofi_proc.pid, self._on_wofi_exit)
        except Exception:
            self._cleanup()

    def _on_wofi_exit(self, pid, condition):
        self._cleanup()

    def _cleanup(self):
        if self.closed:
            return
        self.closed = True
        if self.wofi_proc and self.wofi_proc.poll() is None:
            try:
                self.wofi_proc.terminate()
            except Exception:
                pass
        self._kill_wofi()
        Gtk.main_quit()


def main():
    def sig_handler(sig, frame):
        try:
            subprocess.run(["pkill", "-x", "wofi"])
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    args = sys.argv[1:]
    WofiDismissBackdrop(args)
    Gtk.main()


if __name__ == "__main__":
    main()
