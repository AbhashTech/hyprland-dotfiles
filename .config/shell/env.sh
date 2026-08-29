#!/usr/bin/env bash
# =============================================================================
# Shell Environment & Prompt Initializers
# =============================================================================

export STARSHIP_CONFIG="${HOME}/.config/starship.toml"
export EDITOR="kitty -e nano"
export VISUAL="${EDITOR}"
export PAGER="bat --style=plain"

CACHE_DIR="${HOME}/.cache/shell"
mkdir -p "${CACHE_DIR}" 2>/dev/null || true

_SHELL_NAME=""
if [ -n "$BASH_VERSION" ]; then
    _SHELL_NAME="bash"
elif [ -n "$ZSH_VERSION" ]; then
    _SHELL_NAME="zsh"
fi

if [ -n "$_SHELL_NAME" ]; then
    # --- Starship Prompt ---
    if command -v starship >/dev/null 2>&1; then
        STARSHIP_CACHE="${CACHE_DIR}/starship.${_SHELL_NAME}"
        if [ -f "$STARSHIP_CACHE" ]; then
            source "$STARSHIP_CACHE"
        else
            eval "$(starship init "$_SHELL_NAME")"
            starship init "$_SHELL_NAME" > "$STARSHIP_CACHE" 2>/dev/null || true
        fi
    fi

    # --- Zoxide (Smart cd) ---
    if command -v zoxide >/dev/null 2>&1; then
        ZOXIDE_CACHE="${CACHE_DIR}/zoxide.${_SHELL_NAME}"
        if [ -f "$ZOXIDE_CACHE" ]; then
            source "$ZOXIDE_CACHE"
        else
            eval "$(zoxide init "$_SHELL_NAME")"
            zoxide init "$_SHELL_NAME" > "$ZOXIDE_CACHE" 2>/dev/null || true
        fi
    fi

    # --- Atuin (Searchable SQLite Shell History) ---
    if command -v atuin >/dev/null 2>&1; then
        ATUIN_CACHE="${CACHE_DIR}/atuin.${_SHELL_NAME}"
        if [ -f "$ATUIN_CACHE" ]; then
            source "$ATUIN_CACHE"
        else
            eval "$(atuin init "$_SHELL_NAME")"
            atuin init "$_SHELL_NAME" > "$ATUIN_CACHE" 2>/dev/null || true
        fi
    fi

    # --- Direnv (Per-directory environment & venv switcher) ---
    if command -v direnv >/dev/null 2>&1; then
        DIRENV_CACHE="${CACHE_DIR}/direnv.${_SHELL_NAME}"
        if [ -f "$DIRENV_CACHE" ]; then
            source "$DIRENV_CACHE"
        else
            eval "$(direnv hook "$_SHELL_NAME")"
            direnv hook "$_SHELL_NAME" > "$DIRENV_CACHE" 2>/dev/null || true
        fi
    fi

    # --- Mise (Polyglot dev tool version manager) ---
    if command -v mise >/dev/null 2>&1; then
        MISE_CACHE="${CACHE_DIR}/mise.${_SHELL_NAME}"
        if [ -f "$MISE_CACHE" ]; then
            source "$MISE_CACHE"
        else
            eval "$(mise activate "$_SHELL_NAME")"
            mise activate "$_SHELL_NAME" > "$MISE_CACHE" 2>/dev/null || true
        fi
    fi
fi
