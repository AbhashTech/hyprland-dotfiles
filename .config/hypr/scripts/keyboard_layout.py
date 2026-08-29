#!/usr/bin/env python3
"""
=============================================================================
Hyprland Keyboard Layout & Variant Manager Utility
=============================================================================
Provides CLI and interactive Fuzzel GUI tools to:
- Switch / cycle active keyboard layouts and variants live across keyboards
- Add / remove layout variants (e.g. Indian Hindi Bolnagri/KaGaPa, Tamil, Telugu,
  Kannada, Malayalam, Bengali, US Dvorak, Colemak, French Bépo, etc.)
- Synchronize kb_layout and kb_variant in input.lua safely and persistently
- Display desktop notifications with active layout & variant names
- Integrate with Waybar center widget and Hyprland keybindings
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

# Curated Popular Layouts & Indian Regional Layouts for fast discovery
CURATED_POPULAR = [
    # US & Variants
    ("us", "", "English (US)"),
    ("gb", "", "English (UK)"),
    ("us", "dvorak", "English (Dvorak)"),
    ("us", "colemak", "English (Colemak)"),
    ("us", "intl", "English (US, international with AltGr dead keys)"),

    # Indian Languages & Regional Variants
    ("in", "bolnagri", "Hindi (Bolnagri phonetic)"),
    ("in", "hin-kagapa", "Hindi (KaGaPa, phonetic)"),
    ("in", "deva", "Hindi (Devanagari InScript)"),
    ("in", "eng", "English (India, with Rupee ₹)"),
    ("in", "tam", "Tamil (InScript)"),
    ("in", "tamilnet", "Tamil (TamilNet '99)"),
    ("in", "tel", "Telugu (InScript)"),
    ("in", "tel-kagapa", "Telugu (KaGaPa, phonetic)"),
    ("in", "kan", "Kannada (InScript)"),
    ("in", "kan-kagapa", "Kannada (KaGaPa, phonetic)"),
    ("in", "mal", "Malayalam (InScript)"),
    ("in", "mal_lalitha", "Malayalam (Lalitha)"),
    ("in", "guj", "Gujarati (InScript)"),
    ("in", "guj-kagapa", "Gujarati (KaGaPa, phonetic)"),
    ("in", "ben", "Bangla / Bengali (India)"),
    ("in", "ben_probhat", "Bangla / Bengali (Probhat)"),
    ("in", "guru", "Punjabi (Gurmukhi)"),
    ("in", "marathi", "Marathi (InScript)"),
    ("in", "mar-kagapa", "Marathi (KaGaPa, phonetic)"),
    ("in", "san-kagapa", "Sanskrit (KaGaPa, phonetic)"),
    ("in", "ori", "Odia / Oriya (InScript)"),
    ("in", "asm-kagapa", "Assamese (KaGaPa, phonetic)"),
    ("in", "urd-phonetic", "Urdu (Phonetic)"),

    # Global Keyboards
    ("de", "", "German (Germany)"),
    ("fr", "", "French (France)"),
    ("fr", "bepo", "French (Bépo ergonomic)"),
    ("es", "", "Spanish (Spain)"),
    ("latam", "", "Spanish (Latin American)"),
    ("it", "", "Italian (Italy)"),
    ("pt", "", "Portuguese (Portugal)"),
    ("br", "", "Portuguese (Brazil, ABNT2)"),
    ("ru", "", "Russian"),
    ("ru", "phonetic", "Russian (Phonetic)"),
    ("ara", "", "Arabic"),
    ("jp", "", "Japanese"),
    ("cn", "", "Chinese"),
    ("kr", "", "Korean"),
    ("pl", "", "Polish"),
    ("tr", "", "Turkish"),
    ("ua", "", "Ukrainian"),
    ("se", "", "Swedish"),
    ("no", "", "Norwegian"),
    ("dk", "", "Danish"),
    ("fi", "", "Finnish"),
    ("nl", "", "Dutch"),
    ("cz", "", "Czech"),
    ("gr", "", "Greek"),
    ("il", "", "Hebrew"),
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

def parse_all_xkb_catalog():
    """
    Parse both base layouts and all layout variants from XKB rules.
    Returns:
      layouts: dict of code -> description
      variants: dict of (lay_code, var_code) -> description
    """
    lst_path = XKB_BASE_LST if XKB_BASE_LST.exists() else XKB_EVDEV_LST
    layouts = {}
    variants = {}

    if lst_path.exists():
        try:
            with open(lst_path, "r", encoding="utf-8", errors="ignore") as f:
                section = None
                for line in f:
                    l = line.strip()
                    if l.startswith("! "):
                        section = l[2:].strip()
                        continue
                    if not l or not section:
                        continue
                    parts = line.split(maxsplit=1)
                    if len(parts) < 2:
                        continue
                    code = parts[0].strip()
                    desc = parts[1].strip()
                    if section == "layout":
                        layouts[code] = desc
                    elif section == "variant":
                        if ":" in desc:
                            lay_part, var_desc = desc.split(":", 1)
                            lay_code = lay_part.strip()
                            variants[(lay_code, code)] = var_desc.strip()
        except Exception:
            pass

    return layouts, variants

def get_entry_description(lay, var, layouts_map=None, variants_map=None):
    """Get readable description for a layout/variant combo."""
    if var:
        # Check curated list first
        for c_lay, c_var, c_desc in CURATED_POPULAR:
            if c_lay == lay and c_var == var:
                return c_desc
        if variants_map and (lay, var) in variants_map:
            return variants_map[(lay, var)]
        return f"{lay.upper()} ({var})"
    else:
        for c_lay, c_var, c_desc in CURATED_POPULAR:
            if c_lay == lay and not c_var:
                return c_desc
        if layouts_map and lay in layouts_map:
            return layouts_map[lay]
        return lay.upper()

def format_entry_tag(lay, var):
    """Return compact representation e.g. 'us' or 'in(bolnagri)'."""
    return f"{lay}({var})" if var else lay

def parse_layout_arg(arg):
    """Parse user argument e.g. 'in(bolnagri)', 'in:bolnagri', or 'in'."""
    arg = arg.strip()
    match = re.match(r'^([a-zA-Z0-9_-]+)[(:]([a-zA-Z0-9_-]+)\)?$', arg)
    if match:
        return match.group(1).lower(), match.group(2).lower()
    return arg.lower(), ""

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
        return {"layouts": ["us"], "variants": [""], "options": ""}

    try:
        content = config_file.read_text(encoding="utf-8")

        layout_match = re.search(r'kb_layout\s*=\s*["\']([^"\']*)["\']', content)
        variant_match = re.search(r'kb_variant\s*=\s*["\']([^"\']*)["\']', content)
        options_match = re.search(r'kb_options\s*=\s*["\']([^"\']*)["\']', content)

        kb_layout_str = layout_match.group(1).strip() if layout_match else "us"
        kb_variant_str = variant_match.group(1).strip() if variant_match else ""
        kb_options_str = options_match.group(1).strip() if options_match else ""

        layouts = [l.strip() for l in kb_layout_str.split(",") if l.strip()]
        if not layouts:
            layouts = ["us"]

        # Parse variants list to match length of layouts
        raw_variants = [v.strip() for v in kb_variant_str.split(",")] if kb_variant_str else []
        variants = []
        for i in range(len(layouts)):
            variants.append(raw_variants[i] if i < len(raw_variants) else "")

        return {
            "layouts": layouts,
            "variants": variants,
            "options": kb_options_str
        }
    except Exception:
        return {"layouts": ["us"], "variants": [""], "options": ""}

def get_active_layout_info():
    """Return active layout state including pairs of (layout, variant)."""
    conf = get_configured_from_file()
    layouts = conf["layouts"]
    variants = conf["variants"]

    main_kb = get_main_keyboard()
    active_idx = 0
    active_keymap = "English (US)"

    if main_kb:
        active_idx = main_kb.get("active_layout_index", 0)
        active_keymap = main_kb.get("active_keymap", "English (US)")

    if active_idx >= len(layouts):
        active_idx = 0

    curr_lay = layouts[active_idx] if layouts else "us"
    curr_var = variants[active_idx] if active_idx < len(variants) else ""
    curr_tag = format_entry_tag(curr_lay, curr_var)

    pairs = list(zip(layouts, variants))

    return {
        "active_index": active_idx,
        "active_keymap": active_keymap,
        "current_lay": curr_lay,
        "current_var": curr_var,
        "current_tag": curr_tag,
        "pairs": pairs,
        "layouts": layouts,
        "variants": variants
    }

def save_and_apply_config(layouts, variants, options=None):
    """Update input.lua and apply live via Hyprland IPC."""
    if not layouts:
        layouts = ["us"]
        variants = [""]

    while len(variants) < len(layouts):
        variants.append("")

    kb_layout_str = ",".join(layouts)
    kb_variant_str = ",".join(variants)

    # Save to disk
    target_files = set()
    for p in [INPUT_CONFIG_PATH, DOTFILES_INPUT_PATH]:
        if p.exists():
            target_files.add(p.resolve())
            target_files.add(p)

    for config_file in target_files:
        try:
            content = config_file.read_text(encoding="utf-8")

            # Replace kb_layout
            if re.search(r'kb_layout\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_layout\s*=\s*["\'][^"\']*["\']',
                    f'kb_layout  = "{kb_layout_str}"',
                    content
                )

            # Replace kb_variant
            if re.search(r'kb_variant\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_variant\s*=\s*["\'][^"\']*["\']',
                    f'kb_variant = "{kb_variant_str}"',
                    content
                )

            # Replace kb_options if given
            if options is not None and re.search(r'kb_options\s*=\s*["\'][^"\']*["\']', content):
                content = re.sub(
                    r'kb_options\s*=\s*["\'][^"\']*["\']',
                    f'kb_options = "{options}"',
                    content
                )

            config_file.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: writing {config_file} failed: {e}", file=sys.stderr)

    # Apply live to Hyprland
    lua_code = f'hl.config({{ input = {{ kb_layout = "{kb_layout_str}", kb_variant = "{kb_variant_str}" }} }})'
    run_cmd(["hyprctl", "eval", lua_code])
    run_cmd(["hyprctl", "reload"])

def switch_next_layout():
    """Cycle to next configured keyboard layout/variant across keyboards."""
    info = get_active_layout_info()
    if len(info["pairs"]) <= 1:
        show_notification(
            "󰌌  Single Layout Configured",
            f"Current: <b>{info['active_keymap']}</b>\nPress <b>Super+Shift+K</b> to add more layouts (e.g. Hindi, Tamil, Dvorak)!"
        )
        print("Only 1 layout is configured. Add more layouts with --add or via menu.")
        return

    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        kb_name = kb.get("name")
        if kb_name:
            run_cmd(["hyprctl", "switchxkblayout", kb_name, "next"])

    new_info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()
    curr_desc = get_entry_description(new_info["current_lay"], new_info["current_var"], l_map, v_map)

    layouts_display = " • ".join([
        f"<b><u>{format_entry_tag(l, v).upper()}</u></b>" if i == new_info["active_index"] else format_entry_tag(l, v).upper()
        for i, (l, v) in enumerate(new_info["pairs"])
    ])

    show_notification(
        "󰌌  Keyboard Layout Switched",
        f"Active: <b>{curr_desc}</b>\nLayouts: {layouts_display}"
    )
    print(f"Switched to: {curr_desc} [{format_entry_tag(new_info['current_lay'], new_info['current_var'])}]")

def switch_prev_layout():
    """Cycle to previous configured keyboard layout/variant."""
    info = get_active_layout_info()
    if len(info["pairs"]) <= 1:
        return

    keyboards = get_hypr_keyboards()
    for kb in keyboards:
        kb_name = kb.get("name")
        if kb_name:
            run_cmd(["hyprctl", "switchxkblayout", kb_name, "prev"])

    new_info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()
    curr_desc = get_entry_description(new_info["current_lay"], new_info["current_var"], l_map, v_map)

    show_notification(
        "󰌌  Keyboard Layout Switched",
        f"Active: <b>{curr_desc}</b>"
    )
    print(f"Switched to: {curr_desc} [{format_entry_tag(new_info['current_lay'], new_info['current_var'])}]")

def set_layout_by_index_or_tag(target):
    """Switch directly to a layout by index or tag (e.g. '0', 'in(bolnagri)', 'us')."""
    info = get_active_layout_info()
    pairs = info["pairs"]
    target_idx = -1

    if str(target).isdigit():
        idx = int(target)
        if 0 <= idx < len(pairs):
            target_idx = idx
    else:
        req_lay, req_var = parse_layout_arg(target)
        for i, (l, v) in enumerate(pairs):
            if l.lower() == req_lay and v.lower() == req_var:
                target_idx = i
                break
        if target_idx == -1:
            for i, (l, v) in enumerate(pairs):
                if l.lower() == req_lay:
                    target_idx = i
                    break

    if target_idx != -1:
        keyboards = get_hypr_keyboards()
        for kb in keyboards:
            kb_name = kb.get("name")
            if kb_name:
                run_cmd(["hyprctl", "switchxkblayout", kb_name, str(target_idx)])
        new_info = get_active_layout_info()
        l_map, v_map = parse_all_xkb_catalog()
        desc = get_entry_description(new_info["current_lay"], new_info["current_var"], l_map, v_map)
        show_notification(
            "󰌌  Keyboard Layout Changed",
            f"Active: <b>{desc}</b>"
        )
        print(f"Switched to layout {target_idx}: {desc}")
    else:
        print(f"Layout '{target}' not found in active layouts: {[format_entry_tag(l, v) for l, v in pairs]}", file=sys.stderr)

def add_layout(layout_arg, variant_arg=""):
    """Add a layout or layout(variant) to configured list."""
    if variant_arg:
        lay, var = layout_arg.strip().lower(), variant_arg.strip().lower()
    else:
        lay, var = parse_layout_arg(layout_arg)

    if not lay:
        return False

    conf = get_configured_from_file()
    layouts = list(conf["layouts"])
    variants = list(conf["variants"])

    # Check if already present
    for i, (l, v) in enumerate(zip(layouts, variants)):
        if l == lay and v == var:
            tag = format_entry_tag(lay, var)
            show_notification(
                "󰌌  Keyboard Layout Info",
                f"Layout <b>{tag.upper()}</b> is already configured."
            )
            print(f"Layout '{tag}' is already configured.")
            set_layout_by_index_or_tag(str(i))
            return True

    layouts.append(lay)
    variants.append(var)

    save_and_apply_config(layouts, variants)
    set_layout_by_index_or_tag(str(len(layouts) - 1))

    l_map, v_map = parse_all_xkb_catalog()
    desc = get_entry_description(lay, var, l_map, v_map)
    all_tags = ", ".join([format_entry_tag(l, v).upper() for l, v in zip(layouts, variants)])

    show_notification(
        "󰐕  Keyboard Layout Added",
        f"Added: <b>{desc}</b>\nActive layouts: <b>{all_tags}</b>"
    )
    print(f"Successfully added layout '{format_entry_tag(lay, var)}' ({desc}). Active: {all_tags}")
    return True

def remove_layout(layout_arg, variant_arg=""):
    """Remove a layout/variant from configured list."""
    if variant_arg:
        lay, var = layout_arg.strip().lower(), variant_arg.strip().lower()
    else:
        lay, var = parse_layout_arg(layout_arg)

    conf = get_configured_from_file()
    layouts = list(conf["layouts"])
    variants = list(conf["variants"])

    target_idx = -1
    for i, (l, v) in enumerate(zip(layouts, variants)):
        if l == lay and v == var:
            target_idx = i
            break
    if target_idx == -1:
        for i, (l, v) in enumerate(zip(layouts, variants)):
            if l == lay:
                target_idx = i
                break

    if target_idx == -1:
        print(f"Layout '{format_entry_tag(lay, var)}' is not in configured layouts.", file=sys.stderr)
        return False

    if len(layouts) <= 1:
        show_notification(
            "⚠️  Cannot Remove Layout",
            "At least one keyboard layout must remain configured!",
            urgency="normal"
        )
        print("Cannot remove the only remaining keyboard layout.", file=sys.stderr)
        return False

    removed_tag = format_entry_tag(layouts[target_idx], variants[target_idx])
    del layouts[target_idx]
    del variants[target_idx]

    save_and_apply_config(layouts, variants)
    set_layout_by_index_or_tag("0")

    all_tags = ", ".join([format_entry_tag(l, v).upper() for l, v in zip(layouts, variants)])
    show_notification(
        "󰍵  Keyboard Layout Removed",
        f"Removed: <b>{removed_tag.upper()}</b>\nRemaining: <b>{all_tags}</b>"
    )
    print(f"Successfully removed layout '{removed_tag}'. Active: {all_tags}")
    return True

def run_fuzzel_menu(prompt, lines_list):
    """Display interactive Fuzzel fuzzy-search dmenu."""
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
                "--width", "56",
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
    """Interactive GUI search menu to add any layout or variant."""
    l_map, v_map = parse_all_xkb_catalog()
    conf = get_configured_from_file()
    configured_pairs = set(zip(conf["layouts"], conf["variants"]))

    menu_lines = []
    item_map = {}
    seen = set()

    # 1. Popular & Indian Keyboards First
    for lay, var, desc in CURATED_POPULAR:
        is_conf = (lay, var) in configured_pairs
        tag = format_entry_tag(lay, var)
        status = " (Configured)" if is_conf else ""
        line = f"★ {tag:<16} │ {desc}{status}"
        menu_lines.append(line)
        item_map[line] = (lay, var)
        seen.add((lay, var))

    # 2. All Other Variants from XKB
    for (lay, var), desc in sorted(v_map.items(), key=lambda x: (x[0][0], x[1])):
        if (lay, var) not in seen:
            is_conf = (lay, var) in configured_pairs
            tag = format_entry_tag(lay, var)
            status = " (Configured)" if is_conf else ""
            line = f"  {tag:<16} │ {desc}{status}"
            menu_lines.append(line)
            item_map[line] = (lay, var)
            seen.add((lay, var))

    # 3. Base Layouts (without variants)
    for lay, desc in sorted(l_map.items()):
        if (lay, "") not in seen:
            is_conf = (lay, "") in configured_pairs
            tag = lay
            status = " (Configured)" if is_conf else ""
            line = f"  {tag:<16} │ {desc}{status}"
            menu_lines.append(line)
            item_map[line] = (lay, "")
            seen.add((lay, ""))

    selected = run_fuzzel_menu("󰐕 Add Layout/Variant > ", menu_lines)
    if selected and selected in item_map:
        lay, var = item_map[selected]
        add_layout(lay, var)

def gui_remove_layout_menu():
    """Interactive GUI menu to remove a configured layout."""
    conf = get_configured_from_file()
    pairs = list(zip(conf["layouts"], conf["variants"]))
    l_map, v_map = parse_all_xkb_catalog()

    if len(pairs) <= 1:
        show_notification(
            "⚠️  Cannot Remove Layout",
            f"Only 1 layout ({format_entry_tag(pairs[0][0], pairs[0][1]).upper()}) is configured. You cannot remove it.",
            urgency="normal"
        )
        return

    menu_lines = []
    item_map = {}

    for lay, var in pairs:
        desc = get_entry_description(lay, var, l_map, v_map)
        tag = format_entry_tag(lay, var)
        line = f"󰍵 Remove {tag.upper():<14} │ {desc}"
        menu_lines.append(line)
        item_map[line] = (lay, var)

    selected = run_fuzzel_menu("󰍵 Remove Layout > ", menu_lines)
    if selected and selected in item_map:
        lay, var = item_map[selected]
        remove_layout(lay, var)

def gui_main_menu():
    """Main interactive keyboard layout manager menu."""
    info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()

    menu_lines = []
    action_map = {}

    # 1. Configured layout list & direct switch options
    for idx, (lay, var) in enumerate(info["pairs"]):
        is_active = (idx == info["active_index"])
        desc = get_entry_description(lay, var, l_map, v_map)
        tag = format_entry_tag(lay, var).upper()
        indicator = "●" if is_active else "○"
        status_text = " [Active]" if is_active else ""
        line = f"󰌌 {indicator} {tag:<12} ➜  {desc}{status_text}"
        menu_lines.append(line)
        action_map[line] = ("switch", str(idx))

    menu_lines.append("─────────────────────────────────────────────")
    action_map[menu_lines[-1]] = ("noop", None)

    # 2. Actions
    line_cycle = "󰑐  Cycle Next Layout (Super+Space)"
    menu_lines.append(line_cycle)
    action_map[line_cycle] = ("cycle_next", None)

    line_add = "󰐕  Add New Keyboard Layout / Variant..."
    menu_lines.append(line_add)
    action_map[line_add] = ("gui_add", None)

    line_remove = "󰍵  Remove a Configured Layout..."
    menu_lines.append(line_remove)
    action_map[line_remove] = ("gui_remove", None)

    selected = run_fuzzel_menu("󰌌 Layout Manager > ", menu_lines)
    if not selected or selected not in action_map:
        return

    action, data = action_map[selected]
    if action == "switch":
        set_layout_by_index_or_tag(data)
    elif action == "cycle_next":
        switch_next_layout()
    elif action == "gui_add":
        gui_add_layout_menu()
    elif action == "gui_remove":
        gui_remove_layout_menu()

def print_status_json():
    """Output JSON formatted status for Waybar or scripting."""
    info = get_active_layout_info()
    l_map, v_map = parse_all_xkb_catalog()
    curr_desc = get_entry_description(info["current_lay"], info["current_var"], l_map, v_map)
    tag = info["current_tag"].upper()

    configured_list = ", ".join([
        f"{get_entry_description(l, v, l_map, v_map)} ({format_entry_tag(l, v).upper()})"
        for l, v in info["pairs"]
    ])

    data = {
        "text": tag,
        "alt": curr_desc,
        "tooltip": f"<b>Active Keyboard Layout:</b>\n{curr_desc} ({tag})\n\n<b>Configured Layouts:</b>\n{configured_list}\n\n• Left Click: Cycle Next Layout\n• Right Click: Layout & Variant Menu\n• Middle Click: Add New Layout",
        "class": f"layout-{info['current_lay']}",
        "percentage": (info["active_index"] + 1) / max(len(info["pairs"]), 1) * 100
    }
    print(json.dumps(data))

def main():
    parser = argparse.ArgumentParser(
        description="Hyprland Keyboard Layout & Variant Manager Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  keyboard_layout.py --next                  Switch to next configured layout
  keyboard_layout.py --add "in(bolnagri)"    Add Hindi Bolnagri phonetic layout
  keyboard_layout.py --add "in(tam)"         Add Tamil layout
  keyboard_layout.py --add "in(tel)"         Add Telugu layout
  keyboard_layout.py --add "in(eng)"         Add Indian English with ₹ layout
  keyboard_layout.py --add "us(dvorak)"      Add US Dvorak layout
  keyboard_layout.py --remove "in(bolnagri)" Remove Hindi Bolnagri layout
  keyboard_layout.py --menu                  Open interactive Fuzzel menu
  keyboard_layout.py --add-menu              Open interactive layout/variant catalog
  keyboard_layout.py --list                  List configured layouts & active variant
"""
    )

    parser.add_argument("-n", "--next", action="store_true", help="Switch to next keyboard layout")
    parser.add_argument("-p", "--prev", action="store_true", help="Switch to previous keyboard layout")
    parser.add_argument("-s", "--set", metavar="LAYOUT", help="Switch to layout by index or tag (e.g. 'in(bolnagri)')")
    parser.add_argument("-a", "--add", metavar="LAYOUT", help="Add layout/variant (e.g. 'in(bolnagri)', 'tam', 'de')")
    parser.add_argument("-r", "--remove", metavar="LAYOUT", help="Remove layout/variant")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel layout manager menu")
    parser.add_argument("--add-menu", action="store_true", help="Open interactive Fuzzel add layout/variant menu")
    parser.add_argument("--remove-menu", action="store_true", help="Open interactive Fuzzel remove layout menu")
    parser.add_argument("-l", "--list", action="store_true", help="Print active and configured layouts with variants")
    parser.add_argument("--status", action="store_true", help="Output JSON status for Waybar")

    args = parser.parse_args()

    if args.next:
        switch_next_layout()
    elif args.prev:
        switch_prev_layout()
    elif args.set:
        set_layout_by_index_or_tag(args.set)
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
        l_map, v_map = parse_all_xkb_catalog()
        curr_desc = get_entry_description(info["current_lay"], info["current_var"], l_map, v_map)
        print(f"Active Keymap : {curr_desc} [{info['current_tag'].upper()}]")
        print(f"Active Index  : {info['active_index']}")
        print(f"Configured    : {', '.join([format_entry_tag(l, v).upper() for l, v in info['pairs']])}")
        for i, (l, v) in enumerate(info["pairs"]):
            d = get_entry_description(l, v, l_map, v_map)
            act = " [ACTIVE]" if i == info["active_index"] else ""
            print(f"  [{i}] {format_entry_tag(l, v):<16} : {d}{act}")
    else:
        gui_main_menu()

if __name__ == "__main__":
    main()
