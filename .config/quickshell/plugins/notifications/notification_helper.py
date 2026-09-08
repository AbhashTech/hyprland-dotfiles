#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import html
import re
import time
from pathlib import Path

DISMISSED_FILE = Path.home() / ".cache" / "quickshell_dismissed_notifs.json"

def get_dismissed_ids():
    try:
        if DISMISSED_FILE.exists():
            data = json.loads(DISMISSED_FILE.read_text())
            if isinstance(data, list):
                return set(int(x) for x in data if str(x).isdigit())
    except Exception:
        pass
    return set()

def save_dismissed_ids(ids_set):
    try:
        DISMISSED_FILE.parent.mkdir(parents=True, exist_ok=True)
        DISMISSED_FILE.write_text(json.dumps(list(ids_set)))
    except Exception:
        pass

def restart_mako():
    """Restart mako daemon in background to completely flush mako internal buffer."""
    try:
        subprocess.run(["pkill", "-x", "mako"], timeout=2)
        time.sleep(0.15)
        subprocess.Popen(["mako"], start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def clean_text(t, max_len=500):
    if not t:
        return ""
    clean = re.sub(r'<[^>]+>', '', str(t))
    clean = html.unescape(clean).strip()
    if len(clean) > max_len:
        clean = clean[:max_len] + "..."
    return clean

def get_notifications():
    # 1. Fetch live notifications
    try:
        p_live = subprocess.run(["makoctl", "list", "-j"], capture_output=True, text=True, timeout=3)
        live_data = json.loads(p_live.stdout) if p_live.stdout.strip() else []
    except Exception:
        live_data = []

    # 2. Fetch history notifications
    try:
        p_hist = subprocess.run(["makoctl", "history", "-j"], capture_output=True, text=True, timeout=3)
        hist_data = json.loads(p_hist.stdout) if p_hist.stdout.strip() else []
    except Exception:
        hist_data = []

    # Check DND mode
    dnd = False
    try:
        p_mode = subprocess.run(["makoctl", "mode"], capture_output=True, text=True, timeout=2)
        dnd = "dnd" in p_mode.stdout.splitlines()
    except Exception:
        pass

    dismissed = get_dismissed_ids()
    seen_ids = set()
    notifs = []

    # Process live first
    for item in live_data:
        try:
            nid = int(item.get("id"))
        except (ValueError, TypeError):
            continue
        if nid in dismissed:
            continue
        seen_ids.add(nid)
        app = str(item.get("app_name") or "System")
        summary = clean_text(item.get("summary"), max_len=150)
        body = clean_text(item.get("body"), max_len=400)
        urgency = str(item.get("urgency") or "normal")
        actions = item.get("actions") or {}
        notifs.append({
            "id": nid,
            "appName": app,
            "summary": summary,
            "body": body,
            "urgency": urgency,
            "isLive": True,
            "hasActions": bool(actions)
        })

    # Process history (up to max history capacity: 500 items)
    for item in hist_data[:500]:
        try:
            nid = int(item.get("id"))
        except (ValueError, TypeError):
            continue
        if nid in seen_ids or nid in dismissed:
            continue
        seen_ids.add(nid)
        app = str(item.get("app_name") or "System")
        summary = clean_text(item.get("summary"), max_len=150)
        body = clean_text(item.get("body"), max_len=400)
        urgency = str(item.get("urgency") or "normal")
        actions = item.get("actions") or {}
        notifs.append({
            "id": nid,
            "appName": app,
            "summary": summary,
            "body": body,
            "urgency": urgency,
            "isLive": False,
            "hasActions": bool(actions)
        })

    result = {
        "notifications": notifs,
        "unreadCount": len(notifs),
        "dnd": dnd
    }
    print(json.dumps(result))

def dismiss_single(nid):
    try:
        nid_int = int(nid)
        dismissed = get_dismissed_ids()
        dismissed.add(nid_int)
        save_dismissed_ids(dismissed)
        subprocess.run(["makoctl", "dismiss", "-n", str(nid)], timeout=2)
    except Exception:
        pass

def invoke_action(nid):
    try:
        subprocess.run(["makoctl", "invoke", "-n", str(nid)], timeout=2)
    except Exception:
        pass

def dismiss_all():
    try:
        # Dismiss all active visible
        subprocess.run(["makoctl", "dismiss", "-a"], timeout=2)
    except Exception:
        pass

    try:
        p_live = subprocess.run(["makoctl", "list", "-j"], capture_output=True, text=True, timeout=2)
        p_hist = subprocess.run(["makoctl", "history", "-j"], capture_output=True, text=True, timeout=2)
        live = json.loads(p_live.stdout) if p_live.stdout.strip() else []
        hist = json.loads(p_hist.stdout) if p_hist.stdout.strip() else []
        all_ids = set()
        for x in live + hist:
            try:
                all_ids.add(int(x.get("id")))
            except (ValueError, TypeError):
                pass
        dismissed = get_dismissed_ids()
        dismissed.update(all_ids)
        save_dismissed_ids(dismissed)
    except Exception:
        pass

    # Restart mako to wipe history buffer completely
    restart_mako()

def toggle_dnd():
    try:
        subprocess.run(["makoctl", "mode", "-t", "dnd"], timeout=2)
    except Exception:
        pass

def get_status():
    count = 0
    dnd = False
    try:
        p_live = subprocess.run(["makoctl", "list", "-j"], capture_output=True, text=True, timeout=2)
        p_hist = subprocess.run(["makoctl", "history", "-j"], capture_output=True, text=True, timeout=2)
        live = json.loads(p_live.stdout) if p_live.stdout.strip() else []
        hist = json.loads(p_hist.stdout) if p_hist.stdout.strip() else []
        dismissed = get_dismissed_ids()
        all_ids = set()
        for x in live + hist:
            try:
                i = int(x.get("id"))
                if i not in dismissed:
                    all_ids.add(i)
            except (ValueError, TypeError):
                pass
        count = len(all_ids)
    except Exception:
        count = 0

    try:
        p_mode = subprocess.run(["makoctl", "mode"], capture_output=True, text=True, timeout=2)
        dnd = "dnd" in p_mode.stdout.splitlines()
    except Exception:
        dnd = False

    print(json.dumps({"count": count, "dnd": dnd}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        get_notifications()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        get_notifications()
    elif cmd == "status":
        get_status()
    elif cmd == "count":
        try:
            p_live = subprocess.run(["makoctl", "list", "-j"], capture_output=True, text=True, timeout=2)
            p_hist = subprocess.run(["makoctl", "history", "-j"], capture_output=True, text=True, timeout=2)
            live = json.loads(p_live.stdout) if p_live.stdout.strip() else []
            hist = json.loads(p_hist.stdout) if p_hist.stdout.strip() else []
            dismissed = get_dismissed_ids()
            all_ids = set()
            for x in live + hist:
                try:
                    i = int(x.get("id"))
                    if i not in dismissed:
                        all_ids.add(i)
                except (ValueError, TypeError):
                    pass
            print(len(all_ids))
        except Exception:
            print(0)
    elif cmd == "dismiss":
        nid = sys.argv[2] if len(sys.argv) > 2 else ""
        dismiss_single(nid)
    elif cmd == "invoke":
        nid = sys.argv[2] if len(sys.argv) > 2 else ""
        invoke_action(nid)
    elif cmd == "dismiss-all":
        dismiss_all()
    elif cmd == "toggle-dnd":
        toggle_dnd()
