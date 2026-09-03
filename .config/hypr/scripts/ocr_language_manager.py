#!/usr/bin/env python3
"""
=============================================================================
Tesseract OCR Language Manager & Multi-Language Selector
=============================================================================
A comprehensive graphical (GTK3) and CLI/Fuzzel utility to:
- Select and combine multiple simultaneous OCR languages (e.g. English + Marathi + Hindi)
- Browse, download, and install Tesseract language models without sudo
- Manage installed language packages and delete user-downloaded models
- Instantly trigger and test screen OCR with the active multi-language combination
- Full high-contrast Catppuccin theme styling and App Menu integration
"""

import os
import sys
import json
import html
import shutil
import urllib.request
import argparse
import subprocess
import threading
from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".config" / "hypr"
OCR_CONFIG_PATH = CONFIG_DIR / "ocr_config.json"
USER_TESSDATA_DIR = Path.home() / ".local" / "share" / "tessdata"
SYSTEM_TESSDATA_DIR = Path("/usr/share/tessdata")
OCR_GRAB_SCRIPT = CONFIG_DIR / "scripts" / "ocr_grab.py"

# Official Tesseract Fast Tessdata GitHub Repository
TESSDATA_FAST_BASE_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main"

# Complete Catalog of Languages Supported by Tesseract
LANGUAGE_CATALOG = {
    # Popular
    "eng": {"name": "English", "native": "English", "group": "Popular"},
    "hin": {"name": "Hindi", "native": "हिन्दी", "group": "Indic / South Asian"},
    "mar": {"name": "Marathi", "native": "मराठी", "group": "Indic / South Asian"},
    "spa": {"name": "Spanish", "native": "Español", "group": "Popular"},
    "fra": {"name": "French", "native": "Français", "group": "Popular"},
    "deu": {"name": "German", "native": "Deutsch", "group": "Popular"},
    "chi_sim": {"name": "Chinese (Simplified)", "native": "简体中文", "group": "Popular"},
    "chi_tra": {"name": "Chinese (Traditional)", "native": "繁體中文", "group": "Popular"},
    "jpn": {"name": "Japanese", "native": "日本語", "group": "Popular"},
    "kor": {"name": "Korean", "native": "한국어", "group": "Popular"},
    "rus": {"name": "Russian", "native": "Русский", "group": "Popular"},
    "ara": {"name": "Arabic", "native": "العربية", "group": "Popular"},
    "por": {"name": "Portuguese", "native": "Português", "group": "Popular"},
    "ita": {"name": "Italian", "native": "Italiano", "group": "Popular"},

    # Indic & South Asian
    "ben": {"name": "Bengali / Bangla", "native": "বাংলা", "group": "Indic / South Asian"},
    "tam": {"name": "Tamil", "native": "தமிழ்", "group": "Indic / South Asian"},
    "tel": {"name": "Telugu", "native": "తెలుగు", "group": "Indic / South Asian"},
    "kan": {"name": "Kannada", "native": "ಕನ್ನಡ", "group": "Indic / South Asian"},
    "mal": {"name": "Malayalam", "native": "മലയാളം", "group": "Indic / South Asian"},
    "guj": {"name": "Gujarati", "native": "ગુજરાતી", "group": "Indic / South Asian"},
    "pan": {"name": "Punjabi / Gurmukhi", "native": "ਪੰਜਾਬੀ", "group": "Indic / South Asian"},
    "san": {"name": "Sanskrit", "native": "संस्कृतम्", "group": "Indic / South Asian"},
    "ori": {"name": "Odia / Oriya", "native": "ଓଡ଼ିଆ", "group": "Indic / South Asian"},
    "asm": {"name": "Assamese", "native": "অসমীয়া", "group": "Indic / South Asian"},
    "urd": {"name": "Urdu", "native": "اردو", "group": "Indic / South Asian"},
    "nep": {"name": "Nepali", "native": "नेपाली", "group": "Indic / South Asian"},
    "sin": {"name": "Sinhala", "native": "සිංහල", "group": "Indic / South Asian"},

    # East & Southeast Asian
    "tha": {"name": "Thai", "native": "ไทย", "group": "Southeast Asian"},
    "vie": {"name": "Vietnamese", "native": "Tiếng Việt", "group": "Southeast Asian"},
    "ind": {"name": "Indonesian", "native": "Bahasa Indonesia", "group": "Southeast Asian"},
    "msa": {"name": "Malay", "native": "Bahasa Melayu", "group": "Southeast Asian"},
    "fil": {"name": "Filipino / Tagalog", "native": "Tagalog", "group": "Southeast Asian"},
    "mya": {"name": "Burmese / Myanmar", "native": "မြန်မာဘာသာ", "group": "Southeast Asian"},
    "khm": {"name": "Khmer / Cambodian", "native": "ភាសាខ្មែរ", "group": "Southeast Asian"},
    "lao": {"name": "Lao", "native": "ພາສາລາວ", "group": "Southeast Asian"},

    # European
    "pol": {"name": "Polish", "native": "Polski", "group": "European"},
    "nld": {"name": "Dutch", "native": "Nederlands", "group": "European"},
    "ell": {"name": "Greek", "native": "Ελληνικά", "group": "European"},
    "tur": {"name": "Turkish", "native": "Türkçe", "group": "European"},
    "ukr": {"name": "Ukrainian", "native": "Українська", "group": "European"},
    "ces": {"name": "Czech", "native": "Čeština", "group": "European"},
    "slk": {"name": "Slovak", "native": "Slovenčina", "group": "European"},
    "hun": {"name": "Hungarian", "native": "Magyar", "group": "European"},
    "ron": {"name": "Romanian", "native": "Română", "group": "European"},
    "swe": {"name": "Swedish", "native": "Svenska", "group": "Nordic"},
    "nor": {"name": "Norwegian", "native": "Norsk", "group": "Nordic"},
    "dan": {"name": "Danish", "native": "Dansk", "group": "Nordic"},
    "fin": {"name": "Finnish", "native": "Suomi", "group": "Nordic"},
    "bul": {"name": "Bulgarian", "native": "Български", "group": "European"},
    "srp": {"name": "Serbian", "native": "Српски", "group": "European"},
    "hrv": {"name": "Croatian", "native": "Hrvatski", "group": "European"},
    "bos": {"name": "Bosnian", "native": "Bosanski", "group": "European"},
    "slv": {"name": "Slovenian", "native": "Slovenščina", "group": "European"},
    "lit": {"name": "Lithuanian", "native": "Lietuvių", "group": "European"},
    "lav": {"name": "Latvian", "native": "Latviešu", "group": "European"},
    "est": {"name": "Estonian", "native": "Eesti", "group": "Nordic"},
    "kat": {"name": "Georgian", "native": "ქართული", "group": "European"},
    "hye": {"name": "Armenian", "native": "Հայերեն", "group": "European"},
    "sqi": {"name": "Albanian", "native": "Shqip", "group": "European"},
    "mkd": {"name": "Macedonian", "native": "Македонски", "group": "European"},
    "bel": {"name": "Belarusian", "native": "Беларуская", "group": "European"},
    "isl": {"name": "Icelandic", "native": "Íslenska", "group": "Nordic"},
    "gle": {"name": "Irish", "native": "Gaeilge", "group": "European"},
    "gla": {"name": "Scottish Gaelic", "native": "Gàidhlig", "group": "European"},
    "cym": {"name": "Welsh", "native": "Cymraeg", "group": "European"},
    "eus": {"name": "Basque", "native": "Euskara", "group": "European"},
    "cat": {"name": "Catalan", "native": "Català", "group": "European"},
    "glg": {"name": "Galician", "native": "Galego", "group": "European"},

    # Middle Eastern & African
    "fas": {"name": "Persian / Farsi", "native": "فارسی", "group": "Middle Eastern"},
    "heb": {"name": "Hebrew", "native": "עברית", "group": "Middle Eastern"},
    "kur": {"name": "Kurdish", "native": "Kurdî", "group": "Middle Eastern"},
    "pus": {"name": "Pashto", "native": "پښتو", "group": "Middle Eastern"},
    "uig": {"name": "Uyghur", "native": "ئۇيغۇرچە", "group": "Middle Eastern"},
    "amh": {"name": "Amharic", "native": "አማርኛ", "group": "African"},
    "swa": {"name": "Swahili", "native": "Kiswahili", "group": "African"},
    "afr": {"name": "Afrikaans", "native": "Afrikaans", "group": "African"},
    "yor": {"name": "Yoruba", "native": "Èdè Yorùbá", "group": "African"},

    # Special / Mathematical
    "lat": {"name": "Latin", "native": "Latina", "group": "Classical"},
    "equ": {"name": "Math & Equations", "native": "∑ dx/dt", "group": "Special"},
    "osd": {"name": "Orientation and Script Detection", "native": "OSD", "group": "Special"},
}

CATEGORIES = [
    "All",
    "Popular",
    "Indic / South Asian",
    "European",
    "East Asian",
    "Southeast Asian",
    "Middle Eastern",
    "Nordic",
    "African",
    "Special"
]

def ensure_tessdata_dirs():
    """Ensure user tessdata directory exists and sync system models."""
    USER_TESSDATA_DIR.mkdir(parents=True, exist_ok=True)
    if SYSTEM_TESSDATA_DIR.exists():
        for item in SYSTEM_TESSDATA_DIR.glob("*.traineddata"):
            target = USER_TESSDATA_DIR / item.name
            if not target.exists():
                try:
                    target.symlink_to(item)
                except Exception:
                    pass

def get_installed_languages():
    """Return dictionary of installed language code -> info."""
    ensure_tessdata_dirs()
    installed = {}
    
    # Check ~/.local/share/tessdata
    if USER_TESSDATA_DIR.exists():
        for item in USER_TESSDATA_DIR.glob("*.traineddata"):
            code = item.name.replace(".traineddata", "")
            is_system = item.is_symlink()
            cat = LANGUAGE_CATALOG.get(code, {
                "name": code.upper(),
                "native": code,
                "group": "Custom / Other"
            })
            installed[code] = {
                "code": code,
                "name": cat["name"],
                "native": cat["native"],
                "group": cat["group"],
                "path": str(item),
                "is_system": is_system,
                "size_mb": item.stat().st_size / (1024 * 1024) if item.exists() else 0.0
            }

    # Also check /usr/share/tessdata directly
    if SYSTEM_TESSDATA_DIR.exists():
        for item in SYSTEM_TESSDATA_DIR.glob("*.traineddata"):
            code = item.name.replace(".traineddata", "")
            if code not in installed:
                cat = LANGUAGE_CATALOG.get(code, {
                    "name": code.upper(),
                    "native": code,
                    "group": "Special" if code in ("osd", "equ") else "System"
                })
                installed[code] = {
                    "code": code,
                    "name": cat["name"],
                    "native": cat["native"],
                    "group": cat["group"],
                    "path": str(item),
                    "is_system": True,
                    "size_mb": item.stat().st_size / (1024 * 1024)
                }

    return installed

def load_ocr_config():
    """Load OCR configuration from json file."""
    default_config = {
        "active_language": "eng",
        "active_languages": ["eng"],
        "psm": "6"
    }
    if OCR_CONFIG_PATH.exists():
        try:
            with open(OCR_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass

    if "active_languages" not in default_config or not default_config["active_languages"]:
        raw = default_config.get("active_language", "eng")
        default_config["active_languages"] = [l.strip() for l in raw.split("+") if l.strip()]
    else:
        default_config["active_language"] = "+".join(default_config["active_languages"])

    return default_config

def save_ocr_config(config):
    """Save OCR configuration to json file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(OCR_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)
        return False

def set_active_languages(lang_codes: list):
    """Set active OCR languages list (e.g. ['eng', 'mar'])."""
    clean_codes = [c.strip() for c in lang_codes if c.strip()]
    if not clean_codes:
        clean_codes = ["eng"]

    config = load_ocr_config()
    config["active_languages"] = clean_codes
    config["active_language"] = "+".join(clean_codes)
    save_ocr_config(config)

    # Send notification
    installed = get_installed_languages()
    names = []
    for l in clean_codes:
        if l in installed:
            names.append(f"{installed[l]['name']} ({l})")
        else:
            names.append(l)
    
    display_str = " + ".join(names)
    notify(
        "🌐 OCR Languages Updated",
        f"Active OCR Recognition:\n<b>{display_str}</b>",
        icon="ocr-language-manager"
    )
    return config["active_language"]

def download_language(lang_code: str, progress_callback=None):
    """Download .traineddata file from official GitHub repository."""
    ensure_tessdata_dirs()
    target_file = USER_TESSDATA_DIR / f"{lang_code}.traineddata"
    
    if target_file.is_symlink() and not target_file.exists():
        target_file.unlink()

    url = f"{TESSDATA_FAST_BASE_URL}/{lang_code}.traineddata"

    def reporthook(count, block_size, total_size):
        if progress_callback and total_size > 0:
            percent = min(1.0, count * block_size / total_size)
            progress_callback(percent)

    try:
        urllib.request.urlretrieve(url, target_file, reporthook=reporthook)
        if target_file.exists() and target_file.stat().st_size > 1000:
            return True, "Download successful"
        else:
            if target_file.exists():
                target_file.unlink()
            return False, "Downloaded file is empty or corrupted"
    except Exception as e:
        if target_file.exists():
            target_file.unlink()
        return False, str(e)

def delete_user_language(lang_code: str):
    """Delete a user-downloaded language model from ~/.local/share/tessdata."""
    target_file = USER_TESSDATA_DIR / f"{lang_code}.traineddata"
    if target_file.exists():
        if target_file.is_symlink():
            return False, "Cannot delete system-provided language package."
        target_file.unlink()
        
        # Remove from active if present
        config = load_ocr_config()
        if lang_code in config.get("active_languages", []):
            remaining = [l for l in config["active_languages"] if l != lang_code]
            if not remaining:
                remaining = ["eng"]
            set_active_languages(remaining)

        return True, "Language model deleted."
    return False, "File not found."

def notify(title, body, icon="ocr-language-manager", timeout=4000):
    """Show desktop notification."""
    if not shutil.which("notify-send"):
        return
    cmd = [
        "notify-send",
        "-a", "OCR Language Manager",
        "-i", icon,
        "-t", str(timeout),
        title,
        body
    ]
    try:
        subprocess.Popen(cmd)
    except Exception:
        pass

def run_ocr_grab():
    """Trigger the screen OCR grab utility."""
    if OCR_GRAB_SCRIPT.exists():
        subprocess.Popen(["python3", str(OCR_GRAB_SCRIPT)])
    else:
        notify("❌ Error", "ocr_grab.py not found.", "dialog-error")

# =============================================================================
# Interactive Fuzzel / Dmenu Menu Mode
# =============================================================================

def run_fuzzel_menu():
    """Interactive Fuzzel / Wofi multi-language toggle selector."""
    installed = get_installed_languages()
    config = load_ocr_config()
    active_list = set(config.get("active_languages", ["eng"]))
    active_str = "+".join(sorted(active_list))

    menu_lines = []
    menu_lines.append(f"⭐ Active OCR Combo: {active_str}")
    menu_lines.append("📸 Capture & OCR Screen Now")
    menu_lines.append("⚙️  Open Full OCR Manager GUI")
    menu_lines.append("--- [ TOGGLE INSTALLED LANGUAGES ] ---")

    for code, info in sorted(installed.items(), key=lambda x: (x[0] not in active_list, x[1]["name"])):
        checked = "[✓]" if code in active_list else "[ ]"
        menu_lines.append(f"{checked} {info['name']} ({code}) - {info['native']}")

    menu_lines.append("--- [ DOWNLOAD MORE LANGUAGES ] ---")
    for code, cat in sorted(LANGUAGE_CATALOG.items(), key=lambda x: x[1]["name"]):
        if code not in installed:
            menu_lines.append(f"  + Download {cat['name']} ({code}) - {cat['native']}")

    input_str = "\n".join(menu_lines)

    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", "OCR Languages: ", "--width", "46", "--lines", "18"]
    elif shutil.which("wofi"):
        cmd = ["wofi", "--dmenu", "--prompt", "OCR Languages", "--width", "480", "--height", "480"]
    elif shutil.which("rofi"):
        cmd = ["rofi", "-dmenu", "-p", "OCR Languages"]
    else:
        print("No launcher available.", file=sys.stderr)
        return

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        choice, _ = proc.communicate(input=input_str)
        choice = choice.strip()
        if not choice:
            return

        if "Capture & OCR Screen Now" in choice:
            run_ocr_grab()
        elif "Open Full OCR Manager GUI" in choice:
            subprocess.Popen(["python3", str(Path(__file__).resolve()), "--gui"])
        elif "+ Download" in choice:
            import re
            m = re.search(r"\(([a-z0-9_]+)\)", choice)
            if m:
                code = m.group(1)
                notify("⏳ Downloading Language", f"Downloading Tesseract model for <b>{code}</b>...", "network-idle")
                ok, msg = download_language(code)
                if ok:
                    active_list.add(code)
                    set_active_languages(list(active_list))
                    notify("✅ Language Installed", f"Installed and added <b>{code}</b> to active OCR!", "dialog-information")
                else:
                    notify("❌ Download Failed", f"Could not download {code}: {msg}", "dialog-error")
        elif "(" in choice and ")" in choice:
            import re
            m = re.search(r"\(([a-z0-9_]+)\)", choice)
            if m:
                code = m.group(1)
                if code in installed:
                    if code in active_list:
                        if len(active_list) > 1:
                            active_list.remove(code)
                    else:
                        active_list.add(code)
                    set_active_languages(list(active_list))
    except Exception as e:
        print(f"Error running menu: {e}", file=sys.stderr)

# =============================================================================
# GTK3 Graphical User Interface (High Contrast Catppuccin Theme)
# =============================================================================

def get_theme_colors():
    """Load colors from active theme JSON file with fallback."""
    cache_state = Path.home() / ".cache" / "hypr_theme_state.json"
    current_txt = Path.home() / ".cache" / "current_theme"
    theme_id = "catppuccin-mocha"
    
    if cache_state.exists():
        try:
            with open(cache_state, "r") as f:
                theme_id = json.load(f).get("current_theme", theme_id)
        except Exception:
            pass
    elif current_txt.exists():
        try:
            theme_id = current_txt.read_text().strip() or theme_id
        except Exception:
            pass

    for d in [Path.home() / ".config" / "theme", Path.home() / ".dotfiles" / ".config" / "theme"]:
        tfile = d / f"{theme_id}.json"
        if tfile.exists():
            try:
                with open(tfile, "r") as f:
                    tdata = json.load(f)
                    return tdata.get("colors", {})
            except Exception:
                pass

    return {
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
        "accent": "#cba6f7", "blue": "#89b4fa", "green": "#a6e3a1",
        "yellow": "#f9e2af", "peach": "#fab387", "red": "#f38ba8",
        "mauve": "#cba6f7", "teal": "#94e2d5", "pink": "#f5c2e7",
        "sapphire": "#74c7ec", "lavender": "#b4befe"
    }

def get_contrast_color(hex_color, dark_fg="#11111b", light_fg="#ffffff"):
    """Calculate WCAG high-contrast foreground color based on background luminance."""
    if not hex_color or not isinstance(hex_color, str) or not hex_color.startswith("#"):
        return light_fg
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c + c for c in hex_clean)
    if len(hex_clean) < 6:
        return light_fg
    try:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        return dark_fg if lum > 140 else light_fg
    except Exception:
        return light_fg


def launch_gtk_gui():
    """Launch full GTK3 graphical language manager with multi-language selector."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib

    colors = get_theme_colors()

    c_base = colors.get("base", "#1e1e2e")
    c_mantle = colors.get("mantle", "#181825")
    c_crust = colors.get("crust", "#11111b")
    c_surface0 = colors.get("surface0", "#313244")
    c_surface1 = colors.get("surface1", "#45475a")
    c_surface2 = colors.get("surface2", "#585b70")
    c_text = colors.get("text", "#cdd6f4")
    c_subtext1 = colors.get("subtext1", "#bac2de")
    c_accent = colors.get("accent", "#cba6f7")
    c_green = colors.get("green", "#a6e3a1")
    c_red = colors.get("red", "#f38ba8")
    c_blue = colors.get("blue", "#89b4fa")
    c_sapphire = colors.get("sapphire", "#74c7ec")

    accent_fg = get_contrast_color(c_accent)
    sapphire_fg = get_contrast_color(c_sapphire)
    blue_fg = get_contrast_color(c_blue)
    red_fg = get_contrast_color(c_red)
    green_fg = get_contrast_color(c_green)

    css_provider = Gtk.CssProvider()
    css_data = f"""
    * {{
        font-family: 'JetBrainsMono Nerd Font', 'Noto Sans', sans-serif;
    }}
    
    /* Ensure entire window, viewports, and background remain dark */
    window, viewport, scrolledwindow, box, notebook, notebook > stack, notebook > stack > * {{
        background-color: {c_base};
        color: {c_text};
    }}

    .header-box {{
        background-color: {c_mantle};
        border-bottom: 2px solid {c_surface0};
        padding: 16px 22px;
    }}
    
    .title-label {{
        font-size: 19px;
        font-weight: 800;
        color: {c_accent};
    }}
    
    .subtitle-label {{
        font-size: 12px;
        color: {c_subtext1};
    }}

    .active-combo-bar {{
        background-color: {c_mantle};
        border: 1px solid {c_surface0};
        border-radius: 12px;
        padding: 12px 16px;
        margin: 12px 18px 4px 18px;
    }}

    /* Global button override to fix system theme bleed */
    button {{
        background-image: none;
        box-shadow: none;
        text-shadow: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 12px;
        transition: all 120ms ease-in-out;
    }}

    /* Reset button in active combo bar */
    button.btn-reset {{
        background-color: {c_surface0};
        background-image: none;
        border: 1px solid {c_surface2};
        color: {c_text};
        padding: 6px 14px;
    }}
    button.btn-reset label {{
        color: {c_text};
        font-weight: bold;
    }}
    button.btn-reset:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}
    button.btn-reset:hover label {{
        color: {c_text};
    }}

    /* Action buttons on cards (Select Solo, Only This) */
    button.btn-solo {{
        background-color: {c_surface0};
        background-image: none;
        border: 1px solid {c_surface2};
        color: {c_text};
        padding: 6px 14px;
    }}
    button.btn-solo label {{
        color: {c_text};
        font-weight: bold;
    }}
    button.btn-solo:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}
    button.btn-solo:hover label {{
        color: {c_text};
    }}

    /* Capture & Test OCR Button */
    button.btn-capture {{
        background-color: {c_accent};
        background-image: none;
        border: 1px solid {c_accent};
        color: {accent_fg};
        font-weight: 800;
        font-size: 13px;
        border-radius: 10px;
        padding: 8px 18px;
    }}
    button.btn-capture label {{
        color: {accent_fg};
        font-weight: 800;
    }}
    button.btn-capture:hover {{
        background-color: {c_surface1};
        border-color: {c_accent};
        color: {c_text};
    }}
    button.btn-capture:hover label {{
        color: {c_text};
    }}

    /* Delete Button */
    button.btn-danger {{
        background-color: rgba(243, 139, 168, 0.12);
        background-image: none;
        border: 1px solid {c_red};
        color: {c_red};
        padding: 6px 12px;
    }}
    button.btn-danger label {{
        color: {c_red};
        font-weight: bold;
    }}
    button.btn-danger:hover {{
        background-color: {c_red};
        color: {red_fg};
    }}
    button.btn-danger:hover label {{
        color: {red_fg};
    }}

    /* Download Button */
    button.btn-download {{
        background-color: {c_sapphire};
        background-image: none;
        border: 1px solid {c_sapphire};
        color: {sapphire_fg};
        padding: 6px 14px;
    }}
    button.btn-download label {{
        color: {c_crust};
        font-weight: 800;
    }}
    button.btn-download:hover {{
        background-color: {c_blue};
        color: #000000;
    }}
    button.btn-download:hover label {{
        color: #000000;
    }}

    /* Active Multi-Select Chips */
    .active-chip {{
        background-color: {c_surface0};
        border: 1.5px solid {c_accent};
        border-radius: 16px;
        padding: 5px 12px;
        color: {c_text};
        font-size: 12px;
        font-weight: bold;
    }}
    .active-chip label {{
        color: {c_text};
        font-weight: bold;
    }}
    .active-chip:hover {{
        background-color: {c_surface1};
    }}

    /* Close button on chips */
    button.chip-close-btn {{
        background: transparent;
        background-image: none;
        border: none;
        color: {c_red};
        font-size: 13px;
        font-weight: 800;
        padding: 0 4px;
        margin-left: 6px;
    }}
    button.chip-close-btn label {{
        color: {c_red};
        font-weight: 800;
    }}
    button.chip-close-btn:hover label {{
        color: {colors.get("peach", "#fab387")};
    }}

    /* Search Bar */
    entry.search-entry {{
        background-color: {c_mantle};
        color: {c_text};
        border: 1px solid {c_surface1};
        border-radius: 10px;
        padding: 9px 14px;
        font-size: 13px;
    }}
    entry.search-entry:focus {{
        border-color: {c_accent};
        background-color: {c_crust};
        color: #ffffff;
    }}

    /* Language Cards */
    .card-item {{
        background-color: {c_mantle};
        border: 1px solid {c_surface0};
        border-radius: 12px;
        padding: 14px 18px;
        margin: 5px 14px;
    }}
    .card-item:hover {{
        background-color: {c_surface0};
        border-color: {c_surface1};
    }}
    .card-active {{
        background-color: {c_surface0};
        border: 2px solid {c_accent};
    }}

    /* Category Filter Pills */
    .filter-pill {{
        background-color: {c_mantle};
        color: {c_subtext1};
        border: 1px solid {c_surface0};
        border-radius: 14px;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: bold;
    }}
    .filter-pill:checked {{
        background-color: {c_accent};
        color: {c_crust};
        border-color: {c_accent};
    }}
    .filter-pill label {{
        color: {c_subtext1};
        font-weight: bold;
    }}
    .filter-pill:checked label {{
        color: {c_crust};
        font-weight: 800;
    }}

    /* Notebook Tabs */
    notebook header {{
        background-color: {c_mantle};
        border-bottom: 1px solid {c_surface0};
        padding: 4px 12px;
    }}
    notebook tab {{
        background-color: transparent;
        color: {c_subtext1};
        padding: 10px 22px;
        font-size: 13px;
        font-weight: bold;
        border-radius: 8px 8px 0 0;
        border: none;
    }}
    notebook tab label {{
        color: {c_subtext1};
        font-weight: bold;
    }}
    notebook tab:checked {{
        background-color: {c_base};
        color: {c_accent};
        border-bottom: 3px solid {c_accent};
    }}
    notebook tab:checked label {{
        color: {c_accent};
        font-weight: 800;
    }}

    /* Checkbuttons */
    checkbutton check {{
        min-width: 20px;
        min-height: 20px;
        border-radius: 6px;
        border: 2px solid {c_surface2};
        background-color: {c_surface0};
    }}
    checkbutton check:checked {{
        background-color: {c_accent};
        border-color: {c_accent};
        color: {c_crust};
    }}
    """
    css_provider.load_from_data(css_data.encode("utf-8"))
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    class OCRLangWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Tesseract OCR Language Hub")
            self.set_default_size(800, 740)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.set_icon_name("ocr-language-manager")
            icon_file = Path.home() / ".local/share/icons/hicolor/512x512/apps/ocr-language-manager.png"
            if icon_file.exists():
                try:
                    self.set_icon_from_file(str(icon_file))
                except Exception:
                    pass

            self.installed_langs = get_installed_languages()
            self.config = load_ocr_config()
            self.active_langs = list(self.config.get("active_languages", ["eng"]))
            self.downloading_codes = set()
            self.selected_category = "All"

            main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_vbox)

            # --- 1. Top Header Bar ---
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            header_box.get_style_context().add_class("header-box")
            main_vbox.pack_start(header_box, False, False, 0)

            title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            title_label = Gtk.Label(label="🌐 Tesseract OCR Language Hub", xalign=0)
            title_label.get_style_context().add_class("title-label")
            subtitle_label = Gtk.Label(
                label="Select single or multiple simultaneous recognition languages (e.g. English + Marathi)",
                xalign=0
            )
            subtitle_label.get_style_context().add_class("subtitle-label")
            title_vbox.pack_start(title_label, False, False, 0)
            title_vbox.pack_start(subtitle_label, False, False, 0)
            header_box.pack_start(title_vbox, True, True, 0)

            # Prominent Capture & Test OCR Button
            test_btn = Gtk.Button(label="📸 Capture & Test OCR")
            test_btn.get_style_context().add_class("btn-capture")
            test_btn.connect("clicked", lambda b: run_ocr_grab())
            header_box.pack_start(test_btn, False, False, 0)

            # --- 2. Active Multi-Language Combination Bar ---
            self.combo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            self.combo_box.get_style_context().add_class("active-combo-bar")
            main_vbox.pack_start(self.combo_box, False, False, 0)

            combo_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            combo_title = Gtk.Label(xalign=0)
            combo_title.set_markup(f"<span color='{c_text}'><b>⚡ Active OCR Languages (Simultaneous Recognition):</b></span>")
            combo_header.pack_start(combo_title, True, True, 0)

            # Quick reset button
            reset_en_btn = Gtk.Button(label="Reset to English (eng)")
            reset_en_btn.get_style_context().add_class("btn-reset")
            reset_en_btn.connect("clicked", self.on_reset_english)
            combo_header.pack_start(reset_en_btn, False, False, 0)
            self.combo_box.pack_start(combo_header, False, False, 0)

            # Chips flow row
            self.chips_flow = Gtk.FlowBox()
            self.chips_flow.set_valign(Gtk.Align.START)
            self.chips_flow.set_max_children_per_line(10)
            self.chips_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            self.combo_box.pack_start(self.chips_flow, False, False, 0)

            # Command string preview
            self.cmd_preview_lbl = Gtk.Label(xalign=0)
            self.combo_box.pack_start(self.cmd_preview_lbl, False, False, 0)

            # --- 3. Search Bar ---
            search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            search_box.set_margin_top(12)
            search_box.set_margin_bottom(8)
            search_box.set_margin_start(18)
            search_box.set_margin_end(18)

            self.search_entry = Gtk.Entry()
            self.search_entry.set_placeholder_text("🔍 Search language name, native script, or code (e.g. Marathi, मराठी, mar, Hindi, Sanskrit)...")
            self.search_entry.get_style_context().add_class("search-entry")
            self.search_entry.connect("changed", self.on_search_changed)
            search_box.pack_start(self.search_entry, True, True, 0)
            main_vbox.pack_start(search_box, False, False, 0)

            # --- 4. Notebook (Tabs) ---
            self.notebook = Gtk.Notebook()
            main_vbox.pack_start(self.notebook, True, True, 0)

            # Tab 1: Installed Languages
            self.installed_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            scroll_installed = Gtk.ScrolledWindow()
            scroll_installed.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll_installed.add(self.installed_container)
            self.tab1_label = Gtk.Label()
            self.notebook.append_page(scroll_installed, self.tab1_label)

            # Tab 2: Available Catalog
            available_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

            # Category filter pills
            filter_scroll = Gtk.ScrolledWindow()
            filter_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
            filter_scroll.set_min_content_height(46)
            filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            filter_box.set_margin_start(16)
            filter_box.set_margin_end(16)
            filter_box.set_margin_top(8)
            filter_scroll.add(filter_box)
            available_wrapper.pack_start(filter_scroll, False, False, 0)

            group_btn = None
            for cat in CATEGORIES:
                radio = Gtk.RadioButton.new_with_label_from_widget(group_btn, cat)
                radio.set_mode(False)
                radio.get_style_context().add_class("filter-pill")
                radio.connect("toggled", self.on_category_toggled, cat)
                if cat == "All":
                    radio.set_active(True)
                filter_box.pack_start(radio, False, False, 0)
                if not group_btn:
                    group_btn = radio

            self.available_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            scroll_available = Gtk.ScrolledWindow()
            scroll_available.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll_available.add(self.available_container)
            available_wrapper.pack_start(scroll_available, True, True, 0)

            self.tab2_label = Gtk.Label()
            self.notebook.append_page(available_wrapper, self.tab2_label)

            # Populate initial data
            self.update_chips_and_header()
            self.refresh_installed_list()
            self.refresh_available_list()

        def update_chips_and_header(self):
            """Update active languages chips and command line preview."""
            for child in self.chips_flow.get_children():
                self.chips_flow.remove(child)

            if not self.active_langs:
                self.active_langs = ["eng"]

            for code in self.active_langs:
                info = self.installed_langs.get(code, LANGUAGE_CATALOG.get(code, {"name": code.upper()}))
                name = info.get("name", code)
                
                chip_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                chip_box.get_style_context().add_class("active-chip")
                
                chip_lbl = Gtk.Label(label=f"✓ {name} ({code})")
                chip_box.pack_start(chip_lbl, False, False, 0)

                # Close button (if more than 1 language)
                if len(self.active_langs) > 1:
                    close_btn = Gtk.Button(label="✕")
                    close_btn.get_style_context().add_class("chip-close-btn")
                    close_btn.connect("clicked", lambda b, c=code: self.on_remove_from_active(c))
                    chip_box.pack_start(close_btn, False, False, 0)

                self.chips_flow.add(chip_box)

            self.chips_flow.show_all()

            combo_str = "+".join(self.active_langs)
            self.cmd_preview_lbl.set_markup(
                f"<span foreground='{c_subtext1}' size='small'>"
                f"Active Tesseract Recognition Command: <tt><span foreground='{c_green}' weight='bold'>tesseract -l {combo_str}</span></tt></span>"
            )
            self.tab1_label.set_text(f"📦 Installed ({len(self.installed_langs)})")
            self.tab2_label.set_text(f"➕ Download Models ({len(LANGUAGE_CATALOG) - len(self.installed_langs)})")

        def on_remove_from_active(self, code):
            if code in self.active_langs and len(self.active_langs) > 1:
                self.active_langs.remove(code)
                set_active_languages(self.active_langs)
                self.update_chips_and_header()
                self.refresh_installed_list(self.search_entry.get_text())

        def on_reset_english(self, button):
            self.active_langs = ["eng"]
            set_active_languages(self.active_langs)
            self.update_chips_and_header()
            self.refresh_installed_list(self.search_entry.get_text())

        def on_toggle_language(self, checkbutton, code):
            is_checked = checkbutton.get_active()
            if is_checked:
                if code not in self.active_langs:
                    self.active_langs.append(code)
            else:
                if code in self.active_langs:
                    if len(self.active_langs) > 1:
                        self.active_langs.remove(code)
                    else:
                        checkbutton.set_active(True)
                        notify("⚠️ Info", "At least one language must remain active.", "dialog-information")
                        return

            set_active_languages(self.active_langs)
            self.update_chips_and_header()
            self.refresh_installed_list(self.search_entry.get_text())

        def on_solo_language(self, code):
            """Make this language the ONLY active recognition language."""
            self.active_langs = [code]
            set_active_languages(self.active_langs)
            self.update_chips_and_header()
            self.refresh_installed_list(self.search_entry.get_text())

        def refresh_installed_list(self, query=""):
            for child in self.installed_container.get_children():
                self.installed_container.remove(child)

            self.installed_langs = get_installed_languages()
            self.config = load_ocr_config()
            self.active_langs = list(self.config.get("active_languages", ["eng"]))

            query = query.lower().strip()
            count = 0

            for code, info in sorted(self.installed_langs.items(), key=lambda x: (x[0] not in self.active_langs, x[1]["name"])):
                name = info["name"]
                native = info["native"]
                if query and not (query in name.lower() or query in native.lower() or query in code.lower()):
                    continue

                count += 1
                is_active = (code in self.active_langs)

                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
                card.get_style_context().add_class("card-item")
                if is_active:
                    card.get_style_context().add_class("card-active")

                # Multi-select Checkbox
                chk = Gtk.CheckButton()
                chk.set_active(is_active)
                chk.set_tooltip_text(f"Include {name} in active OCR recognition combo")
                chk.connect("toggled", self.on_toggle_language, code)
                card.pack_start(chk, False, False, 0)

                # Info column
                info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                
                esc_name = html.escape(name)
                esc_native = html.escape(native)
                esc_group = html.escape(info['group'])

                title_txt = f"<span color='{c_text}' weight='bold' size='large'>{esc_name}</span>  <span foreground='{c_subtext1}'>({code})</span>"
                if is_active:
                    title_txt += f"  <span foreground='{c_green}' weight='bold'>● Active (In OCR Combo)</span>"
                
                title_lbl = Gtk.Label(xalign=0)
                title_lbl.set_markup(title_txt)
                
                sub_txt = f"Native: <b>{esc_native}</b> • Category: {esc_group} • Size: {info['size_mb']:.1f} MB"
                if info["is_system"]:
                    sub_txt += " • [System Package]"
                else:
                    sub_txt += " • [User Downloaded]"

                sub_lbl = Gtk.Label(xalign=0)
                sub_lbl.set_markup(f"<span foreground='{c_subtext1}'>{sub_txt}</span>")
                
                info_vbox.pack_start(title_lbl, False, False, 0)
                info_vbox.pack_start(sub_lbl, False, False, 0)
                card.pack_start(info_vbox, True, True, 0)

                # Action buttons
                btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

                solo_btn = Gtk.Button(label="Only This" if is_active else "Select Solo")
                solo_btn.get_style_context().add_class("btn-solo")
                solo_btn.set_tooltip_text(f"Use {name} as the sole OCR language")
                solo_btn.connect("clicked", lambda b, c=code: self.on_solo_language(c))
                btn_box.pack_start(solo_btn, False, False, 0)

                if not info["is_system"]:
                    del_btn = Gtk.Button(label="🗑️ Delete")
                    del_btn.get_style_context().add_class("btn-danger")
                    del_btn.connect("clicked", lambda b, c=code: self.on_delete_lang(c))
                    btn_box.pack_start(del_btn, False, False, 0)

                card.pack_start(btn_box, False, False, 0)
                self.installed_container.pack_start(card, False, False, 3)

            if count == 0:
                empty_lbl = Gtk.Label(label="No installed languages match your search.")
                empty_lbl.set_margin_top(25)
                self.installed_container.pack_start(empty_lbl, False, False, 0)

            self.installed_container.show_all()

        def refresh_available_list(self, query=""):
            for child in self.available_container.get_children():
                self.available_container.remove(child)

            query = query.lower().strip()
            count = 0

            for code, cat in sorted(LANGUAGE_CATALOG.items(), key=lambda x: (x[1]["group"], x[1]["name"])):
                if code in self.installed_langs:
                    continue

                group = cat["group"]
                if self.selected_category != "All" and self.selected_category != group:
                    if not (self.selected_category == "Special" and group == "Special"):
                        continue

                name = cat["name"]
                native = cat["native"]
                if query and not (query in name.lower() or query in native.lower() or query in code.lower() or query in group.lower()):
                    continue

                count += 1

                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
                card.get_style_context().add_class("card-item")

                info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                esc_name = html.escape(name)
                esc_native = html.escape(native)
                esc_group = html.escape(group)

                title_lbl = Gtk.Label(xalign=0)
                title_lbl.set_markup(f"<span color='{c_text}' weight='bold' size='large'>{esc_name}</span> <span foreground='{c_subtext1}'>({code})</span>")
                
                sub_lbl = Gtk.Label(xalign=0)
                sub_lbl.set_markup(f"<span foreground='{c_subtext1}'>Native: <b>{esc_native}</b> • Category: {esc_group}</span>")
                
                info_vbox.pack_start(title_lbl, False, False, 0)
                info_vbox.pack_start(sub_lbl, False, False, 0)
                card.pack_start(info_vbox, True, True, 0)

                # Download button with state
                if code in self.downloading_codes:
                    dl_btn = Gtk.Button(label="⏳ Downloading...")
                    dl_btn.set_sensitive(False)
                else:
                    dl_btn = Gtk.Button(label="⬇️ Download & Add")
                    dl_btn.get_style_context().add_class("btn-download")
                    dl_btn.connect("clicked", lambda b, c=code: self.on_download_clicked(c))

                card.pack_start(dl_btn, False, False, 0)
                self.available_container.pack_start(card, False, False, 3)

            if count == 0:
                empty_lbl = Gtk.Label(label="All languages in this category are installed or no match found.")
                empty_lbl.set_margin_top(25)
                self.available_container.pack_start(empty_lbl, False, False, 0)

            self.available_container.show_all()

        def on_search_changed(self, entry):
            text = entry.get_text()
            self.refresh_installed_list(text)
            self.refresh_available_list(text)

        def on_category_toggled(self, button, category):
            if button.get_active():
                self.selected_category = category
                self.refresh_available_list(self.search_entry.get_text())

        def on_delete_lang(self, code):
            ok, msg = delete_user_language(code)
            if ok:
                self.refresh_installed_list(self.search_entry.get_text())
                self.refresh_available_list(self.search_entry.get_text())
                self.update_chips_and_header()
                notify("🗑️ Language Removed", f"Model <b>{code}</b> has been deleted.", "dialog-information")
            else:
                notify("❌ Error", msg, "dialog-error")

        def on_download_clicked(self, code):
            self.downloading_codes.add(code)
            self.refresh_available_list(self.search_entry.get_text())
            notify("⏳ Downloading Language", f"Downloading model for <b>{code}</b>...", "network-idle")

            def worker():
                ok, msg = download_language(code)
                def on_done():
                    self.downloading_codes.discard(code)
                    if ok:
                        if code not in self.active_langs:
                            self.active_langs.append(code)
                            set_active_languages(self.active_langs)
                        notify("✅ Language Ready", f"Installed and added <b>{code}</b> to active OCR combo!", "dialog-information")
                    else:
                        notify("❌ Download Failed", f"Failed to download {code}: {msg}", "dialog-error")
                    self.update_chips_and_header()
                    self.refresh_installed_list(self.search_entry.get_text())
                    self.refresh_available_list(self.search_entry.get_text())
                GLib.idle_add(on_done)

            threading.Thread(target=worker, daemon=True).start()

    win = OCRLangWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

# =============================================================================
# CLI Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Tesseract OCR Language Manager & Multi-Language Selector")
    parser.add_argument("-g", "--gui", action="store_true", help="Open graphical GTK3 interface (default if no args)")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel / Wofi multi-language toggle menu")
    parser.add_argument("-l", "--list", action="store_true", help="List installed Tesseract languages and active combination")
    parser.add_argument("-s", "--set", type=str, metavar="CODES", help="Set active OCR languages (e.g. 'mar', 'eng+mar', 'eng+hin+san')")
    parser.add_argument("-i", "--install", type=str, metavar="CODE", help="Download and install language model without sudo")
    parser.add_argument("-d", "--delete", type=str, metavar="CODE", help="Delete user-downloaded language model")
    parser.add_argument("-t", "--test", action="store_true", help="Trigger screen OCR grab immediately")

    args = parser.parse_args()

    if args.list:
        installed = get_installed_languages()
        config = load_ocr_config()
        active_list = set(config.get("active_languages", ["eng"]))
        active_combo = "+".join(config.get("active_languages", ["eng"]))
        print(f"\nActive OCR Combination: \033[1;32m{active_combo}\033[0m\n")
        print("Installed Tesseract Languages:")
        for code, info in sorted(installed.items(), key=lambda x: (x[0] not in active_list, x[1]["name"])):
            mark = "● [ACTIVE]" if code in active_list else "  [      ]"
            loc = "[System]" if info["is_system"] else "[User]"
            print(f"  {mark:12} {code:8} {info['name']:25} {info['native']:15} {loc}")
        print("")
        sys.exit(0)

    if args.set:
        codes = [c.strip() for c in args.set.split("+") if c.strip()]
        result = set_active_languages(codes)
        print(f"Active OCR language combination set to: {result}")
        sys.exit(0)

    if args.install:
        code = args.install.lower().strip()
        print(f"Downloading Tesseract model for '{code}'...")
        ok, msg = download_language(code)
        if ok:
            config = load_ocr_config()
            active = config.get("active_languages", ["eng"])
            if code not in active:
                active.append(code)
                set_active_languages(active)
            print(f"Successfully installed and activated '{code}' in OCR combo!")
        else:
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.delete:
        ok, msg = delete_user_language(args.delete)
        if ok:
            print(f"Language '{args.delete}' deleted.")
        else:
            print(f"Error: {msg}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if args.test:
        run_ocr_grab()
        sys.exit(0)

    if args.menu:
        run_fuzzel_menu()
        sys.exit(0)

    # Default to GUI
    launch_gtk_gui()

if __name__ == "__main__":
    main()
