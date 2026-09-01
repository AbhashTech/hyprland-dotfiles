-- =============================================================================
-- UI & Visual Enhancements: Startup Screen, Statusline, Buffers & Notifications
-- =============================================================================

return {
  -- Startup Screen with Custom Zen Silicon Chip Meditator Logo
  {
    "goolord/alpha-nvim",
    event = "VimEnter",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      local alpha = require("alpha")
      local dashboard = require("alpha.themes.dashboard")

      -- Zen Silicon Microchip Logo
      dashboard.section.header.val = {
        [[                       │    │    │    │    │                       ]],
        [[                  ╭────┴────┴────┴────┴────┴────╮                  ]],
        [[                  │  ●                          │                  ]],
        [[             ─────┤            ╭───╮            ├─────             ]],
        [[                  │           (     )           │                  ]],
        [[             ─────┤            ╰─┬─╯            ├─────             ]],
        [[                  │            ╭─┴─╮            │                  ]],
        [[             ─────┤          ╭─╯   ╰─╮          ├─────             ]],
        [[                  │         ╭╯       ╰╮         │                  ]],
        [[             ─────┤        ╭╯  │   │  ╰╮        ├─────             ]],
        [[                  │       ╭╯   │   │   ╰╮       │                  ]],
        [[             ─────┤      (o)   ╰───╯   (o)      ├─────             ]],
        [[                  │     ╭─╯  ╭───────╮  ╰─╮     │                  ]],
        [[                  │     ╰─┬──╯       ╰──┬─╯     │                  ]],
        [[                  │       ╰─────────────╯       │                  ]],
        [[                  ╰────┬────┬────┬────┬────┬────╯                  ]],
        [[                       │    │    │    │    │                       ]],
        [[                                                                   ]],
        [[                   Z E N   S I L I C O N   N V I M                 ]],
        [[                  Unified Hyprland Desktop Edition                 ]],
      }

      dashboard.section.header.opts.hl = "ZenLogoBorder"

      dashboard.section.buttons.val = {
        dashboard.button("f", "  Find File", "<cmd>Telescope find_files<CR>"),
        dashboard.button("n", "  New File", "<cmd>ene <BAR> startinsert<CR>"),
        dashboard.button("r", "  Recent Files", "<cmd>Telescope oldfiles<CR>"),
        dashboard.button("g", "  Find Text (Live Grep)", "<cmd>Telescope live_grep<CR>"),
        dashboard.button("e", "  File Explorer", "<cmd>NvimTreeToggle<CR>"),
        dashboard.button("t", "🎨 Sync Desktop Theme", "<cmd>ThemeSync<CR>"),
        dashboard.button("l", "󰒲  Lazy Plugins", "<cmd>Lazy<CR>"),
        dashboard.button("q", "  Quit Neovim", "<cmd>qa<CR>"),
      }

      for _, btn in ipairs(dashboard.section.buttons.val) do
        btn.opts.hl = "ZenLogoText"
        btn.opts.hl_shortcut = "ZenLogoBorder"
      end

      dashboard.section.footer.opts.hl = "ZenLogoPins"

      dashboard.section.footer.val = function()
        local stats = require("lazy").stats()
        local ms = (math.floor(stats.startuptime * 100 + 0.5) / 100)
        return "⚡ Loaded " .. stats.loaded .. "/" .. stats.count .. " plugins in " .. ms .. "ms"
      end

      alpha.setup(dashboard.opts)
    end,
  },

  -- Statusline (Lualine)
  {
    "nvim-lualine/lualine.nvim",
    event = "VeryLazy",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    opts = function()
      return {
        options = {
          theme = "auto",
          globalstatus = true,
          component_separators = { left = "│", right = "│" },
          section_separators = { left = "", right = "" },
          disabled_filetypes = { statusline = { "alpha", "dashboard", "lazy" } },
        },
        sections = {
          lualine_a = { { "mode", icon = "󰄛" } },
          lualine_b = { { "branch", icon = "" }, "diff", "diagnostics" },
          lualine_c = { { "filename", path = 1, symbols = { modified = " ●", readonly = " 🔒" } } },
          lualine_x = {
            {
              function()
                local status, theme = pcall(require, "theme_colors")
                if status and theme.name then
                  return "🎨 " .. theme.name
                end
                return ""
              end,
            },
            "encoding",
            "fileformat",
            "filetype",
          },
          lualine_y = { "progress" },
          lualine_z = { { "location", icon = "" } },
        },
      }
    end,
  },

  -- Bufferline
  {
    "akinsho/bufferline.nvim",
    event = "VeryLazy",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    opts = {
      options = {
        mode = "buffers",
        separator_style = "slant",
        always_show_bufferline = true,
        show_buffer_close_icons = true,
        show_close_icon = false,
        diagnostics = "nvim_lsp",
        offsets = {
          {
            filetype = "NvimTree",
            text = "File Explorer",
            highlight = "Directory",
            text_align = "left",
          },
        },
      },
    },
  },

  -- Which-Key
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
      preset = "modern",
      win = {
        border = "rounded",
      },
    },
  },

  -- Indent Guides
  {
    "lukas-reineke/indent-blankline.nvim",
    event = { "BufReadPost", "BufNewFile" },
    main = "ibl",
    opts = {
      indent = {
        char = "│",
        tab_char = "│",
      },
      scope = { enabled = true, show_start = false, show_end = false },
      exclude = {
        filetypes = { "help", "alpha", "dashboard", "neo-tree", "Trouble", "lazy", "mason", "notify" },
      },
    },
  },

  -- Modern Notifications & Command UI
  {
    "rcarriga/nvim-notify",
    opts = {
      timeout = 3000,
      background_colour = "#1e1e2e",
      render = "wrapped-compact",
      stages = "fade",
    },
  },
  {
    "folke/noice.nvim",
    event = "VeryLazy",
    dependencies = {
      "MunifTanjim/nui.nvim",
      "rcarriga/nvim-notify",
    },
    opts = {
      lsp = {
        override = {
          ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
          ["vim.lsp.util.stylize_markdown"] = true,
          ["cmp.entry.get_documentation"] = true,
        },
      },
      presets = {
        bottom_search = true,
        command_palette = true,
        long_message_to_split = true,
        inc_rename = false,
        lsp_doc_border = true,
      },
    },
  },
}
