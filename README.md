# ClipLib

A lightweight menu bar app for macOS and Windows that combines a personal snippet library with clipboard history. Lives in your menu bar — no Dock icon, no clutter.

## Features

### Snippet Library
- Organize snippets into custom categories (e.g. SQL Queries, Important Numbers, Terminal Commands)
- Click any snippet to copy it instantly, or double-click / press Enter
- Search across all snippets and categories in real time
- Collapsible categories to keep things tidy
- Preview pane shows full content + character/line count before copying
- Drag and drop to reorder snippets or move them between categories
- Duplicate snippets with one click
- Recently Used section shows your most-copied snippets at the top
- Import/export your library as JSON for backup or sharing

### Clipboard History
- Automatically tracks everything you copy
- Timestamped entries so you know when something was copied
- Pin items to keep them at the top
- Save any history item directly to your snippet library
- Configurable max history size (or unlimited)
- Clear history by date

### Settings
- Global hotkey to open ClipLib from anywhere (default: ⌘⇧L on macOS, Ctrl+Shift+L on Windows)
- Launch at login toggle
- Configurable clipboard history limit
- Clear history before a specific date

## Requirements

- Python 3.9+
- PyQt6
- pynput
- pyobjc (macOS only)

Install dependencies:

```bash
pip install PyQt6 pynput pyobjc
```

> On Windows, omit `pyobjc`.

## Running the App

```bash
# macOS — run as background process
nohup python3 -u ~/ClipLib/main.py &

# Windows
pythonw main.py
```

To stop the app:

```bash
pkill -f "Python.*main.py"
```

## Data Storage

All data is stored locally as JSON files in the app directory:

- `library.json` — your snippet library
- `history.json` — clipboard history
- `settings.json` — app settings

These files are excluded from version control (`.gitignore`).

## Platform Support

| Feature | macOS | Windows |
|---|---|---|
| Menu bar / system tray | ✅ | ✅ |
| Global hotkey | ✅ | ✅ |
| Launch at login | ✅ (LaunchAgent) | ✅ (Registry) |
| Hide from Dock/taskbar | ✅ | ✅ |
