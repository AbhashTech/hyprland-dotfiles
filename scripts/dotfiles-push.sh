#!/usr/bin/env bash
# =============================================================================
# Dotfiles Push & User Config Isolation Wrapper
# =============================================================================
# Isolates local user configuration changes (theme changes, idle timeouts,
# wallpapers, keyboard layouts, and desktop preferences) using git skip-worktree.
#
# Features:
#   - Synchronizes active desktop theme changes to git
#   - Pushes commits cleanly to remote repository
#   - Ensures all user-modifiable configuration files remain untracked
#     (skip-worktree) so local user tweaks never dirty `git status`
#   - CLI actions: --skip, --unskip, --status, --help, or standard git push
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
C_GRAY="\033[38;2;108;112;134m"

# List of user-modifiable and dynamic desktop configuration files to protect
USER_CONFIG_FILES=(
    # Dynamic theme files
    ".config/hypr/theme.conf"
    ".config/hypr/theme_vars.lua"
    ".config/kitty/theme.conf"
    ".config/mako/config"
    ".config/btop/btop.conf"
    ".config/starship.toml"
    ".config/zellij/config.kdl"
    ".config/lazygit/config.yml"
    ".config/swappy/config"
    ".config/kdeglobals"
    ".config/dolphinrc"
    ".config/gtk-3.0/settings.ini"
    ".config/gtk-4.0/settings.ini"
    ".config/xsettingsd/xsettingsd.conf"
    ".config/nvim/lua/theme_colors.lua"

    # User preference & hardware/desktop state
    ".config/hypr/hypridle.conf"
    ".config/hypr/hyprpaper.conf"
    ".config/hypr/modules/input.lua"
    ".config/mimeapps.list"
)

if [ ! -d "${DOTFILES_DIR}/.git" ]; then
    echo -e "${C_RED}Error: ${DOTFILES_DIR} is not a git repository.${C_RESET}" >&2
    exit 1
fi

cd "${DOTFILES_DIR}"

get_existing_user_configs() {
    local existing=()
    for rel_path in "${USER_CONFIG_FILES[@]}"; do
        if [ -f "${DOTFILES_DIR}/${rel_path}" ]; then
            existing+=("${rel_path}")
        fi
    done
    echo "${existing[@]}"
}

apply_skip() {
    local files=($(get_existing_user_configs))
    if [ ${#files[@]} -gt 0 ]; then
        git update-index --skip-worktree "${files[@]}" 2>/dev/null || true
        echo -e "${C_GREEN}✓ Isolated ${#files[@]} user config files with skip-worktree (git status is clean).${C_RESET}"
    fi
}

apply_unskip() {
    local files=($(get_existing_user_configs))
    if [ ${#files[@]} -gt 0 ]; then
        git update-index --no-skip-worktree "${files[@]}" 2>/dev/null || true
        echo -e "${C_YELLOW}⚠ Unskipped ${#files[@]} user config files from skip-worktree.${C_RESET}"
    fi
}

show_status() {
    echo -e "${C_BOLD}=== User Configuration Files Skip-Worktree Status ===${C_RESET}"
    local files=($(get_existing_user_configs))
    local skipped_count=0
    local unskipped_count=0

    local ls_out
    ls_out=$(git ls-files -v "${files[@]}" 2>/dev/null || true)

    while IFS= read -r line; do
        [ -z "$line" ] && continue
        local flag="${line:0:1}"
        local file="${line:2}"
        if [[ "$flag" =~ [[:lower:]] ]] || [ "$flag" = "S" ]; then
            echo -e "  ${C_GREEN}● [SKIPPED]${C_RESET} ${file}"
            skipped_count=$((skipped_count + 1))
        else
            echo -e "  ${C_YELLOW}○ [TRACKED]${C_RESET} ${file}"
            unskipped_count=$((unskipped_count + 1))
        fi
    done <<< "$ls_out"

    echo -e "${C_GRAY}Summary: ${skipped_count} skipped, ${unskipped_count} tracked${C_RESET}"
}

# Handle command-line arguments
case "$1" in
    --skip|-s|skip)
        apply_skip
        exit 0
        ;;
    --unskip|-u|unskip)
        apply_unskip
        exit 0
        ;;
    --status|status)
        show_status
        exit 0
        ;;
    --help|-h|help)
        echo -e "${C_BOLD}Usage:${C_RESET} $0 [options | git push args]"
        echo ""
        echo "Options:"
        echo "  --skip, -s       Mark all user config files as skip-worktree"
        echo "  --unskip, -u     Unmark all user config files from skip-worktree"
        echo "  --status         Show skip-worktree status of all user config files"
        echo "  --help, -h       Show this help message"
        echo ""
        echo "Default behavior (when called with no options or with git arguments):"
        echo "  1. Sync active theme changes with repo"
        echo "  2. Push dotfiles to remote repository (git push [args...])"
        echo "  3. Enforce skip-worktree on all user config files"
        exit 0
        ;;
esac

# 1. Sync theme changes to git (stages & commits only if theme files differ)
if [ -f "${THEME_SWITCHER}" ]; then
    echo -e "${C_BLUE}ℹ Checking and syncing active theme changes with repository...${C_RESET}"
    python3 "${THEME_SWITCHER}" --git-sync
fi

# 2. Push to remote repository
echo -e "${C_BLUE}🚀 Pushing dotfiles to remote repository...${C_RESET}"
git push "$@"

# 3. Ensure skip-worktree is firmly active locally across ALL user configs
echo -e "${C_BLUE}🔒 Enforcing skip-worktree on user configuration files...${C_RESET}"
apply_skip >/dev/null 2>&1 || true

if [ -f "${THEME_SWITCHER}" ]; then
    python3 "${THEME_SWITCHER}" --git-skip >/dev/null 2>&1 || true
fi

echo -e "${C_GREEN}${C_BOLD}✓ Done! Dotfiles pushed and user config changes avoided/isolated from git status.${C_RESET}"
