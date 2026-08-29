--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

-- Persistent workspaces
for i = 1, 5 do
    hl.workspace_rule({
        workspace = tostring(i),
        persistent = true,
    })
end

-- Ref https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- "Smart gaps" / "No gaps when only"
-- uncomment all if you wish to use that.
-- hl.workspace_rule({ workspace = "w[tv1]", gaps_out = 0, gaps_in = 0 })
-- hl.workspace_rule({ workspace = "f[1]",   gaps_out = 0, gaps_in = 0 })
-- hl.window_rule({
--     name  = "no-gaps-wtv1",
--     match = { float = false, workspace = "w[tv1]" },
--     border_size = 0,
--     rounding    = 0,
-- })
-- hl.window_rule({
--     name  = "no-gaps-f1",
--     match = { float = false, workspace = "f[1]" },
--     border_size = 0,
--     rounding    = 0,
-- })

-- Example window rules that are useful
local suppressMaximizeRule = hl.window_rule({
    -- Ignore maximize requests from all apps. You'll probably like this.
    name  = "suppress-maximize-events",
    match = { class = ".*" },

    suppress_event = "maximize",
})
-- suppressMaximizeRule:set_enabled(false)

hl.window_rule({
    -- Fix some dragging issues with XWayland
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },

    no_focus = true,
})

-- Layer rules
hl.layer_rule({
    name  = "fuzzel-blur",
    match = { namespace = "fuzzel" },
    blur  = true,
})

-- Hyprland-run windowrule
hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },

    move  = "20 monitor_h-120",
    float = true,
})

-- Floating rules for Waybar utilities (btop, network)
hl.window_rule({
    name   = "float-btop",
    match  = { class = "btop" },
    float  = true,
    size   = "1000 650",
    center = true,
})

hl.window_rule({
    name   = "float-nmtui",
    match  = { class = "nmtui-floating" },
    float  = true,
    size   = "750 500",
    center = true,
})

hl.window_rule({
    name   = "float-bluetooth",
    match  = { class = "bt-floating" },
    float  = true,
    size   = "750 500",
    center = true,
})

hl.window_rule({
    name   = "float-netctl",
    match  = { class = "netctl-floating" },
    float  = true,
    size   = "850 560",
    center = true,
})

-- Scratchpad Dropdown Terminal & TUI Overlays
hl.window_rule({
    name    = "float-dropdown-terminal",
    match   = { class = "dropdown-terminal" },
    float   = true,
    size    = "1100 680",
    center  = true,
    opacity = "0.95 0.90",
})

hl.window_rule({
    name    = "float-lazygit",
    match   = { class = "lazygit-floating" },
    float   = true,
    size    = "1200 750",
    center  = true,
    opacity = "0.98 0.92",
})

hl.window_rule({
    name    = "float-lazydocker",
    match   = { class = "lazydocker-floating" },
    float   = true,
    size    = "1200 750",
    center  = true,
    opacity = "0.98 0.92",
})

hl.window_rule({
    name    = "float-zellij",
    match   = { class = "zellij-floating" },
    float   = true,
    size    = "1200 750",
    center  = true,
    opacity = "0.98 0.92",
})

-- Layer rules (Fuzzel, Wlogout)
hl.layer_rule({
    name  = "wlogout-blur",
    match = { namespace = "wlogout" },
    blur  = true,
})

-- Screenshot Annotation Tools (Swappy / Satty)
hl.window_rule({
    name   = "float-swappy",
    match  = { class = "swappy" },
    float  = true,
    center = true,
})

hl.window_rule({
    name   = "float-satty",
    match  = { class = "satty" },
    float  = true,
    center = true,
})

-- Polkit Authentication Agent Dialog
hl.window_rule({
    name   = "float-polkit",
    match  = { class = ".*polkit.*" },
    float  = true,
    center = true,
})
