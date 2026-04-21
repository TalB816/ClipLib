from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication


class ClipboardMonitor(QObject):
    changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last = ""
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._check)

    def start(self):
        self._timer.start()

    def _check(self):
        text = QApplication.clipboard().text()
        if text and text != self._last:
            self._last = text
            self.changed.emit(text)
