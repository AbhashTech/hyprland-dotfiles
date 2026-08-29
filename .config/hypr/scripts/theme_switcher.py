#!/usr/bin/env python3
"""
=============================================================================
Universal Desktop Theme Switcher & Palette Manager
=============================================================================
Manages and live-applies color palettes and themes across:
- Hyprland (Borders, shadows, blur, Lua variables)
- Waybar (CSS color definitions & live reload)
- Fuzzel (RGBA launcher palette)
- Kitty (Terminal 16 colors, cursor, borders, tabs)
- Mako (Notification daemon colors & live reload)
- Wofi & Wlogout (CSS glassmorphic styles)
- Hyprlock (Lockscreen color variables)
- Starship Prompt (Dynamic palette selection)
- Zellij Multiplexer (Themes & layouts)
- Btop++ System Monitor (Theme files & config)
- Lazygit (TUI git theme)
- Swappy (Annotation accent color)

Provides CLI management and an interactive Fuzzel / Wofi GUI menu (SUPER + T).
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths
HOME = Path.home()
CONFIG_DIR = HOME / ".config"
DOTFILES_DIR = HOME / ".dotfiles" / ".config"
CACHE_DIR = HOME / ".cache"
STATE_FILE = CACHE_DIR / "hypr_theme_state.json"
CURRENT_THEME_TXT = CACHE_DIR / "current_theme"

# ANSI Colors for CLI
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[38;2;166;227;161m"
C_BLUE = "\033[38;2;137;180;250m"
C_YELLOW = "\033[38;2;249;226;175m"
C_RED = "\033[38;2;243;139;168m"
C_MAUVE = "\033[38;2;203;166;247m"
C_CYAN = "\033[38;2;148;226;213m"
C_GRAY = "\033[38;2;108;112;134m"

# =============================================================================
# 🎨 Comprehensive Theme Definitions Registry
# =============================================================================
THEMES = {
    "catppuccin-mocha": {
        "name": "Catppuccin Mocha",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Warm, soothing dark pastel aesthetic",
        "colors": {
            "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
            "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
            "overlay0": "#6c7086", "overlay1": "#7f849c", "overlay2": "#9399b2",
            "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
            "blue": "#89b4fa", "lavender": "#b4befe", "sapphire": "#74c7ec",
            "sky": "#89dceb", "teal": "#94e2d5", "green": "#a6e3a1",
            "yellow": "#f9e2af", "peach": "#fab387", "maroon": "#eba0ac",
            "red": "#f38ba8", "mauve": "#cba6f7", "pink": "#f5c2e7",
            "flamingo": "#f2cdcd", "rosewater": "#f5e0dc",
            "accent": "#cba6f7",
            "active_border_1": "rgba(cba6f7ee)",
            "active_border_2": "rgba(89b4faee)",
            "inactive_border": "rgba(313244aa)",
            "shadow_hex": "0xee11111b",
            "shadow_css": "rgba(17, 17, 27, 0.6)",
        },
        "terminal": {
            "color0": "#45475a", "color8": "#585b70",
            "color1": "#f38ba8", "color9": "#f38ba8",
            "color2": "#a6e3a1", "color10": "#a6e3a1",
            "color3": "#f9e2af", "color11": "#f9e2af",
            "color4": "#89b4fa", "color12": "#89b4fa",
            "color5": "#cba6f7", "color13": "#cba6f7",
            "color6": "#94e2d5", "color14": "#94e2d5",
            "color7": "#bac2de", "color15": "#a6adc8",
        },
        "starship_palette": "catppuccin_mocha",
    },

    "catppuccin-macchiato": {
        "name": "Catppuccin Macchiato",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Medium-contrast dark pastel palette",
        "colors": {
            "base": "#24273a", "mantle": "#1e2030", "crust": "#181926",
            "surface0": "#363a4f", "surface1": "#494d64", "surface2": "#5b6078",
            "overlay0": "#6e738d", "overlay1": "#8087a2", "overlay2": "#939ab7",
            "text": "#cad3f5", "subtext0": "#a5adcb", "subtext1": "#b8c0e0",
            "blue": "#8aadf4", "lavender": "#b7bdf8", "sapphire": "#7dc4e4",
            "sky": "#91d7e3", "teal": "#8bd5ca", "green": "#a6da95",
            "yellow": "#eed49f", "peach": "#f5a97f", "maroon": "#ee99a0",
            "red": "#ed8796", "mauve": "#c6a0f6", "pink": "#f5bde6",
            "flamingo": "#f0c6c6", "rosewater": "#f4dbd6",
            "accent": "#c6a0f6",
            "active_border_1": "rgba(c6a0f6ee)",
            "active_border_2": "rgba(8aadf4ee)",
            "inactive_border": "rgba(363a4faa)",
            "shadow_hex": "0xee181926",
            "shadow_css": "rgba(24, 25, 38, 0.6)",
        },
        "terminal": {
            "color0": "#494d64", "color8": "#5b6078",
            "color1": "#ed8796", "color9": "#ed8796",
            "color2": "#a6da95", "color10": "#a6da95",
            "color3": "#eed49f", "color11": "#eed49f",
            "color4": "#8aadf4", "color12": "#8aadf4",
            "color5": "#c6a0f6", "color13": "#c6a0f6",
            "color6": "#8bd5ca", "color14": "#8bd5ca",
            "color7": "#b8c0e0", "color15": "#a5adcb",
        },
        "starship_palette": "catppuccin_macchiato",
    },

    "catppuccin-frappe": {
        "name": "Catppuccin Frappé",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Soft, low-contrast dark slate palette",
        "colors": {
            "base": "#303446", "mantle": "#292c3c", "crust": "#232634",
            "surface0": "#414559", "surface1": "#51576d", "surface2": "#626880",
            "overlay0": "#737994", "overlay1": "#838ba7", "overlay2": "#949cbb",
            "text": "#c6d0f5", "subtext0": "#a5b0d6", "subtext1": "#b5bfe2",
            "blue": "#8caaee", "lavender": "#babbf1", "sapphire": "#85c1dc",
            "sky": "#99d1db", "teal": "#81c8be", "green": "#a6d189",
            "yellow": "#e5c890", "peach": "#ef9f76", "maroon": "#ea999c",
            "red": "#e78284", "mauve": "#ca9ee6", "pink": "#f4b8e4",
            "flamingo": "#eebebe", "rosewater": "#f2d5cf",
            "accent": "#ca9ee6",
            "active_border_1": "rgba(ca9ee6ee)",
            "active_border_2": "rgba(8caaeeee)",
            "inactive_border": "rgba(414559aa)",
            "shadow_hex": "0xee232634",
            "shadow_css": "rgba(35, 38, 52, 0.6)",
        },
        "terminal": {
            "color0": "#51576d", "color8": "#626880",
            "color1": "#e78284", "color9": "#e78284",
            "color2": "#a6d189", "color10": "#a6d189",
            "color3": "#e5c890", "color11": "#e5c890",
            "color4": "#8caaee", "color12": "#8caaee",
            "color5": "#ca9ee6", "color13": "#ca9ee6",
            "color6": "#81c8be", "color14": "#81c8be",
            "color7": "#b5bfe2", "color15": "#a5b0d6",
        },
        "starship_palette": "catppuccin_frappe",
    },

    "catppuccin-latte": {
        "name": "Catppuccin Latte",
        "icon": "󰄰",
        "type": "light",
        "desc": "Crisp, clean, elegant light palette",
        "colors": {
            "base": "#eff1f5", "mantle": "#e6e9ef", "crust": "#dce0e8",
            "surface0": "#ccd0da", "surface1": "#bcc0cc", "surface2": "#acb0be",
            "overlay0": "#9ca0b0", "overlay1": "#8c8fa1", "overlay2": "#7c7f93",
            "text": "#4c4f69", "subtext0": "#6c6f85", "subtext1": "#5c5f77",
            "blue": "#1e66f5", "lavender": "#7287fd", "sapphire": "#209fb5",
            "sky": "#04a5e5", "teal": "#179299", "green": "#40a02b",
            "yellow": "#df8e1d", "peach": "#fe640b", "maroon": "#e64553",
            "red": "#d20f39", "mauve": "#8839ef", "pink": "#ea76cb",
            "flamingo": "#dd7878", "rosewater": "#dc8a78",
            "accent": "#8839ef",
            "active_border_1": "rgba(8839efee)",
            "active_border_2": "rgba(1e66f5ee)",
            "inactive_border": "rgba(ccd0daaa)",
            "shadow_hex": "0x55000000",
            "shadow_css": "rgba(0, 0, 0, 0.15)",
        },
        "terminal": {
            "color0": "#5c5f77", "color8": "#6c6f85",
            "color1": "#d20f39", "color9": "#d20f39",
            "color2": "#40a02b", "color10": "#40a02b",
            "color3": "#df8e1d", "color11": "#df8e1d",
            "color4": "#1e66f5", "color12": "#1e66f5",
            "color5": "#8839ef", "color13": "#8839ef",
            "color6": "#179299", "color14": "#179299",
            "color7": "#acb0be", "color15": "#bcc0cc",
        },
        "starship_palette": "catppuccin_latte",
    },

    "tokyo-night": {
        "name": "Tokyo Night",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Iconic cyberpunk dark blue & neon violet",
        "colors": {
            "base": "#1a1b26", "mantle": "#16161e", "crust": "#13141c",
            "surface0": "#24283b", "surface1": "#292e42", "surface2": "#3b4261",
            "overlay0": "#565f89", "overlay1": "#737aa2", "overlay2": "#9aa5ce",
            "text": "#c0caf5", "subtext0": "#9aa5ce", "subtext1": "#a9b1d6",
            "blue": "#7aa2f7", "lavender": "#b4f9f8", "sapphire": "#7dcfff",
            "sky": "#70a5fd", "teal": "#73daca", "green": "#9ece6a",
            "yellow": "#e0af68", "peach": "#ff9e64", "maroon": "#f7768e",
            "red": "#f7768e", "mauve": "#bb9af7", "pink": "#bb9af7",
            "flamingo": "#ff9e64", "rosewater": "#f7768e",
            "accent": "#7aa2f7",
            "active_border_1": "rgba(bb9af7ee)",
            "active_border_2": "rgba(7aa2f7ee)",
            "inactive_border": "rgba(24283baa)",
            "shadow_hex": "0xee13141c",
            "shadow_css": "rgba(19, 20, 28, 0.6)",
        },
        "terminal": {
            "color0": "#15161e", "color8": "#414868",
            "color1": "#f7768e", "color9": "#f7768e",
            "color2": "#9ece6a", "color10": "#9ece6a",
            "color3": "#e0af68", "color11": "#e0af68",
            "color4": "#7aa2f7", "color12": "#7aa2f7",
            "color5": "#bb9af7", "color13": "#bb9af7",
            "color6": "#7dcfff", "color14": "#7dcfff",
            "color7": "#a9b1d6", "color15": "#c0caf5",
        },
        "starship_palette": "tokyo_night",
    },

    "nord": {
        "name": "Nord Arctic",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Arctic, cold bluish clean and minimal palette",
        "colors": {
            "base": "#2e3440", "mantle": "#242933", "crust": "#1e222a",
            "surface0": "#3b4252", "surface1": "#434c5e", "surface2": "#4c566a",
            "overlay0": "#616e88", "overlay1": "#707d97", "overlay2": "#8190a8",
            "text": "#eceff4", "subtext0": "#d8dee9", "subtext1": "#e5e9f0",
            "blue": "#81a1c1", "lavender": "#88c0d0", "sapphire": "#5e81ac",
            "sky": "#88c0d0", "teal": "#8fbcbb", "green": "#a3be8c",
            "yellow": "#ebcb8b", "peach": "#d08770", "maroon": "#bf616a",
            "red": "#bf616a", "mauve": "#b48ead", "pink": "#b48ead",
            "flamingo": "#d08770", "rosewater": "#eceff4",
            "accent": "#88c0d0",
            "active_border_1": "rgba(88c0d0ee)",
            "active_border_2": "rgba(81a1c1ee)",
            "inactive_border": "rgba(3b4252aa)",
            "shadow_hex": "0xee1e222a",
            "shadow_css": "rgba(30, 34, 42, 0.6)",
        },
        "terminal": {
            "color0": "#3b4252", "color8": "#4c566a",
            "color1": "#bf616a", "color9": "#bf616a",
            "color2": "#a3be8c", "color10": "#a3be8c",
            "color3": "#ebcb8b", "color11": "#ebcb8b",
            "color4": "#81a1c1", "color12": "#81a1c1",
            "color5": "#b48ead", "color13": "#b48ead",
            "color6": "#88c0d0", "color14": "#8fbcbb",
            "color7": "#e5e9f0", "color15": "#eceff4",
        },
        "starship_palette": "nord",
    },

    "gruvbox-dark": {
        "name": "Gruvbox Dark",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Retro groove earthy warm golden tones",
        "colors": {
            "base": "#282828", "mantle": "#1d2021", "crust": "#141617",
            "surface0": "#3c3836", "surface1": "#504945", "surface2": "#665c54",
            "overlay0": "#7c6f64", "overlay1": "#928374", "overlay2": "#a89984",
            "text": "#ebdbb2", "subtext0": "#bdae93", "subtext1": "#d5c4a1",
            "blue": "#458588", "lavender": "#83a598", "sapphire": "#83a598",
            "sky": "#8ec07c", "teal": "#689d6a", "green": "#b8bb26",
            "yellow": "#fabd2f", "peach": "#fe8019", "maroon": "#d65d0e",
            "red": "#fb4934", "mauve": "#d3869b", "pink": "#d3869b",
            "flamingo": "#fe8019", "rosewater": "#ebdbb2",
            "accent": "#fabd2f",
            "active_border_1": "rgba(fabd2fee)",
            "active_border_2": "rgba(fe8019ee)",
            "inactive_border": "rgba(3c3836aa)",
            "shadow_hex": "0xee141617",
            "shadow_css": "rgba(20, 22, 23, 0.6)",
        },
        "terminal": {
            "color0": "#282828", "color8": "#928374",
            "color1": "#cc241d", "color9": "#fb4934",
            "color2": "#98971a", "color10": "#b8bb26",
            "color3": "#d79921", "color11": "#fabd2f",
            "color4": "#458588", "color12": "#83a598",
            "color5": "#b16286", "color13": "#d3869b",
            "color6": "#689d6a", "color14": "#8ec07c",
            "color7": "#a89984", "color15": "#ebdbb2",
        },
        "starship_palette": "gruvbox_dark",
    },

    "rose-pine": {
        "name": "Rosé Pine",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Soho minimalist vibes, warm pine, gold & rose",
        "colors": {
            "base": "#191724", "mantle": "#1f1d2e", "crust": "#14121f",
            "surface0": "#26233a", "surface1": "#312f44", "surface2": "#403d52",
            "overlay0": "#524f67", "overlay1": "#6e6a86", "overlay2": "#908caa",
            "text": "#e0def4", "subtext0": "#908caa", "subtext1": "#9ccfd8",
            "blue": "#31748f", "lavender": "#c4a7e7", "sapphire": "#9ccfd8",
            "sky": "#9ccfd8", "teal": "#ebbcba", "green": "#31748f",
            "yellow": "#f6c177", "peach": "#eb6f92", "maroon": "#eb6f92",
            "red": "#eb6f92", "mauve": "#c4a7e7", "pink": "#ebbcba",
            "flamingo": "#f6c177", "rosewater": "#ebbcba",
            "accent": "#ebbcba",
            "active_border_1": "rgba(ebbcbaee)",
            "active_border_2": "rgba(c4a7e7ee)",
            "inactive_border": "rgba(26233aaa)",
            "shadow_hex": "0xee14121f",
            "shadow_css": "rgba(20, 18, 31, 0.6)",
        },
        "terminal": {
            "color0": "#26233a", "color8": "#6e6a86",
            "color1": "#eb6f92", "color9": "#eb6f92",
            "color2": "#31748f", "color10": "#31748f",
            "color3": "#f6c177", "color11": "#f6c177",
            "color4": "#9ccfd8", "color12": "#9ccfd8",
            "color5": "#c4a7e7", "color13": "#c4a7e7",
            "color6": "#ebbcba", "color14": "#ebbcba",
            "color7": "#e0def4", "color15": "#e0def4",
        },
        "starship_palette": "rose_pine",
    },

    "dracula": {
        "name": "Dracula",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Classic dark purple, neon pink and green",
        "colors": {
            "base": "#282a36", "mantle": "#21222c", "crust": "#191a21",
            "surface0": "#343746", "surface1": "#44475a", "surface2": "#6272a4",
            "overlay0": "#6272a4", "overlay1": "#7d8dbd", "overlay2": "#9aa7d3",
            "text": "#f8f8f2", "subtext0": "#bfbfbf", "subtext1": "#e2e2dc",
            "blue": "#6272a4", "lavender": "#bd93f9", "sapphire": "#8be9fd",
            "sky": "#8be9fd", "teal": "#8be9fd", "green": "#50fa7b",
            "yellow": "#f1fa8c", "peach": "#ffb86c", "maroon": "#ff5555",
            "red": "#ff5555", "mauve": "#bd93f9", "pink": "#ff79c6",
            "flamingo": "#ffb86c", "rosewater": "#f8f8f2",
            "accent": "#bd93f9",
            "active_border_1": "rgba(bd93f9ee)",
            "active_border_2": "rgba(ff79c6ee)",
            "inactive_border": "rgba(343746aa)",
            "shadow_hex": "0xee191a21",
            "shadow_css": "rgba(25, 26, 33, 0.6)",
        },
        "terminal": {
            "color0": "#21222c", "color8": "#6272a4",
            "color1": "#ff5555", "color9": "#ff6e6e",
            "color2": "#50fa7b", "color10": "#69ff94",
            "color3": "#f1fa8c", "color11": "#ffffa5",
            "color4": "#bd93f9", "color12": "#d6acff",
            "color5": "#ff79c6", "color13": "#ff92df",
            "color6": "#8be9fd", "color14": "#a4ffff",
            "color7": "#f8f8f2", "color15": "#ffffff",
        },
        "starship_palette": "dracula",
    },

    "everforest": {
        "name": "Everforest Dark",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Comfortable natural green & warm moss tones",
        "colors": {
            "base": "#2d353b", "mantle": "#232a2e", "crust": "#1e2326",
            "surface0": "#343f44", "surface1": "#3d484d", "surface2": "#475258",
            "overlay0": "#56635f", "overlay1": "#7a8478", "overlay2": "#859289",
            "text": "#d3c6aa", "subtext0": "#9da9a0", "subtext1": "#bdc3af",
            "blue": "#7fbbb3", "lavender": "#d699b6", "sapphire": "#7fbbb3",
            "sky": "#83c092", "teal": "#83c092", "green": "#a7c080",
            "yellow": "#dbbc7f", "peach": "#e69875", "maroon": "#e67e80",
            "red": "#e67e80", "mauve": "#d699b6", "pink": "#d699b6",
            "flamingo": "#e69875", "rosewater": "#d3c6aa",
            "accent": "#a7c080",
            "active_border_1": "rgba(a7c080ee)",
            "active_border_2": "rgba(7fbbb3ee)",
            "inactive_border": "rgba(343f44aa)",
            "shadow_hex": "0xee1e2326",
            "shadow_css": "rgba(30, 35, 38, 0.6)",
        },
        "terminal": {
            "color0": "#2d353b", "color8": "#475258",
            "color1": "#e67e80", "color9": "#e67e80",
            "color2": "#a7c080", "color10": "#a7c080",
            "color3": "#dbbc7f", "color11": "#dbbc7f",
            "color4": "#7fbbb3", "color12": "#7fbbb3",
            "color5": "#d699b6", "color13": "#d699b6",
            "color6": "#83c092", "color14": "#83c092",
            "color7": "#d3c6aa", "color15": "#d3c6aa",
        },
        "starship_palette": "everforest",
    },

    "one-dark": {
        "name": "One Dark Pro",
        "icon": "󰄯",
        "type": "dark",
        "desc": "Atom iconic balanced dark aesthetic",
        "colors": {
            "base": "#282c34", "mantle": "#21252b", "crust": "#1b1d23",
            "surface0": "#2c313a", "surface1": "#3e4451", "surface2": "#4b5263",
            "overlay0": "#5c6370", "overlay1": "#6b7280", "overlay2": "#828997",
            "text": "#abb2bf", "subtext0": "#828997", "subtext1": "#9da5b4",
            "blue": "#61afef", "lavender": "#c678dd", "sapphire": "#56b6c2",
            "sky": "#56b6c2", "teal": "#56b6c2", "green": "#98c379",
            "yellow": "#e5c07b", "peach": "#d19a66", "maroon": "#e06c75",
            "red": "#e06c75", "mauve": "#c678dd", "pink": "#c678dd",
            "flamingo": "#d19a66", "rosewater": "#abb2bf",
            "accent": "#61afef",
            "active_border_1": "rgba(61afefee)",
            "active_border_2": "rgba(c678ddee)",
            "inactive_border": "rgba(2c313aaa)",
            "shadow_hex": "0xee1b1d23",
            "shadow_css": "rgba(27, 29, 35, 0.6)",
        },
        "terminal": {
            "color0": "#282c34", "color8": "#5c6370",
            "color1": "#e06c75", "color9": "#e06c75",
            "color2": "#98c379", "color10": "#98c379",
            "color3": "#e5c07b", "color11": "#e5c07b",
            "color4": "#61afef", "color12": "#61afef",
            "color5": "#c678dd", "color13": "#c678dd",
            "color6": "#56b6c2", "color14": "#56b6c2",
            "color7": "#abb2bf", "color15": "#c8ccd4",
        },
        "starship_palette": "one_dark",
    },

    "cyberpunk": {
        "name": "Cyberpunk Synthwave",
        "icon": "󰄯",
        "type": "dark",
        "desc": "High-octane neon magenta, cyan & deep navy",
        "colors": {
            "base": "#120f26", "mantle": "#0c091d", "crust": "#080614",
            "surface0": "#221b3b", "surface1": "#2d244c", "surface2": "#3e3266",
            "overlay0": "#5a4b87", "overlay1": "#7865b0", "overlay2": "#9884d6",
            "text": "#e0f8ff", "subtext0": "#a0e8f8", "subtext1": "#c0f0fc",
            "blue": "#00f0ff", "lavender": "#d800ff", "sapphire": "#00c8ff",
            "sky": "#00f0ff", "teal": "#00ffb2", "green": "#05ffa1",
            "yellow": "#ffe600", "peach": "#ff7700", "maroon": "#ff0055",
            "red": "#ff0055", "mauve": "#ff0077", "pink": "#ff00a0",
            "flamingo": "#ff5500", "rosewater": "#ffe6f0",
            "accent": "#ff0077",
            "active_border_1": "rgba(ff0077ee)",
            "active_border_2": "rgba(00f0ffee)",
            "inactive_border": "rgba(221b3baa)",
            "shadow_hex": "0xee080614",
            "shadow_css": "rgba(8, 6, 20, 0.7)",
        },
        "terminal": {
            "color0": "#120f26", "color8": "#5a4b87",
            "color1": "#ff0055", "color9": "#ff2a6d",
            "color2": "#05ffa1", "color10": "#05ffa1",
            "color3": "#ffe600", "color11": "#ffe600",
            "color4": "#00f0ff", "color12": "#00f0ff",
            "color5": "#ff0077", "color13": "#d800ff",
            "color6": "#00ffb2", "color14": "#00ffb2",
            "color7": "#e0f8ff", "color15": "#ffffff",
        },
        "starship_palette": "cyberpunk",
    },
}

DEFAULT_THEME = "catppuccin-mocha"

# =============================================================================
# Helper Utilities
# =============================================================================
def hex_to_rgb_tuple(hex_str):
    """Convert hex string (e.g. #cba6f7) to tuple of ints (r, g, b)."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (200, 200, 200)

def hex_to_rgba_str(hex_str, alpha="ff"):
    """Convert hex (#1e1e2e) to rgba(1e1e2eff) or RGBA hex string."""
    clean = hex_str.lstrip("#")
    return f"{clean}{alpha}"

def ensure_dirs():
    """Ensure config and cache directories exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "hypr").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "waybar").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "kitty").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "fuzzel").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "wofi").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "wlogout").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "btop" / "themes").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "zellij").mkdir(parents=True, exist_ok=True)

def get_current_theme():
    """Get ID of currently active theme."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                theme_id = data.get("current_theme")
                if theme_id in THEMES:
                    return theme_id
        except Exception:
            pass
    if CURRENT_THEME_TXT.exists():
        try:
            tid = CURRENT_THEME_TXT.read_text().strip()
            if tid in THEMES:
                return tid
        except Exception:
            pass
    return DEFAULT_THEME

def save_state(theme_id):
    """Save active theme ID to cache files."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"current_theme": theme_id}, f, indent=2)
        CURRENT_THEME_TXT.write_text(theme_id)
    except Exception as e:
        print(f"Error saving state: {e}", file=sys.stderr)

# =============================================================================
# Generator Functions for Components
# =============================================================================
def generate_hypr_lua_vars(theme):
    """Generate ~/.config/hypr/theme_vars.lua for Hyprland."""
    c = theme["colors"]
    content = f"""-- Auto-generated by theme_switcher.py for Hyprland
return {{
    name            = "{theme['name']}",
    id              = "{theme['id']}",
    base            = "rgba({c['base'].lstrip('#')}ff)",
    mantle          = "rgba({c['mantle'].lstrip('#')}ff)",
    crust           = "rgba({c['crust'].lstrip('#')}ff)",
    surface0        = "rgba({c['surface0'].lstrip('#')}ff)",
    surface1        = "rgba({c['surface1'].lstrip('#')}ff)",
    surface2        = "rgba({c['surface2'].lstrip('#')}ff)",
    text            = "rgba({c['text'].lstrip('#')}ff)",
    subtext0        = "rgba({c['subtext0'].lstrip('#')}ff)",
    subtext1        = "rgba({c['subtext1'].lstrip('#')}ff)",
    active_border_1 = "{c['active_border_1']}",
    active_border_2 = "{c['active_border_2']}",
    inactive_border = "{c['inactive_border']}",
    shadow          = {c['shadow_hex']},
    accent          = "rgba({c['accent'].lstrip('#')}ff)",
}}
"""
    target = CONFIG_DIR / "hypr" / "theme_vars.lua"
    target.write_text(content)
    # Also write to dotfiles if dotfiles dir exists
    df_target = DOTFILES_DIR / "hypr" / "theme_vars.lua"
    if df_target.parent.exists():
        df_target.write_text(content)

def generate_hypr_conf(theme):
    """Generate ~/.config/hypr/theme.conf for Hyprland / Hyprlock."""
    c = theme["colors"]
    lines = [f"# Hyprland & Hyprlock Theme: {theme['name']}"]
    for k, hex_val in c.items():
        if hex_val.startswith("#"):
            r, g, b = hex_to_rgb_tuple(hex_val)
            lines.append(f"${k} = rgb({r}, {g}, {b})")
    content = "\n".join(lines) + "\n"
    (CONFIG_DIR / "hypr" / "theme.conf").write_text(content)
    if (DOTFILES_DIR / "hypr").exists():
        (DOTFILES_DIR / "hypr" / "theme.conf").write_text(content)

def generate_waybar_colors(theme):
    """Generate ~/.config/waybar/colors.css for Waybar."""
    c = theme["colors"]
    lines = [f"/* Waybar Colors: {theme['name']} */"]
    for k, hex_val in c.items():
        if hex_val.startswith("#"):
            lines.append(f"@define-color {k} {hex_val};")
    content = "\n".join(lines) + "\n"
    (CONFIG_DIR / "waybar" / "colors.css").write_text(content)
    if (DOTFILES_DIR / "waybar").exists():
        (DOTFILES_DIR / "waybar" / "colors.css").write_text(content)

def generate_wofi_colors(theme):
    """Generate ~/.config/wofi/colors.css for Wofi."""
    c = theme["colors"]
    lines = [f"/* Wofi Colors: {theme['name']} */"]
    for k, hex_val in c.items():
        if hex_val.startswith("#"):
            lines.append(f"@define-color {k} {hex_val};")
    content = "\n".join(lines) + "\n"
    (CONFIG_DIR / "wofi" / "colors.css").write_text(content)
    if (DOTFILES_DIR / "wofi").exists():
        (DOTFILES_DIR / "wofi" / "colors.css").write_text(content)

def generate_wlogout_colors(theme):
    """Generate ~/.config/wlogout/colors.css for Wlogout."""
    c = theme["colors"]
    r, g, b = hex_to_rgb_tuple(c["crust"])
    content = f"""/* Wlogout Colors: {theme['name']} */
@define-color base            {c['base']};
@define-color mantle          {c['mantle']};
@define-color crust           {c['crust']};
@define-color text            {c['text']};
@define-color surface0        {c['surface0']};
@define-color surface1        {c['surface1']};
@define-color accent          {c['accent']};
@define-color bg_overlay      rgba({r}, {g}, {b}, 0.75);
"""
    (CONFIG_DIR / "wlogout" / "colors.css").write_text(content)
    if (DOTFILES_DIR / "wlogout").exists():
        (DOTFILES_DIR / "wlogout" / "colors.css").write_text(content)

def generate_kitty_theme(theme):
    """Generate ~/.config/kitty/theme.conf for Kitty."""
    c = theme["colors"]
    t = theme["terminal"]
    content = f"""# =============================================================================
# Kitty Theme Colors - {theme['name']}
# =============================================================================

# Window borders
active_border_color {c['accent']}
inactive_border_color {c['surface0']}
bell_border_color {c['red']}

# Cursor
cursor {c['rosewater']}
cursor_text_color {c['crust']}

# URL
url_color {c['blue']}

# Tabs
active_tab_foreground   {c['crust']}
active_tab_background   {c['accent']}
inactive_tab_foreground {c['text']}
inactive_tab_background {c['mantle']}
tab_bar_background      {c['crust']}

# Color Scheme
background {c['base']}
foreground {c['text']}
selection_background {c['surface2']}
selection_foreground {c['text']}

# Black
color0 {t['color0']}
color8 {t['color8']}

# Red
color1 {t['color1']}
color9 {t['color9']}

# Green
color2  {t['color2']}
color10 {t['color10']}

# Yellow
color3  {t['color3']}
color11 {t['color11']}

# Blue
color4  {t['color4']}
color12 {t['color12']}

# Magenta / Mauve
color5  {t['color5']}
color13 {t['color13']}

# Cyan / Teal
color6  {t['color6']}
color14 {t['color14']}

# White
color7  {t['color7']}
color15 {t['color15']}
"""
    (CONFIG_DIR / "kitty" / "theme.conf").write_text(content)
    if (DOTFILES_DIR / "kitty").exists():
        (DOTFILES_DIR / "kitty" / "theme.conf").write_text(content)

def update_fuzzel_colors(theme):
    """Update ~/.config/fuzzel/fuzzel.ini colors section."""
    c = theme["colors"]
    fuzzel_file = CONFIG_DIR / "fuzzel" / "fuzzel.ini"
    df_fuzzel = DOTFILES_DIR / "fuzzel" / "fuzzel.ini"
    
    target_files = [fuzzel_file]
    if df_fuzzel.exists() and df_fuzzel not in target_files:
        target_files.append(df_fuzzel)

    bg_rgba = hex_to_rgba_str(c["mantle"], "ea")
    text_rgba = hex_to_rgba_str(c["text"], "ff")
    prompt_rgba = hex_to_rgba_str(c["accent"], "ff")
    placeholder_rgba = hex_to_rgba_str(c["overlay0"], "ff")
    input_rgba = hex_to_rgba_str(c["text"], "ff")
    match_rgba = hex_to_rgba_str(c["accent"], "ff")
    selection_rgba = hex_to_rgba_str(c["surface0"], "ff")
    sel_text_rgba = "ffffffef"
    sel_match_rgba = hex_to_rgba_str(c["pink"], "ff")
    border_rgba = hex_to_rgba_str(c["accent"], "88")

    colors_section = f"""[colors]
# {theme['name']} RGBA
background={bg_rgba}
text={text_rgba}
prompt={prompt_rgba}
placeholder={placeholder_rgba}
input={input_rgba}
match={match_rgba}
selection={selection_rgba}
selection-text={sel_text_rgba}
selection-match={sel_match_rgba}
border={border_rgba}

"""

    for fpath in target_files:
        if fpath.exists():
            try:
                content = fpath.read_text()
                if "[colors]" in content:
                    import re
                    content = re.sub(r"\[colors\][\s\S]*?(?=\n\[|\Z)", colors_section.rstrip() + "\n", content)
                    fpath.write_text(content)
            except Exception as e:
                print(f"Error updating fuzzel {fpath}: {e}", file=sys.stderr)


def update_mako_colors(theme):
    """Update ~/.config/mako/config with theme colors."""
    c = theme["colors"]
    mako_file = CONFIG_DIR / "mako" / "config"
    df_mako = DOTFILES_DIR / "mako" / "config"
    
    targets = [mako_file]
    if df_mako.exists() and df_mako not in targets:
        targets.append(df_mako)

    bg_color = f"{c['base']}e6"
    text_color = c["text"]
    border_color = c["accent"]
    progress_color = f"over {c['surface0']}"
    low_border = c["blue"]
    normal_border = c["accent"]
    crit_border = c["red"]
    crit_text = c["red"]

    for fpath in targets:
        if fpath.exists():
            try:
                lines = fpath.read_text().splitlines()
                new_lines = []
                current_section = "main"
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("[") and stripped.endswith("]"):
                        current_section = stripped[1:-1]
                        new_lines.append(line)
                        continue
                    
                    if current_section == "main":
                        if stripped.startswith("background-color="):
                            new_lines.append(f"background-color={bg_color}")
                        elif stripped.startswith("text-color="):
                            new_lines.append(f"text-color={text_color}")
                        elif stripped.startswith("border-color="):
                            new_lines.append(f"border-color={border_color}")
                        elif stripped.startswith("progress-color="):
                            new_lines.append(f"progress-color={progress_color}")
                        else:
                            new_lines.append(line)
                    elif current_section == "urgency=low":
                        if stripped.startswith("border-color="):
                            new_lines.append(f"border-color={low_border}")
                        else:
                            new_lines.append(line)
                    elif current_section == "urgency=normal":
                        if stripped.startswith("border-color="):
                            new_lines.append(f"border-color={normal_border}")
                        else:
                            new_lines.append(line)
                    elif current_section == "urgency=critical":
                        if stripped.startswith("border-color="):
                            new_lines.append(f"border-color={crit_border}")
                        elif stripped.startswith("text-color="):
                            new_lines.append(f"text-color={crit_text}")
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                fpath.write_text("\n".join(new_lines) + "\n")
            except Exception as e:
                print(f"Error updating mako {fpath}: {e}", file=sys.stderr)

def generate_btop_theme(theme):
    """Generate theme file for btop and update btop.conf."""
    c = theme["colors"]
    t = theme["terminal"]
    theme_id = theme["id"]
    
    # Btop theme content
    theme_content = f"""# Btop theme: {theme['name']}
theme[main_bg]="{c['base']}"
theme[main_fg]="{c['text']}"
theme[title]="{c['accent']}"
theme[hi_fg]="{c['blue']}"
theme[selected_bg]="{c['surface0']}"
theme[selected_fg]="{c['accent']}"
theme[inactive_fg]="{c['overlay0']}"
theme[graph_text]="{c['subtext0']}"
theme[proc_misc]="{c['mauve']}"
theme[cpu_box]="{c['accent']}"
theme[mem_box]="{c['green']}"
theme[net_box]="{c['blue']}"
theme[proc_box]="{c['peach']}"
theme[div_line]="{c['surface0']}"
theme[temp_start]="{c['green']}"
theme[temp_mid]="{c['yellow']}"
theme[temp_end]="{c['red']}"
theme[cpu_start]="{c['teal']}"
theme[cpu_mid]="{c['blue']}"
theme[cpu_end]="{c['mauve']}"
theme[free_start]="{c['teal']}"
theme[free_mid]="{c['green']}"
theme[free_end]="{c['yellow']}"
theme[cached_start]="{c['blue']}"
theme[cached_mid]="{c['lavender']}"
theme[cached_end]="{c['mauve']}"
theme[available_start]="{c['peach']}"
theme[available_mid]="{c['yellow']}"
theme[available_end]="{c['green']}"
theme[used_start]="{c['green']}"
theme[used_mid]="{c['yellow']}"
theme[used_end]="{c['red']}"
theme[download_start]="{c['teal']}"
theme[download_mid]="{c['blue']}"
theme[download_end]="{c['mauve']}"
theme[upload_start]="{c['pink']}"
theme[upload_mid]="{c['peach']}"
theme[upload_end]="{c['red']}"
theme[process_start]="{c['teal']}"
theme[process_mid]="{c['blue']}"
theme[process_end]="{c['mauve']}"
"""
    btop_theme_dir = CONFIG_DIR / "btop" / "themes"
    btop_theme_dir.mkdir(parents=True, exist_ok=True)
    theme_file = btop_theme_dir / f"{theme_id}.theme"
    theme_file.write_text(theme_content)
    
    df_btop_dir = DOTFILES_DIR / "btop" / "themes"
    if df_btop_dir.exists():
        (df_btop_dir / f"{theme_id}.theme").write_text(theme_content)

    # Update btop.conf color_theme = "..."
    btop_conf = CONFIG_DIR / "btop" / "btop.conf"
    df_btop_conf = DOTFILES_DIR / "btop" / "btop.conf"
    for bconf in [btop_conf, df_btop_conf]:
        if bconf.exists():
            try:
                lines = bconf.read_text().splitlines()
                new_lines = []
                for l in lines:
                    if l.strip().startswith("color_theme ="):
                        new_lines.append(f'color_theme = "{theme_id}"')
                    else:
                        new_lines.append(l)
                bconf.write_text("\n".join(new_lines) + "\n")
            except Exception:
                pass

def update_starship_palette(theme):
    """Update starship.toml active palette."""
    starship_file = CONFIG_DIR / "starship.toml"
    df_starship = DOTFILES_DIR / "starship.toml"
    palette_name = theme.get("starship_palette", "catppuccin_mocha")
    c = theme["colors"]

    palette_block = f"""[palettes.{palette_name}]
rosewater = "{c['rosewater']}"
flamingo = "{c['flamingo']}"
pink = "{c['pink']}"
mauve = "{c['mauve']}"
red = "{c['red']}"
maroon = "{c['maroon']}"
peach = "{c['peach']}"
yellow = "{c['yellow']}"
green = "{c['green']}"
teal = "{c['teal']}"
sky = "{c['sky']}"
sapphire = "{c['sapphire']}"
blue = "{c['blue']}"
lavender = "{c['lavender']}"
text = "{c['text']}"
subtext1 = "{c['subtext1']}"
subtext0 = "{c['subtext0']}"
overlay2 = "{c['overlay2']}"
overlay1 = "{c['overlay1']}"
overlay0 = "{c['overlay0']}"
surface2 = "{c['surface2']}"
surface1 = "{c['surface1']}"
surface0 = "{c['surface0']}"
base = "{c['base']}"
mantle = "{c['mantle']}"
crust = "{c['crust']}"
"""

    for sfile in [starship_file, df_starship]:
        if sfile.exists():
            try:
                content = sfile.read_text()
                import re
                # Replace palette = "..."
                content = re.sub(r'palette = ".*?"', f'palette = "{palette_name}"', content)
                # Ensure palette definition exists
                if f"[palettes.{palette_name}]" not in content:
                    content = content + "\n" + palette_block
                sfile.write_text(content)
            except Exception as e:
                print(f"Error updating starship {sfile}: {e}", file=sys.stderr)

def update_zellij_theme(theme):
    """Update zellij config with theme."""
    theme_id = theme["id"]
    c = theme["colors"]
    zfile = CONFIG_DIR / "zellij" / "config.kdl"
    df_zfile = DOTFILES_DIR / "zellij" / "config.kdl"
    
    theme_def = f"""    {theme_id} {{
        bg "{c['surface2']}"
        fg "{c['text']}"
        red "{c['red']}"
        green "{c['green']}"
        blue "{c['blue']}"
        yellow "{c['yellow']}"
        magenta "{c['mauve']}"
        orange "{c['peach']}"
        cyan "{c['teal']}"
        black "{c['mantle']}"
        white "{c['text']}"
    }}"""

    for zf in [zfile, df_zfile]:
        if zf.exists():
            try:
                content = zf.read_text()
                import re
                content = re.sub(r'theme ".*?"', f'theme "{theme_id}"', content)
                if f"{theme_id} {{" not in content and "themes {" in content:
                    content = content.replace("themes {", f"themes {{\n{theme_def}")
                zf.write_text(content)
            except Exception as e:
                print(f"Error updating zellij {zf}: {e}", file=sys.stderr)

def update_lazygit_theme(theme):
    """Update lazygit config.yml colors."""
    c = theme["colors"]
    lg_file = CONFIG_DIR / "lazygit" / "config.yml"
    df_lg = DOTFILES_DIR / "lazygit" / "config.yml"
    
    lg_content = f"""# =============================================================================
# Lazygit Configuration - {theme['name']}
# =============================================================================

gui:
  theme:
    activeBorderColor:
      - '{c['accent']}'
      - bold
    inactiveBorderColor:
      - '{c['surface2']}'
    optionsTextColor:
      - '{c['blue']}'
    selectedLineBgColor:
      - '{c['surface0']}'
    cherryPickedCommitBgColor:
      - '{c['surface1']}'
    cherryPickedCommitFgColor:
      - '{c['accent']}'
    unstagedChangesColor:
      - '{c['red']}'
    defaultFgColor:
      - '{c['text']}'
    searchingActiveBorderColor:
      - '{c['yellow']}'

git:
  paging:
    colorArg: always
    pager: delta --dark --paging=never --line-numbers --hyperlinks --side-by-side
"""
    for lf in [lg_file, df_lg]:
        try:
            lf.parent.mkdir(parents=True, exist_ok=True)
            lf.write_text(lg_content)
        except Exception:
            pass

def update_swappy_color(theme):
    """Update swappy/config accent color."""
    c = theme["colors"]
    accent_clean = c["accent"].lstrip("#")
    sfile = CONFIG_DIR / "swappy" / "config"
    df_s = DOTFILES_DIR / "swappy" / "config"
    for sf in [sfile, df_s]:
        if sf.exists():
            try:
                lines = sf.read_text().splitlines()
                new_lines = []
                for l in lines:
                    if l.strip().startswith("custom_color="):
                        new_lines.append(f"custom_color={accent_clean}")
                    else:
                        new_lines.append(l)
                sf.write_text("\n".join(new_lines) + "\n")
            except Exception:
                pass

# =============================================================================
# Core Application & Live Reload
# =============================================================================
def reload_desktop():
    """Reload all active running Wayland apps/daemons."""
    # 1. Reload Hyprland
    try:
        subprocess.run(["hyprctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 2. Reload Waybar
    try:
        subprocess.run(["pkill", "-SIGUSR2", "waybar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 3. Reload Mako
    try:
        subprocess.run(["makoctl", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 4. Reload Kitty terminals
    try:
        subprocess.run(["killall", "-SIGUSR1", "kitty"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def send_theme_notification(theme):
    """Send visual desktop notification with theme information."""
    if not shutil.which("notify-send"):
        return
    c = theme["colors"]
    icon = "preferences-desktop-theme"
    title = f"🎨 Theme Applied: {theme['name']}"
    body = f"<b>Accent:</b> <span foreground=\"{c['accent']}\">████ {c['accent']}</span>  |  <b>Type:</b> {theme['type'].capitalize()}\n{theme['desc']}"
    try:
        subprocess.run(
            ["notify-send", "-a", "Theme Switcher", "-i", icon, "-r", "9944", title, body],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def apply_theme(theme_id, notify=True):
    """Apply theme by ID across all desktop configs and trigger live reloads."""
    if theme_id not in THEMES:
        print(f"{C_RED}Error: Unknown theme '{theme_id}'{C_RESET}", file=sys.stderr)
        return False

    theme = THEMES[theme_id]
    theme["id"] = theme_id
    ensure_dirs()

    # Generate all configuration components
    generate_hypr_lua_vars(theme)
    generate_hypr_conf(theme)
    generate_waybar_colors(theme)
    generate_wofi_colors(theme)
    generate_wlogout_colors(theme)
    generate_kitty_theme(theme)
    update_fuzzel_colors(theme)
    update_mako_colors(theme)
    generate_btop_theme(theme)
    update_starship_palette(theme)
    update_zellij_theme(theme)
    update_lazygit_theme(theme)
    update_swappy_color(theme)

    # Save state
    save_state(theme_id)

    # Live reload desktop
    reload_desktop()

    if notify:
        send_theme_notification(theme)

    print(f"{C_GREEN}✓ Successfully applied theme:{C_RESET} {C_BOLD}{theme['name']}{C_RESET} ({theme_id})")
    return True

# =============================================================================
# Interactive GUI Menu (Fuzzel / Wofi)
# =============================================================================
def run_interactive_menu():
    """Display an interactive Fuzzel or Wofi graphical menu to select a theme."""
    current = get_current_theme()
    menu_items = []
    
    for tid, tdata in THEMES.items():
        is_active = (tid == current)
        active_mark = "✔ " if is_active else "  "
        icon = tdata.get("icon", "🎨")
        name = tdata["name"]
        ttype = tdata.get("type", "dark").capitalize()
        desc = tdata.get("desc", "")
        # Formatted line for fuzzel
        display_line = f"{active_mark}{icon} {name:<22} │ {ttype:<5} │ {desc}"
        menu_items.append((display_line, tid))

    menu_input = "\n".join(item[0] for item in menu_items)
    selected_tid = None

    if shutil.which("fuzzel"):
        # Fuzzel dmenu
        cmd = [
            "fuzzel",
            "--dmenu",
            "--prompt", "🎨 Select Theme: ",
            "--width", "52",
            "--lines", str(len(THEMES) + 1),
        ]
        try:
            res = subprocess.run(cmd, input=menu_input, text=True, capture_output=True)
            chosen_line = res.stdout.strip()
            if chosen_line:
                for dline, tid in menu_items:
                    if dline.strip() == chosen_line:
                        selected_tid = tid
                        break
        except Exception as e:
            print(f"Error launching fuzzel: {e}", file=sys.stderr)
            
    elif shutil.which("wofi"):
        # Fallback to Wofi
        cmd = [
            "wofi",
            "--dmenu",
            "--prompt", "🎨 Select Theme",
            "--width", "550",
            "--lines", str(len(THEMES) + 1),
        ]
        try:
            res = subprocess.run(cmd, input=menu_input, text=True, capture_output=True)
            chosen_line = res.stdout.strip()
            if chosen_line:
                for dline, tid in menu_items:
                    if dline.strip() == chosen_line:
                        selected_tid = tid
                        break
        except Exception as e:
            print(f"Error launching wofi: {e}", file=sys.stderr)

    if selected_tid:
        apply_theme(selected_tid, notify=True)

# =============================================================================
# CLI Commands & Entry Point
# =============================================================================
def list_themes():
    """Print all available themes in formatted CLI output."""
    current = get_current_theme()
    print(f"\n{C_BOLD}{C_MAUVE}═════════════════════════════════════════════════════════════════════════{C_RESET}")
    print(f"{C_BOLD} 🎨 Available Themes & Color Palettes ({len(THEMES)} total){C_RESET}")
    print(f"{C_BOLD}{C_MAUVE}═════════════════════════════════════════════════════════════════════════{C_RESET}\n")

    for tid, tdata in THEMES.items():
        is_active = (tid == current)
        indicator = f"{C_GREEN}● ACTIVE{C_RESET}" if is_active else f"{C_GRAY}○{C_RESET}"
        c = tdata["colors"]
        # Print color swatches
        swatches = f"\033[38;2;{hex_to_rgb_tuple(c['base'])[0]};{hex_to_rgb_tuple(c['base'])[1]};{hex_to_rgb_tuple(c['base'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['surface0'])[0]};{hex_to_rgb_tuple(c['surface0'])[1]};{hex_to_rgb_tuple(c['surface0'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['accent'])[0]};{hex_to_rgb_tuple(c['accent'])[1]};{hex_to_rgb_tuple(c['accent'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['blue'])[0]};{hex_to_rgb_tuple(c['blue'])[1]};{hex_to_rgb_tuple(c['blue'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['green'])[0]};{hex_to_rgb_tuple(c['green'])[1]};{hex_to_rgb_tuple(c['green'])[2]}m██\033[0m" \
                   f"\033[38;2;{hex_to_rgb_tuple(c['red'])[0]};{hex_to_rgb_tuple(c['red'])[1]};{hex_to_rgb_tuple(c['red'])[2]}m██\033[0m"

        print(f"  {indicator:<18} {C_BOLD}{tdata['name']:<22}{C_RESET} [{C_CYAN}{tid:<20}{C_RESET}] {swatches}  {C_GRAY}{tdata['desc']}{C_RESET}")

    print(f"\n{C_BOLD}Tip:{C_RESET} Press {C_YELLOW}SUPER + T{C_RESET} to open the interactive theme menu.\n")

def cycle_theme(forward=True):
    """Cycle to next or previous theme in registry."""
    theme_keys = list(THEMES.keys())
    current = get_current_theme()
    try:
        idx = theme_keys.index(current)
        new_idx = (idx + 1) % len(theme_keys) if forward else (idx - 1) % len(theme_keys)
    except ValueError:
        new_idx = 0
    apply_theme(theme_keys[new_idx], notify=True)

def random_theme():
    """Apply a random theme from registry."""
    import random
    theme_keys = list(THEMES.keys())
    current = get_current_theme()
    candidates = [k for k in theme_keys if k != current]
    choice = random.choice(candidates if candidates else theme_keys)
    apply_theme(choice, notify=True)

def main():
    parser = argparse.ArgumentParser(
        description="Universal Desktop Theme Switcher & Palette Manager (SUPER + T)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-l", "--list", action="store_true", help="List all available themes and their status")
    parser.add_argument("-s", "--set", metavar="THEME_ID", help="Apply a specific theme by ID")
    parser.add_argument("-c", "--current", action="store_true", help="Display the active theme ID")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel / Wofi GUI theme selector")
    parser.add_argument("-n", "--next", action="store_true", help="Cycle to the next theme")
    parser.add_argument("-p", "--prev", action="store_true", help="Cycle to the previous theme")
    parser.add_argument("-r", "--random", action="store_true", help="Apply a random theme")
    parser.add_argument("--silent", action="store_true", help="Suppress desktop notifications")

    args = parser.parse_args()

    if args.list:
        list_themes()
    elif args.set:
        apply_theme(args.set, notify=not args.silent)
    elif args.current:
        cur = get_current_theme()
        name = THEMES.get(cur, {}).get("name", cur)
        print(f"Current theme: {name} ({cur})")
    elif args.menu:
        run_interactive_menu()
    elif args.next:
        cycle_theme(forward=True)
    elif args.prev:
        cycle_theme(forward=False)
    elif args.random:
        random_theme()
    else:
        # Default action: run interactive menu
        run_interactive_menu()

if __name__ == "__main__":
    main()
