#!/usr/bin/env bash
# =============================================================================
# Shell Environment & Prompt Initializers
# =============================================================================

export STARSHIP_CONFIG="${HOME}/.config/starship.toml"
export EDITOR="kitty -e nano"
export VISUAL="${EDITOR}"
export PAGER="bat --style=plain"

# --- Starship Prompt ---
if command -v starship >/dev/null 2>&1; then
    if [ -n "$BASH_VERSION" ]; then
        eval "$(starship init bash)"
    elif [ -n "$ZSH_VERSION" ]; then
        eval "$(starship init zsh)"
    fi
fi

# --- Zoxide (Smart cd) ---
if command -v zoxide >/dev/null 2>&1; then
    if [ -n "$BASH_VERSION" ]; then
        eval "$(zoxide init bash)"
    elif [ -n "$ZSH_VERSION" ]; then
        eval "$(zoxide init zsh)"
    fi
fi

# --- Atuin (Searchable SQLite Shell History) ---
if command -v atuin >/dev/null 2>&1; then
    if [ -n "$BASH_VERSION" ]; then
        eval "$(atuin init bash)"
    elif [ -n "$ZSH_VERSION" ]; then
        eval "$(atuin init zsh)"
    fi
fi

# --- Direnv (Per-directory environment & venv switcher) ---
if command -v direnv >/dev/null 2>&1; then
    if [ -n "$BASH_VERSION" ]; then
        eval "$(direnv hook bash)"
    elif [ -n "$ZSH_VERSION" ]; then
        eval "$(direnv hook zsh)"
    fi
fi

# --- Mise (Polyglot dev tool version manager) ---
if command -v mise >/dev/null 2>&1; then
    if [ -n "$BASH_VERSION" ]; then
        eval "$(mise activate bash)"
    elif [ -n "$ZSH_VERSION" ]; then
        eval "$(mise activate zsh)"
    fi
fi
