# ClipMind 主入口 - Phase 2 体验优化版

import sys
import os
import ctypes
import tempfile
import atexit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import QSettings, QTimer

# 延迟刷新：将 refresh 推迟到下一轮事件循环，避免在定时器回调中直接操作 UI 导致绘制被阻塞
from PySide6.QtGui import QIcon, QAction
from database.db import Database
from database.models import ClipboardItem
from clipboard.monitor import ClipboardMonitor
from search.search_engine import SearchEngine
from clipboard.manager import ClipboardManager
from ui.main_window import MainWindow
from ui.search_window import SearchWindow
from ui.settings_dialog import SettingsDialog
from ui.welcome_dialog import WelcomeDialog
from utils.shortcut import GlobalHotkey
from utils.config import APP_NAME, HOTKEY, DB_DIR, CLIPBOARD_POLL_INTERVAL
import ctypes

_LOCK_FILE = os.path.join(tempfile.gettempdir(), ".clipmind_instance.lock")

def _acquire_instance_lock():
    """防止多个 ClipMind 实例同时运行"""
    try:
        with open(_LOCK_FILE, "x") as f:
            f.write(str(os.getpid()))
        atexit.register(lambda: os.remove(_LOCK_FILE) if os.path.exists(_LOCK_FILE) else None)
        return True
    except FileExistsError:
        try:
            with open(_LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            try:
                import signal
                os.kill(old_pid, 0)
                print("ClipMind 已在运行中。请先关闭已有实例。")
                sys.exit(1)
            except (OSError, ProcessLookupError):
                with open(_LOCK_FILE, "w") as f:
                    f.write(str(os.getpid()))
                atexit.register(lambda: os.remove(_LOCK_FILE) if os.path.exists(_LOCK_FILE) else None)
                return True
        except Exception:
            return True


class ClipMindApp:
    """ClipMind 应用主控"""

    def __init__(self):
        _acquire_instance_lock()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 设置应用图标
        icon_path = self._icon_path()
        if icon_path:
            self.app.setWindowIcon(QIcon(icon_path))

        # 初始化数据库
        self.db = Database()

        # 初始化各模块
        self.search_engine = SearchEngine(self.db)
        self.clipboard_manager = ClipboardManager(self.db)
        self.clipboard_monitor = ClipboardMonitor(self.clipboard_manager, CLIPBOARD_POLL_INTERVAL)

        # 创建 UI
        self.main_window = MainWindow(self.db, self.search_engine, self.clipboard_manager)
        self.search_window = SearchWindow(self.db, self.search_engine, self.clipboard_manager)

        # 连接信号
        self.main_window.open_settings_requested.connect(self._open_settings)
        self.main_window.item_selected.connect(self._on_item_selected)
        self.search_window.item_selected.connect(self._on_item_selected)

        # 全局快捷键
        self.hotkey = GlobalHotkey(HOTKEY, parent=self.app)
        self.hotkey.activated.connect(self._on_hotkey)

        # 剪贴板监听
        self.clipboard_monitor.on_save(self._on_clipboard_save)
        self.clipboard_monitor.start()

        # 注册快捷键
        self.hotkey.register()

        # 系统托盘
        self._setup_tray()

        # 初始化完成后显示窗口
        self.main_window.show()
        QTimer.singleShot(300, self._show_welcome_if_first_run)

        # 窗口显示后才能获得有效 HWND，再注册快捷键

    @staticmethod
    def _icon_path() -> str:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "resources", "icons", "clipmind.ico")
        return path if os.path.exists(path) else ""

    def _setup_tray(self):
        """设置系统托盘"""
        self.tray = QSystemTrayIcon()

        icon_path = self._icon_path()
        if icon_path:
            self.tray.setIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(self._create_fallback_icon())

        self.tray.setToolTip("ClipMind 智能剪贴板")

        menu = QMenu()
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
            QMenu::separator {
                height: 1px;
                background: #e8e8e8;
                margin: 4px 8px;
            }
        """)

        show_action = QAction("显示 ClipMind", self.app)
        show_action.triggered.connect(self.main_window.show)
        menu.addAction(show_action)

        search_action = QAction("快速搜索", self.app)
        search_action.triggered.connect(self._show_search)
        menu.addAction(search_action)

        menu.addSeparator()

        settings_action = QAction("设置...", self.app)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("退出 ClipMind", self.app)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    @staticmethod
    def _create_fallback_icon():
        from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush
        pixmap = QPixmap(48, 48)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#4a9eff")))
        painter.setPen(QColor("#4a9eff"))
        painter.drawRoundedRect(4, 4, 40, 40, 8, 8)
        painter.setBrush(QBrush(QColor(255, 255, 255, 215)))
        painter.drawRoundedRect(9, 12, 30, 30, 4, 4)
        painter.end()
        return QIcon(pixmap)

    def _show_search(self):
        self.search_window.show_and_focus()

    def _on_hotkey(self):
        """全局快捷键：恢复主窗口或切换搜索弹窗"""
        if self.main_window.isMinimized() or not self.main_window.isVisible():
            self.main_window.showNormal()
            self.main_window.raise_()
            self.main_window.activateWindow()
        elif self.search_window.isVisible():
            self.search_window.hide()
        else:
            self.search_window.show_and_focus()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()

    def _show_welcome_if_first_run(self):
        """首次启动时展示欢迎引导，之后不再弹出。"""
        settings = QSettings(APP_NAME, APP_NAME)
        if not settings.value("first_run", True, type=bool):
            return
        dialog = WelcomeDialog()
        dialog.exec()
        settings.setValue("first_run", False)

    def _on_item_selected(self, item: ClipboardItem):
        self.main_window.refresh()

    def _on_clipboard_save(self, item: ClipboardItem):
        QTimer.singleShot(0, self.main_window.refresh)

    def _open_settings(self):
        dialog = SettingsDialog(self.db, self.main_window)
        dialog.settings_changed.connect(self.main_window.refresh)
        dialog.exec()

    def run(self):
        """运行应用"""
        sys.exit(self.app.exec())

    def quit(self):
        """退出应用"""
        self.clipboard_monitor.stop()
        self.hotkey.unregister()
        self.db.close()
        if hasattr(self, "tray"):
            self.tray.hide()
        self.app.quit()


if __name__ == "__main__":
    app = ClipMindApp()
    app.run()
