-- =============================================================================
-- Modern Neovim Configuration with Dynamic Desktop Theme Manager Integration
-- =============================================================================

-- Map leader key to Space before loading plugins
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- Load core modules
require("config.options")
require("config.keymaps")
require("config.autocmds")
require("config.theme").setup()

-- Bootstrap and load lazy.nvim plugins
require("config.lazy")
