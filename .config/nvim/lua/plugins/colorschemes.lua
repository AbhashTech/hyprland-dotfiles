-- =============================================================================
-- Colorschemes Suite for Seamless Desktop Theme Integration
-- =============================================================================

return {
  -- Catppuccin (Mocha, Macchiato, Frappe, Latte)
  {
    "catppuccin/nvim",
    name = "catppuccin",
    priority = 1000,
    opts = {
      flavour = "mocha",
      transparent_background = false,
      term_colors = true,
      integrations = {
        alpha = true,
        cmp = true,
        gitsigns = true,
        nvimtree = true,
        treesitter = true,
        telescope = { enabled = true },
        which_key = true,
        bufferline = true,
        mason = true,
        native_lsp = {
          enabled = true,
          underlines = {
            errors = { "undercurl" },
            hints = { "undercurl" },
            warnings = { "undercurl" },
            information = { "undercurl" },
          },
        },
      },
    },
  },

  -- Tokyo Night (Night, Storm, Day)
  {
    "folke/tokyonight.nvim",
    lazy = true,
    opts = {
      style = "night",
      transparent = false,
      terminal_colors = true,
    },
  },

  -- Gruvbox (Dark, Light)
  {
    "ellisonleao/gruvbox.nvim",
    lazy = true,
    opts = {
      contrast = "hard",
      transparent_mode = false,
    },
  },

  -- Nord
  {
    "shaunsingh/nord.nvim",
    lazy = true,
  },

  -- Rose Pine (Main, Moon, Dawn)
  {
    "rose-pine/neovim",
    name = "rose-pine",
    lazy = true,
    opts = {
      variant = "main",
      dark_variant = "main",
      styles = {
        transparency = false,
      },
    },
  },

  -- Everforest
  {
    "neanias/everforest-nvim",
    lazy = true,
    opts = {
      background = "hard",
      transparent_background_level = 0,
    },
  },

  -- OneDark & OneLight
  {
    "navarasu/onedark.nvim",
    lazy = true,
    opts = {
      style = "dark",
    },
  },

  -- Dracula
  {
    "Mofiqul/dracula.nvim",
    lazy = true,
  },

  -- Solarized
  {
    "maxmx03/solarized.nvim",
    lazy = true,
    opts = {
      theme = "default",
    },
  },
}
