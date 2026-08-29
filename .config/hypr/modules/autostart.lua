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
    hl.exec_cmd("systemctl --user start hyprpolkitagent || /usr/lib/polkit-kde-authentication-agent-1 || /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &")
    hl.exec_cmd(os.getenv("HOME") .. "/.config/waybar/scripts/launch_waybar.sh")
    hl.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --daemon")
end)
