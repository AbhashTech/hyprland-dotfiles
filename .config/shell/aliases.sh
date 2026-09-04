#!/usr/bin/env bash
# =============================================================================
# Shell Aliases & Functions for Modern CLI Productivity Suite
# (Source this in ~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish)
# =============================================================================

# --- eza (Modern ls) ---
if command -v eza >/dev/null 2>&1; then
    alias ls='eza --icons --group-directories-first'
    alias ll='eza -la --icons --group-directories-first --git'
    alias l='eza -l --icons --group-directories-first'
    alias la='eza -a --icons --group-directories-first'
    alias lt='eza --tree --level=2 --icons --group-directories-first'
    alias lta='eza --tree --level=3 -a --icons --group-directories-first'
fi

# --- bat (Modern cat) ---
if command -v bat >/dev/null 2>&1; then
    alias cat='bat --style=plain --paging=never'
    alias catp='bat --style=full'
fi

# --- ripgrep (Modern grep) & fd (Modern find) ---
if command -v rg >/dev/null 2>&1; then
    alias grep='rg'
fi
if command -v fd >/dev/null 2>&1; then
    alias find='fd'
fi

# --- Disk & Resource Analyzers ---
if command -v duf >/dev/null 2>&1; then
    alias df='duf'
fi
if command -v dust >/dev/null 2>&1; then
    alias du='dust'
fi

# --- Safe File Management ---
if command -v trash-put >/dev/null 2>&1; then
    alias rm='trash-put'
    alias rm-force='/bin/rm -i'
    alias trash-list='trash-list'
    alias trash-restore='trash-restore'
    alias trash-empty='trash-empty'
fi

# --- tealdeer (tldr) ---
if command -v tealdeer >/dev/null 2>&1; then
    alias tldr='tealdeer'
fi

# --- HTTP Client ---
if command -v xh >/dev/null 2>&1; then
    alias http='xh'
fi

# --- Markdown Viewer ---
if command -v glow >/dev/null 2>&1; then
    alias md='glow -p'
fi

# --- Git & Container TUIs ---
if command -v lazygit >/dev/null 2>&1; then
    alias lg='lazygit'
fi
if command -v lazydocker >/dev/null 2>&1; then
    alias ld='lazydocker'
fi

# --- Terminal Multiplexer ---
if command -v zellij >/dev/null 2>&1; then
    alias zj='zellij'
fi

# --- System Fetch ---
if command -v fastfetch >/dev/null 2>&1; then
    alias ff='fastfetch'
fi

# --- App Launcher & Shortcut Creator ---
alias add-app="python3 ~/.config/hypr/scripts/app_shortcut_creator.py"
alias create-shortcut="python3 ~/.config/hypr/scripts/app_shortcut_creator.py"
alias app-creator="python3 ~/.config/hypr/scripts/app_shortcut_creator.py"

# --- Dotfiles & Theme Synchronization ---
alias dotpush="~/.dotfiles/scripts/dotfiles-push.sh"
alias theme-sync="python3 ~/.config/hypr/scripts/theme_switcher.py --git-sync"
alias theme-skip="python3 ~/.config/hypr/scripts/theme_switcher.py --git-skip"
alias theme-unskip="python3 ~/.config/hypr/scripts/theme_switcher.py --git-unskip"

