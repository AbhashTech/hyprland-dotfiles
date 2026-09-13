# User-Specific Hyprland Configuration Modules

Files in this directory allow you to customize your desktop environment without modifying the upstream dotfiles repository. All files here are ignored by Git.

Each file is dedicated to a specific category and loaded automatically if it exists:

| File | Purpose | Example Usage |
|---|---|---|
| `monitors.lua` | Display layouts, resolutions & scaling | `hyprland.monitor("DP-1, 2560x1440@144, 0x0, 1")` |
| `input.lua` | Keyboard layout, mouse sensitivity & touchpad | `hyprland.input({ kb_layout = "us,de", kb_options = "grp:alt_shift_toggle" })` |
| `keybinds.lua` | Personal hotkeys and custom shortcuts | `hyprland.bind("SUPER, Return, exec, foot")` |
| `rules.lua` | Custom windowrules and layer rules | `hyprland.windowrule("float, class:^(pavucontrol)$")` |
| `autostart.lua` | Personal background apps and daemons | `hyprland.exec_once("discord --start-minimized")` |
| `env.lua` | Personal Hyprland environment variables | `hyprland.env("GDK_SCALE, 1")` |
| `workspaces.lua` | Custom workspace pinning and behavior | `hyprland.workspace("1, monitor:DP-1, default:true")` |

> [!TIP]
> You can manage, export, and backup your personal configuration files across devices using `~/.dotfiles/scripts/dotfiles-personal.sh`.
