#!/usr/bin/env bash
# =============================================================================
# Dotfiles Push & Theme Sync Wrapper
# =============================================================================
# Synchronizes any active desktop theme changes to git, commits them,
# pushes commits to the remote repository, and ensures local theme changes
# remain untracked (skip-worktree) so git status stays clean.
# =============================================================================

set -e

DOTFILES_DIR="${HOME}/.dotfiles"
THEME_SWITCHER="${DOTFILES_DIR}/.config/hypr/scripts/theme_switcher.py"

# ANSI Colors
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_GREEN="\033[38;2;166;227;161m"
C_BLUE="\033[38;2;137;180;250m"
C_YELLOW="\033[38;2;249;226;175m"
C_RED="\033[38;2;243;139;168m"

if [ ! -d "${DOTFILES_DIR}/.git" ]; then
    echo -e "${C_RED}Error: ${DOTFILES_DIR} is not a git repository.${C_RESET}" >&2
    exit 1
fi

cd "${DOTFILES_DIR}"

# 1. Sync theme changes to git (stages & commits only if theme files differ)
if [ -f "${THEME_SWITCHER}" ]; then
    echo -e "${C_BLUE}ℹ Checking and syncing active theme changes with repository...${C_RESET}"
    python3 "${THEME_SWITCHER}" --git-sync
fi

# 2. Push to remote repository
echo -e "${C_BLUE}🚀 Pushing dotfiles to remote repository...${C_RESET}"
git push "$@"

# 3. Ensure skip-worktree is firmly active locally so git status remains clean
if [ -f "${THEME_SWITCHER}" ]; then
    python3 "${THEME_SWITCHER}" --git-skip >/dev/null 2>&1 || true
fi

echo -e "${C_GREEN}${C_BOLD}✓ Done! Dotfiles pushed and local theme files remain untracked in git status.${C_RESET}"
