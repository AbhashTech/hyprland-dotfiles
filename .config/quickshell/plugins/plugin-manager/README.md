# Quickshell Plugin Manager

A native, interactive GUI & CLI Plugin Manager for **Quickshell** custom plugins on Wayland / Hyprland.

---

## 🌟 Features

- **Dynamic Plugin Discovery**: Automatically lists all custom plugins in `~/.config/quickshell/custom_plugins/` as well as built-in core Quickshell modules.
- **Discover / Community Store**: One-click installation for curated community widgets (Pomodoro Timer, Live Weather Forecast, MPRIS Media Visualizer, System Resource Monitor, GitHub Tracker).
- **Toggle Enable / Disable**: Instant switch updates `manifest.json` and hot-reloads status bar widgets and popup windows.
- **Live Position Switcher**: Shift status bar capsules between `Left`, `Center`, and `Right` groups on the fly with single-click position chips.
- **Manifest & Metadata Editor**: In-app modal to edit plugin display names, authors, descriptions, and positions.
- **Git Sync & Version Control**:
  - Direct `Git Pull` button to fetch upstream changes.
  - In-app `Git Log` commit viewer to inspect author, date, and commit history.
- **Dependency & Health Checker**: Validates system binaries specified in `dependencies` (e.g. `playerctl`, `curl`, `sensors`, `notify-send`) and alerts when dependencies are missing.
- **Export & Backup**: One-click archive export to `.tar.gz` bundles stored in `~/.cache/quickshell_backups/`, plus `.tar.gz` / `.zip` archive import.
- **Add & Scaffold New Plugins**:
  - **Template Scaffolding**: Generate full boilerplate with topbar widget (`Module.qml`), modal window (`Window.qml` + `Menu.qml`), background service (`Service.qml`), manifest, and `README.md`.
  - **Git Clone**: Clone and register any Git repository directly into your Quickshell plugins directory.
- **Delete Plugins**: Safely remove unwanted custom plugins with confirmation safeguards.
- **Real-Time Logs & Diagnostics**: Live console trace drawer to inspect subprocess execution.
- **Application Menu & Keybinding Launch**: Instant popup modal window accessible via application launcher (`SUPER + R` / Fuzzel) or `SUPER + ALT + M`.

---

## 📁 Repository Structure

```text
~/.config/quickshell/plugins/plugin-manager/
├── manifest.json              # Plugin specification & entrypoints
├── qmldir                     # QML module exports
├── PluginManagerWindow.qml    # Glassmorphic overlay popup window
├── PluginManagerMenu.qml      # Multi-tab interactive UI card
├── PluginManagerService.qml   # Backend IPC service singleton
├── plugin_helper.py           # CLI & Python automation engine
├── README.md                  # Documentation
└── .gitignore                 # Untracked build artifacts
```

---

## ⌨️ Keybindings & CLI Usage

### Toggle via Shell Script / Hyprland
```bash
bash ~/.config/quickshell/scripts/toggle_plugin.sh plugin_manager
```

In `~/.config/hypr/modules/keybinds.lua`:
```lua
hl.bind("SUPER + ALT + M", hl.dsp.exec_cmd("bash " .. os.getenv("HOME") .. "/.config/quickshell/scripts/toggle_plugin.sh plugin_manager"))
```

### CLI Commands (`plugin_helper.py`)

- **List all plugins & metadata**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py list
  ```

- **Get Discover / Store Catalog**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py catalog
  ```

- **Enable or disable a plugin**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py toggle <plugin-id> true
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py toggle <plugin-id> false
  ```

- **Update Manifest properties (e.g. position)**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py update-manifest <plugin-id> '{"position":"left"}'
  ```

- **Git Pull remote updates**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py git-pull <plugin-id>
  ```

- **View Git commit history**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py git-log <plugin-id>
  ```

- **Export plugin to .tar.gz bundle**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py export <plugin-id>
  ```

- **Import plugin from archive**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py import /path/to/plugin.tar.gz
  ```

- **Scaffold a new plugin**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py create '{"id":"pomodoro","name":"Pomodoro Timer","author":"Kunal Gautam","position":"center","hasWidget":true,"hasWindow":true,"hasService":false,"initGit":true}'
  ```

- **Install from Git**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py install-git https://github.com/example/my-quickshell-widget.git
  ```

- **Delete a plugin**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py delete <plugin-id>
  ```

- **Reload Quickshell**:
  ```bash
  python3 ~/.config/quickshell/plugins/plugin-manager/plugin_helper.py reload
  ```
