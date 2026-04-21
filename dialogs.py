from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt


DIALOG_STYLE = """
QDialog {
    background: #2b2b2b;
    color: #e0e0e0;
}
QLabel {
    color: #b0b0b0;
    font-size: 12px;
}
QLineEdit, QTextEdit, QComboBox {
    background: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    color: #e0e0e0;
    padding: 4px 8px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #888;
}
QPushButton {
    background: #4a4a4a;
    border: 1px solid #666;
    border-radius: 4px;
    color: #e0e0e0;
    padding: 5px 16px;
    font-size: 13px;
}
QPushButton:hover { background: #5a5a5a; }
QPushButton#primary {
    background: #2d6a9f;
    border-color: #2d6a9f;
}
QPushButton#primary:hover { background: #3a7abf; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #3c3c3c;
    color: #e0e0e0;
    selection-background-color: #2d6a9f;
}
"""


class CategoryDialog(QDialog):
    def __init__(self, parent=None, name=""):
        super().__init__(parent)
        self.setWindowTitle("Category")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(300)
        self.setWindowFlags(Qt.WindowType.Dialog)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Category name"))
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("e.g. SQL Queries")
        layout.addWidget(self.name_input)

        buttons = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Save")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addLayout(buttons)

    @property
    def name(self):
        return self.name_input.text().strip()


class ItemDialog(QDialog):
    def __init__(self, parent=None, categories: list = None, content="", cat_id=""):
        super().__init__(parent)
        self.setWindowTitle("Add Snippet")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(440)
        self.setMinimumHeight(280)
        self.setWindowFlags(Qt.WindowType.Dialog)

        self._categories = categories or []

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Category"))
        self.cat_combo = QComboBox()
        for cat in self._categories:
            self.cat_combo.addItem(cat["name"], cat["id"])
        if cat_id:
            idx = next((i for i, c in enumerate(self._categories) if c["id"] == cat_id), 0)
            self.cat_combo.setCurrentIndex(idx)
        layout.addWidget(self.cat_combo)

        layout.addWidget(QLabel("Snippet"))
        self.content_input = QTextEdit()
        self.content_input.setPlainText(content)
        self.content_input.setPlaceholderText("Paste your query, text, or value here...")
        layout.addWidget(self.content_input)

        buttons = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Save")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addLayout(buttons)

    @property
    def content(self):
        return self.content_input.toPlainText().strip()

    @property
    def cat_id(self):
        return self.cat_combo.currentData()
