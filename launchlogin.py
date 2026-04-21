import os
import sys
import subprocess

PLIST_LABEL = "com.cliplib.app"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_LABEL}.plist")
_PYTHON = sys.executable
_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")


def is_enabled() -> bool:
    return os.path.exists(PLIST_PATH)


def enable():
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
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
    os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)
    with open(PLIST_PATH, "w") as f:
        f.write(plist)
    os.chmod(PLIST_PATH, 0o644)


def disable():
    try:
        subprocess.run(["launchctl", "unload", PLIST_PATH],
                       capture_output=True, timeout=5)
    except Exception:
        pass
    try:
        os.remove(PLIST_PATH)
    except OSError:
        pass
