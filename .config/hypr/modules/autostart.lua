-------------------
---- AUTOSTART ----
-------------------

-- See https://wiki.hypr.land/Configuring/Basics/Autostart/

-- Autostart necessary processes (like notifications daemons, status bars, etc.)
-- Or execute your favorite apps at launch like this:
--
-- local programs = require("modules.programs")
-- hl.on("hyprland.start", function () 
--   hl.exec_cmd(programs.terminal)
--   hl.exec_cmd("nm-applet")
--   hl.exec_cmd("waybar & hyprpaper & firefox")
-- end)

hl.on("hyprland.start", function ()
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("mako")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("systemctl --user start hyprpolkitagent 2>/dev/null || /usr/lib/polkit-kde-authentication-agent-1 &")
    hl.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/waybar/scripts/launch_waybar.sh --restart")
    hl.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --daemon")
    hl.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/monitor_workspace_manager.py --daemon")
    hl.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/wallpaper_switcher.py --init")
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP 2>/dev/null || true")
    hl.exec_cmd("xsettingsd &")
    hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")
end)
