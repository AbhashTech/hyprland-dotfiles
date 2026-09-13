# User-Specific Shell Configuration Modules

Files in this directory allow you to customize your shell environment (Bash/Zsh) without modifying the upstream dotfiles repository. All files here are ignored by Git.

Each file is dedicated to a specific category and sourced automatically:

| File | Purpose | Example Usage |
|---|---|---|
| `env.sh` / `paths.sh` | Personal environment variables and PATH additions | `export GOPATH="${HOME}/go"`, `export PATH="${PATH}:${GOPATH}/bin"` |
| `aliases.sh` | Personal command aliases | `alias gs='git status'` |
| `functions.sh` | Personal shell utility functions | Custom helper functions |
| `tokens.sh` | Private API tokens and credentials | `export GITHUB_TOKEN="..."` |

> [!TIP]
> You can manage, export, and backup your personal configuration files across devices using `~/.dotfiles/scripts/dotfiles-personal.sh`.
