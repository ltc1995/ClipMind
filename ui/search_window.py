# 快速搜索弹窗

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QIcon
from database.db import Database
from database.models import ClipboardItem
from search.search_engine import SearchEngine
from clipboard.manager import ClipboardManager
from utils.config import WINDOW_WIDTH, PREVIEW_MAX_LENGTH


class SearchWindow(QWidget):

    item_selected = Signal(ClipboardItem)

    def __init__(self, db: Database, search_engine: SearchEngine, clipboard_manager: ClipboardManager):
        super().__init__()
        self.db = db
        self.search_engine = search_engine
        self.clipboard_manager = clipboard_manager
        self._items = []
        self._current_search = ""
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("ClipMind 搜索")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.resize(WINDOW_WIDTH, 400)

        self.setStyleSheet("""
            SearchWindow {
                background: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #e8e8e8;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_label = QLabel("快速搜索剪贴板  (Esc 关闭)")
        header_label.setStyleSheet("font-size: 12px; color: #999;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        count_label = QLabel()
        count_label.setObjectName("search_count_label")
        count_label.setStyleSheet("font-size: 11px; color: #aaa;")
        header_layout.addWidget(count_label)
        layout.addWidget(header)
 
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索剪贴板内容...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                font-size: 15px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                background: #fafafa;
            }
            QLineEdit:focus {
                background: white;
                border-bottom: 2px solid #4a9eff;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_return)

        layout.addWidget(self.search_input)
 
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background: white;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background: #e8f0fe;
            }
            QListWidget::item:hover {
                background: #f5f7fa;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        status_bar = QWidget()
        status_bar.setStyleSheet("background: #f8f9fa; border-top: 1px solid #e8e8e8;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 11px; color: #bbb;")
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_bar)

    def show_and_focus(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def _on_search(self, text: str):
        self._current_search = text
        self._load_results(text)

    def _on_return(self):
        if self.list_widget.count() > 0:
            item = self.list_widget.item(0)
            self._on_item_clicked(item)

    def _load_results(self, keyword: str = ""):
        if keyword:
            items = self.search_engine.search(keyword)
        else:
            items = self.search_engine.search("")[:10]

        self._items = items
        self.list_widget.clear()

        count_label = self.findChild(QLabel, "search_count_label")
        if count_label:
            count_label.setText(f"{len(items)} 条")
        self.status_label.setText(f"共 {len(items)} 条记录")
 
        for item in items:
            preview = item.preview(PREVIEW_MAX_LENGTH)
            if item.content_type == "code":
                preview = "</> " + preview
            elif item.content_type == "image":
                preview = "\U0001f5bc 图片"
            if item.is_favorite:
                preview = "\u2605 " + preview
            list_item = QListWidgetItem(preview)
            list_item.setData(Qt.UserRole, item.id)
            self.list_widget.addItem(list_item)

    def _on_item_clicked(self, list_item: QListWidgetItem):
        item_id = list_item.data(Qt.UserRole)
        item = self.db.get_by_id(item_id)
        if item:
            self.clipboard_manager.copy_to_clipboard(item)
            self.item_selected.emit(item)
            self.hide()
            
