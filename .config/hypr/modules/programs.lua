---------------------
---- MY PROGRAMS ----
---------------------

-- Set programs that you use
local programs = {
    terminal    = "kitty",
    fileManager = "dolphin",
    menu        = "bash " .. os.getenv("HOME") .. "/.config/hypr/scripts/fuzzel_launcher.sh",
    browser     = "firefox",
}

return programs
