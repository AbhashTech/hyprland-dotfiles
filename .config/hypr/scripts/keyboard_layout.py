#!/usr/bin/env python3
"""
=============================================================================
Hyprland Keyboard Layout Manager & Switcher Utility
=============================================================================
Provides CLI and interactive Fuzzel GUI tools to:
- Switch / cycle active keyboard layouts live across keyboards
- Add new keyboard layouts from XKB catalog and persist them in input.lua
- Remove configured keyboard layouts
- Display desktop notifications with current layout state
- Integrate seamlessly with Waybar and Hyprland keybindings
"""

import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths
INPUT_CONFIG_PATH = Path.home() / ".config" / "hypr" / "modules" / "input.lua"
DOTFILES_INPUT_PATH = Path.home() / ".dotfiles" / ".config" / "hypr" / "modules" / "input.lua"
XKB_BASE_LST = Path("/usr/share/X11/xkb/rules/base.lst")
XKB_EVDEV_LST = Path("/usr/share/X11/xkb/rules/evdev.lst")

# Common / Popular layout shortcuts for quick discovery
POPULAR_LAYOUTS = [
    ("us", "English (US)"),
    ("gb", "English (UK)"),
    ("us(dvorak)", "English (Dvorak)"),
    ("us(colemak)", "English (Colemak)"),
    ("us(intl)", "English (US, international with altgr)"),
    ("de", "German (Germany)"),
    ("fr", "French (France)"),
    ("es", "Spanish (Spain)"),
    ("it", "Italian (Italy)"),
    ("pt", "Portuguese (Portugal)"),
    ("br", "Portuguese (Brazil, ABNT2)"),
    ("ru", "Russian"),
    ("ara", "Arabic"),
    ("in", "Indian (Hindi / Multilingual)"),
    ("jp", "Japanese"),
    ("cn", "Chinese"),
    ("kr", "Korean"),
    ("pl", "Polish"),
    ("tr", "Turkish"),
    ("ua", "Ukrainian"),
    ("se", "Swedish"),
    ("no", "Norwegian"),
    ("dk", "Danish"),
    ("fi", "Finnish"),
    ("nl", "Dutch"),
    ("cz", "Czech"),
    ("gr", "Greek"),
    ("il", "Hebrew"),
    ("ro", "Romanian"),
    ("hu", "Hungarian"),
    ("latam", "Spanish (Latin American)"),
    ("ca", "French (Canada)"),
]

def run_cmd(cmd, check=False):
    """Run shell command safely and return stdout string."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""

def show_notification(title, body, icon="input-keyboard", urgency="low"):
    """Display a desktop notification."""
    run_cmd([
        "notify-send",
        "-r", "9130",
        "-t", "2200",
        "-u", urgency,
        "-a", "Keyboard Layout",
        "-i", icon,
        "-h", "string:x-canonical-private-synchronous:keyboard_layout",
        title,
        body
    ])

def get_hypr_keyboards():
    """Get all keyboard devices from hyprctl."""
    raw = run_cmd(["hyprctl", "devices", "-j"])
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data.get("keyboards", [])
    except Exception:
        return []

def get_main_keyboard():
    """Find the primary active keyboard device."""
    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        if kb.get("main"):
            return kb
    for kb in keyboards:
        if "receiver" in kb.get("name", "").lower() or "keyboard" in kb.get("name", "").lower():
            return kb
    return keyboards[0] if keyboards else None

def get_active_layout_info():
    """Return dictionary with active keymap, layout index, and configured layouts."""
    main_kb = get_main_keyboard()
    if not main_kb:
        return {
            "active_keymap": "English (US)",
            "active_index": 0,
            "current_code": "us",
            "layout_str": "us",
            "layouts": ["us"]
        }
    
    layout_str = main_kb.get("layout", "us")
    layouts = [l.strip() for l in layout_str.split(",") if l.strip()]
    if not layouts:
        layouts = ["us"]
        
    active_idx = main_kb.get("active_layout_index", 0)
    active_keymap = main_kb.get("active_keymap", "English (US)")
    
    current_code = layouts[active_idx] if active_idx < len(layouts) else layouts[0]
    
    return {
        "active_keymap": active_keymap,
        "active_index": active_idx,
        "current_code": current_code,
        "layout_str": layout_str,
        "layouts": layouts
    }

def get_configured_from_file():
    """Read currently configured layouts and options from input.lua."""
    target_files = [
        INPUT_CONFIG_PATH.resolve() if INPUT_CONFIG_PATH.exists() else None,
        DOTFILES_INPUT_PATH.resolve() if DOTFILES_INPUT_PATH.exists() else None,
        INPUT_CONFIG_PATH,
        DOTFILES_INPUT_PATH
    ]
    config_file = None
    for f in target_files:
        if f and f.exists():
            config_file = f
            break
            
    if not config_file:
        return {"kb_layout": "us", "kb_variant": "", "kb_options": ""}
    
    try:
        content = config_file.read_text(encoding="utf-8")
        
        layout_match = re.search(r'kb_layout\s*=\s*["\']([^"\']*)["\']', content)
        variant_match = re.search(r'kb_variant\s*=\s*["\']([^"\']*)["\']', content)
        options_match = re.search(r'kb_options\s*=\s*["\']([^"\']*)["\']', content)
        
        kb_layout = layout_match.group(1).strip() if layout_match else "us"
        kb_variant = variant_match.group(1).strip() if variant_match else ""
        kb_options = options_match.group(1).strip() if options_match else ""
        
        return {
            "kb_layout": kb_layout if kb_layout else "us",
            "kb_variant": kb_variant,
            "kb_options": kb_options
        }
    except Exception:
        return {"kb_layout": "us", "kb_variant": "", "kb_options": ""}

def save_config_file(kb_layout, kb_variant="", kb_options=None):
    """Update input.lua with new layout values safely."""
    target_files = set()
    for p in [INPUT_CONFIG_PATH, DOTFILES_INPUT_PATH]:
        if p.exists():
            target_files.add(p.resolve())
            target_files.add(p)
            
    saved = False
    for config_file in target_files:
        try:
            content = config_file.read_text(encoding="utf-8")
            
            # Replace kb_layout
            if re.search(r'kb_layout\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_layout\s*=\s*["\'][^"\']*["\']',
                    f'kb_layout  = "{kb_layout}"',
                    content
                )
            else:
                content = re.sub(
                    r'input\s*=\s*\{',
                    f'input = {{\n        kb_layout  = "{kb_layout}",',
                    content
                )
            
            # Replace kb_variant if provided
            if kb_variant is not None and re.search(r'kb_variant\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_variant\s*=\s*["\'][^"\']*["\']',
                    f'kb_variant = "{kb_variant}"',
                    content
                )
                
            # Replace kb_options if provided
            if kb_options is not None and re.search(r'kb_options\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_options\s*=\s*["\'][^"\']*["\']',
                    f'kb_options = "{kb_options}"',
                    content
                )
            
            config_file.write_text(content, encoding="utf-8")
            saved = True
        except Exception as e:
            print(f"Warning: Failed writing to {config_file}: {e}", file=sys.stderr)
    return saved

def apply_hyprland_config(kb_layout, kb_variant="", kb_options=""):
    """Apply layout configuration immediately to running Hyprland instance."""
    lua_code = f'hl.config({{ input = {{ kb_layout = "{kb_layout}", kb_variant = "{kb_variant}", kb_options = "{kb_options}" }} }})'
    res = run_cmd(["hyprctl", "eval", lua_code])
    if "ok" not in res:
        run_cmd(["hyprctl", "eval", f'hl.config({{ input = {{ kb_layout = "{kb_layout}" }} }})'])
    # Trigger reload to ensure all devices update
    run_cmd(["hyprctl", "reload"])

def parse_available_xkb_layouts():
    """Parse list of available system XKB keyboard layouts."""
    lst_path = XKB_BASE_LST if XKB_BASE_LST.exists() else XKB_EVDEV_LST
    layouts = {}
    
    # Load default popular first
    for code, desc in POPULAR_LAYOUTS:
        layouts[code] = desc
        
    if lst_path.exists():
        try:
            with open(lst_path, "r", encoding="utf-8", errors="ignore") as f:
                in_layout_section = False
                for line in f:
                    line_str = line.strip()
                    if line_str == "! layout":
                        in_layout_section = True
                        continue
                    elif in_layout_section and line_str.startswith("!"):
                        break
                    
                    if in_layout_section and line_str:
                        parts = line.split(maxsplit=1)
                        if len(parts) >= 2:
                            code = parts[0].strip()
                            desc = parts[1].strip()
                            if code not in layouts:
                                layouts[code] = desc
        except Exception:
            pass
            
    return layouts

def switch_next_layout():
    """Switch to the next keyboard layout across all keyboards."""
    info = get_active_layout_info()
    if len(info["layouts"]) <= 1:
        show_notification(
            "󰌌  Single Layout Configured",
            f"Current: <b>{info['active_keymap']} ({info['current_code'].upper()})</b>\nPress <b>Super+Shift+K</b> to add more layouts!"
        )
        print("Only 1 layout is configured. Add more layouts with --add or via the menu.")
        return

    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        kb_name = kb.get("name")
        if kb_name:
            run_cmd(["hyprctl", "switchxkblayout", kb_name, "next"])
            
    new_info = get_active_layout_info()
    layouts_display = " • ".join([
        f"<b><u>{l.upper()}</u></b>" if idx == new_info["active_index"] else l.upper()
        for idx, l in enumerate(new_info["layouts"])
    ])
    
    show_notification(
        "󰌌  Keyboard Layout Switched",
        f"Active: <b>{new_info['active_keymap']} ({new_info['current_code'].upper()})</b>\nLayouts: {layouts_display}"
    )
    print(f"Switched to: {new_info['active_keymap']} ({new_info['current_code']})")

def switch_prev_layout():
    """Switch to the previous keyboard layout across all keyboards."""
    info = get_active_layout_info()
    if len(info["layouts"]) <= 1:
        return

    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        kb_name = kb.get("name")
        if kb_name:
            run_cmd(["hyprctl", "switchxkblayout", kb_name, "prev"])
            
    new_info = get_active_layout_info()
    show_notification(
        "󰌌  Keyboard Layout Switched",
        f"Active: <b>{new_info['active_keymap']} ({new_info['current_code'].upper()})</b>"
    )
    print(f"Switched to: {new_info['active_keymap']} ({new_info['current_code']})")

def set_layout_by_index_or_code(target):
    """Switch to a specific layout by code or index."""
    info = get_active_layout_info()
    layouts = info["layouts"]
    target_idx = -1
    
    if str(target).isdigit():
        idx = int(target)
        if 0 <= idx < len(layouts):
            target_idx = idx
    else:
        target_clean = str(target).strip().lower()
        for i, l in enumerate(layouts):
            if l.lower() == target_clean:
                target_idx = i
                break
                
    if target_idx != -1:
        keyboards = get_hypr_keyboards()
        for kb in keyboards:
            kb_name = kb.get("name")
            if kb_name:
                run_cmd(["hyprctl", "switchxkblayout", kb_name, str(target_idx)])
        new_info = get_active_layout_info()
        show_notification(
            "󰌌  Keyboard Layout Changed",
            f"Active: <b>{new_info['active_keymap']} ({new_info['current_code'].upper()})</b>"
        )
        print(f"Switched to layout index {target_idx}: {new_info['active_keymap']}")
    else:
        print(f"Layout '{target}' not found in active layouts: {layouts}", file=sys.stderr)

def add_layout(layout_code, variant=""):
    """Add a new layout code to configured layouts list and apply live."""
    code_clean = layout_code.strip()
    if not code_clean:
        return False
        
    conf = get_configured_from_file()
    current_layouts = [l.strip() for l in conf["kb_layout"].split(",") if l.strip()]
    
    if code_clean in current_layouts:
        show_notification(
            "󰌌  Keyboard Layout Info",
            f"Layout <b>{code_clean.upper()}</b> is already configured."
        )
        print(f"Layout '{code_clean}' is already configured.")
        set_layout_by_index_or_code(code_clean)
        return True
        
    current_layouts.append(code_clean)
    new_layout_str = ",".join(current_layouts)
    
    # Save & Apply
    save_config_file(new_layout_str, conf["kb_variant"], conf["kb_options"])
    apply_hyprland_config(new_layout_str, conf["kb_variant"], conf["kb_options"])
    
    # Switch to the newly added layout
    set_layout_by_index_or_code(str(len(current_layouts) - 1))
    
    all_xkb = parse_available_xkb_layouts()
    desc = all_xkb.get(code_clean, code_clean.upper())
    
    show_notification(
        "󰐕  Keyboard Layout Added",
        f"Added: <b>{desc} ({code_clean.upper()})</b>\nActive layouts: <b>{new_layout_str.upper()}</b>"
    )
    print(f"Successfully added layout '{code_clean}'. Configured layouts: {new_layout_str}")
    return True

def remove_layout(layout_code):
    """Remove a layout code from configured list and apply live."""
    code_clean = layout_code.strip()
    conf = get_configured_from_file()
    current_layouts = [l.strip() for l in conf["kb_layout"].split(",") if l.strip()]
    
    if code_clean not in current_layouts:
        print(f"Layout '{code_clean}' is not in configured layouts.", file=sys.stderr)
        return False
        
    if len(current_layouts) <= 1:
        show_notification(
            "⚠️  Cannot Remove Layout",
            "At least one keyboard layout must remain configured!",
            urgency="normal"
        )
        print("Cannot remove the only remaining keyboard layout.", file=sys.stderr)
        return False
        
    current_layouts.remove(code_clean)
    new_layout_str = ",".join(current_layouts)
    
    # Save & Apply
    save_config_file(new_layout_str, conf["kb_variant"], conf["kb_options"])
    apply_hyprland_config(new_layout_str, conf["kb_variant"], conf["kb_options"])
    
    # Switch to first layout
    set_layout_by_index_or_code("0")
    
    show_notification(
        "󰍵  Keyboard Layout Removed",
        f"Removed: <b>{code_clean.upper()}</b>\nRemaining: <b>{new_layout_str.upper()}</b>"
    )
    print(f"Successfully removed layout '{code_clean}'. Configured layouts: {new_layout_str}")
    return True

def run_fuzzel_menu(prompt, lines_list):
    """Prompt user using Fuzzel dmenu."""
    if not shutil.which("fuzzel"):
        print("Error: fuzzel is not installed.", file=sys.stderr)
        return None
        
    menu_input = "\n".join(lines_list)
    try:
        res = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                "--prompt", prompt,
                "--lines", str(min(max(len(lines_list), 4), 16)),
                "--width", "50",
            ],
            input=menu_input,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        return None
    except Exception as e:
        print(f"Fuzzel execution error: {e}", file=sys.stderr)
        return None

def gui_add_layout_menu():
    """Interactive GUI search menu to add a keyboard layout from XKB catalogue."""
    all_layouts = parse_available_xkb_layouts()
    conf = get_configured_from_file()
    active_layouts = [l.strip() for l in conf["kb_layout"].split(",") if l.strip()]
    
    menu_lines = []
    code_map = {}
    
    # Popular layouts first
    for code, desc in POPULAR_LAYOUTS:
        status_tag = " (Already Added)" if code in active_layouts else ""
        line = f"★ {code:<8} │ {desc}{status_tag}"
        menu_lines.append(line)
        code_map[line] = code
        
    # Other layouts
    for code, desc in sorted(all_layouts.items()):
        if code not in [c for c, _ in POPULAR_LAYOUTS]:
            status_tag = " (Already Added)" if code in active_layouts else ""
            line = f"  {code:<8} │ {desc}{status_tag}"
            menu_lines.append(line)
            code_map[line] = code
            
    selected = run_fuzzel_menu("󰐕 Add Layout > ", menu_lines)
    if selected and selected in code_map:
        target_code = code_map[selected]
        add_layout(target_code)

def gui_remove_layout_menu():
    """Interactive GUI menu to remove a configured layout."""
    conf = get_configured_from_file()
    active_layouts = [l.strip() for l in conf["kb_layout"].split(",") if l.strip()]
    all_xkb = parse_available_xkb_layouts()
    
    if len(active_layouts) <= 1:
        show_notification(
            "⚠️  Cannot Remove Layout",
            f"Only 1 layout ({active_layouts[0].upper()}) is configured. You cannot remove it.",
            urgency="normal"
        )
        return
        
    menu_lines = []
    code_map = {}
    
    for code in active_layouts:
        desc = all_xkb.get(code, "Custom layout")
        line = f"󰍵 Remove {code.upper():<6} │ {desc}"
        menu_lines.append(line)
        code_map[line] = code
        
    selected = run_fuzzel_menu("󰍵 Remove Layout > ", menu_lines)
    if selected and selected in code_map:
        target_code = code_map[selected]
        remove_layout(target_code)

def gui_main_menu():
    """Main interactive keyboard layout manager menu."""
    info = get_active_layout_info()
    all_xkb = parse_available_xkb_layouts()
    
    menu_lines = []
    action_map = {}
    
    # 1. Active layout indicator / quick switch list
    for idx, code in enumerate(info["layouts"]):
        is_active = (idx == info["active_index"])
        desc = all_xkb.get(code, code)
        indicator = "●" if is_active else "○"
        status_text = " [Active]" if is_active else ""
        line = f"󰌌 {indicator} {code.upper():<4} ➜  {desc}{status_text}"
        menu_lines.append(line)
        action_map[line] = ("switch", code)
        
    menu_lines.append("───────────────────────────────────────────")
    action_map[menu_lines[-1]] = ("noop", None)
    
    # 2. Cycle next layout action
    line_cycle = "󰑐  Cycle to Next Layout (Super+Space)"
    menu_lines.append(line_cycle)
    action_map[line_cycle] = ("cycle_next", None)
    
    # 3. Add new layout action
    line_add = "󰐕  Add New Keyboard Layout..."
    menu_lines.append(line_add)
    action_map[line_add] = ("gui_add", None)
    
    # 4. Remove layout action
    line_remove = "󰍵  Remove a Keyboard Layout..."
    menu_lines.append(line_remove)
    action_map[line_remove] = ("gui_remove", None)
    
    selected = run_fuzzel_menu("󰌌 Layout Manager > ", menu_lines)
    if not selected or selected not in action_map:
        return
        
    action, data = action_map[selected]
    if action == "switch":
        set_layout_by_index_or_code(data)
    elif action == "cycle_next":
        switch_next_layout()
    elif action == "gui_add":
        gui_add_layout_menu()
    elif action == "gui_remove":
        gui_remove_layout_menu()

def print_status_json():
    """Output JSON formatted status for custom Waybar modules or scripting."""
    info = get_active_layout_info()
    code = info["current_code"].upper()
    data = {
        "text": code,
        "alt": info["active_keymap"],
        "tooltip": f"Keyboard Layout: {info['active_keymap']} ({code})\nConfigured: {', '.join(info['layouts']).upper()}\n\n• Left Click: Switch Next\n• Right Click: Layout Menu\n• Middle Click: Add Layout",
        "class": f"layout-{info['current_code']}",
        "percentage": (info["active_index"] + 1) / max(len(info["layouts"]), 1) * 100
    }
    print(json.dumps(data))

def main():
    parser = argparse.ArgumentParser(
        description="Hyprland Keyboard Layout Manager & Switcher Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  keyboard_layout.py --next              Switch to next configured layout
  keyboard_layout.py --prev              Switch to previous configured layout
  keyboard_layout.py --set de            Switch directly to German layout
  keyboard_layout.py --add de            Add German layout to config
  keyboard_layout.py --remove de         Remove German layout from config
  keyboard_layout.py --menu              Open interactive Fuzzel menu
  keyboard_layout.py --add-menu          Open interactive layout catalog search
  keyboard_layout.py --list              List configured and active layouts
"""
    )
    
    parser.add_argument("-n", "--next", action="store_true", help="Switch to next keyboard layout")
    parser.add_argument("-p", "--prev", action="store_true", help="Switch to previous keyboard layout")
    parser.add_argument("-s", "--set", metavar="LAYOUT", help="Switch to specific layout code or index")
    parser.add_argument("-a", "--add", metavar="LAYOUT", help="Add layout to configured list and switch to it")
    parser.add_argument("-r", "--remove", metavar="LAYOUT", help="Remove layout from configured list")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel layout manager menu")
    parser.add_argument("--add-menu", action="store_true", help="Open interactive Fuzzel add layout menu")
    parser.add_argument("--remove-menu", action="store_true", help="Open interactive Fuzzel remove layout menu")
    parser.add_argument("-l", "--list", action="store_true", help="Print active and configured layouts")
    parser.add_argument("--status", action="store_true", help="Output JSON status for Waybar / scripting")
    
    args = parser.parse_args()
    
    if args.next:
        switch_next_layout()
    elif args.prev:
        switch_prev_layout()
    elif args.set:
        set_layout_by_index_or_code(args.set)
    elif args.add:
        add_layout(args.add)
    elif args.remove:
        remove_layout(args.remove)
    elif args.add_menu:
        gui_add_layout_menu()
    elif args.remove_menu:
        gui_remove_layout_menu()
    elif args.menu:
        gui_main_menu()
    elif args.status:
        print_status_json()
    elif args.list:
        info = get_active_layout_info()
        print(f"Active Keymap : {info['active_keymap']} ({info['current_code'].upper()})")
        print(f"Active Index  : {info['active_index']}")
        print(f"Configured    : {', '.join(info['layouts']).upper()}")
    else:
        # Default with no args: launch interactive menu
        gui_main_menu()

if __name__ == "__main__":
    main()
