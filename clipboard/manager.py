# 剪贴板管理模块

import os
import hashlib
import time
from PySide6.QtCore import QBuffer, QIODevice
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from database.models import ClipboardItem
from database.db import Database
from utils.config import CODE_LANG_KEYWORDS, CONTENT_TYPE_TEXT, CONTENT_TYPE_CODE, CONTENT_TYPE_IMAGE, IMAGE_DIR

class ClipboardManager:
    def __init__(self, db):
        self.db = db
        self._last_content = None
        self._last_image_hash = None
        self._recently_deleted = set()
        self._last_self_copy_key = None
        self._last_self_copy_at = 0.0
        os.makedirs(IMAGE_DIR, exist_ok=True)

    def _get_clipboard(self):
        app = QApplication.instance()
        if app is None:
            return None
        return app.clipboard()

    @staticmethod
    def _strip_nulls(text: str) -> str:
        """Windows 剪贴板读写会在文本尾部附加 \x00，统一剥掉避免内容比对失败。"""
        return text.rstrip('\x00')

    @staticmethod
    def _image_fingerprint(image: QImage) -> str:
        """基于像素生成稳定指纹，避免同一张图因 PNG 重编码产生不同哈希。"""
        img = image.convertToFormat(QImage.Format.Format_RGBA8888)
        if img.isNull():
            return ""
        raw = bytes(img.constBits())
        return hashlib.md5(f"{img.width()}x{img.height()}:".encode() + raw).hexdigest()

    def _note_self_copy(self, key):
        self._last_self_copy_key = key
        self._last_self_copy_at = time.monotonic()

    def _is_recent_self_copy(self, key) -> bool:
        return (key is not None
                and key == self._last_self_copy_key
                and time.monotonic() - self._last_self_copy_at < 2.0)

    def mark_deleted(self, content):
        self._recently_deleted.add(content)
        if len(self._recently_deleted) > 200:
            self._recently_deleted.clear()

    def forget_deleted(self, content):
        self._recently_deleted.discard(content)

    def detect_type(self, text):
        for lang, keywords in CODE_LANG_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return CONTENT_TYPE_CODE, lang
        return CONTENT_TYPE_TEXT, ""

    def check_and_save(self, force: bool = False):
        text_item = self._check_text(force=force)
        if text_item:
            return text_item
        return self._check_image(force=force)

    def _check_text(self, force: bool = False):
        try:
            clipboard = self._get_clipboard()
            if clipboard is None:
                return None
            if clipboard.mimeData().hasImage():
                return None
            current = self._strip_nulls(clipboard.text())
        except Exception:
            return None
        if not current:
            return None
        if not force and current == self._last_content:
            return None
        if self._is_recent_self_copy(current):
            self._last_content = current
            return None
        if current in self._recently_deleted:
            if force:
                # 用户再次主动复制了已删除的文本，允许重新入库
                self._recently_deleted.discard(current)
            else:
                self._last_content = current
                return None
        existing = self.db.find_by_content(current)
        if existing:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.update_timestamp(existing.id)
            existing.created_time = now
            existing.updated_time = now
            self._last_content = current
            return existing
        self._last_content = current
        content_type, language = self.detect_type(current)
        item = ClipboardItem(content=current, content_type=content_type, language=language)
        item_id = self.db.add_item(item)
        item.id = item_id
        return item

    def _check_image(self, force: bool = False):
        try:
            clipboard = self._get_clipboard()
            if clipboard is None:
                return None
            mime_data = clipboard.mimeData()
            if not mime_data.hasImage():
                return None
            image = clipboard.image()
            if image.isNull():
                return None
            image_hash = self._image_fingerprint(image)
            if not image_hash:
                return None
            if image_hash == self._last_image_hash:
                return None
            self._last_image_hash = image_hash
            if image_hash in self._recently_deleted:
                return None
            existing = self.db.find_by_content(image_hash)
            if existing:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.db.update_timestamp(existing.id)
                existing.created_time = now
                existing.updated_time = now
                return existing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{image_hash[:8]}.png"
            filepath = os.path.join(IMAGE_DIR, filename)
            # Save image in original format from clipboard
            img_to_save = clipboard.image()
            if img_to_save.isNull() or not img_to_save.save(filepath, "PNG"):
                return None
            item = ClipboardItem(content=image_hash, content_type=CONTENT_TYPE_IMAGE,
                                 image_path=filepath)
            item_id = self.db.add_item(item)
            item.id = item_id
            return item
        except Exception as e:
            print(f"Image capture error: {e}")
            return None

    def copy_to_clipboard(self, item):
        try:
            if item.content_type == CONTENT_TYPE_IMAGE:
                self._copy_image_to_clipboard(item)
                return
            clipboard = self._get_clipboard()
            if clipboard is None:
                return
            clipboard.setText(item.content)
            pasted = self._strip_nulls(clipboard.text()) or item.content
            self._last_content = pasted
            self._recently_deleted.discard(pasted)
            self._note_self_copy(pasted)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.update_timestamp(item.id)
            item.created_time = now
            item.updated_time = now
        except Exception as e:
            print(f"clipboard copy failed: {e}")

    def _copy_image_to_clipboard(self, item):
        if not item.image_path or not os.path.exists(item.image_path):
            return
        try:
            image = QImage(item.image_path)
            if image.isNull():
                return
            app = QApplication.instance()
            if app:
                app.clipboard().setImage(image)
                re_read = app.clipboard().image()
                if not re_read.isNull():
                    computed = self._image_fingerprint(re_read)
                    if computed:
                        self._last_image_hash = computed
                        self._recently_deleted.add(computed)
                        self._note_self_copy(computed)
                        if len(self._recently_deleted) > 200:
                            self._recently_deleted.clear()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.db.update_timestamp(item.id)
                    item.created_time = now
                    item.updated_time = now
        except Exception as e:
            print(f"copy image to clipboard failed: {e}")
