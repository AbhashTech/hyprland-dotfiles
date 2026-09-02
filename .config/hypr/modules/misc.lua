----------------
----  MISC  ----
----------------

hl.config({
    misc = {
        force_default_wallpaper   = 0,     -- Set to 0 or 1 to disable the anime mascot wallpapers
        disable_hyprland_logo     = true,  -- Disables the random hyprland logo / anime background
        disable_splash_rendering  = true,  -- Disables the splash text quotes (e.g. "now with 200% more hypr and land")
        focus_on_activate         = true,  -- Shift focus to application window requesting activation (e.g. notification click)
        animate_manual_resizes  = false, -- Reduces GPU overhead during manual resizing
        animate_mouse_windowdragging = false, -- Reduces latency/GPU load during window drags
        vrr                     = 1,     -- Enable Variable Refresh Rate / Adaptive Sync (0=off, 1=on, 2=fullscreen only)
        mouse_move_enables_dpms = true,  -- Wake displays automatically on mouse movement
        key_press_enables_dpms  = true,  -- Wake displays automatically on keyboard key press
    },
    render = {
        direct_scanout = true,           -- Zero-latency direct scanout for fullscreen apps and games
    },
    xwayland = {
        force_zero_scaling = true,       -- Prevents blurry scaling in legacy X11 / XWayland apps
    },
})
