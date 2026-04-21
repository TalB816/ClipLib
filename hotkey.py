import sys
from PyQt6.QtCore import QObject, pyqtSignal

# Platform-appropriate hotkey presets: (display label, pynput hotkey string)
if sys.platform == "darwin":
    HOTKEY_OPTIONS = [
        ("None",      ""),
        ("⌘⇧L",      "<cmd>+<shift>+l"),
        ("⌘⇧Space",  "<cmd>+<shift>+<space>"),
        ("⌘⌥C",      "<cmd>+<alt>+c"),
        ("⌘⌥V",      "<cmd>+<alt>+v"),
        ("⌘⌥L",      "<cmd>+<alt>+l"),
    ]
else:  # Windows / Linux
    HOTKEY_OPTIONS = [
        ("None",          ""),
        ("Ctrl+Shift+L",  "<ctrl>+<shift>+l"),
        ("Ctrl+Shift+Space", "<ctrl>+<shift>+<space>"),
        ("Ctrl+Alt+C",    "<ctrl>+<alt>+c"),
        ("Ctrl+Alt+V",    "<ctrl>+<alt>+v"),
        ("Ctrl+Alt+L",    "<ctrl>+<alt>+l"),
    ]


class GlobalHotkey(QObject):
    activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listener = None

    def start(self, hotkey_str: str):
        self.stop()
        if not hotkey_str:
            return
        try:
            from pynput import keyboard
            self._listener = keyboard.GlobalHotKeys(
                {hotkey_str: self._on_activate}
            )
            self._listener.start()
        except Exception:
            pass

    def stop(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _on_activate(self):
        # Called from pynput thread — Qt queues the signal safely across threads
        self.activated.emit()
