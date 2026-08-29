#!/usr/bin/env python3
"""
=============================================================================
Hyprland Dynamic Wallpaper Switcher & Manager
=============================================================================
Automates wallpaper management for Hyprland and Wayland desktops.
- Automatically creates ~/Wallpaper directory if not present.
- Scans ~/Wallpaper for all supported image file types recursively.
- Randomly cycles or sequentially navigates through wallpapers.
- Provides interactive Fuzzel / Wofi graphical selection menu.
- Integrates seamlessly with hyprpaper (multi-monitor support), swww, swaybg, and fallbacks.
- Sends visual desktop notifications with image thumbnails.
"""

import os
import sys
import json
import time
import random
import shutil
import argparse
import subprocess
from pathlib import Path

# Paths & Directories
PRIMARY_WALLPAPER_DIR = Path.home() / "Wallpaper"
FALLBACK_WALLPAPER_DIRS = [
    Path.home() / "Wallpapers",
    Path.home() / "Pictures" / "Wallpapers",
    Path.home() / "Pictures" / "Wallpaper",
]

CACHE_DIR = Path.home() / ".cache"
STATE_FILE = CACHE_DIR / "hypr_wallpaper_state.json"
CURRENT_WALLPAPER_TXT = CACHE_DIR / "current_wallpaper"
HYPRPAPER_CONF = Path.home() / ".config" / "hypr" / "hyprpaper.conf"

# Supported image file extensions
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif",
    ".svg", ".avif", ".pnm", ".pbm", ".pgm", ".ppm",
    ".tiff", ".tif", ".jxl", ".ico", ".qoi", ".heic", ".heif"
}

# ANSI Colors for CLI output
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[38;2;166;227;161m"
COLOR_BLUE = "\033[38;2;137;180;250m"
COLOR_YELLOW = "\033[38;2;249;226;175m"
COLOR_RED = "\033[38;2;243;139;168m"
COLOR_MAUVE = "\033[38;2;203;166;247m"


def ensure_directories():
    """Ensure the ~/Wallpaper directory and cache directory exist."""
    PRIMARY_WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_all_wallpapers(custom_dir=None):
    """
    Search ~/Wallpaper (and fallbacks if empty) for all supported image files.
    Returns a sorted list of Path objects.
    """
    ensure_directories()
    
    dirs_to_check = []
    if custom_dir:
        dirs_to_check.append(Path(custom_dir).expanduser().resolve())
    else:
        dirs_to_check.append(PRIMARY_WALLPAPER_DIR)
        for fb in FALLBACK_WALLPAPER_DIRS:
            if fb.is_dir() and fb != PRIMARY_WALLPAPER_DIR:
                dirs_to_check.append(fb)

    found_images = []
    seen_paths = set()

    for d in dirs_to_check:
        if not d.is_dir():
            continue
        try:
            for root, _, files in os.walk(d):
                # Skip hidden directories
                if any(part.startswith(".") and part != "." for part in Path(root).parts):
                    continue
                for f in files:
                    if f.startswith("."):
                        continue
                    file_path = Path(root) / f
                    if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        # Check that file is non-empty
                        try:
                            if file_path.stat().st_size > 0 and str(file_path) not in seen_paths:
                                found_images.append(file_path)
                                seen_paths.add(str(file_path))
                        except (OSError, PermissionError):
                            continue
        except (OSError, PermissionError):
            continue

    return sorted(found_images, key=lambda p: str(p).lower())


def load_state():
    """Load persistent state including current wallpaper and history."""
    if STATE_FILE.is_file():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current": None, "history": []}


def save_state(current_path):
    """Save persistent state and write current wallpaper path to cache."""
    try:
        ensure_directories()
        state = load_state()
        state["current"] = str(current_path)
        
        history = state.get("history", [])
        history.append(str(current_path))
        # Keep last 50 history entries
        state["history"] = history[-50:]
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            
        with open(CURRENT_WALLPAPER_TXT, "w", encoding="utf-8") as f:
            f.write(str(current_path) + "\n")
    except Exception:
        pass


def show_notification(title, body, image_path=None, timeout=3000):
    """Send desktop notification via notify-send."""
    if not shutil.which("notify-send"):
        return
    cmd = [
        "notify-send",
        "-a", "Wallpaper Switcher",
        "-t", str(timeout),
    ]
    if image_path and Path(image_path).is_file():
        cmd.extend(["-i", str(image_path)])
    else:
        cmd.extend(["-i", "preferences-desktop-wallpaper"])
    cmd.extend([title, body])
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def get_hyprland_monitors():
    """Get active monitor names using hyprctl."""
    monitors = []
    if shutil.which("hyprctl"):
        try:
            res = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                for mon in data:
                    if "name" in mon:
                        monitors.append(mon["name"])
        except Exception:
            pass
    return monitors


def is_process_running(proc_name):
    """Check if process is running."""
    if shutil.which("pgrep"):
        try:
            res = subprocess.run(["pgrep", "-x", proc_name], capture_output=True)
            return res.returncode == 0
        except Exception:
            pass
    return False


def apply_hyprpaper(image_path):
    """Apply wallpaper via hyprpaper backend."""
    abs_path = str(Path(image_path).resolve())
    
    # Ensure hyprpaper daemon is running
    if not is_process_running("hyprpaper"):
        try:
            subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.2)
        except Exception:
            pass

    if not shutil.which("hyprctl"):
        return False

    try:
        # Preload wallpaper
        subprocess.run(["hyprctl", "hyprpaper", "preload", abs_path], capture_output=True, text=True, timeout=3)
        
        monitors = get_hyprland_monitors()
        if monitors:
            for mon in monitors:
                subprocess.run(["hyprctl", "hyprpaper", "wallpaper", f"{mon},{abs_path}"], capture_output=True, text=True, timeout=3)
        else:
            # Fallback to wildcard / all monitors
            subprocess.run(["hyprctl", "hyprpaper", "wallpaper", f",{abs_path}"], capture_output=True, text=True, timeout=3)
        
        # Unload unused wallpapers to free VRAM
        subprocess.run(["hyprctl", "hyprpaper", "unload", "unused"], capture_output=True, text=True, timeout=3)
        
        # Update hyprpaper.conf so it persists
        try:
            HYPRPAPER_CONF.parent.mkdir(parents=True, exist_ok=True)
            with open(HYPRPAPER_CONF, "w", encoding="utf-8") as f:
                f.write(f"preload = {abs_path}\n")
                f.write(f"wallpaper = ,{abs_path}\nsplash = false\n")
        except Exception:
            pass
            
        return True
    except Exception:
        return False


def apply_swww(image_path):
    """Apply wallpaper via swww backend."""
    if not shutil.which("swww"):
        return False
    abs_path = str(Path(image_path).resolve())
    try:
        if not is_process_running("swww-daemon"):
            subprocess.Popen(["swww-daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.2)
        res = subprocess.run([
            "swww", "img", abs_path,
            "--transition-type", "wipe",
            "--transition-angle", "30",
            "--transition-step", "90",
            "--transition-fps", "60"
        ], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def apply_swaybg(image_path):
    """Apply wallpaper via swaybg backend."""
    if not shutil.which("swaybg"):
        return False
    abs_path = str(Path(image_path).resolve())
    try:
        subprocess.run(["pkill", "-x", "swaybg"], capture_output=True)
        time.sleep(0.05)
        subprocess.Popen(["swaybg", "-i", abs_path, "-m", "fill"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def apply_generic_fallbacks(image_path):
    """Generic desktop environment fallbacks (GNOME, KDE, XFCE, feh)."""
    abs_path = str(Path(image_path).resolve())
    file_uri = Path(abs_path).as_uri()

    # GNOME / GSettings
    if shutil.which("gsettings"):
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", file_uri], capture_output=True)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", file_uri], capture_output=True)
            return True
        except Exception:
            pass

    # Feh (X11)
    if shutil.which("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", abs_path], capture_output=True)
            return True
        except Exception:
            pass

    return False


def set_wallpaper(image_path, silent=False):
    """Apply the chosen wallpaper to the desktop across all supported engines."""
    image_path = Path(image_path).resolve()
    if not image_path.is_file():
        if not silent:
            print(f"{COLOR_RED}Error: File not found: {image_path}{COLOR_RESET}")
        return False

    applied = False

    # 1. Try hyprpaper (default for this Hyprland environment)
    if shutil.which("hyprpaper") or is_process_running("hyprpaper"):
        applied = apply_hyprpaper(image_path)

    # 2. Try swww if hyprpaper not used/failed
    if not applied and shutil.which("swww"):
        applied = apply_swww(image_path)

    # 3. Try swaybg
    if not applied and shutil.which("swaybg"):
        applied = apply_swaybg(image_path)

    # 4. Try generic fallbacks
    if not applied:
        applied = apply_generic_fallbacks(image_path)

    save_state(image_path)

    if not silent:
        filename = image_path.name
        rel_path = str(image_path).replace(str(Path.home()), "~")
        print(f"{COLOR_GREEN}✔ Wallpaper set:{COLOR_RESET} {COLOR_BOLD}{filename}{COLOR_RESET} ({rel_path})")
        show_notification("Wallpaper Changed", filename, image_path=image_path)

    return True


def select_random_wallpaper(images, current=None):
    """Select a random wallpaper, avoiding immediate repetition if possible."""
    if not images:
        return None
    if len(images) == 1:
        return images[0]

    state = load_state()
    current_str = str(current) if current else state.get("current")

    candidates = [img for img in images if str(img) != current_str]
    if not candidates:
        candidates = images

    return random.choice(candidates)


def select_next_wallpaper(images, current=None, reverse=False):
    """Select the next or previous wallpaper alphabetically."""
    if not images:
        return None
    if len(images) == 1:
        return images[0]

    state = load_state()
    current_str = str(current) if current else state.get("current")
    
    paths_str = [str(img) for img in images]
    try:
        idx = paths_str.index(current_str)
        if reverse:
            next_idx = (idx - 1) % len(images)
        else:
            next_idx = (idx + 1) % len(images)
    except ValueError:
        next_idx = 0

    return images[next_idx]


def launch_menu(images):
    """Display an interactive menu using Fuzzel or Wofi to choose a wallpaper."""
    if not images:
        show_notification("Wallpaper Switcher", "No images found in ~/Wallpaper")
        return

    # Prepare menu items
    # Show formatted filename and directory hint
    menu_lines = []
    mapping = {}
    for img in images:
        try:
            rel = img.relative_to(PRIMARY_WALLPAPER_DIR)
            display = f"🖼️  {rel}"
        except ValueError:
            display = f"🖼️  {img.name}  ({img.parent.name})"
        menu_lines.append(display)
        mapping[display] = img

    menu_input = "\n".join(menu_lines)
    selected_line = None

    # Try Fuzzel first
    if shutil.which("fuzzel"):
        try:
            proc = subprocess.Popen(
                ["fuzzel", "-d", "-p", "🎨 Select Wallpaper: ", "-w", "50", "-l", "15"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, _ = proc.communicate(input=menu_input)
            if proc.returncode == 0 and stdout.strip():
                selected_line = stdout.strip()
        except Exception:
            pass

    # Fallback to Wofi
    if not selected_line and shutil.which("wofi"):
        try:
            proc = subprocess.Popen(
                ["wofi", "--dmenu", "--prompt", "Select Wallpaper", "--width", "50%", "--lines", "12"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, _ = proc.communicate(input=menu_input)
            if proc.returncode == 0 and stdout.strip():
                selected_line = stdout.strip()
        except Exception:
            pass

    if selected_line and selected_line in mapping:
        set_wallpaper(mapping[selected_line])


def handle_empty_wallpapers():
    """Handle case where no wallpapers are found in ~/Wallpaper."""
    msg = f"Created directory: {PRIMARY_WALLPAPER_DIR}\nPlease add image files (.jpg, .png, .webp, etc.) to start cycling wallpapers."
    print(f"{COLOR_YELLOW}{msg}{COLOR_RESET}")
    show_notification(
        "Wallpaper Folder Created",
        "Place your images in ~/Wallpaper to cycle through them with SUPER + W.",
        timeout=6000
    )


def run_daemon(interval_seconds, custom_dir=None):
    """Run in background and cycle wallpaper every interval_seconds."""
    print(f"{COLOR_MAUVE}Starting Wallpaper Daemon (Interval: {interval_seconds}s)...{COLOR_RESET}")
    while True:
        images = get_all_wallpapers(custom_dir)
        if images:
            selected = select_random_wallpaper(images)
            if selected:
                set_wallpaper(selected, silent=True)
        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Hyprland Dynamic Wallpaper Switcher & Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 wallpaper_switcher.py --random      # Pick & set a random wallpaper (SUPER + W)
  python3 wallpaper_switcher.py --next        # Switch to next wallpaper
  python3 wallpaper_switcher.py --prev        # Switch to previous wallpaper
  python3 wallpaper_switcher.py --menu        # Open interactive Fuzzel/Wofi wallpaper chooser
  python3 wallpaper_switcher.py --file ~/img.jpg # Set specific wallpaper
  python3 wallpaper_switcher.py --current     # Display current wallpaper path
  python3 wallpaper_switcher.py --daemon 300  # Auto-cycle wallpaper every 5 minutes
        """
    )

    parser.add_argument("-r", "--random", action="store_true", help="Randomly select and apply a wallpaper (default)")
    parser.add_argument("-n", "--next", action="store_true", help="Select and apply next wallpaper alphabetically")
    parser.add_argument("-p", "--prev", action="store_true", help="Select and apply previous wallpaper alphabetically")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive GUI chooser (Fuzzel / Wofi)")
    parser.add_argument("-f", "--file", type=str, help="Apply a specific image file as wallpaper")
    parser.add_argument("-c", "--current", action="store_true", help="Show currently set wallpaper path")
    parser.add_argument("-l", "--list", action="store_true", help="List all discovered wallpapers")
    parser.add_argument("-d", "--dir", type=str, help="Custom directory to search for wallpapers")
    parser.add_argument("--daemon", type=int, nargs="?", const=300, help="Run as background daemon with interval (default: 300s)")
    parser.add_argument("--init", action="store_true", help="Initialize wallpaper on startup (restore or random)")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress notification and verbose output")

    args = parser.parse_args()

    # Ensure ~/Wallpaper exists
    ensure_directories()

    # Direct file specification
    if args.file:
        file_path = Path(args.file).expanduser().resolve()
        if not file_path.is_file():
            print(f"{COLOR_RED}Error: File does not exist: {file_path}{COLOR_RESET}")
            sys.exit(1)
        success = set_wallpaper(file_path, silent=args.silent)
        sys.exit(0 if success else 1)

    # Show current wallpaper
    if args.current:
        state = load_state()
        curr = state.get("current")
        if curr and Path(curr).is_file():
            print(curr)
        else:
            print("No current wallpaper recorded.")
        sys.exit(0)

    # Run daemon mode
    if args.daemon:
        interval = max(5, args.daemon)
        run_daemon(interval, custom_dir=args.dir)
        sys.exit(0)

    # Discover wallpapers
    images = get_all_wallpapers(args.dir)

    # List wallpapers
    if args.list:
        if not images:
            handle_empty_wallpapers()
        else:
            print(f"{COLOR_BOLD}Found {len(images)} wallpaper(s) in {PRIMARY_WALLPAPER_DIR}:{COLOR_RESET}")
            for img in images:
                print(f"  • {img}")
        sys.exit(0)

    if not images:
        handle_empty_wallpapers()
        sys.exit(0)

    # Interactive Menu
    if args.menu:
        launch_menu(images)
        sys.exit(0)

    # Startup Init Mode
    if args.init:
        state = load_state()
        curr = state.get("current")
        if curr and Path(curr).is_file():
            set_wallpaper(curr, silent=True)
        else:
            choice = select_random_wallpaper(images)
            if choice:
                set_wallpaper(choice, silent=True)
        sys.exit(0)

    # Navigation Modes
    if args.next:
        choice = select_next_wallpaper(images, reverse=False)
    elif args.prev:
        choice = select_next_wallpaper(images, reverse=True)
    else:
        # Default: --random
        choice = select_random_wallpaper(images)

    if choice:
        set_wallpaper(choice, silent=args.silent)


if __name__ == "__main__":
    main()
