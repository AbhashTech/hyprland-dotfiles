#!/usr/bin/env python3
"""
Calendar helper for QuickShell Calendar Plugin.
Handles importing calendar .ics files from URL or local disk,
caching events, parsing recurrent/standard VEVENTs,
and querying today's and upcoming events.
"""

import sys
import os
import json
import subprocess
import shutil
import urllib.request
import urllib.error
import datetime
import re
import hashlib
from pathlib import Path

DATA_DIR = Path(os.path.expanduser("~/.config/quickshell/calendar_data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "sources.json"
CACHE_FILE = DATA_DIR / "events_cache.json"

def load_sources():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sources": []}

def save_sources(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def clean_ics_text(val):
    if not val:
        return ""
    # Unescape ICS escaped characters \, \; \, \n \N
    val = re.sub(r'\\([,;\\])', r'\1', val)
    val = val.replace('\\n', '\n').replace('\\N', '\n')
    return val.strip()

def parse_ics_datetime(dt_str):
    """
    Parse ICS datetime string into (datetime.datetime or datetime.date, is_all_day).
    Formats:
    20261004T093000Z
    20261004T093000
    TZID=...:20261004T093000
    VALUE=DATE:20261004
    20261004
    """
    if not dt_str:
        return None, False
    dt_str = dt_str.strip()
    # Check if all day date
    if "T" not in dt_str:
        # e.g. 20261004
        val = dt_str[-8:] if len(dt_str) >= 8 else dt_str
        try:
            d = datetime.datetime.strptime(val, "%Y%m%d").date()
            return datetime.datetime.combine(d, datetime.time.min), True
        except Exception:
            return None, False

    # Datetime format
    is_zulu = dt_str.endswith("Z")
    clean_val = dt_str.rstrip("Z")
    # Take the last 15 chars if contains YYYYMMDDTHHMMSS
    m = re.search(r'(\d{8}T\d{6})', clean_val)
    if m:
        try:
            dt = datetime.datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")
            return dt, False
        except Exception:
            pass
    return None, False

def parse_ics_content(ics_text, source_name=""):
    """
    Unfolds lines and extracts VEVENT components.
    """
    # Unfold lines (ICS lines beginning with space or tab are continuation of prev line)
    unfolded_lines = []
    for line in ics_text.splitlines():
        if line.startswith((' ', '\t')) and unfolded_lines:
            unfolded_lines[-1] += line[1:]
        else:
            unfolded_lines.append(line)

    events = []
    in_vevent = False
    cur_event = {}

    for line in unfolded_lines:
        line = line.strip()
        if not line:
            continue
        if line == "BEGIN:VEVENT":
            in_vevent = True
            cur_event = {"source": source_name}
            continue
        elif line == "END:VEVENT":
            in_vevent = False
            if "start" in cur_event and "summary" in cur_event:
                events.append(cur_event)
            cur_event = {}
            continue

        if in_vevent:
            colon_idx = line.find(":")
            if colon_idx == -1:
                continue
            prop_part = line[:colon_idx]
            val_part = line[colon_idx + 1:]
            prop_name = prop_part.split(";")[0].upper()

            if prop_name == "UID":
                cur_event["uid"] = clean_ics_text(val_part)
            elif prop_name == "SUMMARY":
                cur_event["summary"] = clean_ics_text(val_part)
            elif prop_name == "DESCRIPTION":
                cur_event["description"] = clean_ics_text(val_part)
            elif prop_name == "LOCATION":
                cur_event["location"] = clean_ics_text(val_part)
            elif prop_name == "DTSTART":
                dt, is_all_day = parse_ics_datetime(val_part)
                if dt:
                    cur_event["start"] = dt.strftime("%Y-%m-%dT%H:%M:%S")
                    cur_event["startDate"] = dt.strftime("%Y-%m-%d")
                    cur_event["allDay"] = is_all_day
                    cur_event["timeStr"] = "All Day" if is_all_day else dt.strftime("%I:%M %p")
            elif prop_name == "DTEND":
                dt, is_all_day = parse_ics_datetime(val_part)
                if dt:
                    cur_event["end"] = dt.strftime("%Y-%m-%dT%H:%M:%S")
                    cur_event["endDate"] = dt.strftime("%Y-%m-%d")

    return events

def fetch_and_sync_all():
    """
    Fetch all configured sources (disk or url) and rebuild cache.
    """
    config = load_sources()
    sources = config.get("sources", [])
    all_events = []
    errors = []

    for src in sources:
        if not src.get("enabled", True):
            continue
        src_name = src.get("name", "Calendar")
        src_type = src.get("type", "file") # "file" or "url"
        src_path = src.get("path", "")
        color = src.get("color", "#88c0d0")

        ics_content = ""
        try:
            if src_type == "url":
                req = urllib.request.Request(
                    src_path,
                    headers={'User-Agent': 'Mozilla/5.0 (Quickshell Calendar/1.0)'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    ics_content = response.read().decode('utf-8', errors='ignore')
            elif src_type == "file":
                expanded_path = os.path.expanduser(src_path)
                if os.path.exists(expanded_path):
                    with open(expanded_path, "r", encoding="utf-8", errors="ignore") as f:
                        ics_content = f.read()
                else:
                    errors.append(f"File not found: {src_path}")
                    continue

            if ics_content:
                parsed = parse_ics_content(ics_content, src_name)
                for ev in parsed:
                    ev["color"] = color
                all_events.extend(parsed)
        except Exception as e:
            errors.append(f"Error fetching {src_name}: {str(e)}")

    # Sort events by start date/time
    all_events.sort(key=lambda x: x.get("start", ""))

    cache_data = {
        "last_sync": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": all_events,
        "errors": errors
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)

    return cache_data

def get_cached_events():
    if not CACHE_FILE.exists():
        return fetch_and_sync_all()
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fetch_and_sync_all()

def query_events(view_date_str=None):
    """
    Return organized events:
    - events_by_date: map of 'YYYY-MM-DD' -> count / event summaries
    - today_events: list of events for today
    - future_events: list of future events within next 30 days
    """
    cache = get_cached_events()
    events = cache.get("events", [])
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    events_by_date = {}
    today_events = []
    future_events = []

    for ev in events:
        start_date = ev.get("startDate")
        if not start_date:
            continue
        if start_date not in events_by_date:
            events_by_date[start_date] = []
        events_by_date[start_date].append(ev)

        if start_date == today_str:
            today_events.append(ev)
        elif start_date > today_str:
            # Check within next 30 days
            try:
                ev_d = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                delta = (ev_d - now.date()).days
                if 0 < delta <= 30:
                    ev_copy = dict(ev)
                    ev_copy["daysUntil"] = delta
                    ev_copy["dateLabel"] = ev_d.strftime("%a, %b %d")
                    future_events.append(ev_copy)
            except Exception:
                pass

    return {
        "last_sync": cache.get("last_sync", ""),
        "today_str": today_str,
        "today_events": today_events,
        "future_events": future_events[:20], # limit 20
        "events_by_date": {k: len(v) for k, v in events_by_date.items()},
        "events_map": events_by_date
    }

def add_source(name, src_type, path, color="#88c0d0"):
    config = load_sources()
    sources = config.get("sources", [])
    # Check if duplicate path
    for s in sources:
        if s.get("path") == path:
            s["name"] = name
            s["type"] = src_type
            s["color"] = color
            s["enabled"] = True
            save_sources(config)
            fetch_and_sync_all()
            return {"status": "ok", "message": "Updated existing source"}

    src_id = hashlib.md5(f"{path}{time.time()}".encode()).hexdigest()[:8]
    sources.append({
        "id": src_id,
        "name": name or ("URL Calendar" if src_type == "url" else Path(path).name),
        "type": src_type,
        "path": path,
        "color": color,
        "enabled": True
    })
    config["sources"] = sources
    save_sources(config)
    fetch_and_sync_all()
    return {"status": "ok", "message": "Added source successfully"}

def remove_source(source_id_or_path):
    config = load_sources()
    sources = [s for s in config.get("sources", []) if s.get("id") != source_id_or_path and s.get("path") != source_id_or_path]
    config["sources"] = sources
    save_sources(config)
    fetch_and_sync_all()
    return {"status": "ok", "message": "Removed source"}

def toggle_source(source_id):
    config = load_sources()
    for s in config.get("sources", []):
        if s.get("id") == source_id:
            s["enabled"] = not s.get("enabled", True)
            break
    save_sources(config)
    fetch_and_sync_all()
    return {"status": "ok"}

def import_sample_ics():
    """Create a sample calendar file with upcoming events if user has none."""
    sample_file = DATA_DIR / "sample_events.ics"
    now = datetime.datetime.now()
    d0 = now.strftime("%Y%m%d")
    d1 = (now + datetime.timedelta(days=1)).strftime("%Y%m%d")
    d2 = (now + datetime.timedelta(days=3)).strftime("%Y%m%d")
    d3 = (now + datetime.timedelta(days=7)).strftime("%Y%m%d")

    ics_data = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Quickshell Calendar//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:sample-01-{d0}
SUMMARY:QuickShell Project Review
DESCRIPTION:Review custom calendar integration and performance.
DTSTART:{d0}T100000
DTEND:{d0}T110000
LOCATION:Workspace Desktop
END:VEVENT
BEGIN:VEVENT
UID:sample-02-{d0}
SUMMARY:Team Lunch & Tech Talk
DESCRIPTION:Discussion on Linux desktop custom widgets.
DTSTART:{d0}T130000
DTEND:{d0}T140000
LOCATION:Cafeteria
END:VEVENT
BEGIN:VEVENT
UID:sample-03-{d1}
SUMMARY:Hyprland Configuration Sync
DESCRIPTION:Review keybindings and monitor layouts.
DTSTART:{d1}T153000
DTEND:{d1}T163000
LOCATION:Online
END:VEVENT
BEGIN:VEVENT
UID:sample-04-{d2}
SUMMARY:Product Roadmap Planning
DESCRIPTION:Bi-weekly sync on milestones and goals.
DTSTART:{d2}T110000
DTEND:{d2}T123000
LOCATION:Conference Room B
END:VEVENT
BEGIN:VEVENT
UID:sample-05-{d3}
SUMMARY:Open Source Release & Tagging
DESCRIPTION:Publish v1.0.0 release notes and artifacts.
DTSTART;VALUE=DATE:{d3}
DTEND;VALUE=DATE:{d3}
LOCATION:GitHub
END:VEVENT
END:VCALENDAR
"""
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(ics_data)

    add_source("Sample Calendar", "file", str(sample_file), "#88c0d0")
    return {"status": "ok", "path": str(sample_file)}

def pick_file_zenity():
    """Launch graphical file chooser to select .ics file."""
    try:
        if shutil.which("zenity"):
            res = subprocess.run(
                ["zenity", "--file-selection", "--file-filter=iCalendar files (*.ics) | *.ics", "--title=Select iCalendar (.ics) File"],
                capture_output=True,
                text=True,
                check=False
            )
            selected = res.stdout.strip()
            if selected and os.path.exists(selected):
                return {"status": "ok", "path": selected}
            return {"status": "cancel"}
        elif shutil.which("kdialog"):
            res = subprocess.run(
                ["kdialog", "--getopenfilename", os.path.expanduser("~"), "*.ics | iCalendar files (*.ics)"],
                capture_output=True,
                text=True,
                check=False
            )
            selected = res.stdout.strip()
            if selected and os.path.exists(selected):
                return {"status": "ok", "path": selected}
            return {"status": "cancel"}
        elif shutil.which("yad"):
            res = subprocess.run(
                ["yad", "--file", "--file-filter=iCalendar files (*.ics) | *.ics", "--title=Select iCalendar (.ics) File"],
                capture_output=True,
                text=True,
                check=False
            )
            selected = res.stdout.strip()
            if selected and os.path.exists(selected):
                return {"status": "ok", "path": selected}
            return {"status": "cancel"}
        else:
            return {"status": "error", "message": "No file chooser installed (zenity, kdialog, or yad)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import time

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "query":
        print(json.dumps(query_events()))
    elif cmd == "sync":
        fetch_and_sync_all()
        print(json.dumps(query_events()))
    elif cmd == "list-sources":
        cfg = load_sources()
        print(json.dumps(cfg))
    elif cmd == "add-file":
        # args: name, path, color
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        path = sys.argv[3] if len(sys.argv) > 3 else ""
        color = sys.argv[4] if len(sys.argv) > 4 else "#88c0d0"
        print(json.dumps(add_source(name, "file", path, color)))
    elif cmd == "add-url":
        # args: name, url, color
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        url = sys.argv[3] if len(sys.argv) > 3 else ""
        color = sys.argv[4] if len(sys.argv) > 4 else "#a3be8c"
        print(json.dumps(add_source(name, "url", url, color)))
    elif cmd == "remove-source":
        src_id = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(remove_source(src_id)))
    elif cmd == "toggle-source":
        src_id = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(toggle_source(src_id)))
    elif cmd == "pick-file":
        print(json.dumps(pick_file_zenity()))
    elif cmd == "init-sample":
        print(json.dumps(import_sample_ics()))
    else:
        print(json.dumps({"error": f"Unknown command {cmd}"}))
