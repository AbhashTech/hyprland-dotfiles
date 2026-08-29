#!/usr/bin/env python3
"""
=============================================================================
Hyprland Dynamic Keybindings Viewer & Cheat Sheet
=============================================================================
Parses Hyprland Lua keybinding configuration files dynamically, extracts
categories, descriptions from comments, and key combinations, and displays
them in an interactive Fuzzel/Wofi GUI or formatted CLI tables.
"""

import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths to search for keybind configs
POSSIBLE_CONFIG_PATHS = [
    Path.home() / ".config" / "hypr" / "modules" / "keybinds.lua",
    Path.home() / ".dotfiles" / ".config" / "hypr" / "modules" / "keybinds.lua",
    Path.home() / ".config" / "hypr" / "hyprland.lua",
]

# Catppuccin Mocha ANSI Colors for CLI output
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_MAUVE = "\033[38;2;203;166;247m"
COLOR_BLUE = "\033[38;2;137;180;250m"
COLOR_SAPPHIRE = "\033[38;2;116;199;236m"
COLOR_GREEN = "\033[38;2;166;227;161m"
COLOR_YELLOW = "\033[38;2;249;226;175m"
COLOR_PEACH = "\033[38;2;250;179;135m"
COLOR_RED = "\033[38;2;243;139;168m"


def find_keybinds_file():
    """Locate the primary keybinds configuration file."""
    for path in POSSIBLE_CONFIG_PATHS:
        if path.is_file():
            return path
    return None


def clean_comment(text):
    """Strip comment markers, dashes, and extra whitespace."""
    text = re.sub(r"^[-\s#]+", "", text).strip()
    text = re.sub(r"[-=]{3,}", "", text).strip()
    return text


def extract_inline_comment(line):
    """
    Extract trailing comment from a Lua code line, ignoring '--' inside string literals.
    """
    in_single = False
    in_double = False
    for i in range(len(line) - 1):
        char = line[i]
        if char == '"' and not in_single:
            in_double = not in_double
        elif char == "'" and not in_double:
            in_single = not in_single
        elif char == '-' and line[i+1] == '-' and not in_single and not in_double:
            comment = line[i+2:].strip()
            return clean_comment(comment)
    return None


def is_category_header(raw_line, comment_content):
    """Check if a comment represents a major section / category header."""
    if not comment_content:
        return False
    # Headers with category emoji icons
    if any(emoji in comment_content for emoji in ["🖥️", "🔔", "⚡", "🗂️", "📐", "🔊", "☀️", "📸", "🎨", "📁"]):
        return True
    if "@category" in comment_content.lower():
        return True
    return False


def parse_keybinds(file_path):
    """
    Parse keybinds.lua and extract categories, comments, and key combinations.
    """
    if not file_path or not os.path.exists(file_path):
        return []

    entries = []
    current_category = "🖥️ Core Applications & Navigation"
    pending_comments = []
    last_description = ""
    in_for_loop = False

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()

        # 1. Blank line
        if not line:
            pending_comments = []
            last_description = ""
            i += 1
            continue

        # 2. Category header detection
        if line.startswith("--"):
            comment_content = clean_comment(line)
            if is_category_header(line, comment_content):
                cat_match = re.search(r"@category\s+(.+)$", comment_content, re.IGNORECASE)
                if cat_match:
                    current_category = cat_match.group(1).strip()
                elif comment_content:
                    current_category = comment_content
                pending_comments = []
                last_description = ""
                i += 1
                continue
            elif comment_content and not comment_content.startswith("hl."):
                pending_comments.append(comment_content)
            i += 1
            continue

        # 3. Handle workspace generation loop
        if "for i = 1, 10 do" in line:
            in_for_loop = True
            entries.append({
                "key": "SUPER + [1-9, 0]",
                "desc": "Switch to Workspace 1 through 10",
                "category": current_category,
            })
            entries.append({
                "key": "SUPER + SHIFT + [1-9, 0]",
                "desc": "Move Active Window to Workspace 1 through 10",
                "category": current_category,
            })
            pending_comments = []
            last_description = ""
            i += 1
            continue

        if in_for_loop:
            if line == "end" or line.startswith("end"):
                in_for_loop = False
            i += 1
            continue

        # 4. Detect hl.bind statements
        if "hl.bind(" in line:
            # Extract key combo
            key_combo = "Unknown"
            bind_match = re.search(r"hl\.bind\(\s*([^,\)]+)", line)
            if bind_match:
                raw_key = bind_match.group(1).strip()
                cleaned_key = raw_key.replace('mainMod .. "', 'SUPER').replace('"', '').replace("'", "").replace(' .. ', '')
                cleaned_key = cleaned_key.replace("mainMod", "SUPER").strip()
                key_combo = cleaned_key

            # Look for actual inline comment (outside quotes)
            inline_desc = extract_inline_comment(line)

            # Determine description
            description = ""
            if pending_comments:
                description = " ".join(pending_comments)
                last_description = description
                pending_comments = []
            elif inline_desc:
                description = inline_desc
                last_description = description
            elif last_description:
                # Contiguous bind under same comment header
                description = last_description

            if not description:
                description = "Execute Action"

            if key_combo != "Unknown":
                entries.append({
                    "key": key_combo,
                    "desc": description,
                    "category": current_category,
                })

        i += 1

    return entries


def format_cli_table(entries):
    """Format and print keybindings in organized CLI tables."""
    if not entries:
        print("No keybindings found.")
        return

    categories = {}
    for item in entries:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    print(f"\n{COLOR_BOLD}{COLOR_MAUVE}⚡ Hyprland Dynamic Keybindings Cheat Sheet{COLOR_RESET}")
    print(f"{COLOR_DIM}Press SUPER + / or SUPER + F1 to open GUI search menu anytime{COLOR_RESET}\n")

    for cat_name, items in categories.items():
        print(f"{COLOR_BOLD}{COLOR_SAPPHIRE}─── 󰌌 {cat_name} ───{COLOR_RESET}")
        for item in items:
            key_str = f"{COLOR_YELLOW}{item['key']:<34}{COLOR_RESET}"
            desc_str = f"{COLOR_BLUE}➜{COLOR_RESET} {COLOR_BOLD}{item['desc']}{COLOR_RESET}"
            print(f"  {key_str} {desc_str}")
        print()


def show_gui_menu(entries):
    """
    Display keybindings in a compact, non-full-screen 2-line layout
    so nothing is cut off and it doesn't consume the screen height.
    """
    if not entries:
        return

    lines = []
    entry_map = {}

    for idx, item in enumerate(entries):
        key = item["key"]
        desc = item["desc"]
        cat = item["category"]

        # 2-Line Format: Shortcut on top, Description on next line
        key_line = f"󰌌 {key}"
        desc_line = f"   ↳ {desc}"

        lines.append(key_line)
        lines.append(desc_line)

        # Map both lines so selecting either works seamlessly
        entry_map[key_line] = item
        entry_map[desc_line] = item

    menu_input = "\n".join(lines)
    selected = None

    if shutil.which("fuzzel"):
        try:
            res = subprocess.run(
                [
                    "fuzzel",
                    "--dmenu",
                    "--prompt", " 󰌌 Shortcuts: ",
                    "--width", "52",    # Clean, compact modal width
                    "--lines", "10",    # Reduced height (only 10 lines visible)
                ],
                input=menu_input,
                capture_output=True,
                text=True,
                check=False
            )
            selected = res.stdout.strip()
        except Exception:
            pass
    elif shutil.which("wofi"):
        try:
            res = subprocess.run(
                [
                    "wofi",
                    "--dmenu",
                    "--prompt", "Search Shortcuts",
                    "--width", "620",
                    "--height", "340",
                    "--insensitive",
                ],
                input=menu_input,
                capture_output=True,
                text=True,
                check=False
            )
            selected = res.stdout.strip()
        except Exception:
            pass

    if selected and selected in entry_map:
        item = entry_map[selected]
        if shutil.which("wl-copy"):
            try:
                subprocess.run(["wl-copy"], input=item["key"], text=True, check=False)
            except Exception:
                pass

        if shutil.which("notify-send"):
            try:
                subprocess.run([
                    "notify-send",
                    "-a", "Shortcut Helper",
                    "-i", "preferences-desktop-keyboard-shortcuts",
                    f"⌨️ {item['key']}",
                    f"{item['desc']}\nCategory: {item['category']}\n(Copied to clipboard)"
                ], check=False)
            except Exception:
                pass


def generate_markdown(entries):
    """Generate markdown table format."""
    categories = {}
    for item in entries:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    md = ["# ⌨️ Hyprland Keybindings Reference\n"]
    for cat_name, items in categories.items():
        md.append(f"### {cat_name}\n")
        md.append("| Shortcut | Description |")
        md.append("| :--- | :--- |")
        for item in items:
            md.append(f"| `{item['key']}` | {item['desc']} |")
        md.append("")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Hyprland Dynamic Keybinding Viewer & Cheat Sheet")
    parser.add_argument("--cli", "--table", action="store_true", help="Print formatted table in CLI terminal")
    parser.add_argument("--gui", action="store_true", help="Display interactive Fuzzel/Wofi GUI (Default in desktop)")
    parser.add_argument("--json", action="store_true", help="Output keybindings in JSON format")
    parser.add_argument("--markdown", "--md", action="store_true", help="Output keybindings in Markdown table format")
    parser.add_argument("--file", "-f", type=str, help="Custom path to keybinds configuration file")

    args = parser.parse_args()

    config_file = Path(args.file) if args.file else find_keybinds_file()
    if not config_file or not config_file.is_file():
        print(f"Error: Could not find keybinds configuration file.", file=sys.stderr)
        sys.exit(1)

    entries = parse_keybinds(config_file)

    if args.json:
        print(json.dumps(entries, indent=2))
    elif args.markdown:
        print(generate_markdown(entries))
    elif args.cli or (not args.gui and not os.getenv("WAYLAND_DISPLAY")):
        format_cli_table(entries)
    else:
        show_gui_menu(entries)


if __name__ == "__main__":
    main()
