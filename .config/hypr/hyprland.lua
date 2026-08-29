-- =============================================================================
-- Hyprland Main Configuration
-- =============================================================================
-- Documentation: https://wiki.hypr.land/Configuring/Start/

-- Ensure config directory is in Lua package path for modular requires
local config_dir = os.getenv("HOME") .. "/.config/hypr"
package.path = config_dir .. "/?.lua;" .. config_dir .. "/?/init.lua;" .. package.path

-- Load configuration modules
require("modules.env")
require("modules.monitors")
require("modules.programs")
require("modules.autostart")
require("modules.appearance")
require("modules.animations")
require("modules.layouts")
require("modules.misc")
require("modules.input")
require("modules.keybinds")
require("modules.rules")
require("modules.permissions")
