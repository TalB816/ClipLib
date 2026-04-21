import os
import sys
import subprocess

_PYTHON = sys.executable
_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")

# ── macOS ─────────────────────────────────────────────────────────────────────
_PLIST_LABEL = "com.cliplib.app"
_PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{_PLIST_LABEL}.plist")

# ── Windows ───────────────────────────────────────────────────────────────────
_WIN_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_WIN_REG_NAME = "ClipLib"


def is_enabled() -> bool:
    if sys.platform == "darwin":
        return os.path.exists(_PLIST_PATH)
    elif sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_REG_KEY) as key:
                winreg.QueryValueEx(key, _WIN_REG_NAME)
            return True
        except (ImportError, OSError):
            return False
    return False


def enable():
    if sys.platform == "darwin":
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{_PYTHON}</string>
        <string>{_SCRIPT}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
        os.makedirs(os.path.dirname(_PLIST_PATH), exist_ok=True)
        with open(_PLIST_PATH, "w") as f:
            f.write(plist)
        os.chmod(_PLIST_PATH, 0o644)

    elif sys.platform == "win32":
        try:
            import winreg
            cmd = f'"{_PYTHON}" "{_SCRIPT}"'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_REG_KEY,
                                access=winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, _WIN_REG_NAME, 0, winreg.REG_SZ, cmd)
        except (ImportError, OSError):
            pass


def disable():
    if sys.platform == "darwin":
        try:
            subprocess.run(["launchctl", "unload", _PLIST_PATH],
                           capture_output=True, timeout=5)
        except Exception:
            pass
        try:
            os.remove(_PLIST_PATH)
        except OSError:
            pass

    elif sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_REG_KEY,
                                access=winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, _WIN_REG_NAME)
        except (ImportError, OSError):
            pass
