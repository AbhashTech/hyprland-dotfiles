-----------------------------------------------------------------------------
---- HYPRLAND MODULAR KEYBINDINGS CONFIGURATION ----
-----------------------------------------------------------------------------

local programs = require("modules.programs")
local mainMod = "SUPER" -- Sets "Windows / Meta" key as main modifier

-- =============================================================================
-- 🖥️ Core Applications, System & Navigation
-- =============================================================================

-- Open Kitty Terminal
hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd(programs.terminal))

-- Close Active Window
hl.bind(mainMod .. " + C", hl.dsp.window.close())

-- Open Power & Session Menu
local powerMenuScript = os.getenv("HOME") .. "/.config/waybar/scripts/power-menu.sh"
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("bash " .. powerMenuScript))
hl.bind(mainMod .. " + Escape", hl.dsp.exec_cmd("bash " .. powerMenuScript))

-- Open Dolphin File Manager
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(programs.fileManager))

-- Open Yazi File Manager in Kitty
hl.bind(mainMod .. " + SHIFT + E", hl.dsp.exec_cmd(programs.terminal .. " -e yazi"))

-- Open Floating Lazygit TUI
hl.bind(mainMod .. " + G", hl.dsp.exec_cmd(programs.terminal .. " --class=lazygit-floating -e lazygit"))

-- Open Floating Lazydocker TUI
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd(programs.terminal .. " --class=lazydocker-floating -e lazydocker"))

-- Open Floating Zellij Session
hl.bind(mainMod .. " + SHIFT + Z", hl.dsp.exec_cmd(programs.terminal .. " --class=zellij-floating -e zellij"))

-- Toggle Window Floating Mode
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))

-- Open Fuzzel Application Launcher
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd(programs.menu))

-- Toggle Pseudo Tiling
hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())

-- Toggle Layout Split Orientation
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))

-- Launch Firefox Browser
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(programs.browser or "firefox"))

-- Lock Screen Immediately
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("hyprlock"))
hl.bind(mainMod .. " + ALT + L", hl.dsp.exec_cmd("hyprlock"))

-- Toggle Dropdown Scratchpad Terminal
hl.bind(mainMod .. " + grave", hl.dsp.exec_cmd(programs.terminal .. " --class=dropdown-terminal"))

-- Open Keyboard Shortcuts Cheat Sheet
local keybindViewer = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/keybinds_viewer.py"
hl.bind(mainMod .. " + slash", hl.dsp.exec_cmd(keybindViewer))
hl.bind(mainMod .. " + question", hl.dsp.exec_cmd(keybindViewer))
hl.bind(mainMod .. " + F1", hl.dsp.exec_cmd(keybindViewer))

-- Keyboard Layout Switcher & Manager
local kbLayoutScript = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/keyboard_layout.py"
hl.bind(mainMod .. " + space", hl.dsp.exec_cmd(kbLayoutScript .. " --next"))
hl.bind(mainMod .. " + SHIFT + K", hl.dsp.exec_cmd(kbLayoutScript .. " --menu"))
hl.bind(mainMod .. " + ALT + K", hl.dsp.exec_cmd(kbLayoutScript .. " --add-menu"))

-- =============================================================================
-- 🔔 Notifications & Quick Settings
-- =============================================================================

-- Toggle Notifications History Center
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/waybar/scripts/notifications.py"))

-- Toggle Do-Not-Disturb (DND) Mode
hl.bind(mainMod .. " + SHIFT + N", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/waybar/scripts/notifications.py --toggle-dnd"))

-- Open Clipboard History Browser
hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --menu"))
hl.bind(mainMod .. " + ALT + V",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --menu"))
hl.bind(mainMod .. " + SHIFT + C", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --menu"))

-- Open Clipboard Delete / Wipe Menu
hl.bind(mainMod .. " + ALT + D",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/clipboard_manager.py --delete"))

-- Toggle Waybar Bar
hl.bind(mainMod .. " + SHIFT + W", hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/waybar/scripts/launch_waybar.sh --toggle"))

-- Cycle Desktop Wallpaper (Random)
local wallpaperScript = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/wallpaper_switcher.py"
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd(wallpaperScript .. " --random"))
hl.bind(mainMod .. " + ALT + W", hl.dsp.exec_cmd(wallpaperScript .. " --menu"))

-- =============================================================================
-- ⚡ Productivity & Workflow Utilities
-- =============================================================================

-- Pick Color from Screen & Copy Hex
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.exec_cmd("hyprpicker -a -f hex && notify-send -a Hyprpicker -i color-picker 'Color Picked' \"$(wl-paste)\""))

-- Theme Switcher & Palette Manager
local themeScript = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/theme_switcher.py"
hl.bind(mainMod .. " + T",         hl.dsp.exec_cmd(themeScript .. " --menu"))
hl.bind(mainMod .. " + ALT + T",   hl.dsp.exec_cmd(themeScript .. " --gui"))
hl.bind(mainMod .. " + CTRL + T",  hl.dsp.exec_cmd(themeScript .. " --next"))

-- Screen OCR: Grab Text to Clipboard
hl.bind(mainMod .. " + SHIFT + T", hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/ocr_grab.py"))


-- Night Light: Toggle Blue-Light Filter
hl.bind(mainMod .. " + ALT + N",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/nightlight.py toggle"))

-- Quick Math Calculator
hl.bind(mainMod .. " + equal",     hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/quick_calc.py"))
hl.bind(mainMod .. " + ALT + C",   hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/quick_calc.py"))

-- Search & Paste Emojis
hl.bind(mainMod .. " + period",    hl.dsp.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/emoji_picker.py"))

-- Application Shortcut & Menu Launcher Creator
local appShortcutCreator = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/app_shortcut_creator.py"
hl.bind(mainMod .. " + ALT + S",   hl.dsp.exec_cmd(appShortcutCreator))

-- =============================================================================
-- 🗂️ Workspaces & Window Focus Navigation
-- =============================================================================

-- Focus Window to the Left
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))

-- Focus Window to the Right
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))

-- Focus Window Upwards
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))

-- Focus Window Downwards
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- Switch to Workspace 1–10 / Move Window
for i = 1, 10 do
    local key = i % 10 -- 10 maps to key 0
    hl.bind(mainMod .. " + " .. key,             hl.dsp.focus({ workspace = i}))
    hl.bind(mainMod .. " + SHIFT + " .. key,     hl.dsp.window.move({ workspace = i }))
end

-- Toggle Magic Scratchpad Workspace
hl.bind(mainMod .. " + S",         hl.dsp.workspace.toggle_special("magic"))

-- Move Window to Magic Scratchpad
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll to Next Workspace
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))

-- Scroll to Previous Workspace
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Drag & Move Window (Mouse)
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })

-- Drag & Resize Window (Mouse)
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- =============================================================================
-- 📐 Window Resizing & Screen Scaling
-- =============================================================================

local scaleScript = os.getenv("HOME") .. "/.config/hypr/scripts/scale_window.py"

-- Scale Window Up (+40px) with OSD
hl.bind(mainMod .. " + CTRL + equal",       hl.dsp.exec_cmd(scaleScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + CTRL + plus",        hl.dsp.exec_cmd(scaleScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + CTRL + KP_Add",      hl.dsp.exec_cmd(scaleScript .. " scale_up"),   { repeating = true })

-- Scale Window Down (-40px) with OSD
hl.bind(mainMod .. " + CTRL + minus",       hl.dsp.exec_cmd(scaleScript .. " scale_down"), { repeating = true })
hl.bind(mainMod .. " + CTRL + KP_Subtract", hl.dsp.exec_cmd(scaleScript .. " scale_down"), { repeating = true })

-- Resize Width Right (+40px)
hl.bind(mainMod .. " + CTRL + right", hl.dsp.exec_cmd(scaleScript .. " right"), { repeating = true })
hl.bind(mainMod .. " + CTRL + L",     hl.dsp.exec_cmd(scaleScript .. " right"), { repeating = true })

-- Resize Width Left (-40px)
hl.bind(mainMod .. " + CTRL + left",  hl.dsp.exec_cmd(scaleScript .. " left"),  { repeating = true })
hl.bind(mainMod .. " + CTRL + H",     hl.dsp.exec_cmd(scaleScript .. " left"),  { repeating = true })

-- Resize Height Up (-40px)
hl.bind(mainMod .. " + CTRL + up",    hl.dsp.exec_cmd(scaleScript .. " up"),    { repeating = true })
hl.bind(mainMod .. " + CTRL + K",     hl.dsp.exec_cmd(scaleScript .. " up"),    { repeating = true })

-- Resize Height Down (+40px)
hl.bind(mainMod .. " + CTRL + down",  hl.dsp.exec_cmd(scaleScript .. " down"),  { repeating = true })
hl.bind(mainMod .. " + CTRL + J",     hl.dsp.exec_cmd(scaleScript .. " down"),  { repeating = true })

-- Show Active Window Dimensions OSD
hl.bind(mainMod .. " + CTRL + I", hl.dsp.exec_cmd(scaleScript .. " show"))
hl.bind(mainMod .. " + CTRL + 0", hl.dsp.exec_cmd(scaleScript .. " show"))

-- Resolution & Scaling Menu
local resScript = os.getenv("HOME") .. "/.config/hypr/scripts/resolution_menu.py"
hl.bind(mainMod .. " + SHIFT + R",       hl.dsp.exec_cmd(resScript))
hl.bind(mainMod .. " + SHIFT + D",       hl.dsp.exec_cmd(resScript))
hl.bind(mainMod .. " + ALT + equal",     hl.dsp.exec_cmd(resScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + ALT + plus",      hl.dsp.exec_cmd(resScript .. " scale_up"),   { repeating = true })
hl.bind(mainMod .. " + ALT + minus",     hl.dsp.exec_cmd(resScript .. " scale_down"), { repeating = true })
hl.bind(mainMod .. " + ALT + 0",         hl.dsp.exec_cmd(resScript .. " show"))

-- Set Display Scale to 1.0x (100%)
hl.bind(mainMod .. " + ALT + 1",         hl.dsp.exec_cmd(resScript .. " 1.0"))
hl.bind(mainMod .. " + ALT + BackSpace", hl.dsp.exec_cmd(resScript .. " 1.0"))

-- Set Display Scale to 1.25x (125%)
hl.bind(mainMod .. " + ALT + 2",         hl.dsp.exec_cmd(resScript .. " 1.25"))

-- Set Display Scale to 1.50x (150%)
hl.bind(mainMod .. " + ALT + 3",         hl.dsp.exec_cmd(resScript .. " 1.50"))

-- Set Display Scale to 1.75x (175%)
hl.bind(mainMod .. " + ALT + 4",         hl.dsp.exec_cmd(resScript .. " 1.75"))

-- Set Display Scale to 2.00x (200%)
hl.bind(mainMod .. " + ALT + 5",         hl.dsp.exec_cmd(resScript .. " 2.00"))

-- =============================================================================
-- 🔊 Audio & Media Controls
-- =============================================================================

local volumeScript = os.getenv("HOME") .. "/.config/hypr/scripts/volume_control.py"

-- Speaker Volume Up (+5%) with OSD
hl.bind("XF86AudioRaiseVolume",         hl.dsp.exec_cmd(volumeScript .. " up"),       { locked = true, repeating = true })

-- Speaker Volume Down (-5%) with OSD
hl.bind("XF86AudioLowerVolume",         hl.dsp.exec_cmd(volumeScript .. " down"),     { locked = true, repeating = true })

-- Toggle Speaker Mute with OSD
hl.bind("XF86AudioMute",                hl.dsp.exec_cmd(volumeScript .. " mute"),     { locked = true, repeating = true })

-- Toggle Mic Mute with OSD
hl.bind("XF86AudioMicMute",             hl.dsp.exec_cmd(volumeScript .. " mic-mute"), { locked = true, repeating = true })

-- Mic Volume Up (+5%)
hl.bind("SHIFT + XF86AudioRaiseVolume", hl.dsp.exec_cmd(volumeScript .. " mic-up"),   { locked = true, repeating = true })

-- Mic Volume Down (-5%)
hl.bind("SHIFT + XF86AudioLowerVolume", hl.dsp.exec_cmd(volumeScript .. " mic-down"), { locked = true, repeating = true })

-- Audio Device Switcher Menu
hl.bind(mainMod .. " + SHIFT + A", hl.dsp.exec_cmd(volumeScript .. " menu"))
hl.bind(mainMod .. " + ALT + A",   hl.dsp.exec_cmd(volumeScript .. " menu"))

-- Skip to Next Track
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })

-- Toggle Play / Pause
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })

-- Return to Previous Track
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- =============================================================================
-- ☀️ Screen Brightness & External DDC Controls
-- =============================================================================

local brightnessScript = os.getenv("HOME") .. "/.config/hypr/scripts/brightness_control.py"

-- Laptop Brightness Up (+5%) with OSD
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd(brightnessScript .. " up"),   { locked = true, repeating = true })

-- Laptop Brightness Down (-5%) with OSD
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(brightnessScript .. " down"), { locked = true, repeating = true })

-- External Monitor Brightness Up (DDC)
hl.bind("SHIFT + XF86MonBrightnessUp",         hl.dsp.exec_cmd(brightnessScript .. " ddc-up"),   { locked = true, repeating = true })
hl.bind(mainMod .. " + XF86MonBrightnessUp",   hl.dsp.exec_cmd(brightnessScript .. " ddc-up"),   { locked = true, repeating = true })

-- External Monitor Brightness Down (DDC)
hl.bind("SHIFT + XF86MonBrightnessDown",       hl.dsp.exec_cmd(brightnessScript .. " ddc-down"), { locked = true, repeating = true })
hl.bind(mainMod .. " + XF86MonBrightnessDown", hl.dsp.exec_cmd(brightnessScript .. " ddc-down"), { locked = true, repeating = true })

-- Brightness Presets Menu
hl.bind(mainMod .. " + SHIFT + B", hl.dsp.exec_cmd(brightnessScript .. " menu"))
hl.bind(mainMod .. " + ALT + B",   hl.dsp.exec_cmd(brightnessScript .. " menu"))

-- =============================================================================
-- 📸 Screenshots & Screen Recording
-- =============================================================================

local captureScript = "python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/screen_capture.py"

-- Capture Area / Selection to File & Clipboard
hl.bind("Print",               hl.dsp.exec_cmd(captureScript .. " screenshot --area"))

-- Capture Full Screen to File & Clipboard
hl.bind("SHIFT + Print",       hl.dsp.exec_cmd(captureScript .. " screenshot --full"))

-- Capture Active Window to File & Clipboard
hl.bind("ALT + Print",         hl.dsp.exec_cmd(captureScript .. " screenshot --window"))

-- Capture Area & Annotate (Swappy)
hl.bind("CTRL + Print",        hl.dsp.exec_cmd(captureScript .. " screenshot --edit"))

-- Interactive Screen Capture Dashboard
hl.bind(mainMod .. " + Print", hl.dsp.exec_cmd(captureScript .. " menu"))

-- Toggle Video Screen Recording (wf-recorder)
hl.bind(mainMod .. " + ALT + R",   hl.dsp.exec_cmd(captureScript .. " toggle"))

-- Stop Active Screen Recording
hl.bind(mainMod .. " + SHIFT + R", hl.dsp.exec_cmd(captureScript .. " stop"))
