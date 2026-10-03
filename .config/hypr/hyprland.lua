-- =============================================================================
-- Hyprland Main Configuration
-- =============================================================================
-- Documentation: https://wiki.hypr.land/Configuring/Start/

-- Ensure config directory is in Lua package path for modular requires
local config_dir = os.getenv("HOME") .. "/.config/hypr"
package.path = config_dir .. "/?.lua;" .. config_dir .. "/?/init.lua;" .. package.path

-- Unload cached modules to ensure live reload reflects all edits on disk
for _, mod in ipairs({
  "modules.env", "modules.monitors", "modules.programs", "modules.autostart",
  "modules.appearance", "modules.animations", "modules.layouts", "modules.misc",
  "modules.input", "modules.keybinds", "modules.rules", "modules.permissions"
}) do
  package.loaded[mod] = nil
end

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

-- Load self-descriptive user personal overrides (untracked in dotfiles)
local user_modules = {
  "user.env",
  "user.monitors",
  "user.input",
  "user.keybinds",
  "user.rules",
  "user.autostart",
  "user.workspaces",
}
for _, mod in ipairs(user_modules) do
  pcall(require, mod)
end

