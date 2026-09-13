#!/usr/bin/env bash
# =============================================================================
# Dotfiles Personal Settings Manager (Export, Import & Version Control)
# =============================================================================
# Manages user-specific, untracked personal configurations across packages:
#   - Neovim:      .config/nvim/lua/plugins/personal_*.lua, .config/nvim/lua/custom/
#   - Shell:       .config/shell/user/*, .config/shell/*.local.sh, ~/.zshenv
#   - Hyprland:    .config/hypr/user/*
#   - Quickshell:  .config/quickshell/custom_plugins/*
#
# Commands:
#   status               Show all active personal config files & repo status
#   export [output]      Export personal configs to an archive (.tar.gz) or directory
#   import <input>       Import/restore personal configs from an archive or directory
#   init-repo [dir]      Initialize a standalone Git repo for your personal settings
#   save [message]       Sync personal configs into the personal git repo and commit
#   diff                 View diff between current files and personal git repo
#   push [args...]       Push personal git repo to remote (e.g. private GitHub)
#   pull [args...]       Pull personal git repo updates from remote
# =============================================================================

set -e

DOTFILES_DIR="${HOME}/.dotfiles"
PERSONAL_REPO_DIR="${HOME}/.dotfiles-personal"

# ANSI Colors
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_GREEN="\033[38;2;166;227;161m"
C_BLUE="\033[38;2;137;180;250m"
C_YELLOW="\033[38;2;249;226;175m"
C_RED="\033[38;2;243;139;168m"
C_GRAY="\033[38;2;108;112;134m"
C_CYAN="\033[38;2;148;226;213m"

# Find all personal files currently present on the system
get_personal_files() {
    local files=()

    # 1. Shell environment in home (~/.zshenv)
    [ -f "${HOME}/.zshenv" ] && files+=("${HOME}/.zshenv")

    # 2. Neovim personal plugins & custom files
    if [ -d "${DOTFILES_DIR}/.config/nvim/lua/plugins" ]; then
        for f in "${DOTFILES_DIR}/.config/nvim/lua/plugins"/personal_*.lua; do
            [ -f "$f" ] && files+=("$f")
        done
    fi
    if [ -d "${DOTFILES_DIR}/.config/nvim/lua/custom" ]; then
        while IFS= read -r -d '' f; do
            [ "$(basename "$f")" != "README.md" ] && files+=("$f")
        done < <(find "${DOTFILES_DIR}/.config/nvim/lua/custom" -mindepth 1 -type f -print0 2>/dev/null)
    fi

    # 3. Shell personal modules & local files
    if [ -d "${DOTFILES_DIR}/.config/shell/user" ]; then
        while IFS= read -r -d '' f; do
            [ "$(basename "$f")" != "README.md" ] && files+=("$f")
        done < <(find "${DOTFILES_DIR}/.config/shell/user" -mindepth 1 -type f -print0 2>/dev/null)
    fi
    for f in "${DOTFILES_DIR}/.config/shell"/*.local.sh; do
        [ -f "$f" ] && files+=("$f")
    done

    # 4. Hyprland personal modules
    if [ -d "${DOTFILES_DIR}/.config/hypr/user" ]; then
        while IFS= read -r -d '' f; do
            [ "$(basename "$f")" != "README.md" ] && files+=("$f")
        done < <(find "${DOTFILES_DIR}/.config/hypr/user" -mindepth 1 -type f -print0 2>/dev/null)
    fi

    # 5. Quickshell custom plugins
    if [ -d "${DOTFILES_DIR}/.config/quickshell/custom_plugins" ]; then
        while IFS= read -r -d '' f; do
            [ "$(basename "$f")" != "README.md" ] && files+=("$f")
        done < <(find "${DOTFILES_DIR}/.config/quickshell/custom_plugins" -mindepth 1 -type f ! -path '*/.git*' ! -path '*/__pycache__*' -print0 2>/dev/null)
    fi

    echo "${files[@]}"
}

# Display status of personal files and version control
cmd_status() {
    echo -e "${C_BOLD}=== Personal Settings & Configuration Status ===${C_RESET}"
    echo ""

    local files=($(get_personal_files))
    if [ ${#files[@]} -eq 0 ]; then
        echo -e "${C_YELLOW}No personal configuration files detected on this system.${C_RESET}"
        echo -e "You can create modular personal files in:"
        echo -e "  • Neovim:   ~/.dotfiles/.config/nvim/lua/plugins/personal_<name>.lua"
        echo -e "  • Shell:    ~/.dotfiles/.config/shell/user/<name>.sh or ~/.zshenv"
        echo -e "  • Hyprland: ~/.dotfiles/.config/hypr/user/<name>.lua"
        echo ""
    else
        echo -e "${C_CYAN}Active Personal Files (${#files[@]} found):${C_RESET}"
        for f in "${files[@]}"; do
            local size
            size=$(du -h "$f" 2>/dev/null | cut -f1)
            local rel_display="${f/#$HOME/~}"
            echo -e "  ${C_GREEN}●${C_RESET} ${rel_display} ${C_GRAY}(${size})${C_RESET}"
        done
        echo ""
    fi

    echo -e "${C_CYAN}Version Control Status:${C_RESET}"
    if [ -d "${PERSONAL_REPO_DIR}/.git" ]; then
        echo -e "  Personal Repository: ${C_GREEN}${PERSONAL_REPO_DIR}${C_RESET}"
        local git_branch
        git_branch=$(git -C "${PERSONAL_REPO_DIR}" branch --show-current 2>/dev/null || echo "detached")
        local git_remote
        git_remote=$(git -C "${PERSONAL_REPO_DIR}" remote get-url origin 2>/dev/null || echo "No remote configured")
        echo -e "  Branch: ${C_BLUE}${git_branch}${C_RESET}"
        echo -e "  Remote: ${C_GRAY}${git_remote}${C_RESET}"

        local status_short
        status_short=$(git -C "${PERSONAL_REPO_DIR}" status --short 2>/dev/null || true)
        if [ -z "$status_short" ]; then
            echo -e "  Sync Status: ${C_GREEN}Up to date (clean)${C_RESET}"
        else
            echo -e "  Sync Status: ${C_YELLOW}Changes pending commit/sync${C_RESET}"
        fi
    else
        echo -e "  Personal Repository: ${C_GRAY}Not initialized.${C_RESET}"
        echo -e "  Run ${C_BOLD}$0 init-repo${C_RESET} to set up dedicated version control for your personal settings."
    fi
}

# Export personal files to a tar.gz archive or destination directory
cmd_export() {
    local target="${1:-${HOME}/personal-dotfiles-$(date +%Y%m%d_%H%M%S).tar.gz}"
    local files=($(get_personal_files))

    if [ ${#files[@]} -eq 0 ]; then
        echo -e "${C_RED}Error: No personal files found to export.${C_RESET}" >&2
        exit 1
    fi

    echo -e "${C_BLUE}ℹ Exporting ${#files[@]} personal configuration files...${C_RESET}"

    if [[ "$target" == *.tar.gz || "$target" == *.tgz ]]; then
        local tmp_export
        tmp_export=$(mktemp -d)
        trap 'rm -rf "$tmp_export"' EXIT

        for f in "${files[@]}"; do
            local rel="${f/#$HOME\//}"
            local dest_dir="${tmp_export}/$(dirname "$rel")"
            mkdir -p "$dest_dir"
            cp -p "$f" "${tmp_export}/${rel}"
        done

        mkdir -p "$(dirname "$target")"
        tar -czf "$target" -C "$tmp_export" .
        echo -e "${C_GREEN}✓ Exported personal settings archive:${C_RESET} ${C_BOLD}${target}${C_RESET}"
        echo -e "${C_GRAY}Archive size: $(du -h "$target" | cut -f1)${C_RESET}"
    else
        # Target is a directory
        mkdir -p "$target"
        for f in "${files[@]}"; do
            local rel="${f/#$HOME\//}"
            local dest_dir="${target}/$(dirname "$rel")"
            mkdir -p "$dest_dir"
            cp -p "$f" "${target}/${rel}"
        done
        echo -e "${C_GREEN}✓ Exported personal settings to directory:${C_RESET} ${C_BOLD}${target}${C_RESET}"
    fi
}

# Import personal files from a tar.gz archive or directory
cmd_import() {
    local source="$1"

    if [ -z "$source" ]; then
        echo -e "${C_RED}Error: Please specify the import source (tar.gz archive or directory).${C_RESET}" >&2
        echo -e "Usage: $0 import <path/to/archive.tar.gz | path/to/dir>"
        exit 1
    fi

    if [ ! -e "$source" ]; then
        echo -e "${C_RED}Error: Source '$source' does not exist.${C_RESET}" >&2
        exit 1
    fi

    local src_dir=""
    local cleanup=false

    if [ -f "$source" ] && [[ "$source" == *.tar.gz || "$source" == *.tgz ]]; then
        src_dir=$(mktemp -d)
        cleanup=true
        tar -xzf "$source" -C "$src_dir"
    elif [ -d "$source" ]; then
        src_dir="$source"
    else
        echo -e "${C_RED}Error: Unrecognized source format. Expected .tar.gz archive or directory.${C_RESET}" >&2
        exit 1
    fi

    echo -e "${C_BLUE}ℹ Importing personal configurations into home / dotfiles...${C_RESET}"
    local count=0

    while IFS= read -r -d '' f; do
        local rel="${f/#$src_dir\//}"
        local dest="${HOME}/${rel}"
        mkdir -p "$(dirname "$dest")"
        cp -p "$f" "$dest"
        echo -e "  ${C_GREEN}✓${C_RESET} Restored: ${rel}"
        count=$((count + 1))
    done < <(find "$src_dir" -type f ! -name ".git*" ! -name "README.md" -print0)

    [ "$cleanup" = true ] && rm -rf "$src_dir"

    echo -e "${C_GREEN}${C_BOLD}✓ Imported ${count} personal configuration files successfully!${C_RESET}"
}

# Initialize a standalone Git repository for personal settings
cmd_init_repo() {
    local repo_dir="${1:-$PERSONAL_REPO_DIR}"

    if [ -d "${repo_dir}/.git" ]; then
        echo -e "${C_YELLOW}⚠ Personal git repository already initialized at ${repo_dir}.${C_RESET}"
        return 0
    fi

    echo -e "${C_BLUE}ℹ Initializing personal Git repository at ${repo_dir}...${C_RESET}"
    mkdir -p "$repo_dir"
    git -C "$repo_dir" init -b main

    cat << 'EOF' > "${repo_dir}/README.md"
# Personal Dotfiles & Configurations

This repository contains private, machine-specific or personal configurations for:
- Neovim personal plugins & language suites
- Shell personal environment variables and aliases
- Hyprland user monitor, input, and keybind overrides

Managed via `~/.dotfiles/scripts/dotfiles-personal.sh`.
EOF

    # Sync current files into it
    cmd_save "feat: initial personal configuration setup" "$repo_dir"

    echo ""
    echo -e "${C_GREEN}${C_BOLD}✓ Personal Git repository initialized!${C_RESET}"
    echo -e "To backup to your private GitHub or GitLab repository:"
    echo -e "  ${C_BOLD}cd ${repo_dir}${C_RESET}"
    echo -e "  ${C_BOLD}git remote add origin git@github.com:<username>/my-personal-dotfiles.git${C_RESET}"
    echo -e "  ${C_BOLD}git push -u origin main${C_RESET}"
    echo ""
    echo -e "After setting a remote, you can run ${C_BOLD}$0 push${C_RESET} or ${C_BOLD}$0 pull${C_RESET} anytime."
}

# Sync current system personal files into personal git repo and commit
cmd_save() {
    local msg="${1:-"chore: update personal configurations $(date +'%Y-%m-%d %H:%M')"}"
    local repo_dir="${2:-$PERSONAL_REPO_DIR}"

    if [ ! -d "${repo_dir}/.git" ]; then
        echo -e "${C_YELLOW}Personal repository not found. Initializing...${C_RESET}"
        cmd_init_repo "$repo_dir"
        return 0
    fi

    local files=($(get_personal_files))
    if [ ${#files[@]} -eq 0 ]; then
        echo -e "${C_YELLOW}No personal files found to save.${C_RESET}"
        return 0
    fi

    echo -e "${C_BLUE}ℹ Syncing personal files into ${repo_dir}...${C_RESET}"
    for f in "${files[@]}"; do
        local rel="${f/#$HOME\//}"
        local dest_dir="${repo_dir}/$(dirname "$rel")"
        mkdir -p "$dest_dir"
        cp -p "$f" "${repo_dir}/${rel}"
    done

    git -C "$repo_dir" add -A
    if git -C "$repo_dir" diff --cached --quiet; then
        echo -e "${C_GREEN}✓ No changes detected. Personal repository is up to date.${C_RESET}"
    else
        git -C "$repo_dir" commit -m "$msg"
        echo -e "${C_GREEN}${C_BOLD}✓ Personal configurations committed to git!${C_RESET}"
        echo -e "${C_GRAY}Commit: $(git -C "$repo_dir" rev-parse --short HEAD) - ${msg}${C_RESET}"
    fi
}

# Show git diff between current files and personal git repo
cmd_diff() {
    local repo_dir="${1:-$PERSONAL_REPO_DIR}"

    if [ ! -d "${repo_dir}/.git" ]; then
        echo -e "${C_RED}Error: Personal repository at ${repo_dir} not initialized.${C_RESET}" >&2
        exit 1
    fi

    # Sync first to see diff against HEAD
    local files=($(get_personal_files))
    for f in "${files[@]}"; do
        local rel="${f/#$HOME\//}"
        local dest_dir="${repo_dir}/$(dirname "$rel")"
        mkdir -p "$dest_dir"
        cp -p "$f" "${repo_dir}/${rel}"
    done

    git -C "$repo_dir" diff
}

# Push personal git repo
cmd_push() {
    local repo_dir="${PERSONAL_REPO_DIR}"
    if [ ! -d "${repo_dir}/.git" ]; then
        echo -e "${C_RED}Error: Personal repository at ${repo_dir} not initialized.${C_RESET}" >&2
        exit 1
    fi

    echo -e "${C_BLUE}🚀 Pushing personal repository to remote...${C_RESET}"
    git -C "$repo_dir" push "$@"
    echo -e "${C_GREEN}✓ Personal repository pushed successfully.${C_RESET}"
}

# Pull personal git repo
cmd_pull() {
    local repo_dir="${PERSONAL_REPO_DIR}"
    if [ ! -d "${repo_dir}/.git" ]; then
        echo -e "${C_RED}Error: Personal repository at ${repo_dir} not initialized.${C_RESET}" >&2
        exit 1
    fi

    echo -e "${C_BLUE}📥 Pulling personal repository from remote...${C_RESET}"
    git -C "$repo_dir" pull "$@"
    # Restore pulled files to active system
    cmd_import "$repo_dir"
}

# Help message
cmd_help() {
    echo -e "${C_BOLD}Usage:${C_RESET} $0 <command> [arguments]"
    echo ""
    echo -e "${C_CYAN}Commands:${C_RESET}"
    echo -e "  ${C_BOLD}status${C_RESET}               List all detected personal files & git repo status"
    echo -e "  ${C_BOLD}export${C_RESET} [output]      Export personal files to an archive (.tar.gz) or folder"
    echo -e "  ${C_BOLD}import${C_RESET} <source>      Import personal files from an archive or folder"
    echo -e "  ${C_BOLD}init-repo${C_RESET} [dir]      Initialize a standalone Git repo (default: ~/.dotfiles-personal)"
    echo -e "  ${C_BOLD}save${C_RESET} [message]       Sync active personal files to personal repo and commit"
    echo -e "  ${C_BOLD}diff${C_RESET}                 Show differences between active files and personal repo"
    echo -e "  ${C_BOLD}push${C_RESET} [args...]       Push personal repo to private remote git repository"
    echo -e "  ${C_BOLD}pull${C_RESET} [args...]       Pull personal repo from remote and restore active files"
    echo -e "  ${C_BOLD}help${C_RESET}                 Show this help message"
    echo ""
    echo -e "${C_CYAN}Examples:${C_RESET}"
    echo -e "  $0 status"
    echo -e "  $0 export ~/my-personal-backup.tar.gz"
    echo -e "  $0 import ~/my-personal-backup.tar.gz"
    echo -e "  $0 init-repo"
    echo -e "  $0 save 'feat: add python plugin and monitor layout'"
    echo -e "  $0 push origin main"
}

# CLI routing
case "$1" in
    status|"")
        cmd_status
        ;;
    export)
        shift
        cmd_export "$@"
        ;;
    import)
        shift
        cmd_import "$@"
        ;;
    init-repo|init)
        shift
        cmd_init_repo "$@"
        ;;
    save|commit)
        shift
        cmd_save "$@"
        ;;
    diff)
        shift
        cmd_diff "$@"
        ;;
    push)
        shift
        cmd_push "$@"
        ;;
    pull)
        shift
        cmd_pull "$@"
        ;;
    help|-h|--help)
        cmd_help
        ;;
    *)
        echo -e "${C_RED}Unknown command: $1${C_RESET}" >&2
        cmd_help
        exit 1
        ;;
esac
