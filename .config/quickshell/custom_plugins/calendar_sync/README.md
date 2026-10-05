# Calendar & Event Sync Plugin (`calendar_sync`)

Custom calendar plugin for **Quickshell** that imports iCalendar (`.ics`) files from URLs (Google Calendar, Nextcloud, Apple iCloud, Outlook, CalDAV exports) or from local disk files.

---

## 🌟 Features

- **Import from URL & Disk**: Add public/secret calendar URLs (`webcal://`, `https://...`) or choose local `.ics` files using Zenity file chooser.
- **Top Bar Module**:
  - Automatically overrides the built-in clock module (`"clock"`) in its current position.
  - Displays a green event dot when there are events scheduled for today.
  - Left-click toggles 12-hour Time vs Date view.
  - Right-click opens terminal calendar (`cal -3`).
- **Interactive Hover Popover**:
  - **Live Digital Clock & Date**: Clean header with current time and day.
  - **Month Calendar Grid**: Interactive grid with previous/next month navigation, "Today" return shortcut, and dots on days with scheduled events.
  - **Events Panel**:
    - **Today Tab**: Lists all events scheduled for today with their times and locations.
    - **Upcoming Tab**: Lists future events within the next 30 days, showing relative time offsets (e.g. *Tomorrow*, *in 3d*).
  - **Import / Feeds Management Modal**:
    - Easily add calendar feeds by URL or pick local files.
    - Assign custom color tags for each feed.
    - Enable / disable / delete calendar feeds.
    - Trigger immediate "Sync All" with 1-click.
  - Automatic background synchronization every 15 minutes.

---

## 📁 Directory Structure

```text
~/.config/quickshell/custom_plugins/calendar_sync/
├── manifest.json              # Plugin declaration, clock module override
├── qmldir                     # QML module export
├── CalendarSyncService.qml    # Singleton background service managing events & sources
├── CalendarSyncModule.qml     # Status bar capsule with live time, date & event dot
├── CalendarHoverCard.qml      # Hover popup window with month view & event list
├── CalendarManageModal.qml    # Feed management modal for URL / disk import
├── CalendarSyncWindow.qml     # Plugin window wrapper
└── calendar_helper.py         # Python 3 helper parsing standard .ics files & recurring events
```

---

## 🚀 CLI Usage

You can also interact with the helper script via terminal:

```bash
# Query organized events (JSON)
python3 ~/.config/quickshell/custom_plugins/calendar_sync/calendar_helper.py query

# Synchronize all sources now
python3 ~/.config/quickshell/custom_plugins/calendar_sync/calendar_helper.py sync

# Add a calendar URL
python3 ~/.config/quickshell/custom_plugins/calendar_sync/calendar_helper.py add-url "Work Calendar" "https://example.com/calendar.ics" "#88c0d0"

# Add a local calendar file
python3 ~/.config/quickshell/custom_plugins/calendar_sync/calendar_helper.py add-file "Holidays" "/path/to/holidays.ics" "#a3be8c"

# List configured sources
python3 ~/.config/quickshell/custom_plugins/calendar_sync/calendar_helper.py list-sources
```
