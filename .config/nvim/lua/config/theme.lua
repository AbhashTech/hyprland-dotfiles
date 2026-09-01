-- =============================================================================
-- Dynamic Theme Synchronization with Universal Desktop Theme Manager
-- =============================================================================

local M = {}

-- Safe require helper
local function get_theme_colors()
  package.loaded["theme_colors"] = nil
  local status, data = pcall(require, "theme_colors")
  if status and type(data) == "table" then
    return data
  end

  -- Fallback defaults (Catppuccin Mocha)
  return {
    id = "catppuccin-mocha",
    name = "Catppuccin Mocha",
    type = "dark",
    colorscheme = "catppuccin",
    flavour = "mocha",
    background = "dark",
    colors = {
      base = "#1e1e2e",
      mantle = "#181825",
      crust = "#11111b",
      surface0 = "#313244",
      surface1 = "#45475a",
      surface2 = "#585b70",
      overlay0 = "#6c7086",
      text = "#cdd6f4",
      accent = "#cba6f7",
      blue = "#89b4fa",
      green = "#a6e3a1",
      yellow = "#f9e2af",
      peach = "#fab387",
      red = "#f38ba8",
      mauve = "#cba6f7",
      teal = "#94e2d5",
    },
  }
end

function M.apply_highlights(theme_data)
  local c = theme_data.colors or {}
  local accent = c.accent or "#cba6f7"
  local blue = c.blue or "#89b4fa"
  local teal = c.teal or "#94e2d5"
  local green = c.green or "#a6e3a1"
  local peach = c.peach or "#fab387"
  local yellow = c.yellow or "#f9e2af"
  local text = c.text or "#cdd6f4"
  local surface0 = c.surface0 or "#313244"
  local mantle = c.mantle or "#181825"

  -- Custom startup logo & zen branding highlights
  vim.api.nvim_set_hl(0, "ZenLogoBorder", { fg = accent, bold = true })
  vim.api.nvim_set_hl(0, "ZenLogoPins",   { fg = blue, bold = true })
  vim.api.nvim_set_hl(0, "ZenLogoPerson", { fg = teal, bold = true })
  vim.api.nvim_set_hl(0, "ZenLogoHands",  { fg = green, bold = true })
  vim.api.nvim_set_hl(0, "ZenLogoDot",    { fg = yellow, bold = true })
  vim.api.nvim_set_hl(0, "ZenLogoText",   { fg = text, bold = true })

  -- General UI Accent refinements
  vim.api.nvim_set_hl(0, "FloatBorder",   { fg = accent, bg = mantle })
  vim.api.nvim_set_hl(0, "NormalFloat",   { bg = mantle })
  vim.api.nvim_set_hl(0, "TelescopeBorder", { fg = accent, bg = mantle })
  vim.api.nvim_set_hl(0, "TelescopePromptBorder", { fg = accent, bg = surface0 })
  vim.api.nvim_set_hl(0, "TelescopeTitle", { fg = mantle, bg = accent, bold = true })
end

function M.sync(notify)
  local theme_data = get_theme_colors()
  local bg = theme_data.background or "dark"
  vim.o.background = bg

  local scheme = theme_data.colorscheme or "catppuccin"

  -- If catppuccin, set flavour first
  if scheme == "catppuccin" and theme_data.flavour then
    vim.g.catppuccin_flavour = theme_data.flavour
  end

  local ok, _ = pcall(vim.cmd.colorscheme, scheme)
  if not ok then
    -- Fallback to default or catppuccin
    pcall(vim.cmd.colorscheme, "catppuccin-mocha")
  end

  M.apply_highlights(theme_data)

  if notify then
    vim.notify(
      string.format("Synced theme: %s (%s)", theme_data.name or theme_data.id, scheme),
      vim.log.levels.INFO,
      { title = "Desktop Theme Manager" }
    )
  end
end

function M.setup()
  -- Initial apply
  M.sync(false)

  -- User command
  vim.api.nvim_create_user_command("ThemeSync", function()
    M.sync(true)
  end, { desc = "Synchronize Neovim theme with active desktop palette" })

  -- Background file watcher on ~/.cache/current_theme and theme_colors.lua
  local cache_theme = vim.fn.expand("~/.cache/current_theme")
  local uv = vim.uv or vim.loop
  if uv and uv.new_fs_event then
    local handle = uv.new_fs_event()
    local cache_dir = vim.fn.expand("~/.cache")
    if vim.fn.isdirectory(cache_dir) == 1 then
      pcall(function()
        handle:start(cache_dir, {}, vim.schedule_wrap(function(err, filename, events)
          if filename == "current_theme" or filename == "hypr_theme_state.json" then
            M.sync(false)
          end
        end))
      end)
    end
  end
end

return M
