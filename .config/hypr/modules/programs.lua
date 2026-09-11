---------------------
---- MY PROGRAMS ----
---------------------

-- Set programs that you use
local programs = {
    terminal    = "foot",
    fileManager = "dolphin",
    menu        = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh appmenu",
    powerMenu   = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh powermenu",
    clipboard   = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh clipboard",
    clipClear   = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh clipboard-clear",
    calc        = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh calc",
    emoji       = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh emoji",
    keybinds    = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh keybinds",
    volumeMenu  = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh volume",
    brightnessMenu = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh brightness",
    sysinfo     = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh sysinfo",
    wifiMenu    = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh wifi",
    bluetoothMenu = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh bluetooth",
    notifications = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh notifications",
    filePicker    = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh filepicker",
    filePickerImg = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh filepicker-image",
    workspaces    = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh workspaces",
    pluginManager = "bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh plugin_manager",
    browser     = "firefox",
}

return programs
