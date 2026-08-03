# 剪贴板监听模块

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from clipboard.manager import ClipboardManager


class ClipboardMonitor:
    """使用定时器轮询剪贴板变化"""

    def __init__(self, manager: ClipboardManager, interval: float = 0.5):
        self.manager = manager
        self.timer = QTimer()
        self.timer.setInterval(int(interval * 1000))
        self.timer.timeout.connect(self._on_tick)
        self._on_save_callbacks = []
        app = QApplication.instance()
        if app is not None:
            app.clipboard().dataChanged.connect(self._on_clipboard_changed)

    def start(self):
        """开始监听"""
        self.timer.start()

    def stop(self):
        """停止监听"""
        self.timer.stop()

    def on_save(self, callback):
        """注册保存回调"""
        self._on_save_callbacks.append(callback)

    def _on_tick(self):
        try:
            item = self.manager.check_and_save(force=False)
            if item:
                for cb in self._on_save_callbacks:
                    cb(item)
        except Exception as e:
            print(f"ClipboardMonitor error: {e}")

    def _on_clipboard_changed(self):
        try:
            item = self.manager.check_and_save(force=True)
            if item:
                for cb in self._on_save_callbacks:
                    cb(item)
        except Exception as e:
            print(f"ClipboardMonitor error: {e}")
