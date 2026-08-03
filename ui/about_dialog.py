"""ClipMind 关于对话框：版本信息、隐私声明、功能矩阵。"""

import os

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from utils.config import APP_AUTHOR, APP_DESCRIPTION, APP_NAME, APP_VERSION
from utils.license import FREE_FEATURES, PRO_FEATURES, get_edition
from utils.updater import check_for_update


class UpdateCheckThread(QThread):
    """在后台线程执行更新检查，避免阻塞界面。"""

    result_ready = Signal(tuple)

    def run(self):
        self.result_ready.emit(check_for_update())


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._closed = False
        self.setWindowTitle(f"关于 {APP_NAME}")
        self.setFixedSize(460, 520)
        self.setStyleSheet(self._style())
        self._init_ui()

    def closeEvent(self, event):
        self._closed = True
        super().closeEvent(event)

    @staticmethod
    def _icon_path() -> str:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources", "icons", "clipmind.ico",
        )
        return path if os.path.exists(path) else ""

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(10)

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
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #222;")
        title_box.addWidget(title)
        subtitle = QLabel(f"{APP_DESCRIPTION} · 版本 {APP_VERSION} · {get_edition()}")
        subtitle.setStyleSheet("font-size: 12px; color: #888;")
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        intro = QLabel(
            "ClipMind 是一款 Windows 智能剪贴板管理工具：记录你的复制历史，"
            "并提供搜索、分类、整理能力，让剪贴板成为你的个人知识库。"
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("font-size: 13px; color: #555; line-height: 1.5;")
        layout.addWidget(intro)

        g1 = QGroupBox("隐私承诺")
        g1l = QVBoxLayout(g1)
        privacy = QLabel(
            "所有剪贴板数据默认仅保存在本地，不会上传到云端；\n"
            "ClipMind 不收集、不出售任何用户内容，你可随时清空全部历史记录。"
        )
        privacy.setWordWrap(True)
        privacy.setStyleSheet("font-size: 12px; color: #666; line-height: 1.5;")
        g1l.addWidget(privacy)
        layout.addWidget(g1)

        g2 = QGroupBox("功能")
        g2l = QVBoxLayout(g2)
        free_names = "、".join(FREE_FEATURES.values())
        free_label = QLabel(f"免费功能：{free_names}")
        free_label.setWordWrap(True)
        free_label.setStyleSheet("font-size: 12px; color: #333;")
        g2l.addWidget(free_label)
        pro_names = "、".join(PRO_FEATURES.values())
        pro_label = QLabel(f"Pro 功能（即将上线）：{pro_names}")
        pro_label.setWordWrap(True)
        pro_label.setStyleSheet("font-size: 12px; color: #999;")
        g2l.addWidget(pro_label)
        layout.addWidget(g2)

        layout.addStretch()

        copyright_label = QLabel(
            f"© {APP_AUTHOR} · 本软件仅分发可执行文件，源码不随包发布。")
        copyright_label.setStyleSheet("font-size: 11px; color: #bbb;")
        layout.addWidget(copyright_label)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.update_btn = QPushButton("检查更新")
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self._on_check_update)
        button_row.addWidget(self.update_btn)
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

    @staticmethod
    def _style() -> str:
        return """
            QDialog { background: #ffffff; }
            QGroupBox {
                font-size: 13px; font-weight: bold; color: #333;
                border: 1px solid #e0e0e0; border-radius: 8px;
                margin-top: 10px; padding: 14px 12px 10px 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; background: #fff;
            }
            QPushButton {
                padding: 6px 18px; border: 1px solid #d0d0d0;
                border-radius: 4px; background: #f8f8f8;
                font-size: 13px; color: #333;
            }
            QPushButton:hover { background: #eeeeee; }
            QPushButton#primary {
                background: #4a9eff; color: white; border: none;
                font-weight: bold;
            }
            QPushButton#primary:hover { background: #3a8eef; }
        """

    def _on_check_update(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("检查中...")
        self._update_thread = UpdateCheckThread(self)
        self._update_thread.result_ready.connect(self._on_update_result)
        self._update_thread.finished.connect(self._update_thread.deleteLater)
        self._update_thread.start()

    def _on_update_result(self, result):
        if self._closed:
            return
        self.update_btn.setEnabled(True)
        self.update_btn.setText("检查更新")

        has_update, latest_version, download_url, notes, error = result
        if error:
            QMessageBox.warning(self, "检查更新失败", error)
            return
        if not has_update:
            QMessageBox.information(self, "检查更新", "当前已是最新版本。")
            return

        box = QMessageBox(self)
        box.setWindowTitle("发现新版本")
        box.setText(f"发现新版本 {latest_version}" + (f"\n\n{notes}" if notes else ""))
        download_btn = box.addButton("前往下载", QMessageBox.AcceptRole)
        box.addButton("暂不更新", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is download_btn and download_url:
            QDesktopServices.openUrl(QUrl(download_url))
