-- =============================================================================
-- Autocommands
-- =============================================================================

local augroup = vim.api.nvim_create_augroup
local autocmd = vim.api.nvim_create_autocmd

-- General group
local general_group = augroup("GeneralSettings", { clear = true })

-- Highlight on Yank
autocmd("TextYankPost", {
  group = general_group,
  pattern = "*",
  callback = function()
    vim.highlight.on_yank({ higroup = "IncSearch", timeout = 150 })
  end,
  desc = "Briefly highlight yanked text",
})

-- Resize splits if window got resized
autocmd("VimResized", {
  group = general_group,
  pattern = "*",
  command = "tabdo wincmd =",
  desc = "Auto-resize splits when terminal window size changes",
})

-- Check if file changed outside of Neovim & sync desktop theme on FocusGained
autocmd({ "FocusGained", "BufEnter", "TermLeave" }, {
  group = general_group,
  callback = function()
    if vim.o.buftype ~= "nofile" then
      vim.cmd("checktime")
    end
    require("config.theme").sync(false)
  end,
  desc = "Check for external file updates and sync desktop theme on focus",
})

-- Close some filetypes with <q>
autocmd("FileType", {
  group = general_group,
  pattern = {
    "qf",
    "help",
    "man",
    "notify",
    "lspinfo",
    "spectre_panel",
    "startuptime",
    "tsplayground",
    "PlenaryTestPopup",
    "checkhealth",
  },
  callback = function(event)
    vim.bo[event.buf].buflisted = false
    vim.keymap.set("n", "q", "<cmd>close<CR>", { buffer = event.buf, silent = true })
  end,
  desc = "Close auxiliary windows with 'q'",
})

-- Auto-create dir when saving a file if parent doesn't exist
autocmd("BufWritePre", {
  group = general_group,
  callback = function(event)
    if event.match:match("^%w%w+:[\\/][\\/]") then
      return
    end
    local file = vim.uv.fs_realpath(event.match) or event.match
    vim.fn.mkdir(vim.fn.fnamemodify(file, ":p:h"), "p")
  end,
  desc = "Auto create non-existing parent directory on write",
})
