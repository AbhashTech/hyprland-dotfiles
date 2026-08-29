#!/usr/bin/env python3
"""
=============================================================================
 Catppuccin Mocha Glassmorphic Notification Center for Waybar & Hyprland
 Interfaces with Mako daemon (10s auto-dismiss + history + interactive Wofi menu)
=============================================================================
"""

import html
import json
import os
import re
import subprocess
import sys
import time

DISMISSED_CACHE = os.path.expanduser("~/.cache/mako_dismissed.json")


def run_cmd(cmd, check=False):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""


def run_dmenu(prompt, options, width=44, lines=10):
    import shutil
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", f" {prompt}: ", "--width", str(width), "--lines", str(lines)]
    else:
        cmd = [
            "wofi", "--dmenu",
            "--prompt", prompt,
            "--width", "540",
            "--height", "450",
            "--cache-file", "/dev/null",
            "--hide-scroll",
            "--allow-markup",
            "--insensitive"
        ]
    try:
        proc = subprocess.run(cmd, input="\n".join(options), text=True, capture_output=True)
        return proc.stdout.strip()
    except Exception:
        return ""


def get_dismissed_ids():
    """Load list of individually dismissed notification IDs."""
    if not os.path.exists(DISMISSED_CACHE):
        return set()
    try:
        with open(DISMISSED_CACHE, "r") as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def add_dismissed_id(n_id):
    """Add notification ID to dismissed cache."""
    ids = get_dismissed_ids()
    ids.add(n_id)
    try:
        os.makedirs(os.path.dirname(DISMISSED_CACHE), exist_ok=True)
        with open(DISMISSED_CACHE, "w") as f:
            json.dump(list(ids), f)
    except Exception:
        pass


def clear_dismissed_cache():
    """Reset the dismissed IDs cache."""
    try:
        if os.path.exists(DISMISSED_CACHE):
            os.remove(DISMISSED_CACHE)
    except Exception:
        pass


def get_notifications():
    """Retrieve both active and historical notifications from mako, excluding dismissed ones."""
    active_raw = run_cmd(["makoctl", "list", "-j"])
    history_raw = run_cmd(["makoctl", "history", "-j"])

    active = []
    history = []

    try:
        if active_raw:
            active = json.loads(active_raw)
            if not isinstance(active, list):
                active = []
    except Exception:
        active = []

    try:
        if history_raw:
            history = json.loads(history_raw)
            if not isinstance(history, list):
                history = []
    except Exception:
        history = []

    dismissed = get_dismissed_ids()

    # Merge unique notifications by id (active first, then history)
    seen_ids = set()
    combined = []
    ignored_apps = {"VolumeControl", "BrightnessControl", "volume_control", "brightness_control"}

    for item in active + history:
        item_id = item.get("id")
        app_name = item.get("app_name", "")
        category = item.get("category", "")
        
        # Exclude transient OSD notifications
        if app_name in ignored_apps or category == "osd":
            continue

        if item_id is not None:
            if item_id in dismissed or item_id in seen_ids:
                continue
            seen_ids.add(item_id)
        combined.append(item)

    return combined


DND_STATE_FILE = os.path.expanduser("~/.cache/mako_dnd")


def is_dnd():
    """Check if Do Not Disturb mode is active."""
    mode_out = run_cmd(["makoctl", "mode"])
    mako_dnd = "dnd" in mode_out.splitlines()
    file_dnd = os.path.exists(DND_STATE_FILE)

    # Sync state if mako was restarted
    if file_dnd and not mako_dnd:
        run_cmd(["makoctl", "mode", "-a", "dnd"])
        return True
    elif not file_dnd and mako_dnd:
        return True
    return file_dnd or mako_dnd


def toggle_dnd():
    """Toggle Do Not Disturb mode and persist state."""
    currently_dnd = is_dnd()
    if currently_dnd:
        run_cmd(["makoctl", "mode", "-r", "dnd"])
        if os.path.exists(DND_STATE_FILE):
            try:
                os.remove(DND_STATE_FILE)
            except Exception:
                pass
    else:
        run_cmd(["makoctl", "mode", "-a", "dnd"])
        try:
            os.makedirs(os.path.dirname(DND_STATE_FILE), exist_ok=True)
            with open(DND_STATE_FILE, "w") as f:
                f.write("1")
        except Exception:
            pass

    # Notify waybar to update
    run_cmd(["pkill", "-RTMIN+10", "waybar"])


def clear_all():
    """Clear all notification history and active notifications without affecting DND mode."""
    dnd_active = is_dnd()

    # Dismiss all active without adding to history
    run_cmd(["makoctl", "dismiss", "-a", "-h"])
    clear_dismissed_cache()

    # Restart mako to completely wipe internal history buffer
    if run_cmd(["systemctl", "--user", "is-active", "mako"]) == "active":
        run_cmd(["systemctl", "--user", "restart", "mako"])
    else:
        run_cmd(["pkill", "-x", "mako"])
        subprocess.Popen(["mako"])

    time.sleep(0.15)

    # Re-apply DND mode if it was active
    if dnd_active:
        run_cmd(["makoctl", "mode", "-a", "dnd"])

    run_cmd(["pkill", "-RTMIN+10", "waybar"])


def clean_markup(text):
    """Remove HTML tags and unescape entities to clean plain text."""
    if not text:
        return ""
    no_tags = re.sub(r'<[^>]*>', '', str(text))
    return html.unescape(no_tags).strip()


def waybar_status():
    """Output JSON format for Waybar custom module."""
    notifications = get_notifications()
    dnd = is_dnd()
    count = len(notifications)

    if dnd:
        icon = "󰂛"
        text = f"{icon} {count}" if count > 0 else f"{icon} DND"
        alt = "dnd"
        css_class = "dnd"
    elif count > 0:
        icon = "󱅫"
        text = f"{icon} {count}"
        alt = "notification"
        css_class = "has-notifications"
    else:
        icon = "󰂚"
        text = f"{icon}"
        alt = "none"
        css_class = "none"

    # Build tooltip with safe Pango markup
    tooltip_lines = []
    if dnd:
        tooltip_lines.append("<b>󰂛 Do Not Disturb: ON</b>")
    else:
        tooltip_lines.append(f"<b>󰂚 Notifications ({count})</b>")

    if count > 0:
        tooltip_lines.append("────────────────────────")
        for n in notifications[:5]:
            raw_app = clean_markup(n.get("app_name") or "System")
            raw_summary = clean_markup(n.get("summary") or "Notification")
            raw_body = clean_markup(n.get("body") or "")
            if len(raw_body) > 40:
                raw_body = raw_body[:37] + "..."
            
            app = html.escape(raw_app)
            summary = html.escape(raw_summary)
            body = html.escape(raw_body)
            
            snippet = f"<b>{app}</b>: {summary}"
            if body:
                snippet += f" — <i>{body}</i>"
            tooltip_lines.append(f"• {snippet}")

        if count > 5:
            tooltip_lines.append(f"<i>... and {count - 5} more</i>")
    else:
        tooltip_lines.append("<i>No recent notifications</i>")

    tooltip_lines.append("────────────────────────")
    tooltip_lines.append("<b>Left Click:</b> Open Notification Center")
    tooltip_lines.append("<b>Right Click:</b> Toggle Do Not Disturb")
    tooltip_lines.append("<b>Middle Click:</b> Clear All History")

    output = {
        "text": text,
        "alt": alt,
        "tooltip": "\n".join(tooltip_lines),
        "class": css_class
    }
    print(json.dumps(output))


def open_menu():
    """Display interactive notification center in menu."""
    notifications = get_notifications()
    dnd = is_dnd()
    count = len(notifications)

    dnd_label = "󰂛  Do Not Disturb: ON (Click to Disable)" if dnd else "󰂚  Do Not Disturb: OFF (Click to Enable)"

    options = [
        "─── 󰂚 NOTIFICATION CONTROLS ───",
        dnd_label,
        "󰎟  Clear All Notification History",
        "󰒲  Restore Last Expired Notification",
        "󰐥  Send Test Notification",
    ]

    if count > 0:
        options.append(f"─── 󱅫 NOTIFICATIONS ({count}) ───")
        for i, n in enumerate(notifications):
            app = clean_markup(n.get("app_name") or "System")
            summary = clean_markup(n.get("summary") or "Notification")
            body = clean_markup(n.get("body") or "")
            body_one_line = " ".join(body.split())
            if len(body_one_line) > 50:
                body_one_line = body_one_line[:47] + "..."
            
            urgency = n.get("urgency", "normal")
            urgency_icon = "󰵚" if urgency == "critical" else "󰂚"

            line = f"{urgency_icon} [{i+1}] {app}: {summary}"
            if body_one_line:
                line += f"  ({body_one_line})"
            options.append(line)
    else:
        options.append("─── NOTIFICATIONS (0) ───")
        options.append("󰄴  No notifications in history")

    chosen = run_dmenu("󰂚 Notifications", options, width=42, lines=10)
    if not chosen:
        return

    if "Do Not Disturb" in chosen:
        toggle_dnd()
    elif "Clear All" in chosen:
        clear_all()
    elif "Restore Last" in chosen:
        run_cmd(["makoctl", "restore"])
        run_cmd(["pkill", "-RTMIN+10", "waybar"])
    elif "Send Test" in chosen:
        run_cmd(["notify-send", "-a", "Demo App", "✨ Test Notification", "This notification will dismiss in 10 seconds!"])
        run_cmd(["pkill", "-RTMIN+10", "waybar"])
    elif "[" in chosen and "]" in chosen:
        match = re.search(r'\[(\d+)\]', chosen)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(notifications):
                show_notification_detail(notifications[idx])


def show_notification_detail(n):
    """Show details and action choices for a specific notification."""
    app = clean_markup(n.get("app_name") or "System")
    summary = clean_markup(n.get("summary") or "Notification")
    body = clean_markup(n.get("body") or "No message body")
    n_id = n.get("id")
    actions = n.get("actions") or {}

    options = [
        "─── NOTIFICATION DETAILS ───",
        f"App: {app}",
        f"Title: {summary}",
        f"Message: {body}",
        "─── ACTIONS ───",
    ]

    # Action items from notification
    for act_key, act_label in actions.items():
        options.append(f"󰐥  Action: {clean_markup(act_label)} [{act_key}]")

    options.append("󰒲  Pop Up This Notification on Screen")
    options.append("󰅖  Dismiss / Clear from History")
    options.append("󰌍  « Back to Notification List")

    chosen = run_dmenu(f"󰂚 {app}", options, width=42, lines=8)
    if not chosen or "Back to Notification List" in chosen:
        open_menu()
        return


    if "Action:" in chosen:
        match = re.search(r'\[(.*)\]$', chosen)
        if match and n_id is not None:
            act_key = match.group(1)
            run_cmd(["makoctl", "invoke", "-n", str(n_id), act_key])
    elif "Pop Up" in chosen:
        run_cmd(["notify-send", "-a", app, summary, body])
    elif "Dismiss" in chosen and n_id is not None:
        run_cmd(["makoctl", "dismiss", "-n", str(n_id), "-h"])
        add_dismissed_id(n_id)
        run_cmd(["pkill", "-RTMIN+10", "waybar"])
        open_menu()


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--status":
            waybar_status()
            return
        elif arg == "--toggle-dnd":
            toggle_dnd()
            return
        elif arg == "--clear":
            clear_all()
            return
        elif arg == "--restore":
            run_cmd(["makoctl", "restore"])
            run_cmd(["pkill", "-RTMIN+10", "waybar"])
            return

    open_menu()


if __name__ == "__main__":
    main()
