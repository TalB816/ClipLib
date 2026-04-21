import sys
import signal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from window import PopupWindow
from clipboard import ClipboardMonitor
from hotkey import GlobalHotkey, HOTKEY_OPTIONS
import data as data_module


def make_icon() -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#cccccc"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 6, 24, 22, 3, 3)
    p.setBrush(QColor("#888888"))
    p.drawRoundedRect(10, 2, 12, 7, 2, 2)
    p.setPen(QPen(QColor("#555555"), 1.5))
    p.drawLine(8, 14, 24, 14)
    p.drawLine(8, 19, 24, 19)
    p.drawLine(8, 24, 18, 24)
    p.end()
    return QIcon(pm)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    popup = PopupWindow()

    # Clipboard monitor
    monitor = ClipboardMonitor()
    monitor.changed.connect(popup.add_to_history)
    monitor.start()

    # Global hotkey
    hotkey = GlobalHotkey()
    hotkey.activated.connect(lambda: _toggle(tray, popup))

    settings = data_module.load_settings()
    hk_str = settings.get("hotkey", "<cmd>+<shift>+l")
    hotkey.start(hk_str)

    # Reconnect hotkey when user changes it in Settings
    def _on_hotkey_setting_changed(new_str: str):
        hotkey.start(new_str)

    # Wire the setting change signal — we patch it onto the popup instance
    from PyQt6.QtCore import pyqtSignal
    popup._hotkey_signal_wired = True
    # Connect via settings combo directly
    popup._hotkey_combo.currentIndexChanged.connect(
        lambda idx: hotkey.start(HOTKEY_OPTIONS[idx][1])
    )

    # Tray icon
    tray = QSystemTrayIcon(make_icon(), app)
    tray.setToolTip("ClipLib  ·  " + (
        next((l for l, v in HOTKEY_OPTIONS if v == hk_str), "") or "no hotkey"
    ))

    quit_menu = QMenu()
    quit_menu.setStyleSheet("""
        QMenu { background: #2c2c2c; color: #e0e0e0; border: 1px solid #555; padding: 4px; }
        QMenu::item { padding: 6px 20px; }
        QMenu::item:selected { background: #2d6a9f; }
    """)
    quit_menu.addAction("Quit ClipLib", app.quit)

    def _on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            _toggle(tray, popup)
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            quit_menu.popup(tray.geometry().bottomLeft())

    tray.activated.connect(_on_tray_activated)
    tray.show()

    sys.exit(app.exec())


def _toggle(tray: QSystemTrayIcon, popup: PopupWindow):
    if popup.isVisible():
        popup.hide()
    else:
        popup.show_near_tray(tray.geometry())


if __name__ == "__main__":
    main()
