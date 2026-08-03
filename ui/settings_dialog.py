from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QLineEdit, QGroupBox, QMessageBox
from PySide6.QtCore import Qt, Signal
from utils.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from utils.config import APP_NAME, APP_VERSION, HOTKEY
from utils.license import get_edition
from database.db import Database
from ui.about_dialog import AboutDialog
class SettingsDialog(QDialog):
    settings_changed = Signal()
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
        self._load_settings()
    def _init_ui(self):
        self.setWindowTitle("ClipMind 设置")
        self.setFixedSize(420, 470)
        self.setStyleSheet("QDialog{background:#fff} QGroupBox{font-size:13px;font-weight:bold;color:#333;border:1px solid #e0e0e0;border-radius:8px;margin-top:12px;padding:16px 12px 12px 12px} QGroupBox::title{subcontrol-origin:margin;subcontrol-position:top left;padding:0 8px;background:#fff} QLabel{font-size:13px;color:#555} QLineEdit{padding:6px 10px;border:1px solid #d0d0d0;border-radius:4px;font-size:13px} QLineEdit:focus{border:1px solid #4a9eff} QPushButton{padding:6px 16px;border:1px solid #d0d0d0;border-radius:4px;background:#f8f8f8;font-size:13px} QPushButton:hover{background:#e8e8e8} QPushButton#btn_danger{color:#e53935;border:1px solid #e53935;background:#fff5f5} QPushButton#btn_danger:hover{background:#ffe0e0}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        g1 = QGroupBox("通用设置")
        g1l = QVBoxLayout(g1)
        self.cb_autostart = QCheckBox("开机自动启动 ClipMind")
        self.cb_autostart.setStyleSheet("font-size:13px;color:#333;spacing:8px")
        g1l.addWidget(self.cb_autostart)
        hr = QHBoxLayout()
        hr.setSpacing(8)
        hr.addWidget(QLabel("全局快捷键:"))
        inp = QLineEdit()
        inp.setText(HOTKEY)
        inp.setReadOnly(True)
        inp.setMaximumWidth(180)
        hr.addWidget(inp)
        hr.addStretch()
        g1l.addLayout(hr)
        layout.addWidget(g1)
        g2 = QGroupBox("数据管理")
        g2l = QVBoxLayout(g2)
        lbl = QLabel("剪贴板历史存储在本地 SQLite 数据库中，不会上传到云端。")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#888;font-size:12px")
        g2l.addWidget(lbl)
        btn_clear = QPushButton("清空所有历史记录")
        btn_clear.setObjectName("btn_danger")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self._on_clear_history)
        g2l.addWidget(btn_clear)
        layout.addWidget(g2)
        g3 = QGroupBox("关于")
        g3l = QVBoxLayout(g3)
        ver_label = QLabel(f"{APP_NAME} 版本 {APP_VERSION}（{get_edition()}）")
        ver_label.setStyleSheet("font-size:12px;color:#888")
        g3l.addWidget(ver_label)
        btn_about = QPushButton("关于 ClipMind...")
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.clicked.connect(self._open_about)
        g3l.addWidget(btn_about)
        layout.addWidget(g3)
        layout.addStretch()
        br = QHBoxLayout()
        br.addStretch()
        btn_save = QPushButton("保存设置")
        btn_save.setStyleSheet("QPushButton{background:#4a9eff;color:white;border:none;padding:8px 24px;border-radius:4px;font-size:13px;font-weight:bold} QPushButton:hover{background:#3a8eef}")
        btn_save.clicked.connect(self._on_save)
        br.addWidget(btn_save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        br.addWidget(btn_cancel)
        layout.addLayout(br)
    def _load_settings(self):
        self.cb_autostart.setChecked(is_autostart_enabled())
    def _on_save(self):
        if self.cb_autostart.isChecked():
            enable_autostart()
        else:
            disable_autostart()
        self.settings_changed.emit()
        self.accept()
    def _on_clear_history(self):
        reply = QMessageBox.warning(self, "确认清空", "确定要清空所有剪贴板历史记录吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.clear_all()
            self.settings_changed.emit()
            QMessageBox.information(self, "完成", "所有历史记录已清空。")

    def _open_about(self):
        dialog = AboutDialog(self)
        dialog.exec()
