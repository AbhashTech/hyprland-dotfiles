# =============================================================================
# Modern Zsh Configuration (~/.zshrc)
# =============================================================================

# If not running interactively, don't do anything
[[ -o interactive ]] || return

# --- History Configuration ---
HISTFILE="${HOME}/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000
setopt EXTENDED_HISTORY          # Write history in :start:elapsed;command format
setopt HIST_EXPIRE_DUPS_FIRST    # Expire duplicate entries first when trimming
setopt HIST_IGNORE_DUPS          # Don't record an entry that was just recorded
setopt HIST_IGNORE_ALL_DUPS      # Delete old duplicate entry if new entry is typed
setopt HIST_FIND_NO_DUPS         # Do not display a line previously found
setopt HIST_IGNORE_SPACE         # Don't record lines starting with a space
setopt HIST_SAVE_NO_DUPS         # Don't write duplicate entries in history file
setopt HIST_REDUCE_BLANKS        # Remove superfluous blanks before recording
setopt SHARE_HISTORY             # Share history between all active sessions

# --- Basic Shell Options ---
setopt AUTO_CD                   # Type directory name to cd into it
setopt INTERACTIVE_COMMENTS      # Allow comments even in interactive shell
setopt PROMPT_SUBST              # Enable parameter expansion in prompt

# --- Completion System ---
mkdir -p "${HOME}/.cache/zsh"
autoload -Uz compinit
compinit -d "${HOME}/.cache/zsh/zcompdump"
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' # Case-insensitive tab completion
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"     # Colored completion matching ls

# --- Default Environment Variables ---
export EDITOR="nvim"
export VISUAL="nvim"

# --- Dynamic Terminal / Tab Window Title ---
function set_win_title() {
    print -Pn "\e]0;%1~\a"
}
autoload -Uz add-zsh-hook
add-zsh-hook precmd set_win_title

# --- Modular Shell Suite (Environment, Starship, Atuin, Zoxide, Direnv, Mise) ---
[[ -f "${HOME}/.dotfiles/.config/shell/env.sh" ]] && source "${HOME}/.dotfiles/.config/shell/env.sh"

# --- Shell Productivity Aliases ---
[[ -f "${HOME}/.dotfiles/.config/shell/aliases.sh" ]] && source "${HOME}/.dotfiles/.config/shell/aliases.sh"

# --- Official Pacman Zsh Plugins ---
# Autosuggestions (Fish-like history suggestions)
if [[ -f "/usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
    source "/usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh"
    ZSH_AUTOSUGGEST_STRATEGY=(history completion)
fi

# Syntax Highlighting (Fish-like syntax highlighting - MUST be loaded last)
if [[ -f "/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    source "/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi
