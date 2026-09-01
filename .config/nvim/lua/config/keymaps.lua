-- =============================================================================
-- Global Keymaps & Shortcuts
-- =============================================================================

local map = vim.keymap.set
local opts = { noremap = true, silent = true }

-- Better Navigation in Window Splits
map("n", "<C-h>", "<C-w>h", { desc = "Move to left split" })
map("n", "<C-j>", "<C-w>j", { desc = "Move to below split" })
map("n", "<C-k>", "<C-w>k", { desc = "Move to above split" })
map("n", "<C-l>", "<C-w>l", { desc = "Move to right split" })

-- Resize Splits with Arrows
map("n", "<C-Up>", ":resize -2<CR>", { desc = "Resize split up" })
map("n", "<C-Down>", ":resize +2<CR>", { desc = "Resize split down" })
map("n", "<C-Left>", ":vertical resize -2<CR>", { desc = "Resize split left" })
map("n", "<C-Right>", ":vertical resize +2<CR>", { desc = "Resize split right" })

-- Split Management
map("n", "<leader>sv", "<C-w>v", { desc = "Split vertical" })
map("n", "<leader>sh", "<C-w>s", { desc = "Split horizontal" })
map("n", "<leader>se", "<C-w>=", { desc = "Make splits equal size" })
map("n", "<leader>sx", "<cmd>close<CR>", { desc = "Close current split" })

-- Buffer Navigation
map("n", "<S-l>", "<cmd>bnext<CR>", { desc = "Next buffer" })
map("n", "<S-h>", "<cmd>bprevious<CR>", { desc = "Previous buffer" })
map("n", "<leader>bd", "<cmd>bdelete<CR>", { desc = "Delete buffer" })
map("n", "<leader>ba", "<cmd>%bd|e#|bd#<CR>", { desc = "Close other buffers" })

-- Quick Save & Quit
map({ "n", "i", "v" }, "<C-s>", "<cmd>w<CR>", { desc = "Save file" })
map("n", "<leader>w", "<cmd>w<CR>", { desc = "Save file" })
map("n", "<leader>q", "<cmd>q<CR>", { desc = "Quit" })
map("n", "<leader>Q", "<cmd>qa!<CR>", { desc = "Force quit all" })

-- Clear Search Highlights
map("n", "<Esc>", "<cmd>nohlsearch<CR>", { desc = "Clear search highlight" })

-- Move Lines in Visual Mode
map("v", "J", ":m '>+1<CR>gv=gv", { desc = "Move line down" })
map("v", "K", ":m '<-2<CR>gv=gv", { desc = "Move line up" })

-- Stay in Indent Mode
map("v", "<", "<gv", { desc = "Indent left and keep selection" })
map("v", ">", ">gv", { desc = "Indent right and keep selection" })

-- Better Paste (keep register content)
map("x", "<leader>p", [["_dP]], { desc = "Paste without replacing register" })

-- Diagnostic Navigation
map("n", "[d", vim.diagnostic.goto_prev, { desc = "Previous diagnostic" })
map("n", "]d", vim.diagnostic.goto_next, { desc = "Next diagnostic" })
map("n", "<leader>d", vim.diagnostic.open_float, { desc = "Show diagnostic message" })
map("n", "<leader>qf", vim.diagnostic.setloclist, { desc = "Open diagnostic quickfix" })

-- File Explorer (Nvim-Tree / Oil)
map("n", "<leader>e", "<cmd>NvimTreeToggle<CR>", { desc = "Toggle File Explorer" })
map("n", "<leader>o", "<cmd>Oil<CR>", { desc = "Open Oil file editor" })

-- Dynamic Theme Switcher Trigger within Neovim
map("n", "<leader>th", function()
  require("config.theme").sync(true)
end, { desc = "Sync Neovim theme with desktop manager" })
