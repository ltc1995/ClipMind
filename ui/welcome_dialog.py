"""ClipMind 首次启动欢迎引导。"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from utils.config import APP_DESCRIPTION, APP_NAME, APP_VERSION


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"欢迎使用 {APP_NAME}")
        self.setFixedSize(460, 430)
        self.setStyleSheet(self._style())
        self._init_ui()

    @staticmethod
    def _icon_path() -> str:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources", "icons", "clipmind.ico",
        )
        return path if os.path.exists(path) else ""

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(14)
        icon_label = QLabel()
        icon_label.setFixedSize(56, 56)
        icon_path = self._icon_path()
        if icon_path:
            icon_label.setPixmap(QPixmap(icon_path).scaled(
                56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("✂")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(
                "font-size: 32px; color: #4a9eff; background: #eef4ff; border-radius: 12px;")
        header.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel(f"欢迎使用 {APP_NAME}")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #222;")
        title_box.addWidget(title)
        subtitle = QLabel(f"{APP_DESCRIPTION} v{APP_VERSION}")
        subtitle.setStyleSheet("font-size: 12px; color: #888;")
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        tip_style = "font-size: 13px; color: #444; line-height: 1.6;"
        tips = [
            ("快捷键", "在任意软件中按 Ctrl + Shift + V，快速呼出搜索窗口"),
            ("恢复复制", "点击历史记录即可写回剪贴板，再按 Ctrl + V 粘贴"),
            ("隐私保护", "所有数据仅保存在本地，不上传、不联网"),
        ]
        for index, (label, text) in enumerate(tips):
            row = QHBoxLayout()
            row.setSpacing(10)
            badge = QLabel(f"{index + 1}")
            badge.setFixedSize(24, 24)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #4a9eff;"
                "background: #eef4ff; border-radius: 12px;")
            row.addWidget(badge)
            content = QLabel(f"<b>{label}</b>：{text}")
            content.setTextFormat(Qt.RichText)
            content.setStyleSheet(tip_style)
            content.setWordWrap(True)
            row.addWidget(content, 1)
            layout.addLayout(row)

        layout.addStretch()

        note = QLabel("提示：ClipMind 常驻系统托盘，关闭主窗口不会退出。")
        note.setStyleSheet("font-size: 12px; color: #999;")
        layout.addWidget(note)

        button_row = QHBoxLayout()
        button_row.addStretch()
        start_btn = QPushButton("开始使用")
        start_btn.setObjectName("primary")
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setFixedWidth(140)
        start_btn.clicked.connect(self.accept)
        button_row.addWidget(start_btn)
        layout.addLayout(button_row)

    @staticmethod
    def _style() -> str:
        return """
            QDialog { background: #ffffff; }
            QPushButton#primary {
                background: #4a9eff; color: white; border: none;
                border-radius: 6px; font-size: 14px; font-weight: bold;
                padding: 10px 0;
            }
            QPushButton#primary:hover { background: #3a8eef; }
        """
