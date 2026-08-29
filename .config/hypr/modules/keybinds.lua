---------------------
---- KEYBINDINGS ----
---------------------

local programs = require("modules.programs")

local mainMod = "SUPER" -- Sets "Windows" key as main modifier

-- Example binds, see https://wiki.hypr.land/Configuring/Basics/Binds/ for more
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd(programs.terminal))
local closeWindowBind = hl.bind(mainMod .. " + C", hl.dsp.window.close())
-- closeWindowBind:set_enabled(false)
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(programs.fileManager))
hl.bind(mainMod .. " + SHIFT + E", hl.dsp.exec_cmd(programs.terminal .. " -e yazi"))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd(programs.menu))
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))    -- dwindle only
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(programs.browser or "firefox"))
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("hyprlock"))
hl.bind(mainMod .. " + ALT + L", hl.dsp.exec_cmd("hyprlock"))

-- Notifications & Quick Settings
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/waybar/scripts/notifications.py"))
hl.bind(mainMod .. " + SHIFT + N", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/waybar/scripts/notifications.py --toggle-dnd"))
hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --menu"))
hl.bind(mainMod .. " + ALT + V",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --menu"))
hl.bind(mainMod .. " + SHIFT + C", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --menu"))
hl.bind(mainMod .. " + ALT + D",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --delete"))
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/waybar/scripts/launch_waybar.sh"))

-- Workflow Utilities (Color Picker, OCR, Night Light, Calculator, Emoji)
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.exec_cmd("hyprpicker -a -f hex && notify-send -a Hyprpicker -i color-picker 'Color Picked' \"$(wl-paste)\""))
hl.bind(mainMod .. " + SHIFT + T", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/ocr_grab.py"))
hl.bind(mainMod .. " + ALT + T",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/ocr_grab.py"))
hl.bind(mainMod .. " + ALT + N",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/nightlight.py toggle"))
hl.bind(mainMod .. " + equal",     hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/quick_calc.py"))
hl.bind(mainMod .. " + ALT + C",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/quick_calc.py"))
hl.bind(mainMod .. " + period",    hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/emoji_picker.py"))
hl.bind(mainMod .. " + grave",     hl.dsp.workspace.toggle_special("magic"))


-- Move focus with mainMod + arrow keys
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- Switch workspaces with mainMod + [0-9]
-- Move active window to a workspace with mainMod + SHIFT + [0-9]
for i = 1, 10 do
    local key = i % 10 -- 10 maps to key 0
    hl.bind(mainMod .. " + " .. key,             hl.dsp.focus({ workspace = i}))
    hl.bind(mainMod .. " + SHIFT + " .. key,     hl.dsp.window.move({ workspace = i }))
end

-- Example special workspace (scratchpad)
hl.bind(mainMod .. " + S",         hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Scale window size and show dimensions on screen
local scaleScript = os.getenv("HOME") .. "/.config/hypr/scripts/scale_window.py"

-- Scale up / down proportionally
hl.bind(mainMod .. " + CTRL + equal",       hl.dsp.exec_cmd(scaleScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + CTRL + plus",        hl.dsp.exec_cmd(scaleScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + CTRL + minus",       hl.dsp.exec_cmd(scaleScript .. " scale_down"), { repeating = true })
hl.bind(mainMod .. " + CTRL + KP_Add",      hl.dsp.exec_cmd(scaleScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + CTRL + KP_Subtract", hl.dsp.exec_cmd(scaleScript .. " scale_down"), { repeating = true })

-- Directional resize (Arrow keys and Vim keys)
hl.bind(mainMod .. " + CTRL + right", hl.dsp.exec_cmd(scaleScript .. " right"), { repeating = true })
hl.bind(mainMod .. " + CTRL + left",  hl.dsp.exec_cmd(scaleScript .. " left"),  { repeating = true })
hl.bind(mainMod .. " + CTRL + up",    hl.dsp.exec_cmd(scaleScript .. " up"),    { repeating = true })
hl.bind(mainMod .. " + CTRL + down",  hl.dsp.exec_cmd(scaleScript .. " down"),  { repeating = true })
hl.bind(mainMod .. " + CTRL + L",     hl.dsp.exec_cmd(scaleScript .. " right"), { repeating = true })
hl.bind(mainMod .. " + CTRL + H",     hl.dsp.exec_cmd(scaleScript .. " left"),  { repeating = true })
hl.bind(mainMod .. " + CTRL + K",     hl.dsp.exec_cmd(scaleScript .. " up"),    { repeating = true })
hl.bind(mainMod .. " + CTRL + J",     hl.dsp.exec_cmd(scaleScript .. " down"),  { repeating = true })

-- Display active window size on screen
hl.bind(mainMod .. " + CTRL + I", hl.dsp.exec_cmd(scaleScript .. " show"))
hl.bind(mainMod .. " + CTRL + 0", hl.dsp.exec_cmd(scaleScript .. " show"))

-- Screen Resolution & Display Scaling Manager
local resScript = os.getenv("HOME") .. "/.config/hypr/scripts/resolution_menu.py"
hl.bind(mainMod .. " + SHIFT + R",       hl.dsp.exec_cmd(resScript))
hl.bind(mainMod .. " + SHIFT + D",       hl.dsp.exec_cmd(resScript))
hl.bind(mainMod .. " + ALT + equal",     hl.dsp.exec_cmd(resScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + ALT + plus",      hl.dsp.exec_cmd(resScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + ALT + minus",     hl.dsp.exec_cmd(resScript .. " scale_down"), { repeating = true })
hl.bind(mainMod .. " + ALT + 0",         hl.dsp.exec_cmd(resScript .. " show"))

-- Direct Screen Scale Presets (1.0x, 1.25x, 1.5x, 1.75x, 2.0x)
hl.bind(mainMod .. " + ALT + 1",         hl.dsp.exec_cmd(resScript .. " 1.0"))
hl.bind(mainMod .. " + ALT + BackSpace", hl.dsp.exec_cmd(resScript .. " 1.0")) -- Reset to 1.0x (100%)
hl.bind(mainMod .. " + ALT + 2",         hl.dsp.exec_cmd(resScript .. " 1.25"))
hl.bind(mainMod .. " + ALT + 3",         hl.dsp.exec_cmd(resScript .. " 1.50"))
hl.bind(mainMod .. " + ALT + 4",         hl.dsp.exec_cmd(resScript .. " 1.75"))
hl.bind(mainMod .. " + ALT + 5",         hl.dsp.exec_cmd(resScript .. " 2.00"))

-- Volume Control & Audio Manager
local volumeScript = os.getenv("HOME") .. "/.config/hypr/scripts/volume_control.py"
hl.bind("XF86AudioRaiseVolume",         hl.dsp.exec_cmd(volumeScript .. " up"),       { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume",         hl.dsp.exec_cmd(volumeScript .. " down"),     { locked = true, repeating = true })
hl.bind("XF86AudioMute",                hl.dsp.exec_cmd(volumeScript .. " mute"),     { locked = true, repeating = true })
hl.bind("XF86AudioMicMute",             hl.dsp.exec_cmd(volumeScript .. " mic-mute"), { locked = true, repeating = true })
hl.bind("SHIFT + XF86AudioRaiseVolume", hl.dsp.exec_cmd(volumeScript .. " mic-up"),   { locked = true, repeating = true })
hl.bind("SHIFT + XF86AudioLowerVolume", hl.dsp.exec_cmd(volumeScript .. " mic-down"), { locked = true, repeating = true })

-- Interactive Audio Menu & Device Switcher
hl.bind(mainMod .. " + SHIFT + A", hl.dsp.exec_cmd(volumeScript .. " menu"))
hl.bind(mainMod .. " + ALT + A",   hl.dsp.exec_cmd(volumeScript .. " menu"))

-- Screen Brightness Control & OSD
local brightnessScript = os.getenv("HOME") .. "/.config/hypr/scripts/brightness_control.py"
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd(brightnessScript .. " up"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(brightnessScript .. " down"), { locked = true, repeating = true })

-- External monitor brightness (via ddcutil / brightness_control)
hl.bind("SHIFT + XF86MonBrightnessUp",         hl.dsp.exec_cmd(brightnessScript .. " ddc-up"),   { locked = true, repeating = true })
hl.bind("SHIFT + XF86MonBrightnessDown",       hl.dsp.exec_cmd(brightnessScript .. " ddc-down"), { locked = true, repeating = true })
hl.bind(mainMod .. " + XF86MonBrightnessUp",   hl.dsp.exec_cmd(brightnessScript .. " ddc-up"),   { locked = true, repeating = true })
hl.bind(mainMod .. " + XF86MonBrightnessDown", hl.dsp.exec_cmd(brightnessScript .. " ddc-down"), { locked = true, repeating = true })

-- Interactive Brightness Menu
hl.bind(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd(brightnessScript .. " menu"))
hl.bind(mainMod .. " + ALT + B",   hl.dsp.exec_cmd(brightnessScript .. " menu"))

-- Requires playerctl
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- Screenshot & Screen Recording Utility
local captureScript = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/screen_capture.py"

-- Screenshots
hl.bind("Print",               hl.dsp.exec_cmd(captureScript .. " screenshot --area"))     -- Area / Selection
hl.bind("SHIFT + Print",       hl.dsp.exec_cmd(captureScript .. " screenshot --full"))     -- Full screen
hl.bind("ALT + Print",         hl.dsp.exec_cmd(captureScript .. " screenshot --window"))   -- Active window
hl.bind("CTRL + Print",        hl.dsp.exec_cmd(captureScript .. " screenshot --edit"))     -- Area + Annotate (swappy/satty)
hl.bind(mainMod .. " + Print", hl.dsp.exec_cmd(captureScript .. " menu"))                 -- Interactive Capture Menu

-- Screen Recording
hl.bind(mainMod .. " + ALT + R",   hl.dsp.exec_cmd(captureScript .. " toggle"))            -- Toggle Area Recording
hl.bind(mainMod .. " + SHIFT + R", hl.dsp.exec_cmd(captureScript .. " stop"))              -- Stop Recording


