# ClipMind 主窗口模块

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QLabel,
    QPushButton, QMenu, QMessageBox, QInputDialog, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap
from typing import List
from database.db import Database
from database.models import ClipboardItem
from search.search_engine import SearchEngine
from clipboard.manager import ClipboardManager
from utils.config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, PREVIEW_MAX_LENGTH, CONTENT_TYPE_IMAGE


class HistoryItemWidget(QWidget):
    THUMB_SIZE = 48

    def __init__(self, item: ClipboardItem, parent=None):
        super().__init__(parent)
        self.item = item

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignVCenter)

        type_label = QLabel(self._type_icon(item))
        type_label.setStyleSheet("font-size: 15px;")
        type_label.setFixedWidth(24)
        type_label.setAlignment(Qt.AlignCenter)
        header.addWidget(type_label)

        if item.content_type == CONTENT_TYPE_IMAGE and item.image_path and os.path.exists(item.image_path):
            thumb = QLabel()
            pixmap = QPixmap(item.image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(self.THUMB_SIZE, self.THUMB_SIZE,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                thumb.setPixmap(pixmap)
                thumb.setFixedSize(self.THUMB_SIZE, self.THUMB_SIZE)
                thumb.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 4px;")
                header.addWidget(thumb)

        preview_text = item.preview(PREVIEW_MAX_LENGTH)
        preview = QLabel(preview_text)
        preview.setStyleSheet("font-size: 13px; color: #2c2c2c;")
        preview.setWordWrap(True)
        header.addWidget(preview, 1)

        time_label = QLabel(self._format_time(item.created_time))
        time_label.setStyleSheet("font-size: 11px; color: #aaa;")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_label.setFixedWidth(70)
        header.addWidget(time_label)

        layout.addLayout(header)

        badges = []
        if item.is_favorite:
            badges.append(("\u2605", "#f5a623", "#fff8e1"))
        if item.tags:
            for tag in item.tags.split(","):
                tag = tag.strip()
                if tag:
                    badges.append((tag, "#4a9eff", "#eef4ff"))
        if item.language:
            badges.append((item.language, "#666666", "#f0f0f0"))
        elif item.content_type == "code":
            badges.append(("\u4ee3\u7801", "#666666", "#f0f0f0"))
        elif item.content_type == CONTENT_TYPE_IMAGE:
            badges.append(("\u56fe\u7247", "#34c759", "#e8f8ed"))

        if badges:
            meta_row = QHBoxLayout()
            meta_row.setSpacing(6)
            for text, fg, bg in badges:
                lbl = QLabel(text)
                lbl.setStyleSheet(f"font-size: 11px; color: {fg}; background: {bg}; padding: 2px 8px; border-radius: 8px;")
                meta_row.addWidget(lbl)
            meta_row.addStretch()
            layout.addLayout(meta_row)

    @staticmethod
    def _type_icon(item: ClipboardItem) -> str:
        if item.is_favorite:
            return "\u2605"
        if item.content_type == "code":
            return "</>"
        elif item.content_type == CONTENT_TYPE_IMAGE:
            return "\U0001f5bc"
        return "\U0001f4cb"

    @staticmethod
    def _format_time(time_str: str) -> str:
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            diff = now - dt
            if diff < timedelta(minutes=1):
                return "\u521a\u521a"
            elif diff < timedelta(hours=1):
                return f"{int(diff.total_seconds() // 60)}\u5206\u949f\u524d"
            elif diff < timedelta(days=1):
                return f"{int(diff.total_seconds() // 3600)}\u5c0f\u65f6\u524d"
            elif diff < timedelta(days=2):
                return "\u6628\u5929"
            elif diff < timedelta(days=7):
                return f"{diff.days}\u5929\u524d"
            else:
                return dt.strftime("%m-%d")
        except Exception:
            return time_str


class MainWindow(QMainWindow):

    item_selected = Signal(ClipboardItem)
    open_settings_requested = Signal()

    def nativeEvent(self, eventType, message):
        return super().nativeEvent(eventType, message)

    def __init__(self, db: Database, search_engine: SearchEngine, clipboard_manager: ClipboardManager):
        super().__init__()
        self.db = db
        self.search_engine = search_engine
        self.clipboard_manager = clipboard_manager
        self._items: List[ClipboardItem] = []
        self._current_search = ""
        self._current_filter = "all"
        self._init_ui()
        self._load_history()

    def _init_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        icon_path = self._icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(Qt.Window)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet("QMainWindow { background: #ffffff; }")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #e8e8e8;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 6, 12, 6)
        top_layout.setSpacing(6)

        title_label = QLabel("ClipMind")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        top_layout.addWidget(title_label)

        self.stat_label = QLabel()
        self.stat_label.setStyleSheet("font-size: 11px; color: #aaa;")
        top_layout.addWidget(self.stat_label)

        top_layout.addStretch()

        self.filter_buttons = {}
        for key, label in [("all", "\u5168\u90e8"), ("favorites", "\u6536\u85cf"), ("code", "\u4ee3\u7801"),
                           ("text", "\u6587\u672c"), ("image", "\u56fe\u7247")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == "all")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._filter_button_style(key == "all"))
            btn.clicked.connect(lambda checked, k=key: self._on_filter(k))
            self.filter_buttons[key] = btn
            top_layout.addWidget(btn)

        settings_btn = QPushButton("\u2699")
        settings_btn.setFixedSize(32, 28)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QPushButton:hover {
                background: #e8f0fe;
                border-color: #4a9eff;
            }
        """)
        settings_btn.clicked.connect(self.open_settings_requested.emit)
        top_layout.addWidget(settings_btn)

        main_layout.addWidget(top_bar)

        search_frame = QWidget()
        search_frame.setStyleSheet("background: #fafafa; border-bottom: 1px solid #e0e0e0;")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 12, 8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("\u641c\u7d22\u526a\u8d34\u677f\u5185\u5bb9...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 14px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #4a9eff;
                background: #fff;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        main_layout.addWidget(search_frame)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background: white;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background: #eef4ff;
            }
            QListWidget::item:hover {
                background: #f5f7fa;
            }
        """)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.setSpacing(0)
        main_layout.addWidget(self.list_widget)

        status_bar = QWidget()
        status_bar.setStyleSheet("background: #f8f9fa; border-top: 1px solid #e8e8e8;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 11px; color: #999;")
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(status_bar)

    @staticmethod
    def _filter_button_style(active: bool) -> str:
        if active:
            return """
                QPushButton {
                    font-size: 12px;
                    padding: 4px 12px;
                    border: 1px solid #4a9eff;
                    border-radius: 12px;
                    background: #4a9eff;
                    color: white;
                }
                QPushButton:hover {
                    background: #3a8eef;
                }
            """
        return """
            QPushButton {
                font-size: 12px;
                padding: 4px 12px;
                border: 1px solid #ddd;
                border-radius: 12px;
                background: white;
                color: #666;
            }
            QPushButton:hover {
                background: #f0f4ff;
                border-color: #4a9eff;
                color: #4a9eff;
            }
        """

    @staticmethod
    def _icon_path() -> str:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "resources", "icons", "clipmind.ico")
        return path if os.path.exists(path) else ""

    def _load_history(self, keyword: str = "", filter_type: str = "all"):
        self._current_search = keyword
        self._current_filter = filter_type

        if keyword:
            items = self.search_engine.search(keyword)
        else:
            items = self.search_engine.search("")

        if filter_type == "favorites":
            items = [it for it in items if it.is_favorite]
        elif filter_type == "code":
            items = [it for it in items if it.content_type == "code"]
        elif filter_type == "text":
            items = [it for it in items if it.content_type == "text"]
        elif filter_type == "image":
            items = [it for it in items if it.content_type == CONTENT_TYPE_IMAGE]

        self._items = items
        self.list_widget.clear()
        for item in items:
            widget = HistoryItemWidget(item)
            widget.ensurePolished()
            widget.adjustSize()
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, item.id)
            h = widget.sizeHint().height()
            list_item.setSizeHint(QSize(0, h if h > 0 else 52))
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, widget)

        total = self.db.count_items()
        self.stat_label.setText(f"\u5171 {total} \u6761")
        self.status_label.setText(f"\u663e\u793a {len(items)} \u6761\u8bb0\u5f55")

    def refresh(self):
        if self.search_input:
            self.search_input.blockSignals(True)
            self.search_input.clear()
            self.search_input.blockSignals(False)
        self._current_search = ""
        self._load_history("", getattr(self, "_current_filter", "all"))
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.refresh()
        super().changeEvent(event)

    def closeEvent(self, event):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()
        event.accept()

    def _on_filter(self, filter_type: str):
        for key, btn in self.filter_buttons.items():
            active = key == filter_type
            btn.setChecked(active)
            btn.setStyleSheet(self._filter_button_style(active))
        self._load_history(self._current_search, filter_type)

    def _on_search(self, text: str):
        self._current_search = text
        self._load_history(text, getattr(self, "_current_filter", "all"))

    def _on_item_clicked(self, list_item: QListWidgetItem):
        item_id = list_item.data(Qt.UserRole)
        item = self.db.get_by_id(item_id)
        if item:
            self.clipboard_manager.copy_to_clipboard(item)
            self.item_selected.emit(item)
            if item.content_type == CONTENT_TYPE_IMAGE:
                self.status_label.setText("\u2713 \u56fe\u7247\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f")
            else:
                self.status_label.setText("\u2713 \u5df2\u590d\u5236: " + item.preview(30))
            self.status_label.setStyleSheet("font-size: 11px; color: #34c759;")
            QTimer.singleShot(2000, self._restore_status)

    def _restore_status(self):
        self.status_label.setStyleSheet("font-size: 11px; color: #999;")
        self.status_label.setText(f"\u663e\u793a {len(self._items)} \u6761\u8bb0\u5f55")

    def _show_context_menu(self, pos):
        list_item = self.list_widget.itemAt(pos)
        if not list_item:
            return
        item_id = list_item.data(Qt.UserRole)
        item = self.db.get_by_id(item_id)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                font-size: 13px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #eef4ff;
                color: #1a5cbf;
            }
        """)

        fav_text = "\u2605 \u53d6\u6d88\u6536\u85cf" if item.is_favorite else "\u2606 \u6536\u85cf"
        fav_action = QAction(fav_text, self)
        fav_action.triggered.connect(lambda: self._toggle_favorite(item_id))
        menu.addAction(fav_action)

        menu.addSeparator()

        tag_action = QAction("\U0001f3f7 \u7f16\u8f91\u6807\u7b7e", self)
        tag_action.triggered.connect(lambda: self._edit_tags(item_id))
        menu.addAction(tag_action)

        menu.addSeparator()

        copy_action = QAction("\U0001f4cb \u590d\u5236\u5185\u5bb9", self)
        copy_action.triggered.connect(lambda: self._copy_item(item_id))
        menu.addAction(copy_action)

        if item.content_type == CONTENT_TYPE_IMAGE:
            save_action = QAction("\U0001f4be \u53e6\u5b58\u4e3a...", self)
            save_action.triggered.connect(lambda: self._save_image_as(item_id))
            menu.addAction(save_action)

        menu.addSeparator()

        delete_action = QAction("\U0001f5d1 \u5220\u9664", self)
        delete_action.triggered.connect(lambda: self._delete_item(item_id))
        menu.addAction(delete_action)

        menu.exec(self.list_widget.mapToGlobal(pos))

    def _edit_tags(self, item_id: int):
        item = self.db.get_by_id(item_id)
        if not item:
            return
        tags, ok = QInputDialog.getText(
            self, "\u7f16\u8f91\u6807\u7b7e", "\u8f93\u5165\u6807\u7b7e\uff08\u7528\u9017\u53f7\u5206\u9694\uff09:",
            text=item.tags
        )
        if ok:
            self.db.update_tags(item_id, tags.strip())
            self.refresh()

    def _copy_item(self, item_id: int):
        item = self.db.get_by_id(item_id)
        if item:
            self.clipboard_manager.copy_to_clipboard(item)
            self.item_selected.emit(item)
            if item.content_type == CONTENT_TYPE_IMAGE:
                self.status_label.setText("\u2713 \u56fe\u7247\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f")
            else:
                self.status_label.setText("\u2713 \u5df2\u590d\u5236: " + item.preview(30))
            self.status_label.setStyleSheet("font-size: 11px; color: #34c759;")
            QTimer.singleShot(2000, self._restore_status)

    def _save_image_as(self, item_id: int):
        item = self.db.get_by_id(item_id)
        if not item or not item.image_path or not os.path.exists(item.image_path):
            return
        default_name = os.path.basename(item.image_path)
        save_path, _ = QFileDialog.getSaveFileName(
            self, "\u4fdd\u5b58\u56fe\u7247", default_name,
            "PNG \u56fe\u7247 (*.png);;JPEG \u56fe\u7247 (*.jpg);;\u6240\u6709\u6587\u4ef6 (*)"
        )
        if save_path:
            try:
                pixmap = QPixmap(item.image_path)
                pixmap.save(save_path)
                self.status_label.setText("\u2713 \u56fe\u7247\u5df2\u4fdd\u5b58: " + os.path.basename(save_path))
                self.status_label.setStyleSheet("font-size: 11px; color: #34c759;")
                QTimer.singleShot(3000, self._restore_status)
            except Exception as e:
                print(f"Save image failed: {e}")

    def _toggle_favorite(self, item_id: int):
        self.db.toggle_favorite(item_id)
        self.refresh()

    def _delete_item(self, item_id: int):
        reply = QMessageBox.question(self, "\u786e\u8ba4\u5220\u9664", "\u786e\u5b9a\u8981\u5220\u9664\u8fd9\u6761\u8bb0\u5f55\u5417\uff1f",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            item = self.db.get_by_id(item_id)
            if item:
                self.clipboard_manager.mark_deleted(item.content)
                if item.content_type == CONTENT_TYPE_IMAGE and item.image_path:
                    try:
                        if os.path.exists(item.image_path):
                            os.remove(item.image_path)
                    except Exception as e:
                        print(f"Failed to delete image file: {e}")
            self.db.delete_item(item_id)
            self.refresh()

    def _on_new_item(self, item: ClipboardItem):
        self.refresh()
