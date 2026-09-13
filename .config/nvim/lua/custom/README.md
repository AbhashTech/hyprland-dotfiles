# User-Specific Neovim Configuration Modules

Files in this directory allow you to customize Neovim without modifying the upstream dotfiles repository. All files matching `personal_*.lua` or placed inside `lua/custom/` are ignored by Git.

Each file is dedicated to a specific language, tool, or workflow:

| File Pattern | Purpose | Example Plugins |
|---|---|---|
| `personal_go.lua` | Golang language & tool suite | `ray-x/go.nvim`, `leoluz/nvim-dap-go` |
| `personal_web.lua` | React, Next.js, JSX & TypeScript helpers | `windwp/nvim-ts-autotag` |
| `personal_terminal.lua` | Terminal multiplexer & Lazygit popups | `akinsho/toggleterm.nvim` |
| `personal_lsp.lua` | Custom LSP servers, formatters & linters | `gopls`, `ts_ls`, `tailwindcss`, `eslint`, `conform.nvim` |
| `personal_<tool>.lua` | Any personal plugin or language setup | Rust, Python, Docker, AI assistants, etc. |

> [!TIP]
> You can manage, export, and backup your personal configuration files across devices using `~/.dotfiles/scripts/dotfiles-personal.sh`.
