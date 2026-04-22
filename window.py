import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QListWidget,
    QPushButton, QLabel, QApplication, QAbstractItemView,
    QMenu, QComboBox, QDateEdit, QGroupBox, QSplitter,
    QTextEdit, QCheckBox, QFileDialog, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import json
import data as data_module
from dialogs import CategoryDialog, ItemDialog
import launchlogin
from hotkey import HOTKEY_OPTIONS

STYLE = """
QWidget#popup {
    background: #1e1e1e;
    border: 1px solid #444;
    border-radius: 10px;
}
QLineEdit#search {
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 6px;
    color: #e0e0e0;
    padding: 6px 10px;
    font-size: 14px;
}
QLineEdit#search:focus { border-color: #666; }
QTabWidget::pane { border: none; }
QTabBar::tab {
    background: transparent;
    color: #888;
    padding: 6px 14px;
    font-size: 13px;
    border: none;
}
QTabBar::tab:selected {
    color: #e0e0e0;
    border-bottom: 2px solid #2d6a9f;
}
QTreeWidget, QListWidget {
    background: transparent;
    border: none;
    color: #e0e0e0;
    font-size: 13px;
    outline: none;
}
QTreeWidget::item, QListWidget::item {
    padding: 5px 4px;
    border-radius: 4px;
}
QTreeWidget::item:hover, QListWidget::item:hover { background: #2a2a2a; }
QTreeWidget::item:selected, QListWidget::item:selected {
    background: #2d6a9f;
    color: #fff;
}
QTreeWidget::branch { background: transparent; image: none; }
QTreeWidget { indentation: 16; }
QTextEdit#preview {
    background: #252525;
    border: 1px solid #333;
    border-radius: 5px;
    color: #ccc;
    font-size: 12px;
    padding: 4px;
}
QPushButton#action {
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 5px;
    color: #ccc;
    padding: 4px 10px;
    font-size: 12px;
}
QPushButton#action:hover { background: #3a3a3a; color: #fff; }
QPushButton#danger {
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 5px;
    color: #e06c6c;
    padding: 4px 10px;
    font-size: 12px;
}
QPushButton#danger:hover { background: #3a2020; }
QPushButton#section_header {
    background: transparent;
    border: none;
    color: #777;
    font-size: 11px;
    font-weight: bold;
    text-align: left;
    padding: 2px 0px;
}
QPushButton#section_header:hover { color: #aaa; }
QLabel#hint { color: #555; font-size: 11px; }
QLabel#stats { color: #555; font-size: 11px; }
QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    margin-top: 8px;
    color: #888;
    font-size: 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QComboBox {
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 5px;
    color: #e0e0e0;
    padding: 4px 8px;
    font-size: 13px;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #2c2c2c;
    color: #e0e0e0;
    selection-background-color: #2d6a9f;
    border: 1px solid #555;
}
QDateEdit {
    background: #2c2c2c;
    border: 1px solid #444;
    border-radius: 5px;
    color: #e0e0e0;
    padding: 4px 8px;
    font-size: 13px;
}
QDateEdit::drop-down { border: none; width: 20px; }
QCheckBox { color: #ccc; font-size: 13px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid #555;
    border-radius: 3px;
    background: #2c2c2c;
}
QCheckBox::indicator:checked { background: #2d6a9f; border-color: #2d6a9f; }
QSplitter::handle { background: #333; height: 1px; }
QScrollBar:vertical { width: 6px; background: transparent; }
QScrollBar::handle:vertical { background: #444; border-radius: 3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

MAX_HISTORY_OPTIONS = [
    ("50 items", 50),
    ("100 items", 100),
    ("200 items", 200),
    ("500 items", 500),
    ("1000 items", 1000),
    ("Unlimited", -1),
]


# ---------------------------------------------------------------------------
# Drag-drop aware tree
# ---------------------------------------------------------------------------

class LibraryTree(QTreeWidget):
    reordered = pyqtSignal()
    snippet_moved = pyqtSignal(object, str)       # (item_user_data, target_cat_id)
    snippet_reordered = pyqtSignal(object, str, int)  # (item_user_data, cat_id, target_index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._drag_source_data = None

    def startDrag(self, supported_actions):
        item = self.currentItem()
        self._drag_source_data = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        super().startDrag(supported_actions)

    def _cat_node_at(self, pos):
        """Return the category node under pos, whether hovering the cat itself or a child."""
        target = self.itemAt(pos)
        if target is None:
            return None
        d = target.data(0, Qt.ItemDataRole.UserRole)
        if d and d[0] == "cat":
            return target
        if d and d[0] == "item" and target.parent():
            return target.parent()
        return None

    def dragMoveEvent(self, event):
        if self._drag_source_data and self._drag_source_data[0] == "item":
            target = self.itemAt(event.position().toPoint())
            if target is None:
                event.ignore()
                return
            d = target.data(0, Qt.ItemDataRole.UserRole)
            if d and d[0] == "cat":
                self.setCurrentItem(target)
                event.accept()
            elif d and d[0] == "item":
                self.setCurrentItem(target)
                event.accept()
            else:
                event.ignore()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        source_data = self._drag_source_data
        self._drag_source_data = None

        if source_data and source_data[0] == "item":
            target = self.itemAt(event.position().toPoint())
            if target is not None:
                d = target.data(0, Qt.ItemDataRole.UserRole)
                if d and d[0] == "cat":
                    self.snippet_moved.emit(source_data, d[1])
                    event.accept()
                elif d and d[0] == "item":
                    parent = target.parent()
                    if parent:
                        target_index = parent.indexOfChild(target)
                        self.snippet_reordered.emit(source_data, d[1], target_index)
                        event.accept()
                    else:
                        event.ignore()
                else:
                    event.ignore()
            else:
                event.ignore()
            return  # never call super() for snippet drops

        # Category reorder — use Qt's mechanism, then restore lost UserRole
        if source_data and source_data[0] == "cat":
            target = self.itemAt(event.position().toPoint())
            if target is not None and target.parent() is not None:
                event.ignore()
                return

        super().dropEvent(event)

        # Python tuples don't survive QDataStream; find the orphaned item and fix it
        if source_data is not None:
            self._restore_user_data(source_data)

        self.reordered.emit()

    def _restore_user_data(self, data):
        if data[0] == "cat":
            for i in range(self.topLevelItemCount()):
                node = self.topLevelItem(i)
                if node.data(0, Qt.ItemDataRole.UserRole) is None:
                    node.setData(0, Qt.ItemDataRole.UserRole, data)
                    return
        elif data[0] == "item":
            for i in range(self.topLevelItemCount()):
                cat = self.topLevelItem(i)
                for j in range(cat.childCount()):
                    child = cat.child(j)
                    if child.data(0, Qt.ItemDataRole.UserRole) is None:
                        child.setData(0, Qt.ItemDataRole.UserRole, data)
                        return


# ---------------------------------------------------------------------------
# Main popup window
# ---------------------------------------------------------------------------

class PopupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("popup")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.setMinimumSize(380, 460)
        self.resize(380, 520)

        self._data = data_module.load()
        self._settings = data_module.load_settings()
        self._history: list[dict] = data_module.load_history()
        self._recent_items: list[dict] = []

        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("popup")
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._search = QLineEdit()
        self._search.setObjectName("search")
        self._search.setPlaceholderText("Search...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._build_library_tab(), "Library")
        self._tabs.addTab(self._build_history_tab(), "History")
        self._tabs.addTab(self._build_settings_tab(), "Settings")

        self._populate_tree()
        self._refresh_recent()

    # -------------------------------------------------------------------------
    # Library tab
    # -------------------------------------------------------------------------

    def _build_library_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Recently used section
        self._recent_header = QPushButton("▾  Recently Used")
        self._recent_header.setObjectName("section_header")
        self._recent_header.clicked.connect(self._toggle_recent)
        layout.addWidget(self._recent_header)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(90)
        self._recent_list.setObjectName("recentList")
        self._recent_list.itemDoubleClicked.connect(self._copy_recent_item)
        layout.addWidget(self._recent_list)

        # Splitter: tree / preview
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        self._tree = LibraryTree()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemClicked.connect(self._on_tree_clicked)
        self._tree.itemExpanded.connect(self._on_cat_toggled)
        self._tree.itemCollapsed.connect(self._on_cat_toggled)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._tree_context_menu)
        self._tree.reordered.connect(self._on_tree_reordered)
        self._tree.snippet_moved.connect(self._on_snippet_moved)
        self._tree.snippet_reordered.connect(self._on_snippet_reordered)
        splitter.addWidget(self._tree)

        preview_container = QWidget()
        pl = QVBoxLayout(preview_container)
        pl.setContentsMargins(0, 4, 0, 0)
        pl.setSpacing(2)
        self._preview = QTextEdit()
        self._preview.setObjectName("preview")
        self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("Select a snippet to preview")
        pl.addWidget(self._preview)
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("stats")
        pl.addWidget(self._stats_label)
        splitter.addWidget(preview_container)
        splitter.setSizes([240, 100])
        layout.addWidget(splitter)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        for text, slot, obj in [
            ("+ Category", self._add_category, "action"),
            ("+ Snippet",  self._add_item,     "action"),
        ]:
            b = QPushButton(text)
            b.setObjectName(obj)
            b.clicked.connect(slot)
            toolbar.addWidget(b)
        toolbar.addStretch()
        for text, slot, obj in [
            ("Edit",   self._edit_selected,   "action"),
            ("Delete", self._delete_selected, "danger"),
        ]:
            b = QPushButton(text)
            b.setObjectName(obj)
            b.clicked.connect(slot)
            toolbar.addWidget(b)
        layout.addLayout(toolbar)

        hint = QLabel("Double-click or Enter to copy  ·  Drag to reorder")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        return w

    # -------------------------------------------------------------------------
    # History tab
    # -------------------------------------------------------------------------

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        self._hist_list = QListWidget()
        self._hist_list.itemDoubleClicked.connect(self._copy_history_item)
        layout.addWidget(self._hist_list)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        for text, slot, obj in [
            ("Copy",            self._copy_history_item,       "action"),
            ("📌 Pin",          self._pin_history_item,        "action"),
            ("Save to Library", self._save_history_to_library, "action"),
        ]:
            b = QPushButton(text)
            b.setObjectName(obj)
            b.clicked.connect(slot)
            toolbar.addWidget(b)
        toolbar.addStretch()
        btn_clear = QPushButton("Clear all")
        btn_clear.setObjectName("danger")
        btn_clear.clicked.connect(self._clear_history)
        toolbar.addWidget(btn_clear)
        layout.addLayout(toolbar)

        hint = QLabel("Double-click to copy  ·  Pin = save to last used category")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        return w

    # -------------------------------------------------------------------------
    # Settings tab
    # -------------------------------------------------------------------------

    def _build_settings_tab(self) -> QWidget:
        # Outer widget just holds the scroll area
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer_layout.addWidget(scroll)

        w = QWidget()
        scroll.setWidget(w)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(14)

        # --- Hotkey ---
        hotkey_group = QGroupBox("Global Hotkey")
        hl = QVBoxLayout(hotkey_group)
        hl.addWidget(QLabel("Open ClipLib from anywhere"))
        self._hotkey_combo = QComboBox()
        for label, _ in HOTKEY_OPTIONS:
            self._hotkey_combo.addItem(label)
        current_hk = self._settings.get("hotkey", "<cmd>+<shift>+l")
        idx = next((i for i, (_, v) in enumerate(HOTKEY_OPTIONS) if v == current_hk), 1)
        self._hotkey_combo.setCurrentIndex(idx)
        self._hotkey_combo.currentIndexChanged.connect(self._on_hotkey_changed)
        hl.addWidget(self._hotkey_combo)
        layout.addWidget(hotkey_group)

        # --- Launch at login ---
        login_group = QGroupBox("Startup")
        ll = QVBoxLayout(login_group)
        self._login_check = QCheckBox("Launch ClipLib at login")
        self._login_check.setChecked(launchlogin.is_enabled())
        self._login_check.toggled.connect(self._on_login_toggled)
        ll.addWidget(self._login_check)
        layout.addWidget(login_group)

        # --- History size ---
        hist_group = QGroupBox("Clipboard History")
        hist_l = QVBoxLayout(hist_group)
        hist_l.addWidget(QLabel("Maximum items to keep"))
        self._max_hist_combo = QComboBox()
        for label, value in MAX_HISTORY_OPTIONS:
            self._max_hist_combo.addItem(label, value)
        current_max = self._settings.get("max_history", 200)
        for i, (_, v) in enumerate(MAX_HISTORY_OPTIONS):
            if v == current_max:
                self._max_hist_combo.setCurrentIndex(i)
                break
        self._max_hist_combo.currentIndexChanged.connect(self._on_max_history_changed)
        hist_l.addWidget(self._max_hist_combo)
        layout.addWidget(hist_group)

        # --- Clear by date ---
        date_group = QGroupBox("Clear History by Date")
        dl = QVBoxLayout(date_group)
        dl.addWidget(QLabel("Delete all items copied before:"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("MMM d, yyyy")
        dl.addWidget(self._date_edit)
        btn_clear_before = QPushButton("Clear items before this date")
        btn_clear_before.setObjectName("danger")
        btn_clear_before.clicked.connect(self._clear_history_before_date)
        dl.addWidget(btn_clear_before)
        self._date_result_label = QLabel("")
        self._date_result_label.setObjectName("hint")
        dl.addWidget(self._date_result_label)
        layout.addWidget(date_group)

        # --- Import / Export ---
        io_group = QGroupBox("Library Backup")
        io_l = QHBoxLayout(io_group)
        btn_export = QPushButton("Export Library…")
        btn_export.setObjectName("action")
        btn_export.clicked.connect(self._export_library)
        btn_import = QPushButton("Import Library…")
        btn_import.setObjectName("action")
        btn_import.clicked.connect(self._import_library)
        io_l.addWidget(btn_export)
        io_l.addWidget(btn_import)
        layout.addWidget(io_group)

        layout.addStretch()
        return outer

    # -------------------------------------------------------------------------
    # Recently used
    # -------------------------------------------------------------------------

    def _refresh_recent(self):
        self._recent_items = data_module.get_recently_used(self._data)
        self._recent_list.clear()
        for item in self._recent_items:
            self._recent_list.addItem(f"{item['title']}   ({item['category']})")

    def _toggle_recent(self):
        visible = self._recent_list.isVisible()
        self._recent_list.setVisible(not visible)
        self._recent_header.setText(
            ("▾" if not visible else "▸") + "  Recently Used"
        )

    def _copy_recent_item(self):
        sel = self._recent_list.selectedItems()
        if not sel:
            return
        idx = self._recent_list.row(sel[0])
        if idx < len(self._recent_items):
            h = self._recent_items[idx]
            self._copy_text(h["content"], cat_id=h["cat_id"], item_id=h["id"])

    # -------------------------------------------------------------------------
    # Tree
    # -------------------------------------------------------------------------

    def _make_cat_node(self, cat: dict, expanded: bool = True) -> QTreeWidgetItem:
        arrow = "▾" if expanded else "▸"
        node = QTreeWidgetItem([f"{arrow}  {cat['name']}"])
        node.setData(0, Qt.ItemDataRole.UserRole, ("cat", cat["id"]))
        font = node.font(0)
        font.setBold(True)
        node.setFont(0, font)
        node.setForeground(0, QColor("#aaa"))
        return node

    def _make_item_node(self, item: dict, cat_id: str) -> QTreeWidgetItem:
        node = QTreeWidgetItem([item["title"]])
        node.setData(0, Qt.ItemDataRole.UserRole, ("item", cat_id, item["id"], item["content"]))
        return node

    def _populate_tree(self, query=""):
        self._tree.blockSignals(True)
        self._tree.clear()
        q = query.lower().strip()
        for cat in self._data["categories"]:
            cat_matches = q and q in cat["name"].lower()
            matching_items = (
                [i for i in cat["items"] if q in i["title"].lower() or q in i["content"].lower()]
                if q else cat["items"]
            )
            if q and not cat_matches and not matching_items:
                continue
            items_to_show = cat["items"] if cat_matches else matching_items
            cat_node = self._make_cat_node(cat, expanded=True)
            for item in items_to_show:
                cat_node.addChild(self._make_item_node(item, cat["id"]))
            self._tree.addTopLevelItem(cat_node)
            cat_node.setExpanded(True)
        self._tree.blockSignals(False)

    def _on_tree_clicked(self, node: QTreeWidgetItem, col: int):
        d = node.data(0, Qt.ItemDataRole.UserRole)
        if d and d[0] == "cat":
            node.setExpanded(not node.isExpanded())

    def _on_cat_toggled(self, node: QTreeWidgetItem):
        d = node.data(0, Qt.ItemDataRole.UserRole)
        if d and d[0] == "cat":
            cat = next((c for c in self._data["categories"] if c["id"] == d[1]), None)
            if cat:
                node.setText(0, f"{'▾' if node.isExpanded() else '▸'}  {cat['name']}")

    def _on_selection_changed(self, current: QTreeWidgetItem, _prev):
        if not current:
            self._preview.clear()
            self._stats_label.setText("")
            return
        d = current.data(0, Qt.ItemDataRole.UserRole)
        if d and d[0] == "item":
            content = d[3]
            self._preview.setPlainText(content)
            chars = len(content)
            lines = content.count("\n") + 1 if content else 0
            self._stats_label.setText(f"{chars} chars  ·  {lines} line{'s' if lines != 1 else ''}")
        else:
            self._preview.clear()
            self._stats_label.setText("")

    def _on_snippet_moved(self, item_data, target_cat_id):
        """Snippet was dragged onto a category — move it in the data model."""
        old_cat_id = item_data[1]
        item_id = item_data[2]
        if old_cat_id == target_cat_id:
            return
        # Find the full item object (preserves use_count, last_used, etc.)
        item_obj = None
        for cat in self._data["categories"]:
            if cat["id"] == old_cat_id:
                item_obj = next((i for i in cat["items"] if i["id"] == item_id), None)
                break
        if item_obj is None:
            return
        data_module.delete_item(self._data, old_cat_id, item_id)
        for cat in self._data["categories"]:
            if cat["id"] == target_cat_id:
                cat["items"].append(item_obj)
                break
        data_module.save(self._data)
        self._populate_tree(self._search.text().strip())
        self._refresh_recent()

    def _on_snippet_reordered(self, item_data, target_cat_id, target_index):
        """Snippet dropped onto another snippet — reorder (or move with position)."""
        old_cat_id = item_data[1]
        item_id = item_data[2]

        item_obj = None
        for cat in self._data["categories"]:
            if cat["id"] == old_cat_id:
                item_obj = next((i for i in cat["items"] if i["id"] == item_id), None)
                if item_obj:
                    cat["items"] = [i for i in cat["items"] if i["id"] != item_id]
                break

        if item_obj is None:
            return

        for cat in self._data["categories"]:
            if cat["id"] == target_cat_id:
                cat["items"].insert(min(target_index, len(cat["items"])), item_obj)
                break

        data_module.save(self._data)
        self._populate_tree(self._search.text().strip())
        self._refresh_recent()

    def _on_tree_reordered(self):
        new_order = []
        for i in range(self._tree.topLevelItemCount()):
            node = self._tree.topLevelItem(i)
            d = node.data(0, Qt.ItemDataRole.UserRole)
            if not d or d[0] != "cat":
                continue
            item_ids = []
            for j in range(node.childCount()):
                child = node.child(j)
                cd = child.data(0, Qt.ItemDataRole.UserRole)
                if cd and cd[0] == "item":
                    item_ids.append(cd[2])
            new_order.append({"id": d[1], "item_ids": item_ids})
        data_module.reorder_data(self._data, new_order)
        self._populate_tree(self._search.text().strip())

    def _on_tab_changed(self, index):
        if index == 1:
            self._refresh_history(self._search.text().strip())

    def _on_search(self, text):
        tab = self._tabs.currentIndex()
        if tab == 0:
            self._populate_tree(text.strip())
        elif tab == 1:
            self._refresh_history(text.strip())

    # -------------------------------------------------------------------------
    # Copy
    # -------------------------------------------------------------------------

    def _on_item_double_clicked(self, item, col):
        d = item.data(0, Qt.ItemDataRole.UserRole)
        if d and d[0] == "item":
            self._copy_text(d[3], cat_id=d[1], item_id=d[2])

    def _copy_text(self, text: str, cat_id: str = "", item_id: str = ""):
        QApplication.clipboard().setText(text)
        if cat_id and item_id:
            data_module.update_item_used(self._data, cat_id, item_id)
            self._settings["last_cat_id"] = cat_id
            data_module.save_settings(self._settings)
            self._refresh_recent()
        self._show_copied_flash()

    def _show_copied_flash(self):
        original = self._search.placeholderText()
        self._search.setPlaceholderText("Copied!")
        QTimer.singleShot(1000, lambda: self._search.setPlaceholderText(original))

    # -------------------------------------------------------------------------
    # Context menu
    # -------------------------------------------------------------------------

    def _tree_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        self._tree.setCurrentItem(item)  # ensure right-clicked item is selected
        d = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #2c2c2c; color: #e0e0e0; border: 1px solid #555; }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background: #2d6a9f; }
        """)
        if d and d[0] == "item":
            menu.addAction("Copy",      lambda: self._copy_text(d[3], cat_id=d[1], item_id=d[2]))
            menu.addAction("Duplicate", self._duplicate_selected)
            menu.addAction("Edit",      self._edit_selected)
            menu.addAction("Delete",    self._delete_selected)
        elif d and d[0] == "cat":
            menu.addAction("Add Snippet",    self._add_item)
            menu.addAction("Rename",         self._edit_selected)
            menu.addAction("Delete Category",self._delete_selected)
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    # -------------------------------------------------------------------------
    # Library CRUD
    # -------------------------------------------------------------------------

    def _add_category(self):
        dlg = CategoryDialog(self)
        if dlg.exec() and dlg.name:
            data_module.add_category(self._data, dlg.name)
            self._populate_tree(self._search.text().strip())

    def _add_item(self):
        if not self._data["categories"]:
            self._add_category()
            if not self._data["categories"]:
                return
        cat_id = ""
        sel = self._tree.selectedItems()
        if sel:
            d = sel[0].data(0, Qt.ItemDataRole.UserRole)
            if d:
                cat_id = d[1]
        dlg = ItemDialog(self, self._data["categories"], cat_id=cat_id)
        if dlg.exec() and dlg.content and dlg.cat_id:
            data_module.add_item(self._data, dlg.cat_id, dlg.content)
            self._populate_tree(self._search.text().strip())

    def _edit_selected(self):
        sel = self._tree.selectedItems()
        if not sel:
            return
        d = sel[0].data(0, Qt.ItemDataRole.UserRole)
        if not d:
            return
        if d[0] == "cat":
            cat = next((c for c in self._data["categories"] if c["id"] == d[1]), None)
            if cat:
                dlg = CategoryDialog(self, name=cat["name"])
                if dlg.exec() and dlg.name:
                    data_module.rename_category(self._data, d[1], dlg.name)
                    self._populate_tree(self._search.text().strip())
        elif d[0] == "item":
            cat = next((c for c in self._data["categories"] if c["id"] == d[1]), None)
            item = next((i for i in cat["items"] if i["id"] == d[2]), None) if cat else None
            if item:
                dlg = ItemDialog(self, self._data["categories"], content=item["content"], cat_id=d[1])
                if dlg.exec() and dlg.content:
                    if dlg.cat_id != d[1]:
                        data_module.delete_item(self._data, d[1], d[2])
                        data_module.add_item(self._data, dlg.cat_id, dlg.content)
                    else:
                        data_module.update_item(self._data, d[1], d[2], dlg.content)
                    self._populate_tree(self._search.text().strip())

    def _delete_selected(self):
        sel = self._tree.selectedItems()
        if not sel:
            return
        d = sel[0].data(0, Qt.ItemDataRole.UserRole)
        if not d:
            return
        if d[0] == "cat":
            data_module.delete_category(self._data, d[1])
        elif d[0] == "item":
            data_module.delete_item(self._data, d[1], d[2])
        self._populate_tree(self._search.text().strip())
        self._refresh_recent()

    def _duplicate_selected(self):
        sel = self._tree.selectedItems()
        if not sel:
            return
        d = sel[0].data(0, Qt.ItemDataRole.UserRole)
        if not d or d[0] != "item":
            return
        cat = next((c for c in self._data["categories"] if c["id"] == d[1]), None)
        item = next((i for i in cat["items"] if i["id"] == d[2]), None) if cat else None
        if item:
            data_module.add_item(self._data, d[1], item["content"])
            self._populate_tree(self._search.text().strip())

    # -------------------------------------------------------------------------
    # History
    # -------------------------------------------------------------------------

    def add_to_history(self, text: str):
        if self._history and self._history[0]["text"] == text:
            return
        self._history = [h for h in self._history if h["text"] != text]
        self._history.insert(0, {"text": text, "ts": datetime.now().isoformat(timespec="seconds")})
        max_h = self._settings.get("max_history", 200)
        if max_h != -1 and len(self._history) > max_h:
            self._history = self._history[:max_h]
        data_module.save_history(self._history)
        if self._tabs.currentIndex() == 1:
            self._refresh_history(self._search.text().strip())

    def _refresh_history(self, query=""):
        self._hist_list.clear()
        items = self._history
        if query:
            items = [h for h in items if query.lower() in h["text"].lower()]
        for h in items:
            ts = datetime.fromisoformat(h["ts"]).strftime("%b %d  %H:%M")
            preview = h["text"][:90].replace("\n", " ")
            self._hist_list.addItem(f"{ts}   {preview}")

    def _current_history_item(self) -> dict | None:
        sel = self._hist_list.selectedItems()
        if not sel:
            return None
        idx = self._hist_list.row(sel[0])
        query = self._search.text().strip()
        visible = [h for h in self._history if query.lower() in h["text"].lower()] if query else self._history
        return visible[idx] if idx < len(visible) else None

    def _copy_history_item(self):
        h = self._current_history_item()
        if h:
            self._copy_text(h["text"])

    def _pin_history_item(self):
        """Save selected history item to last used category instantly — no dialog."""
        h = self._current_history_item()
        if not h:
            return
        last_cat_id = self._settings.get("last_cat_id", "")
        cat = next((c for c in self._data["categories"] if c["id"] == last_cat_id), None)
        if not cat:
            # Fall back to full dialog if no last category
            self._save_history_to_library()
            return
        data_module.add_item(self._data, cat["id"], h["text"])
        self._populate_tree(self._search.text().strip())
        self._refresh_recent()
        self._show_copied_flash()

    def _save_history_to_library(self):
        h = self._current_history_item()
        if not h:
            return
        if not self._data["categories"]:
            self._add_category()
            if not self._data["categories"]:
                return
        dlg = ItemDialog(self, self._data["categories"], content=h["text"])
        if dlg.exec() and dlg.content and dlg.cat_id:
            data_module.add_item(self._data, dlg.cat_id, dlg.content)
            self._populate_tree(self._search.text().strip())
            self._refresh_recent()

    def _clear_history(self):
        self._history.clear()
        data_module.save_history(self._history)
        self._hist_list.clear()

    # -------------------------------------------------------------------------
    # Settings handlers
    # -------------------------------------------------------------------------

    def _on_hotkey_changed(self, index):
        _, hk_str = HOTKEY_OPTIONS[index]
        self._settings["hotkey"] = hk_str
        data_module.save_settings(self._settings)
        # Signal main.py to restart the hotkey listener
        self.hotkey_changed.emit(hk_str) if hasattr(self, "_hotkey_signal_wired") else None

    def _on_login_toggled(self, checked: bool):
        if checked:
            launchlogin.enable()
        else:
            launchlogin.disable()

    def _on_max_history_changed(self, index):
        value = self._max_hist_combo.itemData(index)
        self._settings["max_history"] = value
        data_module.save_settings(self._settings)
        if value != -1 and len(self._history) > value:
            self._history = self._history[:value]
            data_module.save_history(self._history)

    def _clear_history_before_date(self):
        qdate = self._date_edit.date()
        cutoff = datetime(qdate.year(), qdate.month(), qdate.day())
        before = len(self._history)
        self._history = data_module.clear_history_before(self._history, cutoff)
        removed = before - len(self._history)
        data_module.save_history(self._history)
        if self._tabs.currentIndex() == 1:
            self._refresh_history()
        msg = f"Removed {removed} item{'s' if removed != 1 else ''}."
        self._date_result_label.setText(msg)
        QTimer.singleShot(3000, lambda: self._date_result_label.setText(""))

    def _export_library(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Library", "cliplib_backup.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def _import_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Library", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                imported = json.load(f)
            if "categories" not in imported:
                raise ValueError("Not a valid ClipLib export file.")
            # Merge: append categories that don't already exist by name
            existing_names = {c["name"] for c in self._data["categories"]}
            added = 0
            for cat in imported.get("categories", []):
                if cat["name"] not in existing_names:
                    self._data["categories"].append(cat)
                    added += 1
            data_module.save(self._data)
            self._populate_tree(self._search.text().strip())
            self._refresh_recent()
            QMessageBox.information(self, "Import Complete", f"Added {added} new categories.")
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))

    # -------------------------------------------------------------------------
    # Show / hide
    # -------------------------------------------------------------------------

    def show_near_tray(self, tray_geometry):
        screen = QApplication.primaryScreen().availableGeometry()
        if tray_geometry.isNull() or (tray_geometry.x() == 0 and tray_geometry.y() == 0):
            x = screen.right() - self.width() - 10
            y = screen.top() + 28
        else:
            x = min(tray_geometry.x(), screen.right() - self.width() - 10)
            y = tray_geometry.bottom() + 4 if tray_geometry.top() < screen.height() // 2 else screen.bottom() - self.height() - 10
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self._search.setFocus()
        self._search.clear()
        self._populate_tree()
        self._refresh_history()
        self._refresh_recent()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._tabs.currentIndex() == 0:
                sel = self._tree.selectedItems()
                if sel:
                    d = sel[0].data(0, Qt.ItemDataRole.UserRole)
                    if d and d[0] == "item":
                        self._copy_text(d[3], cat_id=d[1], item_id=d[2])
                        self.hide()
        super().keyPressEvent(event)
