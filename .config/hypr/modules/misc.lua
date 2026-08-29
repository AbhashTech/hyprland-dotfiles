----------------
----  MISC  ----
----------------

hl.config({
    misc = {
        force_default_wallpaper = -1,    -- Set to 0 or 1 to disable the anime mascot wallpapers
        disable_hyprland_logo   = false, -- If true disables the random hyprland logo / anime girl background. :(
        focus_on_activate       = true,  -- Shift focus to application window requesting activation (e.g. notification click)
        animate_manual_resizes  = false, -- Reduces GPU overhead during manual resizing
        animate_mouse_windowdragging = false, -- Reduces latency/GPU load during window drags
        vrr                     = 1,     -- Enable Variable Refresh Rate / Adaptive Sync (0=off, 1=on, 2=fullscreen only)
    },
    render = {
        direct_scanout = true,           -- Zero-latency direct scanout for fullscreen apps and games
    },
})
