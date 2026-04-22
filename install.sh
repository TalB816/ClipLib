#!/bin/bash
# ClipLib installer for macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ClipLib Installer"
echo "  ================="
echo ""

# ── Check for Python 3 ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: Python 3 is not installed."
    echo ""
    echo "  Install it from https://www.python.org/downloads/"
    echo "  then re-run this script."
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Found Python $PYTHON_VERSION"

python3 -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" || {
    echo ""
    echo "  ERROR: Python 3.9 or higher is required (found $PYTHON_VERSION)."
    echo "  Install a newer version from https://www.python.org/downloads/"
    echo ""
    exit 1
}

# ── Install packages ──────────────────────────────────────────────────────────
echo "  Installing required packages..."
echo ""

python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "  All packages installed successfully."

# ── Accessibility permission reminder ────────────────────────────────────────
echo ""
echo "  NOTE: For the global hotkey to work, macOS requires Accessibility access."
echo "  If prompted, go to:"
echo "  System Settings → Privacy & Security → Accessibility"
echo "  and enable your Terminal (or Python)."

# ── Launch ────────────────────────────────────────────────────────────────────
echo ""
read -p "  Launch ClipLib now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    nohup python3 "$SCRIPT_DIR/main.py" &>/dev/null &
    echo ""
    echo "  ClipLib is running — look for the icon in your menu bar."
fi

echo ""
echo "  To launch ClipLib manually in the future, run:"
echo "    nohup python3 $SCRIPT_DIR/main.py &"
echo ""
