#!/usr/bin/env python3
"""
=============================================================================
Tesseract OCR Language Manager & Selector
=============================================================================
A comprehensive graphical (GTK3) and CLI/Fuzzel utility to:
- Browse, download, and install Tesseract language models without sudo
- View and select active OCR language(s) (including multi-language e.g. eng+hin)
- Manage installed language packages and delete user-downloaded models
- Instantly trigger and test screen OCR with the active language
- Full Catppuccin / Dynamic Theme support and App Menu integration
"""

import os
import sys
import json
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
    "mar": {"name": "Marathi", "native": "मराठी", "group": "Indic / South Asian"},
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
    "equ": {"name": "Math / Equations", "native": "∑ dx/dt", "group": "Special"},
    "osd": {"name": "Orientation & Script Detection", "native": "OSD", "group": "Special"},
}

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
                    "group": "System"
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

def set_active_language(lang_code: str):
    """Set active OCR language code (e.g. 'eng' or 'eng+hin')."""
    config = load_ocr_config()
    config["active_language"] = lang_code
    if "+" in lang_code:
        config["active_languages"] = [l.strip() for l in lang_code.split("+") if l.strip()]
    else:
        config["active_languages"] = [lang_code]
    save_ocr_config(config)

    # Send notification
    installed = get_installed_languages()
    names = []
    for l in config["active_languages"]:
        if l in installed:
            names.append(f"{installed[l]['name']} ({l})")
        else:
            names.append(l)
    
    display_str = " + ".join(names)
    notify(
        "🌐 OCR Language Set",
        f"Active OCR Language:\n<b>{display_str}</b>",
        icon="character-set"
    )

def download_language(lang_code: str, progress_callback=None):
    """Download .traineddata file from official GitHub repository."""
    ensure_tessdata_dirs()
    target_file = USER_TESSDATA_DIR / f"{lang_code}.traineddata"
    
    # If it's currently a broken symlink, remove it
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
        return True, "Language model deleted."
    return False, "File not found."

def notify(title, body, icon="character-set", timeout=4000):
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
    """Interactive Fuzzel / Wofi language selector."""
    installed = get_installed_languages()
    config = load_ocr_config()
    active_lang = config.get("active_language", "eng")

    menu_lines = []
    # Active indicator header
    active_display = active_lang
    if active_lang in installed:
        active_display = f"{installed[active_lang]['name']} ({active_lang})"
    menu_lines.append(f"⭐ Active Language: {active_display}")
    menu_lines.append("📸 Capture & OCR Screen Now")
    menu_lines.append("⚙️  Open Full OCR Language Manager GUI")
    menu_lines.append("--- [ INSTALLED LANGUAGES ] ---")

    for code, info in sorted(installed.items(), key=lambda x: x[1]["name"]):
        badge = "✓ " if code == active_lang else "  "
        menu_lines.append(f"{badge}{info['name']} ({code}) - {info['native']}")

    menu_lines.append("--- [ DOWNLOAD MORE LANGUAGES ] ---")
    # Add uninstalled languages from catalog
    for code, cat in sorted(LANGUAGE_CATALOG.items(), key=lambda x: x[1]["name"]):
        if code not in installed:
            menu_lines.append(f"  + Download {cat['name']} ({code}) - {cat['native']}")

    input_str = "\n".join(menu_lines)

    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", "OCR Lang: ", "--width", "42", "--lines", "16"]
    elif shutil.which("wofi"):
        cmd = ["wofi", "--dmenu", "--prompt", "OCR Languages", "--width", "450", "--height", "450"]
    elif shutil.which("rofi"):
        cmd = ["rofi", "-dmenu", "-p", "OCR Languages"]
    else:
        print("No launcher (fuzzel/wofi/rofi) available.", file=sys.stderr)
        return

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        choice, _ = proc.communicate(input=input_str)
        choice = choice.strip()
        if not choice:
            return

        if "Capture & OCR Screen Now" in choice:
            run_ocr_grab()
        elif "Open Full OCR Language Manager GUI" in choice:
            subprocess.Popen(["python3", str(Path(__file__).resolve()), "--gui"])
        elif "+ Download" in choice:
            # Extract code inside parentheses
            import re
            m = re.search(r"\(([a-z0-9_]+)\)", choice)
            if m:
                code = m.group(1)
                notify("⏳ Downloading Language", f"Downloading Tesseract model for <b>{code}</b>...", "network-idle")
                ok, msg = download_language(code)
                if ok:
                    set_active_language(code)
                    notify("✅ Language Installed", f"Successfully installed and activated <b>{code}</b>!", "dialog-information")
                else:
                    notify("❌ Download Failed", f"Could not download {code}: {msg}", "dialog-error")
        elif "(" in choice and ")" in choice:
            import re
            m = re.search(r"\(([a-z0-9_]+)\)", choice)
            if m:
                code = m.group(1)
                if code in installed:
                    set_active_language(code)
    except Exception as e:
        print(f"Error running menu: {e}", file=sys.stderr)

# =============================================================================
# GTK3 Graphical User Interface
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
        "mauve": "#cba6f7", "teal": "#94e2d5", "pink": "#f5c2e7"
    }

def launch_gtk_gui():
    """Launch full GTK3 graphical language manager."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib

    colors = get_theme_colors()

    css_provider = Gtk.CssProvider()
    css_data = f"""
    * {{
        font-family: 'JetBrainsMono Nerd Font', 'Noto Sans', sans-serif;
    }}
    window {{
        background-color: {colors.get("base", "#1e1e2e")};
        color: {colors.get("text", "#cdd6f4")};
    }}
    .header-box {{
        background-color: {colors.get("mantle", "#181825")};
        border-bottom: 2px solid {colors.get("surface0", "#313244")};
        padding: 16px 20px;
    }}
    .title-label {{
        font-size: 18px;
        font-weight: bold;
        color: {colors.get("accent", "#cba6f7")};
    }}
    .subtitle-label {{
        font-size: 12px;
        color: {colors.get("subtext0", "#a6adc8")};
    }}
    .active-badge {{
        background-color: {colors.get("surface0", "#313244")};
        border: 1px solid {colors.get("accent", "#cba6f7")};
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: bold;
        color: {colors.get("accent", "#cba6f7")};
    }}
    .search-entry {{
        background-color: {colors.get("surface0", "#313244")};
        color: {colors.get("text", "#cdd6f4")};
        border: 1px solid {colors.get("surface1", "#45475a")};
        border-radius: 8px;
        padding: 8px 12px;
    }}
    .search-entry:focus {{
        border-color: {colors.get("accent", "#cba6f7")};
    }}
    .card-item {{
        background-color: {colors.get("mantle", "#181825")};
        border: 1px solid {colors.get("surface0", "#313244")};
        border-radius: 10px;
        padding: 12px 16px;
        margin: 4px 8px;
    }}
    .card-item:hover {{
        background-color: {colors.get("surface0", "#313244")};
        border-color: {colors.get("surface1", "#45475a")};
    }}
    .card-active {{
        background-color: {colors.get("surface0", "#313244")};
        border: 1px solid {colors.get("accent", "#cba6f7")};
    }}
    .btn-primary {{
        background-color: {colors.get("accent", "#cba6f7")};
        color: {colors.get("base", "#1e1e2e")};
        font-weight: bold;
        border-radius: 8px;
        padding: 6px 14px;
        border: none;
    }}
    .btn-primary:hover {{
        background-color: {colors.get("mauve", "#cba6f7")};
    }}
    .btn-secondary {{
        background-color: {colors.get("surface0", "#313244")};
        color: {colors.get("text", "#cdd6f4")};
        border: 1px solid {colors.get("surface1", "#45475a")};
        border-radius: 8px;
        padding: 6px 12px;
    }}
    .btn-secondary:hover {{
        background-color: {colors.get("surface1", "#45475a")};
    }}
    .btn-danger {{
        background-color: transparent;
        color: {colors.get("red", "#f38ba8")};
        border: 1px solid {colors.get("red", "#f38ba8")};
        border-radius: 8px;
        padding: 4px 10px;
    }}
    .btn-danger:hover {{
        background-color: {colors.get("red", "#f38ba8")};
        color: {colors.get("base", "#1e1e2e")};
    }}
    notebook tab {{
        background-color: {colors.get("mantle", "#181825")};
        color: {colors.get("subtext0", "#a6adc8")};
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }}
    notebook tab:checked {{
        background-color: {colors.get("base", "#1e1e2e")};
        color: {colors.get("accent", "#cba6f7")};
        border-bottom: 2px solid {colors.get("accent", "#cba6f7")};
    }}
    """
    css_provider.load_from_data(css_data.encode("utf-8"))
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    class OCRLangWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Tesseract OCR Language Manager")
            self.set_default_size(720, 680)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.set_icon_name("character-set")

            self.installed_langs = get_installed_languages()
            self.config = load_ocr_config()
            self.active_lang = self.config.get("active_language", "eng")
            self.downloading_codes = set()

            main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.add(main_vbox)

            # --- Header Bar ---
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header_box.get_style_context().add_class("header-box")
            main_vbox.pack_start(header_box, False, False, 0)

            title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_label = Gtk.Label(label="🌐 Tesseract OCR Language Manager", xalign=0)
            title_label.get_style_context().add_class("title-label")
            subtitle_label = Gtk.Label(label="Install language models, manage multi-lingual OCR, and test capture", xalign=0)
            subtitle_label.get_style_context().add_class("subtitle-label")
            title_vbox.pack_start(title_label, False, False, 0)
            title_vbox.pack_start(subtitle_label, False, False, 0)
            header_box.pack_start(title_vbox, True, True, 0)

            # Active badge
            self.active_badge = Gtk.Label()
            self.active_badge.get_style_context().add_class("active-badge")
            self.update_active_badge()
            header_box.pack_start(self.active_badge, False, False, 0)

            # Quick Test Button
            test_btn = Gtk.Button(label="📸 Capture & Test OCR")
            test_btn.get_style_context().add_class("btn-primary")
            test_btn.connect("clicked", lambda b: run_ocr_grab())
            header_box.pack_start(test_btn, False, False, 0)

            # --- Search Entry ---
            search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            search_box.set_margin_top(12)
            search_box.set_margin_bottom(8)
            search_box.set_margin_start(16)
            search_box.set_margin_end(16)

            self.search_entry = Gtk.Entry()
            self.search_entry.set_placeholder_text("🔍 Search language name, native script, or code (e.g. Hindi, 日本語, fra)...")
            self.search_entry.get_style_context().add_class("search-entry")
            self.search_entry.connect("changed", self.on_search_changed)
            search_box.pack_start(self.search_entry, True, True, 0)
            main_vbox.pack_start(search_box, False, False, 0)

            # --- Notebook (Tabs) ---
            self.notebook = Gtk.Notebook()
            main_vbox.pack_start(self.notebook, True, True, 0)

            # Tab 1: Installed
            self.installed_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            scroll_installed = Gtk.ScrolledWindow()
            scroll_installed.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll_installed.add(self.installed_container)
            tab1_label = Gtk.Label(label="📦 Installed Languages")
            self.notebook.append_page(scroll_installed, tab1_label)

            # Tab 2: Available Catalog
            self.available_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            scroll_available = Gtk.ScrolledWindow()
            scroll_available.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll_available.add(self.available_container)
            tab2_label = Gtk.Label(label="➕ Download Languages")
            self.notebook.append_page(scroll_available, tab2_label)

            # Populate Lists
            self.refresh_installed_list()
            self.refresh_available_list()

        def update_active_badge(self):
            info = self.installed_langs.get(self.active_lang, {})
            name = info.get("name", self.active_lang)
            self.active_badge.set_markup(f"Active: <b>{name} ({self.active_lang})</b>")

        def refresh_installed_list(self, query=""):
            for child in self.installed_container.get_children():
                self.installed_container.remove(child)

            self.installed_langs = get_installed_languages()
            self.config = load_ocr_config()
            self.active_lang = self.config.get("active_language", "eng")
            self.update_active_badge()

            query = query.lower().strip()
            count = 0

            for code, info in sorted(self.installed_langs.items(), key=lambda x: (x[0] != self.active_lang, x[1]["name"])):
                name = info["name"]
                native = info["native"]
                if query and not (query in name.lower() or query in native.lower() or query in code.lower()):
                    continue

                count += 1
                is_active = (code == self.active_lang)

                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                card.get_style_context().add_class("card-item")
                if is_active:
                    card.get_style_context().add_class("card-active")

                # Info label
                info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                title_txt = f"<b>{name}</b>  <span foreground='{colors.get('subtext0', '#a6adc8')}'>({code})</span>"
                if is_active:
                    title_txt += f"  <span foreground='{colors.get('green', '#a6e3a1')}'>● Active</span>"
                
                title_lbl = Gtk.Label(xalign=0)
                title_lbl.set_markup(title_txt)
                
                sub_txt = f"{native} • Group: {info['group']} • Size: {info['size_mb']:.1f} MB"
                if info["is_system"]:
                    sub_txt += " • [System Package]"
                else:
                    sub_txt += " • [User Downloaded]"

                sub_lbl = Gtk.Label(xalign=0)
                sub_lbl.set_markup(f"<span foreground='{colors.get('subtext0', '#a6adc8')}' size='small'>{sub_txt}</span>")
                
                info_vbox.pack_start(title_lbl, False, False, 0)
                info_vbox.pack_start(sub_lbl, False, False, 0)
                card.pack_start(info_vbox, True, True, 0)

                # Actions
                if is_active:
                    active_btn = Gtk.Button(label="✓ Current Active")
                    active_btn.set_sensitive(False)
                    active_btn.get_style_context().add_class("btn-secondary")
                    card.pack_start(active_btn, False, False, 0)
                else:
                    set_btn = Gtk.Button(label="Select as Active")
                    set_btn.get_style_context().add_class("btn-primary")
                    set_btn.connect("clicked", lambda b, c=code: self.on_set_active(c))
                    card.pack_start(set_btn, False, False, 0)

                if not info["is_system"]:
                    del_btn = Gtk.Button(label="🗑️ Delete")
                    del_btn.get_style_context().add_class("btn-danger")
                    del_btn.connect("clicked", lambda b, c=code: self.on_delete_lang(c))
                    card.pack_start(del_btn, False, False, 0)

                self.installed_container.pack_start(card, False, False, 2)

            if count == 0:
                empty_lbl = Gtk.Label(label="No installed languages match the search query.")
                empty_lbl.set_margin_top(20)
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

                name = cat["name"]
                native = cat["native"]
                group = cat["group"]
                if query and not (query in name.lower() or query in native.lower() or query in code.lower() or query in group.lower()):
                    continue

                count += 1

                card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                card.get_style_context().add_class("card-item")

                info_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                title_lbl = Gtk.Label(xalign=0)
                title_lbl.set_markup(f"<b>{name}</b> <span foreground='{colors.get('subtext0', '#a6adc8')}'>({code})</span>")
                
                sub_lbl = Gtk.Label(xalign=0)
                sub_lbl.set_markup(f"<span foreground='{colors.get('subtext0', '#a6adc8')}' size='small'>{native} • Category: {group}</span>")
                
                info_vbox.pack_start(title_lbl, False, False, 0)
                info_vbox.pack_start(sub_lbl, False, False, 0)
                card.pack_start(info_vbox, True, True, 0)

                # Download button
                if code in self.downloading_codes:
                    dl_btn = Gtk.Button(label="⏳ Downloading...")
                    dl_btn.set_sensitive(False)
                else:
                    dl_btn = Gtk.Button(label="⬇️ Download Model")
                    dl_btn.get_style_context().add_class("btn-primary")
                    dl_btn.connect("clicked", lambda b, c=code: self.on_download_clicked(c))

                card.pack_start(dl_btn, False, False, 0)
                self.available_container.pack_start(card, False, False, 2)

            if count == 0:
                empty_lbl = Gtk.Label(label="All catalog languages are already installed or no match found.")
                empty_lbl.set_margin_top(20)
                self.available_container.pack_start(empty_lbl, False, False, 0)

            self.available_container.show_all()

        def on_search_changed(self, entry):
            text = entry.get_text()
            self.refresh_installed_list(text)
            self.refresh_available_list(text)

        def on_set_active(self, code):
            set_active_language(code)
            self.active_lang = code
            self.refresh_installed_list(self.search_entry.get_text())

        def on_delete_lang(self, code):
            ok, msg = delete_user_language(code)
            if ok:
                if self.active_lang == code:
                    set_active_language("eng")
                self.refresh_installed_list(self.search_entry.get_text())
                self.refresh_available_list(self.search_entry.get_text())
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
                        set_active_language(code)
                        notify("✅ Language Ready", f"Successfully installed and activated <b>{code}</b>!", "dialog-information")
                    else:
                        notify("❌ Download Failed", f"Failed to download {code}: {msg}", "dialog-error")
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
    parser = argparse.ArgumentParser(description="Tesseract OCR Language Manager & Selector")
    parser.add_argument("-g", "--gui", action="store_true", help="Open graphical GTK3 interface (default if no args)")
    parser.add_argument("-m", "--menu", action="store_true", help="Open interactive Fuzzel / Wofi language selector")
    parser.add_argument("-l", "--list", action="store_true", help="List installed Tesseract languages")
    parser.add_argument("-s", "--set", type=str, metavar="CODE", help="Set active OCR language (e.g. 'hin' or 'eng+hin')")
    parser.add_argument("-i", "--install", type=str, metavar="CODE", help="Download and install language model without sudo")
    parser.add_argument("-d", "--delete", type=str, metavar="CODE", help="Delete user-downloaded language model")
    parser.add_argument("-t", "--test", action="store_true", help="Trigger screen OCR grab immediately")

    args = parser.parse_args()

    if args.list:
        installed = get_installed_languages()
        config = load_ocr_config()
        active = config.get("active_language", "eng")
        print(f"\nActive Language: \033[1;32m{active}\033[0m\n")
        print("Installed Tesseract Languages:")
        for code, info in sorted(installed.items(), key=lambda x: x[1]["name"]):
            mark = "● (Active)" if code == active else " "
            loc = "[System]" if info["is_system"] else "[User]"
            print(f"  {mark:10} {code:8} {info['name']:25} {info['native']:15} {loc}")
        print("")
        sys.exit(0)

    if args.set:
        set_active_language(args.set)
        print(f"Active OCR language set to: {args.set}")
        sys.exit(0)

    if args.install:
        code = args.install.lower().strip()
        print(f"Downloading Tesseract model for '{code}'...")
        ok, msg = download_language(code)
        if ok:
            set_active_language(code)
            print(f"Successfully installed and activated '{code}'!")
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
